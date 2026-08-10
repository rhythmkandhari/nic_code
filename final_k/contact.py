# import streamlit as st

# st.set_page_config(page_title="Contact Us", layout="wide")

# st.title("Contact Us")

# name = st.text_input("Your Name")
# email = st.text_input("Your Email")
# feedback = st.text_area("Your Feedback")

# if st.button("Submit"):
#     if name and email and feedback:
#         st.success("Thank you for your feedback! We'll get back to you soon.")
#     else:
#         st.warning("Please fill in all fields before submitting.")

# st.write("📞 Phone: +91-9999084117")
# st.write("📧 Email: karora4_be23@thapar.edu")
# # Sidebar: Font Selection
# font_choice = st.sidebar.selectbox("🔤 Choose Font Style:", ["Default", "Dyslexic-Friendly"])

# # Store the selected font in session state
# if "font_style" not in st.session_state:
#     st.session_state["font_style"] = font_choice
# else:
#     st.session_state["font_style"] = font_choice

# # Define font URLs
# dyslexic_font_url = "https://fonts.cdnfonts.com/css/opendyslexic"

# # Apply CSS dynamically based on the selected font
# if st.session_state["font_style"] == "Dyslexic-Friendly":
#     font_css = f"""
#         <style>
#         @import url('{dyslexic_font_url}');
#         * {{
#             font-family: 'OpenDyslexic', sans-serif !important;
#         }}
#         </style>
#     """
# else:
#     font_css = """
#         <style>
#         * {
#             font-family: 'Arial', sans-serif !important;
#         }
#         </style>
#     """

# st.markdown(font_css, unsafe_allow_html=True)


import streamlit as st
import cx_Oracle

# Oracle DB connection
dsn = cx_Oracle.makedsn("127.0.0.1", port=1521, sid="XE")  
conn = cx_Oracle.connect(user="SYSTEM", password="RHYTHM", dsn=dsn)
cursor = conn.cursor()

# Streamlit UI setup
st.set_page_config(page_title="Contact Us", layout="wide")
st.title("Contact Us")

# Input fields
name = st.text_input("Your Name")
email = st.text_input("Your Email")
feedback = st.text_area("Your Feedback")

# Get max existing ID for autoincrement
def get_next_id():
    cursor.execute("SELECT NVL(MAX(ID), 0) + 1 FROM CONTACT_INFO")
    return cursor.fetchone()[0]

# Submit button
if st.button("Submit"):
    if name and email and feedback:
        try:
            new_id = get_next_id()
            cursor.execute(
                "INSERT INTO CONTACT_INFO (ID, YOUR_NAME, YOUR_MAIN, YOUR_FEEDBACK) VALUES (:1, :2, :3, :4)",
                (new_id, name, email, feedback)
            )
            conn.commit()
            st.success("✅ Thank you for your feedback! We'll get back to you soon.")
        except Exception as e:
            st.error(f"❌ Error submitting feedback: {e}")
    else:
        st.warning("⚠️ Please fill in all fields before submitting.")

# Contact Info
st.write("📞 Phone: +91-9999084117")
st.write("📧 Email: rkandhari_be23@thapar.edu")

# Font selector
font_choice = st.sidebar.selectbox("🔤 Choose Font Style:", ["Default", "Dyslexic-Friendly"])
if "font_style" not in st.session_state:
    st.session_state["font_style"] = font_choice
else:
    st.session_state["font_style"] = font_choice

# Font styling
dyslexic_font_url = "https://fonts.cdnfonts.com/css/opendyslexic"
font_css = f"""
    <style>
    @import url('{dyslexic_font_url}');
    * {{
        font-family: 'OpenDyslexic', sans-serif !important;
    }}
    </style>
""" if st.session_state["font_style"] == "Dyslexic-Friendly" else """
    <style>
    * {
        font-family: 'Arial', sans-serif !important;
    }
    </style>
"""
st.markdown(font_css, unsafe_allow_html=True)
