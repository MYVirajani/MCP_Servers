# MCP Calculator & Notes: Terminal AI Client
 
A small project for learning how the **Model Context Protocol (MCP)** works.
Two MCP servers expose tools, and a terminal chat client connects Gemini to
them so the AI can call those tools to answer your questions.
 
```
You ──► client.py ──► Gemini (decides which tool to use)
            │
            ├── stdio ──► calculator_server.py  (add, subtract, ...)
            └── stdio ──► notes_server.py       (add_note, search_notes, ...)
```
## Features
 
**Calculator server** (`calculator_server.py`)
 
| Type | Name | Description |
|---|---|---|
| Tool | `add`, `subtract`, `multiply`, `divide` | Basic arithmetic (divide by zero returns a clean error) |
| Tool | `power`, `square_root` | Exponents and square roots |
| Resource | `calculator://help` | Help text |
| Prompt | `explain_calculation` | Solve an expression step by step |
 
**Notes server** (`notes_server.py`)
 
| Tool | Description |
|---|---|
| `add_note` | Save a note |
| `list_notes` | List all notes |
| `search_notes` | Find notes by keyword |
| `delete_note` | Delete a note by id |
 
Notes are saved to `notes.json`, because the client may start a fresh server
process for each tool call, so in-memory variables would be lost.

## Project structure
 
```
calculator_server/
├── calculator_server.py   # MCP server: math tools
├── notes_server.py        # MCP server: notes with file storage
├── client.py              # Terminal AI chat client (LangChain + Gemini)
├── test_client.py         # Plain MCP client, no AI, for testing the server
├── requirements.txt
├── .env                   # Your API key (never commit this)
└── .gitignore
```
 
## Requirements
 
- Python 3.10+
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/)
