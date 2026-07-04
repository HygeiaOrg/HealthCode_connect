from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our Xero client helper
from xero_client import get_accounting_api, test_connection

app = FastAPI(title="HealthCode Connect API POC")

# Enable CORS so the frontend can call this backend easily
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    # Show if Xero credentials are configured
    xero_configured = bool(os.getenv("CA2FA153D004D76A7F335D6C1E3A04B") and os.getenv("XERO_CLIENT_SECRET"))
    return {
        "message": "HealthCode Connect Backend is running!",
        "xero_integration_configured": xero_configured
    }

@app.get("/items")
def get_items():
    # Load dummy dataset from seeds.json (or sync from Xero in the future)
    seeds_path = os.path.join(os.path.dirname(__file__), "seeds.json")
    try:
        with open(seeds_path, "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return []

@app.get("/xero/status")
def get_xero_status():
    """
    Check connection status with Xero.
    """
    res = test_connection()
    if res["success"]:
        return {
            "status": "connected",
            "organisation": res["organisation_name"],
            "organisation_id": res["organisation_id"]
        }
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to connect to Xero: {res['error']}"
        )

@app.get("/xero/invoices")
def get_xero_invoices():
    """
    Fetch invoices from Xero.
    """
    try:
        accounting_api = get_accounting_api()
        # Fetch invoices (xero_tenant_id is empty string for Custom Connections)
        invoices = accounting_api.get_invoices(xero_tenant_id="")
        
        # Format response
        result = []
        if invoices and invoices.invoices:
            for inv in invoices.invoices:
                result.append({
                    "invoice_id": inv.invoice_id,
                    "invoice_number": inv.invoice_number,
                    "contact_name": inv.contact.name if inv.contact else None,
                    "date": str(inv.date) if inv.date else None,
                    "due_date": str(inv.due_date) if inv.due_date else None,
                    "total": float(inv.total) if inv.total else 0.0,
                    "amount_due": float(inv.amount_due) if inv.amount_due else 0.0,
                    "status": inv.status
                })
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/xero/contacts")
def get_xero_contacts():
    """
    Fetch contacts from Xero.
    """
    try:
        accounting_api = get_accounting_api()
        # Fetch contacts
        contacts = accounting_api.get_contacts(xero_tenant_id="")
        
        result = []
        if contacts and contacts.contacts:
            for contact in contacts.contacts:
                result.append({
                    "contact_id": contact.contact_id,
                    "name": contact.name,
                    "email_address": contact.email_address,
                    "contact_status": contact.contact_status
                })
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
