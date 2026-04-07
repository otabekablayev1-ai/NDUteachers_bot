import asyncio

from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from data.config import BOT_TOKEN
from database.engine import init_db
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
    student_orders,
    admin_delete_order,
    tutor_orders,
)
from workers.reminder import reminder_worker
from database.db import AsyncSessionLocal
from database.utils import send_daily_notifications
from handlers import admin_managers

logger.add("logs/bot.log", rotation="10 MB", level="INFO")


async def activity_scheduler(bot):
    print("SCHEDULER STARTED")
    while True:
        print("🔍 Faollik tekshirilmoqda...")

        await send_daily_notifications(bot)

        await asyncio.sleep(600)  # 🔥 har 10 minut

async def on_startup(bot: Bot):
    print("🚀 Scheduler ishga tushdi")
    asyncio.create_task(activity_scheduler(bot))

async def main():
    logger.info("🤖 Bot ishga tushmoqda...")

    await init_db()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    #asyncio.create_task(reminder_worker(bot, AsyncSessionLocal))

    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(admin_register_check.router)
    dp.include_router(admin_message.router)
    dp.include_router(admin_managers.router)  # ← shu qatorni qo‘shasiz
    dp.include_router(commands_orders.router)
    dp.include_router(heads.router)
    dp.include_router(teacher_panel.router)
    dp.include_router(student_panel.router)
    dp.include_router(registration.router)
    dp.include_router(student_orders.router)
    dp.include_router(admin_delete_order.router)
    dp.include_router(tutor_orders.router)

    await bot.delete_webhook(drop_pending_updates=True)

    await on_startup(bot)  # 🔥 SHU

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

