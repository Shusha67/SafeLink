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

    async def get_stats(self) -> dict:
        try:
            async with aiosqlite.connect(self._db_path) as db:
                cursor = await db.execute(
                    "SELECT COUNT(*), COALESCE(AVG(score), 0) FROM scan_cache"
                )
                total, avg_score = await cursor.fetchone()

                cursor = await db.execute(
                    "SELECT COUNT(*) FROM scan_cache WHERE score >= 85"
                )
                (safe_count,) = await cursor.fetchone()

                cursor = await db.execute(
                    "SELECT COUNT(*) FROM scan_cache WHERE score >= 50 AND score < 85"
                )
                (suspicious_count,) = await cursor.fetchone()

                cursor = await db.execute(
                    "SELECT COUNT(*) FROM scan_cache WHERE score < 50"
                )
                (dangerous_count,) = await cursor.fetchone()

                return {
                    "total_scans": total,
                    "safe_count": safe_count,
                    "suspicious_count": suspicious_count,
                    "dangerous_count": dangerous_count,
                    "average_score": round(avg_score, 2),
                }
        except Exception:
            logger.exception("failed to fetch stats")
            return {
                "total_scans": 0,
                "safe_count": 0,
                "suspicious_count": 0,
                "dangerous_count": 0,
                "average_score": 0.0,
            }

    async def get_history(self, page: int, page_size: int) -> tuple[list[CachedScan], int]:
        try:
            async with aiosqlite.connect(self._db_path) as db:
                db.row_factory = aiosqlite.Row

                cursor = await db.execute("SELECT COUNT(*) FROM scan_cache")
                (total,) = await cursor.fetchone()

                offset = (page - 1) * page_size
                cursor = await db.execute(
                    "SELECT * FROM scan_cache ORDER BY scanned_at DESC LIMIT ? OFFSET ?",
                    (page_size, offset),
                )
                rows = await cursor.fetchall()
                items = [
                    CachedScan(
                        url=row["url"],
                        score=row["score"],
                        ssl_valid=bool(row["ssl_valid"]),
                        domain_age_days=row["domain_age_days"],
                        google_safe=bool(row["google_safe"]),
                        details=row["details"],
                        scanned_at=row["scanned_at"],
                    )
                    for row in rows
                ]
                return items, total
        except Exception:
            logger.exception("failed to fetch history")
            return [], 0

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
