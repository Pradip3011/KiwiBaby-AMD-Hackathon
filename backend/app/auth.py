import uuid
from datetime import datetime, timedelta

fake_sessions = {}

SESSION_TIMEOUT = timedelta(hours=2)


def create_session(username: str):
    token = str(uuid.uuid4())
    fake_sessions[token] = {
        "username": username,
        "created_at": datetime.utcnow()
    }
    return token


def get_user(token: str):
    session = fake_sessions.get(token)
    if not session:
        return None

    if datetime.utcnow() - session["created_at"] > SESSION_TIMEOUT:
        del fake_sessions[token]
        return None

    return session["username"]
