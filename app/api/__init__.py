from app.extensions.app_extensions import ApiRouter
from app.api.v1.github_routes import router as github_router

# Create the versioned API router and register all routes here
_api_router = ApiRouter()
_api_router.get_router().include_router(github_router)

api_router = _api_router.get_router()
