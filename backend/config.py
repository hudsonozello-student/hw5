"""Settings shared by the whole team: paths, the one model, and the token budget."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")  # keep the console to our own output

HW5_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = HW5_DIR / "backend" / "prompts"
MCP_SERVER_SCRIPT = HW5_DIR / "mcp_server" / "server.py"
ORIGINAL_DB = HW5_DIR / "data" / "campus_customs.db"
# Tests set these two to scratch files; normal runs use the working copy and output/audit_trail.json.
WORKING_DB = Path(os.environ.get("CAMPUS_CUSTOMS_DB", HW5_DIR / "data" / "campus_customs_new.db"))
AUDIT_TRAIL = Path(os.environ.get("CAMPUS_CUSTOMS_AUDIT", HW5_DIR / "output" / "audit_trail.json"))

# The one and only model for every agent, reached through Portkey.
MODEL_NAME = "gpt-6-luna"
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"

# Token and loop limits. Usage is shared across every agent working one ticket,
# so these caps are a per-ticket budget, not a per-agent one.
MAX_OUTPUT_TOKENS = 3000          # per model response (sent as max_completion_tokens)
TICKET_REQUEST_LIMIT = 30         # model calls per ticket, all agents combined
TICKET_TOOL_CALL_LIMIT = 40       # tool calls per ticket, all agents combined
TICKET_TOKEN_LIMIT = 150_000      # input + output tokens per ticket, all agents combined
MAX_DELEGATION_DEPTH = 2          # boss -> specialist -> specialist, no deeper
MAX_DELEGATIONS_PER_TICKET = 6    # hand-offs per ticket, all agents combined
AUDIT_TEXT_LIMIT = 4000           # characters kept per text field in the audit trail


def portkey_api_key() -> str:
    """Load PORTKEY_API_KEY from the nearest .env above this folder (never printed or logged)."""
    for folder in [HW5_DIR, *HW5_DIR.parents]:
        if (folder / ".env").exists():
            load_dotenv(folder / ".env", override=False)
            break
    key = os.environ.get("PORTKEY_API_KEY")
    if not key:
        raise RuntimeError("PORTKEY_API_KEY is not set. Add it to the project-root .env file.")
    return key


def mcp_server_command() -> tuple[str, list[str]]:
    """The command that starts the campus-customs MCP server over stdio with this venv's Python."""
    return sys.executable, [str(MCP_SERVER_SCRIPT)]
