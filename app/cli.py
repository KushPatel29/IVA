"""
Ask questions from the terminal.

    python -m app.cli "which payer type collects the least of what it's billed?"
    python -m app.cli            # interactive REPL

Needs ANTHROPIC_API_KEY in the environment for the language model; the warehouse
and SQL execution run entirely locally.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.assistant import Assistant  # noqa: E402
from engine.warehouse import build_warehouse  # noqa: E402


def show(result):
    if result.refused:
        print(f"\n  I can't answer that from the loaded data: {result.reason}\n")
        return
    print(f"\n{result.answer}\n")
    print("  SQL:")
    for line in result.sql.strip().splitlines():
        print(f"    {line}")
    if result.result.ok:
        cols = result.result.columns
        print("\n  " + " | ".join(cols))
        for row in result.result.rows[:15]:
            print("  " + " | ".join("" if v is None else str(v) for v in row))
        if result.result.truncated:
            print(f"  ... (showing first {len(result.result.rows)} rows)")
    else:
        print(f"\n  query error: {result.result.error}")
    print()


def main():
    con = build_warehouse()
    assistant = Assistant(con)
    if len(sys.argv) > 1:
        show(assistant.ask(" ".join(sys.argv[1:])))
        return
    print("Ask your data. Blank line to quit.\n")
    while True:
        try:
            q = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q:
            break
        show(assistant.ask(q))


if __name__ == "__main__":
    main()
