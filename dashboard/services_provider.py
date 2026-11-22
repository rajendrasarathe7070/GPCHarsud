"""
services_provider.py — AI Model Provider Layer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 MODEL बदलना है? सिर्फ नीचे की 3 lines बदलें।
"""
import re
import json
import logging
import threading
from openai import OpenAI

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════
# 🎯 AI CONFIG — सिर्फ यही छूएँ
# ═══════════════════════════════════════════════════════
AI_PROVIDER = "openrouter"  
# AI_PROVIDER = "gemini" # "gemini" | "deepseek" | "openrouter"
AI_FALLBACKS = ["gemini", "deepseek"]           # primary fail हो तो ये try करो

MODELS = {
    "gemini":     "gemini-2.5-flash",
    "deepseek":   "deepseek-chat",
    # OpenRouter free models (हर महीने बदलते हैं, verify करें):
    "openrouter": "openai/gpt-4o-mini",         # या: "meta-llama/llama-3.3-70b-instruct:free"
}

AI_TEMPERATURE = 0.3
AI_MAX_TOKENS = 1024
AI_TIMEOUT = 45.0
# ═══════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════
# EXCEPTIONS — हर error का अपना user-friendly message
# ═══════════════════════════════════════════════════════
class BotError(Exception):
    """Base — सभी bot errors यहीं से निकलते हैं।"""
    code = "BOT_ERROR"
    default_user_message = "कुछ गलत हो गया। कृपया दोबारा कोशिश करें।"
    def __init__(self, technical=None, user_message=None):
        super().__init__(technical or "")
        self.technical = technical or ""
        self.user_message = user_message or self.default_user_message


class AIQuotaError(BotError):
    code = "AI_QUOTA"
    default_user_message = "AI की मासिक सीमा/बैलेंस खत्म हो गया है। कृपया बाद में कोशिश करें।"

class AIAuthError(BotError):
    code = "AI_AUTH"
    default_user_message = "AI कुंजी काम नहीं कर रही। कृपया एडमिन से संपर्क करें।"

class AIModelError(BotError):
    code = "AI_MODEL"
    default_user_message = "AI मॉडल उपलब्ध नहीं है। कृपया एडमिन से संपर्क करें।"

class AINetworkError(BotError):
    code = "AI_NETWORK"
    default_user_message = "AI सेवा से जुड़ नहीं पाए। कृपया इंटरनेट जाँचें।"

class AITimeoutError(BotError):
    code = "AI_TIMEOUT"
    default_user_message = "AI जवाब देने में बहुत समय लग रहा है। कृपया दोबारा कोशिश करें।"

class AIExtractionError(BotError):
    code = "AI_EXTRACT"
    default_user_message = "टेक्स्ट से सवाल-जवाब नहीं बना पाए। कृपया और content दें।"

class AllProvidersFailedError(BotError):
    code = "ALL_AI_FAILED"
    default_user_message = "सभी AI सेवाएँ फिलहाल काम नहीं कर रही हैं। कृपया बाद में कोशिश करें।"


def _classify_exception(e, provider=""):
    """Provider errors → typed BotError."""
    msg = str(e)
    code = getattr(e, "status_code", None)
    if not code:
        m = re.search(r"Error code: (\d{3})", msg)
        if m:
            code = int(m.group(1))

    if code in (401, 403):     return AIAuthError(f"{provider}: {msg}")
    if code in (402, 429):     return AIQuotaError(f"{provider}: {msg}")
    if code == 404:            return AIModelError(f"{provider}: {msg}")
    if code and code >= 500:   return AINetworkError(f"{provider}: {msg}")
    if "timeout" in msg.lower() or "timed out" in msg.lower():
        return AITimeoutError(f"{provider}: {msg}")
    if "connection" in msg.lower() or "network" in msg.lower():
        return AINetworkError(f"{provider}: {msg}")
    return BotError(f"{provider}: {msg}")


# ═══════════════════════════════════════════════════════
# CLIENTS (lazy singletons)
# ═══════════════════════════════════════════════════════
_clients = {}
_clients_lock = threading.Lock()


def _get_gemini_client():
    if "gemini" not in _clients:
        with _clients_lock:
            if "gemini" not in _clients:
                from django.conf import settings
                key = getattr(settings, "GEMINI_API_KEY", "")
                if not key:
                    raise AIAuthError("GEMINI_API_KEY not set")
                from google import genai
                _clients["gemini"] = genai.Client(api_key=key)
    return _clients["gemini"]


def _get_openai_client(provider):
    if provider not in _clients:
        with _clients_lock:
            if provider not in _clients:
                from django.conf import settings
                if provider == "deepseek":
                    key = getattr(settings, "DEEPSEEK_API_KEY", "")
                    base = getattr(settings, "DEEPSEEK_BASE_URL", "https://api.deepseek.com")
                    headers = None
                elif provider == "openrouter":
                    key = getattr(settings, "OPENROUTER_API_KEY", "")
                    base = "https://openrouter.ai/api/v1"
                    headers = {
                        "HTTP-Referer": getattr(settings, "SITE_URL", "http://localhost:8000"),
                        "X-Title": "College AI Bot",
                    }
                else:
                    raise AIAuthError(f"Unknown provider: {provider}")
                if not key:
                    raise AIAuthError(f"{provider.upper()}_API_KEY not set")
                _clients[provider] = OpenAI(
                    api_key=key, base_url=base, default_headers=headers, timeout=AI_TIMEOUT,
                )
    return _clients[provider]


