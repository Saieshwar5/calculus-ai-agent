"""
Semantic Memory API routes.
Handles semantic memory scheduler testing and management endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
import logging

from app.db.my_sql_config import get_db, AsyncSessionLocal
from app.long_term_memory.semantic.scheduler import get_semantic_memory_scheduler
from app.db.crud.memory.episodic import (
    get_users_with_unprocessed_episodes,
    count_unprocessed_episodes_for_semantic
)
from app.db.crud.memory.semantic import get_semantic_memory_by_user_id

logger = logging.getLogger(__name__)

semantic_memory_router = APIRouter(tags=["Semantic Memory"])


@semantic_memory_router.get("/scheduler/status")
async def get_scheduler_status():
    """
    Get the status of the semantic memory scheduler.
    
    Returns:
        Dictionary with scheduler status information
    """
    try:
        scheduler = get_semantic_memory_scheduler()
        return {
            "initialized": scheduler is not None,
            "running": scheduler.is_running() if scheduler else False,
            "status": "running" if scheduler and scheduler.is_running() else "stopped"
        }
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting scheduler status: {str(e)}")


@semantic_memory_router.get("/scheduler/unprocessed-users")
async def get_unprocessed_users(db: AsyncSession = Depends(get_db)):
    """
    Get list of users with unprocessed episodic memories.
    
    Returns:
        Dictionary with list of users and their unprocessed episode counts
    """
    try:
        users = await get_users_with_unprocessed_episodes(db)
        user_details = []
        
        for user_id in users:
            count = await count_unprocessed_episodes_for_semantic(db, user_id)
            user_details.append({
                "user_id": user_id,
                "unprocessed_episodes": count
            })
        
        return {
            "total_users": len(users),
            "users": user_details
        }
    except Exception as e:
        logger.error(f"Error getting unprocessed users: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting unprocessed users: {str(e)}")


@semantic_memory_router.post("/scheduler/trigger-sync")
async def trigger_semantic_sync():
    """
    Manually trigger the semantic memory sync for all users.
    This processes all unprocessed episodic memories and updates semantic memory.
    
    Returns:
        Dictionary with sync results
    """
    try:
        scheduler = get_semantic_memory_scheduler()
        result = await scheduler.trigger_sync_now()
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        logger.error(f"Error triggering semantic sync: {e}")
        raise HTTPException(status_code=500, detail=f"Error triggering semantic sync: {str(e)}")


@semantic_memory_router.post("/scheduler/process-user/{user_id}")
async def process_single_user(
    user_id: str = Path(..., description="User identifier")
):
    """
    Process semantic memory for a single user.
    
    Args:
        user_id: User identifier
        
    Returns:
        Dictionary with processing results
    """
    try:
        scheduler = get_semantic_memory_scheduler()
        result = await scheduler.process_single_user(user_id)
        
        # Get semantic memory status after processing
        async with AsyncSessionLocal() as db:
            semantic_memory = await get_semantic_memory_by_user_id(db, user_id)
            result["semantic_memory_exists"] = semantic_memory is not None
            if semantic_memory:
                result["semantic_memory_keys"] = list(semantic_memory.memory_data.keys()) if semantic_memory.memory_data else []
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        logger.error(f"Error processing user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing user: {str(e)}")


@semantic_memory_router.post("/scheduler/run-tests")
async def run_scheduler_tests():
    """
    Run comprehensive tests on the semantic memory scheduler.
    This includes:
    - Checking scheduler status
    - Finding users with unprocessed episodes
    - Triggering full sync
    - Testing single user processing
    
    Returns:
        Dictionary with all test results
    """
    try:
        results = {
            "scheduler_status": None,
            "unprocessed_users": [],
            "full_sync_result": None,
            "single_user_result": None
        }
        
        # Test 1: Check scheduler status
        scheduler = get_semantic_memory_scheduler()
        results["scheduler_status"] = {
            "initialized": scheduler is not None,
            "running": scheduler.is_running() if scheduler else False
        }
        
        # Test 2: Check for unprocessed users
        async with AsyncSessionLocal() as db:
            users = await get_users_with_unprocessed_episodes(db)
            user_details = []
            for user_id in users:
                count = await count_unprocessed_episodes_for_semantic(db, user_id)
                user_details.append({
                    "user_id": user_id,
                    "unprocessed_episodes": count
                })
            results["unprocessed_users"] = user_details
        
        # Test 3: Trigger full sync if there are users
        if results["unprocessed_users"]:
            sync_result = await scheduler.trigger_sync_now()
            results["full_sync_result"] = sync_result
            
            # Test 4: Test single user (first user)
            if results["unprocessed_users"]:
                first_user_id = results["unprocessed_users"][0]["user_id"]
                user_result = await scheduler.process_single_user(first_user_id)
                results["single_user_result"] = user_result
        
        return {
            "success": True,
            "test_results": results
        }
    except Exception as e:
        logger.error(f"Error running scheduler tests: {e}")
        raise HTTPException(status_code=500, detail=f"Error running tests: {str(e)}")

