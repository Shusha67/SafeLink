import asyncio
import socket
import ssl
from datetime import datetime, timezone
from urllib.parse import urlparse

from app.checks.base import CheckResult, SecurityCheck
from app.config import settings


def _ssl_connect(hostname: str, ctx: ssl.SSLContext) -> dict:
    with ctx.wrap_socket(socket.socket(), server_hostname=hostname) as sock:
        sock.settimeout(settings.check_timeout_seconds)
        sock.connect((hostname, 443))
        return sock.getpeercert()


class SSLCheck(SecurityCheck):
    name = "SSL"

    async def _execute(self, url: str) -> CheckResult:
        hostname = urlparse(url).hostname
        if not hostname:
            return CheckResult(name=self.name, passed=False, penalty=30, reason="Could not parse hostname from URL")

        try:
            ctx = ssl.create_default_context()
            loop = asyncio.get_running_loop()
            cert = await asyncio.wait_for(
                loop.run_in_executor(None, _ssl_connect, hostname, ctx),
                timeout=settings.check_timeout_seconds,
            )
            not_after = cert.get("notAfter", "")
            if not_after:
                expiry = ssl.cert_time_to_seconds(not_after)
                if expiry < datetime.now(timezone.utc).timestamp():
                    return CheckResult(name=self.name, passed=False, penalty=30, reason="SSL certificate has expired")
            return CheckResult(name=self.name, passed=True, reason="Valid SSL certificate")
        except (ssl.SSLError, ssl.CertificateError) as exc:
            return CheckResult(name=self.name, passed=False, penalty=30, reason=f"SSL error: {exc}")
        except (socket.gaierror, OSError):
            return CheckResult(name=self.name, passed=False, penalty=30, reason="Could not connect to server")
        except asyncio.TimeoutError:
            return CheckResult(name=self.name, passed=False, penalty=30, reason="SSL connection timed out")
