import os
from urllib.parse import quote_plus
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
from sqlalchemy import text
# Load environment variables
load_dotenv()

# PostgreSQL connection configuration
# Note: Requires psycopg package: pip install psycopg[binary]
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "your_password")
POSTGRES_DATABASE = os.getenv("POSTGRES_DATABASE", "calculus")

# URL-encode password to handle special characters
encoded_password = quote_plus(POSTGRES_PASSWORD) if POSTGRES_PASSWORD else ""

# Create PostgreSQL async connection URL
# Format: postgresql+psycopg.async://user:password@host:port/database
DATABASE_URL = f"postgresql+psycopg://{POSTGRES_USER}:{encoded_password}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}"

# Create async SQLAlchemy engine
engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using them
    pool_recycle=3600,    # Recycle connections after 1 hour
    echo=False,
    pool_size=10,
    max_overflow=20
     # Set to True for SQL query logging
)

# Create AsyncSessionLocal class
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Create Base class for declarative models
Base = declarative_base()

# Async dependency to get database session
async def get_db():
    """
    Async database session dependency for FastAPI.
    Usage in FastAPI routes:
        from app.db.my_sql_config import get_db
        @app.get("/items")
        async def read_items(db: AsyncSession = Depends(get_db)):
            ...
    Note: This file is configured for PostgreSQL, despite the filename.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()





# Test database connection
async def test_connection():
    """
    Test function to verify database connection.
    Run with: python -m asyncio -c "from app.db.my_sql_config import test_connection; import asyncio; asyncio.run(test_connection())"
    Or add this at the bottom of the file:
    if __name__ == "__main__":
        import asyncio
        asyncio.run(test_connection())
    """
    try:
        print("Testing PostgreSQL connection...")
        print(f"Connecting to: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}")
        
        # Test engine connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.fetchone()
            print(f"✅ Database connection successful! Test query result: {row[0]}")
        
        # Test session
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            print(f"✅ Session test successful! Current database: {db_name}")
            
            # Test version
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ PostgreSQL version: {version}")
        
        print("✅ All database tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False
    finally:
        await engine.dispose()

# Run test if executed directly
if __name__ == "__main__":
    import asyncio
    asyncio.run(test_connection())






