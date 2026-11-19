import sys
import requests
import ssl
import socket
import datetime
from urllib.parse import urlparse

USER_AGENT = {
    "User-Agent": "SafeSecurityCheck/1.0 (owner-authorized passive check)"
}

HEADER_CHECKS = [
    (
        "Strict-Transport-Security",
        "HIGH",
        "HSTS header missing hai. Browser ko HTTPS use karne ke liye force nahi kiya ja raha.",
        "HTTPS response me Strict-Transport-Security header add karein. Example: max-age=31536000; includeSubDomains"
    ),
    (
        "Content-Security-Policy",
        "MEDIUM",
        "Content-Security-Policy missing hai. XSS aur content injection risk badh sakta hai.",
        "Ek basic CSP add karein, jaise default-src 'self'; object-src 'none'; base-uri 'self'"
    ),
    (
        "X-Content-Type-Options",
        "MEDIUM",
        "X-Content-Type-Options missing hai. MIME sniffing risk ho sakta hai.",
        "X-Content-Type-Options: nosniff header add karein."
    ),
    (
        "X-Frame-Options",
        "MEDIUM",
        "X-Frame-Options missing hai. Clickjacking risk ho sakta hai.",
        "X-Frame-Options: DENYA ya SAMEORIGIN set karein, ya CSP me frame-ancestors use karein."
    ),
    (
        "Referrer-Policy",
        "LOW",
        "Referrer-Policy missing hai. Referrer information leak ho sakti hai.",
        "Referrer-Policy: strict-origin-when-cross-origin recommend kiya jata hai."
    ),
    (
        "Permissions-Policy",
        "LOW",
        "Permissions-Policy missing hai. Browser features restrict nahi kiye gaye hain.",
        "Example: Permissions-Policy: geolocation=(), microphone=(), camera=()"
    ),
]

def add_finding(findings, severity, title, detail, fix):
    findings.append({
        "severity": severity,
        "title": title,
        "detail": detail,
        "fix": fix
    })

def check_tls(hostname, port=443):
    findings = []

    try:
        context = ssl.create_default_context()

        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as secure_sock:
                tls_version = secure_sock.version()

                if tls_version in ("TLSv1", "TLSv1.1"):
                    add_finding(
                        findings,
                        "HIGH",
                        "Purana TLS version detect hua",
                        f"Server {tls_version} use kar raha hai, jo insecure mana jata hai.",
                        "Server par TLS 1.2 aur TLS 1.3 enable karein; TLS 1.0/1.1 disable karein."
                    )
                elif tls_version == "TLSv1.2":
                    add_finding(
                        findings,
                        "INFO",
                        "TLS 1.2 detect hua",
                        "TLS 1.2 abhi acceptable hai, lekin TLS 1.3 better hai.",
                        "Agar possible ho to TLS 1.3 enable karein."
                    )
                elif tls_version == "TLSv1.3":
                    add_finding(
                        findings,
                        "INFO",
                        "TLS 1.3 detect hua",
                        "Achha hai: TLS 1.3 modern aur secure hai.",
                        "Koi action required nahi."
                    )

                cert = secure_sock.getpeercert()
                not_after = cert.get("notAfter")

                if not_after:
                    expiry = datetime.datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                    expiry = expiry.replace(tzinfo=datetime.timezone.utc)
                    now = datetime.datetime.now(datetime.timezone.utc)
                    days_left = (expiry - now).days

                    if days_left < 0:
                        add_finding(
                            findings,
                            "HIGH",
                            "SSL certificate expire ho chuka hai",
                            f"Certificate expiry date: {not_after}",
                            "SSL certificate renew karein aur proper chain ke saath install karein."
                        )
                    elif days_left <= 14:
                        add_finding(
                            findings,
                            "MEDIUM",
                            "SSL certificate jaldi expire hone wala hai",
                            f"Certificate {days_left} din me expire ho jayega.",
                            "Certificate renew karne ka process start karein."
                        )
                    else:
                        add_finding(
                            findings,
                            "INFO",
                            "SSL certificate valid hai",
                            f"Certificate abhi valid hai. Expiry: {not_after}",
                            "Certificate expiry monitor karte rahein."
                        )

    except ssl.SSLCertVerificationError as e:
        add_finding(
            findings,
            "HIGH",
            "SSL certificate verification fail hua",
            f"Error: {e}",
            "Certificate valid CA se issued hona chahiye, hostname se match hona chahiye, aur full chain install honi chahiye."
        )
    except Exception as e:
        add_finding(
            findings,
            "MEDIUM",
            "TLS/SSL check complete nahi ho payi",
            f"Error: {e}",
            "Check karein ki HTTPS port 443 open hai aur SSL properly configured hai."
        )

    return findings

