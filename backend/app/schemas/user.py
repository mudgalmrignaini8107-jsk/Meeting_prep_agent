# app/schemas/user.py

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr

class WorkspaceBase(BaseModel):
    name: str

class WorkspaceCreate(WorkspaceBase):
    pass

class WorkspaceRead(WorkspaceBase):
    id: int
    name: str
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    email: EmailStr
    created_at: datetime
    workspaces: List[WorkspaceRead] = []

    class Config:
        from_attributes = True
