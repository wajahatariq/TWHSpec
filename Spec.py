import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, timedelta
import os
import pytz

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Company Transactions Entry", layout="wide")
GOOGLE_SHEET_NAME = "Company_Transactions"
LOCAL_FILE = "user_temp_inventory.csv"
DELETE_AFTER_MINUTES = 5

# ---------------- GOOGLE SHEET AUTH ----------------
gc = gspread.service_account(filename="credentials.json")

# ---------------- LOAD LOCAL FILE ----------------
if os.path.exists(LOCAL_FILE):
    df = pd.read_csv(LOCAL_FILE)
else:
    df = pd.DataFrame(columns=["Name", "Ph Number", "Amount", "Card Number", "CVC", "Timestamp", "Status"])

# Remove old records (auto cleanup)
now = datetime.now(pytz.timezone("Asia/Karachi"))
if not df.empty:
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    df = df[df["Timestamp"] > now - timedelta(minutes=DELETE_AFTER_MINUTES)]
    df.to_csv(LOCAL_FILE, index=False)

# ---------------- FORM SECTION ----------------
st.header("Enter Transaction")

with st.form("entry_form", clear_on_submit=True):
    name = st.text_input("Name")
    phone = st.text_input("Phone Number")
    amount = st.text_input("Amount")
    card = st.text_input("Card Number")
    cvc = st.text_input("CVC")

    submit = st.form_submit_button("Save Entry")

if submit:
    if not all([name, phone, amount, card, cvc]):
        st.error("Please fill all fields.")
    else:
        new_entry = {
            "Name": name,
            "Ph Number": phone,
            "Amount": amount,
            "Card Number": card,
            "CVC": cvc,
            "Timestamp": now.isoformat(),
            "Status": "Pending"
        }

        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        df.to_csv(LOCAL_FILE, index=False)
        st.success(f"✅ Entry saved locally for {name}")

# ---------------- SIDEBAR SECTION ----------------
st.sidebar.header(f"Manage Pending Entries ({len(df)})")

if not df.empty:
    # Show dropdown of all pending names
    names = df["Name"].tolist()
    selected_name = st.sidebar.selectbox("Select client:", ["-- Select --"] + names)

    if selected_name != "-- Select --":
        entry = df[df["Name"] == selected_name].iloc[0]

        st.sidebar.write(f"**Phone:** {entry['Ph Number']}")
        st.sidebar.write(f"**Amount:** {entry['Amount']}")
        st.sidebar.write(f"**Card:** {entry['Card Number']}")
        st.sidebar.write(f"**CVC:** {entry['CVC']}")

        status_choice = st.sidebar.radio("Update Status to:", ["Charged", "Declined"], horizontal=True)

        if st.sidebar.button("Update Status"):
            try:
                # Update in local df
                df.loc[df["Name"] == selected_name, "Status"] = status_choice

                # Push that record to Google Sheet
                record = df[df["Name"] == selected_name].copy()
                record = record.astype(str).iloc[0].tolist()

                sheet = gc.open(GOOGLE_SHEET_NAME).sheet1
                sheet.append_row(record)

                # Remove from local pending
                df = df[df["Name"] != selected_name]
                df.to_csv(LOCAL_FILE, index=False)

                st.sidebar.success(f"✅ {selected_name} marked as {status_choice} and saved to Google Sheet")

                st.rerun()

            except Exception as e:
                st.sidebar.error(f"❌ Failed to update Google Sheet: {e}")

else:
    st.sidebar.info("No pending entries found.")
