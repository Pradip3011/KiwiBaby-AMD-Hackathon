from app.database import engine, Base
from app.models import TestRun

print("Dropping old test_runs table...")
TestRun.__table__.drop(engine, checkfirst=True)

print("Recreating updated test_runs table with Track 1 metrics...")
Base.metadata.create_all(bind=engine)

print("Database Schema successfully upgraded!")