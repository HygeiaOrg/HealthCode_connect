import os
from dotenv import load_dotenv
from xero_python.api_client import ApiClient, Configuration
from xero_python.api_client.oauth2 import OAuth2Token
from xero_python.accounting import AccountingApi

# Load environment variables from .env file
load_dotenv()

XERO_CLIENT_ID = os.getenv("XERO_CLIENT_ID")
XERO_CLIENT_SECRET = os.getenv("XERO_CLIENT_SECRET")


def get_xero_client() -> ApiClient:
    """
    Initializes and returns the Xero ApiClient configured for Client Credentials flow.
    Used for premium Custom Connections.
    """
    if not XERO_CLIENT_ID or not XERO_CLIENT_SECRET:
        raise ValueError(
            "XERO_CLIENT_ID and XERO_CLIENT_SECRET must be set in the .env file."
        )
    
    # Configure ApiClient with Client Credentials
    config = Configuration(
        oauth2_token=OAuth2Token(
            client_id=XERO_CLIENT_ID,
            client_secret=XERO_CLIENT_SECRET,
            grant_type="client_credentials"
        )
    )
    
    return ApiClient(config)

def get_accounting_api() -> AccountingApi:
    """
    Returns an instance of AccountingApi configured with the custom connection ApiClient.
    """
    client = get_xero_client()
    return AccountingApi(client)

def test_connection():
    """
    Helper function to test the connection by fetching organisation details.
    With Custom Connections, the tenant ID parameter is passed as an empty string.
    """
    try:
        accounting_api = get_accounting_api()
        # Retrieve organization details (empty string for tenant ID)
        organisations = accounting_api.get_organisations(xero_tenant_id="")
        if organisations and organisations.organisations:
            org = organisations.organisations[0]
            print(f"Successfully connected to Xero! Organisation Name: {org.name}")
            return {
                "success": True,
                "organisation_name": org.name,
                "organisation_id": org.organisation_id
            }
        else:
            print("Connected, but no organisations found.")
            return {"success": False, "error": "No organisations found."}
    except Exception as e:
        print(f"Error testing connection: {str(e)}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Test connection when run directly
    print("Testing Xero connection...")
    test_connection()