# ═══════════════════════════════════════════════════════
# PROVIDER IMPLEMENTATIONS
# ═══════════════════════════════════════════════════════
def _call_gemini(user_msg, system_prompt, tool_handler=None):
    try:
        from google.genai import types
        client = _get_gemini_client()
        cfg = {"system_instruction": system_prompt, "temperature": AI_TEMPERATURE}
        if tool_handler:
            cfg["tools"] = [tool_handler]
        resp = client.models.generate_content(
            model=MODELS["gemini"], contents=user_msg,
            config=types.GenerateContentConfig(**cfg),
        )
        return (resp.text or "").strip()
    except BotError:
        raise
    except Exception as e:
        raise _classify_exception(e, "gemini")


def _call_openai_compatible(provider, user_msg, system_prompt, tool_spec=None):
    client = _get_openai_client(provider)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg},
    ]
    kwargs = {
        "model": MODELS[provider],
        "messages": messages,
        "temperature": AI_TEMPERATURE,
        "max_tokens": AI_MAX_TOKENS,
    }
    if tool_spec:
        kwargs["tools"] = [tool_spec["schema"]]
        kwargs["tool_choice"] = "auto"

    try:
        for _ in range(2):
            resp = client.chat.completions.create(**kwargs)
            msg = resp.choices[0].message

            if tool_spec and msg.tool_calls:
                messages.append({
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {"id": tc.id, "type": "function",
                         "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                        for tc in msg.tool_calls
                    ],
                })
                for tc in msg.tool_calls:
                    if tc.function.name == tool_spec["name"]:
                        try:
                            args = json.loads(tc.function.arguments or "{}")
                            result = tool_spec["handler"](**args)
                        except Exception:
                            logger.exception("Tool call failed")
                            result = "Tool execution failed."
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": str(result),
                        })
                kwargs["messages"] = messages
                continue

            return (msg.content or "").strip()
        return ""
    except BotError:
        raise
    except Exception as e:
        raise _classify_exception(e, provider)


# ═══════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════
def call_ai(user_msg, system_prompt, tool_spec=None, tool_handler=None):
    """
    Primary → fallbacks chain।
    Returns (reply_text, provider_used).
    Raises AllProvidersFailedError if all fail.
    """
    chain = [AI_PROVIDER] + [p for p in AI_FALLBACKS if p != AI_PROVIDER]
    errors = []

    for provider in chain:
        try:
            if provider == "gemini":
                reply = _call_gemini(user_msg, system_prompt, tool_handler=tool_handler)
            else:
                reply = _call_openai_compatible(provider, user_msg, system_prompt, tool_spec=tool_spec)

            if reply:
                logger.info(f"AI replied via {provider}")
                return reply, provider
            errors.append(f"{provider}: empty reply")
        except BotError as be:
            logger.warning(f"{provider} failed [{be.code}]: {be.technical}")
            errors.append(f"{provider}[{be.code}]: {be.technical}")
        except Exception as e:
            logger.exception(f"{provider} unexpected")
            errors.append(f"{provider}: {e}")

    raise AllProvidersFailedError(" | ".join(errors))


def ai_extract_qa_pairs(raw_text):
    """
    कोई भी raw text → Q&A pairs (सारे providers chain के through).
    """
    if not raw_text or not raw_text.strip():
        raise AIExtractionError("Empty input")

    raw_text = raw_text.strip()[:50000]

    def _prompt(chunk):
        return f"""तुम data extraction expert हो। नीचे दिए text से सभी Question-Answer pairs निकालो।

नियम:
1. हर educational जानकारी को Q&A pair में convert करो
2. सवाल natural हों (जैसे student पूछेगा)
3. जवाब original text की जानकारी रखें
4. सिर्फ valid JSON array return करो

Format:
[{{"q":"सवाल","a":"जवाब"}}]

TEXT:
---
{chunk}
---

JSON:"""

    CHUNK = 6000
    if len(raw_text) <= CHUNK:
        chunks = [raw_text]
    else:
        chunks, cur = [], ""
        for para in raw_text.split("\n\n"):
            if len(cur) + len(para) + 2 < CHUNK:
                cur += para + "\n\n"
            else:
                if cur.strip():
                    chunks.append(cur.strip())
                cur = para + "\n\n"
        if cur.strip():
            chunks.append(cur.strip())

    all_pairs = []
    sys_msg = "You extract data. Return only valid JSON arrays."

    for i, chunk in enumerate(chunks, 1):
        try:
            reply, provider = call_ai(_prompt(chunk), sys_msg)
            json_str = reply
            m = re.search(r"```(?:json)?\s*(.+?)\s*```", reply, re.S)
            if m:
                json_str = m.group(1)
            m = re.search(r"\[\s*\{.*\}\s*\]", json_str, re.S)
            if m:
                json_str = m.group(0)

            data = json.loads(json_str)
            for item in data:
                q = str(item.get("q", "")).strip()
                a = str(item.get("a", "")).strip()
                if len(q) > 3 and len(a) > 3:
                    all_pairs.append((q, a))
            logger.info(f"Chunk {i}/{len(chunks)} via {provider}: +{len(data)} pairs")
        except Exception as e:
            logger.warning(f"Chunk {i} failed: {e}")

    if not all_pairs:
        raise AIExtractionError(
            "No pairs extracted from any provider",
            user_message="टेक्स्ट से कोई सवाल-जवाब नहीं निकल पाए। कृपया और content डालें।",
        )

    seen, result = set(), []
    for q, a in all_pairs:
        k = q.lower().strip()
        if k not in seen:
            seen.add(k)
            result.append((q, a))

    logger.info(f"Extracted {len(result)} unique Q&A pairs")
    return result