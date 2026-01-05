import os
from redis.asyncio import Redis, ConnectionPool
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

# Redis connection configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_URL = os.getenv("REDIS_URL", None)

# Memory TTL configuration (in days)
MEMORY_TTL_DAYS = int(os.getenv("MEMORY_TTL_DAYS", "7"))
MEMORY_TTL_SECONDS = MEMORY_TTL_DAYS * 24 * 60 * 60

# Redis connection pool
_redis_pool: Optional[ConnectionPool] = None
_redis_client: Optional[Redis] = None


def get_redis_url() -> str:
    """Get Redis connection URL from environment or construct from components."""
    if REDIS_URL:
        return REDIS_URL
    
    if REDIS_PASSWORD:
        return f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    
    return f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"


async def init_redis() -> Redis:
    """
    Initialize Redis connection pool and client.
    Should be called on application startup.
    """
    global _redis_pool, _redis_client
    
    if _redis_client is not None:
        return _redis_client
    
    try:
        redis_url = get_redis_url()
        _redis_pool = ConnectionPool.from_url(
            redis_url,
            max_connections=50,
            decode_responses=True,  # Automatically decode responses to strings
        )
        _redis_client = Redis(connection_pool=_redis_pool)
        
        # Test connection
        await _redis_client.ping()
        print(f"✅ Redis connection successful! Connected to: {REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")
        
        return _redis_client
    except Exception as e:
        print(f"❌ Redis connection failed: {str(e)}")
        raise


async def get_redis() -> Redis:
    """
    Get Redis client instance.
    If not initialized, will initialize it.
    
    Usage in FastAPI routes:
        from app.db.redis_config import get_redis
        @app.get("/items")
        async def read_items(redis: Redis = Depends(get_redis)):
            ...
    """
    global _redis_client
    
    if _redis_client is None:
        _redis_client = await init_redis()
    
    return _redis_client


async def close_redis():
    """Close Redis connection pool. Should be called on application shutdown."""
    global _redis_client, _redis_pool
    
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
    
    if _redis_pool:
        await _redis_pool.disconnect()
        _redis_pool = None
    
    print("✅ Redis connection closed")


async def test_redis_connection() -> bool:
    """
    Test function to verify Redis connection.
    Returns True if connection is successful, False otherwise.
    """
    try:
        print("Testing Redis connection...")
        print(f"Connecting to: {REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")
        
        redis = await get_redis()
        result = await redis.ping()
        
        if result:
            print("✅ Redis connection successful!")
            
            # Test basic operations
            await redis.set("test_key", "test_value", ex=10)
            value = await redis.get("test_key")
            await redis.delete("test_key")
            
            if value == "test_value":
                print("✅ Redis read/write test successful!")
                return True
            else:
                print("❌ Redis read/write test failed!")
                return False
        else:
            print("❌ Redis ping failed!")
            return False
            
    except Exception as e:
        print(f"❌ Redis connection test failed: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False


# Run test if executed directly
if __name__ == "__main__":
    import asyncio
    asyncio.run(test_redis_connection())

