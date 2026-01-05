"""
Authentication API routes.
Handles signup, signin, signout, and token verification.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app.db.my_sql_config import get_db
from app.schemas.pydantic_schemas.auth_schema import (
    SignupRequest,
    SigninRequest,
    AuthResponse,
    MeResponse,
    UserData,
    LogoutResponse
)
from app.db.crud.user_crud import (
    create_user,
    authenticate_user,
    get_user_by_uuid,
    update_last_login
)
from app.utils.jwt_utils import (
    create_access_token,
    verify_token,
    get_token_expiration_seconds
)

auth_router = APIRouter(tags=["Authentication"])
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Dependency to get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer token credentials
        db: Database session
    
    Returns:
        Dictionary with user data (uuid, email)
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_uuid: str = payload.get("sub")
    if user_uuid is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify user exists and is active
    user = await get_user_by_uuid(db, user_uuid, include_inactive=False)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "uuid": user.uuid,
        "email": user.email,
        "userID": user.uuid  # For client compatibility
    }


@auth_router.post("/join", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    signup_data: SignupRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Sign up a new user.
    
    Creates a new user account with email and password.
    Returns JWT access token upon successful registration.
    """
    try:
        # Create user first (we need the user UUID for the token)
        user = await create_user(
            db=db,
            email=signup_data.email,
            password=signup_data.password
        )

        print(f"User created: {user}")
        
        # Create access token after user is created
        access_token_expires = timedelta(minutes=60)
        access_token = create_access_token(
            data={"sub": user.uuid, "email": user.email},
            expires_delta=access_token_expires
        )
        
        # Update last login
        await update_last_login(db, user)
        
        return AuthResponse(
            access_token=access_token,
            expires_in=get_token_expiration_seconds(),
            token_type="bearer",
            data=UserData(
                uuid=user.uuid,
                email=user.email,
                userID=user.uuid
            ),
            message="User created successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )


@auth_router.post("/signin", response_model=AuthResponse)
async def signin(
    signin_data: SigninRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Sign in an existing user.
    
    Authenticates user with email and password.
    Returns JWT access token upon successful authentication.
    """
    # Authenticate user
    user = await authenticate_user(
        db=db,
        email=signin_data.email,
        password=signin_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={"sub": user.uuid, "email": user.email},
        expires_delta=access_token_expires
    )
    
    # Update last login
    await update_last_login(db, user)
    
    return AuthResponse(
        access_token=access_token,
        expires_in=get_token_expiration_seconds(),
        token_type="bearer",
        data=UserData(
            uuid=user.uuid,
            email=user.email,
            userID=user.uuid
        ),
        message="Sign in successful"
    )


@auth_router.post("/logout", response_model=LogoutResponse)
async def logout(
    current_user: dict = Depends(get_current_user)
):
    """
    Logout the current user.
    
    Note: With JWT tokens, logout is typically handled client-side by removing the token.
    This endpoint can be used for logging purposes or to invalidate refresh tokens in the future.
    """
    return LogoutResponse(message="Logged out successfully")


@auth_router.get("/me", response_model=MeResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)
):
    """
    Get current authenticated user information.
    
    Returns user data from the JWT token.
    """
    return MeResponse(
        data=UserData(
            uuid=current_user["uuid"],
            email=current_user["email"],
            userID=current_user["userID"]
        ),
        message="User information retrieved successfully"
    )

