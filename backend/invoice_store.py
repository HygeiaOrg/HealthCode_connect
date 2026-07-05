"""Server-side session store for the seed invoices.

Mirrors frontend/src/api/mock.ts: seeds.json is loaded once into memory and the
fix-queue actions mutate that copy in place, so in live mode the demo shows
invoices moving between refreshes without touching the fixture on disk.
Xero-sourced invoices never enter this store; app.py merges them in front.
"""
import copy
import datetime
import json

from xero_sync import SEEDS_PATH, filter_invoices

# Demo clock: seeds are generated against this date and the frontend pins the
# same value (frontend/src/lib/pipeline.ts TODAY), so summaries and mutation
# timestamps agree between mock and live modes.
TODAY = datetime.date(2026, 7, 4)
TODAY_ISO = TODAY.isoformat()

_db: dict[str, dict] = {}


def reset() -> None:
    """Reload the fixture; tests call this to isolate mutations."""
    global _db
    with open(SEEDS_PATH) as f:
        _db = {r["id"]: r for r in json.load(f)}


reset()


def _find(invoice_id: str) -> dict | None:
    inv = _db.get(invoice_id)
    if inv is not None:
        return inv
    for record in _db.values():
        if record.get("invoice_number") == invoice_id:
            return record
    return None


def _require(invoice_id: str) -> dict:
    inv = _find(invoice_id)
    if inv is None:
        raise KeyError(f"invoice {invoice_id} not in the seed store")
    return inv


def list_invoices(payer_type=None, status=None, q=None) -> list[dict]:
    records = sorted(_db.values(), key=lambda r: r["issued_date"], reverse=True)
    return copy.deepcopy(filter_invoices(records, payer_type=payer_type, status=status, q=q))


def get(invoice_id: str) -> dict | None:
    inv = _find(invoice_id)
    return copy.deepcopy(inv) if inv is not None else None


# ---------- fix-queue actions (mock.ts state transitions) ----------

def resubmit(invoice_id: str) -> dict:
    inv = _require(invoice_id)
    inv["pipeline_status"] = "at_medserv"
    inv["validation_issues"] = []
    inv["submitted_date"] = TODAY_ISO
    inv["timeline"] = inv["timeline"] + [{"stage": "at_medserv", "at": TODAY_ISO}]
    return copy.deepcopy(inv)


def reply(invoice_id: str) -> dict:
    inv = _require(invoice_id)
    inv["pipeline_status"] = "with_insurer"
    inv["query_reason"] = None
    inv["timeline"] = inv["timeline"] + [{"stage": "with_insurer", "at": TODAY_ISO}]
    return copy.deepcopy(inv)


def submit_draft(invoice_id: str) -> dict:
    inv = _require(invoice_id)
    inv["pipeline_status"] = "at_medserv"
    inv["submitted_date"] = TODAY_ISO
    inv["timeline"] = inv["timeline"] + [{"stage": "at_medserv", "at": TODAY_ISO}]
    return copy.deepcopy(inv)


def chase(invoice_id: str) -> dict:
    inv = _require(invoice_id)
    inv["last_chased_at"] = TODAY_ISO
    return copy.deepcopy(inv)


def resolve(invoice_id: str) -> dict:
    inv = _require(invoice_id)
    inv["amount_due"] = 0
    return copy.deepcopy(inv)


# ---------- analytics (mockSummary) ----------

STAGES = ["draft", "at_medserv", "with_insurer", "insurer_query", "paid", "rejected"]


def _days_between(a: str, b: datetime.date) -> int:
    return (b - datetime.date.fromisoformat(a[:10])).days


def _median(xs: list[int]) -> int | None:
    if not xs:
        return None
    s = sorted(xs)
    m = len(s) // 2
    # JS Math.round: halves round up, so an even count averages with +0.5.
    return s[m] if len(s) % 2 else (s[m - 1] + s[m] + 1) // 2


def _is_live(inv: dict) -> bool:
    return inv["pipeline_status"] not in ("paid", "rejected")


def _is_overdue(inv: dict) -> bool:
    due = inv.get("expected_payment_date")
    return _is_live(inv) and bool(due) and datetime.date.fromisoformat(due) < TODAY


def _days_in_stage(inv: dict) -> int:
    timeline = inv.get("timeline") or []
    return _days_between(timeline[-1]["at"], TODAY) if timeline else 0


def summarize(records: list[dict]) -> dict:
    """mockSummary() from frontend/src/api/mock.ts, over the merged list."""
    owed = [i for i in records if i["pipeline_status"] != "rejected" and i["amount_due"] > 0]
    live = [i for i in records if _is_live(i)]
    this_month = TODAY_ISO[:7]
    due_this_month = [
        i for i in live
        if i.get("expected_payment_date") and i["expected_payment_date"][:7] == this_month
    ]
    paid = [i for i in records if i["pipeline_status"] == "paid"]

    def mdays(payer: str) -> int | None:
        return _median([
            _days_between(i["issued_date"], datetime.date.fromisoformat(i["paid_date"]))
            for i in paid if i["payer_type"] == payer and i.get("paid_date")
        ])

    fees = sum(
        i["middleman_fee"] for i in paid
        if i.get("paid_date") and i["paid_date"].startswith("2026")
    )
    return {
        "outstanding_total": round(sum(i["amount_due"] for i in owed), 2),
        "expected_this_month": sum(i["amount_due"] for i in due_this_month),
        "expected_this_month_by": max(
            (i["expected_payment_date"] for i in due_this_month), default=None
        ),
        "overdue_total": sum(i["amount_due"] for i in live if _is_overdue(i)),
        "median_days_to_payment": {
            "private_insurer": mdays("private_insurer"), "nhs": mdays("nhs"),
        },
        "fees_paid_ytd": round(fees, 2),
        "rejected_count": sum(1 for i in records if i["pipeline_status"] == "rejected"),
        "stale_count": sum(1 for i in live if _days_in_stage(i) >= 14),
        "pipeline_totals": [
            {
                "status": stage,
                "amount": sum(i["total"] for i in records if i["pipeline_status"] == stage),
                "count": sum(1 for i in records if i["pipeline_status"] == stage),
            }
            for stage in STAGES
        ],
    }
