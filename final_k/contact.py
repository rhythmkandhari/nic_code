import re

import streamlit as st

from govintel import db

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

st.title("Contact Us")

with st.form("contact_form", clear_on_submit=True):
    name = st.text_input("Your name", max_chars=100)
    email = st.text_input("Your email", max_chars=200)
    feedback = st.text_area("Your feedback", max_chars=2000)
    if st.form_submit_button("Submit"):
        if not (name.strip() and email.strip() and feedback.strip()):
            st.warning("Please fill in all fields before submitting.")
        elif not EMAIL_RE.match(email.strip()):
            st.warning("Please enter a valid email address.")
        else:
            try:
                db.execute(
                    "INSERT INTO CONTACT_INFO (YOUR_NAME, YOUR_MAIL, YOUR_FEEDBACK) "
                    "VALUES (:p_name, :p_mail, :p_feedback)",
                    {"p_name": name.strip(), "p_mail": email.strip(), "p_feedback": feedback.strip()},
                )
                st.success("✅ Thank you for your feedback! We'll get back to you soon.")
            except Exception as e:
                st.error(f"Error submitting feedback: {e}")

st.write("📞 Phone: +91-9999084117")
st.write("📧 Email: rkandhari_be23@thapar.edu")
