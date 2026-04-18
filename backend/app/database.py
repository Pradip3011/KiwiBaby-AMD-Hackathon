import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# Load the variables from your .env file
load_dotenv()

# Pull the Neon Postgres URL securely
DATABASE_URL = os.getenv("DATABASE_URL")

# 🔥 FIX: Added pool_pre_ping to handle Neon's serverless connection drops
# Also added pool_recycle to refresh connections every hour
engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True,
    pool_recycle=3600
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()