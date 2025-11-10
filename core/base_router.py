from fastapi import APIRouter


def get_base_router(app_prefix: str = "", tags: list = []) -> APIRouter:
    base_prefix = "/api/v1"
    return APIRouter(prefix=base_prefix + app_prefix, tags=tags)