def check_http_redirect(http_url):
    findings = []

    try:
        resp = requests.get(
            http_url,
            timeout=10,
            headers=USER_AGENT,
            allow_redirects=False,
            verify=True
        )

        if resp.status_code in (301, 302, 307, 308):
            location = resp.headers.get("Location", "")
            parsed_location = urlparse(location)

            if parsed_location.scheme == "https" or location.startswith("https://"):
                add_finding(
                    findings,
                    "INFO",
                    "HTTP se HTTPS redirect ho raha hai",
                    f"Redirect location: {location}",
                    "Achha hai. HTTP ko HTTPS par redirect kiya ja raha hai."
                )
            else:
                add_finding(
                    findings,
                    "HIGH",
                    "HTTP se HTTPS redirect nahi ho raha",
                    f"HTTP request par redirect mila lekin destination HTTPS nahi hai: {location}",
                    "HTTP traffic ko HTTPS par permanently redirect karein. Example: 301 redirect to https://yourdomain.com"
                )
        else:
            add_finding(
                findings,
                "HIGH",
                "HTTP version bina redirect ke accessible hai",
                f"HTTP status code: {resp.status_code}",
                "HTTP requests ko HTTPS par redirect karein."
            )

    except requests.RequestException as e:
        add_finding(
            findings,
            "MEDIUM",
            "HTTP redirect check fail hua",
            f"Error: {e}",
            "Check karein ki website HTTP par accessible hai ya nahi."
        )

    return findings

def check_headers(resp):
    findings = []
    headers = resp.headers

    for header_name, severity, detail, fix in HEADER_CHECKS:
        if header_name not in headers:
            add_finding(
                findings,
                severity,
                f"Missing security header: {header_name}",
                detail,
                fix
            )

    # X-Content-Type-Options value check
    xcto = headers.get("X-Content-Type-Options", "").lower()
    if "X-Content-Type-Options" in headers and xcto != "nosniff":
        add_finding(
            findings,
            "MEDIUM",
            "X-Content-Type-Options value galat hai",
            f"Current value: {headers.get('X-Content-Type-Options')}",
            "X-Content-Type-Options: nosniff set karein."
        )

    # HSTS max-age basic check
    hsts = headers.get("Strict-Transport-Security", "")
    if hsts:
        hsts_lower = hsts.lower()
        if "max-age" not in hsts_lower:
            add_finding(
                findings,
                "MEDIUM",
                "HSTS header me max-age missing hai",
                f"HSTS value: {hsts}",
                "Strict-Transport-Security: max-age=31536000; includeSubDomains use karein."
            )
        else:
            try:
                max_age_part = hsts_lower.split("max-age=")[1].split(";")[0].strip()
                max_age = int(max_age_part)
                if max_age < 31536000:
                    add_finding(
                        findings,
                        "LOW",
                        "HSTS max-age kam hai",
                        f"Current max-age: {max_age}",
                        "max-age=31536000 recommend kiya jata hai."
                    )
            except Exception:
                add_finding(
                    findings,
                    "LOW",
                    "HSTS max-age parse nahi ho paya",
                    f"HSTS value: {hsts}",
                    "Strict-Transport-Security: max-age=31536000; includeSubDomains use karein."
                )

    # Clickjacking protection: XFO ya CSP frame-ancestors
    xfo = headers.get("X-Frame-Options", "").upper()
    csp = headers.get("Content-Security-Policy", "").lower()

    if not xfo and "frame-ancestors" not in csp:
        add_finding(
            findings,
            "MEDIUM",
            "Clickjacking protection missing",
            "X-Frame-Options aur CSP frame-ancestors dono missing hain.",
            "X-Frame-Options: DENYA/SAMEORIGIN add karein ya CSP me frame-ancestors 'self' use karein."
        )

    if xfo and xfo not in ("DENY", "SAMEORIGIN"):
        add_finding(
            findings,
            "MEDIUM",
            "X-Frame-Options value unexpected hai",
            f"Current value: {headers.get('X-Frame-Options')}",
            "X-Frame-Options: DENYA ya SAMEORIGIN use karein."
        )

    # Server / technology disclosure
    disclosure_headers = ["Server", "X-Powered-By", "X-AspNet-Version", "X-AspNetMvc-Version"]
    disclosed = []

    for h in disclosure_headers:
        if h in headers:
            disclosed.append(f"{h}: {headers[h]}")

    if disclosed:
        add_finding(
            findings,
            "LOW",
            "Server/technology disclosure detect hua",
            "Headers: " + ", ".join(disclosed),
            "Production me Server/X-Powered-By headers remove ya blank karne ka recommendation hota hai."
        )

    # Cookie checks
    try:
        for cookie in resp.cookies:
            cookie_name = cookie.name

            if not cookie.secure:
                add_finding(
                    findings,
                    "MEDIUM",
                    f"Cookie '{cookie_name}' me Secure flag missing hai",
                    "Ye cookie HTTP par bhi send ho sakti hai.",
                    "Sensitive cookies ke liye Secure flag set karein."
                )

            httponly = False
            try:
                httponly = cookie.has_nonstandard_attr("HttpOnly") or "HttpOnly" in getattr(cookie, "_rest", {})
            except Exception:
                httponly = False

            if not httponly:
                add_finding(
                    findings,
                    "MEDIUM",
                    f"Cookie '{cookie_name}' me HttpOnly flag missing hai",
                    "JavaScript cookie read kar sakta hai, XSS impact badh sakta hai.",
                    "Session cookies ke liye HttpOnly flag set karein."
                )

            samesite = False
            try:
                samesite = cookie.has_nonstandard_attr("SameSite") or "SameSite" in getattr(cookie, "_rest", {})
            except Exception:
                samesite = False

            if not samesite:
                add_finding(
                    findings,
                    "LOW",
                    f"Cookie '{cookie_name}' me SameSite flag missing hai",
                    "CSRF risk thoda badh sakta hai.",
                    "SameSite=Lax ya SameSite=Strict set karein, depending on use case."
                )

    except Exception as e:
        add_finding(
            findings,
            "LOW",
            "Cookie check complete nahi ho paya",
            f"Error: {e}",
            "Cookies manually inspect karein."
        )

    return findings

