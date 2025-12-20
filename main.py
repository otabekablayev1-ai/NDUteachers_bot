import asyncio
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from handlers import commands_orders

# === Importlar ===
from data.config import BOT_TOKEN
from database.db import create_tables_if_not_exist, init_db
from database.db import migrate_questions_table
# Routerlar
from handlers import (
    start,
    registration,
    admin,
    admin_register_check,
    admin_message,
    heads,
    teacher_panel,
    student_panel

)

# ========================
# 🔧 BAZANI TAYYORLASH
# ========================
create_tables_if_not_exist()
init_db()

migrate_questions_table()

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

    print("Routers loaded: START")

    # === Router tartibi MUHIM! ===
    dp.include_router(start.router)  # START
    print("START OK")

    dp.include_router(admin.router)  # ADMIN
    print("ADMIN OK")

    dp.include_router(admin_register_check.router)
    print("ADMIN CHECK OK")

    dp.include_router(admin_message.router)
    print("ADMIN MSG OK")

    dp.include_router(commands_orders.router)
    print("ORDERS OK")

    dp.include_router(heads.router)  # RAHBARLAR
    print("HEADS OK")

    dp.include_router(teacher_panel.router)  # O‘QITUVCHI PANEL
    print("TEACHER OK")

    dp.include_router(student_panel.router)  # TALABA PANEL
    print("STUDENT OK")

    dp.include_router(registration.router)  # RO‘YXAT
    print("REG OK")

    # === Polling ===
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info(f"✅ Bot @{(await bot.get_me()).username} ishga tushdi!")

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.warning("🛑 Bot to‘xtatildi.")


