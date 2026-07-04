from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import datetime
import json
import os
from dotenv import load_dotenv
from xero_python.accounting import Invoices, Invoice, Contact, LineItem

# Load environment variables
load_dotenv()

# Import our Xero client helper
from xero_client import get_accounting_api, test_connection

class ClaimProcedure(BaseModel):
    procedure_code: str
    description: str
    fee: float

class ClaimRequest(BaseModel):
    patient_name: str
    patient_dob: str
    insurance_company_name: str # The name of the insurer in Xero (e.g., 'Bupa')
    policy_number: str
    auth_code: str
    treatment_date: str
    procedures: List[ClaimProcedure]

# Deterministic medical-invoice validation engine (see validation/README in schema.json)
from validation.api import router as validation_router

app = FastAPI(title="HealthCode Connect API POC")
app.include_router(validation_router)

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
    xero_configured = bool(os.getenv("XERO_CLIENT_ID") and os.getenv("XERO_CLIENT_SECRET"))
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

@app.post("/api/claims")
def submit_claim(request: ClaimRequest):
    """
    Phase 1: Mirrors a medical claim into Xero as an invoice.
    In Phase 2, this will also submit to the Healthcode Clearing Services API.
    """
    try:
        accounting_api = get_accounting_api()
        
        # 1. (Future Phase) Submit to Healthcode API and get a HC reference
        healthcode_ref = "HC-PENDING" 
        
        # 2. Mirror into Xero as an Invoice
        contact = Contact(name=request.insurance_company_name)
        
        line_items = []
        for proc in request.procedures:
            # Construct the highly detailed description for easy reconciliation
            desc = (f"HC Ref: {healthcode_ref} | Date: {request.treatment_date} | "
                    f"Patient: {request.patient_name} | DOB: {request.patient_dob} | "
                    f"Policy: {request.policy_number} | Auth: {request.auth_code} | "
                    f"Procedure: {proc.procedure_code} ({proc.description})")
            
            line_item = LineItem(
                description=desc,
                quantity=1.0,
                unit_amount=proc.fee,
                account_code="200" # Default Sales Account in Xero
            )
            line_items.append(line_item)
            
        invoice = Invoice(
            type="ACCREC",
            contact=contact,
            line_items=line_items,
            date=datetime.date.today(),
            due_date=datetime.date.today() + datetime.timedelta(days=30),
            reference=f"{request.patient_name} - {request.policy_number}",
            status="DRAFT" # Draft for now so they can review, can change to AUTHORISED later
        )
        
        invoices = Invoices(invoices=[invoice])
        
        # Submit to Xero (xero_tenant_id is empty string for Custom Connections)
        created_invoices = accounting_api.create_invoices(xero_tenant_id="", invoices=invoices)
        
        if created_invoices and created_invoices.invoices:
            created_inv = created_invoices.invoices[0]
            return {
                "message": "Claim successfully mirrored to Xero",
                "healthcode_status": "pending_implementation",
                "xero_invoice_id": created_inv.invoice_id,
                "xero_invoice_number": created_inv.invoice_number
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create invoice in Xero")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
