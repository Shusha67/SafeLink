import asyncio
import time

from app.checks import check_ssl, check_whois, check_google_safe_browsing
from app.scorer import calculate_score, format_response
from app.database import get_cached, save_result, CachedResult
from app.config import CACHE_TTL_SECONDS


async def scan_url(url: str) -> str:
    cached = await get_cached(url, CACHE_TTL_SECONDS)
    if cached:
        reasons = cached.details.split("|") if cached.details else []
        return format_response(url, cached.score, reasons)

    ssl_result, whois_result, google_result = await asyncio.gather(
        check_ssl(url),
        check_whois(url),
        check_google_safe_browsing(url),
    )

    score, reasons = calculate_score(ssl_result, whois_result, google_result)

    await save_result(CachedResult(
        url=url,
        score=score,
        ssl_valid=ssl_result.valid,
        domain_age_days=whois_result.domain_age_days,
        google_safe=google_result.safe,
        details="|".join(reasons),
        scanned_at=time.time(),
    ))

    return format_response(url, score, reasons)
