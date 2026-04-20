import asyncio
import json

from sqlalchemy import select
from database.session import AsyncSessionLocal
from database.models import OrderLink
from database.utils import normalize_text

from services.google_drive_service import get_all_files, read_pdf_from_drive
from services.ai_service import parse_order


async def run_indexer():
    files = get_all_files()
    print(f"Drive dan topilgan fayllar soni: {len(files)}")

    async with AsyncSessionLocal() as session:
        for file in files:
            try:
                file_id = file["id"]

                # 🔍 oldin DBda bormi tekshiramiz
                existing = await session.execute(
                    select(OrderLink).where(OrderLink.file_id == file_id)
                )

                if existing.scalar():
                    continue

                print(f"\n🆕 Yangi fayl: {file['name']}")

                link = f"https://drive.google.com/file/d/{file_id}/view"

                # 🔥 PDF o‘qish (xatoni ushlaymiz)
                try:
                    text = read_pdf_from_drive(link)
                except Exception as e:
                    print(f"❌ PDF o‘qishda xato: {e}")
                    continue

                if not text:
                    print("❌ PDF text bo‘sh")
                    continue

                print(f"📄 PDF uzunligi: {len(text)}")

                # 🤖 AI analiz
                ai_result = parse_order(text)

                # 🔥 FIX: ```json ni tozalash
                ai_result = ai_result.strip()

                if ai_result.startswith("```"):
                    ai_result = ai_result.replace("```json", "").replace("```", "").strip()

                try:
                    data = json.loads(ai_result)
                except Exception as e:
                    print("❌ AI parse xato:", e)
                    print("AI RESULT:", ai_result)
                    continue

                students = data.get("students", [])

                if not students:
                    print("❌ Student topilmadi")
                    continue

                # 📦 bitta fayl → bitta row
                full_names = []
                order_type = None
                order_number = None
                order_date = None

                for student in students:
                    name = (student.get("full_name") or "").strip()
                    if name:
                        full_names.append(name)

                    if not order_type:
                        order_type = student.get("order_type")
                    if not order_number:
                        order_number = student.get("order_number")
                    if not order_date:
                        order_date = student.get("order_date")

                students_raw = ", ".join(full_names)
                students_search = normalize_text(students_raw)

                new_order = OrderLink(
                    title=file["name"],
                    link=link,
                    file_id=file_id,
                    type=order_type,
                    students_raw=students_raw,
                    students_search=students_search,
                )

                session.add(new_order)
                await session.commit()

                print(f"✅ Saqlandi: {file['name']}")

            except Exception as e:
                print(f"💥 Katta xato: {e}")
                continue

    print("\n✅ Index tugadi")

if __name__ == "__main__":
    asyncio.run(run_indexer())