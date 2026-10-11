"""
app.py — Streamlit GUI for the PUCIT GPA/CGPA agent (bonus).

Run:  streamlit run app.py

The agent is stateless, so the full message history lives in
st.session_state and is passed to ask() on every turn (Part 2).
"""

import streamlit as st
from langchain.messages import HumanMessage

from agent import ask

st.set_page_config(page_title="PUCIT GPA Assistant", page_icon="🎓")
st.title("🎓 PUCIT GPA Assistant")
st.caption("Semester GPA, CGPA projection, and target-CGPA planning for BS(CS).")

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("Try asking")
    examples = [
        "I got 78 in Analysis of Algorithms, 85 in AI, and 64 in HCI. What's my GPA?",
        "My CGPA is 3.1 and I've done 64 credit hours. If I get a 3.6 this semester, where do I end up?",
        "I'm in semester 5, CGPA 3.0, 64 credit hours, I want a 3.4. What do I need?",
        "What courses are in semester 6?",
    ]
    picked = None
    for ex in examples:
        if st.button(ex, use_container_width=True):
            picked = ex
    show_tools = st.checkbox("Show tool calls", value=False)
    if st.button("New conversation", type="primary", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Replay history
for msg in st.session_state.messages:
    if msg.type == "human":
        with st.chat_message("user"):
            st.write(msg.text)
    elif msg.type == "ai":
        if msg.text.strip():
            with st.chat_message("assistant"):
                st.write(msg.text)
        if show_tools and getattr(msg, "tool_calls", None):
            for call in msg.tool_calls:
                with st.chat_message("assistant", avatar="🔧"):
                    st.code(f"{call['name']}({call['args']})", language="python")
    elif msg.type == "tool" and show_tools:
        with st.chat_message("assistant", avatar="📎"):
            st.code(f"→ {msg.content}")

user_input = st.chat_input("Ask about your GPA or CGPA…") or picked

if user_input:
    with st.chat_message("user"):
        st.write(user_input)
    history_before = list(st.session_state.messages)
    st.session_state.messages.append(HumanMessage(user_input))
    with st.chat_message("assistant"):
        with st.spinner("Working it out…"):
            try:
                st.session_state.messages = ask(st.session_state.messages)
            except Exception as exc:  # noqa: BLE001
                st.session_state.messages = history_before
                st.error(f"That didn't work ({exc}). Please send it again.")
                st.stop()
    st.rerun()
