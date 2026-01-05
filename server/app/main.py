from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.api import api_router
from app.api.auth.auth_api import auth_router
from app.db.create_tables import create_tables
from app.db.redis_config import init_redis, close_redis, test_redis_connection
from app.services.semantic_memory_scheduler import start_semantic_memory_scheduler, stop_semantic_memory_scheduler
import asyncio
# Define the Item model
class Item(BaseModel):
    name: str
    description: str = None
    price: float
    tax: float = None

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database, Redis, and MongoDB connections when application starts"""
    # Initialize MySQL database tables
    await create_tables()
    print("✅ Database tables initialized")
    
    # Initialize Redis connection
    try:
        await init_redis()
        # Test Redis connection
        redis_ok = await test_redis_connection()
        if not redis_ok:
            print("⚠️  Warning: Redis connection test failed, but continuing...")
    except Exception as e:
        print(f"⚠️  Warning: Redis initialization failed: {str(e)}")
        print("⚠️  Application will continue, but short-term memory features may not work")
    
   
    
    # Start semantic memory scheduler (runs at midnight)
    try:
        start_semantic_memory_scheduler()
        print("✅ Semantic memory scheduler started (runs at midnight)")
    except Exception as e:
        print(f"⚠️  Warning: Failed to start semantic memory scheduler: {str(e)}")
        print("⚠️  Application will continue, but episodic-to-semantic sync may not work")


@app.on_event("shutdown")
async def shutdown_event():
    """Close connections when application shuts down"""
   
    
    # Stop semantic memory scheduler
    try:
        stop_semantic_memory_scheduler()
        print("✅ Semantic memory scheduler stopped")
    except Exception as e:
        print(f"⚠️  Error stopping semantic memory scheduler: {str(e)}")
    
    try:
        await close_redis()
    except Exception as e:
        print(f"⚠️  Error closing Redis connection: {str(e)}")
    
   


# Auth routes at /api/auth to match client expectations
app.include_router(auth_router, prefix="/api/auth")

app.include_router(api_router, prefix="/api/v1")
# Include learning preference router at /api to match client expectations

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

