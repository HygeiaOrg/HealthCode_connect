# HealthCode Connect

A cashflow and invoice-lifecycle dashboard for UK private-practice doctors. **HealthCode Connect** answers the question doctors ask most: "When do I get paid?"

## The Problem

UK private-practice doctors invoice through a fragmented chain: Semble (appointment transcription) → Healthcode (claim submission) → insurers → payment. Today's tools show payment status in silos — Semble knows when the claim left, Healthcode knows if it reached the insurer, the doctor's bank account shows actual payment. Nobody shows the timeline end-to-end, or predicts when money will arrive.

Meanwhile, rejections happen post-submission, requiring manual rework. Pre-submission validation exists nowhere.

## What We Built

**HealthCode Connect** is a single dashboard that:

1. **Shows the full invoice timeline** — Draft → Submitted to Semble → Sent to Healthcode → With insurer → Paid, each stage dated
2. **Predicts payment dates** — Uses insurer-specific latency data to show "Expected: Dec 15" on every invoice
3. **Validates before submission** — Catches missing data, postcode errors, membership issues *before* the claim leaves, with field-specific fixes
4. **Splits private vs NHS** — Side-by-side comparison of invoice streams with aging buckets per insurer
5. **Surfaces action queues** — "8 invoices stuck with insurer", "2 rejected, need follow-up" — counts that drive the day's work

## Key Features

- **Invoice Dashboard**: Live cashflow view with aging breakdown and status pipeline
- **Pre-Submission Validation**: 29-label PDF extraction + rule engine catches errors before Healthcode
- **Duplicate Detection**: SHA-256 fingerprinting blocks resubmitted claims with new invoice numbers
- **Xero Integration**: Live invoices mapped to pipeline stages, with seeds.json fallback when Xero is unreachable
- **Drive Watcher**: Monitors Google Drive for new PDFs, auto-parses, deduplicates, submits to the API
- **Responsive UI**: React dashboard for desktop; mobile support via responsive layout (responsive only, no native app)

## Demo

