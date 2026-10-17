import os
from tempfile import gettempdir
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE_PATH = Path(gettempdir()) / "trustvision.db" if os.getenv("VERCEL") else ROOT_DIR / "trustvision.db"
DATABASE_PATH = Path(os.getenv("TRUSTVISION_DB_PATH", DEFAULT_DATABASE_PATH)).resolve()
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_PATH.as_posix()}")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
if DATABASE_URL.startswith("sqlite"):
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
