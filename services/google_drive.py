
import io

from google.oauth2 import service_account
from googleapiclient.discovery import build
from PyPDF2 import PdfReader

# 🔐 ENV dan credentials olish
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

creds = service_account.Credentials.from_service_account_file(
    "ndu-ai-bot-26071a4302e6.json",
    scopes=SCOPES
)
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

import requests

def download_file(file_id, save_path):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    r = requests.get(url)

    with open(save_path, "wb") as f:
        f.write(r.content)

    return save_path