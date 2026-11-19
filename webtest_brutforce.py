#!/usr/bin/env python3
"""
Self-contained load test — 34 URLs hardcoded.
RPS har round DOUBLE hota hai. Report: per-second count + delay + per-URL.
Bas chalao: python bruteforce.py
"""

import time
import threading
from collections import Counter, defaultdict
from urllib.parse import urlparse

import requests

# ---------------- CONFIG (change if needed) ----------------
ALLOWED_HOSTS = {"gpcharsud.de5.net"}
START_RPS     = 1        # first round RPS
DURATION      = 2.0      # seconds per round
ROUNDS        = 5     # number of rounds (RPS doubles each round)
MAX_THREADS   = 600
TIMEOUT       = 10.0
PER_URL       = True     # print per-URL timing

URLS = [
    "https://gpcharsud.de5.net/",
    "https://gpcharsud.de5.net/About#Messages",
    "https://gpcharsud.de5.net/About#visions",
    "https://gpcharsud.de5.net/About#calendar",
    "https://gpcharsud.de5.net/About#Approvals",
    "https://gpcharsud.de5.net/About#Offered",
    "https://gpcharsud.de5.net/About#campusinfo",
    "https://gpcharsud.de5.net/About#location",
    "https://gpcharsud.de5.net/academic#Courses-tab-pane",
    "https://gpcharsud.de5.net/academic#Departments-tab-pane",
    "https://gpcharsud.de5.net/academic#AcademicCalendar-tab-pane",
    "https://gpcharsud.de5.net/academic#Syllabus-tab-pane",
    "https://gpcharsud.de5.net/academic#TimeTable-tab-pane",
    "https://gpcharsud.de5.net/academic#Faculty-tab-pane",
    "https://gpcharsud.de5.net/admission#Process-tab-pane",
    "https://gpcharsud.de5.net/admission#Eligibility-tab-pane",
    "https://gpcharsud.de5.net/admission#Required-tab-pane",
    "https://gpcharsud.de5.net/admission#FeeStructure-tab-pane",
    "https://gpcharsud.de5.net/admission#Haw-to-apply-tab-pane",
    "https://gpcharsud.de5.net/campus.html#campus-tab-pane",
    "https://gpcharsud.de5.net/campus.html#Hostel-tab-pane",
    "https://gpcharsud.de5.net/campus.html#library-tab-pane",
    "https://gpcharsud.de5.net/campus.html#labsr-tab-pane",
    "https://gpcharsud.de5.net/events/",
    "https://gpcharsud.de5.net/dashboard/login/",
    "https://gpcharsud.de5.net/dashboard/login/#calendar",
    "https://gpcharsud.de5.net/cheatsheets/",
    "https://gpcharsud.de5.net/pyqs/",
    "https://gpcharsud.de5.net/placements#home-tab-pane",
    "https://gpcharsud.de5.net/placements#Statistics-tab-pane",
    "https://gpcharsud.de5.net/placements#Recruiters-Companies-tab-pane",
    "https://gpcharsud.de5.net/student_engagement_page/",
    "https://gpcharsud.de5.net/company_student_verification",
    "https://gpcharsud.de5.net/contact_us",
]
# -----------------------------------------------------------


def validate_urls():
    for u in URLS:
        p = urlparse(u)
        if p.scheme not in ("http", "https"):
            raise SystemExit(f"Refused non-http(s): {u}")
        if p.netloc.lower() not in ALLOWED_HOSTS:
            raise SystemExit(f"Refused host {p.netloc!r} — not in ALLOWED_HOSTS")


def run_round(target_rps):
    results = []
    lock = threading.Lock()
    t_start = time.time()
    n_urls = len(URLS)

    n_threads = max(1, min(target_rps, MAX_THREADS))
    per_thread_interval = n_threads / target_rps
    counter = [0]

    def worker(offset):
        time.sleep(offset)
        last_fire = 0.0
        while True:
            now = time.time()
            if now - t_start >= DURATION:
                return
            wait = last_fire + per_thread_interval - now
            if wait > 0:
                time.sleep(wait)
            if time.time() - t_start >= DURATION:
                return
            t0 = time.time()
            last_fire = t0
            with lock:
                idx = counter[0]
                counter[0] += 1
            url = URLS[idx % n_urls]
            try:
                r = requests.get(url, timeout=TIMEOUT)
                status = r.status_code
            except Exception as e:
                status = type(e).__name__
            dt = time.time() - t0
            with lock:
                results.append((t0 - t_start, dt, status, url))

    threads = []
    for i in range(n_threads):
        offset = (i / n_threads) * per_thread_interval
        t = threading.Thread(target=worker, args=(offset,), daemon=True)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    return results, time.time() - t_start


