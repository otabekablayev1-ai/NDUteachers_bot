import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select
from database.models import Question


def get_delay(remind_count: int):
    if remind_count < 5:
        return timedelta(minutes=10)
    elif remind_count < 10:
        return timedelta(minutes=30)
    elif remind_count < 15:
        return timedelta(hours=1)
    else:
        return timedelta(hours=6)


async def reminder_worker(bot, session_maker):
    print("🚀 REMINDER WORKER STARTED")

    while True:
        async with session_maker() as session:
            result = await session.execute(
                select(Question).where(
                    Question.answered == False,
                    Question.manager_id != None,
                    Question.message_text != None
                )
            )
            questions = result.scalars().all()

            now = datetime.utcnow()

            for q in questions:

                # ❌ BU QATORNI O‘CHIRDIK (endi eski savollar ham ishlaydi)
                # if q.created_at < now - timedelta(hours=24):
                #     continue

                delay = get_delay(q.remind_count or 0)

                should_send = False

                # 1-marta
                if not q.last_reminded:
                    if q.created_at and now - q.created_at >= delay:
                        should_send = True

                # keyingi martalar
                else:
                    if now - q.last_reminded >= delay:
                        should_send = True

                if not should_send:
                    continue

                try:
                    await bot.send_message(
                        q.manager_id,
                        f"⏰ <b>ESLATMA!</b>\n\n"
                        f"❗ Savolga hali javob bermadingiz:\n\n"
                        f"💬 {q.message_text}",
                        parse_mode="HTML",
                        disable_notification=False
                    )
                except Exception as e:
                    print("SEND ERROR:", e)
                    continue

                q.remind_count = (q.remind_count or 0) + 1
                q.last_reminded = now

            await session.commit()

        await asyncio.sleep(60)