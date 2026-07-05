"""The Xero-facing HTTP surface: claims gate, payment recording, contract
invoice listing with seeds fallback, submit transition and the health probe.
All Xero traffic goes through xero_sync.get_api(), monkeypatched to a fake
AccountingApi that records every call."""
import datetime
from types import SimpleNamespace as NS

import pytest
from fastapi.testclient import TestClient

import xero_sync
from app import app

client = TestClient(app)

PAY_DAY = datetime.date(2026, 7, 5)


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
    def __init__(self, invoices=(), fail=False):
        self.by_id = {i.invoice_id: i for i in invoices}
        self.fail = fail
        self.calls = []
        self.contacts = []
        self.created_invoices = []

    def _guard(self):
        if self.fail:
            raise RuntimeError("xero down")

    def get_invoices(self, xero_tenant_id, **kw):
        self._guard()
        self.calls.append(("get_invoices", kw.get("where")))
        return NS(invoices=list(self.by_id.values()))

    def get_invoice(self, xero_tenant_id, invoice_id, **kw):
        self._guard()
        self.calls.append(("get_invoice", invoice_id))
        if invoice_id not in self.by_id:
            raise RuntimeError("invoice not found")
        return NS(invoices=[self.by_id[invoice_id]])

    def update_invoice(self, xero_tenant_id, invoice_id, invoices=None, **kw):
        self._guard()
        status = invoices.invoices[0].status
        self.calls.append(("update_invoice", invoice_id, status))
        self.by_id[invoice_id].status = status
        return NS(invoices=[self.by_id[invoice_id]])

    def create_payment(self, xero_tenant_id, payment=None, idempotency_key=None, **kw):
        self._guard()
        self.calls.append(("create_payment", payment.invoice.invoice_id,
                           payment.amount, idempotency_key))
        inv = self.by_id[payment.invoice.invoice_id]
        inv.amount_paid = round(inv.amount_paid + payment.amount, 2)
        inv.amount_due = round(inv.amount_due - payment.amount, 2)
        if inv.amount_due <= 0.001:  # Xero flips to PAID itself
            inv.status = "PAID"
            inv.fully_paid_on_date = PAY_DAY
        return NS(payments=[NS(payment_id="pay-1")])

    def get_accounts(self, xero_tenant_id, where=None, **kw):
        self._guard()
        self.calls.append(("get_accounts", where))
        return NS(accounts=[NS(code="090")])

    def get_organisations(self, xero_tenant_id, **kw):
        self._guard()
        return NS(organisations=[NS(name="Demo Practice Ltd", organisation_id="org-1")])

    def get_contacts(self, xero_tenant_id, where=None, **kw):
        self._guard()
        self.calls.append(("get_contacts", where))
        hits = [c for c in self.contacts if where and c.email_address in where]
        return NS(contacts=hits)

    def create_contacts(self, xero_tenant_id, contacts=None, idempotency_key=None, **kw):
        self._guard()
        wanted = contacts.contacts[0]
        made = NS(contact_id=f"c-{len(self.contacts) + 1}",
                  name=wanted.name, email_address=wanted.email_address)
        self.contacts.append(made)
        self.calls.append(("create_contacts", wanted.name))
        return NS(contacts=[made])

    def create_invoices(self, xero_tenant_id, invoices=None, idempotency_key=None, **kw):
        self._guard()
        self.calls.append(("create_invoices", idempotency_key))
        self.created_invoices.append(invoices.invoices[0])
        return NS(invoices=[NS(invoice_id="new-xid", invoice_number="INV-999")])


@pytest.fixture
def install(monkeypatch):
    def _install(api):
        monkeypatch.setattr(xero_sync, "get_api", lambda: api)
        monkeypatch.setattr(xero_sync, "_account_code", None)
        return api
    return _install


@pytest.fixture
def xero_down(monkeypatch):
    def _raise():
        raise RuntimeError("no credentials")
    monkeypatch.setattr(xero_sync, "get_api", _raise)


def valid_claim(**over):
    claim = {
        "patient_name": "Amelia Hart",
        "patient_dob": "1981-03-14",
        "insurance_company_name": "Bupa",
        "policy_number": "BUP12345678",
        "auth_code": "12345678",
        "treatment_date": "2026-06-20",
        "procedures": [
            {"procedure_code": "CONS-INIT", "description": "Initial consultation", "fee": 250.0}
        ],
    }
    claim.update(over)
    return claim


