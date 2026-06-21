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
# TEST RUN TABLE (CORE - GLOBAL TELEMETRY + AMD TRACK 1 TUNING)
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

    # 🌍 GLOBAL TELEMETRY FIELDS
    # --------------------------------
    trigger_ip = Column(String, nullable=True)
    trigger_city = Column(String, nullable=True)
    trigger_country = Column(String, nullable=True)

    # 🏎️ AMD HACKATHON TRACK 1 ROUTING METRICS
    # --------------------------------
    # Destination node: "LOCAL_CPU", "REMOTE_AMD", or "COMPRESSED_REMOTE"
    routing_destination = Column(String, nullable=False, default="LOCAL_CPU")
    
    # Precise metric tracking for leaderboard evaluation
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    
    # Timing and operational cost boundaries
    execution_latency_ms = Column(Float, nullable=False, default=0.0)
    estimated_cost_saved = Column(Float, nullable=False, default=0.0)
    compression_ratio = Column(Float, nullable=True, default=1.0)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return (f"<TestRun id={self.id} user_id={self.user_id} "
                f"dest={self.routing_destination} savings=${self.estimated_cost_saved:.4f}>")