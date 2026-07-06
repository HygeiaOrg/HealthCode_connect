# Xero MCP server in this repo

This repo ships an `.mcp.json` that wires up the official Xero MCP server, `@xeroapi/xero-mcp-server`. It is a stdio server launched with `npx`, and it authenticates with the same Custom Connection (client_credentials) app the backend uses. No extra Xero setup is required: the two env vars below are the same ones `backend/app.py` reads.

## How to use it

1. Open Claude Code in the repo root. `.mcp.json` is picked up automatically (approve the server when prompted).
2. Export the credentials in the shell you launch Claude Code from:

   ```sh
   export XERO_CLIENT_ID=...
   export XERO_CLIENT_SECRET=...
   ```

3. Ask Claude something about the org. The server exchanges the client credentials for a token itself; with a Custom Connection there is one org, so no tenant selection is needed (the backend uses `xero_tenant_id=""` for the same reason).

Secrets never go in `.mcp.json`. The file references `${XERO_CLIENT_ID}` and `${XERO_CLIENT_SECRET}`, which are expanded from the environment at launch.

## Tools relevant to this app

The server exposes ~50 tools. For a UK private-practice invoicing app these matter most:

- `list-invoices`, `create-invoice`
- `list-payments`, `create-payment`
- `list-aged-receivables-by-contact`
- `list-organisation-details`

Constraint worth remembering: `create-payment` only works against an invoice with status `AUTHORISED`. A `DRAFT` invoice must be approved first, which mirrors how the backend submits invoices.

## Scopes

The Custom Connection should be configured with the granular scopes: `accounting.invoices`, `accounting.payments`, `accounting.contacts`, and `accounting.settings.read`. The broad `accounting.transactions` scope is deprecated in favour of these; both the backend and the MCP server work with the granular set.

## Example prompts

- "List all unpaid invoices for Bupa and total the amount outstanding."
- "A remittance came in for 240 GBP from AXA Health. Record a payment against their oldest AUTHORISED invoice."
- "Show aged receivables per insurer contact and flag anyone with a balance older than 60 days."
