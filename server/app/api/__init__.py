from fastapi import APIRouter
from app.api.chat_apis.chat_api import chat_router
from app.api.profile_apis.profile import profile_router
from app.api.queries.query_api import query_router
from app.api.learning_preference_apis import learning_preference_router
from app.api.episodic_memory.episodic_memory_api import episodic_memory_router


api_router = APIRouter()

api_router.include_router(chat_router, prefix="/chat")
api_router.include_router(profile_router)
api_router.include_router(query_router)
api_router.include_router(learning_preference_router)
api_router.include_router(episodic_memory_router, prefix="/episodic-memory")
__all__ = ["api_router"]