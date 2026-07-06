"""Seed-data integrity: the demo dataset must obey the shared contract and the
engine's own guarantees, and the two copies (backend and frontend) must match."""
import json
from datetime import date
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[2]
REPO = BACKEND.parent
SEEDS = json.loads((BACKEND / "seeds.json").read_text())

STATUSES = {"draft", "at_medserv", "with_insurer", "insurer_query", "paid", "rejected"}
REQUIRED_KEYS = {
    "id", "invoice_number", "payer_type", "insurer_name", "patient_ref", "description",
    "total", "amount_due", "middleman_fee", "currency", "issued_date", "submitted_date",
    "expected_payment_date", "paid_date", "pipeline_status", "query_reason",
    "last_chased_at", "timeline", "validation_issues", "source",
}


def test_frontend_copy_is_identical():
    frontend = (REPO / "frontend" / "src" / "api" / "seeds.json").read_text()
    assert frontend == (BACKEND / "seeds.json").read_text()


def test_every_seed_matches_contract_shape():
    assert len(SEEDS) > 100
    for inv in SEEDS:
        assert REQUIRED_KEYS <= set(inv), inv["id"]
        assert inv["pipeline_status"] in STATUSES
        assert inv["payer_type"] in ("private_insurer", "nhs")
        assert inv["currency"] == "GBP"
        assert 0 <= inv["amount_due"] <= inv["total"]


def test_invoice_numbers_unique_and_sequential_format():
    numbers = [i["invoice_number"] for i in SEEDS]
    assert len(numbers) == len(set(numbers))
    assert all(n.startswith("INV-2026-") for n in numbers)


def test_timelines_are_ordered_and_consistent():
    for inv in SEEDS:
        dates = [e["at"] for e in inv["timeline"]]
        assert dates == sorted(dates), inv["id"]
        assert inv["timeline"][-1]["stage"] == inv["pipeline_status"], inv["id"]
        assert inv["timeline"][0]["stage"] == "draft", inv["id"]


def test_rejected_seeds_carry_engine_issues_and_only_they_do():
    for inv in SEEDS:
        if inv["pipeline_status"] == "rejected":
            assert inv["validation_issues"], inv["id"]
            for issue in inv["validation_issues"]:
                assert issue["field"] and issue["error"] and issue["solution"], inv["id"]
        else:
            assert inv["validation_issues"] == [], inv["id"]


def test_paid_semantics():
    for inv in SEEDS:
        if inv["pipeline_status"] == "paid":
            assert inv["paid_date"], inv["id"]
            assert date.fromisoformat(inv["paid_date"]) >= date.fromisoformat(inv["issued_date"])
        else:
            assert inv["paid_date"] is None, inv["id"]


def test_query_semantics():
    for inv in SEEDS:
        if inv["pipeline_status"] == "insurer_query":
            assert inv["query_reason"], inv["id"]


def test_nhs_invoices_carry_no_middleman_fee():
    for inv in SEEDS:
        if inv["payer_type"] == "nhs":
            assert inv["middleman_fee"] == 0, inv["id"]
        elif inv["payer_type"] == "private_insurer":
            assert inv["middleman_fee"] == pytest.approx(inv["total"] * 0.03, abs=0.01), inv["id"]
