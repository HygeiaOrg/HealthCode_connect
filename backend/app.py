from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import datetime
import json
import os
import uuid
from dotenv import load_dotenv
from xero_python.accounting import Invoices, Invoice, LineItem

# Load environment variables
load_dotenv()

# Import our Xero client helper
from xero_client import get_accounting_api, test_connection
import xero_sync

class ClaimProcedure(BaseModel):
    procedure_code: str
    description: str
    fee: float

class ClaimRequest(BaseModel):
    patient_name: str
    patient_dob: str
    insurance_company_name: str # The name of the insurer in Xero (e.g., 'Bupa')
    insurer_email: Optional[str] = None # Enables contact upsert-by-email in Xero
    policy_number: str
    auth_code: str
    treatment_date: str
    procedures: List[ClaimProcedure]

class PaymentRequest(BaseModel):
    amount: float
    reference: Optional[str] = None

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
    Phase 1: Mirrors a medical claim into Xero as an invoice, after a
    deterministic validation gate.

    The gate maps the claim onto a partial MedicalInvoice (patient name/DOB,
    policy + auth code, treatment date, charge lines and totals) and runs the
    full validation engine. Blocks the claim form does not collect — practice
    and provider details, patient address/sex, ICD-10/CCSD coding, care
    setting — are left absent and issues on them are suppressed, so the gate
    only rejects on data the claim actually carries (see xero_sync.claim_issues).
    Any severity=="error" issue returns 422 and nothing is written to Xero.

    In Phase 2, this will also submit to the Healthcode Clearing Services API.
    """
    issues = xero_sync.claim_issues(request.model_dump())
    if any(i["severity"] == "error" for i in issues):
        return JSONResponse(status_code=422, content={"valid": False, "issues": issues})

    try:
        accounting_api = xero_sync.get_api()

        # 1. (Future Phase) Submit to Healthcode API and get a HC reference
        healthcode_ref = "HC-PENDING"

        # 2. Mirror into Xero as an Invoice
        contact = xero_sync.upsert_contact(
            accounting_api, request.insurance_company_name, request.insurer_email
        )

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
        created_invoices = accounting_api.create_invoices(
            xero_tenant_id="", invoices=invoices, idempotency_key=str(uuid.uuid4())
        )

        if created_invoices and created_invoices.invoices:
            created_inv = created_invoices.invoices[0]
            return {
                "message": "Claim successfully mirrored to Xero",
                "healthcode_status": "pending_implementation",
                "xero_invoice_id": created_inv.invoice_id,
                "xero_invoice_number": created_inv.invoice_number
            }
        else:
            raise HTTPException(status_code=502, detail="Xero returned no created invoice")

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=502, detail="Xero error while creating the invoice")


# ---- contract endpoints (shared-api-contract.json) ----

def _fetch_xero_invoice(api, invoice_id: str):
    """404 on a missing/unknown invoice; the caller owns other Xero errors."""
    try:
        res = api.get_invoice(xero_sync.TENANT, invoice_id)
    except Exception:
        raise HTTPException(status_code=404, detail="invoice not found in Xero")
    if not res or not res.invoices:
        raise HTTPException(status_code=404, detail="invoice not found in Xero")
    return res.invoices[0]


@app.get("/invoices")
def list_invoices(payer_type: Optional[str] = None, status: Optional[str] = None,
                  q: Optional[str] = None):
    """
    Contract GET /invoices. Live Xero data when reachable, seeds.json otherwise.
    frontend/src/api/client.ts expects a bare Invoice[] (not an envelope), so
    provenance travels per-invoice in the contract's "source" field
    ("xero" | "seed").
    """
    try:
        records = xero_sync.fetch_invoices(xero_sync.get_api())
    except Exception:
        records = xero_sync.load_seeds()
    return xero_sync.filter_invoices(records, payer_type=payer_type, status=status, q=q)


@app.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: str):
    """Contract GET /invoices/{id}: Xero first, seeds fallback, else 404."""
    try:
        api = xero_sync.get_api()
        res = api.get_invoice(xero_sync.TENANT, invoice_id)
        if res and res.invoices:
            return xero_sync.map_invoice(res.invoices[0])
    except Exception:
        pass
    for record in xero_sync.load_seeds():
        if invoice_id in (record.get("id"), record.get("invoice_number")):
            return record
    raise HTTPException(status_code=404, detail="invoice not found")


@app.post("/invoices/{invoice_id}/record-payment")
def record_payment(invoice_id: str, body: PaymentRequest):
    """
    Record an insurer payment against a Xero invoice. Drafts are walked to
    AUTHORISED first; Xero flips the status to PAID itself once payments
    cover the total.
    """
    try:
        api = xero_sync.get_api()
    except Exception:
        raise HTTPException(status_code=502, detail="Xero is not reachable")
    inv = _fetch_xero_invoice(api, invoice_id)
    try:
        if inv.status in ("DRAFT", "SUBMITTED"):
            inv = xero_sync.authorise(api, invoice_id, inv.status)
        amount_due = float(inv.amount_due or 0)
        if body.amount > amount_due + 1e-9:
            raise HTTPException(
                status_code=422,
                detail=f"amount {body.amount:.2f} exceeds amount due {amount_due:.2f}",
            )
        payment_id = xero_sync.pay(api, invoice_id, body.amount, body.reference)
        inv = api.get_invoice(xero_sync.TENANT, invoice_id).invoices[0]
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=502, detail="Xero error while recording the payment")
    return {
        "invoice_id": inv.invoice_id,
        "status": inv.status,
        "amount_paid": float(inv.amount_paid or 0),
        "amount_due": float(inv.amount_due or 0),
        "fully_paid_on": str(inv.fully_paid_on_date)[:10] if getattr(inv, "fully_paid_on_date", None) else None,
        "payment_id": payment_id,
    }


@app.post("/invoices/{invoice_id}/submit")
def submit_invoice(invoice_id: str):
    """Contract draft -> at_medserv: Xero DRAFT -> SUBMITTED."""
    try:
        api = xero_sync.get_api()
    except Exception:
        raise HTTPException(status_code=502, detail="Xero is not reachable")
    inv = _fetch_xero_invoice(api, invoice_id)
    if inv.status == "DRAFT":
        try:
            api.update_invoice(
                xero_sync.TENANT, invoice_id,
                invoices=Invoices(invoices=[Invoice(status="SUBMITTED")]),
            )
            inv = api.get_invoice(xero_sync.TENANT, invoice_id).invoices[0]
        except Exception:
            raise HTTPException(status_code=502, detail="Xero error while submitting the invoice")
    elif inv.status != "SUBMITTED":
        raise HTTPException(status_code=422, detail=f"invoice is {inv.status}, not a draft")
    return xero_sync.map_invoice(inv)


@app.get("/xero/health")
def xero_health():
    """Connection probe that never raises; the UI renders the error string."""
    try:
        api = xero_sync.get_api()
        orgs = api.get_organisations(xero_tenant_id=xero_sync.TENANT)
        name = orgs.organisations[0].name if orgs and orgs.organisations else None
        if name:
            return {"connected": True, "org_name": name, "error": None}
        return {"connected": False, "org_name": None, "error": "no organisations returned"}
    except Exception as e:
        return {"connected": False, "org_name": None, "error": str(e)[:200]}
