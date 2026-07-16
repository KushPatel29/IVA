"""The executor runs validated SQL, caps rows, and surfaces errors as data
rather than raising."""

from engine.query import run_query


def test_simple_aggregate(con):
    res = run_query(con, "SELECT COUNT(*) AS n FROM hr_fact_employees")
    assert res.ok
    assert res.columns == ["n"]
    assert res.rows[0][0] == 1900


def test_blocked_query_returns_error_not_exception(con):
    res = run_query(con, "DROP TABLE hr_fact_employees")
    assert not res.ok
    assert "guard" in res.error


def test_bad_column_is_reported(con):
    res = run_query(con, "SELECT no_such_column FROM hr_fact_employees")
    assert not res.ok
    assert res.error  # DuckDB binder error surfaced as a string


def test_row_cap_is_enforced_and_flagged(con):
    res = run_query(con, "SELECT * FROM supplychain_fact_orders", max_rows=50)
    assert res.ok
    assert res.row_count == 50
    assert res.truncated
