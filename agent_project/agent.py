import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

from tools import ALL_TOOLS, TOOL_DICT
from memory import get_history, save_message

# Load API key and model from .env file
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

client = genai.Client(api_key=API_KEY)

SYSTEM_RULES = """

# 1. ROLE & IDENTITY
You are an autonomous Forward Deployed Engineer (FDE) Agent operating within a sandboxed developer workspace.

# 2. OBJECTIVES & TOOL USAGE
- Use available deterministic tools to fulfill user requests accurately:
  * Arithmetic/Math: Always delegate calculations to `calculate`.
  * Workspace Files: Use `create_directory`, `write_file`, `read_file`, and `list_files`.
- Carefully inspect tool execution results before producing your final answer.

# 3. BEHAVIOR & COMMUNICATION STYLE
- Be direct, concise, and technically precise. Omit conversational filler and generic preambles.
- When an operation completes, summarize the outcome in 1–2 plain sentences.
- When saving code or files, state the exact relative path where the asset was created.

# 4. STRICT CONSTRAINTS & GUARDRAILS
- NEVER approximate or mentally calculate numbers; always call the `calculate` tool.
- NEVER attempt to read, write, or traverse paths outside the designated sandbox root.
- If a tool fails or raises an error, communicate the issue plainly—never fabricate a successful result.
- Restrict actions solely to the provided tools and workspace boundaries.
"""


async def stream_agent(session_id: str, user_input: str):
    """Streams Gemini's response and executes tools as requested."""

    # 1. Save incoming user message
    save_message(session_id, "user", user_input)

    # 2. Build message list from history
    contents = []
    for msg in get_history(session_id):
        contents.append(
            types.Content(
                role=msg["role"],
                parts=[types.Part.from_text(text=msg["text"])]
            )
        )

    # 3. Configure Gemini with tools and rules
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_RULES,
        tools=ALL_TOOLS,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
    )

    # 4. Stream response from Gemini
    stream = await client.aio.models.generate_content_stream(
        model=MODEL_NAME,
        contents=contents,
        config=config
    )

    full_reply = ""
    tool_calls = []

    async for chunk in stream:
        if chunk.text:
            full_reply += chunk.text
            yield f"data: {json.dumps({'type': 'token', 'content': chunk.text})}\n\n"

        if chunk.function_calls:
            for call in chunk.function_calls:
                tool_calls.append(call)

    # 5. If Gemini asked to call a tool, run it
    if tool_calls:
        # Save model's tool intent
        call_parts = [types.Part.from_function_call(name=c.name, args=c.args or {}) for c in tool_calls]
        contents.append(types.Content(role="user", parts=call_parts))

        response_parts = []
        for call in tool_calls:
            tool_name = call.name
            tool_args = call.args or {}

            # Notify the browser UI about the running tool
            yield f"data: {json.dumps({'type': 'status', 'content': f'Running {tool_name}...'})}\n\n"

            # Execute the tool
            func = TOOL_DICT.get(tool_name)
            output = func(**tool_args) if func else f"Tool '{tool_name}' not found."

            response_parts.append(
                types.Part.from_function_response(
                    name=tool_name,
                    response={"result": str(output)}
                )
            )

        contents.append(types.Content(role="user", parts=response_parts))

        # 6. Stream the final summary of the action
        second_stream = await client.aio.models.generate_content_stream(
            model=MODEL_NAME,
            contents=contents,
            config=config
        )

        async for chunk in second_stream:
            if chunk.text:
                full_reply += chunk.text
                yield f"data: {json.dumps({'type': 'token', 'content': chunk.text})}\n\n"

    # 7. Save bot's reply in memory
    if full_reply:
        save_message(session_id, "model", full_reply)

    yield f"data: {json.dumps({'type': 'done'})}\n\n"