"""
Memory Queue for Async Semantic Memory Operations.
Optional async queue for non-blocking memory operations.
"""
import asyncio
from typing import Dict, Any, Optional, Callable, Awaitable
from collections import deque
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MemoryQueue:
    """
    Async queue for processing semantic memory operations.
    Allows non-blocking memory saves for better performance.
    """
    
    def __init__(self, max_size: int = 1000, batch_size: int = 10):
        """
        Initialize memory queue.
        
        Args:
            max_size: Maximum queue size before blocking
            batch_size: Number of operations to process in batch
        """
        self.queue: deque = deque(maxlen=max_size)
        self.batch_size = batch_size
        self.is_processing = False
        self.processor_task: Optional[asyncio.Task] = None
    
    async def enqueue(
        self,
        operation: str,
        user_id: str,
        data: Dict[str, Any],
        handler: Callable[[str, Dict[str, Any]], Awaitable[Any]]
    ) -> bool:
        """
        Enqueue a memory operation for async processing.
        
        Args:
            operation: Operation type ('create', 'update', 'merge', 'delete')
            user_id: User identifier
            data: Operation data
            handler: Async function to handle the operation
        
        Returns:
            True if enqueued successfully, False if queue is full
        """
        if len(self.queue) >= self.queue.maxlen:
            logger.warning(f"Memory queue is full, dropping operation for user {user_id}")
            return False
        
        queue_item = {
            "operation": operation,
            "user_id": user_id,
            "data": data,
            "handler": handler,
            "timestamp": datetime.utcnow()
        }
        
        self.queue.append(queue_item)
        logger.debug(f"Enqueued {operation} operation for user {user_id}")
        
        # Start processor if not running
        if not self.is_processing:
            self.processor_task = asyncio.create_task(self._process_queue())
        
        return True
    
    async def _process_queue(self):
        """
        Process queued memory operations in batches.
        """
        self.is_processing = True
        logger.info("Memory queue processor started")
        
        try:
            while len(self.queue) > 0:
                batch = []
                # Collect batch
                for _ in range(min(self.batch_size, len(self.queue))):
                    if len(self.queue) > 0:
                        batch.append(self.queue.popleft())
                
                # Process batch
                if batch:
                    await self._process_batch(batch)
                
                # Small delay between batches
                await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Error in memory queue processor: {e}")
        finally:
            self.is_processing = False
            logger.info("Memory queue processor stopped")
    
    async def _process_batch(self, batch: list):
        """
        Process a batch of memory operations.
        
        Args:
            batch: List of queue items to process
        """
        tasks = []
        for item in batch:
            try:
                task = item["handler"](item["user_id"], item["data"])
                tasks.append(task)
            except Exception as e:
                logger.error(f"Error creating task for {item['operation']}: {e}")
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error processing {batch[i]['operation']}: {result}")
                else:
                    logger.debug(f"Successfully processed {batch[i]['operation']} for user {batch[i]['user_id']}")
    
    def get_queue_size(self) -> int:
        """Get current queue size."""
        return len(self.queue)
    
    def clear_queue(self):
        """Clear all queued operations."""
        self.queue.clear()
        logger.info("Memory queue cleared")


# Global memory queue instance
_memory_queue: Optional[MemoryQueue] = None


def get_memory_queue() -> MemoryQueue:
    """
    Get or create global memory queue instance.
    
    Returns:
        MemoryQueue instance
    """
    global _memory_queue
    if _memory_queue is None:
        _memory_queue = MemoryQueue()
    return _memory_queue

