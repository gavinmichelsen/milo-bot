"""
Withings API integration for Milo bot.

Handles OAuth 2.0 authentication (with HMAC-SHA256 signed requests)
and fetching weight, body fat, and body composition data.

Withings API docs: https://developer.withings.com/
"""

import hashlib
import hmac
import os
import time
from urllib.parse import urlencode

import httpx

from utils.logger import setup_logger

logger = setup_logger("milo.withings")

WITHINGS_AUTH_URL = "https://account.withings.com/oauth2_user/authorize2"
WITHINGS_TOKEN_URL = "https://wbsapi.withings.net/v2/oauth2"
WITHINGS_MEASURE_URL = "https://wbsapi.withings.net/measure"
WITHINGS_SIGNATURE_URL = "https://wbsapi.withings.net/v2/signature"
REDIRECT_URI = os.getenv(
    "WITHINGS_REDIRECT_URI",
    "https://worker-production-526b.up.railway.app/auth/withings/callback",
)


def _sign(values: list, client_secret: str) -> str:
    """Generate HMAC-SHA256 signature from ordered values.

    Withings signs only specific fields (action, client_id, nonce/timestamp),
    NOT all request params. The caller provides the values in correct order.
    """
    message = ",".join(str(v) for v in values)
    return hmac.new(
        client_secret.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()


def get_auth_url(state: str) -> str:
    """Build the Withings OAuth authorization URL."""
    params = {
        "response_type": "code",
        "client_id": os.getenv("WITHINGS_CLIENT_ID"),
        "redirect_uri": REDIRECT_URI,
        "scope": "user.metrics",
        "state": state,
    }
    return f"{WITHINGS_AUTH_URL}?{urlencode(params)}"


async def _get_nonce() -> str:
    """Fetch a nonce from Withings for request signing."""
    client_id = os.getenv("WITHINGS_CLIENT_ID")
    client_secret = os.getenv("WITHINGS_CLIENT_SECRET")
    ts = str(int(time.time()))

    # Withings signs: action, client_id, timestamp (in that order)
    signature = _sign(["getnonce", client_id, ts], client_secret)
    params = {
        "action": "getnonce",
        "client_id": client_id,
        "timestamp": ts,
        "signature": signature,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(WITHINGS_SIGNATURE_URL, data=params)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != 0:
            raise Exception(f"Withings nonce error: {data}")
        return data["body"]["nonce"]


async def exchange_token(code: str) -> dict:
    """Exchange authorization code for access + refresh tokens."""
    client_id = os.getenv("WITHINGS_CLIENT_ID")
    client_secret = os.getenv("WITHINGS_CLIENT_SECRET")
    nonce = await _get_nonce()

    # Withings signs only: action, client_id, nonce (in that order)
    signature = _sign(["requesttoken", client_id, nonce], client_secret)
    params = {
        "action": "requesttoken",
        "grant_type": "authorization_code",
        "client_id": client_id,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "nonce": nonce,
        "signature": signature,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(WITHINGS_TOKEN_URL, data=params)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != 0:
            raise Exception(f"Withings token exchange error: {data}")
        return data["body"]


async def refresh_withings_token(refresh_token: str) -> dict:
    """Refresh an expired Withings access token."""
    client_id = os.getenv("WITHINGS_CLIENT_ID")
    client_secret = os.getenv("WITHINGS_CLIENT_SECRET")
    nonce = await _get_nonce()

    # Withings signs only: action, client_id, nonce (in that order)
    signature = _sign(["requesttoken", client_id, nonce], client_secret)
    params = {
        "action": "requesttoken",
        "grant_type": "refresh_token",
        "client_id": client_id,
        "refresh_token": refresh_token,
        "nonce": nonce,
        "signature": signature,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(WITHINGS_TOKEN_URL, data=params)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != 0:
            raise Exception(f"Withings token refresh error: {data}")
        return data["body"]


async def get_latest_measurements(access_token: str) -> dict:
    """Fetch latest weight, body fat % from Withings."""
    params = {
        "action": "getmeas",
        "meastype": "1,6,8",
        "category": 1,
        "lastupdate": int(time.time()) - (30 * 24 * 60 * 60),
    }
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            WITHINGS_MEASURE_URL,
            data=params,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != 0:
            raise Exception(f"Withings measure error: {data}")

        measuregrps = data["body"].get("measuregrps", [])
        if not measuregrps:
            return {}

        latest = measuregrps[0]["measures"]
        result = {}
        for m in latest:
            value = m["value"] * (10 ** m["unit"])
            if m["type"] == 1:
                result["weight_lbs"] = round(value * 2.20462, 1)
            elif m["type"] == 6:
                result["fat_ratio"] = round(value, 1)
            elif m["type"] == 8:
                result["fat_mass_kg"] = round(value, 1)
        return result
