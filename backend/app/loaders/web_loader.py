import socket
import ipaddress
from datetime import datetime, timezone
from urllib.parse import urlparse
from typing import Union, Dict, Any, List
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

from app.loaders.base import BaseLoader
from app.models.internal import Document
from app.core.errors import InvalidFileError, ConfigurationError
from app.core.logging import logger


class SSRFProtectionError(InvalidFileError):
    """Raised when a requested URL violates SSRF security boundaries."""
    pass


def validate_url_ssrf(url_str: str) -> str:
    """
    Validates that a URL is safe against Server-Side Request Forgery (SSRF).
    Rejects private IP ranges, localhost, cloud metadata services, and non-HTTP protocols.
    """
    try:
        parsed = urlparse(url_str)
    except Exception as e:
        raise SSRFProtectionError(f"Invalid URL format: {url_str}")

    scheme = (parsed.scheme or "").lower()
    if scheme not in ("http", "https"):
        raise SSRFProtectionError(f"Prohibited protocol '{scheme}'. Only HTTP and HTTPS are allowed.")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFProtectionError(f"URL missing hostname: {url_str}")

    hostname_lower = hostname.lower()
    if hostname_lower in ("localhost", "localhost.localdomain", "127.0.0.1", "0.0.0.0", "::1"):
        raise SSRFProtectionError(f"Access to loopback address '{hostname}' is forbidden.")

    if hostname_lower.endswith(".local") or hostname_lower.endswith(".internal"):
        raise SSRFProtectionError(f"Access to internal domain '{hostname}' is forbidden.")

    # Resolve IP address to prevent DNS rebinding to internal networks
    try:
        ip_str = socket.gethostbyname(hostname)
        ip = ipaddress.ip_address(ip_str)
    except Exception as e:
        raise SSRFProtectionError(f"Could not resolve hostname '{hostname}': {str(e)}")

    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
        raise SSRFProtectionError(f"Resolved IP '{ip_str}' is within a forbidden private/internal range.")

    # Explicit check for AWS/GCP cloud metadata IP
    if ip_str.startswith("169.254."):
        raise SSRFProtectionError(f"Access to cloud metadata service '{ip_str}' is forbidden.")

    return url_str


class WebLoader(BaseLoader):
    """Web page loader with SSRF protection, main-content HTML extraction, and heading parsing."""

    def load(self, source: Union[str, Path], metadata: Dict[str, Any] = None) -> Document:
        url_str = str(source)
        validate_url_ssrf(url_str)

        try:
            logger.info(f"Fetching web page: {url_str}")
            headers = {"User-Agent": "Load2Ask-RAG-Bot/1.0"}
            with httpx.Client(follow_redirects=True, timeout=12.0, headers=headers) as client:
                response = client.get(url_str)
                response.raise_for_status()
                html_content = response.text
        except httpx.HTTPStatusError as e:
            raise InvalidFileError(f"HTTP error {e.response.status_code} fetching URL {url_str}")
        except Exception as e:
            logger.error(f"Failed to fetch URL {url_str}: {e}")
            raise InvalidFileError(f"Failed to fetch web page {url_str}: {str(e)}")

        # Parse HTML and extract main content
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract title
        title = soup.title.string.strip() if soup.title and soup.title.string else url_str

        # Extract headings
        headings = [
            h.get_text().strip()
            for h in soup.find_all(["h1", "h2", "h3"])
            if h.get_text().strip()
        ]

        # Strip navigation, header, footer, scripts, styles, ads
        for element in soup(["script", "style", "nav", "header", "footer", "aside", "form", "iframe", "noscript"]):
            element.decompose()

        # Extract main text
        main_content = soup.get_text(separator="\n")

        # Clean text lines
        lines = [line.strip() for line in main_content.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        timestamp = datetime.now(timezone.utc).isoformat()

        meta = {
            "source_type": "web",
            "url": url_str,
            "title": title,
            "headings": headings[:10],
            "retrieval_timestamp": timestamp,
            **(metadata or {})
        }

        return Document(
            source_type="web",
            source_name=title or url_str,
            source_uri=url_str,
            content=f"# {title}\n\n{clean_text}",
            metadata=meta
        )
