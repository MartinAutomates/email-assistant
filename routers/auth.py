from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.db import User
from models.user import UserCreate, UserResponse
from auth import hash_password


router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user is not None:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )
    
    # Create new user with hashed password
    new_user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user