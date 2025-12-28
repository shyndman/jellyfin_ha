"""URL helpers for the Jellyfin integration."""
from urllib.parse import urlparse, urlunparse

from .const import DEFAULT_HTTP_PORT, DEFAULT_HTTPS_PORT


def normalize_server_url(raw_url: str) -> str:
    """Normalize a Jellyfin server URL with default scheme/port."""
    url = raw_url.strip()
    if url.endswith("/"):
        url = url[:-1]

    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        parsed = urlparse(f"http://{url}")

    scheme = (parsed.scheme or "http").lower()
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must include a hostname")

    port = parsed.port
    if port is None:
        port = DEFAULT_HTTPS_PORT if scheme == "https" else DEFAULT_HTTP_PORT

    if ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"

    netloc = f"{hostname}:{port}"
    return urlunparse(
        (
            scheme,
            netloc,
            parsed.path or "",
            parsed.params or "",
            parsed.query or "",
            parsed.fragment or "",
        )
    )
