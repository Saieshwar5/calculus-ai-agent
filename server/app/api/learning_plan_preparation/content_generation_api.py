"""
Content Generation API routes.

Handles streaming educational content generation and topic completion tracking.
"""
from fastapi import APIRouter, HTTPException, Depends, Path, Request, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.schemas.pydantic_schemas.content_generation_schema import (
    ContentGenerationRequest,
    TopicCompletionRequest,
    TopicCompletionResponse,
    CompletionStats,
    ConceptProgressInfo,
    AllTopicsCompletedResponse,
    TopicHistoryItem,
    TopicHistoryResponse
)
from app.db.my_sql_config import get_db
from app.utils.auth_helpers import get_user_id
from app.db.crud.course.learning_plan_crud import get_learning_plan
from app.db.crud.course.semantic_memory_crud import get_semantic_memory
from app.db.crud.learning_preference_crud import get_learning_preference_by_user_id
from app.db.crud.course.topic_completion_crud import (
    create_topic_completion,
    get_completed_topics,
    get_completion_stats,
    get_topic_history_with_content
)
from app.db.crud.course.concept_progress_crud import (
    get_or_create_concept_progress,
    update_concept_progress,
    get_concept_progress
)
from app.core.learning_plan_engine.content_generator import (
    stream_content_generation,
    find_subject_in_plan,
    extract_topic_name_from_content,
    extract_depth_increment_from_content
)

content_generation_router = APIRouter(tags=["Content Generation"])


@content_generation_router.post("/stream-content/{user_id}")
async def stream_educational_content(
    request: Request,
    user_id: str = Path(..., description="User identifier"),
    db: AsyncSession = Depends(get_db)
):
    """
    Stream personalized educational content for the next topic in a subject.

    This endpoint:
    1. Retrieves the learning plan, semantic memory, and user preferences
    2. Gets list of completed topics to avoid repetition
    3. Uses AI to determine the next logical topic
    4. Streams comprehensive educational content
    5. Returns topic name in response headers

    Args:
        request: FastAPI request object
        user_id: User identifier from path
        db: Database session

    Returns:
        StreamingResponse with educational content

    Raises:
        HTTPException: If learning plan not found, subject not found, or all topics completed
    """
    try:
        # Parse request body
        body = await request.json()
        content_request = ContentGenerationRequest(**body)
        course_id = content_request.course_id
        subject_name = content_request.subject_name
        concept_name = content_request.concept_name

        print(f"\n{'='*80}")
        print(f"CONTENT GENERATION REQUEST")
        print(f"{'='*80}")
        print(f"User: {user_id}")
        print(f"Course: {course_id}")
        print(f"Subject: {subject_name}")
        if concept_name:
            print(f"Concept: {concept_name}")
        print(f"{'='*80}\n")

        # Retrieve learning plan
        learning_plan = await get_learning_plan(db, user_id, course_id)
        if not learning_plan:
            raise HTTPException(
                status_code=404,
                detail=f"Learning plan not found for user {user_id}, course {course_id}"
            )

        # Verify subject exists in plan
        subject = find_subject_in_plan(learning_plan.plan_data, subject_name)
        if not subject:
            raise HTTPException(
                status_code=404,
                detail=f"Subject '{subject_name}' not found in learning plan"
            )

        # Verify concept exists in subject
        concepts = subject.get("concepts", [])
        concept_names = [c.get("name", "").strip().lower() for c in concepts]
        if concept_name.strip().lower() not in concept_names:
            raise HTTPException(
                status_code=404,
                detail=f"Concept '{concept_name}' not found in subject '{subject_name}'. "
                       f"Available concepts: {', '.join([c.get('name', '') for c in concepts])}"
            )

        # Get completed topics for this subject
        completed_topics = await get_completed_topics(db, user_id, course_id, subject_name)
        print(f"📊 Completed topics: {len(completed_topics)}")

        # Check if all topics completed (heuristic: completed >= concepts count * 1.5)
        concepts = subject.get("concepts", [])
        num_concepts = len(concepts)
        max_topics = max(num_concepts * 2, 10)  # Allow 2x concepts or at least 10 topics

        if len(completed_topics) >= max_topics:
            # All topics likely completed
            stats = await get_completion_stats(db, user_id, course_id, subject_name)
            response = AllTopicsCompletedResponse(
                message=f"Congratulations! You've completed {len(completed_topics)} topics in {subject_name}. "
                        f"You've mastered this subject!",
                completion_stats=CompletionStats(
                    total_completed=stats["total_completed"],
                    subject_name=stats.get("subject_name")
                )
            )
            return response.model_dump(by_alias=True)

        # Retrieve semantic memory (optional)
        semantic_memory = await get_semantic_memory(db, user_id, course_id)
        if not semantic_memory:
            print("⚠️ No semantic memory found - content will be less personalized")

        # Retrieve learning preferences (optional)
        learning_preferences = await get_learning_preference_by_user_id(db, user_id)
        if not learning_preferences:
            print("⚠️ No learning preferences found - using default teaching style")

        # Store topic name and depth increment for headers
        topic_name_holder = {"topic": None}
        depth_increment_holder = {"depth": 1}
        full_content = {"content": ""}

        async def content_generator():
            """Generator that streams content and captures topic name and depth."""
            try:
                # Stream content from AI
                generator, topic_hint, depth_hint = await stream_content_generation(
                    user_id=user_id,
                    course_id=course_id,
                    subject_name=subject_name,
                    learning_plan=learning_plan,
                    semantic_memory=semantic_memory,
                    learning_preferences=learning_preferences,
                    completed_topics=completed_topics,
                    concept_name=concept_name
                )

                async for chunk in generator:
                    full_content["content"] += chunk

                    # Try to extract topic name from accumulated content
                    if not topic_name_holder["topic"] and "TOPIC:" in full_content["content"]:
                        extracted = extract_topic_name_from_content(full_content["content"])
                        if extracted:
                            topic_name_holder["topic"] = extracted

                    # Try to extract depth increment from accumulated content
                    if depth_increment_holder["depth"] == 1 and "DEPTH_INCREMENT:" in full_content["content"]:
                        extracted_depth = extract_depth_increment_from_content(full_content["content"])
                        if extracted_depth:
                            depth_increment_holder["depth"] = extracted_depth

                    yield chunk

            except Exception as e:
                error_msg = f"\n\n[Error generating content: {str(e)}]"
                print(f"❌ Content generation error: {str(e)}")
                yield error_msg

        # Create streaming response with headers
        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Subject-Name": subject_name,
            "X-Concept-Name": concept_name,
        }

        # Note: Topic name and depth increment will be extracted during streaming
        # They won't be known until the first chunk is processed
        # Client should parse TOPIC: and DEPTH_INCREMENT: from content

        response = StreamingResponse(
            content_generator(),
            media_type="text/plain",
            headers=headers
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in stream_educational_content: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating content: {str(e)}"
        )


