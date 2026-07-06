"""Live-mode surface for the React frontend: merged GET /invoices,
GET /analytics/summary, and the fix-queue action endpoints. Seed invoices
mutate in the server-side store exactly like frontend/src/api/mock.ts;
Xero-sourced invoices get real history notes. All Xero traffic goes through
xero_sync.get_api(), monkeypatched to a fake AccountingApi."""
import datetime
import json
from types import SimpleNamespace as NS

import pytest
from fastapi.testclient import TestClient

import invoice_store
import xero_sync
from app import app

client = TestClient(app)

TODAY_ISO = "2026-07-04"  # demo clock, pinned in invoice_store and pipeline.ts


def fake_invoice(**over):
    base = dict(
        invoice_id="xid-1",
        invoice_number="INV-100",
        contact=NS(name="Bupa"),
        reference="A.B-1234",
        total=250.0,
        amount_due=250.0,
        amount_paid=0.0,
        amount_credited=0.0,
        fully_paid_on_date=None,
        status="DRAFT",
        date=datetime.date(2026, 6, 1),
        due_date=datetime.date(2026, 7, 1),
        line_items=[NS(description="Initial consultation")],
    )
    base.update(over)
    return NS(**base)


class FakeAccountingApi:
    """The slice of test_xero_endpoints' fake these paths use, plus history."""

    def __init__(self, invoices=()):
        self.by_id = {i.invoice_id: i for i in invoices}
        self.calls = []

    def get_invoices(self, xero_tenant_id, **kw):
        self.calls.append(("get_invoices", kw.get("where")))
        return NS(invoices=list(self.by_id.values()))

    def get_invoice(self, xero_tenant_id, invoice_id, **kw):
        self.calls.append(("get_invoice", invoice_id))
        if invoice_id not in self.by_id:
            raise RuntimeError("invoice not found")
        return NS(invoices=[self.by_id[invoice_id]])

    def update_invoice(self, xero_tenant_id, invoice_id, invoices=None, **kw):
        status = invoices.invoices[0].status
        self.calls.append(("update_invoice", invoice_id, status))
        self.by_id[invoice_id].status = status
        return NS(invoices=[self.by_id[invoice_id]])

    def create_invoice_history(self, xero_tenant_id, invoice_id, history_records=None,
                               idempotency_key=None, **kw):
        details = history_records.history_records[0].details
        self.calls.append(("create_invoice_history", invoice_id, details, idempotency_key))
        return NS(history_records=history_records.history_records)


@pytest.fixture(autouse=True)
def fresh_store():
    invoice_store.reset()
    yield
    invoice_store.reset()


@pytest.fixture
def install(monkeypatch):
    def _install(api):
        monkeypatch.setattr(xero_sync, "get_api", lambda: api)
        return api
    return _install


@pytest.fixture
def xero_down(monkeypatch):
    def _raise():
        raise RuntimeError("no credentials")
    monkeypatch.setattr(xero_sync, "get_api", _raise)


def seed_where(**want):
    for inv in invoice_store.list_invoices():
        if all(inv.get(k) == v for k, v in want.items()):
            return inv
    raise AssertionError(f"no seed matches {want}")


# ---------- store actions mirror mock.ts ----------

def test_resubmit_clears_issues_and_moves_to_medserv(xero_down):
    seed = seed_where(pipeline_status="rejected")
    assert seed["validation_issues"]
    body = client.post(f"/invoices/{seed['id']}/resubmit").json()
    assert body["pipeline_status"] == "at_medserv"
    assert body["validation_issues"] == []
    assert body["submitted_date"] == TODAY_ISO
    assert body["timeline"][:-1] == seed["timeline"]
    assert body["timeline"][-1] == {"stage": "at_medserv", "at": TODAY_ISO}
    again = client.get(f"/invoices/{seed['id']}").json()  # persists across requests
    assert again["pipeline_status"] == "at_medserv" and again["validation_issues"] == []


def test_reply_moves_query_to_with_insurer(xero_down):
    seed = seed_where(pipeline_status="insurer_query")
    res = client.post(f"/invoices/{seed['id']}/reply", json={"message": "GP report attached."})
    assert res.status_code == 200
    body = res.json()
    assert body["pipeline_status"] == "with_insurer"
    assert body["query_reason"] is None
    assert body["timeline"][-1] == {"stage": "with_insurer", "at": TODAY_ISO}
    assert client.get(f"/invoices/{seed['id']}").json()["pipeline_status"] == "with_insurer"


