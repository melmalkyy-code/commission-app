"""
Shared startup module — imported by every page.
Ensures the DB schema and seed data exist before any page uses the database.
The @st.cache_resource decorator guarantees this runs only ONCE per process.
"""
import streamlit as st
from src.schema import create_schema
from src.seed import seed


@st.cache_resource
def init_db() -> bool:
    create_schema()
    try:
        seed()
    except Exception:
        # PG may have dropped between create_schema and seed, switching the
        # thread to a fresh SQLite that has no tables. Re-apply schema and retry.
        create_schema()
        seed()
    return True
