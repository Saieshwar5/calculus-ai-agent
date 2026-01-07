"""
Learning Plan Creation API routes.
Handles streaming conversation for interactive learning plan generation.
"""
from fastapi import APIRouter, HTTPException, Depends, Path, Request
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from app.core.learning_plan_engine.session_manager import (
    get_session_manager,
    LearningPlanSessionManager
)
from app.core.learning_plan_engine.learning_plan import (
    stream_learning_plan_response,
    parse_final_plan,
    create_learning_plan_object,
    print_session_summary,
    extract_semantic_memory
)
from app.schemas.pydantic_schemas.learning_plan_schema import (
    LearningPlanQueryRequest,
    SessionInfoResponse,
    SessionClearResponse,
    LearningPlanMessage,
    LearningPlanCreate
)
from app.db.my_sql_config import get_db
from app.db.crud.course import (
    create_learning_plan as db_create_learning_plan,
    create_semantic_memory as db_create_semantic_memory,
    get_user_learning_plans,
    learning_plan_to_response
)

learning_plan_router = APIRouter(tags=["Learning Plan Creation"])


async def stream_plan_creation(
    user_id: str,
    plan_id: str,
    query_text: str,
    session_manager: LearningPlanSessionManager,
    db: AsyncSession
):
    """
    Generator function that streams learning plan creation responses.

    Args:
        user_id: User identifier
        plan_id: Plan session identifier
        query_text: User's query/response
        session_manager: Session manager instance
        db: Database session
    """
    full_response = ""

    try:
        # Store user message in session
        await session_manager.add_message(
            user_id=user_id,
            plan_id=plan_id,
            role="user",
            content=query_text
        )

        # Stream OpenAI response
        async for chunk in stream_learning_plan_response(
            query_text=query_text,
            user_id=user_id,
            plan_id=plan_id,
            session_manager=session_manager,
            model="gpt-4o-mini",
            temperature=0.7
        ):
            full_response += chunk
            yield chunk

        # Store assistant response in session
        if full_response and full_response.strip():
            await session_manager.add_message(
                user_id=user_id,
                plan_id=plan_id,
                role="assistant",
                content=full_response
            )

        # Check if response contains FINAL_PLAN
        is_final, message_part, plan_dict = parse_final_plan(full_response)

        if is_final and plan_dict:
            print(f"✅ [API] Detected FINAL_PLAN for user {user_id}, plan {plan_id}")

            try:
                # Create learning plan object
                final_plan = create_learning_plan_object(plan_id, plan_dict)

                # Print session summary (as requested in requirements)
                await print_session_summary(
                    user_id=user_id,
                    plan_id=plan_id,
                    session_manager=session_manager,
                    final_plan=final_plan
                )

                # === NEW: Extract semantic memory from conversation ===
                print("\n" + "="*80)
                print("EXTRACTING SEMANTIC MEMORY")
                print("="*80)

                # Get all conversation messages
                messages = await session_manager.get_messages(user_id, plan_id)

                # Extract semantic memory using OpenAI
                semantic_memory, conversation_summary = await extract_semantic_memory(messages)

                if semantic_memory:
                    print(f"✅ Semantic memory extracted successfully")

                    # Save semantic memory to database
                    try:
                        await db_create_semantic_memory(
                            db=db,
                            user_id=user_id,
                            course_id=plan_id,
                            memory_data=semantic_memory,
                            conversation_summary=conversation_summary
                        )
                        print(f"✅ Semantic memory saved to database")
                    except Exception as db_error:
                        print(f"⚠️ Error saving semantic memory to DB: {str(db_error)}")
                else:
                    print(f"⚠️ Failed to extract semantic memory")

                print("="*80 + "\n")

                # === NEW: Save learning plan to database ===
                print("\n" + "="*80)
                print("SAVING LEARNING PLAN TO DATABASE")
                print("="*80)

                try:
                    plan_create = LearningPlanCreate(
                        user_id=user_id,
                        course_id=plan_id,
                        title=plan_dict.get("title", "Untitled Course"),
                        description=plan_dict.get("description", ""),
                        plan_data=plan_dict,
                        status="active"
                    )

                    await db_create_learning_plan(db=db, plan_data=plan_create)
                    print(f"✅ Learning plan saved to database")
                    print(f"   Title: {plan_create.title}")
                    print(f"   Subjects: {len(plan_dict.get('subjects', []))}")
                except Exception as db_error:
                    print(f"⚠️ Error saving learning plan to DB: {str(db_error)}")

                print("="*80 + "\n")

                # Print Redis cache summary
                print("\n" + "="*80)
                print("REDIS CACHE SUMMARY")
                print("="*80)
                session_data = await session_manager.get_session_data(user_id, plan_id)
                if session_data:
                    print(f"\n📦 Cached in Redis:")
                    print(f"   Key Pattern: learning_plan:{user_id}:{plan_id}:*")
                    print(f"   Messages Stored: {session_data['message_count']}")
                    print(f"   TTL: {session_manager.SESSION_TTL_DAYS} days")
                    print(f"   Metadata: {session_data.get('metadata', {})}")
                print("="*80 + "\n")

            except Exception as e:
                print(f"⚠️ [API] Error processing final plan: {str(e)}")

    except Exception as e:
        error_message = f"Error generating learning plan: {str(e)}"
        print(f"❌ {error_message}")
        yield f"\n\n[Error: {error_message}]"


