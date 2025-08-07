# File: core/app/schemas.py
# --- Purpose: Defines the data shapes for API validation using Pydantic. ---

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# --- Task Schemas ---
class TaskBase(BaseModel):
    title: str

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    id: int
    project_id: int

    class Config:
        from_attributes = True

# --- Note Schemas ---
class NoteBase(BaseModel):
    title: str
    content: Optional[str] = None

class NoteCreate(NoteBase):
    pass

class Note(NoteBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True

# --- Project Schemas ---
class ProjectBase(BaseModel):
    name: str

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: int
    owner_id: int
    tasks: List[Task] = []

    class Config:
        from_attributes = True

# --- Micro Anchor Schemas ---
class MicroAnchorLogBase(BaseModel):
    anchor_name: str
    reflection: Optional[str] = None

class MicroAnchorLogCreate(MicroAnchorLogBase):
    pass

class MicroAnchorLog(MicroAnchorLogBase):
    id: int
    timestamp: datetime
    owner_id: int

    class Config:
        from_attributes = True

# --- User Schemas ---
class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    notes: List[Note] = []
    projects: List[Project] = []
    anchor_logs: List[MicroAnchorLog] = []

    class Config:
        from_attributes = True
