"""
The natural-language layer: turn a plain-English question into SQL, run it, and
answer from the result.

Design choices that keep this honest:

- The model's ONLY job is to write SQL. It never states a number from its own
  head — every figure in the final answer comes from a query that actually ran
  against the warehouse, and the SQL is returned alongside the answer so it can
  be audited. If the question can't be answered from the loaded tables, the
  model says so instead of inventing one.
- **Bounded self-correction.** When the SQL fails (a mistyped column, a guard
  block), the database error is fed back to the model for a corrected attempt —
  at most MAX_ATTEMPTS total, never an unbounded agent loop. Every failed
  attempt is kept on the result for transparency.
- **Conversation memory.** Follow-up questions ("and by region?") work because
  prior turns — question, the SQL used, the answer — are passed back as context.
  The caller owns the history, so the Assistant itself stays stateless and
  thread-safe.
- **Prompt caching.** The schema catalog is the bulk of every request, and it
  never changes within a session, so the system block carries `cache_control` —
  from the second question on, the catalog is served from the prompt cache at a
  fraction of the cost.

The model is asked for structured output via a tool, so we get clean SQL (or a
refusal) rather than having to scrape it out of prose.
"""

import os
from dataclasses import dataclass, field

import anthropic

from engine.query import QueryResult, run_query
from engine.warehouse import schema_catalog

MODEL = os.environ.get("ASK_YOUR_DATA_MODEL", "claude-opus-4-8")
MAX_ATTEMPTS = 3   # 1 initial attempt + up to 2 corrections
HISTORY_TURNS = 6  # how many prior turns are replayed as context

SYSTEM = """You are a careful analytics engineer answering questions about a \
read-only DuckDB warehouse by writing SQL.

Rules:
- Use ONLY the tables and columns listed in the schema. Never invent a column.
- Table names are exactly as written — they are domain-prefixed (e.g.
  healthcare_fact_claims, hr_fact_employees). The same base name can exist in
  several domains, so always use the full prefixed name.
- Write DuckDB SQL. SELECT statements only — no INSERT/UPDATE/DDL. If the user
  asks you to modify, delete, or export data, call cannot_answer and explain
  that this is a read-only interface.
- Read the column descriptions carefully. For example, pending healthcare claims
  have blank allowed_amount/paid_amount; net collection rate is paid/allowed.
- For "top", "most", "highest" questions add ORDER BY and a LIMIT.
- Round money to whole dollars and rates to a sensible precision in the SQL when
  it makes the answer clearer.
- Follow-up questions refer to the earlier conversation — reuse the same tables
  and filters unless the user changes them.
- If the question cannot be answered from these tables, call cannot_answer with a
  short reason — do not guess.

SCHEMA
======
{catalog}
"""

TOOLS = [
    {
        "name": "answer_with_sql",
        "description": "Provide the DuckDB SELECT query that answers the question.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "A single DuckDB SELECT query."},
                "explanation": {"type": "string",
                                "description": "One sentence on what the query computes."},
            },
            "required": ["sql", "explanation"],
        },
    },
    {
        "name": "cannot_answer",
        "description": "Use when the question cannot be answered from the available tables.",
        "input_schema": {
            "type": "object",
            "properties": {"reason": {"type": "string"}},
            "required": ["reason"],
        },
    },
]


@dataclass
class Turn:
    """One completed exchange, replayed as context for follow-up questions."""
    question: str
    sql: str
    answer: str


@dataclass
class AskResult:
    question: str
    sql: str = ""
    explanation: str = ""
    answer: str = ""
    result: QueryResult = None
    refused: bool = False
    reason: str = ""
    attempts: int = 1
    corrections: list = field(default_factory=list)  # errors from failed attempts

    @property
    def ok(self):
        return not self.refused and self.result is not None and self.result.ok

    def as_turn(self) -> Turn:
        return Turn(self.question, self.sql, self.answer)


def _format_result(res: QueryResult, max_rows: int = 30) -> str:
    if not res.columns:
        return "(no columns)"
    lines = [" | ".join(res.columns)]
    for row in res.rows[:max_rows]:
        lines.append(" | ".join("" if v is None else str(v) for v in row))
    if res.truncated or len(res.rows) > max_rows:
        lines.append(f"... ({res.row_count}{'+' if res.truncated else ''} rows)")
    return "\n".join(lines)


def _history_messages(history):
    """Render prior turns as plain alternating messages. Plain text (rather than
    replayed tool_use blocks) keeps the protocol simple: only the current turn
    uses the tool call."""
    messages = []
    for turn in history[-HISTORY_TURNS:]:
        messages.append({"role": "user", "content": turn.question})
        messages.append({"role": "assistant",
                         "content": f"(SQL used)\n{turn.sql}\n\n(answer)\n{turn.answer}"})
    return messages


class Assistant:
    """Stateless NL->SQL assistant. Pass `history` (a list of Turn) to enable
    follow-up questions; the caller owns and appends to it."""

    def __init__(self, con, client=None, model: str = MODEL):
        self.con = con
        self.client = client or anthropic.Anthropic()
        self.model = model
        # cache_control: the catalog is identical on every request in a session,
        # so it is served from the prompt cache after the first question.
        self.system = [{
            "type": "text",
            "text": SYSTEM.format(catalog=schema_catalog(con)),
            "cache_control": {"type": "ephemeral"},
        }]

    def ask(self, question: str, history: list = None) -> AskResult:
        messages = _history_messages(history or [])
        messages.append({"role": "user", "content": question})

        corrections = []
        sql, explanation, result = "", "", None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            msg = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=self.system,
                tools=TOOLS,
                tool_choice={"type": "any"},
                messages=messages,
            )
            tool_use = next((b for b in msg.content if b.type == "tool_use"), None)
            if tool_use is None:
                return AskResult(question, refused=True, attempts=attempt,
                                 corrections=corrections,
                                 reason="model did not produce a query")
            if tool_use.name == "cannot_answer":
                return AskResult(question, refused=True, attempts=attempt,
                                 corrections=corrections,
                                 reason=tool_use.input.get("reason", "out of scope"))

            sql = tool_use.input["sql"]
            explanation = tool_use.input.get("explanation", "")
            result = run_query(self.con, sql)
            if result.ok:
                answer = self._summarize(question, result)
                return AskResult(question, sql=sql, explanation=explanation,
                                 answer=answer, result=result,
                                 attempts=attempt, corrections=corrections)

            # Self-correction: hand the real error back and ask for a fix.
            corrections.append(result.error)
            messages.append({"role": "assistant", "content": f"I tried this SQL:\n{sql}"})
            messages.append({"role": "user", "content": (
                f"That query failed with: {result.error}\n"
                "Write a corrected single SELECT query. Use only tables and "
                "columns that appear in the schema."
            )})

        # Out of attempts — return the last failure honestly.
        return AskResult(question, sql=sql, explanation=explanation, result=result,
                         attempts=MAX_ATTEMPTS, corrections=corrections)

    def _summarize(self, question: str, result: QueryResult) -> str:
        """Turn the result table into one or two plain-English sentences, grounded
        strictly in the returned rows."""
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=400,
            system=("Answer the user's question in one or two sentences using ONLY "
                    "the SQL result provided. Never invent or round beyond what is "
                    "shown. If there are no rows, say nothing matched."),
            messages=[{"role": "user",
                       "content": f"Question: {question}\n\nSQL result:\n{_format_result(result)}"}],
        )
        return "".join(b.text for b in msg.content if b.type == "text").strip()
