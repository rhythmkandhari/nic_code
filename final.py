"""GovINTEL.AI entrypoint. Run with:  streamlit run final.py"""
import streamlit as st

from govintel import ROOT, db, ui

st.set_page_config(page_title="GovINTEL.AI – NIC Code Finder", page_icon="🏷️", layout="wide")

try:
    db.init_db()
except Exception as e:
    st.error(
        f"Could not open the {db.backend()} database: {e}\n\n"
        "Check `.streamlit/secrets.toml` (see `.streamlit/secrets.toml.example`)."
    )
    st.stop()

PAGES = ROOT / "final_k"
pg = st.navigation(
    [
        st.Page(PAGES / "home.py", title="Home", icon="🏠", default=True),
        st.Page(PAGES / "NCI.py", title="NIC Codes Info", icon="📋"),
        st.Page(PAGES / "About.py", title="About Us", icon="ℹ️"),
        st.Page(PAGES / "contact.py", title="Contact", icon="✉️"),
    ]
)
ui.sidebar()
pg.run()
