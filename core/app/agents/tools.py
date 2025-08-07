# File: core/app/agents/tools.py
# --- Purpose: Defines the callable Python functions that the AI agents can execute. ---

from sqlalchemy.orm import Session
from .. import crud, schemas


def retrieve_context(query: str, db: Session, user_id: int) -> str:
    """
    This is the primary tool for the ResearchAgent.
    It will perform a RAG query against the user's vector database.
    (For now, we will simulate this by searching the regular database).
    """
    print(f"--- TOOL: Retrieving context for query: '{query}' ---")
    # In the future, this will query ChromaDB.
    # For now, let's search all note titles and content.
    notes = crud.get_notes(db, user_id=user_id, limit=1000)

    relevant_notes = [
        f"Title: {note.title}\nContent: {note.content}"
        for note in notes
        if query.lower() in note.title.lower() or (note.content and query.lower() in note.content.lower())
    ]

    if not relevant_notes:
        return "No relevant information found in the knowledge base."

    return "\n---\n".join(relevant_notes)


def create_note_tool(title: str, content: str, db: Session, user_id: int) -> str:
    """
    This is a tool for the TaskMasterAgent.
    It creates a new note in the user's database.
    """
    print(f"--- TOOL: Creating note with title: '{title}' ---")
    note_data = schemas.NoteCreate(title=title, content=content)
    crud.create_user_note(db=db, note=note_data, user_id=user_id)
    return f"Successfully created note titled '{title}'."

# We will add more tools here later, like create_project, create_task, etc.
