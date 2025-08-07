# File: core/app/database.py
# --- Purpose: Sets up the database connection and session management. ---

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Optional
# --- Ensure the data directory exists before creating the database file ---
# Define the path for the data directory
# This navigates up one level from the current file's directory (app) to 'core', then into 'data'
data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
# Create the directory if it doesn't exist
os.makedirs(data_dir, exist_ok=True)

# Define the local SQLite database URL. The database file will be created in core/app/data/
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(data_dir, 'kairos.db')}"

# Create the SQLAlchemy engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create a SessionLocal class. Each instance will be a database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class. Our ORM models will inherit from this.
Base = declarative_base()

# --- Dependency to get a DB session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
