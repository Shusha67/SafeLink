import sys
import time
import types
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Stub the telegram package so importing app.main doesn't trigger the broken
# cryptography dependency chain in this CI environment.
_telegram_stub = types.ModuleType("telegram")
_telegram_stub.Update = MagicMock()
_telegram_ext = types.ModuleType("telegram.ext")
_telegram_ext.Application = MagicMock()
_telegram_ext.CommandHandler = MagicMock()
_telegram_ext.MessageHandler = MagicMock()
_telegram_ext.ContextTypes = MagicMock()
_telegram_ext.filters = MagicMock()
sys.modules.setdefault("telegram", _telegram_stub)
sys.modules.setdefault("telegram.ext", _telegram_ext)

from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_stats_endpoint():
    mock_stats = {
        "total_scans": 10,
        "safe_count": 6,
        "suspicious_count": 3,
        "dangerous_count": 1,
        "average_score": 72.5,
    }
    with patch("app.main.cache") as mock_cache:
        mock_cache.get_stats = AsyncMock(return_value=mock_stats)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/dashboard/stats")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total_scans"] == 10
    assert data["safe_count"] == 6
    assert data["average_score"] == 72.5


@pytest.mark.asyncio
async def test_history_endpoint():
    from app.cache.database import CachedScan

    items = [
        CachedScan(url="https://a.com", score=90, ssl_valid=True,
                    domain_age_days=365, google_safe=True, details="", scanned_at=time.time()),
    ]
    with patch("app.main.cache") as mock_cache:
        mock_cache.get_history = AsyncMock(return_value=(items, 1))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/dashboard/history?page=1&page_size=10")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["url"] == "https://a.com"
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_history_validates_params():
    with patch("app.main.cache"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/dashboard/history?page=0")
    assert resp.status_code == 422

    with patch("app.main.cache"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/dashboard/history?page_size=200")
    assert resp.status_code == 422
