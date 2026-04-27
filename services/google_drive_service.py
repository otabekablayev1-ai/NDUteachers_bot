import io
import re
from PyPDF2 import PdfReader
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        "ndu-ai-bot-26071a4302e6.json",  # ✅ TO‘G‘RILANDI
        scopes=SCOPES
    )

    return build('drive', 'v3', credentials=creds)

def extract_file_id(link: str):
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", link)
    if match:
        return match.group(1)
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

def get_all_files():
    service = get_drive_service()

    all_files = []
    page_token = None

    while True:
        results = service.files().list(
            pageSize=1000,
            fields="nextPageToken, files(id, name, mimeType)",
            q="mimeType='application/pdf'",
            pageToken=page_token
        ).execute()

        files = results.get("files", [])
        all_files.extend(files)

        page_token = results.get("nextPageToken")

        if not page_token:
            break

    return all_files

