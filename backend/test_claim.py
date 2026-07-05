import json
from fastapi.testclient import TestClient
from app import app

def test_api_claim():
    client = TestClient(app)
    
    payload = {
        "patient_name": "Jane Smith",
        "patient_dob": "1985-06-15",
        "insurance_company_name": "Bupa",
        "policy_number": "BUP-987654321",
        "auth_code": "AUTH-XYZ-123",
        "treatment_date": "2026-07-04",
        "procedures": [
            {
                "procedure_code": "20140",
                "description": "Initial Consultation",
                "fee": 150.0
            }
        ]
    }

    print("Sending ClaimRequest to /api/claims...")
    response = client.post("/api/claims", json=payload)
    
    print(f"Status Code: {response.status_code}")
    try:
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print("Response Text:", response.text)

if __name__ == "__main__":
    test_api_claim()
