import asyncio
from datetime import datetime, UTC, timedelta
from sqlalchemy import select
from database.models import Question



def get_delay(remind_count: int):
    # 🔹 0–4 → 10 min
    if remind_count < 5:
        return timedelta(seconds=10)

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
    print("🚀 REMINDER WORKER STARTED")

    while True:
        async with session_maker() as session:
            result = await session.execute(
                select(Question).where(
                    Question.answered.is_(False),
                    Question.manager_id.is_not(None),
                    Question.message_text.is_not(None)
                )
            )
            questions = result.scalars().all()

            now = datetime.now(UTC)

            for q in questions:
                # manager yo'q bo'lsa skip
                if not q.manager_id:
                    continue

                delay = get_delay(q.remind_count or 0)

                should_send = False

                if not q.last_reminded:
                    if q.created_at and now - q.created_at >= delay:
                        should_send = True
                else:
                    if now - q.last_reminded >= delay:
                        should_send = True

                if not should_send:
                    continue

                try:
                    await bot.send_message(
                        q.manager_id,
                        f"🚨 <b>ESLATMA!</b>\n\n"
                        f"❗ Savolga hali javob bermadingiz:\n\n"
                        f"💬 {q.message_text}",
                        parse_mode="HTML",
                        disable_notification=False
                    )
                    print(f"[REMINDER] sent to {q.manager_id} | q_id={q.id}")

                except Exception as e:
                    print("[REMINDER ERROR]:", e)
                    continue

                q.remind_count = (q.remind_count or 0) + 1
                q.last_reminded = now

            await session.commit()

        await asyncio.sleep(60)