import os
import time

import httpx
from mcp.server.fastmcp import FastMCP

HOST = os.getenv("HOST", "127.0.0.1")  
PORT = int(os.getenv("PORT", "8000"))

mcp = FastMCP("currency", host=HOST, port=PORT)

API = "https://open.er-api.com/v6/latest/{base}"
CACHE_SECONDS = 3600
_cache: dict[str, tuple[float, dict]] = {}  # base -> (fetched_at, api_response)


def _fetch_rates(base: str) -> dict:
    """Get rates for a base currency, cached for an hour (rates change daily)."""
    base = base.upper().strip()
    hit = _cache.get(base)
    if hit and time.time() - hit[0] < CACHE_SECONDS:
        return hit[1]
    try:
        r = httpx.get(API.format(base=base), timeout=10)
        r.raise_for_status()
        data = r.json()
    except httpx.HTTPError as e:
        raise ValueError(f"Could not fetch exchange rates: {e}") from e
    if data.get("result") != "success":
        raise ValueError(f"Unknown or unsupported currency code '{base}'")
    _cache[base] = (time.time(), data)
    return data


def _rate(from_currency: str, to_currency: str) -> tuple[float, dict]:
    data = _fetch_rates(from_currency)
    to = to_currency.upper().strip()
    if to not in data["rates"]:
        raise ValueError(f"Unknown currency code '{to_currency}'. Use list_currencies to search.")
    return data["rates"][to], data


@mcp.tool()
def get_exchange_rate(from_currency: str, to_currency: str) -> dict:
    """Get the exchange rate for 1 unit of from_currency in to_currency.
    Use 3-letter ISO codes such as USD, EUR, LKR, GBP."""
    rate, data = _rate(from_currency, to_currency)
    return {
        "from": from_currency.upper(),
        "to": to_currency.upper(),
        "rate": rate,
        "last_updated": data.get("time_last_update_utc"),
        "source": "exchangerate-api.com",
    }


@mcp.tool()
def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """Convert an amount from one currency to another using the latest daily rate.
    Use 3-letter ISO codes such as USD, EUR, LKR, GBP."""
    if amount < 0:
        raise ValueError("Amount must not be negative")
    rate, data = _rate(from_currency, to_currency)
    return {
        "amount": amount,
        "from": from_currency.upper(),
        "to": to_currency.upper(),
        "rate": rate,
        "converted": round(amount * rate, 2),
        "last_updated": data.get("time_last_update_utc"),
        "source": "exchangerate-api.com",
    }


@mcp.tool()
def list_currencies(search: str = "") -> list[str]:
    """List supported currency codes. Optionally filter by text, e.g. 'LK' or 'EU'."""
    codes = sorted(_fetch_rates("USD")["rates"])
    s = search.upper().strip()
    return [c for c in codes if s in c] if s else codes


if __name__ == "__main__":
    print(f"Serving on http://{HOST}:{PORT}/mcp", flush=True)
    mcp.run(transport="streamable-http")
