from app.checks.base import CheckResult


def calculate_score(results: list[CheckResult]) -> tuple[int, list[str]]:
    score = 100
    reasons: list[str] = []
    for r in results:
        if r.penalty > 0:
            score -= r.penalty
            if r.reason:
                reasons.append(r.reason)
    return max(0, min(100, score)), reasons


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
