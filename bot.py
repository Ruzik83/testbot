# ===========================
# bot.py (600 qatorlik boshlanish)
# ===========================

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

from handlers import (
    cmd_start, cmd_testyaratish, cmd_done, handle_answer,
    cmd_addlink, cmd_dellink, cmd_showlinks, handle_menu,
    cmd_showtests, cmd_deletetest, handle_starttest_cb,
    cmd_stats, cmd_help
)

from db import init_db
from config import BOT_TOKEN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot")

def main():
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    # Admin va foydalanuvchi komandalarini qo‘shish
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("testyaratish", cmd_testyaratish))
    app.add_handler(CommandHandler("done", cmd_done))
    app.add_handler(CommandHandler("addlink", cmd_addlink))
    app.add_handler(CommandHandler("dellink", cmd_dellink))
    app.add_handler(CommandHandler("showlinks", cmd_showlinks))
    app.add_handler(CommandHandler("showtests", cmd_showtests))
    app.add_handler(CommandHandler("deletetest", cmd_deletetest))
    app.add_handler(CommandHandler("stats", cmd_stats))

    # Foydalanuvchi xabarlarini qabul qilish
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))

    # Inline callbacklar
    app.add_handler(CallbackQueryHandler(handle_answer, pattern=r"^answer:"))
    app.add_handler(CallbackQueryHandler(handle_starttest_cb, pattern=r"^starttest:"))

    logger.info("Bot ishga tushdi.")
    app.run_polling()


if __name__ == "__main__":
    main()

# ===========================
# Shu yerda siz xohlaysizmi? davom ettirish va to‘ldirish
# ===========================
