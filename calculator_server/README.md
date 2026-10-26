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

## Setup
 
```powershell
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1        # macOS/Linux: source .venv/bin/activate
 
# 2. Install dependencies
pip install -r requirements.txt
```

If PowerShell blocks the activate script, run this once:
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`
 
Create a `.env` file next to `client.py`:
 
```
GOOGLE_API_KEY=your_gemini_key_here
GEMINI_MODEL=your_model_name
```
 
`GEMINI_MODEL` is optional. Model names change often, so check the current
ones in Google AI Studio.
 
### requirements.txt
 
```
mcp>=1.2.0,<2
langchain>=1.0
langchain-mcp-adapters
langchain-google-genai
python-dotenv
```

## Usage
 
### 1. Test the server without AI (uses no API quota)
 
```powershell
python test_client.py
```
 
This lists the tools and calls a few of them directly.
 
### 2. Chat with the AI
 
```powershell
python client.py
```
 
`client.py` launches both servers itself over stdio, so you don't need
separate terminals. Example session:
 
```
Connected. Tools: add, subtract, multiply, divide, power, square_root, add_note, ...
You: what is 15% of 2480, then its square root?
  [tool call] multiply({'b': 2480, 'a': 0.15})
  [tool result] 372.0
  [tool call] square_root({'x': 372})
  [tool result] 19.28730152198591
AI: 15% of 2,480 is **372**.

The square root of 372 is approximately **19.29** (or `19.28730152198591`).
 
You: save a note: buy milk tomorrow
You: what notes do I have about milk?
```
 
Type `exit` to quit.
