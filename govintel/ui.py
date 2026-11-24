"""Sidebar and styling shared by every page (rendered once from final.py)."""
from __future__ import annotations

import streamlit as st

from . import ASSETS

FONTS = {
    "Default": "<style>html, body, [class*='css'], .stMarkdown { font-family: Arial, sans-serif; }</style>",
    "Dyslexic-Friendly": (
        "<style>@import url('https://fonts.cdnfonts.com/css/opendyslexic');"
        "html, body, [class*='css'], .stMarkdown, input, textarea, button "
        "{ font-family: 'OpenDyslexic', sans-serif !important; }</style>"
    ),
}


def sidebar() -> None:
    st.session_state.setdefault("font_style", "Default")
    with st.sidebar:
        st.image(str(ASSETS / "GovINTEL.AI.png"), width="stretch")
        # Widget lives in the entrypoint, so its value survives page switches.
        st.selectbox("🔤 Font style", list(FONTS), key="font_style")
    st.markdown(FONTS[st.session_state["font_style"]], unsafe_allow_html=True)
