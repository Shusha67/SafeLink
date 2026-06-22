import asyncio

from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from telegram import Update

from app.database import init_db
from app.telegram_bot import create_bot_app
from app.url_extractor import extract_urls
from app.scanner import scan_url

bot_app = create_bot_app()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await bot_app.initialize()
    await bot_app.start()
    yield
    await bot_app.stop()
    await bot_app.shutdown()


app = FastAPI(title="SafeLink", version="1.0.0", lifespan=lifespan)


@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {"ok": True}


@app.post("/api/scan")
async def api_scan(request: Request):
    body = await request.json()
    text = body.get("text", "")
    urls = extract_urls(text)
    if not urls:
        return {"error": "No valid URL found in the provided text"}
    results = []
    for url in urls:
        result = await scan_url(url)
        results.append({"url": url, "report": result})
    return {"results": results}


@app.get("/health")
async def health():
    return {"status": "ok"}
