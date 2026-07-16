"""
Ask-Your-Data chat UI.

    streamlit run app/streamlit_app.py

Every answer shows the plain-English result, the SQL the model wrote, and the
returned rows — so a reader can always check the number against the query.
Needs ANTHROPIC_API_KEY in the environment.
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
    con = build_warehouse()
    return Assistant(con), con


assistant, con = get_assistant()

st.title("💬 Ask Your Data")
st.caption("A natural-language layer over the analytics datasets from my portfolio "
           "projects. Ask in plain English — it writes the SQL, runs it, and shows its work.")

with st.sidebar:
    st.subheader("What you can ask about")
    for domain, blurb in DOMAINS.items():
        st.markdown(f"**{domain}** — {blurb}")
    st.divider()
    st.caption(f"{len(table_names(con))} tables loaded across {len(DOMAINS)} domains.")

EXAMPLES = [
    "Which payer type collects the least of what it bills?",
    "How many active employees do we have, and how many left voluntarily?",
    "What's the overall order fill rate?",
    "Who is the top wholesale customer by revenue?",
    "How many migration artifacts passed parallel-run validation?",
]

st.write("Try one of these, or type your own:")
cols = st.columns(len(EXAMPLES))
clicked = None
for col, ex in zip(cols, EXAMPLES):
    if col.button(ex, use_container_width=True):
        clicked = ex

question = st.chat_input("Ask a question about the data...") or clicked

if question:
    st.chat_message("user").write(question)
    with st.chat_message("assistant"):
        with st.spinner("Writing SQL and running it..."):
            result = assistant.ask(question)
        if result.refused:
            st.warning(f"I can't answer that from the loaded data: {result.reason}")
        else:
            st.markdown(f"**{result.answer}**")
            with st.expander("Show the SQL and the data behind this answer", expanded=True):
                st.code(result.sql, language="sql")
                if result.result.ok and result.result.rows:
                    df = pd.DataFrame(result.result.rows, columns=result.result.columns)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    if result.result.truncated:
                        st.caption(f"Showing the first {len(result.result.rows)} rows.")
                elif not result.result.ok:
                    st.error(f"Query error: {result.result.error}")
