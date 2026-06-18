from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=100, description="Plain password, will be hashed")


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}
    
    id: int
    email: EmailStr
    created_at: datetime