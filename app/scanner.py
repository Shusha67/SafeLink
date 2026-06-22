import asyncio
import logging

from app.checks import SSLCheck, WhoisCheck, GoogleSafeBrowsingCheck, SecurityCheck
from app.scorer import calculate_score, format_response
from app.cache import CacheManager

logger = logging.getLogger(__name__)

DEFAULT_CHECKS: list[SecurityCheck] = [
    SSLCheck(),
    WhoisCheck(),
    GoogleSafeBrowsingCheck(),
]


class Scanner:
    def __init__(
        self,
        cache: CacheManager,
        checks: list[SecurityCheck] | None = None,
    ) -> None:
        self._cache = cache
        self._checks = checks or DEFAULT_CHECKS

    async def scan(self, url: str) -> str:
        cached = await self._cache.get(url)
        if cached is not None:
            score, reasons = cached
            logger.info("cache hit url=%s score=%d", url, score)
            return format_response(url, score, reasons)

        results = await asyncio.gather(
            *(check.run(url) for check in self._checks)
        )

        score, reasons = calculate_score(list(results))

        ssl_valid = True
        domain_age_days: int | None = None
        google_safe = True
        for r in results:
            if r.name == "SSL":
                ssl_valid = r.passed
            elif r.name == "WHOIS":
                domain_age_days = r.metadata.get("domain_age_days")
            elif r.name == "GoogleSafeBrowsing":
                google_safe = r.passed

        await self._cache.put(url, score, ssl_valid, domain_age_days, google_safe, reasons)
        logger.info("scan complete url=%s score=%d", url, score)
        return format_response(url, score, reasons)
