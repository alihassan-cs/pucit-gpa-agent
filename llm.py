"""
llm.py — model setup, same as Lab 2.

Reads GROQ_API_KEY from .env (see .env.example). Never hardcode the key.
"""

import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError(
        "GROQ_API_KEY is not set. Copy .env.example to .env and add your key."
    )

llm = init_chat_model("groq:openai/gpt-oss-20b")