def analyze_url(target_url):
    target_url = target_url.strip()

    if not target_url.startswith(("http://", "https://")):
        target_url = "https://" + target_url

    parsed = urlparse(target_url)

    if not parsed.hostname:
        raise ValueError("Valid URL nahi mila. Example: https://example.com")

    findings = []

    # Agar HTTP diya hai, pehle redirect check karo
    if parsed.scheme == "http":
        findings.extend(check_http_redirect(target_url))

        # Ab HTTPS version try karte hain
        https_url = target_url.replace("http://", "https://", 1)
        add_finding(
            findings,
            "INFO",
            "HTTPS version test kar raha hoon",
            f"Trying: {https_url}",
            "Agar HTTPS accessible hai to security headers/TLS bhi check hoga."
        )
        target_url = https_url
        parsed = urlparse(target_url)

    try:
        resp = requests.get(
            target_url,
            timeout=10,
            headers=USER_AGENT,
            allow_redirects=True,
            verify=True
        )

        final_parsed = urlparse(resp.url)

        if final_parsed.scheme != "https":
            add_finding(
                findings,
                "HIGH",
                "Final URL HTTPS nahi hai",
                f"Final URL: {resp.url}",
                "Website ko HTTPS par serve karein aur HTTP ko redirect karein."
            )
        else:
            findings.extend(check_tls(final_parsed.hostname, final_parsed.port or 443))

        if resp.status_code >= 500:
            add_finding(
                findings,
                "HIGH",
                "Server error detect hua",
                f"HTTP status code: {resp.status_code}",
                "Server logs check karein. Production me 5xx errors expose nahi hone chahiye."
            )
        elif resp.status_code >= 400:
            add_finding(
                findings,
                "MEDIUM",
                "Client error status code detect hua",
                f"HTTP status code: {resp.status_code}",
                "Check karein ki URL sahi hai aur page accessible hai."
            )
        else:
            add_finding(
                findings,
                "INFO",
                "HTTP response mila",
                f"Status code: {resp.status_code}, Final URL: {resp.url}",
                "Basic connectivity OK."
            )

        findings.extend(check_headers(resp))

    except requests.exceptions.SSLError as e:
        add_finding(
            findings,
            "HIGH",
            "SSL error while connecting",
            f"Error: {e}",
            "SSL certificate, chain, hostname match, ya TLS configuration check karein."
        )
    except requests.RequestException as e:
        add_finding(
            findings,
            "HIGH",
            "Website request fail hui",
            f"Error: {e}",
            "Check karein ki website online hai, firewall/block to nahi kar raha, aur DNS sahi hai."
        )

    return target_url, findings

def build_report(target_url, findings):
    lines = []
    lines.append("=" * 70)
    lines.append("SAFE SECURITY REPORT")
    lines.append("=" * 70)
    lines.append(f"Target: {target_url}")
    lines.append(f"Generated: {datetime.datetime.now().isoformat()}")
    lines.append("Mode: Passive/safe checks only. No exploitation performed.")
    lines.append("")

    if not findings:
        lines.append("No findings detected.")
        return "\n".join(lines)

    severity_order = {
        "HIGH": 0,
        "MEDIUM": 1,
        "LOW": 2,
        "INFO": 3
    }

    findings.sort(key=lambda x: severity_order.get(x["severity"], 99))

    for i, f in enumerate(findings, 1):
        lines.append(f"[{i}] {f['severity']} - {f['title']}")
        lines.append(f"Detail: {f['detail']}")
        lines.append(f"Fix: {f['fix']}")
        lines.append("-" * 70)

    return "\n".join(lines)

def main():
    if len(sys.argv) != 2:
        print("Usage:")
        print("python safe_security_check.py https://yourwebsite.com")
        return

    target = sys.argv[1]

    try:
        final_target, findings = analyze_url(target)
        report = build_report(final_target, findings)

        print(report)

        with open("security_report.txt", "w", encoding="utf-8") as f:
            f.write(report)

        print("")
        print("Report saved to: security_report.txt")

    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()