def report(round_no, target_rps, results, wall):
    target_delay = 1.0 / target_rps
    total = len(results)
    actual_rps = total / wall if wall > 0 else 0.0
    statuses = Counter(s for _, _, s, _ in results)
    lats = sorted(dt for _, dt, _, _ in results)

    def pct(p):
        if not lats:
            return 0.0
        return lats[min(len(lats) - 1, int(len(lats) * p))]

    buckets = Counter(int(ts) for ts, _, _, _ in results)

    print(f"\n{'=' * 74}")
    print(f"Round {round_no}  |  target {target_rps} RPS  |  wall {wall:.2f}s  |  URLs={len(URLS)}")
    print(f"{'=' * 74}")
    print(f"  Target delay/req      : {target_delay * 1000:>9.2f} ms  ({target_delay:.4f} s)")
    print(f"  Total requests        : {total}")
    print(f"  Actual avg RPS        : {actual_rps:.2f}")
    print(f"  Latency p50/p95/p99   : "
          f"{pct(0.50) * 1000:.1f} / {pct(0.95) * 1000:.1f} / {pct(0.99) * 1000:.1f} ms")
    print(f"  Latency max           : {max(lats) * 1000 if lats else 0:.1f} ms")
    print(f"  Status breakdown      : {dict(statuses)}")
    print(f"  Per-second breakdown  :")
    for s in sorted(buckets):
        cnt = buckets[s]
        avg_delay_ms = 1000.0 / cnt if cnt else 0.0
        print(f"    t={s:>3}s -> {cnt:>4} req   (avg delay ≈ {avg_delay_ms:>7.2f} ms/req)")

    per_url = defaultdict(list)
    for _, dt, st, u in results:
        per_url[u].append(dt)

    if PER_URL:
        print(f"  Per-URL timing (n, avg/min/max ms):")
        for u in URLS:
            if u not in per_url:
                continue
            l = per_url[u]
            print(f"    {u}")
            print(f"      n={len(l):<4} avg={sum(l) / len(l) * 1000:>8.1f}  "
                  f"min={min(l) * 1000:>8.1f}  max={max(l) * 1000:>8.1f}")
    else:
        slow = sorted(per_url.items(), key=lambda kv: -sum(kv[1]) / len(kv[1]))[:5]
        print(f"  Top 5 slowest URLs (avg ms):")
        for u, l in slow:
            print(f"    avg={sum(l) / len(l) * 1000:>8.1f}  n={len(l):<4}  {u}")

    return actual_rps


def main():
    validate_urls()
    print(f"Loaded {len(URLS)} URLs (hardcoded)")
    print(f"Allowed hosts  : {sorted(ALLOWED_HOSTS)}")
    print(f"Start RPS      : {START_RPS}  (doubles each round)")
    print(f"Duration/round : {DURATION}s   Rounds: {ROUNDS}")

    rps = START_RPS
    prev = None
    rows = []
    try:
        for r in range(1, ROUNDS + 1):
            results, wall = run_round(rps)
            actual = report(r, rps, results, wall)
            rows.append((r, rps, actual))
            if prev is not None:
                ratio = actual / prev if prev else 0
                verdict = "OK (~2x)" if ratio >= 1.6 else \
                          ("partial" if ratio >= 1.0 else "SATURATED")
                print(f"  vs previous : {actual - prev:+.2f} RPS  "
                      f"(x{ratio:.2f})  -> {verdict}")
            prev = actual
            rps *= 2
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")

    if rows:
        print(f"\n{'=' * 74}\nSUMMARY\n{'=' * 74}")
        print(f"{'Round':>5} {'Target RPS':>11} {'Actual RPS':>11} {'Ratio':>7}")
        for r, t, a in rows:
            print(f"{r:>5} {t:>11} {a:>11.2f} {a / t if t else 0:>7.2f}")


if __name__ == "__main__":
    main()