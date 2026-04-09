import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select
from database.models import Question

from datetime import timedelta

def get_delay(remind_count: int):
    # 🔹 0–4 → 10 min
    if remind_count < 5:
        return timedelta(minutes=10)

    # 🔹 5–9 → 30 min
    elif remind_count < 10:
        return timedelta(minutes=30)

    # 🔹 10–14 → 1 soat
    elif remind_count < 15:
        return timedelta(hours=1)

    # 🔹 15+ → 6 soat (cheksiz)
    else:
        return timedelta(hours=6)
async def reminder_worker(bot, session_maker):
    while True:
        async with session_maker() as session:
            result = await session.execute(
                select(Question).where(Question.answered == False)
            )
            questions = result.scalars().all()

            now = datetime.utcnow()

            for q in questions:
                # ❌ eski savollarni skip
                if q.created_at < now - timedelta(hours=24):
                    continue

                # ❌ max 2 marta
                if q.remind_count >= 20:
                    continue

                should_send = False

                if q.remind_count == 0:
                    if now - q.created_at >= timedelta(minutes=10):
                        should_send = True

                elif q.remind_count == 1:
                    if q.last_reminded and now - q.last_reminded >= timedelta(minutes=30):
                        should_send = True

                if not should_send:
                    continue

                recipients = []

                if q.manager_id:
                    recipients = [q.manager_id]

                if not recipients:
                    continue

                for manager_id in recipients:
                    try:
                        await bot.send_message(
                            manager_id,
                            f"⏰ Eslatma!\n\nSavolga hali javob bermadingiz:\n\n{q.message_text}"
                        )
                    except Exception as e:
                        print("SEND ERROR:", e)

                q.remind_count += 1
                q.last_reminded = now

            await session.commit()

        await asyncio.sleep(60)