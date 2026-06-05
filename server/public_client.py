import httpx
from fastapi import HTTPException
from auth import get_access_token, invalidate_token

BASE_URL = "https://api.public.com"


async def api_get(path: str, params: dict | None = None) -> dict:
    token = await get_access_token()
    async with httpx.AsyncClient() as client:
        resp = await _do_get(client, path, token, params)
        if resp.status_code == 401:
            await invalidate_token()
            token = await get_access_token()
            resp = await _do_get(client, path, token, params)
        if resp.status_code == 401:
            raise HTTPException(status_code=502, detail="Auth failed — check PUBLIC_API_SECRET")
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=str(e))
        return resp.json()


async def _do_get(
    client: httpx.AsyncClient, path: str, token: str, params: dict | None
) -> httpx.Response:
    return await client.get(
        f"{BASE_URL}{path}",
        headers={"Authorization": f"Bearer {token}"},
        params=params or {},
    )
