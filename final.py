import streamlit as st


if "is_authenticated" not in st.session_state:
    st.session_state["is_authenticated"] = False  


home_page = st.Page(
    "final_k\home.py",
    title="Home",
    # icon=":material/account_circle:",
    default=True,
)
about_page = st.Page(
    "final_k\About.py",
    title="About Us",
    # icon=":material/bar_chart:",
)
contact_page = st.Page(
    "final_k\contact.py",
    title="Contact",
    # icon=":material/smart_toy:",
)
login_page = st.Page(
    "final_k\login.py",
    title="Login/Register",
    # icon=":material/smart_toy:",
)
info_page = st.Page(
    "final_k\\NCI.py",
    title="NIC Codes Info",
)


pages = [home_page, about_page, contact_page, info_page]  
if not st.session_state.get("is_authenticated", False):
    pages.append(login_page) 

pg = st.navigation(pages=pages) 

pg.run()