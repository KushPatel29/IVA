"""Run every golden question's reference SQL against the warehouse and check the
answer. This proves, without any API key, that the reference SQL is valid and the
data still produces the documented answers — the accuracy contract the live
assistant is measured against."""

from pathlib import Path

import pytest
import yaml

from engine.query import run_query

EVALS = Path(__file__).resolve().parent.parent / "evals"
GOLDEN = yaml.safe_load((EVALS / "golden_questions.yaml").read_text(encoding="utf-8"))


def _scalar(res):
    return res.rows[0][0]


@pytest.mark.parametrize("case", GOLDEN, ids=[c["id"] for c in GOLDEN])
def test_reference_sql_gives_expected_answer(con, case):
    res = run_query(con, case["sql"])
    assert res.ok, f"{case['id']}: reference SQL failed — {res.error}"
    assert res.rows, f"{case['id']}: reference SQL returned no rows"
    got, expect = _scalar(res), case["expect"]
    if isinstance(expect, float):
        assert abs(float(got) - expect) < 0.05, f"{case['id']}: {got} != {expect}"
    else:
        assert got == expect, f"{case['id']}: {got!r} != {expect!r}"


def test_golden_set_covers_every_domain(con):
    from data_manifest import DOMAINS
    covered = {c["domain"] for c in GOLDEN}
    assert covered == set(DOMAINS), f"golden set misses domains: {set(DOMAINS) - covered}"


def test_adversarial_set_is_well_formed():
    cases = yaml.safe_load((EVALS / "adversarial_questions.yaml").read_text(encoding="utf-8"))
    assert len(cases) >= 5
    for c in cases:
        assert c["id"] and c["question"], c
