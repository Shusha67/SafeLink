import logging
import time

from app.cache.database import CachedScan, DatabaseCache
from app.cache.memory import MemoryCache

logger = logging.getLogger(__name__)


class CacheManager:
    """Two-tier cache: in-memory LRU (L1) backed by SQLite (L2)."""

    def __init__(self) -> None:
        self._memory = MemoryCache()
        self._db = DatabaseCache()

    async def init(self) -> None:
        await self._db.init()

    async def get(self, url: str) -> tuple[int, list[str]] | None:
        mem = self._memory.get(url)
        if mem is not None:
            logger.debug("L1 cache hit url=%s", url)
            reasons = mem.details.split("|") if mem.details else []
            return mem.score, reasons

        db_row = await self._db.get(url)
        if db_row is not None:
            logger.debug("L2 cache hit url=%s", url)
            self._memory.put(url, db_row.score, db_row.details)
            reasons = db_row.details.split("|") if db_row.details else []
            return db_row.score, reasons

        return None

    async def put(
        self,
        url: str,
        score: int,
        ssl_valid: bool,
        domain_age_days: int | None,
        google_safe: bool,
        reasons: list[str],
    ) -> None:
        details = "|".join(reasons)
        self._memory.put(url, score, details)
        await self._db.put(CachedScan(
            url=url,
            score=score,
            ssl_valid=ssl_valid,
            domain_age_days=domain_age_days,
            google_safe=google_safe,
            details=details,
            scanned_at=time.time(),
        ))
