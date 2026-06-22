from app.checks.base import CheckResult
from app.scorer import calculate_score, format_response


def _make_results(ssl_valid=True, domain_age=365, google_safe=True):
    ssl_penalty = 0 if ssl_valid else 30
    ssl_reason = "test ssl" if ssl_valid else "SSL failed"

    if domain_age < 7:
        whois_penalty = 40
        whois_reason = f"Domain created only {domain_age} days ago — very high risk"
    elif domain_age < 30:
        whois_penalty = 25
        whois_reason = f"Domain is only {domain_age} days old — suspicious"
    elif domain_age < 60:
        whois_penalty = 15
        whois_reason = f"Domain is {domain_age} days old — relatively new"
    else:
        whois_penalty = 0
        whois_reason = f"Domain is {domain_age} days old"

    google_penalty = 0 if google_safe else 50
    google_reason = "OK" if google_safe else "Flagged by Google"

    return [
        CheckResult(name="SSL", passed=ssl_valid, penalty=ssl_penalty, reason=ssl_reason),
        CheckResult(name="WHOIS", passed=domain_age >= 60, penalty=whois_penalty, reason=whois_reason, metadata={"domain_age_days": domain_age}),
        CheckResult(name="GoogleSafeBrowsing", passed=google_safe, penalty=google_penalty, reason=google_reason),
    ]


def test_perfect_score():
    score, reasons = calculate_score(_make_results())
    assert score == 100
    assert reasons == []


def test_no_ssl_reduces_score():
    score, _ = calculate_score(_make_results(ssl_valid=False))
    assert score == 70


def test_new_domain_reduces_score():
    score, reasons = calculate_score(_make_results(domain_age=3))
    assert score == 60
    assert any("days ago" in r for r in reasons)


def test_google_flagged_reduces_score():
    score, _ = calculate_score(_make_results(google_safe=False))
    assert score == 50


def test_all_bad_clamps_to_zero():
    score, _ = calculate_score(_make_results(ssl_valid=False, domain_age=1, google_safe=False))
    assert score == 0


def test_format_safe():
    text = format_response("https://google.com", 95, [])
    assert "Safe" in text
    assert "\U0001f7e2" in text


def test_format_suspicious():
    text = format_response("http://new-site.com", 65, ["Domain is new"])
    assert "Suspicious" in text


def test_format_dangerous():
    text = format_response("http://malware.com", 20, ["Flagged"])
    assert "Dangerous" in text