# ---------- claims gate ----------

def test_invalid_claim_is_422_and_never_reaches_xero(install):
    api = install(FakeAccountingApi())
    res = client.post("/api/claims", json=valid_claim(patient_dob="2030-01-01", auth_code="BAD"))
    assert res.status_code == 422
    body = res.json()
    assert body["valid"] is False
    assert {i["rule"] for i in body["issues"]} == {"format.preauth", "cross.dob_after_treatment"}
    for issue in body["issues"]:
        assert set(issue) == {"field", "error", "solution", "severity", "rule", "path"}
        assert not issue["path"].startswith(("practice", "provider"))
    assert api.calls == []


def test_valid_claim_passes_gate_and_creates_invoice_idempotently(install):
    api = install(FakeAccountingApi())
    res = client.post("/api/claims", json=valid_claim())
    assert res.status_code == 200
    assert res.json()["xero_invoice_id"] == "new-xid"
    create = [c for c in api.calls if c[0] == "create_invoices"]
    assert len(create) == 1 and create[0][1]  # idempotency key sent


def test_claim_contact_upsert_reuses_contact_found_by_email(install):
    api = install(FakeAccountingApi())
    api.contacts.append(NS(contact_id="c-77", name="Bupa", email_address="claims@bupa.co.uk"))
    res = client.post("/api/claims", json=valid_claim(insurer_email="claims@bupa.co.uk"))
    assert res.status_code == 200
    assert ("get_contacts", 'EmailAddress=="claims@bupa.co.uk"') in api.calls
    assert not any(c[0] == "create_contacts" for c in api.calls)
    assert api.created_invoices[0].contact.contact_id == "c-77"


def test_claim_contact_upsert_creates_contact_when_email_unknown(install):
    api = install(FakeAccountingApi())
    res = client.post("/api/claims", json=valid_claim(insurer_email="new@axa.co.uk"))
    assert res.status_code == 200
    assert ("create_contacts", "Bupa") in api.calls


# ---------- record-payment ----------

def test_record_payment_authorises_a_draft_then_pays_in_full(install):
    api = install(FakeAccountingApi([fake_invoice()]))
    res = client.post("/invoices/xid-1/record-payment",
                      json={"amount": 250.0, "reference": "BACS-1"})
    assert res.status_code == 200
    assert res.json() == {
        "invoice_id": "xid-1",
        "status": "PAID",
        "amount_paid": 250.0,
        "amount_due": 0.0,
        "fully_paid_on": "2026-07-05",
        "payment_id": "pay-1",
    }
    ordered = [c[:3] for c in api.calls if c[0] in ("update_invoice", "create_payment")]
    assert ordered == [
        ("update_invoice", "xid-1", "SUBMITTED"),
        ("update_invoice", "xid-1", "AUTHORISED"),
        ("create_payment", "xid-1", 250.0),
    ]


def test_partial_payment_leaves_invoice_authorised(install):
    install(FakeAccountingApi([fake_invoice(status="AUTHORISED")]))
    res = client.post("/invoices/xid-1/record-payment", json={"amount": 100.0})
    body = res.json()
    assert res.status_code == 200
    assert body["status"] == "AUTHORISED"
    assert body["amount_paid"] == 100.0 and body["amount_due"] == 150.0
    assert body["fully_paid_on"] is None


def test_overpayment_is_422(install):
    install(FakeAccountingApi([fake_invoice(status="AUTHORISED", amount_due=100.0)]))
    res = client.post("/invoices/xid-1/record-payment", json={"amount": 150.0})
    assert res.status_code == 422
    assert "exceeds" in res.json()["detail"]


def test_record_payment_unknown_invoice_is_404(install):
    install(FakeAccountingApi())
    assert client.post("/invoices/nope/record-payment", json={"amount": 10.0}).status_code == 404


def test_record_payment_is_502_when_xero_unreachable(xero_down):
    assert client.post("/invoices/xid-1/record-payment", json={"amount": 10.0}).status_code == 502


# ---------- GET /invoices ----------

XERO_STATUS_TO_PIPELINE = [
    (fake_invoice(invoice_id="a", status="DRAFT"), "draft"),
    (fake_invoice(invoice_id="b", status="SUBMITTED"), "at_medserv"),
    (fake_invoice(invoice_id="c", status="AUTHORISED"), "with_insurer"),
    (fake_invoice(invoice_id="d", status="AUTHORISED", amount_paid=50.0, amount_due=200.0),
     "insurer_query"),
    (fake_invoice(invoice_id="e", status="PAID", amount_paid=250.0, amount_due=0.0,
                  fully_paid_on_date=PAY_DAY), "paid"),
    (fake_invoice(invoice_id="f", status="VOIDED"), "rejected"),
]


