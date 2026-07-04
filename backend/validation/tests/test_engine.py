import jsonschema
import pytest

from validation import is_valid, load_schema, validate_invoice
from validation.rules.formats import nhs_number_check_digit, nhs_number_valid


def rules_of(issues):
    return {i.rule_id for i in issues}


def errors_only(issues):
    return [i for i in issues if i.severity == "error"]


# ---------- foundations ----------

def test_schema_is_valid_jsonschema():
    jsonschema.Draft202012Validator.check_schema(load_schema())


def test_golden_invoice_is_clean(golden):
    issues = validate_invoice(golden)
    assert issues == []
    assert is_valid(issues)


# ---------- NHS Modulus 11 (NHS Data Dictionary algorithm) ----------

def test_nhs_number_known_valid():
    assert nhs_number_valid("9434765919")
    assert nhs_number_valid("943 476 5919")


def test_nhs_number_single_digit_typo_fails():
    assert not nhs_number_valid("9434765918")


def test_nhs_number_check_digit_ten_is_invalid():
    # first nine "000000006": weighted sum 12, remainder 1, 11-1=10 -> never issued
    assert nhs_number_check_digit("000000006") is None
    assert not nhs_number_valid("0000000060")


def test_nhs_number_check_digit_eleven_maps_to_zero():
    # find a prefix whose remainder is 0 -> check digit 0
    prefix = "000000000"
    assert nhs_number_check_digit(prefix) == 0
    assert nhs_number_valid(prefix + "0")


# ---------- layer 1: structural ----------

def test_missing_membership_number(golden):
    del golden["policy"]["membership_number"]
    issues = validate_invoice(golden)
    hit = [i for i in issues if i.rule_id == "structural.required" and i.field == "Membership Number"]
    assert hit and "card" in hit[0].solution


def test_bad_care_setting_enum(golden):
    golden["episode"]["care_setting"] = "home_visit"
    assert "structural.enum" in rules_of(validate_invoice(golden))


# ---------- layer 2: formats ----------

def test_bad_postcode(golden):
    golden["patient"]["postcode"] = "NOT A CODE"
    issues = validate_invoice(golden)
    assert "format.postcode" in rules_of(issues)


def test_bad_gmc(golden):
    golden["provider"]["gmc_number"] = "12345"
    assert "format.gmc" in rules_of(validate_invoice(golden))


def test_wpa_membership_format_enforced(golden):
    golden["policy"]["insurer_id"] = "wpa"
    golden["policy"]["pre_authorisation"] = "123456"
    golden["policy"]["membership_number"] = "ABC123"
    assert "format.membership" in rules_of(validate_invoice(golden))


def test_impossible_calendar_date(golden):
    golden["episode"]["treatment_date"] = "2026-02-31"
    assert "format.date" in rules_of(validate_invoice(golden))


# ---------- layer 3: dictionary ----------

def test_unknown_icd10_suggests_closest(golden):
    golden["episode"]["diagnoses"] = ["M17.2"]
    issues = [i for i in validate_invoice(golden) if i.rule_id == "dict.icd10"]
    assert issues and "M17.1" in issues[0].solution


def test_unknown_ccsd_suggests_closest(golden):
    golden["episode"]["procedures"] = ["W4311"]
    golden["totals"] = {"net": 250.0, "vat": 0, "gross": 250.0}
    issues = [i for i in validate_invoice(golden) if i.rule_id == "dict.ccsd"]
    assert issues and "W4310" in issues[0].solution


def test_unmapped_charge_code(golden):
    golden["lines"][0]["service_code"] = "CONS-XXXX"
    assert "dict.charge_code" in rules_of(validate_invoice(golden))


# ---------- layer 4: cross-field ----------

def test_icd10_required_for_bupa(golden):
    golden["episode"]["diagnoses"] = []
    issues = [i for i in validate_invoice(golden) if i.rule_id == "cross.icd10_required"]
    assert issues and "Bupa" in issues[0].error


def test_treatment_after_invoice_date(golden):
    golden["episode"]["treatment_date"] = "2026-07-10"
    assert "cross.treated_after_invoice" in rules_of(validate_invoice(golden))


def test_inpatient_requires_stay_dates(golden):
    golden["episode"]["care_setting"] = "inpatient"
    assert "cross.inpatient_dates" in rules_of(validate_invoice(golden))


def test_setting_must_suit_procedure(golden):
    golden["episode"]["procedures"] = ["W4310"]  # knee replacement: inpatient only
    assert "cross.setting_procedure" in rules_of(validate_invoice(golden))


def test_specialist_not_mapped_to_insurer(golden):
    golden["policy"]["insurer_id"] = "allianz"
    golden["policy"]["membership_number"] = "P12345"
    assert "cross.specialist_mapping" in rules_of(validate_invoice(golden))


def test_duplicate_invoice_number_via_ledger(golden):
    issues = validate_invoice(golden, ledger=frozenset({"INV-2026-0200"}))
    assert "cross.duplicate_number" in rules_of(issues)


def test_lines_must_sum_to_net(golden):
    golden["totals"] = {"net": 300.0, "vat": 0, "gross": 300.0}
    assert "cross.net_mismatch" in rules_of(validate_invoice(golden))


def test_fee_above_schedule_ceiling(golden):
    golden["lines"][0]["unit_fee"] = 400.0
    golden["totals"] = {"net": 400.0, "vat": 0, "gross": 400.0}
    assert "cross.tariff" in rules_of(validate_invoice(golden))


def test_vat_on_exempt_service_is_warning_not_blocker(golden):
    golden["lines"][0]["vat_rate"] = 0.2
    golden["totals"] = {"net": 250.0, "vat": 50.0, "gross": 300.0}
    issues = validate_invoice(golden)
    vat = [i for i in issues if i.rule_id == "cross.vat_exempt"]
    assert vat and vat[0].severity == "warning"
    assert errors_only(issues) == []
    assert is_valid(issues)


def test_service_not_billable_to_insurer(golden):
    golden["lines"][0]["service_code"] = "REPORT-MED"
    assert "cross.not_billable" in rules_of(validate_invoice(golden))


# ---------- determinism ----------

def test_same_input_same_output(golden):
    golden["patient"]["postcode"] = "XX99 9XX"
    golden["episode"]["diagnoses"] = ["M17.2"]
    a = validate_invoice(golden)
    b = validate_invoice(golden)
    assert a == b


@pytest.mark.parametrize("drop", ["patient", "policy", "episode"])
def test_missing_blocks_reported_with_labels(golden, drop):
    del golden[drop]
    issues = validate_invoice(golden)
    assert any(i.rule_id == "structural.required" for i in issues)
    assert all("'" not in i.field for i in issues)  # human labels, not raw paths
