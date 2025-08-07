# File: core/app/crud.py
# --- Purpose: Holds all the database interaction logic (Create, Read, Update, Delete). ---

from sqlalchemy.orm import Session
from . import models, schemas, dependencies
import chromadb
from sentence_transformers import SentenceTransformer

# --- RAG Pipeline Setup ---
# Initialize the embedding model. This will download the model on first run.
embedding_model = SentenceTransformer('nomic-embed-text')

# Initialize the ChromaDB client. It will store data in the 'vector_store' directory.
chroma_client = chromadb.PersistentClient(path="./core/app/data/vector_store")

# Get or create a collection to store the note embeddings.
# In a multi-user app, you would create a separate collection for each user.
notes_collection = chroma_client.get_or_create_collection(name="kairos_notes")


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
    """
    Creates a new note for a specific user and adds its content to the vector store.
    """
    # 1. Create the note in the regular SQL database
    db_note = models.Note(**note.model_dump(), owner_id=user_id)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)

    # 2. Create the embedding for the RAG pipeline
    note_content = f"Title: {db_note.title}\nContent: {db_note.content}"
    embedding = embedding_model.encode(note_content).tolist()

    # 3. Add the embedding to the ChromaDB vector store
    notes_collection.add(
        embeddings=[embedding],
        documents=[note_content],
        metadatas=[{"title": db_note.title, "owner_id": user_id}],
        ids=[f"note_{db_note.id}"]  # Create a unique ID for the vector
    )

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
