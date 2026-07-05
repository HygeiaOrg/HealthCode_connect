"""Xero <-> contract glue: invoice mapping, payment plumbing, seeds fallback,
and the pre-Xero validation gate for claims.

Everything here takes an AccountingApi instance so tests can substitute a fake;
app.py obtains one via get_api(), which late-binds to xero_client so credentials
are only needed when a request actually reaches Xero.
"""
import datetime
import json
import os
import uuid

from xero_python.accounting import (
    Account, Contact, Contacts, HistoryRecord, HistoryRecords, Invoice, Invoices, Payment,
)

from validation.engine import load_dictionaries, validate_invoice

# Custom Connections address a single org; the SDK still wants the tenant arg.
TENANT = ""

SEEDS_PATH = os.path.join(os.path.dirname(__file__), "seeds.json")


def get_api():
    import xero_client
    return xero_client.get_accounting_api()


# ---------- claims validation gate ----------

# A ClaimRequest carries far less than a full MedicalInvoice: no practice or
# provider block, no patient sex/address/postcode, no ICD-10/CCSD coding and no
# care setting. We map what exists, run the full engine, then keep only issues
# rooted at paths the claim can actually populate — otherwise every claim would
# fail on blocks the form does not collect.
_MAPPED_PATHS = (
    "patient.first_name", "patient.surname", "patient.date_of_birth",
    "policy", "episode.treatment_date", "lines", "totals",
    "currency", "invoice_date",
)


def _resolve_insurer_id(name: str):
    insurers = load_dictionaries().insurers
    key = (name or "").strip().lower()
    if key in insurers:
        return key
    for iid, meta in insurers.items():
        if meta["name"].strip().lower() == key:
            return iid
    return None


def _claim_to_partial_invoice(claim: dict) -> dict:
    parts = (claim.get("patient_name") or "").strip().split()
    net = round(sum(float(p["fee"]) for p in claim.get("procedures") or []), 2)
    invoice = {
        "invoice_date": datetime.date.today().isoformat(),
        "currency": "GBP",
        "patient": {
            "first_name": parts[0] if parts else "",
            "surname": " ".join(parts[1:]) if len(parts) > 1 else "",
            "date_of_birth": claim.get("patient_dob"),
        },
        "policy": {
            "membership_number": claim.get("policy_number"),
            "pre_authorisation": claim.get("auth_code"),
        },
        "episode": {"treatment_date": claim.get("treatment_date")},
        "lines": [
            {
                "service_code": p["procedure_code"],
                "description": p["description"],
                "quantity": 1,
                "unit_fee": float(p["fee"]),
                "vat_rate": 0,
            }
            for p in claim.get("procedures") or []
        ],
        "totals": {"net": net, "vat": 0, "gross": net},
    }
    insurer_id = _resolve_insurer_id(claim.get("insurance_company_name") or "")
    if insurer_id:  # absent id -> structural.required on policy.insurer_id
        invoice["policy"]["insurer_id"] = insurer_id
    return invoice


def _path_is_mapped(path: str) -> bool:
    return any(
        path == p or path.startswith(p + ".") or path.startswith(p + "[")
        for p in _MAPPED_PATHS
    )


def claim_issues(claim: dict) -> list[dict]:
    """Validate a ClaimRequest through the invoice engine.

    Returns wire-shaped issues (field/error/solution/severity/rule/path)
    restricted to what the claim form maps; issues on unmapped blocks
    (practice, provider, diagnoses, care setting, patient address) are
    suppressed by design.
    """
    issues = validate_invoice(_claim_to_partial_invoice(claim))
    return [
        {**i.to_contract(), "severity": i.severity, "rule": i.rule_id, "path": i.path}
        for i in issues
        if _path_is_mapped(i.path)
    ]


# ---------- contacts ----------

def upsert_contact(api, name: str, email: str | None) -> Contact:
    """Reuse the contact matching this email, create one otherwise.

    Xero does not dedupe contacts by name, so without an email we fall back to
    a name-only Contact and let Xero resolve it at invoice creation.
    """
    if not email:
        return Contact(name=name)
    found = api.get_contacts(TENANT, where=f'EmailAddress=="{email}"')
    if found and found.contacts:
        return Contact(contact_id=found.contacts[0].contact_id)
    created = api.create_contacts(
        TENANT,
        contacts=Contacts(contacts=[Contact(name=name, email_address=email)]),
        idempotency_key=str(uuid.uuid4()),
    )
    return Contact(contact_id=created.contacts[0].contact_id)


# ---------- payments ----------

_account_code: str | None = None


def payment_account_code(api) -> str:
    """First ACTIVE bank/payments-enabled account; cached after one lookup."""
    global _account_code
    if _account_code is None:
        res = api.get_accounts(
            TENANT,
            where='Status=="ACTIVE" AND (Type=="BANK" OR EnablePaymentsToAccount==true)',
        )
        if not res or not res.accounts:
            raise RuntimeError("no payment-capable account in this Xero org")
        _account_code = res.accounts[0].code
    return _account_code


