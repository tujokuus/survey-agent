import pytest

from survey_browser_agent.safety import (
    UnsafeUrlError,
    allowed_domain_patterns,
    validate_public_http_url,
)


@pytest.mark.parametrize(
    "url",
    [
        "file:///C:/secret.txt",
        "http://localhost/admin",
        "http://127.0.0.1:8000",
        "http://192.168.1.2",
        "https://user:pass@example.com/article",
    ],
)
def test_rejects_non_public_or_credentialed_urls(url: str) -> None:
    with pytest.raises(UnsafeUrlError):
        validate_public_http_url(url)


def test_allows_public_https_url() -> None:
    assert validate_public_http_url("https://news.example.com/article") == (
        "https://news.example.com/article"
    )


def test_domain_patterns_include_www_parent() -> None:
    assert allowed_domain_patterns("https://www.example.com/article") == [
        "www.example.com",
        "*.www.example.com",
        "example.com",
        "*.example.com",
    ]
