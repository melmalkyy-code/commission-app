"""
Shared startup module — imported by every page.
Ensures the DB schema and seed data exist before any page uses the database.
The @st.cache_resource decorator guarantees this runs only ONCE per process
(and is retried on the next run if it raises).
"""
import streamlit as st
from src.schema import create_schema
from src.seed import seed


@st.cache_resource
def init_db() -> bool:
    try:
        create_schema()
        seed()
    except Exception:
        # One retry for transient connection drops (pooler timeouts).
        # A second failure propagates and is shown to the user.
        create_schema()
        seed()
    return True
