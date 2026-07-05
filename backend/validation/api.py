"""FastAPI router exposing the validator. Wire-up in app.py:

    from validation.api import router as validation_router
    app.include_router(validation_router)
"""
from fastapi import APIRouter, File, UploadFile

from .engine import is_valid, validate_invoice
from .pdf_ingest import ingest_pdf

router = APIRouter(tags=["validation"])


def _wire(issues) -> list[dict]:
    return [
        {**i.to_contract(), "severity": i.severity, "rule": i.rule_id, "path": i.path}
        for i in issues
    ]


@router.post("/invoices/validate")
def validate(invoice: dict) -> dict:
    issues = validate_invoice(invoice)
    return {"valid": is_valid(issues), "issues": _wire(issues)}


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
    issues = validate_invoice(invoice)
    return {
        "filename": file.filename,
        "valid": is_valid(issues),
        "parsed": invoice,
        "issues": _wire(issues),
    }
