import os
import json
import uuid
import datetime
from dotenv import load_dotenv
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

load_dotenv()

HEALTHCODE_CLIENT_ID = os.getenv("HEALTHCODE_CLIENT_ID", "HAP0SBPJ_mial_connect")
HEALTHCODE_CLIENT_SECRET = os.getenv("HEALTHCODE_CLIENT_SECRET", "ALNXvqsRUXA5acNhXnchaVqonZI6eBCxMRgOX7WU68fkSnaUujsn3Hhrt2GLY_xAdIz8TTr0c7G-Gm_wBS5chw0")
HEALTHCODE_TOKEN_URL = os.getenv("HEALTHCODE_TOKEN_URL", "https://auth.uat.healthcode.co.uk/token")
HEALTHCODE_SITE_ID = os.getenv("HEALTHCODE_SITE_ID", "HC15431")

def get_healthcode_session():
    """
    Initializes and returns an OAuth2Session for Healthcode API.
    Uses Client Credentials flow.
    """
    if not HEALTHCODE_CLIENT_ID or not HEALTHCODE_CLIENT_SECRET:
        print("Healthcode OAuth credentials not configured. Running in mock mode.")
        return None
        
    client = BackendApplicationClient(client_id=HEALTHCODE_CLIENT_ID)
    oauth = OAuth2Session(client=client)
    
    try:
        # Fetch token
        oauth.fetch_token(
            token_url=HEALTHCODE_TOKEN_URL,
            client_id=HEALTHCODE_CLIENT_ID,
            client_secret=HEALTHCODE_CLIENT_SECRET
        )
        print("Successfully authenticated with Healthcode OAuth!")
        return oauth
    except Exception as e:
        print(f"Failed to authenticate with Healthcode: {e}")
        return None

def generate_fhir_claim(request) -> dict:
    """
    Generates a mock FHIR R4 Claim resource from the ClaimRequest.
    """
    items = []
    for i, proc in enumerate(request.procedures):
        items.append({
            "sequence": i + 1,
            "productOrService": {
                "coding": [{"code": proc.procedure_code, "display": proc.description}]
            },
            "net": {"value": proc.fee, "currency": "GBP"}
        })

    fhir_claim = {
        "resourceType": "Claim",
        "status": "active",
        "type": {
            "coding": [{"system": "http://terminology.hl7.org/CodeSystem/claim-type", "code": "professional"}]
        },
        "use": "claim",
        "patient": {
            "display": request.patient_name
        },
        "created": datetime.datetime.now().isoformat(),
        "insurance": [{
            "sequence": 1,
            "focal": True,
            "coverage": {
                "display": request.insurance_company_name
            }
        }],
        "item": items,
        "extension": [
            {
                "url": "http://hl7.org/fhir/StructureDefinition/patient-birthTime",
                "valueDateTime": request.patient_dob
            },
            {
                "url": "http://hl7.org/fhir/StructureDefinition/insurance-policy-number",
                "valueString": request.policy_number
            },
            {
                "url": "http://hl7.org/fhir/StructureDefinition/insurance-auth-code",
                "valueString": request.auth_code
            }
        ]
    }
    return fhir_claim

def submit_to_healthcode(request) -> dict:
    """
    Simulates submitting a FHIR Claim to the Healthcode Clearing Services API.
    Returns a mock Healthcode reference and the status.
    """
    fhir_payload = generate_fhir_claim(request)
    
    session = get_healthcode_session()
    
    if session:
        # In a real scenario, we would use the authenticated session to POST to the Healthcode API
        print("--- Submitting FHIR Payload to Healthcode via OAuth ---")
        headers = {}
        if HEALTHCODE_SITE_ID:
            headers["SU-SiteId"] = HEALTHCODE_SITE_ID
        # e.g., response = session.post("https://api.healthcode.co.uk/claims", json=fhir_payload, headers=headers)
    else:
        print("--- [Mock] Submitting FHIR Payload to Healthcode ---")
        
    print(json.dumps(fhir_payload, indent=2))
    print("--------------------------------------------------")
    
    # Simulate a successful response from Healthcode API
    hc_reference = f"HC-{uuid.uuid4().hex[:8].upper()}"
    
    return {
        "success": True,
        "reference": hc_reference,
        "status": "submitted"
    }
