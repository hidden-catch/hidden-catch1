from fastapi import APIRouter, status

from app.core.config import settings

api_router = APIRouter()


@api_router.get("/healthz", status_code=status.HTTP_200_OK)
def health_check():
    return {"service": settings.app_name, "status": "ok"}
