import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Path to the SQLite database file
# Automatically resolve to the 'database' folder at project root
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
DB_DIR = os.path.join(PROJECT_ROOT, "database")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "aura.db")

DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create SQLAlchemy engine for SQLite
# check_same_thread is set to False for SQLite multithreaded access in FastAPI
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Session local factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base model
Base = declarative_base()

def get_db():
    """
    FastAPI dependency that provides a database session per request
    and safely closes it after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

