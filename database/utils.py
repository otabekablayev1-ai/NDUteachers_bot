# handlers/utils.py
import re
import unicodedata

async def send_long_message(message, text, chunk=4000):
    for i in range(0, len(text), chunk):
        await message.answer(
            text[i:i + chunk],
            parse_mode="HTML"
        )

import re

def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"[‘’ʻʼ`´]", "'", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
