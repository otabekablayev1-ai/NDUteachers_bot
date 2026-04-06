import asyncio
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def send_question_notification(bot, head_id, question_id, info_text, message):
    """
    Barcha notification logikasi shu yerda
    """

    reply_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✉️ Javob yozish",
                    callback_data=f"reply_{question_id}"
                )
            ]
        ]
    )

    # 🚨 URGENT STYLE
    full_text = "🚨 <b>YANGI SAVOL!</b>\n\n" + info_text

    send_kwargs = {
        "chat_id": head_id,
        "reply_markup": reply_kb,
        "parse_mode": "HTML",
        "disable_notification": False  # 🔔 MUHIM
    }

    if message.text:
        msg = await bot.send_message(
            text=full_text + f"<b>Savol:</b>\n{message.text}",
            **send_kwargs
        )

    elif message.document:
        msg = await bot.send_document(
            document=message.document.file_id,
            caption=full_text,
            **send_kwargs
        )

    elif message.photo:
        msg = await bot.send_photo(
            photo=message.photo[-1].file_id,
            caption=full_text,
            **send_kwargs
        )

    elif message.video:
        msg = await bot.send_video(
            video=message.video.file_id,
            caption=full_text,
            **send_kwargs
        )

    # 📌 PIN (eng muhim)
    try:
        await bot.pin_chat_message(
            chat_id=head_id,
            message_id=msg.message_id
        )
    except Exception as e:
        print("PIN ERROR:", e)

    return msg