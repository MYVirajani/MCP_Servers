import csv
import json
import os
import re
import sqlite3
import sys
import time
from contextlib import contextmanager
from pathlib import Path

from mcp.server.fastmcp import FastMCP

DATA_DIR = Path(os.getenv("DATA_DIR", Path(__file__).parent / "data")).resolve()
PORT = int(os.getenv("PORT", "8000"))  
MAX_ROWS = 500          
QUERY_SECONDS = 5       
MAX_CSV_MB = 25         
CSV_EXT = {".csv"}
DB_EXT = {".db", ".sqlite", ".sqlite3"}

mcp = FastMCP("data-explorer", host="127.0.0.1", port=PORT)
_csv_cache: dict[Path, tuple[float, sqlite3.Connection]] = {}


# ----------------------------------------------------------------- helpers
def _resolve(file: str) -> Path:
    """Only plain file names inside DATA_DIR are allowed (blocks ../ tricks)."""
    if Path(file).name != file:
        raise ValueError("Give a plain file name from list_files, not a path")
    path = (DATA_DIR / file).resolve()
    if path.parent != DATA_DIR or not path.is_file() or path.suffix.lower() not in CSV_EXT | DB_EXT:
        raise ValueError(f"File '{file}' not found. Use list_files to see what is available.")
    return path


def _clean_names(header: list[str]) -> list[str]:
    names, seen = [], set()
    for i, h in enumerate(header):
        n = re.sub(r"\W+", "_", h.strip()).strip("_").lower() or f"col{i + 1}"
        if n[0].isdigit():
            n = "_" + n
        base, k = n, 2
        while n in seen:
            n, k = f"{base}_{k}", k + 1
        seen.add(n)
        names.append(n)
    return names


def _infer(values: list[str]) -> str:
    vals = [v for v in values if v != ""]
    if not vals:
        return "TEXT"
    for caster, sql_type in ((int, "INTEGER"), (float, "REAL")):
        try:
            for v in vals:
                caster(v)
            return sql_type
        except ValueError:
            continue
    return "TEXT"


def _load_csv(path: Path) -> sqlite3.Connection:
    mtime = path.stat().st_mtime
    hit = _csv_cache.get(path)
    if hit and hit[0] == mtime:
        return hit[1]
    if path.stat().st_size > MAX_CSV_MB * 1024 * 1024:
        raise ValueError(f"CSV is larger than {MAX_CSV_MB} MB")
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header:
            raise ValueError("CSV file is empty")
        rows = [r for r in reader if any(c.strip() for c in r)]
    names = _clean_names(header)
    width = len(names)
    rows = [(r + [""] * width)[:width] for r in rows]
    types = [_infer([r[i].strip() for r in rows]) for i in range(width)]

    def convert(v: str, t: str):
        v = v.strip()
        if v == "":
            return None
        return int(v) if t == "INTEGER" else float(v) if t == "REAL" else v

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    cols = ", ".join(f'"{n}" {t}' for n, t in zip(names, types))
    conn.execute(f"CREATE TABLE data ({cols})")
    conn.executemany(
        f"INSERT INTO data VALUES ({', '.join('?' * width)})",
        [[convert(v, t) for v, t in zip(r, types)] for r in rows],
    )
    conn.commit()
    _csv_cache[path] = (mtime, conn)
    return conn


@contextmanager
def _open(file: str):
    """Yield (connection, kind). SQLite files are opened read-only."""
    path = _resolve(file)
    if path.suffix.lower() in CSV_EXT:
        yield _load_csv(path), "csv"
        return
    conn = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
    try:
        yield conn, "sqlite"
    finally:
        conn.close()


def _tables(conn) -> list[str]:
    q = "SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' ORDER BY name"
    return [r[0] for r in conn.execute(q)]


def _columns(conn, table: str) -> list[tuple[str, str]]:
    return [(r[1], r[2] or "") for r in conn.execute(f'PRAGMA table_info("{table}")')]


def _pick_table(conn, table: str) -> str:
    tables = _tables(conn)
    if not table:
        if len(tables) == 1:
            return tables[0]
        raise ValueError(f"Specify a table. Available: {tables}")
    if table not in tables:
        raise ValueError(f"Unknown table '{table}'. Available: {tables}")
    return table


def _jsonable(v):
    return f"<{len(v)} bytes>" if isinstance(v, (bytes, bytearray)) else v


_ALLOWED = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_RECURSIVE}


def _authorizer(action, *_):
    return sqlite3.SQLITE_OK if action in _ALLOWED else sqlite3.SQLITE_DENY


