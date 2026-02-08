import asyncio
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

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
    student_orders,
    admin_delete_order,
    tutor_orders,
)

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
    dp.include_router(commands_orders.router)
    dp.include_router(heads.router)
    dp.include_router(teacher_panel.router)
    dp.include_router(student_panel.router)
    dp.include_router(registration.router)
    dp.include_router(student_orders.router)
    dp.include_router(admin_delete_order.router)
    dp.include_router(tutor_orders.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
