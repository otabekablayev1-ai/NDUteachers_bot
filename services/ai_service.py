from openai import OpenAI
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 🔥 TEXTNI BO‘LAMIZ
def split_text(text, chunk_size=6000):
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]


# 🔥 AI JSON TOZALASH
def clean_ai_json(ai_result: str) -> str:
    if not ai_result:
        return ""

    ai_result = ai_result.strip()

    if ai_result.startswith("```"):
        ai_result = ai_result.replace("```json", "").replace("```", "").strip()

    if "**Note:**" in ai_result:
        ai_result = ai_result.split("**Note:**")[0].strip()

    # 🔥 JSONni topib olish
    start = ai_result.find("{")
    end = ai_result.rfind("}")

    if start != -1 and end != -1:
        ai_result = ai_result[start:end+1]

    return ai_result

# 🔥 BIR CHUNK UCHUN AI
def parse_chunk(chunk: str):
    prompt = f"""
    You are an expert at extracting structured data from university orders.

    Extract ALL students from the text.

    Return ONLY valid JSON in this format:

    {{
      "students": [
        {{
          "full_name": "string",
          "order_type": "string",
          "order_number": "string",
          "order_date": "YYYY-MM-DD",
          "course_from": number or null,
          "course_to": number or null
        }}
      ]
    }}

    IMPORTANT RULES:

    1. Extract FULL NAME exactly.
    2. Detect order_type (qabul, kursdan-kursga, tiklash, ko'chirish, etc).
    3. Extract order_number and order_date if exists.

    4. 🔥 COURSE EXTRACTION (VERY IMPORTANT):

    - Extract course transition ONLY if explicitly written.
    - DO NOT GUESS.

    Examples:
    "1-kursdan 2-kursga" → course_from=1, course_to=2  
    "2 kursdan 3 kursga" → course_from=2, course_to=3  
    "3-kursdan 4-kursga o'tkazish" → course_from=3, course_to=4  

    - If multiple numbers exist, IGNORE:
      ❌ order number
      ❌ dates
      ❌ document numbers

    - ONLY extract numbers near "kurs"

    - If not clearly found:
      → course_from = null
      → course_to = null

    5. Return ONLY JSON. No explanation.

    TEXT:
    \"\"\"
    {chunk}
    \"\"\"
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=4000,
        )

        content = response.choices[0].message.content
        content = clean_ai_json(content)

        # 🔥 ASOSIY PARSE
        try:
            data = json.loads(content)
            return data.get("students", [])

        except Exception as e:
            print(f"❌ JSON xato, fallback ishladi: {e}")

            # 🔥 FALLBACK (ism chiqaramiz)
            names = re.findall(r"[A-Z][a-z]+ [A-Z][a-z]+", content)

            return [{"full_name": n} for n in names]

    except Exception as e:
        print(f"❌ AI xato: {e}")
        return []

# 🔥 ASOSIY FUNKSIYA
def parse_order(text: str) -> str:

    # 🔥 SMART CHUNK (SHU YERGA)
    if len(text) < 8000:
        chunks = [text]
    else:
        chunks = split_text(text, 12000)

    print(f"🔪 {len(chunks)} ta chunkga bo‘lindi")

    all_students = []

    for i, chunk in enumerate(chunks):
        print(f"🤖 Chunk {i+1}/{len(chunks)} yuborildi")

        students = parse_chunk(chunk)

        print(f"📥 {len(students)} ta student topildi")

        all_students.extend(students)

    # duplicate remove
    unique = {}
    for s in all_students:
        name = (s.get("full_name") or "").strip().lower()
        number = (s.get("order_number") or "").strip()
        key = (name, number)
        unique[key] = s

    final_students = list(unique.values())

    print(f"✅ Yakuniy studentlar soni: {len(final_students)}")

    return json.dumps({"students": final_students}, ensure_ascii=False)

import base64

def parse_image_with_ai(image_path: str) -> str:
    with open(image_path, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode()

    prompt = """
Extract ALL students from this document.

IMPORTANT:
- Do NOT skip any student
- Return ALL names
- Output ONLY JSON

Format:
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

    vision_input = [
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
                {
                    "type": "input_image",
                    "image_url": f"data:image/png;base64,{image_base64}",
                },
            ],
        }
    ]

    response = client.responses.create(
        model="gpt-4.1",
        input=vision_input,  # type: ignore[arg-type]
    )

    # 🔥 STABLE RETURN
    if hasattr(response, "output_text") and response.output_text:
        return response.output_text

    # 🔥 fallback
    try:
        return response.output[0].content[0].text
    except (AttributeError, IndexError, KeyError):
        return ""