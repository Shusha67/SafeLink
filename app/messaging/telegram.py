from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import Application

from app.config import settings
from app.messaging.base import IncomingMessage, MessagingPort

logger = logging.getLogger(__name__)

START_MESSAGE = (
    "Welcome to *SafeLink* \\! \n\n"
    "Forward or send me any message containing a link, "
    "and I'll check if it's safe\\.\n\n"
    "Simply paste or forward the suspicious message here\\."
)


class TelegramAdapter(MessagingPort):
    def __init__(self) -> None:
        self._app: Application | None = None

    async def initialize(self) -> None:
        if not settings.telegram_bot_token:
            logger.warning("Telegram bot token not configured — adapter disabled")
            return
        self._app = Application.builder().token(settings.telegram_bot_token).build()
        await self._app.initialize()
        await self._app.start()
        logger.info("Telegram adapter initialized")

    async def shutdown(self) -> None:
        if self._app:
            await self._app.stop()
            await self._app.shutdown()
            logger.info("Telegram adapter shut down")

    async def parse_webhook(self, payload: dict) -> IncomingMessage | None:
        if not self._app:
            return None
        update = Update.de_json(payload, self._app.bot)
        if not update or not update.message:
            return None

        if update.message.text and update.message.text.startswith("/start"):
            await update.message.reply_text(START_MESSAGE, parse_mode="MarkdownV2")
            return None

        text = update.message.text or ""
        return IncomingMessage(text=text, platform_data=update)

    async def send_reply(self, message: IncomingMessage, text: str) -> None:
        update: Update = message.platform_data
        if update and update.message:
            await update.message.reply_text(text, parse_mode="Markdown")
