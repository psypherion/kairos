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
    This is a tool for the TaskMasterAgent.
    It creates a new note in the user's database.
    """
    print(f"--- TOOL: Creating note with title: '{title}' ---")
    note_data = schemas.NoteCreate(title=title, content=content)
    crud.create_user_note(db=db, note=note_data, user_id=user_id)
    return f"Successfully created note titled '{title}'."

# We will add more tools here later, like create_project, create_task, etc.
