"""FastAPI router exposing the validator. Wire-up in app.py:

    from validation.api import router as validation_router
    app.include_router(validation_router)
"""
from fastapi import APIRouter, File, UploadFile

from . import dedup
from .dedup import load_ledger
from .engine import is_valid, validate_invoice
from .pdf_ingest import ingest_pdf

router = APIRouter(tags=["validation"])


def _wire(issues) -> list[dict]:
    return [
        {**i.to_contract(), "severity": i.severity, "rule": i.rule_id, "path": i.path}
        for i in issues
    ]


def _run_engine(invoice: dict):
    # Number uniqueness (cross.duplicate_number) is a submission gate: it runs
    # once the bill is otherwise clean, so re-checking an existing ledger
    # record surfaces its content errors, not a collision with its own number.
    issues = validate_invoice(invoice)
    if is_valid(issues):
        issues = validate_invoice(invoice, ledger=load_ledger())
    return issues


def _dedup_issue(invoice: dict) -> dict | None:
    # dedup.INDEX is looked up per request so tests can swap in a fresh index.
    earlier = dedup.INDEX.check(invoice)
    if earlier is None:
        return None
    return {
        "field": "Invoice",
        "error": f"Content duplicates invoice {earlier}",
        "solution": f"An identical claim (same patient, episode and totals) was "
                    f"already raised as {earlier}; chase or credit the original "
                    "instead of resubmitting it under a new number.",
        "severity": "error",
        "rule": "dedup.duplicate_claim",
        "path": "invoice_number",
    }


@router.post("/invoices/validate")
def validate(invoice: dict) -> dict:
    issues = _run_engine(invoice)
    wire = _wire(issues)
    dup = _dedup_issue(invoice)
    if dup is not None:
        wire.append(dup)
    return {"valid": dup is None and is_valid(issues), "issues": wire}


@router.post("/invoices/upload")
async def upload(file: UploadFile = File(...)) -> dict:
    data = await file.read()
    try:
        invoice = ingest_pdf(data)
    except Exception:
        return {
            "filename": file.filename,
            "valid": False,
            "parsed": None,
            "issues": [{
                "field": "Document",
                "error": "Could not read an invoice from this PDF",
                "solution": "Upload a text-based invoice PDF exported from the practice system; scanned images are not supported in the demo.",
                "severity": "error",
                "rule": "ingest.unreadable",
                "path": "",
            }],
        }
    issues = _run_engine(invoice)
    wire = _wire(issues)
    dup = _dedup_issue(invoice)
    if dup is not None:
        wire.append(dup)
    return {
        "filename": file.filename,
        "valid": dup is None and is_valid(issues),
        "parsed": invoice,
        "issues": wire,
    }
