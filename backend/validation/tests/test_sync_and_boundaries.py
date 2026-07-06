"""Cross-repo sync guards and boundary cases.

The insurer SLA table lives in three places by design (frontend triage,
validation dictionaries, seed generator); these tests fail the build the
moment they drift. Boundary tests pin exact thresholds so refactors cannot
quietly move them."""
import ast
import json
import re
from pathlib import Path

from validation import validate_invoice
from validation.rules.formats import POSTCODE_RE, nhs_number_valid

BACKEND = Path(__file__).resolve().parents[2]
REPO = BACKEND.parent


# ---------- three-way SLA sync ----------

def _sla_from_insurers_json() -> dict[str, int]:
    data = json.loads((BACKEND / "validation" / "dictionaries" / "insurers.json").read_text())
    return {v["name"]: v["sla_days"] for v in data["insurers"].values()}


def _sla_from_gen_seeds() -> dict[str, int]:
    text = (BACKEND / "scripts" / "gen_seeds.py").read_text()
    match = re.search(r"^SLA\s*=\s*(\{[^}]*\})", text, re.MULTILINE)
    assert match, "SLA literal not found in gen_seeds.py"
    return ast.literal_eval(match.group(1))


def _sla_from_frontend_triage() -> dict[str, int]:
    text = (REPO / "frontend" / "src" / "lib" / "triage.ts").read_text()
    block = re.search(r"SLA_DAYS[^{]*\{(.*?)\}", text, re.DOTALL)
    assert block, "SLA_DAYS not found in triage.ts"
    return {
        name.strip(): int(days)
        for name, days in re.findall(r"'?\"?([A-Za-z][A-Za-z ]*)'?\"?\s*:\s*(\d+)", block.group(1))
    }


def test_sla_synchronised_across_all_three_homes():
    registry = _sla_from_insurers_json()
    seeds = _sla_from_gen_seeds()
    triage = _sla_from_frontend_triage()
    for name, days in seeds.items():
        assert registry.get(name) == days, f"gen_seeds vs insurers.json drift for {name}"
    for name, days in triage.items():
        assert registry.get(name) == days, f"triage.ts vs insurers.json drift for {name}"
    assert seeds == triage, "gen_seeds.py vs triage.ts drift"


def test_seed_insurers_all_exist_in_registry():
    seeds = json.loads((BACKEND / "seeds.json").read_text())
    registry_names = set(_sla_from_insurers_json())
    assert {i["insurer_name"] for i in seeds} <= registry_names


# ---------- boundary pins ----------

def test_fee_exactly_at_tariff_cap_passes(golden):
    golden["lines"][0]["unit_fee"] = 300.0  # 0101A cap is exactly 300
    golden["totals"] = {"net": 300.0, "vat": 0, "gross": 300.0}
    assert "cross.tariff" not in {i.rule_id for i in validate_invoice(golden)}


def test_fee_a_penny_over_cap_fails(golden):
    golden["lines"][0]["unit_fee"] = 300.01
    golden["totals"] = {"net": 300.01, "vat": 0, "gross": 300.01}
    assert "cross.tariff" in {i.rule_id for i in validate_invoice(golden)}


def test_gir_0aa_special_postcode_accepted():
    assert POSTCODE_RE.match("GIR 0AA")


def test_postcode_without_space_accepted(golden):
    golden["patient"]["postcode"] = "SW1A1AA"
    assert "format.postcode" not in {i.rule_id for i in validate_invoice(golden)}


def test_nhs_number_formatting_variants():
    assert nhs_number_valid("9434765919")
    assert nhs_number_valid("943 476 5919")
    assert not nhs_number_valid("94347659190")  # 11 digits
    assert not nhs_number_valid("943476591")    # 9 digits


def test_bupa_global_membership_boundaries(golden):
    golden["policy"]["insurer_id"] = "bupa_global"
    golden["policy"]["pre_authorisation"] = "12345678"
    golden["provider"]["payee_provider_id"] = "PP-4402"
    golden["policy"]["membership_number"] = "BI-1234-5678-9012"
    rules_ok = {i.rule_id for i in validate_invoice(golden)}
    assert "format.membership" not in rules_ok

    golden["policy"]["membership_number"] = "BI-1234-5678-901"  # one digit short
    assert "format.membership" in {i.rule_id for i in validate_invoice(golden)}


def test_issue_dedupe_same_invoice_twice_identical(golden):
    golden["patient"]["postcode"] = "BAD"
    first = validate_invoice(golden)
    second = validate_invoice(golden)
    assert first == second
    keys = [(i.path, i.error) for i in first]
    assert len(keys) == len(set(keys)), "duplicate issues emitted"
