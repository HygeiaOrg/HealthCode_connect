"""Deterministic PDF ingestion: extract text with pypdf, map labelled lines to
the MedicalInvoice shape, hand the result to the validation engine. No OCR, no
models: the demo PDFs (and any practice-system export) are text-based with
one 'Label: value' pair per line, the same format scripts/gen_sample_pdfs.py
renders, so parsing is a pure label lookup."""
from __future__ import annotations

import io
import re

from pypdf import PdfReader

from .engine import load_dictionaries

# PDF label -> dotted path into MedicalInvoice. Single source of truth shared
# with scripts/gen_sample_pdfs.py (which imports LABELS to render).
LABELS: dict[str, str] = {
    "Invoice Number": "invoice_number",
    "Invoice Date": "invoice_date",
    "Currency": "currency",
    "Practice Name": "practice.name",
    "Practice Address": "practice.address_line1",
    "Practice Postcode": "practice.postcode",
    "Patient First Name": "patient.first_name",
    "Patient Surname": "patient.surname",
    "Date of Birth": "patient.date_of_birth",
    "Sex": "patient.sex",
    "Patient Address": "patient.address_line1",
    "Patient Postcode": "patient.postcode",
    "NHS Number": "patient.nhs_number",
    "Insurer": "policy.insurer_id",
    "Membership Number": "policy.membership_number",
    "Pre-authorisation": "policy.pre_authorisation",
    "Specialist Name": "provider.specialist_name",
    "GMC Number": "provider.gmc_number",
    "Payee Provider": "provider.payee_provider_id",
    "Treatment Site": "provider.treatment_site_id",
    "Care Setting": "episode.care_setting",
    "Treatment Date": "episode.treatment_date",
    "Admission Date": "episode.admission_date",
    "Discharge Date": "episode.discharge_date",
    "Diagnosis Codes": "episode.diagnoses",
    "Procedure Codes": "episode.procedures",
    "Net Total": "totals.net",
    "VAT Total": "totals.vat",
    "Gross Total": "totals.gross",
}
LIST_PATHS = {"episode.diagnoses", "episode.procedures"}
NUMBER_PATHS = {"totals.net", "totals.vat", "totals.gross"}


def _set_path(obj: dict, dotted: str, value) -> None:
    parts = dotted.split(".")
    cur = obj
    for part in parts[:-1]:
        cur = cur.setdefault(part, {})
    cur[parts[-1]] = value


def _number(raw: str) -> float | None:
    cleaned = raw.replace("£", "").replace(",", "").strip()
    try:
        return round(float(cleaned), 2)
    except ValueError:
        return None


def _insurer_alias_map() -> dict[str, str]:
    insurers = load_dictionaries().insurers
    aliases: dict[str, str] = {}
    for iid, entry in insurers.items():
        aliases[iid.lower()] = iid
        aliases[entry["name"].lower()] = iid
    return aliases


def extract_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def parse_invoice_text(text: str) -> dict:
    """Labelled lines -> MedicalInvoice dict. Unknown lines are ignored;
    missing labels simply leave fields absent for the structural layer to flag."""
    invoice: dict = {}
    charges: list[dict] = []
    aliases = _insurer_alias_map()

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        label, _, raw_value = line.partition(":")
        label = label.strip()
        value = raw_value.strip()
        if not value:
            continue

        if label == "Charge":
            parts = [p.strip() for p in value.split("|")]
            if len(parts) == 5:
                qty = _number(parts[2])
                fee = _number(parts[3])
                vat = _number(parts[4])
                if qty is not None and fee is not None and vat is not None:
                    charges.append({
                        "service_code": parts[0],
                        "description": parts[1],
                        "quantity": int(qty),
                        "unit_fee": fee,
                        "vat_rate": vat,
                    })
            continue

        path = LABELS.get(label)
        if path is None:
            continue
        if path in LIST_PATHS:
            _set_path(invoice, path, [c.strip().upper() for c in value.split(",") if c.strip()])
        elif path in NUMBER_PATHS:
            num = _number(value)
            if num is not None:
                _set_path(invoice, path, num)
        elif path == "policy.insurer_id":
            _set_path(invoice, path, aliases.get(value.lower(), value))
        else:
            _set_path(invoice, path, value)

    if charges:
        invoice["lines"] = charges
    # Lists default to empty so the cross-field layer (not a crash) judges them.
    if "episode" in invoice:
        invoice["episode"].setdefault("diagnoses", [])
        invoice["episode"].setdefault("procedures", [])
        invoice["episode"].setdefault("admission_date", None)
        invoice["episode"].setdefault("discharge_date", None)
    return invoice


def ingest_pdf(pdf_bytes: bytes) -> dict:
    """Bytes -> MedicalInvoice dict. Raises ValueError if the PDF carries no
    recognisable invoice fields at all."""
    text = extract_text(pdf_bytes)
    invoice = parse_invoice_text(text)
    if not invoice:
        raise ValueError("no recognisable invoice fields in PDF text")
    return invoice
