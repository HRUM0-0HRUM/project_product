#!/usr/bin/env python3
import logging
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

from bot.config import BOT_TOKEN, DEBUG
from bot.handlers import (
    start_command,
    help_command,
    cancel_command,
    handle_message,
    handle_selection
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG if DEBUG else logging.INFO
)

logger = logging.getLogger(__name__)

def main():
    if not BOT_TOKEN:
        logger.error("Ошибка: BOT_TOKEN не найден в .env файле")
        sys.exit(1)
    
    logger.info("Запуск бота...")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_message
    ))
    
    application.add_handler(CallbackQueryHandler(handle_selection))
    
    logger.info("Бот запущен и готов к работе!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()