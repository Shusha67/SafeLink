import time
import pytest
import pytest_asyncio

from app.cache.database import CachedScan, DatabaseCache


@pytest_asyncio.fixture
async def db(tmp_path):
    db_path = str(tmp_path / "test.db")
    database = DatabaseCache(db_path=db_path)
    await database.init()
    return database


async def _insert_scan(db: DatabaseCache, url: str, score: int, scanned_at: float | None = None):
    await db.put(CachedScan(
        url=url,
        score=score,
        ssl_valid=score >= 70,
        domain_age_days=365 if score >= 50 else 3,
        google_safe=score >= 50,
        details="test details",
        scanned_at=scanned_at or time.time(),
    ))


@pytest.mark.asyncio
async def test_stats_empty(db):
    stats = await db.get_stats()
    assert stats["total_scans"] == 0
    assert stats["average_score"] == 0.0


@pytest.mark.asyncio
async def test_stats_with_data(db):
    await _insert_scan(db, "https://safe.com", 95)
    await _insert_scan(db, "https://sketchy.com", 60)
    await _insert_scan(db, "https://evil.com", 20)

    stats = await db.get_stats()
    assert stats["total_scans"] == 3
    assert stats["safe_count"] == 1
    assert stats["suspicious_count"] == 1
    assert stats["dangerous_count"] == 1
    assert 58 <= stats["average_score"] <= 59


@pytest.mark.asyncio
async def test_history_pagination(db):
    for i in range(5):
        await _insert_scan(db, f"https://site-{i}.com", 80 + i, scanned_at=time.time() + i)

    items, total = await db.get_history(page=1, page_size=2)
    assert total == 5
    assert len(items) == 2
    assert items[0].url == "https://site-4.com"
    assert items[1].url == "https://site-3.com"

    items, total = await db.get_history(page=3, page_size=2)
    assert total == 5
    assert len(items) == 1


@pytest.mark.asyncio
async def test_history_empty(db):
    items, total = await db.get_history(page=1, page_size=10)
    assert total == 0
    assert items == []


@pytest.mark.asyncio
async def test_history_order_most_recent_first(db):
    await _insert_scan(db, "https://old.com", 90, scanned_at=1000.0)
    await _insert_scan(db, "https://new.com", 90, scanned_at=2000.0)

    items, _ = await db.get_history(page=1, page_size=10)
    assert items[0].url == "https://new.com"
    assert items[1].url == "https://old.com"
