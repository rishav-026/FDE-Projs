from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent import stream_agent

app = FastAPI()

# Serve static frontend files
STATIC_DIR = Path("static").resolve()
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ChatInput(BaseModel):
    session_id: str
    message: str


@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/chat")
async def chat_endpoint(data: ChatInput):
    """Streams word-by-word tokens over Server-Sent Events (SSE)."""
    return StreamingResponse(
        stream_agent(data.session_id, data.message),
        media_type="text/event-stream"
    )