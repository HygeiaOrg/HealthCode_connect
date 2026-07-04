import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json

creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/drive.readonly'])
service = build('drive', 'v3', credentials=creds)
folder_id = '154Pb03xlrrMdmh4z8tCoaV2328UT1v7l'
results = service.files().list(q=f"'{folder_id}' in parents", fields="files(id, name, mimeType)").execute()
print(json.dumps(results.get('files', []), indent=2))
