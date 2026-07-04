import os
import time
import io
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import requests
import re
from PyPDF2 import PdfReader

from dotenv import load_dotenv

load_dotenv(override=True)

# Configuration
SCOPES = ['https://www.googleapis.com/auth/drive.readonly'] 

def authenticate_drive():
    """Authenticates and returns the Google Drive API service instance using OAuth 2.0 Desktop App flow."""
    creds = None
    # token.json stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('client_secret.json'):
                print("Error: 'client_secret.json' not found.")
                print("Please download your OAuth 2.0 Client ID JSON from Google Cloud Console, rename it to 'client_secret.json', and place it in the backend folder.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            # Print the URL to the terminal instead of auto-opening to prevent Linux browser quirks
            print("\nPlease click the link below to authenticate:")
            creds = flow.run_local_server(port=0, open_browser=False)
            
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    service = build('drive', 'v3', credentials=creds)
    return service

def list_invoices(service):
    """Lists files in the target Google Drive folder."""
    folder_id = os.getenv('DRIVE_FOLDER_ID')
    if not folder_id:
        print("Error: DRIVE_FOLDER_ID environment variable not set in .env")
        return []
        
    query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
    try:
        results = service.files().list(
            q=query, pageSize=10, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])
        return items
    except Exception as e:
        print(f"Error listing files: {e}")
        return []

def download_invoice(service, file_id, file_name):
    """Downloads a file from Google Drive."""
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print(f"Downloading {file_name}: {int(status.progress() * 100)}%.")
    
    fh.seek(0)
    local_path = f"temp_{file_name}"
    with open(local_path, "wb") as f:
        f.write(fh.read())
    return local_path

def parse_invoice(local_path):
    """
    Extracts text from the PDF and attempts to parse out fields.
    Falls back to default values for the POC if specific fields aren't found.
    """
    try:
        reader = PdfReader(local_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
            
        print(f"--- Extracted Text Preview ---\n{text[:200]}...\n------------------------------")
        
        # Simple Regex attempts
        patient_name = "Unknown Patient"
        policy_number = "UNKNOWN-POLICY"
        insurance_company = "Bupa" # Defaulting for POC
        
        name_match = re.search(r'(?i)Patient Name:\s*(.*)', text)
        if name_match:
            patient_name = name_match.group(1).strip()
            
        policy_match = re.search(r'(?i)Policy Number:\s*([A-Z0-9\-]+)', text)
        if policy_match:
            policy_number = policy_match.group(1).strip()
            
        # Construct the payload matching our FastAPI ClaimRequest schema
        payload = {
            "patient_name": patient_name,
            "patient_dob": "1980-01-01", # Placeholder for POC
            "insurance_company_name": insurance_company,
            "policy_number": policy_number,
            "auth_code": "AUTH-PENDING",
            "treatment_date": "2026-07-04",
            "procedures": [
                {
                    "procedure_code": "20600",
                    "description": "Initial Consultation",
                    "fee": 150.00
                }
            ]
        }
        return payload
    except Exception as e:
        print(f"Error parsing PDF {local_path}: {e}")
        return None

def poll_drive():
    """Main polling loop to watch the Drive folder."""
    print("Starting Drive Watcher...")
    service = authenticate_drive()
    if not service:
        return
        
    # In a real app, this would be a persistent database table of processed IDs
    processed_files = set() 
    
    while True:
        print("Polling Google Drive for new invoices...")
        items = list_invoices(service)
        
        for item in items:
            if item['id'] not in processed_files:
                print(f"Found new invoice: {item['name']} (ID: {item['id']})")
                
                # 1. Download the PDF
                local_path = download_invoice(service, item['id'], item['name'])
                
                # 2. Extract Data
                print(f"Parsing data from {local_path}...")
                claim_payload = parse_invoice(local_path)
                
                # 3. Post to our FastAPI endpoint
                if claim_payload:
                    print(f"Ready to POST parsed data to http://localhost:8000/api/claims")
                    try:
                        response = requests.post("http://localhost:8000/api/claims", json=claim_payload)
                        if response.status_code == 200:
                            print(f"Successfully submitted claim: {response.json()}")
                        else:
                            print(f"Failed to submit claim: {response.text}")
                    except Exception as e:
                        print(f"Error connecting to FastAPI: {e}")
                else:
                    print("Skipping POST due to parsing failure.")
                
                # Mark as processed
                processed_files.add(item['id'])
                
                # Cleanup local file
                if os.path.exists(local_path):
                    os.remove(local_path)
                    
        time.sleep(15) # Poll every 15 seconds

if __name__ == '__main__':
    poll_drive()
