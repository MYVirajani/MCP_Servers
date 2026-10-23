"""A simple notes MCP server that remembers notes between calls.

State is saved in notes.json because the client may start a fresh server
process for each tool call, so memory held in variables would be lost.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("notes")
FILE = Path(__file__).parent / "notes.json"


def _load() -> list[dict]:
    return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else []


def _save(notes: list[dict]) -> None:
    FILE.write_text(json.dumps(notes, indent=2), encoding="utf-8")


@mcp.tool()
def add_note(text: str) -> str:
    """Save a new note and return its id."""
    notes = _load()
    note_id = max((n["id"] for n in notes), default=0) + 1
    notes.append({"id": note_id, "text": text, "created": datetime.now().isoformat(timespec="seconds")})
    _save(notes)
    return f"Saved note #{note_id}"


@mcp.tool()
def list_notes() -> list[dict]:
    """List all saved notes."""
    return _load()


@mcp.tool()
def search_notes(keyword: str) -> list[dict]:
    """Find notes containing a keyword (case-insensitive)."""
    return [n for n in _load() if keyword.lower() in n["text"].lower()]


@mcp.tool()
def delete_note(note_id: int) -> str:
    """Delete a note by its id."""
    notes = _load()
    kept = [n for n in notes if n["id"] != note_id]
    if len(kept) == len(notes):
        raise ValueError(f"No note with id {note_id}")
    _save(kept)
    return f"Deleted note #{note_id}"


if __name__ == "__main__":
    mcp.run()
