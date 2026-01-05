"""
Script to create all database tables.
Run this once to initialize the database schema.
"""
import asyncio
from sqlalchemy import text
from app.db.my_sql_config import engine, Base
from app.models.profile_model import Profile  # Import models to register them
from app.models.query_model import Query  # Import models to register them
from app.models.learning_preference_model import LearningPreference  # Import models to register them
from app.models.user_model import User  # Import User model to register it
from app.models.semantic_memory_model import SemanticMemory  # Import SemanticMemory model to register it
from app.models.episodic_memory_model import EpisodicMemory  # Import EpisodicMemory model to register it


async def create_tables():
    """
    Create all tables defined in the models.
    """
    async with engine.begin() as conn:
        # Enable pgvector extension
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            print("✅ pgvector extension enabled")
        except Exception as e:
            print(f"⚠️  Warning: Could not enable pgvector extension: {e}")
            print("⚠️  Make sure pgvector is installed in PostgreSQL")
        
        # Drop all tables (use with caution in production!)
        # await conn.run_sync(Base.metadata.drop_all)
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("✅ All tables created successfully!")
        
        # Create vector index for episodic memory (HNSW for fast similarity search)
        try:
            # Check if index already exists
            index_check = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_indexes 
                    WHERE indexname = 'episodic_memory_event_embedding_idx'
                )
            """))
            index_exists = index_check.scalar()
            
            if not index_exists:
                await conn.execute(text("""
                    CREATE INDEX episodic_memory_event_embedding_idx 
                    ON episodic_memory 
                    USING hnsw (event_embedding vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64)
                """))
                print("✅ Vector index created for episodic_memory.event_embedding")
            else:
                print("✅ Vector index already exists")
        except Exception as e:
            print(f"⚠️  Warning: Could not create vector index: {e}")
            print("⚠️  Vector similarity search may be slower without index")


if __name__ == "__main__":
    asyncio.run(create_tables())

