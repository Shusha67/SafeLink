from app.checks import SSLResult, WhoisResult, GoogleSBResult


def calculate_score(
    ssl_result: SSLResult,
    whois_result: WhoisResult,
    google_result: GoogleSBResult,
) -> tuple[int, list[str]]:
    score = 100
    reasons: list[str] = []

    if not ssl_result.valid:
        score -= 30
        reasons.append(ssl_result.reason)

    if whois_result.domain_age_days is not None:
        if whois_result.domain_age_days < 7:
            score -= 40
            reasons.append(f"Domain created only {whois_result.domain_age_days} days ago — very high risk")
        elif whois_result.domain_age_days < 30:
            score -= 25
            reasons.append(f"Domain is only {whois_result.domain_age_days} days old — suspicious")
        elif whois_result.domain_age_days < 60:
            score -= 15
            reasons.append(f"Domain is {whois_result.domain_age_days} days old — relatively new")
    elif whois_result.reason == "WHOIS lookup failed":
        score -= 10
        reasons.append("Could not verify domain age")

    if not google_result.safe:
        score -= 50
        reasons.append(google_result.reason)

    score = max(0, min(100, score))
    return score, reasons


def format_response(url: str, score: int, reasons: list[str]) -> str:
    if score >= 85:
        emoji = "\U0001f7e2"
        label = "Safe"
    elif score >= 50:
        emoji = "\U0001f7e1"
        label = "Suspicious — exercise caution"
    else:
        emoji = "\U0001f534"
        label = "Dangerous — do not click!"

    lines = [
        f"{emoji} *SafeLink Scan Result*",
        f"*URL:* `{url}`",
        f"*Score:* {score}/100 — {label}",
    ]
    if reasons:
        lines.append("")
        lines.append("*Findings:*")
        for r in reasons:
            lines.append(f"• {r}")

    if score >= 85:
        lines.append("\nThis link appears to be safe.")
    elif score >= 50:
        lines.append("\nProceed with caution. Verify the source before clicking.")
    else:
        lines.append("\nWe strongly recommend *not* opening this link.")

    return "\n".join(lines)
