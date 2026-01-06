"""
Query API routes.
Handles streaming query endpoints with file upload support and RAG.
"""
from fastapi import APIRouter, HTTPException, Depends, Path, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from pydantic import ValidationError
import json
import asyncio

from app.db.my_sql_config import get_db
from app.schemas.pydantic_schemas.query_schema import QueryRequest, QueryCreate, QueryUpdate
from app.db.crud.query_crud import (
    create_query as crud_create_query,
    update_query as crud_update_query
)
from app.short_term_memory.manager import MemoryManager, get_memory_manager
from app.schemas.pydantic_schemas.memory.short_term import MemoryResponse, MemoryClearResponse
from app.long_term_memory.episodic.trigger import get_episodic_memory_trigger
from app.services.rag_service import get_rag_service, RAGService

query_router = APIRouter(tags=["Queries"])


async def stream_query_response(
    query_id: int,
    db: AsyncSession,
    user_id: str,
    memory_manager: MemoryManager,
    query_text: str,
    rag_context: Optional[str] = None
):
    """
    Generator function that streams query responses using OpenAI.
    
    Args:
        query_id: Database query ID
        db: Database session
        user_id: User identifier for memory storage
        memory_manager: Memory manager instance for storing responses
        query_text: The user's query text
        rag_context: Optional context from RAG document retrieval
    """
    from app.core.query_engine.openai_ai import stream_openai_response
    
    full_response = ""
    
    try:
        # Stream OpenAI response with conversation context and function calling
        async for chunk in stream_openai_response(
            query_text=query_text,
            user_id=user_id,
            memory_manager=memory_manager,
            db=db,  # Pass database session for semantic memory operations
            model="gpt-4o-mini",  # You can make this configurable via env var
            temperature=0.7,
            enable_function_calling=True,
            rag_context=rag_context
        ):
            full_response += chunk
            yield chunk
        
        # Update the query with the complete response
        try:
            await crud_update_query(db, query_id, QueryUpdate(response_text=full_response))
        except Exception as e:
            print(f"Error updating query in database: {e}")
        
        # Store assistant response in short-term memory
        # Only save if there's actual content (not just function calls)
        try:
            if full_response and full_response.strip():
                await memory_manager.add_message(
                    user_id=user_id,
                    role="assistant",
                    content=full_response
                )
            else:
                print(f"[INFO] Skipping empty assistant response in memory (likely only function calls)")
        except Exception as e:
            print(f"Warning: Failed to store response in memory: {e}")
        
        # Check if we should trigger episodic memory processing
        # This runs asynchronously to not block the response
        # Note: The background task creates its own database session to avoid conflicts
        try:
            trigger = get_episodic_memory_trigger()
            # Create background task for episodic memory processing
            # No db session passed - task creates its own to avoid session conflicts
            asyncio.create_task(
                trigger.check_and_process_async(user_id)
            )
        except Exception as e:
            # Log but don't fail the request
            print(f"Warning: Failed to trigger episodic memory processing: {e}")
            
    except Exception as e:
        error_message = f"Error generating response: {str(e)}"
        print(error_message)
        yield f"\n\n[Error: {error_message}]"
        # Still try to save the error message
        try:
            await crud_update_query(db, query_id, QueryUpdate(response_text=error_message))
        except Exception as db_error:
            print(f"Error saving error message to database: {db_error}")


