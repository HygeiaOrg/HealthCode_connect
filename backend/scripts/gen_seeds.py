#!/usr/bin/env python3
"""Regenerate demo seed invoices for HealthCode Connect.

Rejected invoices get a full MedicalInvoice payload, a deliberate corruption,
and are run through the REAL validation engine (backend/validation), so the
Field/Error/Solution triplets in seeds.json are genuine engine output.

Run from backend/:  .venv/bin/python scripts/gen_seeds.py
Regenerate together with TODAY in frontend/src/lib/pipeline.ts on demo day.
"""
from __future__ import annotations

import json
import random
import statistics
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from validation import validate_invoice  # noqa: E402
from validation.rules.formats import nhs_number_check_digit  # noqa: E402

random.seed(43)
MED_RNG = random.Random(7)  # separate stream so medical payloads don't shift the base story
TODAY = date(2026, 7, 4)
START = date(2026, 1, 5)

# Must match backend/validation/dictionaries/insurers.json and frontend triage SLA_DAYS.
SLA = {"Bupa": 35, "AXA Health": 40, "Aviva": 45, "Vitality": 40, "WPA": 30, "NHS England": 30}
INSURER_IDS = {"Bupa": "bupa", "AXA Health": "axa_health", "Aviva": "aviva",
               "Vitality": "vitality", "WPA": "wpa", "NHS England": "nhs_england"}
INSURERS = [("Bupa", 35), ("AXA Health", 25), ("Aviva", 15), ("Vitality", 15), ("WPA", 10)]
PROCEDURES = [
    ("Initial consultation", 250), ("Follow-up consultation", 150),
    ("Minor procedure", 450), ("Diagnostic review", 320),
    ("Major procedure", 900), ("Medical report", 120),
]
NHS_SESSIONS = [("NHS clinic session", 320), ("NHS surgical list", 480)]
SURNAME_INITIALS = list("ABCDEFGHJKLMNPRSTW")

QUERY_POOL = [
    "Insurer requests the pre-authorisation reference for this treatment.",
    "Clinical notes required before the claim can be assessed.",
    "Insurer asks whether this was a new condition or a continuation of care.",
    "Confirmation of treatment setting (outpatient vs day case) requested.",
    "Insurer requests the referring GP's details.",
]

# ---- medical payload building (rejected invoices only) ----

SERVICE_MAP = {
    "Initial consultation": ("CONS-INIT", "0101A", "outpatient"),
    "Follow-up consultation": ("CONS-FU", "0102A", "outpatient"),
    "Minor procedure": ("PROC-MINOR", "S0620", "outpatient"),
    "Diagnostic review": ("DIAG-REVIEW", "0201B", "outpatient"),
    "Major procedure": ("PROC-MAJOR", "J1830", "day_case"),
    "Medical report": ("CONS-FU", "0102A", "outpatient"),  # REPORT-MED is only billable to WPA/Allianz
    "NHS clinic session": ("NHS-SESSION", "X3550", "outpatient"),
    "NHS surgical list": ("NHS-SURG", "T6810", "day_case"),
}
SITES = {  # site -> (settings, insurer ids); mirrors providers.json
    "SITE-021": ({"outpatient"}, {"bupa", "axa_health", "aviva", "vitality", "wpa", "allianz", "bupa_global", "nhs_england"}),
    "SITE-087": ({"outpatient", "day_case"}, {"bupa", "axa_health", "vitality", "wpa", "nhs_england"}),
    "SITE-134": ({"outpatient", "day_case", "inpatient"}, {"bupa", "axa_health", "aviva", "vitality", "nhs_england"}),
}
FIRST = {"A": "Amelia", "B": "Ben", "C": "Clara", "D": "David", "E": "Elena", "F": "Finn", "G": "Grace",
         "H": "Harry", "J": "Jack", "K": "Kate", "L": "Liam", "M": "Maya", "N": "Noah", "P": "Paul",
         "R": "Rosa", "S": "Sam", "T": "Tara", "W": "Will"}
SUR = {"A": "Ashford", "B": "Bennett", "C": "Carter", "D": "Dawson", "E": "Ellis", "F": "Foster",
       "G": "Graham", "H": "Hart", "J": "Jennings", "K": "Keller", "L": "Lawson", "M": "Mercer",
       "N": "Norton", "P": "Price", "R": "Reeves", "S": "Shaw", "T": "Turner", "W": "Whitmore"}
GOOD_POSTCODES = ["SW1A 1AA", "RG1 8BX", "M4 5JD", "LS2 7EY", "BS8 1TH", "EH3 9DR"]
GOOD_ICD = ["M17.1", "K21.9", "J45.9", "M54.5", "G56.0", "I10", "N20.0", "M75.1"]


def valid_nhs_number() -> str:
    while True:
        prefix = "".join(str(MED_RNG.randint(0, 9)) for _ in range(9))
        check = nhs_number_check_digit(prefix)
        if check is not None:
            return prefix + str(check)


