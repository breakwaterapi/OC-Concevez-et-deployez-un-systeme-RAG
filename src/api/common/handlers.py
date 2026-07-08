from fastapi import Request
from fastapi.responses import JSONResponse

from api.common.exceptions import DomainError


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    headers = {"Retry-After": str(exc.retry_after)} if exc.retry_after else None
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)}, headers=headers)
