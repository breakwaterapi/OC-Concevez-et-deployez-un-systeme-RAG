import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from api.common.config import get_settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_rebuild_api_key(api_key: str | None = Security(_api_key_header)) -> None:
    settings = get_settings()
    if not settings.rebuild_api_key or not secrets.compare_digest(
        api_key or "", settings.rebuild_api_key
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid X-API-Key header.",
        )
