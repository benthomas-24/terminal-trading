import requests
import json
import os

# Step 1: exchange secret for access token
secret = os.getenv("PUBLIC_API_SECRET")
if not secret:
    raise SystemExit("PUBLIC_API_SECRET is not set")

token_resp = requests.post(
    "https://api.public.com/userapiauthservice/personal/access-tokens",
    headers={
        "Content-Type": "application/json",
        "User-Agent": "public-dev-docs",
    },
    json={
        "secret": secret,
        "validityInMinutes": 1440,
    },
)
print("Token exchange status:", token_resp.status_code)
print("Token response:", token_resp.json())

token = token_resp.json().get("accessToken") or token_resp.json().get("access_token") or token_resp.json().get("token")
if not token:
    raise SystemExit("Could not extract token from response above")

# Step 2: call account endpoint with the token
account_resp = requests.get(
    "https://api.public.com/userapigateway/trading/account",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "public-dev-docs",
    },
)
print("\nAccount status:", account_resp.status_code)
print("Account response:", json.dumps(account_resp.json(), indent=2))
