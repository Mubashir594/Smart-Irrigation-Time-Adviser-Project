import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Add current directory to path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from database import engine, Base
from routes import authentication, irrigation, users

# Resolve project paths
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
if not os.path.exists(FRONTEND_DIR):
    FRONTEND_DIR = PROJECT_ROOT

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Automatic database table initialization upon backend startup.
    Ensures aura.db and all required tables exist before handling requests,
    with safe automatic column migrations.
    """
    print("[*] Starting AURA OS Backend...")
    Base.metadata.create_all(bind=engine)

    # Safe migration: verify full_name column exists in users table
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(users)"))
            cols = [row[1] for row in result.fetchall()]
            if "full_name" not in cols:
                print("[*] Migrating schema: adding 'full_name' column to users table...")
                conn.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR(100) DEFAULT ''"))
                conn.commit()
    except Exception as e:
        print(f"[!] Schema check notice: {e}")

    print("[OK] SQLite database verified and tables ready.")
    yield
    print("[*] Shutting down AURA OS Backend.")

app = FastAPI(
    title="AURA — Smart Irrigation Time Adviser API",
    description="Final-Year BCA Project backend providing authentication, calculation storage, and node configuration.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS so local execution and any local origins work without friction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(authentication.router)
app.include_router(irrigation.router)
app.include_router(users.router)

# Serve Frontend HTML Pages
@app.get("/", response_class=FileResponse, tags=["Frontend Pages"])
def serve_index():
    """Serves the Aura OS Terminal Login interface."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if not os.path.exists(index_path):
        index_path = os.path.join(PROJECT_ROOT, "index.html")
    return FileResponse(index_path)

@app.get("/index.html", response_class=FileResponse, tags=["Frontend Pages"])
def serve_index_alias():
    """Alias for index.html."""
    return serve_index()

@app.get("/dash.html", response_class=FileResponse, tags=["Frontend Pages"])
def serve_dashboard():
    """Serves the AURA Smart Irrigation Dashboard."""
    dash_path = os.path.join(FRONTEND_DIR, "dash.html")
    if not os.path.exists(dash_path):
        dash_path = os.path.join(PROJECT_ROOT, "dash.html")
    return FileResponse(dash_path)

# Root health check endpoint
@app.get("/api/health", tags=["System"])
def health_check():
    """Simple health check endpoint to verify backend status."""
    return {
        "system": "AURA OS Core",
        "status": "operational",
        "version": "1.0.0"
    }
