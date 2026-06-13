# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import declarative_base, sessionmaker

# SQLite Database URL
# This will create 'lms.db' in the root directory.
SQLALCHEMY_DATABASE_URL = "sqlite:///./lms.db"

# Create the SQLAlchemy engine.
# connect_args={"check_same_thread": False} is required for SQLite when used with multithreaded frameworks like FastAPI.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create a sessionmaker to generate database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base class for models
Base = declarative_base()

# Session generator to handle database connections per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
