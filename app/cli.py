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

from engine.assistant import Assistant, AssistantUnavailable  # noqa: E402
from engine.warehouse import build_warehouse  # noqa: E402


def _usage_line(usage):
    if not usage:
        return ""
    parts = [f"in {usage.get('input_tokens', 0):,}", f"out {usage.get('output_tokens', 0):,}"]
    if usage.get("cache_read_input_tokens"):
        parts.append(f"cache read {usage['cache_read_input_tokens']:,}")
    return "tokens: " + " / ".join(parts)


def show(result):
    if result.refused:
        print(f"\n  I can't answer that from the loaded data: {result.reason}\n")
        return
    print(f"\n{result.answer}\n")
    if result.attempts > 1:
        print(f"  (self-corrected after {result.attempts} attempts)")
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
    if result.usage:
        print(f"\n  {_usage_line(result.usage)}")
    print()


def main():
    con = build_warehouse()
    assistant = Assistant(con)

    def ask(q, history=None):
        try:
            return assistant.ask(q, history=history)
        except AssistantUnavailable as e:
            print(f"\n  The language model is unavailable: {e}\n"
                  "  Set ANTHROPIC_API_KEY (and check your credit balance) and try again.\n")
            return None

    if len(sys.argv) > 1:
        result = ask(" ".join(sys.argv[1:]))
        if result:
            show(result)
        return
    print("Ask your data. Follow-up questions work. Blank line to quit.\n")
    history = []
    while True:
        try:
            q = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q:
            break
        result = ask(q, history=history)
        if result is None:
            continue
        show(result)
        if result.ok:
            history.append(result.as_turn())


if __name__ == "__main__":
    main()
