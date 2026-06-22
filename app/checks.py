import asyncio
import ssl
import socket
from urllib.parse import urlparse
from datetime import datetime, timezone
from dataclasses import dataclass

import httpx
import whois

from app.config import GOOGLE_SAFE_BROWSING_API_KEY


@dataclass
class SSLResult:
    valid: bool
    reason: str


@dataclass
class WhoisResult:
    domain_age_days: int | None
    reason: str


@dataclass
class GoogleSBResult:
    safe: bool
    reason: str


async def check_ssl(url: str) -> SSLResult:
    hostname = urlparse(url).hostname
    if not hostname:
        return SSLResult(valid=False, reason="Could not parse hostname from URL")
    try:
        ctx = ssl.create_default_context()
        loop = asyncio.get_running_loop()
        conn = await asyncio.wait_for(
            loop.run_in_executor(None, _ssl_connect, hostname, ctx),
            timeout=5,
        )
        not_after = conn.get("notAfter", "")
        if not_after:
            expiry = ssl.cert_time_to_seconds(not_after)
            if expiry < datetime.now(timezone.utc).timestamp():
                return SSLResult(valid=False, reason="SSL certificate has expired")
        return SSLResult(valid=True, reason="Valid SSL certificate")
    except (ssl.SSLError, ssl.CertificateError) as e:
        return SSLResult(valid=False, reason=f"SSL error: {e}")
    except (socket.gaierror, OSError):
        return SSLResult(valid=False, reason="Could not connect to server")
    except asyncio.TimeoutError:
        return SSLResult(valid=False, reason="SSL connection timed out")


def _ssl_connect(hostname: str, ctx: ssl.SSLContext) -> dict:
    with ctx.wrap_socket(socket.socket(), server_hostname=hostname) as sock:
        sock.settimeout(5)
        sock.connect((hostname, 443))
        return sock.getpeercert()


async def check_whois(url: str) -> WhoisResult:
    hostname = urlparse(url).hostname
    if not hostname:
        return WhoisResult(domain_age_days=None, reason="Could not parse hostname")
    try:
        loop = asyncio.get_running_loop()
        w = await asyncio.wait_for(
            loop.run_in_executor(None, whois.whois, hostname),
            timeout=10,
        )
        creation = w.creation_date
        if isinstance(creation, list):
            creation = creation[0]
        if creation is None:
            return WhoisResult(domain_age_days=None, reason="Domain creation date unavailable")
        age = (datetime.now(timezone.utc) - creation.replace(tzinfo=timezone.utc)).days
        return WhoisResult(domain_age_days=age, reason=f"Domain is {age} days old")
    except Exception:
        return WhoisResult(domain_age_days=None, reason="WHOIS lookup failed")


async def check_google_safe_browsing(url: str) -> GoogleSBResult:
    if not GOOGLE_SAFE_BROWSING_API_KEY:
        return GoogleSBResult(safe=True, reason="Google Safe Browsing API key not configured (skipped)")

    api_url = (
        f"https://safebrowsing.googleapis.com/v4/threatMatches:find"
        f"?key={GOOGLE_SAFE_BROWSING_API_KEY}"
    )
    payload = {
        "client": {"clientId": "safelink", "clientVersion": "1.0"},
        "threatInfo": {
            "threatTypes": [
                "MALWARE",
                "SOCIAL_ENGINEERING",
                "UNWANTED_SOFTWARE",
                "POTENTIALLY_HARMFUL_APPLICATION",
            ],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}],
        },
    }
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.post(api_url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            if data.get("matches"):
                threat = data["matches"][0].get("threatType", "unknown threat")
                return GoogleSBResult(safe=False, reason=f"Flagged by Google Safe Browsing: {threat}")
            return GoogleSBResult(safe=True, reason="Not found in Google Safe Browsing blacklist")
    except Exception:
        return GoogleSBResult(safe=True, reason="Google Safe Browsing check failed (skipped)")
