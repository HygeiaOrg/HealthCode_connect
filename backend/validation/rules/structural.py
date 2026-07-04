"""Layer 1: structure. JSON Schema validation with errors translated into
plain-language Field / Error / Solution triplets. Raw validator output never
reaches the user (the incumbent's raw-SOAP audit log is the anti-pattern)."""
from __future__ import annotations

import jsonschema

from ..engine import Issue

# Human labels and fix guidance per schema path. Fallback prettifies the path.
LABELS: dict[str, tuple[str, str]] = {
    "invoice_number": ("Invoice Number", "Give the invoice a unique reference of letters, digits, / or - (HMRC requires a unique sequential number)."),
    "invoice_date": ("Invoice Date", "Enter the issue date as YYYY-MM-DD."),
    "currency": ("Currency", "UK medical bills are invoiced in GBP."),
    "practice": ("Practice Details", "Add the practice block: name, address and postcode (HMRC supplier requirements)."),
    "practice.name": ("Practice Name", "Enter the billing practice's trading name."),
    "practice.address_line1": ("Practice Address", "Enter the practice's address; HMRC requires the supplier address on every invoice."),
    "practice.postcode": ("Practice Postcode", "Enter the practice postcode."),
    "patient": ("Patient Details", "Add the patient block: name, date of birth, sex, address and postcode."),
    "patient.first_name": ("Patient First Name", "Enter the patient's forename as registered with the insurer."),
    "patient.surname": ("Patient Surname", "Enter the patient's surname as registered with the insurer; name mismatches fail the demographic check."),
    "patient.date_of_birth": ("Date of Birth", "Enter the patient's date of birth as YYYY-MM-DD; insurers match it against the policy record."),
    "patient.sex": ("Patient Sex", "Select M, F or X; required for the insurer membership enquiry."),
    "patient.address_line1": ("Patient Address", "Enter the patient's address as held by the insurer."),
    "patient.postcode": ("Patient Postcode", "Enter the patient's postcode; it is part of the insurer's demographic match."),
    "policy": ("Policy Details", "Add the policy block: insurer and membership number."),
    "policy.insurer_id": ("Insurer", "Select the paying insurer; it decides which validation rules apply."),
    "policy.membership_number": ("Membership Number", "Enter the policy or membership number from the patient's card; bills without one are rejected."),
    "provider": ("Provider Details", "Add the provider block: specialist, GMC number, payee and treatment site."),
    "provider.specialist_name": ("Controlling Specialist", "Name the treating consultant."),
    "provider.gmc_number": ("GMC Number", "Enter the specialist's 7-digit GMC reference number."),
    "provider.payee_provider_id": ("Payee Provider", "Select who is to be paid; the payee must be registered and mapped to this insurer."),
    "provider.treatment_site_id": ("Treatment Site", "Select the facility where treatment took place."),
    "episode": ("Episode Details", "Add the episode block: care setting, treatment date, diagnoses and procedures."),
    "episode.care_setting": ("Care Setting", "Choose outpatient, day_case or inpatient, matching where treatment actually happened."),
    "episode.treatment_date": ("Treatment Date", "Enter the treatment date as YYYY-MM-DD."),
    "episode.diagnoses": ("Diagnosis Code", "List the ICD-10 diagnosis code(s) for this episode."),
    "episode.procedures": ("Procedure Code", "List the CCSD procedure code(s) billed."),
    "lines": ("Charge Lines", "Add at least one charge line: service code, description, quantity and fee."),
    "totals": ("Totals", "Add totals: net, vat and gross."),
}


def _label(path: str) -> tuple[str, str]:
    if path in LABELS:
        return LABELS[path]
    leaf = path.split(".")[-1].split("[")[0]
    if leaf in LABELS:
        return LABELS[leaf]
    pretty = leaf.replace("_", " ").title() if leaf else "Invoice"
    return pretty, f"Correct the {pretty} field and revalidate."


def _path_of(err: jsonschema.ValidationError) -> str:
    parts: list[str] = []
    for p in err.absolute_path:
        if isinstance(p, int):
            parts[-1] = f"{parts[-1]}[{p}]" if parts else f"[{p}]"
        else:
            parts.append(str(p))
    return ".".join(parts)


def check(invoice: dict, schema: dict) -> list[Issue]:
    validator = jsonschema.Draft202012Validator(schema)
    issues: list[Issue] = []
    for err in sorted(validator.iter_errors(invoice), key=lambda e: str(e.absolute_path)):
        base = _path_of(err)
        if err.validator == "required":
            missing_props = [p for p in err.validator_value if p not in (err.instance or {})]
            for prop in missing_props:
                path = f"{base}.{prop}" if base else prop
                label, solution = _label(path)
                issues.append(Issue(label, "Missing required field", solution, rule_id="structural.required", path=path))
        elif err.validator in ("enum", "const"):
            allowed = err.validator_value if err.validator == "enum" else [err.validator_value]
            label, solution = _label(base)
            issues.append(Issue(label, f"Value not allowed (allowed: {', '.join(map(str, allowed))})", solution, rule_id="structural.enum", path=base))
        elif err.validator == "type":
            label, solution = _label(base)
            issues.append(Issue(label, f"Wrong type; expected {err.validator_value}", solution, rule_id="structural.type", path=base))
        elif err.validator == "pattern":
            label, solution = _label(base)
            issues.append(Issue(label, "Value is not in the expected format", solution, rule_id="structural.pattern", path=base))
        elif err.validator == "minItems":
            label, solution = _label(base)
            issues.append(Issue(label, "At least one entry is required", solution, rule_id="structural.min_items", path=base))
        elif err.validator in ("minimum", "minLength"):
            label, solution = _label(base)
            issues.append(Issue(label, "Value is empty or below the allowed minimum", solution, rule_id="structural.minimum", path=base))
        elif err.validator == "additionalProperties":
            continue  # unknown extras are tolerated at the top level message level
        elif err.validator == "oneOf":
            label, solution = _label(base)
            issues.append(Issue(label, "Value is not in the expected format", solution, rule_id="structural.format", path=base))
        else:
            label, solution = _label(base)
            issues.append(Issue(label, "Value fails the invoice schema", solution, rule_id=f"structural.{err.validator}", path=base))
    return issues
