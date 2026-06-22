import logging
import time
from dataclasses import dataclass

import aiosqlite

from app.config import settings
from app.exceptions import CacheError

logger = logging.getLogger(__name__)


@dataclass
class CachedScan:
    url: str
    score: int
    ssl_valid: bool
    domain_age_days: int | None
    google_safe: bool
    details: str
    scanned_at: float


class DatabaseCache:
    def __init__(self, db_path: str | None = None):
        self._db_path = db_path or settings.db_path

    async def init(self) -> None:
        try:
            async with aiosqlite.connect(self._db_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS scan_cache (
                        url TEXT PRIMARY KEY,
                        score INTEGER NOT NULL,
                        ssl_valid INTEGER NOT NULL,
                        domain_age_days INTEGER,
                        google_safe INTEGER NOT NULL,
                        details TEXT NOT NULL,
                        scanned_at REAL NOT NULL
                    )
                """)
                await db.commit()
            logger.info("database initialized at %s", self._db_path)
        except Exception as exc:
            raise CacheError(f"Failed to initialize database: {exc}") from exc

    async def get(self, url: str) -> CachedScan | None:
        try:
            async with aiosqlite.connect(self._db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM scan_cache WHERE url = ? AND scanned_at > ?",
                    (url, time.time() - settings.cache_ttl_seconds),
                )
                row = await cursor.fetchone()
                if row is None:
                    return None
                return CachedScan(
                    url=row["url"],
                    score=row["score"],
                    ssl_valid=bool(row["ssl_valid"]),
                    domain_age_days=row["domain_age_days"],
                    google_safe=bool(row["google_safe"]),
                    details=row["details"],
                    scanned_at=row["scanned_at"],
                )
        except Exception:
            logger.exception("database cache read failed for url=%s", url)
            return None

    async def put(self, scan: CachedScan) -> None:
        try:
            async with aiosqlite.connect(self._db_path) as db:
                await db.execute(
                    """INSERT OR REPLACE INTO scan_cache
                       (url, score, ssl_valid, domain_age_days, google_safe, details, scanned_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        scan.url,
                        scan.score,
                        int(scan.ssl_valid),
                        scan.domain_age_days,
                        int(scan.google_safe),
                        scan.details,
                        scan.scanned_at,
                    ),
                )
                await db.commit()
        except Exception:
            logger.exception("database cache write failed for url=%s", scan.url)
