import ipaddress
from urllib.parse import urlsplit


class UnsafeUrlError(ValueError):
    """Raised when a URL is outside this MVP's public-web boundary."""


def validate_public_http_url(url: str) -> str:
    """Allow public HTTP(S) URLs and reject credentials and obvious local targets."""

    candidate = url.strip()
    parsed = urlsplit(candidate)
    if parsed.scheme not in {"http", "https"}:
        raise UnsafeUrlError("Only http:// and https:// URLs are allowed.")
    if not parsed.hostname:
        raise UnsafeUrlError("The URL must contain a hostname.")
    if parsed.username or parsed.password:
        raise UnsafeUrlError("URLs containing credentials are not allowed.")

    hostname = parsed.hostname.rstrip(".").lower()
    if hostname == "localhost" or hostname.endswith((".localhost", ".local")):
        raise UnsafeUrlError("Local hostnames are not allowed.")

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address and not address.is_global:
        raise UnsafeUrlError(
            "Private, loopback, link-local, and reserved IP addresses are not allowed."
        )

    return candidate


def allowed_domain_patterns(url: str) -> list[str]:
    """Restrict Browser Use navigation to the supplied publisher host."""

    hostname = urlsplit(validate_public_http_url(url)).hostname
    assert hostname is not None
    hostname = hostname.lower()
    patterns = [hostname, f"*.{hostname}"]
    if hostname.startswith("www."):
        parent = hostname[4:]
        patterns.extend([parent, f"*.{parent}"])
    return list(dict.fromkeys(patterns))
