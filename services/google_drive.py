import os
import io
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from PyPDF2 import PdfReader

# 🔐 ENV dan credentials olish
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

creds_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))

creds = service_account.Credentials.from_service_account_info(
    creds_dict,
    scopes=SCOPES
)

# 📦 Google Drive service
drive_service = build("drive", "v3", credentials=creds)


# 🔗 Linkdan file_id ajratish
def extract_file_id(link: str):
    try:
        return link.split("/d/")[1].split("/")[0]
    except:
        return None


# ⬇️ PDF yuklab olish
def download_pdf(file_id: str):
    try:
        request = drive_service.files().get_media(fileId=file_id)
        file = io.BytesIO(request.execute())
        return file
    except Exception as e:
        print("DOWNLOAD ERROR:", e)
        return None


# 📖 PDF o‘qish
def read_pdf(file):
    try:
        reader = PdfReader(file)
        text = ""

        for page in reader.pages:
            text += page.extract_text() or ""

        return text
    except Exception as e:
        print("READ PDF ERROR:", e)
        return None