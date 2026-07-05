#!/usr/bin/env python3
"""Generate demo invoice PDFs: 5 valid, 5 with known errors.

Each PDF renders a MedicalInvoice in the exact 'Label: value' format that
validation/pdf_ingest.py parses (LABELS is imported, so the two cannot drift).
Before writing, every payload is self-checked against the engine: valid samples
must produce zero issues, invalid samples must produce exactly the expected
rule families. Output: backend/samples/*.pdf + manifest.json.

Run from backend/:  .venv/bin/python scripts/gen_sample_pdfs.py
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

from fpdf import FPDF

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from validation import validate_invoice  # noqa: E402
from validation.pdf_ingest import LABELS, ingest_pdf, parse_invoice_text  # noqa: E402
from validation.engine import get_path  # noqa: E402

PATH_TO_LABEL = {path: label for label, path in LABELS.items()}
INSURER_DISPLAY = {"bupa": "Bupa", "axa_health": "AXA Health", "aviva": "Aviva",
                   "vitality": "Vitality", "wpa": "WPA", "nhs_england": "NHS England"}


def render_lines(inv: dict) -> list[str]:
    lines = ["MEDICAL INVOICE", ""]
    order = [
        "invoice_number", "invoice_date", "currency",
        "practice.name", "practice.address_line1", "practice.postcode",
        "patient.first_name", "patient.surname", "patient.date_of_birth", "patient.sex",
        "patient.address_line1", "patient.postcode", "patient.nhs_number",
        "policy.insurer_id", "policy.membership_number", "policy.pre_authorisation",
        "provider.specialist_name", "provider.gmc_number", "provider.payee_provider_id",
        "provider.treatment_site_id",
        "episode.care_setting", "episode.treatment_date", "episode.admission_date",
        "episode.discharge_date", "episode.diagnoses", "episode.procedures",
    ]
    for path in order:
        value = get_path(inv, path)
        if value in (None, "", []):
            continue
        if isinstance(value, list):
            value = ", ".join(value)
        elif path == "policy.insurer_id":
            value = INSURER_DISPLAY.get(value, value)
        lines.append(f"{PATH_TO_LABEL[path]}: {value}")
    for line in inv.get("lines", []):
        lines.append(
            f"Charge: {line['service_code']} | {line['description']} | "
            f"{line['quantity']} | {line['unit_fee']:.2f} | {line['vat_rate']}"
        )
    totals = inv.get("totals", {})
    for key, label in [("net", "Net Total"), ("vat", "VAT Total"), ("gross", "Gross Total")]:
        if key in totals:
            lines.append(f"{label}: {totals[key]:.2f}")
    return lines


def write_pdf(inv: dict, path: Path) -> None:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "MEDICAL INVOICE", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    for line in render_lines(inv)[2:]:
        pdf.cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(path))


def base_invoice(**over) -> dict:
    inv = {
        "invoice_number": "INV-2026-9001",
        "invoice_date": "2026-07-04",
        "currency": "GBP",
        "practice": {"name": "Harley Street Practice Ltd", "address_line1": "12 Harley Street, London", "postcode": "W1G 9PF"},
        "patient": {"first_name": "Amelia", "surname": "Hart", "date_of_birth": "1981-03-14", "sex": "F",
                    "address_line1": "4 Elm Grove, London", "postcode": "SW1A 1AA", "nhs_number": None},
        "policy": {"insurer_id": "bupa", "membership_number": "MB1234567", "pre_authorisation": "12345678"},
        "provider": {"specialist_name": "Dr T. Okafor", "gmc_number": "4479761",
                     "payee_provider_id": "PP-4402", "treatment_site_id": "SITE-021"},
        "episode": {"care_setting": "outpatient", "treatment_date": "2026-06-20",
                    "admission_date": None, "discharge_date": None,
                    "diagnoses": ["M17.1"], "procedures": ["0101A"]},
        "lines": [{"service_code": "CONS-INIT", "description": "Initial consultation",
                   "quantity": 1, "unit_fee": 250.0, "vat_rate": 0}],
        "totals": {"net": 250.0, "vat": 0, "gross": 250.0},
    }
    inv = copy.deepcopy(inv)
    for dotted, value in over.items():
        parts = dotted.split(".")
        cur = inv
        for p in parts[:-1]:
            cur = cur[p]
        cur[parts[-1]] = value
    return inv


def money(inv: dict, fee: float) -> None:
    inv["lines"][0]["unit_fee"] = fee
    inv["totals"] = {"net": fee, "vat": 0, "gross": fee}


def build_samples() -> list[tuple[str, dict, bool, set[str]]]:
    """(filename, invoice, expect_valid, expected_rule_ids)"""
    samples: list[tuple[str, dict, bool, set[str]]] = []

    # ---- five valid invoices across insurers and settings ----
    v1 = base_invoice(**{"invoice_number": "INV-2026-9001"})
    samples.append(("valid_01_bupa_consult.pdf", v1, True, set()))

    v2 = base_invoice(**{
        "invoice_number": "INV-2026-9002",
        "policy.insurer_id": "wpa", "policy.membership_number": "48291065", "policy.pre_authorisation": "552901",
        "provider.treatment_site_id": "SITE-087",
        "episode.care_setting": "day_case", "episode.diagnoses": ["M65.3"], "episode.procedures": ["T6810"],
    })
    v2["lines"] = [{"service_code": "PROC-MINOR", "description": "Trigger finger release",
                    "quantity": 1, "unit_fee": 700.0, "vat_rate": 0}]
    v2["totals"] = {"net": 700.0, "vat": 0, "gross": 700.0}
    samples.append(("valid_02_wpa_daycase.pdf", v2, True, set()))

    v3 = base_invoice(**{
        "invoice_number": "INV-2026-9003",
        "policy.insurer_id": "aviva", "policy.pre_authorisation": "918274",
        "provider.treatment_site_id": "SITE-134",
        "episode.care_setting": "day_case", "episode.diagnoses": ["K21.9"], "episode.procedures": ["G4500"],
    })
    v3["lines"] = [{"service_code": "PROC-MAJOR", "description": "Diagnostic gastroscopy",
                    "quantity": 1, "unit_fee": 650.0, "vat_rate": 0}]
    v3["totals"] = {"net": 650.0, "vat": 0, "gross": 650.0}
    samples.append(("valid_03_aviva_gastroscopy.pdf", v3, True, set()))

    v4 = base_invoice(**{
        "invoice_number": "INV-2026-9004",
        "policy.insurer_id": "vitality", "policy.pre_authorisation": "VH662140",
        "episode.diagnoses": ["D22.9"], "episode.procedures": ["S0620"],
    })
    v4["lines"] = [{"service_code": "PROC-MINOR", "description": "Excision of skin lesion",
                    "quantity": 1, "unit_fee": 450.0, "vat_rate": 0}]
    v4["totals"] = {"net": 450.0, "vat": 0, "gross": 450.0}
    samples.append(("valid_04_vitality_lesion.pdf", v4, True, set()))

    v5 = base_invoice(**{
        "invoice_number": "INV-2026-9005",
        "patient.nhs_number": "943 476 5919",
        "policy.insurer_id": "nhs_england", "policy.membership_number": "NHSPT4471", "policy.pre_authorisation": None,
        "episode.diagnoses": ["J45.9"], "episode.procedures": ["X3550"],
    })
    v5["lines"] = [{"service_code": "NHS-SESSION", "description": "NHS clinic session",
                    "quantity": 1, "unit_fee": 320.0, "vat_rate": 0}]
    v5["totals"] = {"net": 320.0, "vat": 0, "gross": 320.0}
    samples.append(("valid_05_nhs_session.pdf", v5, True, set()))

    # ---- five invalid invoices, each a realistic failure story ----
    i1 = base_invoice(**{"invoice_number": "INV-2026-9101",
                         "patient.postcode": "RG1 999", "patient.nhs_number": "9434765918"})
    samples.append(("invalid_01_postcode_nhs.pdf", i1, False, {"format.postcode", "format.nhs_number"}))

    i2 = base_invoice(**{
        "invoice_number": "INV-2026-9102",
        "policy.insurer_id": "wpa", "policy.membership_number": "ABC123", "policy.pre_authorisation": "552901",
        "provider.treatment_site_id": "SITE-087",
        "episode.care_setting": "day_case", "episode.diagnoses": ["M65.3"], "episode.procedures": ["T6810"],
    })
    money(i2, 700.0)
    samples.append(("invalid_02_wpa_membership.pdf", i2, False, {"format.membership"}))

    i3 = base_invoice(**{
        "invoice_number": "INV-2026-9103",
        "policy.insurer_id": "vitality", "policy.pre_authorisation": "AUTH-1",
        "episode.diagnoses": ["D22.9"], "episode.procedures": ["W4310"],
    })
    samples.append(("invalid_03_vitality_preauth_setting.pdf", i3, False,
                    {"format.preauth", "cross.setting_procedure"}))

    i4 = base_invoice(**{
        "invoice_number": "INV-2026-9104",
        "policy.insurer_id": "aviva", "policy.membership_number": "", "policy.pre_authorisation": "918274",
        "provider.treatment_site_id": "SITE-134",
        "episode.care_setting": "day_case", "episode.diagnoses": ["K21.9"], "episode.procedures": ["G4500"],
    })
    money(i4, 650.0)
    samples.append(("invalid_04_missing_membership.pdf", i4, False, {"structural.required"}))

    i5 = base_invoice(**{"invoice_number": "INV-2026-9105", "episode.diagnoses": ["M17.9"]})
    money(i5, 400.0)  # 0101A schedule ceiling is 300
    samples.append(("invalid_05_tariff_unknown_icd.pdf", i5, False, {"cross.tariff", "dict.icd10"}))

    return samples


def self_check(samples) -> None:
    for name, inv, expect_valid, expected_rules in samples:
        # Round-trip through the exact text the PDF will carry, then validate.
        parsed = parse_invoice_text("\n".join(render_lines(inv)))
        issues = validate_invoice(parsed)
        errors = {i.rule_id for i in issues if i.severity == "error"}
        if expect_valid and errors:
            raise SystemExit(f"{name}: expected clean, engine says {sorted(errors)}")
        if not expect_valid:
            missing = expected_rules - errors
            if missing:
                raise SystemExit(f"{name}: expected rules {sorted(expected_rules)}, engine says {sorted(errors)}")


def main() -> None:
    out = BACKEND / "samples"
    out.mkdir(exist_ok=True)
    samples = build_samples()
    self_check(samples)
    manifest = []
    for name, inv, expect_valid, expected_rules in samples:
        write_pdf(inv, out / name)
        verdict = validate_invoice(ingest_pdf((out / name).read_bytes()))
        errors = {i.rule_id for i in verdict if i.severity == "error"}
        ok = (not errors) if expect_valid else expected_rules <= errors
        manifest.append({"file": name, "expect_valid": expect_valid,
                         "expected_rules": sorted(expected_rules), "pdf_roundtrip_ok": ok})
        print(f"{'PASS' if ok else 'FAIL'}  {name}  ->  {sorted(errors) if errors else 'clean'}")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    if not all(m["pdf_roundtrip_ok"] for m in manifest):
        raise SystemExit("PDF round-trip check failed")
    print(f"\n{len(manifest)} sample PDFs written to {out}")


if __name__ == "__main__":
    main()
