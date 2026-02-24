from fastapi import APIRouter
from app.core.settings import settings


class ApiRouter:
    def __init__(self):
        self.api_version = settings.API_VERSION
        self.router = APIRouter(
            prefix=f"/api/v{self.api_version}",
        )

    def get_router(self) -> APIRouter:
        return self.router