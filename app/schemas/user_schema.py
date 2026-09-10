from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    username: str
    email: EmailStr
    role: str
    created_at: datetime


class UpdateRoleRequest(BaseModel):
    role: str