@content_generation_router.post("/mark-topic-complete/{user_id}")
async def mark_topic_complete(
    request: Request,
    user_id: str = Path(..., description="User identifier"),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a topic as completed.

    This endpoint is called by the client after the user has finished studying a topic.
    It records the completion in the database to prevent repetition and tracks progress.

    Args:
        request: FastAPI request object
        user_id: User identifier from path
        db: Database session

    Returns:
        TopicCompletionResponse with success status and completion statistics

    Raises:
        HTTPException: If topic already completed or database error
    """
    try:
        # Parse request body
        body = await request.json()
        completion_request = TopicCompletionRequest(**body)
        course_id = completion_request.course_id
        subject_name = completion_request.subject_name
        concept_name = completion_request.concept_name
        topic_name = completion_request.topic_name
        depth_increment = completion_request.depth_increment
        content_snapshot = completion_request.content_snapshot
        full_content = completion_request.full_content

        print(f"\n{'='*80}")
        print(f"MARKING TOPIC AS COMPLETE")
        print(f"{'='*80}")
        print(f"User: {user_id}")
        print(f"Course: {course_id}")
        print(f"Subject: {subject_name}")
        print(f"Concept: {concept_name}")
        print(f"Topic: {topic_name}")
        print(f"Depth Increment: +{depth_increment}")
        print(f"{'='*80}\n")

        # Get learning plan to find target depth for concept
        learning_plan = await get_learning_plan(db, user_id, course_id)
        if not learning_plan:
            raise HTTPException(
                status_code=404,
                detail=f"Learning plan not found for user {user_id}, course {course_id}"
            )

        # Find concept in learning plan to get target depth
        subject = find_subject_in_plan(learning_plan.plan_data, subject_name)
        if not subject:
            raise HTTPException(
                status_code=404,
                detail=f"Subject '{subject_name}' not found in learning plan"
            )

        # Find concept to get target depth
        concepts = subject.get("concepts", [])
        target_depth = 5  # Default
        for concept in concepts:
            if concept.get("name", "").strip().lower() == concept_name.strip().lower():
                target_depth = concept.get("depth", 5)
                break

        # Get or create concept progress
        concept_progress = await get_or_create_concept_progress(
            db=db,
            user_id=user_id,
            course_id=course_id,
            subject_name=subject_name,
            concept_name=concept_name,
            target_depth=target_depth
        )

        # Create topic completion record
        try:
            completion = await create_topic_completion(
                db=db,
                user_id=user_id,
                course_id=course_id,
                subject_name=subject_name,
                concept_name=concept_name,
                topic_name=topic_name,
                depth_increment=depth_increment,
                content_snapshot=content_snapshot,
                full_content=full_content
            )
        except ValueError as e:
            # Topic already completed
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )

        # Update concept progress
        concept_progress = await update_concept_progress(
            db=db,
            user_id=user_id,
            course_id=course_id,
            subject_name=subject_name,
            concept_name=concept_name,
            depth_increment=depth_increment,
            topic_name=topic_name
        )

        # Get updated completion statistics
        stats = await get_completion_stats(db, user_id, course_id, subject_name)

        # Determine next action
        next_action = "concept_complete" if concept_progress.completed else "continue_learning"

        # Build response
        response = TopicCompletionResponse(
            success=True,
            message=f"Topic '{topic_name}' marked as complete",
            topic_id=completion.id,
            completion_stats=CompletionStats(
                total_completed=stats["total_completed"],
                subject_name=stats.get("subject_name"),
                subjects_breakdown=stats.get("subjects_breakdown")
            ),
            topic_name=topic_name,
            completed_at=completion.completed_at,
            concept_progress=ConceptProgressInfo(
                concept_name=concept_progress.concept_name,
                current_depth=concept_progress.current_depth,
                target_depth=concept_progress.target_depth,
                topics_completed=concept_progress.topics_completed,
                progress_percent=concept_progress.progress_percentage,
                last_topic_name=concept_progress.last_topic_name,
                completed=concept_progress.completed
            ),
            next_action=next_action
        )

        return response.model_dump(by_alias=True)

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error marking topic complete: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error marking topic complete: {str(e)}"
        )


@content_generation_router.get("/completion-stats/{user_id}/{course_id}")
async def get_course_completion_stats(
    user_id: str = Path(..., description="User identifier"),
    course_id: str = Path(..., description="Course identifier"),
    subject_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get completion statistics for a course or specific subject.

    Args:
        user_id: User identifier
        course_id: Course identifier
        subject_name: Optional subject name filter
        db: Database session

    Returns:
        Completion statistics including total completed and per-subject breakdown
    """
    try:
        stats = await get_completion_stats(db, user_id, course_id, subject_name)

        return {
            "success": True,
            "userId": user_id,
            "courseId": course_id,
            "totalCompleted": stats["total_completed"],
            "subjectName": stats.get("subject_name"),
            "subjectsBreakdown": stats.get("subjects_breakdown", {})
        }

    except Exception as e:
        print(f"❌ Error getting completion stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving completion statistics: {str(e)}"
        )


@content_generation_router.get("/topic-history/{user_id}")
async def get_topic_history_for_concept(
    user_id: str = Path(..., description="User identifier"),
    course_id: str = Query(..., description="Course identifier"),
    subject_name: str = Query(..., description="Subject name"),
    concept_name: str = Query(..., description="Concept name"),
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch all completed topics with full content for navigation within a concept.

    Args:
        user_id: User identifier
        course_id: Course identifier
        subject_name: Subject name
        concept_name: Concept name
        db: Database session

    Returns:
        TopicHistoryResponse with list of completed topics including full content
    """
    try:
        print(f"\n{'='*80}")
        print(f"FETCHING TOPIC HISTORY")
        print(f"{'='*80}")
        print(f"User: {user_id}")
        print(f"Course: {course_id}")
        print(f"Subject: {subject_name}")
        print(f"Concept: {concept_name}")
        print(f"{'='*80}\n")

        # Fetch topic history
        topics = await get_topic_history_with_content(
            db=db,
            user_id=user_id,
            course_id=course_id,
            subject_name=subject_name,
            concept_name=concept_name
        )

        # Convert to response schema
        topic_items = [
            TopicHistoryItem(
                id=topic.id,
                topic_name=topic.topic_name,
                completed_at=topic.completed_at,
                full_content=topic.full_content,
                depth_increment=topic.depth_increment,
                content_snapshot=topic.content_snapshot
            )
            for topic in topics
        ]

        print(f"📚 Found {len(topic_items)} completed topics")

        response = TopicHistoryResponse(
            success=True,
            topics=topic_items,
            total_count=len(topic_items)
        )

        return response.model_dump(by_alias=True)

    except Exception as e:
        print(f"❌ Error fetching topic history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching topic history: {str(e)}"
        )
