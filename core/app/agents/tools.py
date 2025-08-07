# File: core/app/agents/tools.py
# --- Purpose: Defines the callable Python functions that the AI agents can execute. ---

import asyncio
import json
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from .. import crud, schemas, models
from ..crud import notes_collection, embedding_model
import trafilatura
from crawl4ai import AsyncWebCrawler
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

# --- Helper function for async Playwright ---
async def _run_playwright_stealth(url: str):
    """Internal async function to run a headless browser with stealth to scrape a page."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await stealth_async(page)
        await page.goto(url, wait_until="networkidle")
        html_content = await page.content()
        await browser.close()
        return html_content

# --- Async Core Logic for Scraping ---
async def _scrape_and_assimilate_url_async(url: str, db: Session, user_id: int) -> str:
    """Async core logic for scraping a URL, trying crawl4ai first, then playwright."""
    print(f"--- TOOL: Assimilating URL: {url} ---")
    content = None
    page_title = None

    try:
        # --- Attempt 1: Use the powerful crawl4ai for structured data ---
        print("--- Trying crawl4ai... ---")
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            if result and result.markdown:
                content = result.markdown
                page_title = result.metadata.get("title", url)
    except Exception as e:
        print(f"--- crawl4ai failed: {e}. Falling back to Playwright Stealth. ---")
        content = None

    if not content:
        try:
            # --- Attempt 2: Fallback to Playwright Stealth for JS-heavy sites ---
            print("--- Trying Playwright Stealth... ---")
            html_content = await _run_playwright_stealth(url)
            content = trafilatura.extract(html_content)
            if content:
                page_title = trafilatura.extract_metadata(html_content).title or url
        except Exception as e:
            return f"An error occurred with both scrapers: {e}"

    if not content:
        return f"Error: Could not extract main content from {url}."

    # Use the create_note_tool to save it to the database
    result = create_note_tool(title=f"Assimilated: {page_title}", content=content, db=db, user_id=user_id)
    return result

# --- Synchronous Wrapper for AutoGen ---
def scrape_and_assimilate_url(url: str, db: Session, user_id: int) -> str:
    """
    Synchronous wrapper for the async scraping tool. This is the function
    that will be registered with AutoGen.
    """
    return asyncio.run(_scrape_and_assimilate_url_async(url, db, user_id))

# --- New Tool: Google Takeout Processor ---
def process_google_takeout(file_path: str, db: Session, user_id: int) -> str:
    """
    Processes a Google Takeout 'My Activity' HTML file, extracts search queries,
    and adds them to the AI's knowledge base.
    """
    print(f"--- TOOL: Processing Google Takeout file: {file_path} ---")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        # Find all content cells that contain search queries
        content_cells = soup.find_all('div', class_='content-cell')
        search_queries = []
        for cell in content_cells:
            # Google uses a specific structure for search queries
            if cell.text.strip().startswith('Searched for'):
                query_link = cell.find('a')
                if query_link and query_link.text:
                    search_queries.append(query_link.text)

        if not search_queries:
            return "No search queries found in the provided file."

        # Embed and add the queries to the vector store
        embeddings = embedding_model.encode(search_queries).tolist()
        ids = [f"takeout_{user_id}_{i}" for i in range(len(search_queries))]
        metadatas = [{"source": "google_takeout", "owner_id": user_id} for _ in search_queries]

        notes_collection.add(
            embeddings=embeddings,
            documents=search_queries,
            metadatas=metadatas,
            ids=ids
        )

        return f"Successfully processed and assimilated {len(search_queries)} search queries from your Google Takeout file."

    except FileNotFoundError:
        return f"Error: The file was not found at the specified path: {file_path}"
    except Exception as e:
        return f"An error occurred while processing the Takeout file: {e}"


# --- Other Tools (Unchanged) ---

def retrieve_context(query: str, db: Session, user_id: int) -> str:
    """
    This is the primary tool for the ResearchAgent.
    It performs a RAG query against the user's ChromaDB vector store.
    """
    print(f"--- TOOL: Retrieving context for query: '{query}' ---")
    query_embedding = embedding_model.encode(query).tolist()
    results = notes_collection.query(
        query_embeddings=[query_embedding],
        n_results=5,
        where={"owner_id": user_id}
    )
    retrieved_documents = results.get('documents', [[]])[0]
    if not retrieved_documents:
        return "No relevant information found in the knowledge base."
    context_str = "\n---\n".join(retrieved_documents)
    print(f"--- TOOL: Found context: {context_str[:200]}... ---")
    return context_str

def create_note_tool(title: str, content: str, db: Session, user_id: int) -> str:
    """Creates a new note in the user's database."""
    print(f"--- TOOL: Creating note with title: '{title}' ---")
    note_data = schemas.NoteCreate(title=title, content=content)
    crud.create_user_note(db=db, note=note_data, user_id=user_id)
    return f"Successfully created note titled '{title}'."

def create_project_tool(name: str, db: Session, user_id: int) -> str:
    """Creates a new project in the user's database."""
    print(f"--- TOOL: Creating project with name: '{name}' ---")
    project_data = schemas.ProjectCreate(name=name)
    crud.create_user_project(db=db, project=project_data, user_id=user_id)
    return f"Successfully created project named '{name}'."

def create_task_tool(project_name: str, title: str, db: Session, user_id: int) -> str:
    """Creates a new task under a specific project for the user."""
    print(f"--- TOOL: Creating task '{title}' for project '{project_name}' ---")
    projects = crud.get_projects(db=db, user_id=user_id, limit=1000)
    target_project = next((p for p in projects if p.name.lower() == project_name.lower()), None)
    if not target_project:
        return f"Error: Project '{project_name}' not found."
    task_data = schemas.TaskCreate(title=title)
    crud.create_project_task(db=db, task=task_data, project_id=target_project.id)
    return f"Successfully created task '{title}' in project '{project_name}'."

def log_anchor_tool(anchor_name: str, reflection: str, db: Session, user_id: int) -> str:
    """Logs a Micro Anchor practice for the user."""
    print(f"--- TOOL: Logging anchor '{anchor_name}' ---")
    log_data = schemas.MicroAnchorLogCreate(anchor_name=anchor_name, reflection=reflection)
    crud.create_anchor_log(db=db, anchor_log=log_data, user_id=user_id)
    return f"Successfully logged Micro Anchor: '{anchor_name}'."
