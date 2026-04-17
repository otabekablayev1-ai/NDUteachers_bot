import pandas as pd
import json

from services.google_drive_service import read_pdf_from_drive
from services.ai_service import parse_order
from database.db import get_all_order_links


def process_excel():
    # 📥 Excel yuklash
    df = pd.read_excel("input.xlsx")

    # 📥 DB dan linklar
    orders = get_all_order_links()

    all_data = []

    # 📄 PDFlarni o‘qish
    for order in orders:
        print("Processing:", order["link"])

        text = read_pdf_from_drive(order["link"])

        print("PDF TEXT LENGTH:", len(text))  # 👈 shu yerga

        if not text:
            continue

        ai_result = parse_order(text)

        try:
            data = json.loads(ai_result)
            all_data.extend(data.get("students", []))
        except Exception as e:
            print("AI parse error:", e)

    # 📊 Excelga yozish
    for i, row in df.iterrows():
        fio = str(row["F.I.O"]).lower()

        for student in all_data:
            full_name = student.get("full_name", "").lower()

            if fio in full_name:

                order_text = f"{student.get('order_number')} ({student.get('order_date')})"

                if student.get("order_type") == "stipendiya":
                    df.at[i, "Stipendiya buyrug'i"] = order_text

                elif student.get("order_type") == "qabul":
                    df.at[i, "Qabul buyrug'i"] = order_text

    # 💾 Saqlash
    df.to_excel("output.xlsx", index=False)
    print("✅ Tayyor: output.xlsx")


if __name__ == "__main__":
    process_excel()