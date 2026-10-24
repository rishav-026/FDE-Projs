import os
import json
from pathlib import Path

# Safe workspace folder
SANDBOX = Path("sandbox").resolve()
SANDBOX.mkdir(exist_ok=True)


def safe_path(path_str: str) -> Path:
    """Ensures paths stay strictly inside the sandbox folder."""
    target = (SANDBOX / path_str.strip("/\\")).resolve()
    if not target.is_relative_to(SANDBOX):
        raise PermissionError("Access denied: You cannot exit the sandbox!")
    return target


def create_directory(path: str) -> str:
    """Create a new folder inside the workspace."""
    target = safe_path(path)
    target.mkdir(parents=True, exist_ok=True)
    return f"Created folder: {path}"


def write_file(path: str, content: str) -> str:
    """Write text content to a file in the workspace."""
    target = safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Saved file: {path}"


def read_file(path: str) -> str:
    """Read an existing file from the workspace."""
    target = safe_path(path)
    if not target.exists():
        return f"File '{path}' does not exist."
    with open(target, "r", encoding="utf-8") as f:
        return f.read()


def list_files(path: str = "") -> str:
    """List all files in the workspace."""
    target = safe_path(path)
    files = [str(p.relative_to(SANDBOX)) for p in target.glob("**/*") if p.is_file()]
    return json.dumps(files if files else ["Workspace is empty."])


def calculate(expression: str) -> str:
    """Safely calculate basic arithmetic expressions (e.g. 500 * 25)."""
    allowed_chars = set("0123456789+-*/.() ")
    if not set(expression).issubset(allowed_chars):
        return "Error: Invalid characters in calculation."
    try:
        # Evaluates only mathematical expressions
        result = eval(expression, {"__builtins__": None}, {})
        return str(result)
    except Exception as e:
        return f"Calculation error: {e}"


# List of tools provided to Gemini
ALL_TOOLS = [create_directory, write_file, read_file, list_files, calculate]
TOOL_DICT = {fn.__name__: fn for fn in ALL_TOOLS}