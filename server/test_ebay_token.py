"""Test eBay OAuth token fetch and print the full response."""
import asyncio
import base64
import httpx
import os, sys

# Load .env manually
env = {}
with open(".env") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()

client_id = env.get("EBAY_CLIENT_ID", "")
client_secret = env.get("EBAY_CLIENT_SECRET", "")

print(f"Client ID    : {client_id}")
print(f"Client Secret: {client_secret}")
print(f"Secret length: {len(client_secret)} chars")
print()

async def test_token():
    is_sandbox = "SBX" in client_id
    token_url = (
        "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
        if is_sandbox
        else "https://api.ebay.com/identity/v1/oauth2/token"
    )
    encoded_creds = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            token_url,
            data={
                "grant_type": "client_credentials",
                "scope": "https://api.ebay.com/oauth/api_scope",
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {encoded_creds}",
            },
        )
    print(f"HTTP Status  : {resp.status_code}")
    print(f"Response     : {resp.text[:500]}")

asyncio.run(test_token())