def authorise(api, invoice_id: str, current_status: str):
    """Walk DRAFT -> SUBMITTED -> AUTHORISED (Xero rejects skipped steps)."""
    steps = ["SUBMITTED", "AUTHORISED"] if current_status == "DRAFT" else ["AUTHORISED"]
    for status in steps:
        api.update_invoice(
            TENANT, invoice_id, invoices=Invoices(invoices=[Invoice(status=status)])
        )
    return api.get_invoice(TENANT, invoice_id).invoices[0]


def pay(api, invoice_id: str, amount: float, reference: str | None) -> str:
    payment = Payment(
        invoice=Invoice(invoice_id=invoice_id),
        account=Account(code=payment_account_code(api)),
        date=datetime.date.today(),
        amount=amount,
        reference=reference,
    )
    res = api.create_payment(TENANT, payment=payment, idempotency_key=str(uuid.uuid4()))
    return res.payments[0].payment_id


# ---------- Xero invoice -> contract Invoice ----------

def _iso(value) -> str | None:
    return str(value)[:10] if value else None


def _num(value) -> float:
    return float(value or 0)


def pipeline_status_of(inv) -> str:
    status = (inv.status or "").upper()
    if status == "SUBMITTED":
        return "at_medserv"
    if status == "AUTHORISED":
        paid = _num(inv.amount_paid)
        credited = _num(getattr(inv, "amount_credited", 0))
        return "insurer_query" if paid > 0 or credited > 0 else "with_insurer"
    if status == "PAID":
        return "paid"
    if status == "VOIDED":
        return "rejected"
    return "draft"


def map_invoice(inv) -> dict:
    """Best-effort projection of a Xero ACCREC invoice onto the contract shape.

    Xero has no native home for some contract fields: patient_ref rides in the
    invoice reference, insurer_name is the contact name, and middleman_fee is
    re-derived as the 3% private clearing fee (0 for NHS) like gen_seeds.py.
    """
    contact_name = inv.contact.name if inv.contact else ""
    payer_type = "nhs" if "nhs" in (contact_name or "").lower() else "private_insurer"
    total = _num(inv.total)
    status = pipeline_status_of(inv)
    issued = _iso(inv.date) or datetime.date.today().isoformat()
    paid_date = _iso(getattr(inv, "fully_paid_on_date", None))
    line_items = getattr(inv, "line_items", None) or []
    timeline = [{"stage": "draft", "at": issued}]
    if status != "draft":
        timeline.append({"stage": status, "at": paid_date or issued})
    return {
        "id": inv.invoice_id,
        "invoice_number": inv.invoice_number or "",
        "payer_type": payer_type,
        "insurer_name": contact_name or "",
        "patient_ref": inv.reference or "",
        "description": (line_items[0].description or "") if line_items else "",
        "total": total,
        "amount_due": _num(inv.amount_due),
        "middleman_fee": 0.0 if payer_type == "nhs" else round(total * 0.03, 2),
        "currency": "GBP",
        "issued_date": issued,
        "submitted_date": None if status == "draft" else issued,
        "expected_payment_date": _iso(inv.due_date),
        "paid_date": paid_date,
        "pipeline_status": status,
        "query_reason": None,
        "last_chased_at": None,
        "timeline": timeline,
        "validation_issues": [],
        "source": "xero",
    }


def fetch_invoices(api) -> list[dict]:
    res = api.get_invoices(TENANT, where='Type=="ACCREC"', order="Date DESC", page=1)
    return [map_invoice(i) for i in (res.invoices if res and res.invoices else [])]


def add_history(api, invoice_id: str, details: str) -> None:
    """Attach a note to the invoice's History & Notes tab in Xero.

    Chase/reply/resubmit have no status transition of their own in Xero, so
    the audit note is their real-world equivalent.
    """
    records = HistoryRecords(history_records=[HistoryRecord(details=details[:250])])
    api.create_invoice_history(
        TENANT, invoice_id, history_records=records, idempotency_key=str(uuid.uuid4())
    )


# ---------- seeds fallback ----------

def load_seeds() -> list[dict]:
    with open(SEEDS_PATH) as f:
        return json.load(f)


def filter_invoices(records: list[dict], payer_type=None, status=None, q=None) -> list[dict]:
    out = records
    if payer_type:
        out = [r for r in out if r.get("payer_type") == payer_type]
    if status:
        out = [r for r in out if r.get("pipeline_status") == status]
    if q:
        ql = q.lower()
        out = [
            r for r in out
            if ql in (r.get("invoice_number") or "").lower()
            or ql in (r.get("patient_ref") or "").lower()
            or ql in (r.get("insurer_name") or "").lower()
        ]
    return out
