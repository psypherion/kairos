# File: core/app/agents/tools.py
# --- Purpose: Defines the callable Python functions that the AI agents can execute. ---

from sqlalchemy.orm import Session
from .. import crud, schemas, models
from ..crud import notes_collection, embedding_model


def retrieve_context(query: str, db: Session, user_id: int) -> str:
    """
    This is the primary tool for the ResearchAgent.
    It performs a RAG query against the user's ChromaDB vector store.
    """
    print(f"--- TOOL: Retrieving context for query: '{query}' ---")

    # 1. Create an embedding for the user's query
    query_embedding = embedding_model.encode(query).tolist()

    # 2. Query the ChromaDB collection to find the most relevant notes
    results = notes_collection.query(
        query_embeddings=[query_embedding],
        n_results=5,  # Return the top 5 most similar notes
        where={"owner_id": user_id}  # Filter results to only this user's notes
    )

    # 3. Format the results into a string to be passed to the LLM
    retrieved_documents = results.get('documents', [[]])[0]

    if not retrieved_documents:
        return "No relevant information found in the knowledge base."

    context_str = "\n---\n".join(retrieved_documents)
    print(f"--- TOOL: Found context: {context_str[:200]}... ---")  # Log a snippet of the context

    return context_str


def create_note_tool(title: str, content: str, db: Session, user_id: int) -> str:
    """
    Creates a new note in the user's database.
    """
    print(f"--- TOOL: Creating note with title: '{title}' ---")
    note_data = schemas.NoteCreate(title=title, content=content)
    crud.create_user_note(db=db, note=note_data, user_id=user_id)
    return f"Successfully created note titled '{title}'."


def create_project_tool(name: str, db: Session, user_id: int) -> str:
    """
    Creates a new project in the user's database.
    """
    print(f"--- TOOL: Creating project with name: '{name}' ---")
    project_data = schemas.ProjectCreate(name=name)
    crud.create_user_project(db=db, project=project_data, user_id=user_id)
    return f"Successfully created project named '{name}'."


def create_task_tool(project_name: str, title: str, db: Session, user_id: int) -> str:
    """
    Creates a new task under a specific project for the user.
    """
    print(f"--- TOOL: Creating task '{title}' for project '{project_name}' ---")
    # First, find the project by name for the current user
    projects = crud.get_projects(db=db, user_id=user_id, limit=1000)
    target_project = next((p for p in projects if p.name.lower() == project_name.lower()), None)

    if not target_project:
        return f"Error: Project '{project_name}' not found."

    task_data = schemas.TaskCreate(title=title)
    crud.create_project_task(db=db, task=task_data, project_id=target_project.id)
    return f"Successfully created task '{title}' in project '{project_name}'."


def log_anchor_tool(anchor_name: str, reflection: str, db: Session, user_id: int) -> str:
    """
    Logs a Micro Anchor practice for the user.
    """
    print(f"--- TOOL: Logging anchor '{anchor_name}' ---")
    log_data = schemas.MicroAnchorLogCreate(anchor_name=anchor_name, reflection=reflection)
    crud.create_anchor_log(db=db, anchor_log=log_data, user_id=user_id)
    return f"Successfully logged Micro Anchor: '{anchor_name}'."
