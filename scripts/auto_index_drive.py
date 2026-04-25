import asyncio
import json
import os
from sqlalchemy import select
from database.session import AsyncSessionLocal
from database.models import OrderLink
from database.utils import normalize_text
from services.ai_service import parse_image_with_ai, clean_ai_json
from utils.pdf_to_images import pdf_to_images
from services.google_drive import download_file
from services.google_drive_service import get_all_files, read_pdf_from_drive
from services.ai_service import parse_order
import os
import glob

# 🔥 startda temp fayllarni tozalaymiz
for f in glob.glob("temp_*"):
    try:
        os.remove(f)
    except:
        pass

async def run_indexer():
    files = get_all_files()
    print(f"Drive dan topilgan fayllar soni: {len(files)}")

    for file in files:
        async with AsyncSessionLocal() as session:
            try:
                file_id = file["id"]

                # 🔍 DB da bormi tekshiramiz
                existing = await session.execute(
                    select(OrderLink).where(OrderLink.file_id == file_id)
                )

                if existing.scalar():
                    continue

                print(f"\n🆕 Yangi fayl: {file['name']}")
                link = f"https://drive.google.com/file/d/{file_id}/view"

                text = ""

                # 🔥 PDF o‘qish
                try:
                    text = read_pdf_from_drive(link)

                    # 🔥 AGAR TEXT BO‘SH BO‘LSA → VISION
                    if not text:
                        print("🖼 Rasm PDF, Vision ishlatyapmiz...")

                        local_path = f"temp_{file_id}.pdf"
                        download_file(file_id, local_path)

                        images = pdf_to_images(local_path)
                        all_text = ""

                        try:
                            for i, img in enumerate(images):
                                img_path = f"temp_{file_id}_{i}.png"
                                img.save(img_path)

                                print(f"📸 Image {i + 1} AI ga yuborildi")

                                try:
                                    ai_result = parse_image_with_ai(img_path)
                                    ai_result = clean_ai_json(ai_result)
                                    all_text += ai_result
                                finally:
                                    # 🔥 PNG har doim o‘chadi
                                    if os.path.exists(img_path):
                                        os.remove(img_path)

                            text = all_text

                        finally:
                            # 🔥 PDF har doim o‘chadi
                            if os.path.exists(local_path):
                                os.remove(local_path)

                except Exception as e:
                    print(f"❌ PDF o‘qishda xato: {e}")
                    continue

                print(f"📄 PDF uzunligi: {len(text)}")

                # 🤖 AI analiz
                ai_result = parse_order(text)

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
                await session.rollback()
                continue

    print("\n✅ Index tugadi")

if __name__ == "__main__":
    asyncio.run(run_indexer())