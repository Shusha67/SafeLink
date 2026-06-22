import logging
from pathlib import Path

from fastapi import FastAPI, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.cache import CacheManager
from app.scanner import Scanner
from app.messaging.telegram import TelegramAdapter
from app.schemas import HistoryResponse, ScanRecord, StatsResponse
from app.url_extractor import extract_urls
from app.exceptions import SafeLinkError

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

cache = CacheManager()
scanner = Scanner(cache=cache)
telegram = TelegramAdapter()

NO_URL_MESSAGE = "Please send a message containing a valid link for inspection."


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await cache.init()
    await telegram.initialize()
    logger.info("SafeLink started")
    yield
    await telegram.shutdown()
    logger.info("SafeLink stopped")


app = FastAPI(title="SafeLink", version="2.0.0", lifespan=lifespan)


@app.exception_handler(SafeLinkError)
async def safelink_error_handler(_request: Request, exc: SafeLinkError):
    logger.error("SafeLinkError: %s", exc)
    return JSONResponse(status_code=500, content={"error": str(exc)})


@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    payload = await request.json()
    message = await telegram.parse_webhook(payload)
    if message is None:
        return {"ok": True}

    urls = extract_urls(message.text)
    if not urls:
        await telegram.send_reply(message, NO_URL_MESSAGE)
        return {"ok": True}

    for url in urls:
        result = await scanner.scan(url)
        await telegram.send_reply(message, result)

    return {"ok": True}


@app.post("/api/scan")
async def api_scan(request: Request):
    body = await request.json()
    text = body.get("text", "")
    urls = extract_urls(text)
    if not urls:
        return JSONResponse(
            status_code=400,
            content={"error": "No valid URL found in the provided text"},
        )
    results = []
    for url in urls:
        report = await scanner.scan(url)
        results.append({"url": url, "report": report})
    return {"results": results}


@app.get("/api/dashboard/stats", response_model=StatsResponse)
async def dashboard_stats():
    stats = await cache.get_stats()
    return StatsResponse(**stats)


@app.get("/api/dashboard/history", response_model=HistoryResponse)
async def dashboard_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    items, total = await cache.get_history(page, page_size)
    return HistoryResponse(
        items=[ScanRecord(**vars(item)) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
