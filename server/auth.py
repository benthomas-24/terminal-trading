import os
import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.public.com"
_cached_token: str | None = None


def get_secret() -> str:
    secret = os.getenv("PUBLIC_API_SECRET")
    if not secret:
        raise EnvironmentError("PUBLIC_API_SECRET is not set")
    return secret


async def get_access_token() -> str:
    global _cached_token
    if env_token := os.getenv("PUBLIC_ACCESS_TOKEN"):
        return env_token
    if _cached_token:
        return _cached_token
    _cached_token = await _fetch_token()
    return _cached_token


async def _fetch_token() -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/userapigateway/personal/access-tokens",
            headers={"Authorization": f"Bearer {get_secret()}"},
        )
        resp.raise_for_status()
        data = resp.json()
        # Key may vary — try common shapes
        return data.get("access_token") or data.get("token") or data["accessToken"]


async def invalidate_token() -> None:
    global _cached_token
    _cached_token = None
