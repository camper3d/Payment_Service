from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware для проверки API-ключа в заголовках запроса."""
    async def dispatch(self, request: Request, call_next):
        """Перехватывает запрос, проверяет API-ключ и передает управление дальше"""
        if request.url.path.startswith("/api/"):
            api_key = request.headers.get("X-API-Key")

            if not api_key or api_key != settings.api_key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or missing API Key"
                )

        response = await call_next(request)
        return response