def make_membership(insurer_id: str) -> str:
    if insurer_id == "wpa":
        return "".join(str(MED_RNG.randint(0, 9)) for _ in range(8))
    return "MB" + "".join(str(MED_RNG.randint(0, 9)) for _ in range(7))


def make_preauth(insurer_id: str) -> str | None:
    digits = lambda n: "".join(str(MED_RNG.randint(0, 9)) for _ in range(n))  # noqa: E731
    return {"bupa": digits(8), "axa_health": digits(8), "aviva": digits(6),
            "vitality": "VH" + digits(6), "wpa": digits(6)}.get(insurer_id)


def pick_site(setting: str, insurer_id: str) -> str:
    for site, (settings, insurers) in SITES.items():
        if setting in settings and insurer_id in insurers:
            return site
    raise ValueError(f"no site supports {setting} for {insurer_id}")


def build_medical_payload(inv: dict) -> dict:
    insurer_id = INSURER_IDS[inv["insurer_name"]]
    service, procedure, setting = SERVICE_MAP[inv["description"]]
    fi, si = inv["patient_ref"][0], inv["patient_ref"][2]
    dob = date(MED_RNG.randint(1950, 2000), MED_RNG.randint(1, 12), MED_RNG.randint(1, 28))
    return {
        "invoice_number": inv["invoice_number"],
        "invoice_date": inv["submitted_date"] or inv["issued_date"],
        "currency": "GBP",
        "practice": {"name": "Harley Street Practice Ltd", "address_line1": "12 Harley Street, London", "postcode": "W1G 9PF"},
        "patient": {
            "first_name": FIRST.get(fi, "Alex"), "surname": SUR.get(si, "Morgan"),
            "date_of_birth": dob.isoformat(), "sex": MED_RNG.choice(["M", "F"]),
            "address_line1": "4 Elm Grove, London", "postcode": MED_RNG.choice(GOOD_POSTCODES),
            "nhs_number": valid_nhs_number() if insurer_id == "nhs_england" else None,
        },
        "policy": {"insurer_id": insurer_id, "membership_number": make_membership(insurer_id),
                   "pre_authorisation": make_preauth(insurer_id)},
        "provider": {"specialist_name": "Dr T. Okafor", "gmc_number": "4479761",
                     "payee_provider_id": "PP-4402", "treatment_site_id": pick_site(setting, insurer_id)},
        "episode": {"care_setting": setting, "treatment_date": inv["issued_date"],
                    "admission_date": None, "discharge_date": None,
                    "diagnoses": [MED_RNG.choice(GOOD_ICD)], "procedures": [procedure]},
        "lines": [{"service_code": service, "description": inv["description"], "quantity": 1,
                   "unit_fee": inv["total"], "vat_rate": 0}],
        "totals": {"net": inv["total"], "vat": 0, "gross": inv["total"]},
    }


def corruptions_for(insurer_id: str) -> list[str]:
    menu = ["postcode", "icd_nearmiss", "gmc_typo", "setting_clash"]
    if insurer_id != "nhs_england":
        menu.append("preauth_bad")
    if insurer_id == "wpa":
        menu.append("membership_bad")
    return menu


def apply_corruption(payload: dict, kind: str) -> None:
    if kind == "postcode":
        payload["patient"]["postcode"] = "RG1 999"
    elif kind == "icd_nearmiss":
        base = payload["episode"]["diagnoses"][0]
        bumped = base[:-1] + ("2" if base[-1] != "2" else "3")
        payload["episode"]["diagnoses"] = [bumped]
    elif kind == "gmc_typo":
        payload["provider"]["gmc_number"] = "447976"
    elif kind == "setting_clash":
        payload["episode"]["procedures"] = ["W4310"]  # inpatient-only knee replacement
    elif kind == "preauth_bad":
        payload["policy"]["pre_authorisation"] = "AUTH-1"
    elif kind == "membership_bad":
        payload["policy"]["membership_number"] = "ABC123"


def engine_issues(inv: dict, reject_index: int) -> list[dict]:
    payload = build_medical_payload(inv)
    clean = validate_invoice(payload)
    if clean:
        raise SystemExit(f"seed self-check failed for {inv['invoice_number']}: base payload not clean: "
                         + "; ".join(f"{i.rule_id}:{i.error}" for i in clean))
    menu = corruptions_for(payload["policy"]["insurer_id"])
    count = 1 if reject_index % 2 == 0 else 2
    chosen = [menu[(reject_index + k) % len(menu)] for k in range(count)]
    for kind in dict.fromkeys(chosen):
        apply_corruption(payload, kind)
    issues = [i.to_contract() for i in validate_invoice(payload) if i.severity == "error"]
    if not issues:
        raise SystemExit(f"corruption produced no issues for {inv['invoice_number']}: {chosen}")
    return issues


# ---- base story generation (statuses, dates, amounts) ----

def pick_insurer():
    r = random.uniform(0, 100)
    acc = 0
    for name, w in INSURERS:
        acc += w
        if r <= acc:
            return name
    return INSURERS[-1][0]


def iso(d):
    return d.isoformat() if d else None


