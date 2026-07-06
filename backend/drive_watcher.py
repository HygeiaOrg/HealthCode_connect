import os
import time
import io
import json
import datetime
import os.path
import requests

from dotenv import load_dotenv

from validation.pdf_ingest import ingest_pdf
from validation.engine import load_dictionaries

load_dotenv(override=True)

# Configuration
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
API_URL = os.getenv("CLAIMS_API_URL", "http://localhost:8000")
STATE_PATH = os.path.join(os.path.dirname(__file__), ".watcher_state.json")

def authenticate_drive():
    """Authenticates and returns the Google Drive API service instance using OAuth 2.0 Desktop App flow."""
    # Google libs imported here so the mapping/state helpers stay importable
    # (e.g. in tests) without the google packages installed.
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

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
    """Lists all PDF files in the target Google Drive folder, following pagination."""
    folder_id = os.getenv('DRIVE_FOLDER_ID')
    if not folder_id:
        print("Error: DRIVE_FOLDER_ID environment variable not set in .env")
        return []

    query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
    items = []
    page_token = None
    try:
        while True:
            results = service.files().list(
                q=query, pageSize=100, pageToken=page_token,
                fields="nextPageToken, files(id, name, md5Checksum)").execute()
            items.extend(results.get('files', []))
            page_token = results.get('nextPageToken')
            if not page_token:
                break
        return items
    except Exception as e:
        print(f"Error listing files: {e}")
        return []

def download_invoice(service, file_id, file_name):
    """Downloads a file from Google Drive and returns its bytes."""
    from googleapiclient.http import MediaIoBaseDownload

    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print(f"Downloading {file_name}: {int(status.progress() * 100)}%.")
    return fh.getvalue()

def load_state():
    """Loads the persisted watcher state; missing or corrupt files start fresh."""
    try:
        with open(STATE_PATH) as f:
            state = json.load(f)
        if not isinstance(state, dict):
            raise ValueError("state is not a dict")
        return {
            "processed": list(state.get("processed", [])),
            "rejected": list(state.get("rejected", [])),
        }
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        return {"processed": [], "rejected": []}

def save_state(state):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)

def parse_invoice(file_bytes):
    """
    Extracts fields via the validation engine's PDF ingester and maps them onto
    the /api/claims ClaimRequest schema.
    Falls back to default values for the POC if specific fields aren't found.
    """
    try:
        invoice = ingest_pdf(file_bytes)
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return None
    return map_invoice_to_claim(invoice)

def map_invoice_to_claim(invoice):
    """Maps a parsed MedicalInvoice dict onto the ClaimRequest payload.
    Missing blocks degrade to the POC placeholders rather than crashing."""
    patient = invoice.get("patient") or {}
    policy = invoice.get("policy") or {}
    episode = invoice.get("episode") or {}
    totals = invoice.get("totals") or {}

    name_parts = [patient.get("first_name"), patient.get("surname")]
    patient_name = " ".join(p for p in name_parts if p) or "Unknown Patient"

    insurer_id = policy.get("insurer_id")
    insurance_company = "Bupa"  # Defaulting for POC
    if insurer_id:
        try:
            entry = load_dictionaries().insurers.get(insurer_id)
        except Exception:
            entry = None
        insurance_company = (entry or {}).get("name", insurer_id)

    treatment_date = (
        episode.get("admission_date")
        or episode.get("treatment_date")
        or invoice.get("invoice_date")
        or datetime.date.today().isoformat()
    )

    procedures = []
    for line in invoice.get("lines") or []:
        qty = line.get("quantity") or 1
        fee = line.get("unit_fee") or 0.0
        procedures.append({
            "procedure_code": line.get("service_code", "20600"),
            "description": line.get("description", "Initial Consultation"),
            "fee": round(qty * fee, 2),
        })
    if not procedures:
        procedures = [{
            "procedure_code": "20600",
            "description": "Initial Consultation",
            "fee": totals.get("net", 150.00),
        }]

    return {
        "patient_name": patient_name,
        "patient_dob": patient.get("date_of_birth", "1980-01-01"),
        "insurance_company_name": insurance_company,
        "policy_number": policy.get("membership_number", "UNKNOWN-POLICY"),
        "auth_code": policy.get("pre_authorisation") or "AUTH-PENDING",
        "treatment_date": treatment_date,
        "procedures": procedures,
    }

def poll_drive():
    """Main polling loop to watch the Drive folder."""
    print("Starting Drive Watcher...")
    service = authenticate_drive()
    if not service:
        return

    state = load_state()
    processed = set(state["processed"])
    rejected = set(state["rejected"])

    while True:
        print("Polling Google Drive for new invoices...")
        items = list_invoices(service)

        for item in items:
            # Dedup on content so a re-uploaded copy of the same invoice
            # (new file id) is still skipped; file id is the fallback.
            key = item.get('md5Checksum') or item['id']
            if key in processed or key in rejected:
                continue
            print(f"Found new invoice: {item['name']} (ID: {item['id']})")

            # 1. Download the PDF
            try:
                file_bytes = download_invoice(service, item['id'], item['name'])
            except Exception as e:
                print(f"Error downloading {item['name']}: {e} — will retry next cycle.")
                continue

            # 2. Extract Data
            print(f"Parsing data from {item['name']}...")
            claim_payload = parse_invoice(file_bytes)
            if not claim_payload:
                print("Skipping POST due to parsing failure — will retry next cycle.")
                continue

            # 3. Post to our FastAPI endpoint
            print(f"Ready to POST parsed data to {API_URL}/api/claims")
            try:
                response = requests.post(f"{API_URL}/api/claims", json=claim_payload)
            except Exception as e:
                print(f"Error connecting to FastAPI: {e} — will retry next cycle.")
                continue

            if response.status_code == 200:
                print(f"Successfully submitted claim: {response.json()}")
                processed.add(key)
                state["processed"] = sorted(processed)
                save_state(state)
            elif response.status_code == 422:
                # Validation gate rejection: retrying an invalid claim forever
                # is pointless, so record it and move on.
                print(f"Claim rejected by validation gate: {response.text}")
                rejected.add(key)
                state["rejected"] = sorted(rejected)
                save_state(state)
            else:
                print(f"Failed to submit claim ({response.status_code}): {response.text} — will retry next cycle.")

        time.sleep(15) # Poll every 15 seconds

if __name__ == '__main__':
    poll_drive()