@query_router.post("/stream-query/{user_id}")
async def stream_query(
    request: Request,
    user_id: str = Path(..., description="User identifier"),
    db: AsyncSession = Depends(get_db),
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """
    Stream a query response. Supports both JSON and FormData requests.
    
    - **JSON request**: Send `{ "query": "your query text" }` with Content-Type: application/json
    - **FormData request**: Send `query` as form field and optionally `files` for file uploads
    
    Args:
        request: FastAPI Request object to access headers and body
        user_id: User identifier from URL path
        db: Database session
    
    Returns:
        StreamingResponse with text chunks
    """
    try:
        content_type = request.headers.get("content-type", "")
        query_text = None
        files = []
        
        if "application/json" in content_type:
            # Handle JSON request - use Pydantic model for validation
            body = await request.json()
            try:
                query_request = QueryRequest(**body)  # Validate with Pydantic model
                query_text = query_request.query
            except ValidationError as e:
                raise HTTPException(
                    status_code=422,
                    detail=f"Validation error: {e.errors()}"
                )
        elif "multipart/form-data" in content_type:
            # Handle FormData request
            form = await request.form()
            if "query" not in form:
                raise HTTPException(status_code=400, detail="Query text is required in 'query' form field")
            query_text = form["query"]
            
            # Validate query_text matches Pydantic requirements (min_length=1)
            if not query_text or len(query_text.strip()) < 1:
                raise HTTPException(
                    status_code=400,
                    detail="Query text cannot be empty"
                )
            
            # Get files if any
            if "files" in form:
                file_list = form.getlist("files")
                files = [file for file in file_list if hasattr(file, 'filename')]
        else:
            raise HTTPException(
                status_code=400,
                detail="Content-Type must be either 'application/json' or 'multipart/form-data'"
            )
        
        if not query_text or not query_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Query text cannot be empty"
            )
        
        # RAG: Process and store files if provided
        rag_context = None
        print(f"[API] Getting RAG service...")
        
        try:
            rag_service = get_rag_service()
            print(f"[API] ✅ RAG service obtained")
        except Exception as e:
            print(f"[API] ❌ Failed to get RAG service: {e}")
            import traceback
            traceback.print_exc()
            rag_service = None
        
        if files and rag_service:
            file_names = [file.filename for file in files if hasattr(file, 'filename')]
            print(f"[API] Received {len(file_names)} file(s): {file_names}")
            
            try:
                print(f"[API] Calling rag_service.store_documents...")
                # Store documents in Qdrant
                store_result = await rag_service.store_documents(user_id, files)
                if store_result.get("success"):
                    print(f"[API] ✅ Stored {store_result.get('stored', 0)} chunks for user {user_id}")
                else:
                    print(f"[API] ⚠️ Document storage issues: {store_result.get('message')}")
                    if store_result.get("errors"):
                        print(f"[API] Errors: {store_result.get('errors')}")
            except Exception as e:
                print(f"[API] ❌ Failed to store documents: {str(e)}")
                import traceback
                traceback.print_exc()
                # Continue processing even if RAG storage fails
        
        # RAG: Retrieve relevant context for the query
        if rag_service:
            try:
                print(f"[API] Calling rag_service.retrieve_relevant_chunks...")
                retrieved_chunks = await rag_service.retrieve_relevant_chunks(
                    user_id=user_id,
                    query=query_text.strip(),
                    top_k=5
                )
                if retrieved_chunks:
                    rag_context = rag_service.format_context_for_prompt(retrieved_chunks)
                    print(f"[API] ✅ Retrieved {len(retrieved_chunks)} relevant chunks for context")
                else:
                    print(f"[API] No relevant chunks found")
            except Exception as e:
                print(f"[API] ❌ Failed to retrieve context: {str(e)}")
                import traceback
                traceback.print_exc()
                # Continue without RAG context
        
        # Store user query in short-term memory
        try:
            await memory_manager.add_message(
                user_id=user_id,
                role="user",
                content=query_text.strip()
            )
        except Exception as e:
            print(f"Warning: Failed to store query in memory: {str(e)}")
            # Continue processing even if memory storage fails
        
        # Create query record in database
        query_data = QueryCreate(
            user_id=user_id,
            query_text=query_text.strip()
        )
        
        query_record = await crud_create_query(db, query_data)
        query_id = query_record.id
        
        # Create a generator that streams the response
        async def response_generator():
            async for chunk in stream_query_response(
                query_id, db, user_id, memory_manager, query_text.strip(), rag_context
            ):
                yield chunk
        
        return StreamingResponse(
            response_generator(),
            media_type="text/plain",
            headers={
                "X-Query-ID": str(query_id),
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@query_router.get("/memory/{user_id}", response_model=MemoryResponse)
async def get_memory(
    user_id: str = Path(..., description="User identifier"),
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """
    Get recent messages from user's short-term memory.
    
    Useful for debugging and testing memory functionality.
    
    Args:
        user_id: User identifier
        memory_manager: Memory manager instance
    
    Returns:
        MemoryResponse with recent messages
    """
    try:
        messages = await memory_manager.get_recent_messages(user_id)
        count = await memory_manager.get_message_count(user_id)
        
        return MemoryResponse(
            user_id=user_id,
            messages=messages,
            count=count,
            max_messages=memory_manager.MAX_MESSAGES
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving memory: {str(e)}"
        )


@query_router.delete("/memory/{user_id}", response_model=MemoryClearResponse)
async def clear_memory(
    user_id: str = Path(..., description="User identifier"),
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """
    Clear all messages from user's short-term memory.
    
    Useful for debugging and testing memory functionality.
    
    Args:
        user_id: User identifier
        memory_manager: Memory manager instance
    
    Returns:
        MemoryClearResponse indicating success
    """
    try:
        cleared = await memory_manager.clear_memory(user_id)
        
        return MemoryClearResponse(
            user_id=user_id,
            cleared=cleared,
            message="Memory cleared successfully" if cleared else "No memory found to clear"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing memory: {str(e)}"
        )


@query_router.delete("/documents/{user_id}")
async def clear_documents(
    user_id: str = Path(..., description="User identifier")
):
    """
    Clear all documents from user's RAG collection.
    
    Deletes all stored document embeddings for the user from Qdrant.
    
    Args:
        user_id: User identifier
    
    Returns:
        Status message indicating success or failure
    """
    try:
        rag_service = get_rag_service()
        deleted = await rag_service.delete_user_documents(user_id)
        
        return {
            "user_id": user_id,
            "cleared": deleted,
            "message": "Documents cleared successfully" if deleted else "No documents found to clear"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing documents: {str(e)}"
        )

