from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.api import api_router
from app.api.auth.auth_api import auth_router
from app.db.create_tables import create_tables
from app.db.redis_config import init_redis, close_redis, test_redis_connection
from app.long_term_memory.semantic.scheduler import start_semantic_memory_scheduler, stop_semantic_memory_scheduler, get_semantic_memory_scheduler
from app.db.my_sql_config import AsyncSessionLocal
from app.db.crud.memory.episodic import get_users_with_unprocessed_episodes, count_unprocessed_episodes_for_semantic
from app.mcp.client import init_mcp_client, close_mcp_client
import asyncio
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
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
        
        # Optionally run scheduler test on startup (controlled by env variable)
        if os.getenv("RUN_SEMANTIC_SCHEDULER_TEST_ON_STARTUP", "false").lower() == "true":
            print("\n" + "="*60)
            print("Running Semantic Memory Scheduler Test on Startup")
            print("="*60)
            try:
                await run_scheduler_test_on_startup()
            except Exception as e:
                print(f"⚠️  Warning: Scheduler test failed on startup: {str(e)}")
                logger.exception("Error running scheduler test on startup")
    except Exception as e:
        print(f"⚠️  Warning: Failed to start semantic memory scheduler: {str(e)}")
        print("⚠️  Application will continue, but episodic-to-semantic sync may not work")
    
    # Initialize MCP client for web search
    try:
        mcp_connected = await init_mcp_client()
        if mcp_connected:
            print("✅ MCP client initialized (web search available)")
        else:
            print("⚠️  Warning: MCP client failed to connect")
            print("⚠️  Application will continue, but web search features may not work")
    except Exception as e:
        print(f"⚠️  Warning: MCP client initialization failed: {str(e)}")
        print("⚠️  Application will continue, but web search features may not work")


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
    
    # Close MCP client
    try:
        await close_mcp_client()
        print("✅ MCP client closed")
    except Exception as e:
        print(f"⚠️  Error closing MCP client: {str(e)}")
    
   


# Auth routes at /api/auth to match client expectations
app.include_router(auth_router, prefix="/api/auth")

app.include_router(api_router, prefix="/api/v1")
# Include learning preference router at /api to match client expectations

async def run_scheduler_test_on_startup():
    """Run a quick test of the semantic memory scheduler on startup."""
    scheduler = get_semantic_memory_scheduler()
    
    # Check scheduler status
    is_running = scheduler.is_running()
    print(f"✅ Scheduler initialized: {scheduler is not None}")
    print(f"✅ Scheduler running: {is_running}")
    
    # Check for unprocessed users
    async with AsyncSessionLocal() as db:
        users = await get_users_with_unprocessed_episodes(db)
        print(f"📊 Found {len(users)} users with unprocessed episodes")
        
        if users:
            print("\nUsers with unprocessed episodes:")
            for user_id in users[:5]:  # Show first 5 users
                count = await count_unprocessed_episodes_for_semantic(db, user_id)
                print(f"  - User: {user_id} ({count} unprocessed episodes)")
            if len(users) > 5:
                print(f"  ... and {len(users) - 5} more users")
            
            # Optionally trigger sync on startup
            if os.getenv("TRIGGER_SEMANTIC_SYNC_ON_STARTUP", "false").lower() == "true":
                print("\n🔄 Triggering semantic sync on startup...")
                result = await scheduler.trigger_sync_now()
                print(f"✅ Sync completed!")
                print(f"   Users processed: {result.get('users_processed', 0)}")
                print(f"   Episodes processed: {result.get('episodes_processed', 0)}")
                print(f"   Duration: {result.get('duration_seconds', 0):.2f} seconds")
                if result.get('errors'):
                    print(f"   ⚠️  Errors: {len(result['errors'])}")
        else:
            print("ℹ️  No users with unprocessed episodes found.")
    
    print("="*60 + "\n")


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

