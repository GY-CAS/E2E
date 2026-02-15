from app.api.endpoints.projects import router as projects_router
from app.api.endpoints.documents import router as documents_router
from app.api.endpoints.function_points import router as function_points_router
from app.api.endpoints.testcases import router as testcases_router
from app.api.endpoints.testscripts import router as testscripts_router
from app.api.endpoints.generator import router as generator_router

__all__ = [
    "projects_router",
    "documents_router",
    "function_points_router",
    "testcases_router",
    "testscripts_router",
    "generator_router"
]
