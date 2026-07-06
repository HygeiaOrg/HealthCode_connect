"""The HTTP surface: the router must return exactly what the engine returns,
in the contract shape, for valid, invalid, and garbage payloads."""
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from validation.api import router

FIXTURES = Path(__file__).parent / "fixtures"

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def post(payload: dict):
    res = client.post("/invoices/validate", json=payload)
    assert res.status_code == 200
    return res.json()


def test_golden_is_valid_over_http():
    body = post(json.loads((FIXTURES / "golden_valid.json").read_text()))
    assert body == {"valid": True, "issues": []}


def test_rejected_showcase_pins_expected_rules():
    body = post(json.loads((FIXTURES / "rejected_showcase.json").read_text()))
    assert body["valid"] is False
    assert [i["rule"] for i in body["issues"]] == [
        "format.postcode",
        "format.nhs_number",
        "format.preauth",
        "dict.icd10",
        "cross.setting_procedure",
    ]


def test_issue_wire_shape_matches_contract():
    body = post(json.loads((FIXTURES / "rejected_showcase.json").read_text()))
    for issue in body["issues"]:
        assert set(issue) == {"field", "error", "solution", "severity", "rule", "path"}
        assert issue["field"] and issue["error"] and issue["solution"]
        assert issue["severity"] in ("error", "warning")


def test_empty_payload_reports_missing_blocks_not_500():
    body = post({})
    assert body["valid"] is False
    fields = {i["field"] for i in body["issues"]}
    assert {"Invoice Number", "Patient Details", "Policy Details"} <= fields
