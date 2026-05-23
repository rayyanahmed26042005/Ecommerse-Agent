"""Catalog API routes."""

from fastapi import APIRouter, Response

from app.services.catalog_service import get_essentials, get_personal_picks, get_trending

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/trending")
async def trending(response: Response):
    items = get_trending()
    response.headers["Cache-Control"] = "public, max-age=300"
    return [i.model_dump() for i in items]


@router.get("/essentials")
async def essentials(response: Response):
    items = get_essentials()
    response.headers["Cache-Control"] = "public, max-age=300"
    return [i.model_dump() for i in items]


@router.get("/picks/{user_id}")
async def picks(user_id: str, response: Response):
    items = get_personal_picks(user_id)
    response.headers["Cache-Control"] = "public, max-age=60"
    return [i.model_dump() for i in items]
