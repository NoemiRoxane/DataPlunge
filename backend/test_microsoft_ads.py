import os
import requests
from dotenv import load_dotenv

load_dotenv()

TENANT_ID = os.getenv("MICROSOFT_TENANT_ID")
CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
REDIRECT_URI = os.getenv("MICROSOFT_REDIRECT_URI")

# 1. Authorization Code Flow
auth_code = input("✏️ Bitte Authorization Code eingeben: ").strip()

token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
token_data = {
    "client_id": CLIENT_ID,
    "scope": "https://ads.microsoft.com/msads.manage offline_access",
    "code": auth_code,
    "redirect_uri": REDIRECT_URI,
    "grant_type": "authorization_code",
    "client_secret": CLIENT_SECRET
}

token_response = requests.post(token_url, data=token_data).json()
print("🔐 Token Response:")
print(token_response)

access_token = token_response.get("access_token")

if not access_token:
    print("❌ Kein Access Token erhalten.")
    exit(1)

# 2. Kunden & Accounts direkt via REST abfragen
headers = {
    "Authorization": f"Bearer {access_token}",
    "DeveloperToken": os.getenv("BING_DEVELOPER_TOKEN"),
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Versuch, Benutzerinformationen abzurufen
customer_url = "https://api.ads.microsoft.com/v13/customers/getuser"
print("\n📡 Abruf von Benutzerinfo via REST...")

response = requests.post(customer_url, headers=headers, json={})
print("🔍 Benutzerinfo:")
print(response.text)
