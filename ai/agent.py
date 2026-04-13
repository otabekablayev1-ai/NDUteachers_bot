from openai import OpenAI
import json

import os


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
Sen Telegram bot uchun admin yordamchisan.

Agar foydalanuvchi odamga tegishli buyruqlarni qidirsa,
search_orders funksiyasini chaqir.

Faqat function chaqir.
"""

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_orders",
            "description": "Buyruqlarni topish",
            "parameters": {
                "type": "object",
                "properties": {
                    "first_name": {"type": "string"},
                    "last_name": {"type": "string"}
                },
                "required": ["first_name", "last_name"]
            }
        }
    }
]


async def run_agent(text):
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        tools=tools,
        tool_choice="auto"
    )

    msg = response.choices[0].message

    if msg.tool_calls:
        tool_call = msg.tool_calls[0]

        return {
            "tool": tool_call.function.name,
            "args": json.loads(tool_call.function.arguments)
        }

    return {"tool": None, "args": {}}