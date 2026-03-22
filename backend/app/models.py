from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from datetime import datetime
from .database import Base


# -------------------------
# USER TABLE
# -------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)

    def __repr__(self):
        return f"<User id={self.id} username={self.username}>"


# -------------------------
# TEST RUN TABLE (CORE)
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

    # 🔥 NEW: format tracking
    format = Column(String, nullable=False)

    # 🔥 OPTIONAL: coverage tracking (useful for analytics/demo)
    coverage_percent = Column(Float, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<TestRun id={self.id} user_id={self.user_id} format={self.format}>"
