import asyncio
import signal
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from handlers import admin_delete_order
from handlers import tutor_orders

from data.config import BOT_TOKEN
from database.db import init_db

from handlers import (
    start,
    registration,
    admin,
    admin_register_check,
    admin_message,
    heads,
    teacher_panel,
    student_panel,
    commands_orders,
    student_orders
)

# ========================
# 🔧 DATABASE INIT (FAKAT 1 MARTA)
# ========================
init_db()

# ========================
# 🛑 Graceful shutdown
# ========================
stop_event = asyncio.Event()

def shutdown():
    logger.warning("⛔ Bot to‘xtatilmoqda...")
    stop_event.set()

# ========================
# 🚀 BOTNI ISHGA TUSHIRISH
# ========================
async def main():
    logger.info("🤖 Bot ishga tushmoqda...")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher(storage=MemoryStorage())

    # 🔥 Routerlar tartibi juda muhim!
    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(admin_register_check.router)
    dp.include_router(admin_message.router)
    dp.include_router(commands_orders.router)
    dp.include_router(heads.router)
    dp.include_router(teacher_panel.router)
    dp.include_router(student_panel.router)
    dp.include_router(registration.router)
    dp.include_router(student_orders.router)
    dp.include_router(admin_delete_order.router)
    dp.include_router(tutor_orders.router)

    await bot.delete_webhook(drop_pending_updates=True)
    me = await bot.get_me()
    logger.info(f"✅ Bot @{me.username} ishga tushdi!")

    # Pollingni backgroundda ishga tushiramiz
    polling_task = asyncio.create_task(dp.start_polling(bot))

    # To‘xtatish signallarini kutamiz
    await stop_event.wait()

    polling_task.cancel()
    await bot.session.close()
    logger.warning("🛑 Bot to‘xtadi.")

# ========================
# 🔁 Entry point
# ========================
if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown)

    try:
        loop.run_until_complete(main())
    except Exception as e:
        logger.exception("❌ Fatal error:", e)
