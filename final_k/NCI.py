# import streamlit as st
# import pandas as pd
# import cx_Oracle
# from datetime import datetime
# # Set page title
# st.set_page_config(page_title="CSV Viewer", layout="wide")

# dsn = cx_Oracle.makedsn("127.0.0.1", port=1521, sid="XE")  
# conn = cx_Oracle.connect(user="SYSTEM", password="RHYTHM", dsn=dsn)
# cursor = conn.cursor()

# def add_data(activity_name,nic_code,description):
#     intial_id=200
#     #every time new id add the id increaases with one 
#     id=id+1
#     cursor.execute("INSERT INTO NIC_CODES (ID, ACTIVITY_NAME, NIC_CODE, DESCRIPTION) VALUES ('id','activity_name','nic_code','description'); ")
   
    

# # Title
# st.title("NIC Codes 📊")


# csv_file_path = r"C:/Users/ASUS/Desktop/DBMS Project/final_k/NIC_5digit.csv"
# df = pd.read_csv(csv_file_path)

# # Set the index to start from 1 instead of 0
# df.index = df.index + 1

# # Display the dataframe as a table
# st.dataframe(df, use_container_width=True)


# # Sidebar: Font Selection
# font_choice = st.sidebar.selectbox("🔤 Choose Font Style:", ["Default", "Dyslexic-Friendly"])

# enter_code=st.table(
#     label="fuck you ", placeholder="enter new code ", label_visibility="collapsed"
# )

# #def combine_code_enter(enter_code,add_code):
    
    
    


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

# import streamlit as st
# import pandas as pd
# import cx_Oracle
# from datetime import datetime

# # Set page title
# st.set_page_config(page_title="NIC Code Manager", layout="wide")

# # Oracle DB connection
# dsn = cx_Oracle.makedsn("127.0.0.1", port=1521, sid="XE")  
# conn = cx_Oracle.connect(user="SYSTEM", password="RHYTHM", dsn=dsn)
# cursor = conn.cursor()

# # Function to add data to Oracle DB
# def add_data(activity_name, nic_code, description):
#     # Fetch current max ID
#     cursor.execute("SELECT NVL(MAX(ID), 199) FROM NIC_CODES")
#     current_max_id = cursor.fetchone()[0]
#     new_id = current_max_id + 1
    
#     # Insert data using bind variables to prevent SQL injection
#     cursor.execute(
#         "INSERT INTO NIC_CODES (ID, ACTIVITY_NAME, NIC_CODE, DESCRIPTION) VALUES (:1, :2, :3, :4)",
#         (new_id, activity_name, nic_code, description)
#     )
#     conn.commit()
#     st.success(f"Record added successfully with ID: {new_id}")

# # Title
# st.title("NIC Codes 📊")

# # Sidebar font style
# font_choice = st.sidebar.selectbox("🔤 Choose Font Style:", ["Default", "Dyslexic-Friendly"])
# if "font_style" not in st.session_state:
#     st.session_state["font_style"] = font_choice
# else:
#     st.session_state["font_style"] = font_choice

# # Apply font style
# if st.session_state["font_style"] == "Dyslexic-Friendly":
#     st.markdown("""
#         <style>
#         @import url('https://fonts.cdnfonts.com/css/opendyslexic');
#         * {
#             font-family: 'OpenDyslexic', sans-serif !important;
#         }
#         </style>
#     """, unsafe_allow_html=True)
# else:
#     st.markdown("""
#         <style>
#         * {
#             font-family: 'Arial', sans-serif !important;
#         }
#         </style>
#     """, unsafe_allow_html=True)

# # Form to add new NIC Code
# st.header("➕ Add New NIC Code")
# with st.form("add_nic_code_form"):
#     activity_name = st.text_input("Activity Name")
#     nic_code = st.text_input("NIC Code")
#     description = st.text_area("Description")

#     submit = st.form_submit_button("Add NIC Code")
#     if submit:
#         if activity_name and nic_code and description:
#             add_data(activity_name, nic_code, description)
#         else:
#             st.error("Please fill all the fields before submitting.")

# # Optional: display table from CSV (can be removed later)
# csv_file_path = r"C:/Users/ASUS/Desktop/DBMS Project/final_k/NIC_5digit.csv"
# df = pd.read_csv(csv_file_path)
# df.index = df.index + 1
# st.dataframe(df, use_container_width=True)




import streamlit as st
import pandas as pd
from final_k.local_db import get_connection

# Local offline SQLite database
conn = get_connection()
cursor = conn.cursor()

# Function to check if NIC code already exists
def nic_code_exists(nic_code):
    cursor.execute("SELECT COUNT(*) FROM NIC_CODES WHERE NIC_CODE = ?", (nic_code,))
    count = cursor.fetchone()[0]
    return count > 0

