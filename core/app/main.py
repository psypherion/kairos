# File: core/app/main.py
# --- Purpose: The main entry point for the FastAPI application, defining API endpoints. ---

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta

# Import all our modules
from . import crud, models, schemas, dependencies
from .database import engine, get_db
from .agents import team  # Import the agent team

# This crucial line tells SQLAlchemy to create all the database tables
# based on the models defined in models.py.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Project Kairos Core")


# --- Chat Schema ---
class ChatRequest(schemas.BaseModel):
    message: str


class ChatResponse(schemas.BaseModel):
    reply: str


@app.get("/")
def read_root():
    """Root endpoint to confirm the server is running."""
    return {"status": "Kairos Core is online"}


# --- Authentication Endpoints ---
@app.post("/token", response_model=schemas.Token)
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Provides a token for a user after verifying their password.
    The client sends 'username' and 'password' in a form body.
    """
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not dependencies.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=dependencies.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = dependencies.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# --- User Endpoints ---
@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Creates a new user."""
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/me/", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(dependencies.get_current_user)):
    """Returns the details of the currently authenticated user."""
    return current_user


# --- Note Endpoints ---
@app.post("/notes/", response_model=schemas.Note)
def create_note_for_user(
        note: schemas.NoteCreate, db: Session = Depends(get_db),
        current_user: models.User = Depends(dependencies.get_current_user)
):
    """Creates a new note for the currently authenticated user."""
    return crud.create_user_note(db=db, note=note, user_id=current_user.id)


@app.get("/notes/", response_model=List[schemas.Note])
def read_notes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
               current_user: models.User = Depends(dependencies.get_current_user)):
    """Lists all notes for the currently authenticated user."""
    notes = crud.get_notes(db, user_id=current_user.id, skip=skip, limit=limit)
    return notes


# --- Agent Chat Endpoint ---
@app.post("/chat/", response_model=ChatResponse)
def chat_with_agents(
        request: ChatRequest,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(dependencies.get_current_user)
):
    """
    Initiates a conversation with the Kairos agentic team.
    """
    # Register the tools with the current user's context
    team.register_tools(db_session=db, user_id=current_user.id)

    # Initiate the chat with the user's message
    team.user_proxy.initiate_chat(
        recipient=team.group_chat_manager,
        message=request.message,
    )

    # The last message in the chat history is the final reply
    final_reply = team.groupchat.messages[-1]['content']

    # Clear the chat history for the next interaction
    team.groupchat.reset()

    return {"reply": final_reply}

