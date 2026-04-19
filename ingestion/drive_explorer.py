#!/usr/bin/env python3
"""
DocSense AI - Google Drive Downloader + Text Extractor (Improved)
Downloads PDFs and exports Google Docs as PDF, then extracts text.
"""

import os
import io
from pathlib import Path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
from googleapiclient.http import MediaIoBaseDownload

ROOT_FOLDER_ID = "1mv-iDrQdpMw8YBVJSwK3WcSR-CfIDmnk"
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
DOWNLOAD_FOLDER = "downloaded_docs"

def get_drive_service():
    creds = None
    token_path = 'token.pickle'

    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)


def download_file(service, file_id, file_name, mime_type, destination_folder=DOWNLOAD_FOLDER):
    """Download file - handles both uploaded PDFs and Google Docs."""
    Path(destination_folder).mkdir(parents=True, exist_ok=True)
    
    # If it's a Google Doc, export as PDF
    if mime_type == 'application/vnd.google-apps.document':
        export_mime = 'application/pdf'
        request = service.files().export_media(fileId=file_id, mimeType=export_mime)
        safe_name = file_name.replace('/', '_') + ".pdf"
    else:
        # Regular file (PDF, etc.)
        request = service.files().get_media(fileId=file_id)
        safe_name = file_name

    file_path = Path(destination_folder) / safe_name

    with io.FileIO(file_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"Downloading {safe_name}... {int(status.progress() * 100)}%")

    print(f"✅ Downloaded: {safe_name}")
    return file_path


def explore_and_download(service, folder_id, current_path=DOWNLOAD_FOLDER):
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query,
        fields="files(id, name, mimeType)",
        orderBy="folder,name"
    ).execute()

    items = results.get('files', [])

    for item in items:
        item_name = item['name']
        item_id = item['id']
        mime_type = item['mimeType']

        if mime_type == 'application/vnd.google-apps.folder':
            print(f"📁 Entering folder: {item_name}")
            new_path = os.path.join(current_path, item_name)
            os.makedirs(new_path, exist_ok=True)
            explore_and_download(service, item_id, new_path)
        else:
            # Download PDFs and Google Docs
            if (mime_type == 'application/pdf' or 
                mime_type == 'application/vnd.google-apps.document' or
                item_name.lower().endswith(('.pdf', '.docx'))):
                download_file(service, item_id, item_name, mime_type, current_path)
            else:
                print(f"⏭️  Skipping unsupported file: {item_name}")


def main():
    print("🔍 Connecting to Google Drive...")
    service = get_drive_service()

    print("\n📥 Starting improved recursive download...")
    print("=" * 70)

    explore_and_download(service, ROOT_FOLDER_ID)

    print("\n🎉 Download completed! All files are in the 'downloaded_docs/' folder.")


if __name__ == "__main__":
    main()
