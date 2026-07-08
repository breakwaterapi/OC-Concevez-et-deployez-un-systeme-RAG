from fastapi import Request
from fastapi.responses import JSONResponse

from api.common.exceptions import DomainError


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})
