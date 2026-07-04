"""Deterministic validation pipeline for UK private medical invoices.

Four pure layers, run in order, each a function of the invoice and the
bundled dictionaries: structural (JSON Schema), formats (regex + checksums),
dictionary (code membership), cross-field (conditional logic). No network,
no models, no randomness: the same invoice always yields the same issues.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PKG_DIR = Path(__file__).parent
DICT_DIR = PKG_DIR / "dictionaries"


@dataclass(frozen=True)
class Issue:
    field: str          # human label, e.g. "Diagnosis Code"
    error: str
    solution: str
    severity: str = "error"   # "error" blocks submission; "warning" does not
    rule_id: str = ""
    path: str = ""            # machine path, e.g. "episode.diagnoses[0]"

    def to_contract(self) -> dict:
        """The wire shape used by shared-api-contract.json ValidationIssue."""
        return {"field": self.field, "error": self.error, "solution": self.solution}


@dataclass(frozen=True)
class Dictionaries:
    insurers: dict
    icd10: dict
    ccsd: dict
    specialists: dict
    payee_providers: dict
    treatment_sites: dict
    charge_codes: dict


def _read(name: str) -> dict:
    return json.loads((DICT_DIR / name).read_text())


@lru_cache(maxsize=1)
def load_dictionaries() -> Dictionaries:
    providers = _read("providers.json")
    return Dictionaries(
        insurers=_read("insurers.json")["insurers"],
        icd10=_read("icd10_subset.json")["codes"],
        ccsd=_read("ccsd_subset.json")["codes"],
        specialists=providers["specialists"],
        payee_providers=providers["payee_providers"],
        treatment_sites=providers["treatment_sites"],
        charge_codes=_read("charge_codes.json")["codes"],
    )


@lru_cache(maxsize=1)
def load_schema() -> dict:
    return json.loads((PKG_DIR / "schema.json").read_text())


def get_path(obj: dict, dotted: str, default=None):
    """Safe nested getter: get_path(inv, 'patient.postcode')."""
    cur = obj
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def validate_invoice(invoice: dict, *, ledger: frozenset[str] = frozenset()) -> list[Issue]:
    """Run all layers; returns issues in layer order, deduplicated."""
    from .rules import cross_field, dictionary, formats, structural

    d = load_dictionaries()
    issues: list[Issue] = []
    issues += structural.check(invoice, load_schema())
    issues += formats.check(invoice, d)
    issues += dictionary.check(invoice, d)
    issues += cross_field.check(invoice, d, ledger=ledger)

    seen: set[tuple[str, str]] = set()
    out: list[Issue] = []
    for i in issues:
        key = (i.path or i.field, i.error)
        if key in seen:
            continue
        seen.add(key)
        out.append(i)
    return out


def is_valid(issues: list[Issue]) -> bool:
    return not any(i.severity == "error" for i in issues)