[![HealthCode Connect Demo](https://img.shields.io/badge/▶-Watch%20Demo%20Video-blue?style=for-the-badge)](docs/videos/demo.mp4)

A full walkthrough of the dashboard, invoice timeline, validation engine, and payment tracking:

https://github.com/HygeiaOrg/HealthCode_connect/assets/docs/videos/demo.mp4

## Tech Stack

### Frontend
- **React 18** + **TypeScript** + **Vite**
- **Recharts** for timeline and aging-bucket visualizations
- **React Router** for navigation
- **React Query** for API state management
- Responsive design with mobile support

### Backend
- **Python 3.9+** with **FastAPI** / **Uvicorn**
- **Xero API** integration for live invoice data
- **Google Drive API** watcher for PDF ingestion
- **PDF extraction** with 29-label validation engine
- **SQLite** for persistence (dedup index, watcher state)

### Infrastructure
- Local development: backend on port 8000, frontend (Vite) on port 5173
- No containerization required for hackathon; can be adapted for production
- Xero credentials optional; API degrades gracefully without them

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+ (for frontend)
- Optional: Xero OAuth credentials (`XERO_CLIENT_ID` / `XERO_CLIENT_SECRET`)

### Run the Backend
```bash
cd backend
../.venv/bin/pip install -r requirements.txt  # if not already installed
../.venv/bin/uvicorn app:app --port 8000
```

The backend serves:
- `/api/claims` — POST invoices (runs validation first), returns 422 with field-specific errors
- `/invoices` — GET live Xero invoices mapped to pipeline stages
- `/invoices/{id}` — GET single invoice detail
- `/invoices/{id}/record-payment` — POST payment recording
- `/xero/health` — GET Xero connectivity status

### Run the Frontend
```bash
cd frontend
npm install  # if not already installed
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). The frontend runs in **mock mode** by default (no backend required); set `VITE_API_URL=http://localhost:8000` to use the live backend.

### Run Tests
```bash
# Backend
cd backend && python -m pytest

# Frontend
cd frontend && npm run test
```

## Project Structure

```
├── backend/                      # Python FastAPI application
│   ├── app.py                   # Main routes, invoice lifecycle
│   ├── validation/              # Validation engine
│   │   ├── engine.py           # Rule definitions
│   │   ├── pdf_ingest.py       # PDF label extraction (29 labels)
│   │   └── dedup.py            # Duplicate detection by SHA-256
│   ├── xero_client.py          # Xero API wrapper
│   ├── xero_sync.py            # Invoice-to-pipeline-stage mapping
│   ├── drive_watcher.py        # Google Drive PDF monitor
│   ├── invoice_store.py        # Persistence layer
│   ├── seeds.json              # Demo data (used when Xero unreachable)
│   └── requirements.txt
│
├── frontend/                     # React + Vite application
│   ├── src/
│   │   ├── components/         # UI components
│   │   ├── pages/              # Route pages (Dashboard, Invoice Detail)
│   │   ├── api/                # API client and data fetching
│   │   ├── hooks/              # Custom React hooks
│   │   └── App.tsx             # Main app
│   ├── vite.config.ts          # Vite configuration
│   ├── package.json
│   └── tsconfig.json
│
├── design/                       # UX design research
│   ├── DESIGN.md               # Competitive analysis (22 products)
│   └── references/             # Screenshots from competitors
│
├── docs/                         # Implementation guides
│   ├── REAL_WORLD_VERIFICATION.md  # How validation maps to Healthcode
│   ├── XERO_LIVE_HANDOFF.md        # Xero integration details
│   └── xero-mcp.md                 # Xero MCP server usage
│
├── shared-api-contract.json    # Single source of truth for API schemas
├── PROGRESS.md                 # Latest feature additions (July 2026)
└── README.md                   # This file
```

## Data Models

All API responses conform to `shared-api-contract.json`. Key types:

- **Invoice**: ID, amount, payer, stage (DRAFT | SUBMITTED | AUTHORISED | PAID | VOIDED), dates, timeline events
- **ValidationError**: Field, rule name, human-readable message, and a suggested fix
- **Pipeline Stage**: DRAFT → at_medserv (Semble) → with_insurer → paid or rejected

See `shared-api-contract.json` for the complete schema.

## Design Decisions

The MVP prioritizes:

1. **Landing screen = cashflow answer** — Expected money, outstanding total, action queue. Zero clicks to "when do I get paid?"
2. **Pipeline as filter** — One segmented bar showing £ amount and count per stage; clicking a stage filters the invoice list
3. **Per-invoice timeline** — Inline expansion shows dated milestones (submitted, insurer received, expected payment)
4. **Pre-submission validation** — Named checks with pass/fail chips; live count reaches zero before invoice can submit
5. **Private vs NHS comparison** — Paired series showing dual income streams with aging buckets per payer

See `design/DESIGN.md` for full competitive analysis and decision rationale.

## Development

### Adding a New Validation Rule

1. Define the rule in `backend/validation/engine.py`
2. Add test cases to `backend/test_claim.py`
3. Run `pytest` to verify
4. The frontend's pre-submission panel will automatically surface the error

### Connecting to Live Xero

1. Register your app at [Xero Developer Portal](https://developer.xero.com)
2. Set environment variables:
   ```bash
   export XERO_CLIENT_ID=your_client_id
   export XERO_CLIENT_SECRET=your_client_secret
   ```
3. Restart the backend; the first request will trigger OAuth flow
4. Live invoices will appear on the dashboard; seeds.json is used as fallback if Xero is unreachable

### Watching Google Drive for PDFs

Set `CLAIMS_API_URL` and optional `GOOGLE_DRIVE_FOLDER_ID` in `.env`, then:
```bash
python backend/drive_watcher.py
```

The watcher:
- Polls Google Drive for new PDFs
- Parses each with the validation engine (29 labels)
- Deduplicates by MD5 checksum
- POSTs to `/api/claims`; 422-rejected claims are parked, not retried

## Status

This is a **hackathon POC** (proof of concept) built in July 2026. Production readiness would require:

- [ ] Authentication & authorization (role-based access)
- [ ] Persistence layer upgrade (PostgreSQL instead of SQLite)
- [ ] Containerization (Docker for backend and frontend)
- [ ] Performance optimization (caching, database indexing)
- [ ] Mobile app (currently responsive web only)
- [ ] Error recovery and retry logic for Xero sync
- [ ] Audit logging and compliance features

## Contributing

Open an issue or PR. Code follows these conventions:

- **Backend**: PEP 8 with type hints; test every validation rule
- **Frontend**: React best practices, no external component libraries beyond Recharts
- **Commits**: One feature or fix per commit; include why in the message, not just what

## License

Proprietary — built for Hygeia Org.

## Contact

For questions about the design decisions or integration points, see `design/DESIGN.md` and `docs/`.
