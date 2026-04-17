from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
Sen universitet buyruqlarini analiz qiluvchi AI'san.

Senga PDF matni beriladi.
Undan quyidagi ma'lumotlarni ajrat:

- full_name
- order_type (qabul / stipendiya / akademik tatil / ...)
- order_number
- order_date

Natijani JSON formatda qaytar:

{
  "students": [
    {
      "full_name": "...",
      "order_type": "...",
      "order_number": "...",
      "order_date": "..."
    }
  ]
}
"""


def parse_order(text: str):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text[:15000]}  # limit
        ],
        temperature=0
    )

    return response.choices[0].message.content