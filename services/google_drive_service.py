import io
import os
from PyPDF2 import PdfReader
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_drive_service():
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")

    if not creds_json:
        raise ValueError("GOOGLE_CREDENTIALS_JSON topilmadi")

    import json
    creds_dict = json.loads(creds_json)

    creds = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=SCOPES
    )

    return build('drive', 'v3', credentials=creds)


def extract_file_id(link: str):
    try:
        return link.split("/d/")[1].split("/")[0]
    except:
        return None


def read_pdf_from_drive(link: str):
    service = get_drive_service()
    file_id = extract_file_id(link)

    if not file_id:
        return ""

    request = service.files().get_media(fileId=file_id)
    file = io.BytesIO(request.execute())

    reader = PdfReader(file)

    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

    return text