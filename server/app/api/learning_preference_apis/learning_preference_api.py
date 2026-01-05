"""
Learning Preference API routes.
This file contains only routing logic - all CRUD operations are in learning_preference_crud.py
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.my_sql_config import get_db
from app.schemas.pydantic_schemas.learning_preference_schema import (
    LearningPreferenceCreate,
    LearningPreferenceUpdate,
    LearningPreferenceResponse
)
from app.db.crud.learning_preference_crud import (
    get_learning_preference_by_user_id,
    create_learning_preference as crud_create_learning_preference,
    update_learning_preference as crud_update_learning_preference,
    create_or_update_learning_preference as crud_create_or_update_learning_preference
)
from app.utils.auth_helpers import get_user_id

learning_preference_router = APIRouter(tags=["Learning Preferences"])


@learning_preference_router.post("/learnconfig/create", response_model=LearningPreferenceResponse, status_code=201)
async def create_learning_config(
    preference_data: LearningPreferenceCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id)
):
    """
    Create new learning preferences for the current user.
    """
    try:
        preference = await crud_create_learning_preference(db, user_id, preference_data)
        return preference
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating learning preferences: {str(e)}")


@learning_preference_router.put("/learnconfig/update/", response_model=LearningPreferenceResponse)
async def update_learning_config(
    preference_data: LearningPreferenceCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id)
):
    """
    Update current user's learning preferences.
    Uses upsert logic - creates if doesn't exist, updates if it does.
    """
    try:
        preference = await crud_create_or_update_learning_preference(db, user_id, preference_data)
        return preference
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating learning preferences: {str(e)}")


@learning_preference_router.get("/learnconfig", response_model=LearningPreferenceResponse)
async def get_learning_config(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id)
):
    """
    Get current user's learning preferences.
    """
    try:
        preference = await get_learning_preference_by_user_id(db, user_id)
        if not preference:
            raise HTTPException(status_code=404, detail="Learning preferences not found")
        return preference
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching learning preferences: {str(e)}")


@learning_preference_router.post("/learnconfig/upsert", response_model=LearningPreferenceResponse)
async def upsert_learning_config(
    preference_data: LearningPreferenceCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id)
):
    """
    Create or update learning preferences (upsert operation).
    Useful when you're not sure if preferences already exist.
    """
    try:
        preference = await crud_create_or_update_learning_preference(db, user_id, preference_data)
        return preference
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error upserting learning preferences: {str(e)}")

