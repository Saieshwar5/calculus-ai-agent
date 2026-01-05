"""
Profile API routes.
This file contains only routing logic - all CRUD operations are in profile_crud.py
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.my_sql_config import get_db
from app.schemas.pydantic_schemas.profile_schema import (
    ProfileCreate,
    ProfileUpdate,
    ProfileResponse,
    ProfileListResponse
)
from app.db.crud.profile_crud import (
    get_profile_by_user_id,
    create_profile as crud_create_profile,
    update_profile as crud_update_profile,
    delete_profile as crud_delete_profile,
    activate_profile as crud_activate_profile,
    list_profiles as crud_list_profiles
)
from app.utils.auth_helpers import get_user_id, check_admin

profile_router = APIRouter(tags=["Profile"])


# ==================== USER PROFILE ROUTES ====================

@profile_router.post("/profile", response_model=ProfileResponse, status_code=201)
async def create_profile(
    profile_data: ProfileCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id)
):
    """
    Create a new user profile.
    """
    try:
       # user_id = "123e4567-e89b-12d3-a456-426614174092"
        profile = await crud_create_profile(db, user_id, profile_data)
        return profile
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating profile: {str(e)}")


@profile_router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id)
):
    """
    Get current user's profile.
    """
    try:
        profile = await get_profile_by_user_id(db, user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching profile: {str(e)}")


@profile_router.put("/profile", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id)
):
    """
    Update current user's profile.
    """
    try:
        profile = await crud_update_profile(db, user_id, profile_data)
        return profile
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating profile: {str(e)}")


@profile_router.delete("/profile", status_code=204)
async def delete_profile(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id)
):
    """
    Soft delete current user's profile (sets is_active to False).
    """
    try:
        await crud_delete_profile(db, user_id, hard_delete=False)
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting profile: {str(e)}")


# ==================== ADMIN ROUTES ====================

@profile_router.get("/admin/profiles", response_model=ProfileListResponse)
async def list_all_profiles(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(check_admin)
):
    """
    Admin: Get list of all user profiles with pagination.
    """
    try:
        profiles, total = await crud_list_profiles(db, page, page_size, is_active)
        return ProfileListResponse(
            profiles=[ProfileResponse.model_validate(p) for p in profiles],
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching profiles: {str(e)}")


@profile_router.get("/admin/profiles/{user_id}", response_model=ProfileResponse)
async def get_profile_by_user_id_admin(
    user_id: str = Path(..., description="User ID"),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(check_admin)
):
    """
    Admin: Get profile by user_id.
    """
    try:
        profile = await get_profile_by_user_id(db, user_id, include_inactive=True)
        if not profile:
            raise HTTPException(status_code=404, detail=f"Profile not found for user_id: {user_id}")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching profile: {str(e)}")


@profile_router.put("/admin/profiles/{user_id}", response_model=ProfileResponse)
async def admin_update_profile(
    user_id: str = Path(..., description="User ID"),
    profile_data: ProfileUpdate = ...,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(check_admin)
):
    """
    Admin: Update any user's profile.
    """
    try:
        profile = await crud_update_profile(db, user_id, profile_data, include_inactive=True)
        return profile
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating profile: {str(e)}")


@profile_router.delete("/admin/profiles/{user_id}", status_code=204)
async def admin_delete_profile(
    user_id: str = Path(..., description="User ID"),
    hard_delete: bool = Query(False, description="Hard delete (permanently remove)"),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(check_admin)
):
    """
    Admin: Delete user profile (soft delete by default, hard delete if specified).
    """
    try:
        await crud_delete_profile(db, user_id, hard_delete=hard_delete)
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting profile: {str(e)}")


@profile_router.post("/admin/profiles/{user_id}/activate", response_model=ProfileResponse)
async def admin_activate_profile(
    user_id: str = Path(..., description="User ID"),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(check_admin)
):
    """
    Admin: Activate a user profile (set is_active to True).
    """
    try:
        profile = await crud_activate_profile(db, user_id)
        return profile
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error activating profile: {str(e)}")
