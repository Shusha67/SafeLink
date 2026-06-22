import aiosqlite
import time
from dataclasses import dataclass

DB_PATH = "safelink.db"


@dataclass
class CachedResult:
    url: str
    score: int
    ssl_valid: bool
    domain_age_days: int | None
    google_safe: bool
    details: str
    scanned_at: float


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
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


async def get_cached(url: str, ttl_seconds: int) -> CachedResult | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM scan_cache WHERE url = ? AND scanned_at > ?",
            (url, time.time() - ttl_seconds),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return CachedResult(
            url=row["url"],
            score=row["score"],
            ssl_valid=bool(row["ssl_valid"]),
            domain_age_days=row["domain_age_days"],
            google_safe=bool(row["google_safe"]),
            details=row["details"],
            scanned_at=row["scanned_at"],
        )


async def save_result(result: CachedResult) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT OR REPLACE INTO scan_cache
               (url, score, ssl_valid, domain_age_days, google_safe, details, scanned_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                result.url,
                result.score,
                int(result.ssl_valid),
                result.domain_age_days,
                int(result.google_safe),
                result.details,
                result.scanned_at,
            ),
        )
        await db.commit()
