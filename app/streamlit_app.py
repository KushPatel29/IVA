"""
Ask-Your-Data chat UI.

    streamlit run app/streamlit_app.py

A real conversation: follow-up questions ("and by region?") carry the earlier
turns as context. Every answer shows the plain-English result, the SQL the model
wrote, and the returned rows — so a reader can always check the number against
the query. Needs ANTHROPIC_API_KEY in the environment.
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data_manifest import DOMAINS  # noqa: E402
from engine.assistant import Assistant  # noqa: E402
from engine.warehouse import build_warehouse, table_names  # noqa: E402

st.set_page_config(page_title="Ask Your Data", page_icon="💬", layout="wide")


@st.cache_resource
def get_assistant():
    # Shared across sessions: the Assistant is stateless and queries run on
    # isolated cursors. Per-user conversation state lives in st.session_state.
    con = build_warehouse()
    return Assistant(con), con


assistant, con = get_assistant()
st.session_state.setdefault("turns", [])      # engine context (Turn objects)
st.session_state.setdefault("transcript", [])  # everything we rendered, incl. refusals

st.title("💬 Ask Your Data")
st.caption("A natural-language layer over the analytics datasets from my portfolio "
           "projects. Ask in plain English — it writes the SQL, runs it, and shows "
           "its work. Follow-up questions welcome.")

with st.sidebar:
    st.subheader("What you can ask about")
    for domain, blurb in DOMAINS.items():
        st.markdown(f"**{domain}** — {blurb}")
    st.divider()
    st.caption(f"{len(table_names(con))} tables loaded across {len(DOMAINS)} domains.")
    if st.button("Start a new conversation"):
        st.session_state.turns = []
        st.session_state.transcript = []
        st.rerun()

EXAMPLES = [
    "Which payer type collects the least of what it bills?",
    "How many active employees do we have, and how many left voluntarily?",
    "What's the overall order fill rate?",
    "Who is the top wholesale customer by revenue?",
    "How many migration artifacts passed parallel-run validation?",
]

if not st.session_state.transcript:
    st.write("Try one of these, or type your own:")
clicked = None
if not st.session_state.transcript:
    cols = st.columns(len(EXAMPLES))
    for col, ex in zip(cols, EXAMPLES):
        if col.button(ex, use_container_width=True):
            clicked = ex


def render_entry(entry):
    st.chat_message("user").write(entry["question"])
    with st.chat_message("assistant"):
        if entry["refused"]:
            st.warning(f"I can't answer that from the loaded data: {entry['reason']}")
            return
        st.markdown(f"**{entry['answer']}**")
        if entry["attempts"] > 1:
            st.caption(f"Self-corrected after {entry['attempts']} attempts "
                       f"(first error: {entry['corrections'][0]})")
        with st.expander("Show the SQL and the data behind this answer"):
            st.code(entry["sql"], language="sql")
            if entry["rows"] is not None:
                st.dataframe(entry["rows"], use_container_width=True, hide_index=True)
                if entry["truncated"]:
                    st.caption("Showing the first rows only.")
            elif entry["error"]:
                st.error(f"Query error: {entry['error']}")


for entry in st.session_state.transcript:
    render_entry(entry)

question = st.chat_input("Ask a question about the data...") or clicked

if question:
    st.chat_message("user").write(question)
    with st.chat_message("assistant"):
        with st.spinner("Writing SQL and running it..."):
            result = assistant.ask(question, history=st.session_state.turns)

    entry = {
        "question": question,
        "refused": result.refused,
        "reason": result.reason,
        "answer": result.answer,
        "sql": result.sql,
        "attempts": result.attempts,
        "corrections": result.corrections,
        "rows": (pd.DataFrame(result.result.rows, columns=result.result.columns)
                 if (result.result and result.result.ok and result.result.rows) else None),
        "truncated": bool(result.result and result.result.truncated),
        "error": result.result.error if (result.result and not result.result.ok) else "",
    }
    st.session_state.transcript.append(entry)
    if result.ok:
        st.session_state.turns.append(result.as_turn())
    st.rerun()
