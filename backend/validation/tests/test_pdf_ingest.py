"""End-to-end PDF pipeline: the ten demo PDFs must classify exactly as their
manifest says, through both the ingestion module and the HTTP upload route."""
import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from validation import validate_invoice
from validation.api import router
from validation.pdf_ingest import ingest_pdf, parse_invoice_text

BACKEND = Path(__file__).resolve().parents[2]
SAMPLES = BACKEND / "samples"
MANIFEST = json.loads((SAMPLES / "manifest.json").read_text())

app = FastAPI()
app.include_router(router)
client = TestClient(app)


@pytest.mark.parametrize("entry", MANIFEST, ids=[m["file"] for m in MANIFEST])
def test_sample_pdf_classification(entry):
    pdf = (SAMPLES / entry["file"]).read_bytes()
    issues = validate_invoice(ingest_pdf(pdf))
    errors = {i.rule_id for i in issues if i.severity == "error"}
    if entry["expect_valid"]:
        assert errors == set(), f"{entry['file']} should be clean, got {sorted(errors)}"
    else:
        assert set(entry["expected_rules"]) <= errors, (
            f"{entry['file']} should trip {entry['expected_rules']}, got {sorted(errors)}"
        )


@pytest.mark.parametrize("entry", MANIFEST, ids=[m["file"] for m in MANIFEST])
def test_upload_route_matches_direct_ingestion(entry):
    pdf = (SAMPLES / entry["file"]).read_bytes()
    res = client.post("/invoices/upload", files={"file": (entry["file"], pdf, "application/pdf")})
    assert res.status_code == 200
    body = res.json()
    assert body["valid"] is entry["expect_valid"]
    assert body["parsed"] is not None
    if not entry["expect_valid"]:
        assert set(entry["expected_rules"]) <= {i["rule"] for i in body["issues"]}


def test_garbage_bytes_fail_gracefully():
    res = client.post("/invoices/upload", files={"file": ("junk.pdf", b"not a pdf at all", "application/pdf")})
    assert res.status_code == 200
    body = res.json()
    assert body["valid"] is False
    assert body["issues"][0]["rule"] == "ingest.unreadable"


def test_parser_ignores_unknown_labels_and_junk_lines():
    text = "\n".join([
        "Random header",
        "Invoice Number: INV-2026-7777",
        "Coffee Order: espresso",
        "Net Total: not-a-number",
    ])
    parsed = parse_invoice_text(text)
    assert parsed["invoice_number"] == "INV-2026-7777"
    assert "totals" not in parsed


def test_insurer_display_names_map_to_ids():
    parsed = parse_invoice_text("Insurer: AXA Health")
    assert parsed["policy"]["insurer_id"] == "axa_health"
