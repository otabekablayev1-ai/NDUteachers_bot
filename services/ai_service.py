from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_orders(students, orders_text):
    prompt = f"""
    Sen universitet tizimidagi AI yordamchisan.

    Talabalar:
    {students}

    Buyruqlar matni:
    {orders_text}

    Vazifa:
    - Har bir talabani top
    - Qaysi buyruqqa tushganini aniqlash
    - Natijani quyidagi formatda ber:

    FIO - BUYRUQ TURI
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content