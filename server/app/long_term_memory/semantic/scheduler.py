"""
Semantic Memory Scheduler Service.
Uses APScheduler to run midnight job that processes episodic memories
and extracts semantic information for each user.
"""
import os
import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from app.db.my_sql_config import AsyncSessionLocal
from app.db.crud.memory.episodic import (
    get_users_with_unprocessed_episodes,
    get_unprocessed_episodes_for_semantic,
    mark_episodes_as_semantic_processed,
    count_unprocessed_episodes_for_semantic
)
from app.db.crud.memory.semantic import (
    get_semantic_memory_by_user_id,
    merge_semantic_memory,
    get_or_create_semantic_memory
)
from app.long_term_memory.semantic.extractor import get_semantic_memory_extractor
from app.long_term_memory.shared.validator import MemoryValidator

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
SEMANTIC_SYNC_HOUR = int(os.getenv("SEMANTIC_SYNC_HOUR", "0"))  # Midnight by default
SEMANTIC_SYNC_MINUTE = int(os.getenv("SEMANTIC_SYNC_MINUTE", "0"))
SEMANTIC_SYNC_BATCH_SIZE = int(os.getenv("SEMANTIC_SYNC_BATCH_SIZE", "50"))  # Episodes per user per batch


class SemanticMemoryScheduler:
    """
    Scheduler for periodic semantic memory synchronization.
    Runs at midnight to process episodic memories and update semantic profiles.
    """
    
    def __init__(self):
        """Initialize the scheduler."""
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.extractor = get_semantic_memory_extractor()
        self.validator = MemoryValidator()
        self._is_running = False
    
    def start(self):
        """Start the scheduler with midnight cron job."""
        if self.scheduler is not None:
            logger.warning("Scheduler already initialized")
            return
        
        self.scheduler = AsyncIOScheduler()
        
        # Add midnight job
        self.scheduler.add_job(
            self.run_semantic_sync,
            CronTrigger(hour=SEMANTIC_SYNC_HOUR, minute=SEMANTIC_SYNC_MINUTE),
            id="semantic_memory_sync",
            name="Episodic to Semantic Memory Sync",
            replace_existing=True
        )
        
        self.scheduler.start()
        self._is_running = True
        logger.info(f"Semantic memory scheduler started. Sync runs daily at {SEMANTIC_SYNC_HOUR:02d}:{SEMANTIC_SYNC_MINUTE:02d}")
    
    def stop(self):
        """Stop the scheduler."""
        if self.scheduler is not None:
            self.scheduler.shutdown(wait=False)
            self.scheduler = None
            self._is_running = False
            logger.info("Semantic memory scheduler stopped")
    
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._is_running and self.scheduler is not None
    
    async def run_semantic_sync(self) -> Dict[str, Any]:
        """
        Main job: Process all users with unprocessed episodic memories.
        
        Returns:
            Dictionary with sync results
        """
        start_time = datetime.utcnow()
        logger.info(f"Starting semantic memory sync at {start_time.isoformat()}")
        
        results = {
            "start_time": start_time.isoformat(),
            "users_processed": 0,
            "episodes_processed": 0,
            "errors": []
        }
        
        try:
            async with AsyncSessionLocal() as db:
                # Get all users with unprocessed episodes
                users = await get_users_with_unprocessed_episodes(db)
                logger.info(f"Found {len(users)} users with unprocessed episodes")
                
                for user_id in users:
                    try:
                        user_result = await self._process_user_semantic(db, user_id)
                        results["users_processed"] += 1
                        results["episodes_processed"] += user_result.get("episodes_processed", 0)
                    except Exception as e:
                        error_msg = f"Error processing user {user_id}: {str(e)}"
                        logger.error(error_msg)
                        results["errors"].append(error_msg)
            
            end_time = datetime.utcnow()
            results["end_time"] = end_time.isoformat()
            results["duration_seconds"] = (end_time - start_time).total_seconds()
            
            logger.info(f"Semantic sync completed. Processed {results['users_processed']} users, "
                       f"{results['episodes_processed']} episodes in {results['duration_seconds']:.2f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"Critical error in semantic sync: {e}")
            results["errors"].append(f"Critical error: {str(e)}")
            return results
    
    async def _process_user_semantic(
        self,
        db,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Process semantic memory extraction for a single user.
        
        Args:
            db: Database session
            user_id: User identifier
        
        Returns:
            Dictionary with processing results
        """
        result = {
            "user_id": user_id,
            "episodes_processed": 0,
            "success": False
        }
        
        try:
            # Get unprocessed episodes
            episodes = await get_unprocessed_episodes_for_semantic(
                db, user_id, limit=SEMANTIC_SYNC_BATCH_SIZE
            )
            
            if not episodes:
                logger.debug(f"No unprocessed episodes for user {user_id}")
                result["success"] = True
                return result
            
            logger.info(f"Processing {len(episodes)} episodes for user {user_id}")
            
            # Get existing semantic memory
            existing_semantic = await get_semantic_memory_by_user_id(db, user_id)
            existing_data = existing_semantic.memory_data if existing_semantic else {}
            
            # Extract semantic data from episodes
            extracted_data = await self.extractor.extract_from_episodes(
                episodes=episodes,
                existing_semantic=existing_data
            )
            
            if not extracted_data:
                logger.warning(f"No semantic data extracted for user {user_id}")
                result["success"] = True
                return result
            
            # Merge with existing semantic memory
            merged_data = await self.extractor.merge_semantic_data(
                existing=existing_data,
                new_data=extracted_data
            )
            
            # Validate the merged data
            is_valid, error, cleaned_data = self.validator.validate_memory_data(merged_data)
            
            if not is_valid:
                logger.warning(f"Validation failed for user {user_id}: {error}")
                # Continue with cleaned data anyway
                cleaned_data = merged_data
            
            # Ensure semantic memory exists and update it
            await get_or_create_semantic_memory(db, user_id, {})
            await merge_semantic_memory(db, user_id, cleaned_data)
            
            # Mark episodes as processed
            episode_ids = [ep.id for ep in episodes]
            await mark_episodes_as_semantic_processed(db, episode_ids)
            
            result["episodes_processed"] = len(episodes)
            result["success"] = True
            
            logger.info(f"Successfully updated semantic memory for user {user_id} "
                       f"from {len(episodes)} episodes")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing semantic memory for user {user_id}: {e}")
            result["error"] = str(e)
            raise
    
    async def trigger_sync_now(self) -> Dict[str, Any]:
        """
        Manually trigger semantic sync (for testing or admin purposes).
        
        Returns:
            Dictionary with sync results
        """
        logger.info("Manual semantic sync triggered")
        return await self.run_semantic_sync()
    
    async def process_single_user(self, user_id: str) -> Dict[str, Any]:
        """
        Process semantic memory for a single user (on-demand).
        
        Args:
            user_id: User identifier
        
        Returns:
            Dictionary with processing results
        """
        logger.info(f"Processing semantic memory for single user: {user_id}")
        
        async with AsyncSessionLocal() as db:
            return await self._process_user_semantic(db, user_id)


# Global scheduler instance
_semantic_memory_scheduler: Optional[SemanticMemoryScheduler] = None


def get_semantic_memory_scheduler() -> SemanticMemoryScheduler:
    """
    Get or create global semantic memory scheduler instance.
    
    Returns:
        SemanticMemoryScheduler instance
    """
    global _semantic_memory_scheduler
    if _semantic_memory_scheduler is None:
        _semantic_memory_scheduler = SemanticMemoryScheduler()
    return _semantic_memory_scheduler


def start_semantic_memory_scheduler():
    """Start the semantic memory scheduler."""
    scheduler = get_semantic_memory_scheduler()
    scheduler.start()


def stop_semantic_memory_scheduler():
    """Stop the semantic memory scheduler."""
    scheduler = get_semantic_memory_scheduler()
    scheduler.stop()

