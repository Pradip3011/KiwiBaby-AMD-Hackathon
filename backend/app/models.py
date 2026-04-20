from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from datetime import datetime
from .database import Base


# -------------------------
# USER TABLE (STRICT NO-TOUCH)
# -------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # 🔥 Use email instead of username
    email = Column(String, unique=True, nullable=False, index=True)

    # 🔥 Store hashed password (NOT plain text)
    hashed_password = Column(String, nullable=False)

    # 🔥 Track creation
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"


# -------------------------
# TEST RUN TABLE (CORE - GLOBAL TELEMETRY UPDATED)
# -------------------------
class TestRun(Base):
    __tablename__ = "test_runs"

    id = Column(Integer, primary_key=True, index=True)

    # Who triggered it
    user_id = Column(Integer, nullable=False)

    # Input
    requirement = Column(Text, nullable=False)

    # Output (JSON / Gherkin / Text)
    output = Column(Text, nullable=False)

    # Format tracking
    format = Column(String, nullable=False)

    # Coverage tracking
    coverage_percent = Column(Float, nullable=True)

    # 🌍 GLOBAL TELEMETRY FIELDS (NEW)
    # --------------------------------
    trigger_ip = Column(String, nullable=True)
    trigger_city = Column(String, nullable=True)
    trigger_country = Column(String, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<TestRun id={self.id} user_id={self.user_id} format={self.format}>"