def test_submit_moves_seed_draft_to_medserv(xero_down):
    seed = seed_where(pipeline_status="draft")
    body = client.post(f"/invoices/{seed['id']}/submit").json()
    assert body["pipeline_status"] == "at_medserv"
    assert body["submitted_date"] == TODAY_ISO
    assert body["timeline"][-1] == {"stage": "at_medserv", "at": TODAY_ISO}
    assert client.get(f"/invoices/{seed['id']}").json()["submitted_date"] == TODAY_ISO


def test_chase_stamps_last_chased_at_only(xero_down):
    seed = seed_where(pipeline_status="with_insurer")
    body = client.post(f"/invoices/{seed['id']}/chase").json()
    assert body["last_chased_at"] == TODAY_ISO
    assert body["pipeline_status"] == "with_insurer"
    assert body["timeline"] == seed["timeline"]  # chase appends no timeline event
    assert client.get(f"/invoices/{seed['id']}").json()["last_chased_at"] == TODAY_ISO


def test_resolve_zeroes_amount_due(xero_down):
    seed = next(i for i in invoice_store.list_invoices() if i["amount_due"] > 0)
    body = client.post(f"/invoices/{seed['id']}/resolve").json()
    assert body["amount_due"] == 0
    assert client.get(f"/invoices/{seed['id']}").json()["amount_due"] == 0


def test_action_on_unknown_id_is_404(install):
    install(FakeAccountingApi())
    for action in ("resubmit", "chase", "resolve", "submit"):
        assert client.post(f"/invoices/absent/{action}").status_code == 404
    assert client.post("/invoices/absent/reply", json={"message": "x"}).status_code == 404


def test_action_on_non_store_id_is_502_when_xero_down(xero_down):
    assert client.post("/invoices/xid-9/chase").status_code == 502


# ---------- merged GET /invoices ----------

def test_merged_list_puts_xero_first_then_seeds(install):
    install(FakeAccountingApi([
        fake_invoice(),
        fake_invoice(invoice_id="xid-2", invoice_number="INV-101", status="AUTHORISED"),
    ]))
    body = client.get("/invoices").json()
    assert len(body) == 2 + len(invoice_store.list_invoices())
    assert [r["source"] for r in body[:2]] == ["xero", "xero"]
    assert all(r["source"] == "seed" for r in body[2:])
    assert {body[0]["id"], body[1]["id"]} == {"xid-1", "xid-2"}


def test_merged_list_filters_span_both_sources(install):
    install(FakeAccountingApi([fake_invoice(status="DRAFT")]))
    drafts = client.get("/invoices", params={"status": "draft"}).json()
    assert drafts[0]["source"] == "xero"
    assert len(drafts) > 1 and all(r["pipeline_status"] == "draft" for r in drafts)
    assert {r["source"] for r in drafts[1:]} == {"seed"}
    hits = client.get("/invoices", params={"q": "INV-100"}).json()  # matches Xero only
    assert [r["id"] for r in hits] == ["xid-1"]


def test_list_is_store_only_when_xero_down(xero_down):
    body = client.get("/invoices").json()
    assert len(body) == len(invoice_store.list_invoices())
    assert all(r["source"] == "seed" for r in body)


# ---------- GET /analytics/summary ----------

def days(a: str, b: str) -> int:
    return (datetime.date.fromisoformat(b) - datetime.date.fromisoformat(a)).days


