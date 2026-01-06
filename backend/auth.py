from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional
from models import User
from database import get_async_session
from sqlmodel import select
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-should-be-long-and-random")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Dependency to get current user object from token
async def get_current_user_obj(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await get_user_by_email(email, session)
    if user is None:
        raise credentials_exception
    return user

# Helper functions
async def get_user_by_email(email: str, session: AsyncSession) -> Optional[User]:
    """Get user by email from database"""
    result = await session.execute(select(User).where(User.email == email))
    return result.scalars().first()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def authenticate_user(email: str, password: str, session: AsyncSession) -> Optional[User]:
    """Authenticate user with email and password"""
    user = await get_user_by_email(email, session)
    if not user:
        return None
    if not user.verify_password(password):
        return None
    return user

# API Endpoints
@router.post("/auth/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_async_session)
):
    """Login endpoint - returns access token"""
    user = await authenticate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email,
        "name": user.name
    }

@router.post("/auth/logout")
async def logout():
    """Logout endpoint - JWT is stateless, so just return success"""
    return {"message": "Successfully logged out"}

@router.get("/auth/me")
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session)
):
    """Get current authenticated user information"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await get_user_by_email(email, session)
    if user is None:
        raise credentials_exception

    return {
        "user_id": user.id,
        "email": user.email,
        "name": user.name,
        "email_verified": user.email_verified is not None
    }

@router.post("/auth/change-password")
async def change_password(
    data: dict = Body(...),
    current_user: User = Depends(get_current_user_obj),
    session: AsyncSession = Depends(get_async_session)
):
    """Change password for the current authenticated user"""
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    if not current_password or not new_password:
        raise HTTPException(status_code=400, detail="current_password and new_password are required")
    if not current_user.verify_password(current_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.set_password(new_password)
    session.add(current_user)
    await session.commit()
    return {"message": "Password changed successfully"}

@router.get("/users")
async def list_users(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_obj),
):
    """List users (admin only)."""
    if current_user.email != "admin@test.com":
        raise HTTPException(status_code=403, detail="Only admin can manage users")
    result = await session.execute(select(User))
    users = result.scalars().all()
    return [
        {"id": u.id, "email": u.email, "name": u.name}
        for u in users
    ]

@router.post("/users")
async def create_user(
    data: dict = Body(...),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_obj),
):
    """Create a new user (admin only)."""
    if current_user.email != "admin@test.com":
        raise HTTPException(status_code=403, detail="Only admin can manage users")
    email = data.get("email")
    name = data.get("name")
    password = data.get("password")
    if not email or not password:
        raise HTTPException(status_code=400, detail="email and password are required")
    existing = await session.execute(select(User).where(User.email == email))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Email already exists")
    user = User(email=email, name=name)
    user.set_password(password)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return {"id": user.id, "email": user.email, "name": user.name}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_obj),
):
    """Delete a user by ID (admin only)."""
    if current_user.email != "admin@test.com":
        raise HTTPException(status_code=403, detail="Only admin can manage users")
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.email == "admin@test.com":
        raise HTTPException(status_code=400, detail="Cannot delete admin user")
    await session.delete(user)
    await session.commit()
    return {"message": "User deleted"}
