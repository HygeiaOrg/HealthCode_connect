# andrii/bg-work — what this branch adds (2026-07-05)

This branch sits on top of `andrii/backend-merge-safe-to-push` (the verified merge of `backend-phase2` and `andrii/pdf-validation-and-ui`; one trivial `.gitignore` conflict, resolved by union). Test suite: **113 passed** (73 from the merge + 40 new). Nothing on `main`, `backend-phase2`, or `andrii/pdf-validation-and-ui` was touched.

## New since the merge

1. **Xero lifecycle endpoints** (`backend/app.py`, `backend/xero_sync.py`)
   - `POST /api/claims` now runs the validation engine first and returns 422 with field/error/solution issues before anything reaches Xero. Contact upsert by email (no more duplicate contacts), idempotency keys on all writes.
   - `POST /invoices/{id}/record-payment` (authorise-then-pay, partial payments supported), `POST /invoices/{id}/submit`, `GET /xero/health`.
   - `GET /invoices` and `GET /invoices/{id}` from the shared contract: live Xero data mapped to pipeline stages (DRAFT→draft, SUBMITTED→at_medserv, AUTHORISED→with_insurer or insurer_query by paid amounts, PAID→paid, VOIDED→rejected), automatic seeds.json fallback when Xero is unreachable.

2. **Duplicate-claim detection** (`backend/validation/dedup.py`)
   - Activates the dormant `ledger` param of `validate_invoice`: reusing a known invoice number now trips `cross.duplicate_number` over HTTP.
   - New rule `dedup.duplicate_claim`: SHA-256 fingerprint over canonicalised identity fields catches the same claim resubmitted under a NEW number. In-memory by default; set `DEDUP_INDEX_PATH` for persistence.

3. **Drive watcher fixes** (`backend/drive_watcher.py`)
   - Parses PDFs with the shared `validation/pdf_ingest.py` (29 labels) instead of two regexes with hardcoded Bupa placeholders.
   - Dedup keyed on Drive `md5Checksum`, persisted to `backend/.watcher_state.json`: restarts no longer create duplicate Xero drafts.
   - Follows `nextPageToken`; failed POSTs retry, 422-rejected claims are parked, `CLAIMS_API_URL` env var.

4. **Xero MCP wiring** (`.mcp.json`, `.claude/skills/xero-python/SKILL.md`, `docs/xero-mcp.md`)
   - Official `@xeroapi/xero-mcp-server` registered (env-var refs only, no secrets), official Xero skill vendored, usage doc with domain prompts.

## Verified as a user (2026-07-05, no Xero credentials on the test machine)

- Browser flow: dashboard renders 115 invoices; Fix-queue dropzone returns the green pass card for `valid_01_bupa_consult.pdf` and a 2-issue table for `invalid_01_postcode_nhs.pdf`.
- Watcher replay: `invalid_02_wpa_membership.pdf` mapped and POSTed to `/api/claims` → 422 with the WPA membership issue; `valid_01` passes the gate and stops cleanly at the credential-less Xero boundary (502).
- Dedup over HTTP: golden fixture valid; same content under a new number → `dedup.duplicate_claim` naming the original invoice.

## Run it

```bash
cd backend && ../.venv/bin/uvicorn app:app --port 8000   # one process serves everything
cd frontend && npm run dev                                # leave VITE_API_URL unset (mock mode + real PDF check)
```

Real-Xero E2E still needs `XERO_CLIENT_ID`/`XERO_CLIENT_SECRET` in `backend/.env`; every endpoint degrades cleanly without them.
