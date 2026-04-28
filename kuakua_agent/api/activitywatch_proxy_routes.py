from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response
import httpx

from kuakua_agent.services.settings_service import get_settings_service

router = APIRouter(tags=["activitywatch-proxy"])


async def _forward(method: str, path: str, request: Request) -> Response:
    settings = get_settings_service().get_settings()
    base_url = str(settings.aw_server_url).rstrip("/")
    target_url = f"{base_url}{path}"
    body = await request.body()

    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in {"host", "content-length", "connection"}
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            upstream = await client.request(
                method,
                target_url,
                content=body or None,
                headers=headers,
            )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"ActivityWatch upstream error: {exc}") from exc

    response_headers = {
        key: value
        for key, value in upstream.headers.items()
        if key.lower() not in {"content-encoding", "transfer-encoding", "connection"}
    }
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
        media_type=upstream.headers.get("content-type"),
    )


@router.get("/0/buckets/")
async def proxy_list_buckets(request: Request) -> Response:
    return await _forward("GET", "/api/0/buckets/", request)


@router.post("/0/buckets/{bucket_id}")
async def proxy_create_bucket(bucket_id: str, request: Request) -> Response:
    return await _forward("POST", f"/api/0/buckets/{bucket_id}", request)


@router.post("/0/buckets/{bucket_id}/events")
async def proxy_bucket_events(bucket_id: str, request: Request) -> Response:
    return await _forward("POST", f"/api/0/buckets/{bucket_id}/events", request)
