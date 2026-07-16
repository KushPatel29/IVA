"""
Execute a validated read-only query against the warehouse and return a small,
display-ready result. Rows are capped so a broad query can't dump a whole fact
table into a chat window; the cap being hit is reported, not hidden.
"""

from dataclasses import dataclass, field

from engine.sql_guard import validate_sql

MAX_ROWS = 200


@dataclass
class QueryResult:
    sql: str
    columns: list = field(default_factory=list)
    rows: list = field(default_factory=list)   # list of tuples
    row_count: int = 0
    truncated: bool = False
    error: str = ""

    @property
    def ok(self):
        return not self.error


def run_query(con, sql: str, max_rows: int = MAX_ROWS) -> QueryResult:
    ok, reason = validate_sql(sql)
    if not ok:
        return QueryResult(sql=sql, error=f"blocked by SQL guard: {reason}")
    try:
        cur = con.execute(sql)
        columns = [d[0] for d in cur.description]
        rows = cur.fetchmany(max_rows + 1)
    except Exception as e:  # surface DuckDB errors (bad column, etc.) to the caller
        return QueryResult(sql=sql, error=str(e).strip().splitlines()[0])
    truncated = len(rows) > max_rows
    rows = rows[:max_rows]
    return QueryResult(sql=sql, columns=columns, rows=rows,
                       row_count=len(rows), truncated=truncated)
