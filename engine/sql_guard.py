"""
Read-only guard for model-generated SQL.

The language model writes the SQL, so it is never trusted. Before anything runs,
`validate_sql` proves the statement is a single read-only query: it must be one
statement, start with SELECT or WITH, and contain no data- or schema-modifying
keyword. Comments and string/identifier literals are stripped first so a value
like WHERE note = 'please DROP TABLE' can't trip the check.

This is the safety boundary the whole assistant leans on, which is why it has its
own exhaustive test suite and runs before the executor ever sees the SQL.
"""

import re

# Anything that writes data, changes schema, touches the filesystem, or loads an
# extension. DuckDB-specific verbs (ATTACH, COPY, INSTALL, LOAD, PRAGMA, EXPORT)
# are included alongside the standard DML/DDL set.
FORBIDDEN = [
    "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE",
    "REPLACE", "MERGE", "UPSERT", "ATTACH", "DETACH", "COPY", "INSTALL",
    "LOAD", "PRAGMA", "CALL", "SET", "RESET", "EXPORT", "IMPORT", "GRANT",
    "REVOKE", "VACUUM", "ANALYZE", "CHECKPOINT",
]


def _strip_literals(sql: str) -> str:
    """Remove comments and string/identifier literals so keyword scanning only
    sees actual SQL syntax, never data values or column names."""
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)   # block comments
    sql = re.sub(r"--[^\n]*", " ", sql)                 # line comments
    sql = re.sub(r"'(?:''|[^'])*'", " '' ", sql)         # single-quoted strings
    sql = re.sub(r'"(?:""|[^"])*"', ' "" ', sql)         # quoted identifiers
    return sql


def validate_sql(sql: str):
    """Return (ok: bool, reason: str). ok=True means the SQL is a single
    read-only statement that is safe to execute."""
    if not sql or not sql.strip():
        return False, "empty query"

    cleaned = _strip_literals(sql).strip().rstrip(";").strip()

    if ";" in cleaned:
        return False, "only a single statement is allowed"

    upper = cleaned.upper()
    if not (upper.startswith("SELECT") or upper.startswith("WITH")):
        return False, "query must start with SELECT or WITH (read-only)"

    for kw in FORBIDDEN:
        if re.search(rf"\b{kw}\b", upper):
            return False, f"forbidden keyword: {kw}"

    return True, "ok"
