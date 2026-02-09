# handlers/utils.py
import re
import unicodedata

async def send_long_message(message, text, chunk=4000):
    for i in range(0, len(text), chunk):
        await message.answer(
            text[i:i + chunk],
            parse_mode="HTML"
        )

def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = unicodedata.normalize("NFKD", text)
    text = text.lower()

    replacements = {
        "‘": "'", "’": "'", "ʻ": "'", "ʼ": "'",
        "`": "'", "´": "'",
        "o‘": "o'", "g‘": "g'",
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    text = re.sub(r"\s+", " ", text)
    return text.strip()