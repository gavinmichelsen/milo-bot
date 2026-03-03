"""
Withings API integration for Milo bot.

Handles OAuth 2.0 authentication and fetching body composition
data (weight, body fat %, muscle mass) from the Withings platform.

Withings API docs: https://developer.withings.com/
"""

import os

import httpx

from utils.logger import setup_logger

logger = setup_logger("milo.withings")

WITHINGS_AUTH_URL = "https://account.withings.com/oauth2_user/authorize2"
WITHINGS_TOKEN_URL = "https://wbsapi.withings.net/v2/oauth2"
WITHINGS_MEASURE_URL = "https://wbsapi.withings.net/measure"


class WithingsClient:
    """Client for interacting with the Withings API.

    Manages OAuth tokens and provides methods to fetch
    body composition measurements for a user.
    """

    def __init__(self):
        self.client_id = os.getenv("WITHINGS_CLIENT_ID")
        self.client_secret = os.getenv("WITHINGS_CLIENT_SECRET")
        self.http = httpx.AsyncClient()

    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        """Generate the OAuth authorization URL for a user to connect Withings.

        Args:
            redirect_uri: Callback URL after authorization.
            state: Unique state parameter to prevent CSRF.

        Returns:
            Full authorization URL to redirect the user to.
        """
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": "user.metrics",
            "state": state,
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{WITHINGS_AUTH_URL}?{query}"

    async def exchange_token(self, code: str, redirect_uri: str) -> dict:
        """Exchange an authorization code for access and refresh tokens.

        Args:
            code: Authorization code from the OAuth callback.
            redirect_uri: The same redirect URI used in the auth request.

        Returns:
            Token response dict with access_token, refresh_token, etc.
        """
        response = await self.http.post(
            WITHINGS_TOKEN_URL,
            data={
                "action": "requesttoken",
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        response.raise_for_status()
        logger.info("Successfully exchanged Withings OAuth token")
        return response.json()

    async def get_body_measures(self, access_token: str) -> dict:
        """Fetch the latest body composition measurements.

        Retrieves weight, body fat percentage, muscle mass,
        and other body metrics from the user's Withings account.

        Args:
            access_token: Valid Withings access token.

        Returns:
            Measurement data including weight, body fat, and muscle mass.
        """
        response = await self.http.post(
            WITHINGS_MEASURE_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            data={
                "action": "getmeas",
                "meastypes": "1,6,76",  # Weight, Fat %, Muscle Mass
                "category": 1,  # Real measurements only
                "lastupdate": 0,
            },
        )
        response.raise_for_status()
        return response.json()

    async def close(self):
        """Close the underlying HTTP client."""
        await self.http.aclose()
