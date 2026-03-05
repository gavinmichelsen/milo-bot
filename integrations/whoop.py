"""
Whoop API integration for Milo bot.

Handles OAuth 2.0 authentication and fetching recovery, strain,
sleep, workout, and body measurement data from the Whoop platform.

Whoop API docs: https://developer.whoop.com/
"""

import os
from urllib.parse import urlencode

import aiohttp
import httpx

from utils.logger import setup_logger

logger = setup_logger("milo.whoop")

WHOOP_AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
WHOOP_TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
WHOOP_API_BASE = "https://api.prod.whoop.com/developer/v2"


def kilojoules_to_calories(kj: float) -> float:
    """Convert kilojoules to calories (1 kJ = 0.239006 calories)."""
    if kj is None:
        return None
    return round(kj * 0.239006, 1)


def kilograms_to_pounds(kg: float) -> float:
    """Convert kilograms to pounds (1 kg = 2.20462 lbs)."""
    if kg is None:
        return None
    return round(kg * 2.20462, 1)


def meters_to_feet(meters: float) -> float:
    """Convert meters to feet (1 m = 3.28084 feet)."""
    if meters is None:
        return None
    return round(meters * 3.28084, 1)


class WhoopClient:
    """Client for interacting with the Whoop API.

    Manages OAuth tokens and provides methods to fetch
    recovery, sleep, strain, workout, and body data for a user.
    """

    def __init__(self):
        self.client_id = os.getenv("WHOOP_CLIENT_ID")
        self.client_secret = os.getenv("WHOOP_CLIENT_SECRET")
        self.http = httpx.AsyncClient()

    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        """Generate the OAuth authorization URL for a user to connect Whoop.

        Args:
            redirect_uri: Callback URL after authorization.
            state: Unique state parameter to prevent CSRF.

        Returns:
            Full authorization URL to redirect the user to.
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "read:recovery read:sleep read:workout read:cycles read:body_measurement offline",
            "state": state,
        }
        return f"{WHOOP_AUTH_URL}?{urlencode(params)}"

    async def exchange_token(self, code: str, redirect_uri: str) -> dict:
        """Exchange an authorization code for access and refresh tokens.

        Args:
            code: Authorization code from the OAuth callback.
            redirect_uri: The same redirect URI used in the auth request.

        Returns:
            Token response dict with access_token, refresh_token, etc.
        """
        response = await self.http.post(
            WHOOP_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        response.raise_for_status()
        logger.info("Successfully exchanged Whoop OAuth token")
        return response.json()

    async def get_recovery(self, access_token: str) -> dict:
        """Fetch the latest recovery data from the v2 API."""
        response = await self.http.get(
            f"{WHOOP_API_BASE}/recovery",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"limit": 1},
        )
        response.raise_for_status()
        return response.json()

    async def get_sleep(self, access_token: str) -> dict:
        """Fetch the latest sleep data from the v2 API."""
        response = await self.http.get(
            f"{WHOOP_API_BASE}/activity/sleep",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"limit": 1},
        )
        response.raise_for_status()
        return response.json()

    async def get_cycles(self, access_token: str, limit: int = 1) -> dict:
        """Fetch the latest daily cycles (strain data) from the v2 API.

        Args:
            access_token: Valid Whoop access token.
            limit: Number of cycles to fetch (default 1).

        Returns:
            JSON response with cycle data including strain, heart rate, kilojoules.
        """
        response = await self.http.get(
            f"{WHOOP_API_BASE}/cycles",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"limit": limit},
        )
        response.raise_for_status()
        return response.json()

    async def get_workouts(self, access_token: str, limit: int = 1) -> dict:
        """Fetch the latest workouts from the v2 API.

        Args:
            access_token: Valid Whoop access token.
            limit: Number of workouts to fetch (default 1).

        Returns:
            JSON response with workout data including strain, heart rate, zones.
        """
        response = await self.http.get(
            f"{WHOOP_API_BASE}/activity/workout",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"limit": limit},
        )
        response.raise_for_status()
        return response.json()

    async def get_body_measurements(self, access_token: str) -> dict:
        """Fetch the user's body measurements from the v2 API.

        Args:
            access_token: Valid Whoop access token.

        Returns:
            JSON response with height, weight, max heart rate.
        """
        response = await self.http.get(
            f"{WHOOP_API_BASE}/user/body/measurements",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()

    async def close(self):
        """Close the underlying HTTP client."""
        await self.http.aclose()


async def refresh_whoop_token(refresh_token: str) -> dict:
    """Exchange a refresh token for a new access + refresh token pair."""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            WHOOP_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": os.getenv("WHOOP_CLIENT_ID"),
                "client_secret": os.getenv("WHOOP_CLIENT_SECRET"),
                "scope": "offline",
            },
        ) as resp:
            resp.raise_for_status()
            return await resp.json()