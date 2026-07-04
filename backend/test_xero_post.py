from xero_client import get_xero_client
from xero_python.accounting import Invoice, LineItem, Contact
import os

client = get_xero_client()
print("Xero Client configured.")

try:
    contact = Contact(name="Bupa")
    line_item = LineItem(
        description="Test Invoice from Python",
        quantity=1.0,
        unit_amount=150.00,
        account_code="200" # Sales account code
    )
    invoice = Invoice(
        type="ACCREC",
        contact=contact,
        line_items=[line_item],
        status="DRAFT"
    )
    print("Sending invoice to Xero...")
    invoices = client.accounting_api.create_invoices(
        xero_tenant_id="", # Custom Connection
        invoices={"invoices": [invoice]}
    )
    print(f"Success! Invoice ID: {invoices.invoices[0].invoice_id}")
except Exception as e:
    print(f"Failed: {e}")
