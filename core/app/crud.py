# File: core/app/crud.py
# --- Purpose: Holds all the database interaction logic (Create, Read, Update, Delete). ---

from sqlalchemy.orm import Session
from . import models, schemas, dependencies

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

# --- Project CRUD ---
def get_projects(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """Fetches all projects for a specific user."""
    return db.query(models.Project).filter(models.Project.owner_id == user_id).offset(skip).limit(limit).all()

def create_user_project(db: Session, project: schemas.ProjectCreate, user_id: int):
    """Creates a new project for a specific user."""
    db_project = models.Project(**project.model_dump(), owner_id=user_id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

# --- Task CRUD ---
def create_project_task(db: Session, task: schemas.TaskCreate, project_id: int):
    """Creates a new task for a specific project."""
    db_task = models.Task(**task.model_dump(), project_id=project_id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

# --- Micro Anchor CRUD ---
def create_anchor_log(db: Session, anchor_log: schemas.MicroAnchorLogCreate, user_id: int):
    """Creates a new Micro Anchor log entry for a user."""
    db_log = models.MicroAnchorLog(**anchor_log.model_dump(), owner_id=user_id)
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log
