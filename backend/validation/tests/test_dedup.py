"""Duplicate-claim detection: canonical fingerprints, the seed number ledger,
the fingerprint index (persistence included), and the HTTP wiring."""
import copy

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from validation import dedup
from validation.api import router
from validation.dedup import FingerprintIndex, canonical_fingerprint, load_ledger
from validation.engine import validate_invoice

app = FastAPI()
app.include_router(router)
client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_index(monkeypatch):
    """Each test gets its own in-memory index; the module one is untouched."""
    monkeypatch.setattr(dedup, "INDEX", FingerprintIndex())


def post(payload: dict) -> dict:
    res = client.post("/invoices/validate", json=payload)
    assert res.status_code == 200
    return res.json()


def rules(body: dict) -> list[str]:
    return [i["rule"] for i in body["issues"]]


# --- canonical_fingerprint ---------------------------------------------------

def test_fingerprint_deterministic(golden):
    assert canonical_fingerprint(golden) == canonical_fingerprint(copy.deepcopy(golden))


def test_fingerprint_ignores_code_order_and_invoice_number(golden):
    a = copy.deepcopy(golden)
    a["episode"]["diagnoses"] = ["M17.1", "E11.9"]
    a["episode"]["procedures"] = ["0101A", "W4310"]
    b = copy.deepcopy(a)
    b["episode"]["diagnoses"].reverse()
    b["episode"]["procedures"].reverse()
    b["invoice_number"] = "INV-2026-0999"
    assert canonical_fingerprint(a) == canonical_fingerprint(b)


def test_fingerprint_changes_with_totals(golden):
    tweaked = copy.deepcopy(golden)
    tweaked["totals"]["net"] = golden["totals"]["net"] + 0.01
    assert canonical_fingerprint(tweaked) != canonical_fingerprint(golden)


# --- HTTP wiring ---------------------------------------------------------------

def test_same_content_new_number_trips_dedup(golden):
    assert post(golden) == {"valid": True, "issues": []}
    resub = copy.deepcopy(golden)
    resub["invoice_number"] = "INV-2026-0201"
    body = post(resub)
    assert body["valid"] is False
    assert "dedup.duplicate_claim" in rules(body)
    dup = next(i for i in body["issues"] if i["rule"] == "dedup.duplicate_claim")
    assert dup["error"] == f"Content duplicates invoice {golden['invoice_number']}"
    assert set(dup) == {"field", "error", "solution", "severity", "rule", "path"}


def test_same_invoice_twice_is_idempotent(golden):
    first = post(golden)
    second = post(golden)
    assert first == second == {"valid": True, "issues": []}


def test_penny_difference_is_not_a_duplicate(golden):
    post(golden)
    near = copy.deepcopy(golden)
    near["invoice_number"] = "INV-2026-0202"
    near["totals"]["net"] = golden["totals"]["net"] + 0.01
    near["totals"]["gross"] = golden["totals"]["gross"] + 0.01
    body = post(near)
    assert "dedup.duplicate_claim" not in rules(body)


# --- ledger (cross.duplicate_number) -------------------------------------------

def test_ledger_holds_seed_numbers():
    ledger = load_ledger()
    assert "INV-2026-0001" in ledger
    assert "INV-2026-0200" not in ledger


def test_seed_number_trips_duplicate_number_in_engine(golden):
    golden["invoice_number"] = "INV-2026-0001"
    issues = validate_invoice(golden, ledger=load_ledger())
    assert "cross.duplicate_number" in {i.rule_id for i in issues}


def test_seed_number_trips_duplicate_number_over_http(golden):
    reused = copy.deepcopy(golden)
    reused["invoice_number"] = "INV-2026-0001"
    body = post(reused)
    assert body["valid"] is False
    assert "cross.duplicate_number" in rules(body)


# --- FingerprintIndex persistence ----------------------------------------------

def test_index_round_trips_through_json(golden, tmp_path):
    path = tmp_path / "index.json"
    first = FingerprintIndex(path)
    assert first.check(golden) is None
    assert path.exists()

    reloaded = FingerprintIndex(path)
    resub = copy.deepcopy(golden)
    resub["invoice_number"] = "INV-2026-0300"
    assert reloaded.check(resub) == golden["invoice_number"]


def test_corrupt_index_file_starts_empty(golden, tmp_path):
    path = tmp_path / "index.json"
    path.write_text("{not json![")
    index = FingerprintIndex(path)
    assert index.check(golden) is None


def test_missing_index_file_starts_empty(golden, tmp_path):
    index = FingerprintIndex(tmp_path / "absent.json")
    assert index.check(golden) is None
