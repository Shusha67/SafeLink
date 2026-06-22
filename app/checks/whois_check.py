import asyncio
from datetime import datetime, timezone
from urllib.parse import urlparse

import whois

from app.checks.base import CheckResult, SecurityCheck
from app.config import settings


class WhoisCheck(SecurityCheck):
    name = "WHOIS"

    async def _execute(self, url: str) -> CheckResult:
        hostname = urlparse(url).hostname
        if not hostname:
            return CheckResult(name=self.name, passed=False, penalty=10, reason="Could not parse hostname")

        loop = asyncio.get_running_loop()
        w = await asyncio.wait_for(
            loop.run_in_executor(None, whois.whois, hostname),
            timeout=settings.whois_timeout_seconds,
        )

        creation = w.creation_date
        if isinstance(creation, list):
            creation = creation[0]
        if creation is None:
            return CheckResult(
                name=self.name, passed=True, penalty=10,
                reason="Domain creation date unavailable",
                metadata={"domain_age_days": None},
            )

        age_days = (datetime.now(timezone.utc) - creation.replace(tzinfo=timezone.utc)).days

        if age_days < 7:
            return CheckResult(
                name=self.name, passed=False, penalty=40,
                reason=f"Domain created only {age_days} days ago — very high risk",
                metadata={"domain_age_days": age_days},
            )
        if age_days < 30:
            return CheckResult(
                name=self.name, passed=False, penalty=25,
                reason=f"Domain is only {age_days} days old — suspicious",
                metadata={"domain_age_days": age_days},
            )
        if age_days < 60:
            return CheckResult(
                name=self.name, passed=False, penalty=15,
                reason=f"Domain is {age_days} days old — relatively new",
                metadata={"domain_age_days": age_days},
            )

        return CheckResult(
            name=self.name, passed=True,
            reason=f"Domain is {age_days} days old",
            metadata={"domain_age_days": age_days},
        )