# Function to add validated data
def add_data(activity_name, nic_code, description):
    cursor.execute("SELECT IFNULL(MAX(ID), 199) FROM NIC_CODES")
    current_max_id = cursor.fetchone()[0]
    new_id = current_max_id + 1

    cursor.execute(
        "INSERT INTO NIC_CODES (ID, ACTIVITY_NAME, NIC_CODE, DESCRIPTION) VALUES (?, ?, ?, ?)",
        (new_id, activity_name, nic_code, description)
    )
    conn.commit()
    st.success(f"✅ Record added successfully with ID: {new_id}")
    
def fetch_all_nic_codes():
    cursor.execute("SELECT ID, ACTIVITY_NAME, NIC_CODE, DESCRIPTION FROM NIC_CODES ORDER BY ID")
    data = cursor.fetchall()
    columns = ["ID", "Activity Name", "NIC Code", "Description"]
    df = pd.DataFrame(data, columns=columns)
    return df

st.header("📋 Current NIC Code Records (Live Table)")
nic_df = fetch_all_nic_codes()
st.dataframe(nic_df, use_container_width=True)



st.header("➕ Add New NIC Code")
with st.form("add_nic_code_form"):
    activity_name = st.text_input("Activity Name (Max 50 characters)")
    nic_code = st.text_input("NIC Code (Exactly 5 characters)")
    description = st.text_area("Description (Max 200 characters)")

    submit = st.form_submit_button("Add NIC Code")

    if submit:
        # Validation checks
        if not activity_name or not nic_code or not description:
            st.error("❌ Please fill in all the fields.")
        elif len(nic_code) != 5:
            st.error("❌ NIC Code must be exactly 5 characters long.")
        elif nic_code_exists(nic_code):
            st.error("❌ This NIC Code already exists. Please use a unique one.")
        elif len(description) > 200:
            st.error("❌ Description cannot be more than 200 characters.")
        elif len(activity_name) > 50:
            st.error("❌ Activity Name cannot be more than 50 characters.")
        else:
            add_data(activity_name, nic_code, description)


st.header("🔎 Search NIC Code")
search_code = st.text_input("Enter NIC Code to Search (5 characters)")

if st.button("Search"):
    if len(search_code) != 5 :
        st.error("❌ NIC Code must be exactly 5 characters long.")
    else:
        cursor.execute("SELECT * FROM NIC_CODES WHERE NIC_CODE = ?", (search_code,))
        result = cursor.fetchone()
        if result:
            st.success("✅ NIC Code Found:")
            st.write(f"ID: {result[0]}")
            st.write(f"Activity Name: {result[1]}")
            st.write(f"NIC Code: {result[2]}")
            st.write(f"Description: {result[3]}")
        else:
            st.warning("⚠️ No NIC Code found with that value.")


st.header("🗑️ Delete NIC Code")
delete_code = st.text_input("Enter NIC Code to Delete (5 characters)")

if st.button("Delete"):
    if len(delete_code) != 5:
        st.error("❌ NIC Code must be exactly 5 characters long.")
    elif not nic_code_exists(delete_code):
        st.warning("⚠️ NIC Code not found. Cannot delete.")
    else:
        cursor.execute("DELETE FROM NIC_CODES WHERE NIC_CODE = ?", (delete_code,))
        conn.commit()
        st.success(f"✅ NIC Code '{delete_code}' deleted successfully.")

st.header("✏️ Edit Existing NIC Code")
edit_code = st.text_input("Enter NIC Code to Edit (5 characters)")

if st.button("Load for Edit"):
    if len(edit_code) != 5:
        st.error("❌ NIC Code must be exactly 5 characters.")
    elif not nic_code_exists(edit_code):
        st.warning("⚠️ NIC Code not found.")
    else:
        cursor.execute("SELECT * FROM NIC_CODES WHERE NIC_CODE = ?", (edit_code,))
        record = cursor.fetchone()
        if record:
            with st.form("edit_form"):
                new_activity = st.text_input("New Activity Name", value=record[1])
                new_description = st.text_area("New Description", value=record[3])
                submit_update = st.form_submit_button("Update")

                if submit_update:
                    if len(new_activity) > 50:
                        st.error("❌ Activity Name cannot exceed 50 characters.")
                    elif len(new_description) > 200:
                        st.error("❌ Description cannot exceed 200 characters.")
                    else:
                        cursor.execute("""
                            UPDATE NIC_CODES
                            SET ACTIVITY_NAME = ?, DESCRIPTION = ?
                            WHERE NIC_CODE = ?
                        """, (new_activity, new_description, edit_code))
                        conn.commit()
                        st.success(f"✅ NIC Code '{edit_code}' updated successfully.")
                        


#st.rerun()

