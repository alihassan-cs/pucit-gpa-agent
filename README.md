# PUCIT GPA/CGPA Agent

1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in `GROQ_API_KEY=<your key>`.
3. Run `python agent.py` for a terminal chat (type `quit` to exit).
4. Saved reports land in `reports/` next to `tools.py`.
5. To use it programmatically, import `agent` and `ask` from `agent.py` and pass your own message list (see the docstring on `ask`).
6. Bonus GUI: `pip install streamlit` then `streamlit run app.py`.
