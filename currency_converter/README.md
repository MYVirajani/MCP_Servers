# Currency Converter MCP Server

A currency converter built as an **MCP (Model Context Protocol) server** over
**streamable HTTP**, plus a terminal AI client (LangChain + Gemini) that lets
you ask for conversions in plain English.

```
You ──► client.py ──► Gemini (decides which tool to use)
            │
            └── HTTP ──► server.py ──► open.er-api.com (daily exchange rates)
                         http://localhost:8000/mcp
```

## Features

| Tool | Description |
|---|---|
| `convert_currency(amount, from_currency, to_currency)` | Convert an amount and return the rate, result and last-updated time |
| `get_exchange_rate(from_currency, to_currency)` | Rate for 1 unit of a currency |
| `list_currencies(search)` | List supported currency codes, optionally filtered (e.g. `LK`) |

- About 160 currencies, including LKR, using 3-letter ISO codes (USD, EUR, GBP, LKR...).
- Rates are cached for one hour to avoid unnecessary API calls.
- Invalid codes and network failures return clear error messages instead of crashing.

## Data source

Rates come from the free open endpoint of [ExchangeRate-API](https://www.exchangerate-api.com)
(`open.er-api.com`). No API key is needed.

- Rates update **once per day**, so this is suitable for everyday conversion, not trading.
- The service is rate limited and asks for attribution to exchangerate-api.com.
  Tool responses include a `source` field for this.

## Project structure

```
currency-mcp/
├── server.py          # MCP server (HTTP only)
├── client.py          # Terminal AI client (LangChain + Gemini)
├── requirements.txt
├── .env.example       # Copy to .env and fill in your key
└── .gitignore
```

## Requirements

- Python 3.10+
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/)
- Internet access (for exchange rates and Gemini)

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

Copy `.env.example` to `.env` and fill it in:

```
GOOGLE_API_KEY=your_gemini_key_here
GEMINI_MODEL=your_model_name
```

`GEMINI_MODEL` is optional. Model names change often, so check the current
ones in Google AI Studio.

## Usage

You need **two terminals**, with the virtual environment active in each.

**Terminal 1: start the server**

```powershell
python server.py
```

It prints `Serving on http://127.0.0.1:8000/mcp` and keeps running.

**Terminal 2: start the chat client**

```powershell
python client.py
```

Example session:

```
Connected. Tools: get_exchange_rate, convert_currency, list_currencies
You: convert 50 USD to LKR
  [tool call] convert_currency({'amount': 50, 'from_currency': 'USD', 'to_currency': 'LKR'})
  [tool result] {"converted": ..., "rate": ..., ...}
AI: 50 USD is about ... LKR at today's rate.

You: how many euros is 10000 LKR?
You: which currency codes start with LK?
```

Type `exit` to quit. The `[tool call]` and `[tool result]` lines show MCP
working: Gemini asks for a tool, the client runs it on the server, and the
result goes back to Gemini to write the answer.

## Configuration

| Variable | Where | Default | Purpose |
|---|---|---|---|
| `GOOGLE_API_KEY` | `.env` | none (required) | Gemini API key |
| `GEMINI_MODEL` | `.env` | `gemini-3.6-flash` | Model name |
| `PORT` | server environment | `8000` | Server port |
| `HOST` | server environment | `127.0.0.1` | Server address |
| `MCP_URL` | client environment | `http://localhost:8000/mcp` | Where the client connects |

If you change `PORT`, set `MCP_URL` to match.