@learning_plan_router.post("/stream-learning-plan/{user_id}")
async def stream_learning_plan(
    request: Request,
    user_id: str = Path(..., description="User identifier"),
    session_manager: LearningPlanSessionManager = Depends(get_session_manager),
    db: AsyncSession = Depends(get_db)
):
    """
    Stream a learning plan creation conversation.

    The endpoint handles an interactive conversation where the AI asks questions
    to understand the user's learning goals and eventually generates a structured
    learning plan.

    **Request Body:**
    ```json
    {
        "query": "I want to learn web development",
        "planId": null  // optional, will create new session if not provided
    }
    ```

    **Response:**
    - Streams text chunks from the AI conversation
    - When ready, sends FINAL_PLAN marker followed by JSON structure
    - Client should detect FINAL_PLAN to extract the learning plan

    **Headers:**
    - X-Plan-ID: The plan session identifier (for continuing conversation)

    Args:
        request: FastAPI Request object
        user_id: User identifier from URL path
        session_manager: Session manager instance

    Returns:
        StreamingResponse with text chunks
    """
    try:
        content_type = request.headers.get("content-type", "")

        if "application/json" not in content_type:
            raise HTTPException(
                status_code=400,
                detail="Content-Type must be 'application/json'"
            )

        # Parse request body
        body = await request.json()

        try:
            query_request = LearningPlanQueryRequest(**body)
        except ValidationError as e:
            raise HTTPException(
                status_code=422,
                detail=f"Validation error: {e.errors()}"
            )

        query_text = query_request.query
        plan_id = query_request.plan_id

        # Create new session if plan_id not provided or session doesn't exist
        if not plan_id or not await session_manager.session_exists(user_id, plan_id):
            plan_id = await session_manager.create_session(user_id, plan_id)
            print(f"✅ [API] Created new learning plan session: {plan_id}")
        else:
            print(f"📝 [API] Continuing existing session: {plan_id}")

        # Create streaming response
        async def response_generator():
            async for chunk in stream_plan_creation(
                user_id, plan_id, query_text, session_manager, db
            ):
                yield chunk

        return StreamingResponse(
            response_generator(),
            media_type="text/plain",
            headers={
                "X-Plan-ID": plan_id,
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing learning plan request: {str(e)}"
        )


@learning_plan_router.get("/learning-plan-session/{user_id}/{plan_id}")
async def get_learning_plan_session(
    user_id: str = Path(..., description="User identifier"),
    plan_id: str = Path(..., description="Plan session identifier"),
    session_manager: LearningPlanSessionManager = Depends(get_session_manager)
):
    """
    Get learning plan session data (for debugging).

    Retrieves the complete conversation history and metadata for a learning plan session.

    Args:
        user_id: User identifier
        plan_id: Plan session identifier
        session_manager: Session manager instance

    Returns:
        SessionInfoResponse with session data
    """
    try:
        # Check if session exists
        if not await session_manager.session_exists(user_id, plan_id):
            raise HTTPException(
                status_code=404,
                detail=f"Session not found for user {user_id}, plan {plan_id}"
            )

        # Get session data
        session_data = await session_manager.get_session_data(user_id, plan_id)

        if not session_data:
            raise HTTPException(
                status_code=404,
                detail="Session data not found"
            )

        # Convert messages to Pydantic models
        messages = [
            LearningPlanMessage(**msg)
            for msg in session_data["messages"]
        ]

        return SessionInfoResponse(
            user_id=user_id,
            plan_id=plan_id,
            message_count=session_data["message_count"],
            messages=messages,
            metadata=session_data.get("metadata")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving session: {str(e)}"
        )


@learning_plan_router.delete("/learning-plan-session/{user_id}/{plan_id}")
async def clear_learning_plan_session(
    user_id: str = Path(..., description="User identifier"),
    plan_id: str = Path(..., description="Plan session identifier"),
    session_manager: LearningPlanSessionManager = Depends(get_session_manager)
):
    """
    Clear a learning plan session.

    Deletes all conversation messages and metadata for the specified session.

    Args:
        user_id: User identifier
        plan_id: Plan session identifier
        session_manager: Session manager instance

    Returns:
        SessionClearResponse indicating success
    """
    try:
        cleared = await session_manager.clear_session(user_id, plan_id)

        return SessionClearResponse(
            user_id=user_id,
            plan_id=plan_id,
            cleared=cleared,
            message="Session cleared successfully" if cleared else "Session not found"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing session: {str(e)}"
        )


@learning_plan_router.get("/plans/{user_id}")
async def get_learning_plans(
    user_id: str = Path(..., description="User identifier"),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve all saved learning plans for a user.

    This endpoint fetches learning plans that have been saved to the database
    after the user completed the conversational planning process.

    **Query Parameters:**
    - status: Optional filter by status (draft|active|completed|archived)

    Args:
        user_id: User identifier from URL path
        status: Optional status filter
        db: Database session

    Returns:
        List of learning plans in camelCase format for frontend consumption
    """
    try:
        # Get learning plans from database
        plans = await get_user_learning_plans(db, user_id, status)

        # Convert to response format (camelCase for frontend)
        response_plans = [learning_plan_to_response(plan) for plan in plans]

        # Convert Pydantic models to dicts with camelCase aliases
        return [plan.model_dump(by_alias=True) for plan in response_plans]

    except Exception as e:
        print(f"❌ Error retrieving learning plans for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving learning plans: {str(e)}"
        )
