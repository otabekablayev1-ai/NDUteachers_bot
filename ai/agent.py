from openai import OpenAI
import os
import json
from scripts.process_excel_orders import process_excel
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
Sen Telegram bot uchun admin yordamchisan.

Agar foydalanuvchi odamga tegishli buyruqlarni qidirmoqchi bo‘lsa,
search_orders_multi funksiyasini chaqir.

fio ni to‘liq matn sifatida uzat.
Faqat function chaqir.
"""

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_orders_multi",
            "description": "Buyruqlarni qidirish",
            "parameters": {
                "type": "object",
                "properties": {
                    "fio": {"type": "string"},
                    "faculty": {"type": "string"},
                    "type": {"type": "string"}
                },
                "required": ["fio"]
            }
        }
    }
]

async def run_agent(text: str):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        tools=tools,
        tool_choice="auto"
    )

    message = response.choices[0].message

    if message.tool_calls:
        tool_call = message.tool_calls[0]

        return {
            "tool": tool_call.function.name,
            "args": json.loads(tool_call.function.arguments)
        }

    return {
        "tool": None,
        "args": None
    }


def handle_ai_request():
    links = [
        "https://drive.google.com/file/d/xxxx/view",
        "https://drive.google.com/file/d/yyyy/view"
    ]

    result = process_excel("students.xlsx", links)

    return result