from app.url_extractor import extract_urls


def test_extracts_http_url():
    text = "Check this out http://example.com right now"
    assert extract_urls(text) == ["http://example.com"]


def test_extracts_https_url():
    text = "Visit https://secure.example.com/path?q=1"
    assert extract_urls(text) == ["https://secure.example.com/path?q=1"]


def test_extracts_multiple_urls():
    text = "Go to http://a.com and https://b.com/page"
    result = extract_urls(text)
    assert len(result) == 2
    assert "http://a.com" in result
    assert "https://b.com/page" in result


def test_no_url_returns_empty():
    assert extract_urls("Hello, no links here!") == []
    assert extract_urls("") == []


def test_url_embedded_in_text():
    text = "Urgent! Click the link and see http://scam-site.com now!"
    assert extract_urls(text) == ["http://scam-site.com"]
