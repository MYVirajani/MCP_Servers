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
 
