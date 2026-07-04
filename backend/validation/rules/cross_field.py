"""Layer 4: cross-field logic. Rules that need more than one field at once:
insurer-conditional requirements, date ordering, setting/procedure consistency,
mapping to the insurer, tariffs, arithmetic, VAT exemption, ledger uniqueness."""
from __future__ import annotations

from datetime import date

from ..engine import Dictionaries, Issue, get_path


def _d(value) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def check(invoice: dict, d: Dictionaries, *, ledger: frozenset[str] = frozenset()) -> list[Issue]:
    issues: list[Issue] = []
    insurer_id = get_path(invoice, "policy.insurer_id") or ""
    insurer = d.insurers.get(insurer_id)
    insurer_name = insurer["name"] if insurer else insurer_id or "the insurer"

    # Ledger uniqueness (HMRC: unique sequential number).
    number = invoice.get("invoice_number")
    if isinstance(number, str) and number and number in ledger:
        issues.append(Issue("Invoice Number", f"'{number}' has already been used",
                            "Invoice numbers must be unique and sequential; take the next number in the series.",
                            rule_id="cross.duplicate_number", path="invoice_number"))

    # Insurer-conditional: ICD-10 requirement.
    diagnoses = [c for c in (get_path(invoice, "episode.diagnoses") or []) if str(c).strip()]
    if insurer and insurer.get("requires_icd10") and not diagnoses:
        issues.append(Issue("Diagnosis Code", f"{insurer_name} requires an ICD-10 diagnosis on every bill",
                            "Add the ICD-10 code for the treated condition before submitting.",
                            rule_id="cross.icd10_required", path="episode.diagnoses"))

    # Demographic-match inputs for insurers without a published membership format.
    if insurer and insurer.get("membership_format") is None and insurer_id != "nhs_england":
        missing = [label for path, label in [
            ("patient.surname", "surname"),
            ("patient.date_of_birth", "date of birth"),
            ("patient.postcode", "postcode"),
        ] if not str(get_path(invoice, path) or "").strip()]
        if missing:
            issues.append(Issue("Membership Number",
                                f"{insurer_name} validates membership against patient demographics, and {', '.join(missing)} are missing",
                                "Complete the patient's surname, date of birth and postcode exactly as the insurer holds them.",
                                rule_id="cross.demographics", path="patient"))

    # Date logic.
    dob = _d(get_path(invoice, "patient.date_of_birth"))
    treated = _d(get_path(invoice, "episode.treatment_date"))
    invoiced = _d(invoice.get("invoice_date"))
    admitted = _d(get_path(invoice, "episode.admission_date"))
    discharged = _d(get_path(invoice, "episode.discharge_date"))

    if treated and invoiced and treated > invoiced:
        issues.append(Issue("Treatment Date", "Treatment date is after the invoice date",
                            "You cannot invoice before treating; correct whichever date is wrong.",
                            rule_id="cross.treated_after_invoice", path="episode.treatment_date"))
    if dob and treated and dob > treated:
        issues.append(Issue("Date of Birth", "Date of birth is after the treatment date",
                            "Check the patient's date of birth; as entered they had not been born at treatment.",
                            rule_id="cross.dob_after_treatment", path="patient.date_of_birth"))
    if admitted and discharged and admitted > discharged:
        issues.append(Issue("Admission Date", "Admission date is after the discharge date",
                            "Swap or correct the admission and discharge dates.",
                            rule_id="cross.admission_order", path="episode.admission_date"))

    setting = get_path(invoice, "episode.care_setting")
    if setting == "inpatient" and (not admitted or not discharged):
        issues.append(Issue("Care Setting", "Inpatient bills need admission and discharge dates",
                            "Add both dates, or change the setting if this was not an inpatient stay.",
                            rule_id="cross.inpatient_dates", path="episode.care_setting"))

    # Setting must suit the procedure (VEDA rule) and the site must support the setting.
    for i, code in enumerate(get_path(invoice, "episode.procedures") or []):
        entry = d.ccsd.get(str(code).strip().upper())
        if entry and setting and setting not in entry["allowed_settings"]:
            issues.append(Issue("Care Setting",
                                f"{code} ({entry['narrative']}) cannot be billed as {setting}",
                                f"Bill this procedure in one of: {', '.join(entry['allowed_settings'])}, or correct the procedure code.",
                                rule_id="cross.setting_procedure", path=f"episode.procedures[{i}]"))

    site = d.treatment_sites.get(get_path(invoice, "provider.treatment_site_id") or "")
    if site and setting and setting not in site["settings"]:
        issues.append(Issue("Treatment Site", f"{site['name']} does not support {setting} care",
                            "Pick the site where this setting is available, or correct the care setting.",
                            rule_id="cross.setting_site", path="provider.treatment_site_id"))

    # Insurer mappings (the VEDA "Invalid Code / Not Mapped" family).
    if insurer:
        gmc = str(get_path(invoice, "provider.gmc_number") or "").strip()
        spec = d.specialists.get(gmc)
        if spec and insurer_id not in spec["insurers"]:
            issues.append(Issue("Controlling Specialist",
                                f"{spec['name']} is not mapped to {insurer_name}",
                                f"Register the specialist with {insurer_name} (provider number mapping) before billing them.",
                                rule_id="cross.specialist_mapping", path="provider.gmc_number"))
        payee = d.payee_providers.get(get_path(invoice, "provider.payee_provider_id") or "")
        if payee and insurer_id not in payee["insurers"]:
            issues.append(Issue("Payee Provider", f"{payee['name']} is not mapped to {insurer_name}",
                                f"Set up the payee's data consent with {insurer_name}, or choose a mapped payee.",
                                rule_id="cross.payee_mapping", path="provider.payee_provider_id"))
        if site and insurer_id not in site["insurers"]:
            issues.append(Issue("Treatment Site", f"{site['name']} is not mapped to {insurer_name}",
                                f"Map the site to {insurer_name}, or bill from a mapped facility.",
                                rule_id="cross.site_mapping", path="provider.treatment_site_id"))

        # Billability of each charge line for this insurer.
        for i, line in enumerate(get_path(invoice, "lines") or []):
            cc = d.charge_codes.get(line.get("service_code") if isinstance(line, dict) else "")
            if cc and cc["billable_insurers"] != "all" and insurer_id not in cc["billable_insurers"]:
                issues.append(Issue("Provider Chargecode",
                                    f"Service '{cc['description']}' is not billable to {insurer_name}",
                                    "No fee is agreed for this service with this insurer; remove the line or bill the patient directly.",
                                    rule_id="cross.not_billable", path=f"lines[{i}].service_code"))

    # Arithmetic: lines must sum to net; net + vat = gross.
    lines = get_path(invoice, "lines") or []
    totals = invoice.get("totals") or {}
    if lines and isinstance(totals, dict) and all(k in totals for k in ("net", "vat", "gross")):
        try:
            computed = round(sum(float(l["quantity"]) * float(l["unit_fee"]) for l in lines), 2)
        except (KeyError, TypeError, ValueError):
            computed = None
        if computed is not None and abs(computed - float(totals["net"])) > 0.01:
            issues.append(Issue("Totals", f"Charge lines sum to £{computed:.2f} but net total says £{float(totals['net']):.2f}",
                                "Recalculate the net total from the charge lines; insurers reject bills that do not add up.",
                                rule_id="cross.net_mismatch", path="totals.net"))
        if abs(float(totals["net"]) + float(totals["vat"]) - float(totals["gross"])) > 0.01:
            issues.append(Issue("Totals", "Net plus VAT does not equal the gross total",
                                "Recalculate the gross total as net + VAT.",
                                rule_id="cross.gross_mismatch", path="totals.gross"))

    # Tariff ceiling from the loaded schedule.
    caps = [d.ccsd[str(c).strip().upper()]["tariff_cap"]
            for c in (get_path(invoice, "episode.procedures") or [])
            if str(c).strip().upper() in d.ccsd]
    if caps and isinstance(totals, dict) and "net" in totals:
        cap_total = sum(caps)
        try:
            net = float(totals["net"])
        except (TypeError, ValueError):
            net = None
        if net is not None and net > cap_total:
            issues.append(Issue("Totals", f"Net total £{net:.2f} exceeds the schedule ceiling £{cap_total:.2f} for the procedures billed",
                                "Reduce the fee to the agreed tariff, or check the procedure codes cover everything performed.",
                                rule_id="cross.tariff", path="totals.net"))

    # VAT on exempt medical services (Notice 701/57) is a warning, not a blocker.
    for i, line in enumerate(lines):
        if not isinstance(line, dict):
            continue
        cc = d.charge_codes.get(line.get("service_code") or "")
        if cc and cc["vat_exempt"] and float(line.get("vat_rate") or 0) > 0:
            issues.append(Issue("VAT", f"VAT charged on '{cc['description']}', an exempt medical service",
                                "Medical care is VAT-exempt (VAT Notice 701/57); set the VAT rate to zero unless this line is genuinely non-medical.",
                                severity="warning", rule_id="cross.vat_exempt", path=f"lines[{i}].vat_rate"))

    return issues
