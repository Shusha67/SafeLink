from app.checks import SSLResult, WhoisResult, GoogleSBResult
from app.scorer import calculate_score, format_response


def _make_results(ssl_valid=True, domain_age=365, google_safe=True):
    return (
        SSLResult(valid=ssl_valid, reason="test ssl"),
        WhoisResult(domain_age_days=domain_age, reason=f"Domain is {domain_age} days old"),
        GoogleSBResult(safe=google_safe, reason="test google"),
    )


def test_perfect_score():
    score, reasons = calculate_score(*_make_results())
    assert score == 100
    assert reasons == []


def test_no_ssl_reduces_score():
    score, _ = calculate_score(*_make_results(ssl_valid=False))
    assert score == 70


def test_new_domain_reduces_score():
    score, reasons = calculate_score(*_make_results(domain_age=3))
    assert score == 60
    assert any("days ago" in r for r in reasons)


def test_google_flagged_reduces_score():
    score, _ = calculate_score(*_make_results(google_safe=False))
    assert score == 50


def test_all_bad_clamps_to_zero():
    score, _ = calculate_score(*_make_results(ssl_valid=False, domain_age=1, google_safe=False))
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