invoices = []
n = 115
for i in range(n):
    issued = START + timedelta(days=random.randint(0, (TODAY - START).days))
    is_nhs = random.random() < 0.35
    if is_nhs:
        desc, amount = random.choice(NHS_SESSIONS)
        insurer, payer, fee = "NHS England", "nhs", 0.0
        reject_p, query_p, shortfall_p = 0.01, 0.02, 0.0
    else:
        desc, amount = random.choice(PROCEDURES)
        insurer, payer = pick_insurer(), "private_insurer"
        fee = round(amount * 0.03, 2)
        reject_p, query_p, shortfall_p = 0.07, 0.10, 0.12

    sla = SLA[insurer]
    to_medserv = issued + timedelta(days=random.randint(0, 3))
    to_insurer = to_medserv + timedelta(days=random.randint(1, 4))
    pay_days = max(10, round(random.gauss(sla * 0.9, sla * 0.3)))
    paid_at = to_insurer + timedelta(days=pay_days)

    rejected = random.random() < reject_p
    queried = (not rejected) and random.random() < query_p
    shortfall = (not rejected) and (not queried) and random.random() < shortfall_p
    still_draft = random.random() < 0.035

    timeline = [{"stage": "draft", "at": iso(issued)}]
    status = "draft"
    submitted_date = None
    expected = None
    paid_date = None
    query_reason = None
    amount_due = float(amount)
    was_rejected = False

    if not still_draft and to_medserv <= TODAY:
        timeline.append({"stage": "at_medserv", "at": iso(to_medserv)})
        status = "at_medserv"
        submitted_date = to_medserv
        expected = to_insurer + timedelta(days=sla)
        if rejected:
            reject_day = to_medserv + timedelta(days=random.randint(1, 5))
            if reject_day <= TODAY:
                timeline.append({"stage": "rejected", "at": iso(reject_day)})
                status = "rejected"
                was_rejected = True
        if status != "rejected" and to_insurer <= TODAY:
            timeline.append({"stage": "with_insurer", "at": iso(to_insurer)})
            status = "with_insurer"
            if queried:
                query_day = to_insurer + timedelta(days=random.randint(5, 15))
                if query_day <= TODAY:
                    timeline.append({"stage": "insurer_query", "at": iso(query_day)})
                    status = "insurer_query"
                    query_reason = random.choice(QUERY_POOL)
            if status == "with_insurer" and paid_at <= TODAY:
                timeline.append({"stage": "paid", "at": iso(paid_at)})
                status = "paid"
                paid_date = paid_at
                if shortfall:
                    amount_due = round(amount * random.choice([0.10, 0.15, 0.20, 0.25]), 2)
                else:
                    amount_due = 0.0

    invoices.append({
        "id": f"inv_{i+1:04d}",
        "invoice_number": None,
        "payer_type": payer,
        "insurer_name": insurer,
        "patient_ref": f"{random.choice(SURNAME_INITIALS)}.{random.choice(SURNAME_INITIALS)}-{random.randint(1000, 9999)}",
        "description": desc,
        "total": float(amount),
        "amount_due": amount_due,
        "middleman_fee": fee,
        "currency": "GBP",
        "issued_date": iso(issued),
        "submitted_date": iso(submitted_date),
        "expected_payment_date": iso(expected),
        "paid_date": iso(paid_date),
        "pipeline_status": status,
        "query_reason": query_reason,
        "last_chased_at": None,
        "timeline": timeline,
        "validation_issues": [],
        "_was_rejected": was_rejected,
    })

invoices.sort(key=lambda x: x["issued_date"])
reject_index = 0
for idx, inv in enumerate(invoices):
    inv["invoice_number"] = f"INV-2026-{idx+1:04d}"
for inv in invoices:
    if inv.pop("_was_rejected"):
        inv["validation_issues"] = engine_issues(inv, reject_index)
        reject_index += 1
    inv["source"] = "seed"

# ---- report + write ----
paid = [x for x in invoices if x["pipeline_status"] == "paid"]
def dtp(x):
    return (date.fromisoformat(x["paid_date"]) - date.fromisoformat(x["issued_date"])).days
priv = [dtp(x) for x in paid if x["payer_type"] == "private_insurer"]
nhs = [dtp(x) for x in paid if x["payer_type"] == "nhs"]
rejected_rows = [x for x in invoices if x["pipeline_status"] == "rejected"]
print("statuses:", Counter(x["pipeline_status"] for x in invoices))
print(f"median days to pay: private={statistics.median(priv):.0f} nhs={statistics.median(nhs):.0f}")
print(f"rejected with engine-authored issues: {len(rejected_rows)}")
for r in rejected_rows:
    print(f"  {r['invoice_number']}: " + " | ".join(i["field"] + " - " + i["error"] for i in r["validation_issues"]))

out = json.dumps(invoices, indent=2)
for path in [BACKEND / "seeds.json", REPO / "frontend" / "src" / "api" / "seeds.json"]:
    path.write_text(out + "\n")
print("wrote seeds to backend/ and frontend/src/api/")
