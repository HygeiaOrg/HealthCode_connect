"""Drive watcher unit tests: invoice -> claim mapping and state persistence.

No network, no Google libs — drive_watcher keeps its google imports inside
functions precisely so these paths stay importable in this venv.
"""
from pathlib import Path

import pytest

import drive_watcher
from validation.pdf_ingest import ingest_pdf

SAMPLES = Path(drive_watcher.__file__).parent / "samples"


def test_imports_without_google():
    import sys
    assert "googleapiclient" not in sys.modules


def test_map_full_invoice_from_sample_pdf():
    invoice = ingest_pdf((SAMPLES / "valid_01_bupa_consult.pdf").read_bytes())
    claim = drive_watcher.map_invoice_to_claim(invoice)

    assert claim["patient_name"] == "Amelia Hart"
    assert claim["patient_dob"] == "1981-03-14"
    assert claim["insurance_company_name"] == "Bupa"
    assert claim["policy_number"] == "MB1234567"
    assert claim["auth_code"] == "12345678"
    # Outpatient: no admission date, so the episode treatment date wins.
    assert claim["treatment_date"] == "2026-06-20"
    assert claim["procedures"] == [
        {"procedure_code": "CONS-INIT", "description": "Initial consultation", "fee": 250.0}
    ]


def test_map_missing_blocks_degrades_to_placeholders():
    claim = drive_watcher.map_invoice_to_claim({})

    assert claim["patient_name"] == "Unknown Patient"
    assert claim["patient_dob"] == "1980-01-01"
    assert claim["insurance_company_name"] == "Bupa"
    assert claim["policy_number"] == "UNKNOWN-POLICY"
    assert claim["auth_code"] == "AUTH-PENDING"
    assert claim["treatment_date"]  # today's date, never empty
    assert claim["procedures"] == [
        {"procedure_code": "20600", "description": "Initial Consultation", "fee": 150.00}
    ]


def test_map_unknown_insurer_falls_back_to_raw_id():
    claim = drive_watcher.map_invoice_to_claim(
        {"policy": {"insurer_id": "acme-health", "membership_number": "X1"}}
    )
    assert claim["insurance_company_name"] == "acme-health"
    assert claim["policy_number"] == "X1"


def test_map_totals_fallback_when_lines_absent():
    claim = drive_watcher.map_invoice_to_claim({"totals": {"net": 320.5}})
    assert claim["procedures"][0]["fee"] == 320.5


def test_map_line_fee_is_quantity_times_unit_fee():
    claim = drive_watcher.map_invoice_to_claim(
        {"lines": [{"service_code": "PHYS-S", "description": "Physio", "quantity": 3, "unit_fee": 45.0}]}
    )
    assert claim["procedures"] == [
        {"procedure_code": "PHYS-S", "description": "Physio", "fee": 135.0}
    ]


def test_state_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(drive_watcher, "STATE_PATH", str(tmp_path / "state.json"))
    state = {"processed": ["abc123", "def456"], "rejected": ["bad789"]}
    drive_watcher.save_state(state)
    assert drive_watcher.load_state() == state


def test_state_missing_file_starts_fresh(tmp_path, monkeypatch):
    monkeypatch.setattr(drive_watcher, "STATE_PATH", str(tmp_path / "nope.json"))
    assert drive_watcher.load_state() == {"processed": [], "rejected": []}


@pytest.mark.parametrize("garbage", ["{not json", '["a", "b"]', ""])
def test_state_corrupt_file_starts_fresh(tmp_path, monkeypatch, garbage):
    path = tmp_path / "state.json"
    path.write_text(garbage)
    monkeypatch.setattr(drive_watcher, "STATE_PATH", str(path))
    assert drive_watcher.load_state() == {"processed": [], "rejected": []}
