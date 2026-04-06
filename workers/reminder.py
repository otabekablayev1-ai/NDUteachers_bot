import asyncio
from datetime import datetime
from database.utils import get_unanswered_questions

async def reminder_worker(bot, session_maker):
    while True:
        await asyncio.sleep(300)  # har 5 minut

        async with session_maker() as session:
            questions = await get_unanswered_questions(session)

            for q in questions:
                try:
                    await bot.send_message(
                        q.manager_id,
                        f"⏰ <b>Eslatma!</b>\n\n"
                        f"Sizda javobsiz savol bor:\n\n"
                        f"{q.message_text}",
                        parse_mode="HTML",
                        disable_notification=False
                    )

                    q.last_reminded = datetime.utcnow()
                    await session.commit()

                except Exception as e:
                    print("REMINDER ERROR:", e)