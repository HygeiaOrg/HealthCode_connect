# Connecting the frontend to real Xero data (handoff for John)

Branch: `andrii/bg-work`. Everything here was tested end to end on 2026-07-05 with the Xero SDK mocked at the boundary (113 backend tests green, browser flows verified). The only untested step is the one that needs the credentials you hold: a live token fetch against your Custom Connection. This doc walks that last mile with an expected result at every step, so a failure points at exactly one cause.

## What the app does in live mode

With `VITE_API_URL` set, the frontend stops using its client-side demo dataset and reads everything from the FastAPI backend. `GET /invoices` returns the real ACCREC invoices from Xero first (each tagged `"source": "xero"`), followed by the seeded demo invoices that keep the Fix queue interesting. Xero statuses map onto the pipeline: DRAFT shows as draft, SUBMITTED as at Medserv, AUTHORISED as with insurer (or insurer query once partially paid), PAID as paid, VOIDED as rejected. Amounts, amount due and paid dates come from Xero's own fields. The sidebar badge flips from "Xero · demo data" to "Xero · connected".

## Steps

1. Check out the branch and set credentials:

   ```bash
   git fetch origin && git checkout andrii/bg-work
   cd backend
   cp .env.example .env   # then fill in:
   # XERO_CLIENT_ID=...
   # XERO_CLIENT_SECRET=...
   ```

   If your Custom Connection has the settings scope enabled (needed for recording payments), also add:
   `XERO_SCOPES=accounting.transactions accounting.contacts accounting.settings.read`
   Without that line the code requests the same two scopes it always has, so whatever worked for you before keeps working.

2. Environment and backend:

   ```bash
   ./setup_venv.sh          # from the repo root, or reuse your existing venv
   cd backend
   ../.venv/bin/uvicorn app:app --port 8000    # adjust the venv path to yours
   ```

3. Prove the Xero connection before touching the frontend:

   ```bash
   curl -s localhost:8000/xero/health
   ```

   Expected: `{"connected": true, "org_name": "<your org>", "error": null}`.
   If `connected` is false, the `error` string tells you which stage failed; see troubleshooting below.

4. Frontend in live mode:

   ```bash
   cd frontend
   npm install
   VITE_API_URL=http://localhost:8000 npm run dev
   ```

   Open http://localhost:5173. Expected: green dot + "Xero · connected" in the sidebar, and any ACCREC invoices from your org at the top of the table. If the org has none yet, the table shows only seed data until step 5 creates one.

5. Full loop: create a real invoice through the claims pipeline, then pay it.

   ```bash
   curl -s -X POST localhost:8000/api/claims -H 'Content-Type: application/json' -d '{
     "patient_name": "Amelia Hart",
     "patient_dob": "1981-03-14",
     "insurance_company_name": "Bupa",
     "policy_number": "MB1234567",
     "auth_code": "12345678",
     "treatment_date": "2026-06-20",
     "procedures": [{"procedure_code": "CONS-INIT", "description": "Initial consultation", "fee": 250.0}]
   }'
   ```

   Expected: 200 with `xero_invoice_id`. Refresh the app: the invoice appears at the top as a draft. Check the Xero UI too; there is a DRAFT invoice for contact Bupa. (This payload is exactly what the Drive watcher produces from `backend/samples/valid_01_bupa_consult.pdf`. Send an invalid claim, for example `"auth_code": "BAD"`, and you get a 422 with field-level issues instead; nothing reaches Xero.)

   Then, using the `xero_invoice_id` from the response:

   ```bash
   curl -s -X POST localhost:8000/invoices/<xero_invoice_id>/submit
   curl -s -X POST localhost:8000/invoices/<xero_invoice_id>/record-payment \
     -H 'Content-Type: application/json' -d '{"amount": 250.0, "reference": "BUPA remittance TEST-1"}'
   ```

   Expected: submit returns the invoice at the at-Medserv stage; record-payment authorises then pays it, and the response shows `amount_due: 0` with a `fully_paid_on` date. Refresh the app and the invoice sits in the paid column; Xero shows the payment on the invoice. Partial amounts work too and leave the invoice as an insurer-query (shortfall) case.

6. Optional, your Drive watcher against the same backend:

   ```bash
   cd backend
   CLAIMS_API_URL=http://localhost:8000 python drive_watcher.py
   ```

   It now parses with the shared 29-label parser, dedups on Drive content hashes across restarts (`backend/.watcher_state.json`), follows pagination, and retries failed posts. A PDF that fails validation is logged with its issues and parked, not retried forever.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| health: `unsupported_grant_type` or `invalid_client` | Credentials are wrong or the app is not a Custom Connection. Re-copy the secret from the developer portal. |
| health: `invalid_scope` | The connection does not have a requested scope enabled. Either enable the missing scope in the portal or set `XERO_SCOPES` in `.env` to exactly the scopes the connection has. |
| health ok, table shows only seed rows | The org simply has no ACCREC invoices yet; run step 5. |
| record-payment returns 502 mentioning accounts | The settings scope is missing (see step 1) or the org has no bank / payments-enabled account. Enable payments on an account in Xero, or add the scope. |
| Port 8000 busy | Pick any port for uvicorn and use the same value in `VITE_API_URL`. |
| Frontend badge stays "demo data" | `VITE_API_URL` was not set when Vite started; restart `npm run dev` with it. |

Notes: CORS is open, so ports do not need to match. Rate limits are 60 calls/min per tenant; the app stays far under that. The Demo Company connects to a Custom Connection free of charge, and it resets every 28 days, dropping the connection when it does. Nothing on `main` or `backend-phase2` was modified; this branch is additive and safe to discard if anything misbehaves.