def test_summary_matches_mock_computation_over_seeds(xero_down):
    with open(xero_sync.SEEDS_PATH) as f:
        seeds = json.load(f)
    body = client.get("/analytics/summary").json()
    assert set(body) == {
        "outstanding_total", "expected_this_month", "expected_this_month_by",
        "overdue_total", "median_days_to_payment", "fees_paid_ytd",
        "rejected_count", "stale_count", "pipeline_totals",
    }

    owed = [i for i in seeds if i["pipeline_status"] != "rejected" and i["amount_due"] > 0]
    assert body["outstanding_total"] == round(sum(i["amount_due"] for i in owed), 2)

    live = [i for i in seeds if i["pipeline_status"] not in ("paid", "rejected")]
    due = [i for i in live if (i.get("expected_payment_date") or "")[:7] == "2026-07"]
    assert body["expected_this_month"] == pytest.approx(sum(i["amount_due"] for i in due))
    assert body["expected_this_month_by"] == max(i["expected_payment_date"] for i in due)
    overdue = [
        i for i in live
        if i.get("expected_payment_date") and i["expected_payment_date"] < TODAY_ISO
    ]
    assert body["overdue_total"] == pytest.approx(sum(i["amount_due"] for i in overdue))

    paid = [i for i in seeds if i["pipeline_status"] == "paid" and i["paid_date"]]
    for payer in ("private_insurer", "nhs"):
        xs = sorted(days(i["issued_date"], i["paid_date"])
                    for i in paid if i["payer_type"] == payer)
        m = len(xs) // 2
        want = xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m] + 1) // 2  # JS Math.round
        assert body["median_days_to_payment"][payer] == want

    fees = sum(i["middleman_fee"] for i in paid if i["paid_date"].startswith("2026"))
    assert body["fees_paid_ytd"] == round(fees, 2)
    assert body["rejected_count"] == sum(1 for i in seeds if i["pipeline_status"] == "rejected")
    assert body["stale_count"] == sum(
        1 for i in live if days(i["timeline"][-1]["at"], TODAY_ISO) >= 14
    )
    assert [t["status"] for t in body["pipeline_totals"]] == [
        "draft", "at_medserv", "with_insurer", "insurer_query", "paid", "rejected",
    ]
    for t in body["pipeline_totals"]:
        rows = [i for i in seeds if i["pipeline_status"] == t["status"]]
        assert t["count"] == len(rows)
        assert t["amount"] == pytest.approx(sum(i["total"] for i in rows))


def test_summary_includes_xero_invoices_when_reachable(install):
    install(FakeAccountingApi([fake_invoice(status="SUBMITTED")]))  # -> at_medserv
    seed_count = sum(
        1 for i in invoice_store.list_invoices() if i["pipeline_status"] == "at_medserv"
    )
    row = next(t for t in client.get("/analytics/summary").json()["pipeline_totals"]
               if t["status"] == "at_medserv")
    assert row["count"] == seed_count + 1


# ---------- actions on Xero-sourced invoices ----------

def test_chase_on_xero_invoice_writes_history_note(install):
    api = install(FakeAccountingApi([fake_invoice(status="AUTHORISED")]))
    res = client.post("/invoices/xid-1/chase")
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == "xid-1" and body["source"] == "xero"
    notes = [c for c in api.calls if c[0] == "create_invoice_history"]
    assert len(notes) == 1
    assert notes[0][1] == "xid-1" and "chaser" in notes[0][2].lower()
    assert notes[0][3]  # idempotency key sent


def test_reply_on_xero_invoice_notes_the_message(install):
    api = install(FakeAccountingApi([fake_invoice(status="AUTHORISED")]))
    res = client.post("/invoices/xid-1/reply", json={"message": "GP referral attached"})
    assert res.status_code == 200
    note = next(c for c in api.calls if c[0] == "create_invoice_history")
    assert "GP referral attached" in note[2]


def test_resubmit_on_xero_invoice_notes_and_remaps(install):
    api = install(FakeAccountingApi([fake_invoice(status="SUBMITTED")]))
    body = client.post("/invoices/xid-1/resubmit").json()
    assert body["pipeline_status"] == "at_medserv" and body["source"] == "xero"
    assert any(c[0] == "create_invoice_history" for c in api.calls)


def test_resolve_on_xero_invoice_is_422(install):
    install(FakeAccountingApi([fake_invoice(status="AUTHORISED")]))
    res = client.post("/invoices/xid-1/resolve")
    assert res.status_code == 422
    assert "credit note" in res.json()["detail"]


def test_history_note_failure_is_502(install):
    api = install(FakeAccountingApi([fake_invoice(status="AUTHORISED")]))

    def boom(*args, **kwargs):
        raise RuntimeError("nope")

    api.create_invoice_history = boom
    assert client.post("/invoices/xid-1/chase").status_code == 502
