"""Browse, search, add, edit and delete NIC codes. Changes feed straight into the search."""
import pandas as pd
import streamlit as st

from govintel import db, search


def valid_code(code: str) -> bool:
    return len(code) == 5 and code.isdigit()


def get_code(code: str):
    return db.fetch_one(
        "SELECT NIC_CODE, ACTIVITY_NAME, DESCRIPTION FROM NIC_CODES WHERE NIC_CODE = :p_code",
        {"p_code": code},
    )


def changed(message: str) -> None:
    """After a write: rebuild the search index and show the message after the rerun."""
    search.refresh_index()
    st.session_state["nci_flash"] = message
    st.rerun()


st.title("📋 NIC Codes")
if msg := st.session_state.pop("nci_flash", None):
    st.success(msg)

# ---------- Browse ----------
rows = db.fetch_all(
    "SELECT NIC_CODE, ACTIVITY_NAME, DESCRIPTION FROM NIC_CODES ORDER BY NIC_CODE"
)
df = pd.DataFrame(rows, columns=["NIC_CODE", "ACTIVITY_NAME", "DESCRIPTION"]).rename(
    columns={"NIC_CODE": "NIC code", "ACTIVITY_NAME": "Activity name", "DESCRIPTION": "Description"}
)
c1, c2 = st.columns([3, 1])
text_filter = c1.text_input("Filter by code or keyword", placeholder="e.g. 62 or software")
sections = ["All"] + sorted({c[:2] for c in df["NIC code"]})
division = c2.selectbox("Division (first 2 digits)", sections)
view = df
if division != "All":
    view = view[view["NIC code"].str.startswith(division)]
if text_filter:
    mask = view.apply(
        lambda r: text_filter.lower() in " ".join(map(str, r.values)).lower(), axis=1
    )
    view = view[mask]
st.caption(f"{len(view)} of {len(df)} codes")
st.dataframe(view, hide_index=True, width="stretch", height=350)

tab_add, tab_edit, tab_delete = st.tabs(["➕ Add", "✏️ Edit", "🗑️ Delete"])

# ---------- Add ----------
with tab_add, st.form("add_form", clear_on_submit=True):
    code = st.text_input("NIC code (5 digits)", max_chars=5)
    activity = st.text_input("Activity name (optional)", max_chars=100)
    description = st.text_area("Description", max_chars=500)
    if st.form_submit_button("Add NIC code"):
        code = code.strip()
        if not valid_code(code):
            st.error("NIC code must be exactly 5 digits.")
        elif not description.strip():
            st.error("Description is required.")
        elif get_code(code):
            st.error(f"NIC code {code} already exists — use the Edit tab.")
        else:
            db.execute(
                "INSERT INTO NIC_CODES (NIC_CODE, ACTIVITY_NAME, DESCRIPTION) "
                "VALUES (:p_code, :p_activity, :p_descr)",
                {"p_code": code, "p_activity": activity.strip() or None, "p_descr": description.strip()},
            )
            changed(f"Added NIC code {code}.")

# ---------- Edit ----------
with tab_edit:
    edit_code = st.text_input("NIC code to edit", max_chars=5, key="edit_code").strip()
    if edit_code:
        record = get_code(edit_code) if valid_code(edit_code) else None
        if not record:
            st.warning("No NIC code found with that value (must be 5 digits).")
        else:
            # The form is drawn whenever a valid code is typed (not inside a button),
            # so the Update click survives Streamlit's rerun.
            with st.form(f"edit_form_{edit_code}"):
                new_activity = st.text_input("Activity name", value=record["ACTIVITY_NAME"] or "", max_chars=100)
                new_description = st.text_area("Description", value=record["DESCRIPTION"], max_chars=500)
                if st.form_submit_button("Update"):
                    if not new_description.strip():
                        st.error("Description is required.")
                    else:
                        db.execute(
                            "UPDATE NIC_CODES SET ACTIVITY_NAME = :p_activity, DESCRIPTION = :p_descr "
                            "WHERE NIC_CODE = :p_code",
                            {
                                "p_activity": new_activity.strip() or None,
                                "p_descr": new_description.strip(),
                                "p_code": edit_code,
                            },
                        )
                        changed(f"Updated NIC code {edit_code}.")

# ---------- Delete ----------
with tab_delete:
    del_code = st.text_input("NIC code to delete", max_chars=5, key="del_code").strip()
    if del_code:
        record = get_code(del_code) if valid_code(del_code) else None
        if not record:
            st.warning("No NIC code found with that value (must be 5 digits).")
        else:
            st.write(f"**{record['NIC_CODE']}** — {record['DESCRIPTION']}")
            sure = st.checkbox("Yes, delete this code", key=f"confirm_{del_code}")
            if st.button("Delete", type="primary", disabled=not sure):
                db.execute("DELETE FROM NIC_CODES WHERE NIC_CODE = :p_code", {"p_code": del_code})
                changed(f"Deleted NIC code {del_code}.")
