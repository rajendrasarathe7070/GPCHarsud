"""
services_bot.py — Cache, rate limiter, restrictions, parsers
(AI related सब कुछ services_provider.py में है)
"""
import re
import time
import logging
import threading
from difflib import get_close_matches, SequenceMatcher

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════
# FAQ CACHE
# ═══════════════════════════════════════════════════════
class FAQCache:
    def __init__(self):
        self._lock = threading.RLock()
        self._dict = {}
        self._keys = []
        self._context = ""
        self._loaded = False

    def refresh(self):
        try:
            from .models import BotKnowledge
            with self._lock:
                d = {}
                for q, a in BotKnowledge.objects.filter(is_active=True).values_list("question", "answer"):
                    k = (q or "").lower().strip()
                    if k:
                        d[k] = a
                self._dict = d
                self._keys = list(d.keys())
                self._context = "\n\n".join(f"Q: {q}\nA: {a}" for q, a in d.items())
                self._loaded = True
                logger.info(f"FAQ cache: {len(d)} entries")
        except Exception:
            logger.exception("FAQ cache refresh failed")

    def _ensure(self):
        if not self._loaded:
            self.refresh()

    def match(self, query, cutoff=0.72):
        self._ensure()
        with self._lock:
            if not self._keys:
                return None
            q = (query or "").lower().strip()
            if q in self._dict:
                return self._dict[q]
            matches = get_close_matches(q, self._keys, n=1, cutoff=cutoff)
            return self._dict[matches[0]] if matches else None

    def get_context(self):
        self._ensure()
        with self._lock:
            return self._context

    def get_relevant_context(self, query, top_k=25):
        self._ensure()
        with self._lock:
            items = list(self._dict.items())
        if not items:
            return ""
        if len(items) <= 100:
            return "\n\n".join(f"Q: {q}\nA: {a}" for q, a in items)

        q_lower = (query or "").lower().strip()
        scored = []
        for q, a in items:
            qq = q.lower()
            score = SequenceMatcher(None, q_lower, qq).ratio()
            if qq in q_lower or q_lower in qq:
                score += 0.4
            common = sum(1 for w in set(q_lower.split()) if w and w in qq)
            if common:
                score += min(common * 0.05, 0.2)
            scored.append((score, q, a))
        scored.sort(key=lambda x: x[0], reverse=True)
        return "\n\n".join(f"Q: {q}\nA: {a}" for _, q, a in scored[:top_k])

    def add(self, question, answer):
        with self._lock:
            k = (question or "").lower().strip()
            if not k:
                return
            self._dict[k] = answer
            if k not in self._keys:
                self._keys.append(k)
            self._context = "\n\n".join(f"Q: {q}\nA: {a}" for q, a in self._dict.items())

    def size(self):
        self._ensure()
        return len(self._dict)


faq_cache = FAQCache()


# ═══════════════════════════════════════════════════════
# RATE LIMITER
# ═══════════════════════════════════════════════════════
class RateLimiter:
    def __init__(self, max_calls=30, window=60):
        self.max_calls = max_calls
        self.window = window
        self._data = {}
        self._lock = threading.Lock()

    def allow(self, key):
        now = time.time()
        with self._lock:
            dq = self._data.setdefault(key, [])
            dq[:] = [t for t in dq if now - t < self.window]
            if len(dq) >= self.max_calls:
                return False
            dq.append(now)
            return True


rate_limiter = RateLimiter(max_calls=30, window=60)


# ═══════════════════════════════════════════════════════
# RESTRICTIONS
# ═══════════════════════════════════════════════════════
_restricted_cache = {"keywords": [], "loaded": False, "lock": threading.Lock()}

REFUSAL_MESSAGE = "क्षमा करें, मैं केवल कॉलेज, एडमिशन, कोर्स, फीस और एजुकेशन से जुड़ी जानकारी दे सकता हूँ।"


def refresh_restricted_cache():
    with _restricted_cache["lock"]:
        try:
            from .models import RestrictedKeyword
            _restricted_cache["keywords"] = [
                k.lower().strip()
                for k in RestrictedKeyword.objects.filter(is_active=True).values_list("keyword", flat=True)
                if k and k.strip()
            ]
            _restricted_cache["loaded"] = True
            logger.info(f"Restricted keywords: {len(_restricted_cache['keywords'])}")
        except Exception:
            logger.exception("Restricted cache failed")


def is_restricted(text):
    if not _restricted_cache["loaded"]:
        refresh_restricted_cache()
    m = (text or "").lower()
    return any(kw in m for kw in _restricted_cache["keywords"])


# ═══════════════════════════════════════════════════════
# PARSERS
# ═══════════════════════════════════════════════════════
_Q_PAT = re.compile(r'^\s*(?:Q|Question|प्रश्न|सवाल)\s*[:：\-\.\)]\s*(.+)$', re.I)
_A_PAT = re.compile(r'^\s*(?:A|Answer|उत्तर|जवाब|Ans)\s*[:：\-\.\)]\s*(.+)$', re.I)


def parse_bulk_text(text):
    text = (text or "").strip()
    if not text:
        return []

    if _Q_PAT.search(text):
        pairs, cur_q, cur_a = [], None, []
        for line in text.splitlines():
            mq, ma = _Q_PAT.match(line), _A_PAT.match(line)
            if mq:
                if cur_q and cur_a:
                    ans = "\n".join(cur_a).strip()
                    if ans:
                        pairs.append((cur_q.strip(), ans))
                cur_q, cur_a = mq.group(1).strip(), []
            elif ma and cur_q is not None:
                cur_a = [ma.group(1).strip()]
            elif cur_q is not None and line.strip():
                cur_a.append(line.strip())
        if cur_q and cur_a:
            ans = "\n".join(cur_a).strip()
            if ans:
                pairs.append((cur_q.strip(), ans))
        if pairs:
            return pairs

    for delim in ["||", "\t", " :: ", " === ", " | "]:
        if delim in text:
            pairs = []
            for line in text.splitlines():
                line = line.strip()
                if not line or delim not in line:
                    continue
                q, a = line.split(delim, 1)
                if len(q.strip()) > 2 and len(a.strip()) > 2:
                    pairs.append((q.strip(), a.strip()))
            if pairs:
                return pairs
    return []


def parse_bulk_csv(file_obj):
    import csv
    from io import TextIOWrapper
    pairs = []
    try:
        wrapper = TextIOWrapper(file_obj, encoding="utf-8", errors="ignore")
        sample = wrapper.read(2048)
        wrapper.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel
        reader = csv.reader(wrapper, dialect)
        for row in reader:
            if len(row) < 2:
                continue
            q, a = row[0].strip(), row[1].strip()
            if not q or not a:
                continue
            if q.lower() in ("question", "q", "प्रश्न", "सवाल"):
                continue
            pairs.append((q, a))
    except Exception:
        logger.exception("CSV parse failed")
    return pairs