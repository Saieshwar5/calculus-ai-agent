"""
Test script for Semantic Memory Scheduler.
Run this to manually test the scheduler functionality.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the server directory to the path
server_dir = Path(__file__).parent
sys.path.insert(0, str(server_dir))

from app.long_term_memory.semantic.scheduler import get_semantic_memory_scheduler
from app.db.my_sql_config import AsyncSessionLocal
from app.db.crud.memory.episodic import (
    get_users_with_unprocessed_episodes,
    count_unprocessed_episodes_for_semantic
)
from app.db.crud.memory.semantic import get_semantic_memory_by_user_id
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_scheduler_status():
    """Test if scheduler is running."""
    print("\n" + "="*60)
    print("Testing Scheduler Status")
    print("="*60)
    
    scheduler = get_semantic_memory_scheduler()
    is_running = scheduler.is_running()
    
    print(f"✅ Scheduler initialized: {scheduler is not None}")
    print(f"✅ Scheduler running: {is_running}")
    
    return scheduler


async def test_get_unprocessed_users():
    """Check which users have unprocessed episodes."""
    print("\n" + "="*60)
    print("Checking Users with Unprocessed Episodes")
    print("="*60)
    
    async with AsyncSessionLocal() as db:
        users = await get_users_with_unprocessed_episodes(db)
        print(f"Found {len(users)} users with unprocessed episodes")
        
        if users:
            print("\nUsers with unprocessed episodes:")
            for user_id in users:
                count = await count_unprocessed_episodes_for_semantic(db, user_id)
                print(f"  - User: {user_id} ({count} unprocessed episodes)")
        else:
            print("⚠️  No users with unprocessed episodes found.")
            print("   You may need to create some episodic memories first.")
        
        return users


async def test_process_single_user(user_id: str):
    """Test processing semantic memory for a single user."""
    print("\n" + "="*60)
    print(f"Testing Single User Processing: {user_id}")
    print("="*60)
    
    scheduler = get_semantic_memory_scheduler()
    
    try:
        result = await scheduler.process_single_user(user_id)
        
        print(f"\n✅ Processing completed!")
        print(f"   User ID: {result.get('user_id')}")
        print(f"   Episodes processed: {result.get('episodes_processed', 0)}")
        print(f"   Success: {result.get('success', False)}")
        
        if 'error' in result:
            print(f"   ❌ Error: {result['error']}")
        
        # Check the semantic memory after processing
        async with AsyncSessionLocal() as db:
            semantic_memory = await get_semantic_memory_by_user_id(db, user_id)
            if semantic_memory:
                print(f"\n📊 Semantic Memory Status:")
                print(f"   Memory exists: ✅")
                print(f"   Memory keys: {list(semantic_memory.memory_data.keys()) if semantic_memory.memory_data else 'Empty'}")
                if semantic_memory.memory_data:
                    print(f"   Sample data:")
                    for key, value in list(semantic_memory.memory_data.items())[:3]:
                        if isinstance(value, list):
                            print(f"     - {key}: {len(value)} items")
                        elif isinstance(value, dict):
                            print(f"     - {key}: {len(value)} keys")
                        else:
                            print(f"     - {key}: {value}")
            else:
                print(f"\n⚠️  No semantic memory found for user {user_id}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error processing user: {e}")
        logger.exception("Error in test_process_single_user")
        return None


async def test_trigger_full_sync():
    """Test triggering the full semantic sync manually."""
    print("\n" + "="*60)
    print("Testing Full Semantic Sync")
    print("="*60)
    
    scheduler = get_semantic_memory_scheduler()
    
    try:
        print("Triggering semantic sync...")
        result = await scheduler.trigger_sync_now()
        
        print(f"\n✅ Sync completed!")
        print(f"   Start time: {result.get('start_time')}")
        print(f"   End time: {result.get('end_time')}")
        print(f"   Duration: {result.get('duration_seconds', 0):.2f} seconds")
        print(f"   Users processed: {result.get('users_processed', 0)}")
        print(f"   Episodes processed: {result.get('episodes_processed', 0)}")
        
        if result.get('errors'):
            print(f"\n⚠️  Errors encountered: {len(result['errors'])}")
            for error in result['errors']:
                print(f"   - {error}")
        else:
            print(f"\n✅ No errors!")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error during sync: {e}")
        logger.exception("Error in test_trigger_full_sync")
        return None


async def run_all_tests():
    """Run all tests and return results."""
    results = {
        "scheduler_status": None,
        "unprocessed_users": [],
        "full_sync_result": None,
        "single_user_result": None
    }
    
    try:
        # Test 1: Check scheduler status
        scheduler = await test_scheduler_status()
        results["scheduler_status"] = {
            "initialized": scheduler is not None,
            "running": scheduler.is_running() if scheduler else False
        }
        
        # Test 2: Check for unprocessed users
        users = await test_get_unprocessed_users()
        results["unprocessed_users"] = users
        
        if users:
            # Test 3: Trigger full sync
            sync_result = await test_trigger_full_sync()
            results["full_sync_result"] = sync_result
            
            # Test 4: Test single user (first user)
            if users:
                user_result = await test_process_single_user(users[0])
                results["single_user_result"] = user_result
        
        return results
        
    except Exception as e:
        logger.exception("Error in run_all_tests")
        results["error"] = str(e)
        return results


async def main():
    """Main test function."""
    print("\n" + "="*60)
    print("Semantic Memory Scheduler Test Suite")
    print("="*60)
    
    # Test 1: Check scheduler status
    scheduler = await test_scheduler_status()
    
    # Test 2: Check for unprocessed users
    users = await test_get_unprocessed_users()
    
    if not users:
        print("\n" + "="*60)
        print("⚠️  No users with unprocessed episodes found.")
        print("   The scheduler needs episodic memories to process.")
        print("   Create some episodic memories first, then run this test again.")
        print("="*60)
        return
    
    # Ask user what they want to test
    print("\n" + "="*60)
    print("Test Options:")
    print("="*60)
    print("1. Test full sync (processes all users)")
    print("2. Test single user processing")
    print("3. Run both tests")
    print("="*60)
    
    choice = input("\nEnter your choice (1/2/3) [default: 1]: ").strip() or "1"
    
    if choice == "1" or choice == "3":
        # Test full sync
        await test_trigger_full_sync()
    
    if choice == "2" or choice == "3":
        # Test single user
        if users:
            user_id = input(f"\nEnter user ID to test [default: {users[0]}]: ").strip() or users[0]
            await test_process_single_user(user_id)
    
    print("\n" + "="*60)
    print("✅ Test Suite Completed!")
    print("="*60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        logger.exception("Fatal error in test script")
        sys.exit(1)

