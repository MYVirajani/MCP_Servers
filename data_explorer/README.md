# CSV / SQLite Explorer MCP Server

A **read-only** MCP server that lets an AI explore CSV and SQLite files: see
what files exist, inspect their structure, preview rows, run `SELECT` queries
and get column statistics. Includes a terminal chat client (LangChain + Gemini).

## Tools

| Tool | Description |
|---|---|
| `list_files()` | CSV and SQLite files available in `data/` |
| `describe_file(file)` | Tables, columns, types and row counts |
| `preview_table(file, table, limit)` | First rows of a table |
| `run_query(file, sql, limit)` | Read-only SQL `SELECT` (max 500 rows) |
| `column_stats(file, column, table)` | Count, nulls, distinct, min, max, average, top values |

CSV files are loaded into an in-memory SQLite table called `data`, with column
names cleaned to lowercase (`Unit Price` becomes `unit_price`) and numeric
types detected automatically. The same SQL works for CSV and SQLite files.

## Included sample data

- `data/sales.csv`: 60 orders (region, product, quantity, unit price, customer)
- `data/school.db`: SQLite with `students`, `courses` and `enrollments`

Add your own files to the `data/` folder (or set `DATA_DIR`).

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your Gemini key:

```
GOOGLE_API_KEY=your_gemini_key_here
GEMINI_MODEL=your_model_name
```

## Run

**stdio (simplest):** the client launches the server itself.

```powershell
python client.py
```

**HTTP:** start the server yourself, then the client in a second terminal.

```powershell
# Terminal 1
python server.py --http

# Terminal 2
$env:MCP_MODE="http"
python client.py
```

## Example questions

```
what files do I have?
which region has the highest total revenue in sales.csv?
show the top 3 products by quantity sold
how many orders have no customer name?
which students are enrolled in Machine Learning, and what are their grades?
what is the average GPA by year in school.db?
```


## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `DATA_DIR` | `./data` | Folder the server may read |
| `PORT` | `8000` | HTTP mode port |
| `MCP_MODE` | `stdio` | Client mode: `stdio` or `http` |
| `MCP_URL` | `http://localhost:8000/mcp` | Client URL in HTTP mode |
| `GOOGLE_API_KEY` | none | Gemini key |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Model name |


