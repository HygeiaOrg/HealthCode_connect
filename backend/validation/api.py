"""FastAPI router exposing the validator. Wire-up in app.py:

    from validation.api import router as validation_router
    app.include_router(validation_router)
"""
from fastapi import APIRouter

from .engine import is_valid, validate_invoice

router = APIRouter(tags=["validation"])


@router.post("/invoices/validate")
def validate(invoice: dict) -> dict:
    issues = validate_invoice(invoice)
    return {
        "valid": is_valid(issues),
        "issues": [
            {**i.to_contract(), "severity": i.severity, "rule": i.rule_id, "path": i.path}
            for i in issues
        ],
    }
