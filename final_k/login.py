import streamlit as st
from final_k.local_db import get_connection


st.set_page_config(page_title="Login / Register", layout="wide")


conn = get_connection()
cursor = conn.cursor()

if "history" not in st.session_state:
    st.session_state["history"] = []
if "voice_input" not in st.session_state:
    st.session_state["voice_input"] = ""
st.session_state.setdefault("is_authenticated", False)
st.session_state.setdefault("user_email", "anonymous")

st.sidebar.image("GovINTEL.AI.png", use_container_width=True)
st.sidebar.title("📜 Search History")

if st.session_state["is_authenticated"]:
    
    cursor.execute("SELECT ACTIVITY_NAME, PREDICTED_NIC FROM RESULT_CODES WHERE USER_NAME = ? ORDER BY ID DESC", (st.session_state["user_email"],))
    history_records = cursor.fetchall()
    if history_records:
        for i, (user_input, nic_codes) in enumerate(history_records, start=1):
            st.sidebar.markdown(f"**{i}.** {user_input}  \n🚀 *{nic_codes}*")
    else:
        st.sidebar.info("No history yet.")
else:
    st.sidebar.info("Login to see your history.")


if st.sidebar.button("Clear History"):
    if st.session_state["is_authenticated"]:
        cursor.execute("DELETE FROM RESULT_CODES WHERE USER_NAME = ?", (st.session_state["user_email"],))
        conn.commit()
        st.sidebar.success("Your history cleared!")
    else:
        st.sidebar.warning("Login first to clear history!")


st.title("Login & Register")

st.write("""To access all features of **NIC Code Finder**, please log in or create an account.""")


def create_user(email, password):
    cursor.execute("SELECT * FROM LOGIN_DETAILS WHERE USER_NAME = ?", (email,))
    existing_user = cursor.fetchone()
    if existing_user:
        return False
    cursor.execute("INSERT INTO LOGIN_DETAILS (USER_NAME, PASSWORD) VALUES (?, ?)", (email, password))
    conn.commit()
    return True

def authenticate_user(email, password):
    cursor.execute("SELECT * FROM LOGIN_DETAILS WHERE USER_NAME = ? AND PASSWORD = ?", (email, password))
    user = cursor.fetchone()
    if user:
        return True
    return False


col1, col2 = st.columns(2)


with col1:
    st.markdown("### **Existing Users - Login**")
    login_email = st.text_input("Email", key="login_email", placeholder="Enter your email")
    login_password = st.text_input("Password", key="login_password", placeholder="Enter your password", type="password")
    if st.button("Login", key="login_button"):
        if login_email and login_password:
            if authenticate_user(login_email, login_password):
                st.session_state["is_authenticated"] = True
                st.session_state["user_email"] = login_email
                st.success(f"Welcome back, {login_email}!")
                st.rerun()
            else:
                st.warning("Invalid email or password.")
        else:
            st.warning("Please enter both email and password!")


with col2:
    st.markdown("### **New Users - Register**")
    reg_email = st.text_input("Email", key="reg_email", placeholder="Enter your email")
    reg_password = st.text_input("Password", key="reg_password", placeholder="Create a password", type="password")
    if st.button("Register", key="register_button"):
        if reg_email and reg_password:
            if create_user(reg_email, reg_password):
                st.success(f"Account created successfully for {reg_email}! Please login.")
            else:
                st.warning("User already exists! Try logging in.")
        else:
            st.warning("Please fill all fields!")


st.markdown("**Your account gives you access to exclusive features in NIC Code Finder.**")


font_choice = st.sidebar.selectbox("🔤 Choose Font Style:", ["Default", "Dyslexic-Friendly"])


if "font_style" not in st.session_state:
    st.session_state["font_style"] = font_choice
else:
    st.session_state["font_style"] = font_choice


dyslexic_font_url = "https://fonts.cdnfonts.com/css/opendyslexic"


if st.session_state["font_style"] == "Dyslexic-Friendly":
    font_css = f"""
        <style>
        @import url('{dyslexic_font_url}');
        * {{
            font-family: 'OpenDyslexic', sans-serif !important;
        }}
        </style>
    """
else:
    font_css = """
        <style>
        * {
            font-family: 'Arial', sans-serif !important;
        }
        </style>
    """

st.markdown(font_css, unsafe_allow_html=True)
