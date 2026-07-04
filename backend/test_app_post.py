from app import submit_claim, ClaimRequest, ClaimProcedure

payload = {
    "patient_name": "Test Patient",
    "patient_dob": "1980-01-01",
    "insurance_company_name": "Bupa",
    "policy_number": "12345",
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

req = ClaimRequest(**payload)
try:
    res = submit_claim(req)
    print("Success:", res)
except Exception as e:
    import traceback
    traceback.print_exc()
