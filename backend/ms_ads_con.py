from flask import Flask, redirect, request, session
import requests
import os
from dotenv import load_dotenv
import json

from bingads.authorization import AuthorizationData, OAuthTokens
from bingads.authorization import OAuthWebAuthCodeGrant
from bingads.service_client import ServiceClient

# .env-Datei laden
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# OAuth2 Konfig
CLIENT_ID = os.getenv("MSADS_CLIENT_ID")
CLIENT_SECRET = os.getenv("MSADS_CLIENT_SECRET")
TENANT_ID = os.getenv("MSADS_TENANT_ID", "common")
REDIRECT_URI = os.getenv("MSADS_REDIRECT_URI", "http://localhost:5000/microsoft-ads/callback")


#BING_DEVELOPER_TOKEN = "1076082Q52731399"
BING_DEVELOPER_TOKEN = "BBD37VB98"  # ✅ universeller Sandbox-Token

SCOPE = "https://ads.microsoft.com/msads.manage offline_access"

AUTH_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize"
TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"


@app.route("/microsoft-ads/assign-budget")
def msads_assign_budget():
    try:
        # Token laden
        with open("msads_token.json", "r") as f:
            token_data = json.load(f)
    except FileNotFoundError:
        return "❌ Kein Token gespeichert."

    # Auth & SDK Setup
    oauth_tokens = OAuthTokens(
        access_token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
    )

    authorization_data = AuthorizationData(
        developer_token=BING_DEVELOPER_TOKEN,
        authentication=oauth_tokens,
        customer_id=None,
        account_id=None
    )

    try:
        # GetUser() statt GetCustomersInfo() – stabiler und direkt
        customer_service = ServiceClient(
            service='CustomerManagementService',
            version=13,
            authorization_data=authorization_data,
            environment='sandbox'
        )

        user = customer_service.GetUser().User
        customer_id = user.CustomerId
        accounts = customer_service.GetAccountsInfo(CustomerId=customer_id)
        account_id = accounts[0].Id

        # Setze IDs
        authorization_data.customer_id = customer_id
        authorization_data.account_id = account_id

        # Budget erstellen
        campaign_service = ServiceClient(
            service='CampaignManagementService',
            version=13,
            authorization_data=authorization_data,
            environment='sandbox'
        )

        budget = campaign_service.factory.create('Budget')
        budget.Amount = 100.00
        budget.BudgetType = 'DailyBudgetStandard'
        budget.Name = "SandboxTestBudget"

        response = campaign_service.AddBudgets([budget])
        budget_id = response.BudgetIds.long[0]

        # Kampagnen abrufen
        campaigns = campaign_service.GetCampaignsByAccountId(
            AccountId=account_id,
            CampaignType=['Search']
        )

        if not campaigns['Campaign']:
            return "❌ Keine Kampagnen gefunden."

        kampagne = campaigns['Campaign'][0]
        kampagne.BudgetId = budget_id
        kampagne.Status = 'Active'

        update_request = campaign_service.factory.create('UpdateCampaignsRequest')
        update_request.AccountId = account_id
        update_request.Campaigns = [kampagne]

        campaign_service.UpdateCampaigns(**update_request.__dict__)

        return f"✅ Budget erstellt und Kampagne '{kampagne.Name}' aktiviert (BudgetId: {budget_id})"

    except Exception as e:
        return f"❌ Fehler bei der Budget-Zuweisung: {str(e)}"


# ---------- ROUTE 1: LOGIN ----------
@app.route("/microsoft-ads/login")
def msads_login():
    return redirect(
        f"{AUTH_URL}?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_mode=query"
        f"&scope={SCOPE}"
        f"&state=1234"
    )

# ---------- ROUTE 2: CALLBACK ----------
@app.route("/microsoft-ads/callback")
def msads_callback():
    code = request.args.get("code")
    if not code:
        return f"❌ Fehler: {request.args.get('error_description', 'Kein Code erhalten.')}"

    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
        "scope": SCOPE
    }

    response = requests.post(TOKEN_URL, data=token_data)
    token_result = response.json()

    if "access_token" in token_result:
        with open("msads_token.json", "w") as f:
            json.dump(token_result, f)
        return "✅ Verbindung zu Microsoft Ads erfolgreich!"
    else:
        return f"❌ Fehler beim Token-Abruf: {token_result}"

# ---------- DEBUG: Token anzeigen ----------
@app.route("/token")
def show_token():
    try:
        with open("msads_token.json", "r") as f:
            token_data = json.load(f)
            return token_data.get("access_token", "⚠️ Kein access_token gefunden.")
    except FileNotFoundError:
        return "Noch kein Token gespeichert"

# ---------- Microsoft Ads Kunden-Daten ----------
@app.route("/microsoft-ads/customers")
def msads_customers():
    try:
        with open("msads_token.json", "r") as f:
            token_data = json.load(f)
    except FileNotFoundError:
        return "❌ Kein Token gespeichert."

    try:
        # Auth-Objekt setzen
        auth = OAuthWebAuthCodeGrant(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirection_uri=REDIRECT_URI
        )
        auth._oauth_tokens = OAuthTokens(
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"]
        )

        authorization_data = AuthorizationData(
            developer_token=BING_DEVELOPER_TOKEN,
            authentication=auth,
            customer_id=None,
            account_id=None
        )

        customer_service = ServiceClient(
            service='CustomerManagementService',
            version=13,
            authorization_data=authorization_data,
            environment='sandbox'
        )
        user = customer_service.GetUser()
        return {
            "Name": user.User.Name,
            "UserId": user.User.Id,
            "CustomerId": user.User.CustomerId
        }

    except Exception as e:
        # Fehler = vermutlich ungültiger Token
        os.remove("msads_token.json")
        return f"❌ Fehler beim Abruf: {str(e)} – Token wurde zurückgesetzt. Bitte erneut einloggen."

