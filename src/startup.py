"""
Shared startup module — imported by every page.
Ensures the DB schema and seed data exist before any page uses the database.
The @st.cache_resource decorator guarantees this runs only ONCE per process,
no matter how many pages import it.
"""
import streamlit as st
from src.schema import create_schema
from src.seed import seed


@st.cache_resource
def init_db() -> bool:
    create_schema()
    seed()
    return True
