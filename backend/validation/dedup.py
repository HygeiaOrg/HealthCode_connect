"""Duplicate-claim detection: a ledger of invoice numbers the practice has
already issued (feeds rule cross.duplicate_number), plus content
fingerprinting that catches the same claim resubmitted under a fresh number:
same patient, policy, episode and money means the same claim."""
from __future__ import annotations

import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path

from .engine import get_path

PKG_DIR = Path(__file__).parent
SEEDS_PATH = PKG_DIR.parent / "seeds.json"
DEFAULT_INDEX_PATH = PKG_DIR / ".dedup_index.json"


@lru_cache(maxsize=1)
def load_ledger() -> frozenset[str]:
    """Invoice numbers already used by the practice, from the seed ledger."""
    seeds = json.loads(SEEDS_PATH.read_text())
    return frozenset(s["invoice_number"] for s in seeds if s.get("invoice_number"))


def _text(value) -> str | None:
    text = str(value).strip().casefold() if value is not None else ""
    return text or None


def _money(value) -> float | None:
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def _codes(values) -> list[str]:
    return sorted(c for c in (_text(v) for v in values or []) if c)


def canonical_fingerprint(invoice: dict) -> str:
    """SHA-256 hex over a canonical JSON of the claim's identity fields.

    invoice_number is deliberately excluded: identical content resubmitted
    under a new number must still collide. Strings are stripped and
    casefolded, money rounded to 2dp, code lists sorted, missing fields null,
    so the digest is deterministic and order-insensitive.
    """
    identity = {
        "invoice_date": _text(invoice.get("invoice_date")),
        "patient": {k: _text(get_path(invoice, f"patient.{k}"))
                    for k in ("first_name", "surname", "date_of_birth", "nhs_number")},
        "policy": {k: _text(get_path(invoice, f"policy.{k}"))
                   for k in ("insurer_id", "membership_number")},
        "episode": {
            "admission_date": _text(get_path(invoice, "episode.admission_date")),
            "discharge_date": _text(get_path(invoice, "episode.discharge_date")),
            "diagnoses": _codes(get_path(invoice, "episode.diagnoses")),
            "procedures": _codes(get_path(invoice, "episode.procedures")),
        },
        "totals": {k: _money(get_path(invoice, f"totals.{k}"))
                   for k in ("net", "vat", "gross")},
    }
    canon = json.dumps(identity, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


class FingerprintIndex:
    """Map of fingerprint -> first-seen invoice number.

    In-memory when path is None; with a path, entries load at construction
    and every new entry is saved back (the file is only created on save).
    """

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self._first_seen: dict[str, str] = {}
        if self.path is not None:
            self.load(self.path)

    def load(self, path: str | Path) -> None:
        """A missing or corrupt file starts the index empty rather than crash."""
        try:
            data = json.loads(Path(path).read_text())
        except (OSError, ValueError):
            data = None
        self._first_seen = ({str(k): str(v) for k, v in data.items()}
                            if isinstance(data, dict) else {})

    def save(self, path: str | Path | None = None) -> None:
        target = Path(path) if path else self.path
        if target is not None:
            target.write_text(json.dumps(self._first_seen, indent=2, sort_keys=True))

    def check(self, invoice: dict) -> str | None:
        """Record this claim; return the earlier invoice number when the same
        content was already claimed under a DIFFERENT number, else None."""
        number = str(invoice.get("invoice_number") or "").strip()
        fingerprint = canonical_fingerprint(invoice)
        first = self._first_seen.get(fingerprint)
        if first is not None:
            return None if first == number else first
        if number:
            self._first_seen[fingerprint] = number
            self.save()
        return None


def _module_index() -> FingerprintIndex:
    # In-memory by default so test runs and demo restarts start clean; set
    # DEDUP_INDEX_PATH (DEFAULT_INDEX_PATH is a sensible value) to persist.
    return FingerprintIndex(os.environ.get("DEDUP_INDEX_PATH") or None)


INDEX = _module_index()


def reset_index(index: FingerprintIndex | None = None) -> FingerprintIndex:
    """Swap the module index; tests install a fresh in-memory one."""
    global INDEX
    INDEX = index if index is not None else _module_index()
    return INDEX
