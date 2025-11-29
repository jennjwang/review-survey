"""Utilities for uploading files to Google Drive."""

from __future__ import annotations

import io
import json
import os
import re
from typing import List, Optional

import streamlit as st

try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    from google.oauth2.service_account import Credentials
except Exception:  # pragma: no cover - handled at runtime
    build = None
    MediaIoBaseUpload = None
    Credentials = None


SCOPES = ['https://www.googleapis.com/auth/drive']
CHUNK_SIZE = 100 * 1024 * 1024  # 100 MB chunks keep uploads efficient


def _require_google_libs():
    if build is None or MediaIoBaseUpload is None or Credentials is None:
        raise RuntimeError(
            "Google API libraries not available. Please install 'google-api-python-client' and 'google-auth'."
        )


def get_drive_service():
    """Initialize a Google Drive service using a service account stored in secrets."""
    _require_google_libs()
    sa_info = st.secrets.get('gcp_service_account')
    if not sa_info:
        candidate_path = st.secrets.get('GCP_SERVICE_ACCOUNT_FILE', 'google_auth.json')
        if candidate_path and os.path.exists(candidate_path):
            with open(candidate_path, 'r', encoding='utf-8') as f:
                sa_info = json.load(f)
        else:
            raise RuntimeError(
                "Missing service account credentials. Provide st.secrets['gcp_service_account'] or place google_auth.json in the app root."
            )
    creds = Credentials.from_service_account_info(sa_info, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds, cache_discovery=False)


def sanitize_filename(name: str) -> str:
    """Make a filename safe for Drive by replacing problematic characters."""
    safe = re.sub(r"[\\/\n\r\t]", "_", name)
    safe = re.sub(r"[^A-Za-z0-9._ -]", "_", safe)
    safe = re.sub(r"[ _]+", " ", safe).strip()
    return safe or "uploaded_file"


def _get_or_create_folder(service, parent_id: str, name: str) -> str:
    """Return the ID of a child folder with given name under parent, creating it if needed."""
    folder_name = sanitize_filename(name)
    query = (
        f"mimeType = 'application/vnd.google-apps.folder' and "
        f"name = '{folder_name}' and '{parent_id}' in parents and trashed = false"
    )
    res = service.files().list(
        q=query,
        fields='files(id, name)',
        pageSize=1,
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()
    items = res.get('files', [])
    if items:
        return items[0]['id']
    body = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id],
    }
    created = service.files().create(
        body=body,
        fields='id',
        supportsAllDrives=True
    ).execute()
    return created['id']


def upload_to_drive_in_subfolders(
    file,
    base_folder_id: str,
    subfolders: Optional[List[str]] = None,
    filename: Optional[str] = None,
):
    """Upload a Streamlit UploadedFile into nested Drive folders, creating them as needed."""
    if not base_folder_id:
        raise RuntimeError("Missing Drive folder ID. Set 'GDRIVE_FOLDER_ID' (or REVIEWER_GDRIVE_FOLDER_ID) in secrets.")

    service = get_drive_service()
    parent_id = base_folder_id
    for folder_name in subfolders or []:
        if folder_name:
            parent_id = _get_or_create_folder(service, parent_id, folder_name)

    file_bytes = file.getvalue()
    mimetype = getattr(file, 'type', None) or 'application/octet-stream'
    safe_name = sanitize_filename(filename or getattr(file, 'name', 'uploaded_file'))

    media = MediaIoBaseUpload(
        io.BytesIO(file_bytes),
        mimetype=mimetype,
        resumable=True,
        chunksize=CHUNK_SIZE
    )
    body = {'name': safe_name, 'parents': [parent_id]}
    request = service.files().create(
        body=body,
        media_body=media,
        fields='id, webViewLink',
        supportsAllDrives=True
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
    return response
