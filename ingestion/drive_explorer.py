#!/usr/bin/env python3
"""
DocSense AI - Google Drive Downloader + Metadata Capture
"""

import os
import io
import json
from pathlib import Path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
from googleapiclient.http import MediaIoBaseDownload

# Import config (now uses .env)
from ingestion.config import ROOT_FOLDER_ID, DOWNLOAD_FOLDER, METADATA_FILE

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

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
    Path(destination_folder).mkdir(parents=True, exist_ok=True)
   
    if mime_type == 'application/vnd.google-apps.document':
        export_mime = 'application/pdf'
        request = service.files().export_media(fileId=file_id, mimeType=export_mime)
        safe_name = file_name.replace('/', '_') + ".pdf"
    else:
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
    return file_path, safe_name

def explore_and_download(service, folder_id, current_path=DOWNLOAD_FOLDER, metadata: dict = None):
    if metadata is None:
        metadata = {}

    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query,
        fields="files(id, name, mimeType, webViewLink)",
        orderBy="folder,name"
    ).execute()
    items = results.get('files', [])

    for item in items:
        item_name = item['name']
        item_id = item['id']
        mime_type = item['mimeType']
        web_view_link = item.get('webViewLink')

        if mime_type == 'application/vnd.google-apps.folder':
            print(f"📁 Entering folder: {item_name}")
            new_path = os.path.join(current_path, item_name)
            os.makedirs(new_path, exist_ok=True)
            explore_and_download(service, item_id, new_path, metadata)
        else:
            if (mime_type == 'application/pdf' or
                mime_type == 'application/vnd.google-apps.document' or
                item_name.lower().endswith(('.pdf', '.docx'))):
                
                file_path, safe_name = download_file(service, item_id, item_name, mime_type, current_path)
                
                # Save metadata using relative path as key
                rel_path = str(file_path.relative_to(DOWNLOAD_FOLDER))
                metadata[rel_path] = {
                    "file_id": item_id,
                    "web_view_link": web_view_link,
                    "original_name": item_name,
                    "mime_type": mime_type
                }
            else:
                print(f"⏭️ Skipping unsupported file: {item_name}")

    return metadata

def main():
    print("🔍 Connecting to Google Drive...")
    service = get_drive_service()
    print(f"\n📥 Starting recursive download from folder ID: {ROOT_FOLDER_ID}")
    print("=" * 70)
    
    metadata = explore_and_download(service, ROOT_FOLDER_ID)
    
    # Save persistent metadata (survives cleanup)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved Drive metadata for {len(metadata)} files → {METADATA_FILE}")
    
    print("\n🎉 Download completed!")

if __name__ == "__main__":
    main()
