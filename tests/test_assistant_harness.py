"""
Harness tests for the assistant's control flow, run entirely offline.

A scripted fake client stands in for the model, which lets CI prove the parts of
the assistant that are pure logic — the self-correction loop, the bounded retry
budget, conversation memory, prompt-cache wiring, and the guard integration —
without an API key. The live model's SQL-writing accuracy is graded separately
(scripts/run_live_eval.py); everything here must hold no matter what the model
returns.
"""

from types import SimpleNamespace

import pytest

from engine.assistant import MAX_ATTEMPTS, Assistant, Turn


def tool_use(name, **input):
    return SimpleNamespace(type="tool_use", name=name, input=input)


def text(t):
    return SimpleNamespace(type="text", text=t)


def msg(*blocks):
    return SimpleNamespace(content=list(blocks))


class FakeClient:
    """Returns scripted responses in order and records every request payload."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        if not self._responses:
            raise AssertionError("assistant made more API calls than scripted")
        return self._responses.pop(0)


GOOD_SQL = "SELECT COUNT(*) AS n FROM healthcare_fact_claims"
BAD_SQL = "SELECT no_such_column FROM healthcare_fact_claims"
EVIL_SQL = "DROP TABLE healthcare_fact_claims"


def test_happy_path_single_attempt(con):
    client = FakeClient([
        msg(tool_use("answer_with_sql", sql=GOOD_SQL, explanation="counts claims")),
        msg(text("There are 12,000 claims.")),  # the summarize call
    ])
    res = Assistant(con, client=client).ask("how many claims?")
    assert res.ok and res.attempts == 1 and res.corrections == []
    assert res.result.rows[0][0] == 12000
    assert res.answer == "There are 12,000 claims."


def test_self_corrects_after_a_bad_column(con):
    client = FakeClient([
        msg(tool_use("answer_with_sql", sql=BAD_SQL, explanation="")),
        msg(tool_use("answer_with_sql", sql=GOOD_SQL, explanation="")),
        msg(text("12,000.")),
    ])
    res = Assistant(con, client=client).ask("how many claims?")
    assert res.ok and res.attempts == 2
    assert len(res.corrections) == 1 and "no_such_column" in res.corrections[0]
    # the retry request must carry the real database error back to the model
    retry_messages = client.calls[1]["messages"]
    assert any("failed with" in str(m.get("content", "")) for m in retry_messages)


def test_malicious_sql_is_blocked_not_executed_then_corrected(con):
    before = con.execute("SELECT COUNT(*) FROM healthcare_fact_claims").fetchone()[0]
    client = FakeClient([
        msg(tool_use("answer_with_sql", sql=EVIL_SQL, explanation="")),
        msg(tool_use("answer_with_sql", sql=GOOD_SQL, explanation="")),
        msg(text("12,000.")),
    ])
    res = Assistant(con, client=client).ask("drop the claims table")
    assert res.ok and res.attempts == 2
    assert "guard" in res.corrections[0]
    # the table is untouched — the guard rejected the statement before execution
    after = con.execute("SELECT COUNT(*) FROM healthcare_fact_claims").fetchone()[0]
    assert before == after == 12000


def test_retry_budget_is_bounded(con):
    client = FakeClient([
        msg(tool_use("answer_with_sql", sql=BAD_SQL, explanation=""))
        for _ in range(MAX_ATTEMPTS)
    ])
    res = Assistant(con, client=client).ask("how many claims?")
    assert not res.ok
    assert res.attempts == MAX_ATTEMPTS
    assert len(res.corrections) == MAX_ATTEMPTS
    assert len(client.calls) == MAX_ATTEMPTS  # no unbounded loop, no extra calls


def test_refusal_passes_through(con):
    client = FakeClient([msg(tool_use("cannot_answer", reason="no weather data"))])
    res = Assistant(con, client=client).ask("what's the weather?")
    assert res.refused and res.reason == "no weather data"
    assert len(client.calls) == 1  # a refusal must not trigger retries


def test_history_is_replayed_for_follow_ups(con):
    client = FakeClient([
        msg(tool_use("answer_with_sql", sql=GOOD_SQL, explanation="")),
        msg(text("12,000.")),
    ])
    history = [Turn(question="denial rate by payer?",
                    sql="SELECT payer_id, 0.1 FROM healthcare_dim_payer",
                    answer="Around 8-12% depending on payer.")]
    Assistant(con, client=client).ask("and how many claims in total?", history=history)
    sent = client.calls[0]["messages"]
    assert sent[0]["content"] == "denial rate by payer?"
    assert "(SQL used)" in sent[1]["content"]
    assert sent[-1]["content"] == "and how many claims in total?"


def test_schema_catalog_is_cache_controlled(con):
    client = FakeClient([
        msg(tool_use("answer_with_sql", sql=GOOD_SQL, explanation="")),
        msg(text("12,000.")),
    ])
    Assistant(con, client=client).ask("how many claims?")
    system = client.calls[0]["system"]
    assert system[0]["cache_control"] == {"type": "ephemeral"}
    assert "healthcare_fact_claims" in system[0]["text"]
