"""Layer 2: lexical and arithmetic formats. Regex where a pattern is published;
real arithmetic where a checksum exists (regex cannot verify a check digit)."""
from __future__ import annotations

import re
from datetime import date

from ..engine import Dictionaries, Issue, get_path

# GOV.UK postcode regex (official data-standards helper), anchored, upper-cased input.
POSTCODE_RE = re.compile(
    r"^(GIR 0AA|((([A-Z][0-9]{1,2})|(([A-Z][A-HJ-Y][0-9]{1,2})|(([A-Z][0-9][A-Z])|([A-Z][A-HJ-Y][0-9][A-Z]?))))\s?[0-9][A-Z]{2}))$"
)
GMC_RE = re.compile(r"^\d{7}$")                                # NHS Data Dictionary attribute
ICD10_RE = re.compile(r"^[A-TV-Z][0-9]{2}(\.[0-9A-Z]{1,4})?$")  # WHO structure; U-codes reserved
CCSD_RE = re.compile(r"^([A-Z]\d{4}|\d{4}[A-Z]|\d{5})$")        # CCSD Technical Guide shapes


def nhs_number_check_digit(first_nine: str) -> int | None:
    """NHS Data Dictionary Modulus 11: weights 10..2 over digits 1-9; 11-remainder;
    11 means 0; 10 means the number is invalid (never issued)."""
    total = sum(int(d) * w for d, w in zip(first_nine, range(10, 1, -1)))
    result = 11 - (total % 11)
    if result == 11:
        return 0
    if result == 10:
        return None
    return result


def nhs_number_valid(value: str) -> bool:
    digits = re.sub(r"\s", "", value)
    if not re.fullmatch(r"\d{10}", digits):
        return False
    check = nhs_number_check_digit(digits[:9])
    return check is not None and check == int(digits[9])


def parseable_date(value) -> bool:
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def check(invoice: dict, d: Dictionaries) -> list[Issue]:
    issues: list[Issue] = []

    for path, label in [("patient.postcode", "Patient Postcode"), ("practice.postcode", "Practice Postcode")]:
        v = get_path(invoice, path)
        if isinstance(v, str) and v.strip() and not POSTCODE_RE.match(v.strip().upper()):
            issues.append(Issue(label, f"'{v}' is not a valid UK postcode",
                                "Enter a real UK postcode (for example SW1A 1AA); the insurer demographic match uses it.",
                                rule_id="format.postcode", path=path))

    nhs = get_path(invoice, "patient.nhs_number")
    if isinstance(nhs, str) and nhs.strip() and not nhs_number_valid(nhs):
        issues.append(Issue("NHS Number", f"'{nhs}' fails the NHS Modulus-11 check",
                            "An NHS number is 10 digits whose last digit is a checksum. Re-read it from the record; one mistyped digit breaks the check.",
                            rule_id="format.nhs_number", path="patient.nhs_number"))

    gmc = get_path(invoice, "provider.gmc_number")
    if isinstance(gmc, str) and gmc.strip() and not GMC_RE.match(gmc.strip()):
        issues.append(Issue("GMC Number", f"'{gmc}' is not a valid GMC reference number",
                            "A doctor's GMC reference number is exactly 7 digits with no letters.",
                            rule_id="format.gmc", path="provider.gmc_number"))

    for i, code in enumerate(get_path(invoice, "episode.diagnoses") or []):
        if isinstance(code, str) and code.strip() and not ICD10_RE.match(code.strip().upper()):
            issues.append(Issue("Diagnosis Code", f"'{code}' is not shaped like an ICD-10 code",
                                "ICD-10 codes are a letter, two digits, and an optional subcategory after a dot (for example M17.1).",
                                rule_id="format.icd10", path=f"episode.diagnoses[{i}]"))

    for i, code in enumerate(get_path(invoice, "episode.procedures") or []):
        if isinstance(code, str) and code.strip() and not CCSD_RE.match(code.strip().upper()):
            issues.append(Issue("Procedure Code", f"'{code}' is not shaped like a CCSD code",
                                "CCSD codes are 5 characters: a chapter letter plus four digits (W4310), or digits with a category letter (0101A).",
                                rule_id="format.ccsd", path=f"episode.procedures[{i}]"))

    insurer = d.insurers.get(get_path(invoice, "policy.insurer_id") or "")
    member = get_path(invoice, "policy.membership_number")
    if insurer and insurer.get("membership_format") and isinstance(member, str) and member.strip():
        if not re.match(insurer["membership_format"], member.strip()):
            issues.append(Issue("Membership Number",
                                f"'{member}' does not match the {insurer['name']} format",
                                f"{insurer['name']} membership numbers match {insurer['membership_format']}. Copy the number exactly from the patient's card.",
                                rule_id="format.membership", path="policy.membership_number"))

    preauth = get_path(invoice, "policy.pre_authorisation")
    if insurer and insurer.get("preauth_format") and isinstance(preauth, str) and preauth.strip():
        if not re.match(insurer["preauth_format"], preauth.strip()):
            issues.append(Issue("Authorisation Code",
                                f"'{preauth}' is not in the {insurer['name']} authorisation format",
                                "Correct the pre-authorisation reference or remove the field; a malformed one fails validation outright.",
                                rule_id="format.preauth", path="policy.pre_authorisation"))

    for path, label in [("invoice_date", "Invoice Date"), ("patient.date_of_birth", "Date of Birth"),
                        ("episode.treatment_date", "Treatment Date"), ("episode.admission_date", "Admission Date"),
                        ("episode.discharge_date", "Discharge Date")]:
        v = get_path(invoice, path)
        if isinstance(v, str) and v and re.fullmatch(r"\d{4}-\d{2}-\d{2}", v) and not parseable_date(v):
            issues.append(Issue(label, f"'{v}' is not a real calendar date",
                                "Correct the date; the day does not exist in that month.",
                                rule_id="format.date", path=path))

    return issues
