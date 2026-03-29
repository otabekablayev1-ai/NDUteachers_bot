import asyncio

from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from datetime import datetime, timedelta
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
from database.utils import send_daily_notifications
from handlers import admin_managers
from datetime import datetime, timedelta, timezone

UZ_TZ = timezone(timedelta(hours=5))

async def daily_scheduler(bot):
    while True:
        now = datetime.now(UZ_TZ)

        target = now.replace(hour=9, minute=0, second=0, microsecond=0)

        if now >= target:
            target += timedelta(days=1)

        sleep_seconds = (target - now).total_seconds()

        logger.info(f"⏳ Keyingi ishga tushish: {target}")

        await asyncio.sleep(sleep_seconds)

        logger.info("🚀 09:00 notification yuborilmoqda...")
        await send_daily_notifications(bot)

async def test_scheduler(bot):
    while True:
        print("TEST SCHEDULER STARTED")
        print("⏳ TEST: 1 daqiqa kutyapti...")
        await asyncio.sleep(60)  # 🔥 1 daqiqa

        print("🚀 TEST: notification yuborilmoqda...")
        await send_daily_notifications(bot)

async def main():
    logger.info("🤖 Bot ishga tushmoqda...")

    await init_db()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

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

    asyncio.create_task(test_scheduler(bot))  # 🔥 SHU YERGA KO‘CHIRING

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

