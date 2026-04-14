import pandas as pd
from services.google_drive import extract_file_id, download_pdf, read_pdf
from services.ai_service import analyze_orders


def process_excel(input_file, links):

    df = pd.read_excel(input_file)

    students = df["FIO"].tolist()

    texts = []

    for link in links:
        file_id = extract_file_id(link)
        if not file_id:
            continue

        file = download_pdf(file_id)
        if not file:
            continue

        text = read_pdf(file)
        if text:
            texts.append(text)

    orders_text = "\n\n".join(texts)

    result = analyze_orders(students, orders_text)

    print("AI RESULT:\n", result)

    return result