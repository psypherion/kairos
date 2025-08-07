# File: core/app/crud.py
# --- Purpose: Holds all the database interaction logic (Create, Read, Update, Delete). ---

from sqlalchemy.orm import Session
from . import models, schemas, dependencies
from typing import Optional

# --- User CRUD ---
def get_user_by_email(db: Session, email: str):
    """Fetches a single user by their email address."""
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    """Creates a new user in the database."""
    hashed_password = dependencies.get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Note CRUD ---
def get_notes(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """Fetches all notes for a specific user."""
    return db.query(models.Note).filter(models.Note.owner_id == user_id).offset(skip).limit(limit).all()

def create_user_note(db: Session, note: schemas.NoteCreate, user_id: int):
    """Creates a new note for a specific user."""
    db_note = models.Note(**note.model_dump(), owner_id=user_id)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note
