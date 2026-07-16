"""
Live evaluation of the natural-language layer.

Asks the assistant every golden question, runs the SQL *it* writes, and checks
the answer against the expected value. This is the real test of the model — the
offline suite only proves the reference SQL and the plumbing. Needs an API key.

    python scripts/run_live_eval.py
"""

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.assistant import Assistant  # noqa: E402
from engine.warehouse import build_warehouse  # noqa: E402


def matches(got, expect):
    if got is None:
        return False
    if isinstance(expect, float):
        try:
            return abs(float(got) - expect) < 0.05
        except (TypeError, ValueError):
            return False
    return str(got).strip() == str(expect).strip()


def main():
    golden = yaml.safe_load((ROOT / "evals" / "golden_questions.yaml").read_text(encoding="utf-8"))
    assistant = Assistant(build_warehouse())
    passed = 0
    for case in golden:
        res = assistant.ask(case["question"])
        got = res.result.rows[0][0] if (res.ok and res.result.rows) else None
        ok = matches(got, case["expect"])
        passed += ok
        mark = "PASS" if ok else "FAIL"
        print(f"[{mark}] {case['id']:22s} expected={case['expect']!r} got={got!r}")
        if not ok and res.sql:
            print(f"         sql: {res.sql.strip().splitlines()[0]} ...")
    print(f"\n{passed}/{len(golden)} correct ({passed / len(golden):.0%})")
    return 0 if passed == len(golden) else 1


if __name__ == "__main__":
    raise SystemExit(main())
