import os
from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database.db")

# Enable WAL mode for better concurrency in SQLite
connect_args = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

def enable_wal():
    with engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA journal_mode=WAL")
        conn.exec_driver_sql("PRAGMA synchronous=NORMAL")

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    enable_wal()
