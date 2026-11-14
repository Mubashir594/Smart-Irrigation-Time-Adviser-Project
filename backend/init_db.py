import sys
import os
import argparse
import getpass

# Add backend directory to path if run directly
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from database import engine, Base, SessionLocal
from models import User, UserSettings, IrrigationHistory
from auth import hash_password

def init_database():
    """Create all database tables in SQLite and ensure migrations."""
    print("[+] Initializing SQLite database tables...")
    Base.metadata.create_all(bind=engine)
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            cols = [row[1] for row in conn.execute(text("PRAGMA table_info(users)")).fetchall()]
            if "full_name" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR(100) DEFAULT ''"))
                conn.commit()
    except Exception as e:
        print(f"[!] Migration notice: {e}")
    print("[OK] Tables initialized successfully.")

def create_admin_user(username: str = None, password: str = None):
    """
    Safely create or update an administrator account.
    """
    init_database()
    db = SessionLocal()
    try:
        if not username:
            default_user = "aura_admin_01"
            input_user = input(f"Enter Administrator Auth ID [{default_user}]: ").strip()
            username = input_user if input_user else default_user

        if not password:
            while True:
                pwd1 = getpass.getpass("Enter Administrator Password: ")
                if not pwd1 or len(pwd1) < 4:
                    print("[-] Password must be at least 4 characters.")
                    continue
                pwd2 = getpass.getpass("Confirm Administrator Password: ")
                if pwd1 != pwd2:
                    print("[-] Passwords do not match. Try again.")
                    continue
                password = pwd1
                break

        # Check if user already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"[*] User '{username}' already exists. Updating password...")
            existing_user.password_hash = hash_password(password)
            db.commit()
            print(f"[OK] Password for '{username}' updated successfully.")
            return

        # Create new user
        hashed = hash_password(password)
        new_user = User(full_name="System Administrator", username=username, password_hash=hashed)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Initialize default settings
        default_settings = UserSettings(
            user_id=new_user.id,
            sensor_frequency="Standard (15m)",
            autonomous_mode=True
        )
        db.add(default_settings)
        db.commit()

        print(f"[OK] Administrator account '{username}' created successfully with secure bcrypt hash.")

    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AURA OS Database Initialization & Admin Setup")
    parser.add_argument("--username", "-u", type=str, help="Administrator Auth ID")
    parser.add_argument("--password", "-p", type=str, help="Administrator Password")
    args = parser.parse_args()

    create_admin_user(args.username, args.password)
