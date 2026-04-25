import io
import os

import psycopg2
from PyPDF2 import PdfReader
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ==============================
# 🔐 CONFIG
# ==============================

CREDENTIALS_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def get_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL topilmadi")
    return psycopg2.connect(database_url)


creds = service_account.Credentials.from_service_account_file(
    CREDENTIALS_FILE,
    scopes=SCOPES,
)

drive_service = build("drive", "v3", credentials=creds)

# ==============================
# 🧩 HELPERS
# ==============================


def extract_file_id(link: str):
    try:
        return link.split("/d/")[1].split("/")[0]
    except Exception:
        return None


def read_pdf(file_id: str):
    try:
        request = drive_service.files().get_media(fileId=file_id)
        file_data = io.BytesIO(request.execute())

        reader = PdfReader(file_data)

        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""

        return text.strip()
    except Exception as e:
        print(f"❌ PDF o‘qishda xato: {e}")
        return ""


def clean_text(text: str):
    return text.lower().replace("\n", " ").strip()


# ==============================
# 📥 DB FUNCTIONS
# ==============================


def get_links_from_db():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT drive_link
            FROM orders_links
            WHERE drive_link IS NOT NULL
            """
        )
        rows = cur.fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()


def save_to_orders(file_id, link, text):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO orders (file_id, drive_link, content)
            VALUES (%s, %s, %s)
            ON CONFLICT (file_id) DO NOTHING
            """,
            (file_id, link, text),
        )
        conn.commit()
    finally:
        conn.close()


# ==============================
# 🚀 MAIN LOGIC
# ==============================
def run():
    links = get_links_from_db()

    print(f"🔎 Jami linklar: {len(links)}")

    for i, link in enumerate(links, start=1):
        print(f"\n[{i}] Processing...")

        file_id = extract_file_id(link)

        if not file_id:
            print("❌ file_id topilmadi")
            continue

        text = read_pdf(file_id)

        if not text:
            print("❌ text bo‘sh")
            continue

        text = clean_text(text)
        save_to_orders(file_id, link, text)

        print("✅ Saqlandi")


if __name__ == "__main__":
    run()