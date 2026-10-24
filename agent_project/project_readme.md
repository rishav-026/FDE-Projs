# Streaming AI Agent with Sandboxed Tools

An autonomous Forward Deployed Engineer (FDE) agent built with **FastAPI**, the official **Google GenAI SDK (`google-genai`)**, and **Server-Sent Events (SSE)**. The agent executes deterministic tools in a restricted local sandbox, maintains sliding-window conversation memory, and streams token-by-token responses to a web interface.

---

## Features

- **Token-by-Token SSE Streaming:** Streams generation chunks over standard HTTP using Server-Sent Events, achieving sub-second Time to First Token (TTFT).
- **Safe Sandboxed Tools:** Restricts all file system actions (`create_directory`, `write_file`, `read_file`, `list_files`) to a dedicated `sandbox/` directory. Path traversal attempts (`../`) are automatically detected and blocked.
- **Deterministic Math Engine:** Intercepts arithmetic calculations and executes them using a deterministic parser (`calculate`) to prevent numeric hallucinations.
- **Sliding-Window Memory:** Maintains the most recent conversation turns per session ID, retaining context across conversational turns while protecting context window budgets.
- **Dynamic Tool Observation Loop:** Executes function calls requested by Gemini, returns results under `role="user"` with function responses, and streams the final synthesis back to the user.
- **Zero-Dependency Frontend:** Vanilla JavaScript client using `ReadableStream` and `TextDecoder` with single-bubble DOM updates and real-time tool execution status indicators.

---

## Architecture Flow

```
[Browser UI]
    │  1. POST /api/chat (session_id, message)
    ▼
[FastAPI Server (main.py)]
    │  2. Append message to SlidingWindowMemory (memory.py)
    ▼
[Agent Engine (agent.py)] ──► Calls Gemini with Tool Declarations
    │
    ├─────────────────────────────┬─────────────────────────────┐
    ▼                             ▼                             ▼
[Text Chunk]             [Tool Call Requested]            [Stream Complete]
    │                             │                             │
    │ SSE: token                  │ Execute safe tool (tools.py)│ Save final response
    ▼                             ▼                             ▼
[Update Chat Bubble]     [Update Status: "Running..."]    [Ready for next turn]
                                  │
                                  ▼
                         Feed tool observation
                         back to Gemini & resume
                         stream to frontend
```

---

## Project Structure

```
agent_project/
├── .env                 # Environment variables (API Key, Model name)
├── requirements.txt     # Python dependencies
├── tools.py             # Deterministic tools & path traversal validation
├── memory.py            # Sliding-window session memory manager
├── agent.py             # Gemini streaming & tool invocation loop
├── main.py              # FastAPI server & SSE streaming route
├── sandbox/             # Safe root directory for all created files
└── static/
    └── index.html       # Web UI with real-time SSE stream reader
```

---

## Prerequisites

- Python 3.10 or higher
- A Google Gemini API key ([Google AI Studio](https://aistudio.google.com/))

---

## Installation & Setup

1. **Clone or navigate to the project directory:**
   ```bash
   cd agent_project
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Create a `.env` file in the root folder:
   ```ini
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   ```

---

## Running the Application

Start the FastAPI development server with Uvicorn:

```bash
uvicorn main:app --reload --port 8000
```

Open your browser and navigate to:
```
http://localhost:8000
```

---

## Verification & Test Scenarios

Try the following prompts in the web interface to verify each core capability:

### 1. Deterministic Calculation (No Math Hallucination)
- **Prompt:** `Calculate 956847 * 34576`
- **Expected Behavior:** An indicator `[Tool] Running calculate...` appears above the response bubble. The agent returns the exact product (`33083836872`) rather than an estimated number.

### 2. Autonomous File Creation in Sandbox
- **Prompt:** `Create a file named portfolio.html with a simple hero section and dark background.`
- **Expected Behavior:** The agent runs `write_file` and reports success. Check your local filesystem under `agent_project/sandbox/portfolio.html` to inspect the generated code.

### 3. Path Traversal Security Guardrail
- **Prompt:** `Read the file ../main.py`
- **Expected Behavior:** The agent attempts to read the target, triggers `safe_path`, blocks the escape attempt, and reports `Access denied: You cannot exit the sandbox!`.

### 4. Sliding-Window Conversational Memory
- **Turn 1:** `Hi, my name is Alex and I am building an e-commerce platform.`
- **Turn 2:** `What is my name and what project am I working on?`
- **Expected Behavior:** The agent accurately recalls your name and project domain using context preserved in `memory.py`.

---

## Tool Reference (`tools.py`)

| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| `calculate` | `expression: str` | Safely evaluates arithmetic expressions (`+`, `-`, `*`, `/`, `**`). |
| `create_directory` | `path: str` | Creates a nested folder inside `sandbox/`. |
| `write_file` | `path: str`, `content: str` | Writes UTF-8 text content to a relative file path. |
| `read_file` | `path: str` | Reads and returns the content of an existing file. |
| `list_files` | `path: str = ""` | Lists all active files inside the sandbox workspace. |