# ------------------------------------------------------------------- tools
@mcp.tool()
def list_files() -> list[dict]:
    """List the CSV and SQLite files available to explore."""
    files = []
    for p in sorted(DATA_DIR.glob("*")):
        ext = p.suffix.lower()
        if p.is_file() and ext in CSV_EXT | DB_EXT:
            files.append({"name": p.name, "type": "csv" if ext in CSV_EXT else "sqlite",
                          "size_kb": round(p.stat().st_size / 1024, 1)})
    return files


@mcp.tool()
def describe_file(file: str) -> dict:
    """Show the tables, columns, column types and row counts of a file.
    CSV files have a single table named 'data' with cleaned column names."""
    with _open(file) as (conn, kind):
        tables = []
        for t in _tables(conn):
            count = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
            tables.append({"table": t, "rows": count,
                           "columns": [{"name": n, "type": ty} for n, ty in _columns(conn, t)]})
        return {"file": file, "type": kind, "tables": tables}


@mcp.tool()
def preview_table(file: str, table: str = "", limit: int = 5) -> dict:
    """Show the first few rows of a table. For CSV files the table is 'data'
    (leave it empty). For SQLite files with several tables, name the table."""
    limit = max(1, min(limit, 50))
    with _open(file) as (conn, _):
        t = _pick_table(conn, table)
        cur = conn.execute(f'SELECT * FROM "{t}" LIMIT ?', (limit,))
        return {"table": t, "columns": [d[0] for d in cur.description],
                "rows": [[_jsonable(v) for v in r] for r in cur.fetchall()]}


@mcp.tool()
def run_query(file: str, sql: str, limit: int = 100) -> dict:
    """Run a read-only SQL SELECT query (SQLite dialect). CSV files expose one
    table called 'data'. Use describe_file first to get exact column names.
    Results are capped at 500 rows. Any statement that is not a SELECT is rejected."""
    sql = sql.strip().rstrip(";").strip()
    if not re.match(r"(?is)^(select|with)\b", sql):
        raise ValueError("Only SELECT queries are allowed")
    limit = max(1, min(limit, MAX_ROWS))
    with _open(file) as (conn, _):
        deadline = time.time() + QUERY_SECONDS
        conn.set_authorizer(_authorizer)
        conn.set_progress_handler(lambda: 1 if time.time() > deadline else 0, 10000)
        try:
            cur = conn.execute(sql)
            columns = [d[0] for d in cur.description or []]
            rows = cur.fetchmany(limit + 1)
        except (sqlite3.Error, sqlite3.Warning) as e:
            raise ValueError(f"SQL error: {e}") from e
        finally:
            conn.set_authorizer(None)
            conn.set_progress_handler(None, 0)
    truncated = len(rows) > limit
    rows = rows[:limit]
    return {"columns": columns, "rows": [[_jsonable(v) for v in r] for r in rows],
            "row_count": len(rows), "truncated": truncated}


@mcp.tool()
def column_stats(file: str, column: str, table: str = "") -> dict:
    """Summary statistics for one column: count, nulls, distinct values, min, max,
    average (numeric columns) and the 5 most common values."""
    with _open(file) as (conn, _):
        t = _pick_table(conn, table)
        cols = dict(_columns(conn, t))
        if column not in cols:
            raise ValueError(f"Unknown column '{column}'. Columns: {list(cols)}")
        c = f'"{column}"'
        total, nulls, distinct, mn, mx, avg = conn.execute(
            f'SELECT COUNT(*), SUM({c} IS NULL), COUNT(DISTINCT {c}), MIN({c}), MAX({c}), AVG({c}) FROM "{t}"'
        ).fetchone()
        top = conn.execute(
            f'SELECT {c}, COUNT(*) FROM "{t}" WHERE {c} IS NOT NULL GROUP BY {c} ORDER BY 2 DESC, 1 LIMIT 5'
        ).fetchall()
        numeric = cols[column].upper() in {"INTEGER", "REAL", "INT", "FLOAT", "NUMERIC", "DOUBLE"}
        return {"table": t, "column": column, "type": cols[column], "rows": total,
                "nulls": nulls or 0, "distinct": distinct, "min": _jsonable(mn), "max": _jsonable(mx),
                "average": round(avg, 4) if numeric and avg is not None else None,
                "top_values": [{"value": _jsonable(v), "count": n} for v, n in top]}


if __name__ == "__main__":
    if "--http" in sys.argv:
        print(f"Serving on http://127.0.0.1:{PORT}/mcp (data: {DATA_DIR})", file=sys.stderr, flush=True)
        mcp.run(transport="streamable-http")
    else:
        mcp.run()