def test_list_maps_every_xero_status_to_pipeline_status(install):
    install(FakeAccountingApi([inv for inv, _ in XERO_STATUS_TO_PIPELINE]))
    res = client.get("/invoices")
    assert res.status_code == 200
    body = res.json()
    assert isinstance(body, list)  # client.ts expects bare Invoice[], no envelope
    # Merged list: the Xero block comes first, seed-store invoices after it.
    xero_rows = body[:len(XERO_STATUS_TO_PIPELINE)]
    assert all(r["source"] == "seed" for r in body[len(XERO_STATUS_TO_PIPELINE):])
    got = {r["id"]: r["pipeline_status"] for r in xero_rows}
    assert got == {inv.invoice_id: want for inv, want in XERO_STATUS_TO_PIPELINE}
    for r in xero_rows:
        assert r["source"] == "xero"
        assert {"invoice_number", "payer_type", "insurer_name", "patient_ref", "total",
                "amount_due", "middleman_fee", "currency", "issued_date",
                "pipeline_status", "timeline", "validation_issues"} <= set(r)


def test_list_derives_contract_fields_from_xero_data(install):
    install(FakeAccountingApi([
        fake_invoice(invoice_id="p", status="PAID", amount_paid=250.0, amount_due=0.0,
                     fully_paid_on_date=PAY_DAY),
        fake_invoice(invoice_id="n", contact=NS(name="NHS England"), total=100.0),
    ]))
    by_id = {r["id"]: r for r in client.get("/invoices").json()}
    private, nhs = by_id["p"], by_id["n"]
    assert private["payer_type"] == "private_insurer"
    assert private["middleman_fee"] == 7.5  # 3% of 250, as in gen_seeds.py
    assert private["paid_date"] == "2026-07-05"
    assert private["patient_ref"] == "A.B-1234" and private["insurer_name"] == "Bupa"
    assert nhs["payer_type"] == "nhs" and nhs["middleman_fee"] == 0.0


def test_list_falls_back_to_seeds_when_xero_down(xero_down):
    res = client.get("/invoices")
    body = res.json()
    assert res.status_code == 200 and body
    assert all(r["source"] == "seed" for r in body)
    filtered = client.get("/invoices", params={"payer_type": "nhs", "q": "NHS"}).json()
    assert filtered and all(
        r["payer_type"] == "nhs" and "nhs" in r["insurer_name"].lower() for r in filtered
    )
    one_status = client.get("/invoices", params={"status": "paid"}).json()
    assert one_status and all(r["pipeline_status"] == "paid" for r in one_status)


def test_get_single_invoice_from_xero_and_seeds(install):
    install(FakeAccountingApi([fake_invoice()]))
    body = client.get("/invoices/xid-1").json()
    assert body["id"] == "xid-1" and body["source"] == "xero"
    # Unknown in Xero -> seeds by id; unknown everywhere -> 404.
    seed_id = xero_sync.load_seeds()[0]["id"]
    seeded = client.get(f"/invoices/{seed_id}").json()
    assert seeded["id"] == seed_id and seeded["source"] == "seed"
    assert client.get("/invoices/absent-everywhere").status_code == 404


# ---------- submit ----------

def test_submit_moves_draft_to_at_medserv(install):
    api = install(FakeAccountingApi([fake_invoice()]))
    res = client.post("/invoices/xid-1/submit")
    assert res.status_code == 200
    assert res.json()["pipeline_status"] == "at_medserv"
    assert ("update_invoice", "xid-1", "SUBMITTED") in api.calls


def test_submit_rejects_non_draft(install):
    install(FakeAccountingApi([fake_invoice(status="PAID")]))
    assert client.post("/invoices/xid-1/submit").status_code == 422


# ---------- health ----------

def test_health_reports_org_when_connected(install):
    install(FakeAccountingApi())
    assert client.get("/xero/health").json() == {
        "connected": True, "org_name": "Demo Practice Ltd", "error": None,
    }


def test_health_degrades_cleanly_when_xero_down(xero_down):
    body = client.get("/xero/health").json()
    assert body["connected"] is False and body["org_name"] is None
    assert body["error"]
