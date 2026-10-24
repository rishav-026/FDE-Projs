# In-memory dictionary: session_id -> list of messages
sessions = {}

MAX_MESSAGES = 8  # Keeps the last 8 messages (4 user questions + 4 bot answers)


def get_history(session_id: str):
    """Retrieve chat history for a session."""
    return sessions.get(session_id, [])


def save_message(session_id: str, role: str, text: str):
    """Save a user or bot message and trim old ones."""
    if session_id not in sessions:
        sessions[session_id] = []

    sessions[session_id].append({"role": role, "text": text})

    # Keep only the most recent messages (sliding window)
    if len(sessions[session_id]) > MAX_MESSAGES:
        sessions[session_id] = sessions[session_id][-MAX_MESSAGES:]