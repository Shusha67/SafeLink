from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from app.config import TELEGRAM_BOT_TOKEN
from app.url_extractor import extract_urls
from app.scanner import scan_url

NO_URL_MESSAGE = "Please send a message containing a valid link for inspection."

START_MESSAGE = (
    "Welcome to *SafeLink* \\! \n\n"
    "Forward or send me any message containing a link, "
    "and I'll check if it's safe\\.\n\n"
    "Simply paste or forward the suspicious message here\\."
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(START_MESSAGE, parse_mode="MarkdownV2")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text or ""
    urls = extract_urls(text)

    if not urls:
        await update.message.reply_text(NO_URL_MESSAGE)
        return

    for url in urls:
        result = await scan_url(url)
        await update.message.reply_text(result, parse_mode="Markdown")


def create_bot_app() -> Application:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app
