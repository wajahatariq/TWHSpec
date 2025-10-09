import streamlit as st
import pandas as pd
import gspread
from datetime import datetime
import os
import pytz

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Client Management System", layout="wide")

GOOGLE_SHEET_NAME = "Company_Transactions"
LOCAL_FILE = "user_temp_inventory.csv"

# ---------------- GOOGLE SHEET CONNECTION ----------------
try:
    gc = gspread.service_account(filename="service_account.json")
except Exception as e:
    st.error("❌ Google Sheets connection failed. Please check service_account.json")
    st.stop()

# ---------------- FUNCTIONS ----------------
def load_local_data():
    if os.path.exists(LOCAL_FILE):
        return pd.read_csv(LOCAL_FILE)
    else:
        return pd.DataFrame(columns=[
            "Agent Name", "Name", "Ph Number", "Complete Address", "Email",
            "Card Holder Name", "Card Number", "Expiry Date", "CVC",
            "Charge", "LLC", "Date Of Charge", "Status"
        ])

def save_local_data(df):
    df.to_csv(LOCAL_FILE, index=False)

def append_to_google_sheet(row):
    try:
        sh = gc.open(GOOGLE_SHEET_NAME)
        ws = sh.sheet1
    except Exception as e:
        st.error(f"❌ Could not open Google Sheet: {e}")
        return False

    try:
        # Convert all values to strings before upload
        row_str = [str(x) for x in row]
        ws.append_row(row_str)
        return True
    except Exception as e:
        st.error(f"❌ Failed to append to Google Sheet: {e}")
        return False

# ---------------- FORM SECTION ----------------
st.title("Client Management System")
st.write("Fill the form. Data is saved locally first, and synced to Google Sheet after status update.")

df = load_local_data()

with st.form("entry_form"):
    st.subheader("Add New Entry")
    agent_name = st.text_input("Agent Name")
    name = st.text_input("Name")
    phone = st.text_input("Ph Number")
    address = st.text_input("Complete Address (Address, City, State, Zipcode)")
    email = st.text_input("Email")
    card_holder = st.text_input("Card Holder Name")
    card_number = st.text_input("Card Number")
    expiry = st.text_input("Expiry Date (MM/YYYY)")
    cvc = st.text_input("CVC")
    charge = st.text_input("Charge")
    llc = st.text_input("LLC")
    date_of_charge = datetime.now(pytz.timezone("Asia/Karachi")).strftime("%Y/%m/%d")

    submitted = st.form_submit_button("Save Entry")

    if submitted:
        new_entry = pd.DataFrame([{
            "Agent Name": agent_name,
            "Name": name,
            "Ph Number": phone,
            "Complete Address": address,
            "Email": email,
            "Card Holder Name": card_holder,
            "Card Number": card_number,
            "Expiry Date": expiry,
            "CVC": cvc,
            "Charge": charge,
            "LLC": llc,
            "Date Of Charge": date_of_charge,
            "Status": "Pending"
        }])
        df = pd.concat([df, new_entry], ignore_index=True)
        save_local_data(df)
        st.success("✅ Saved locally (Pending status). Will be uploaded after status update.")

# ---------------- SIDEBAR SECTION ----------------
st.sidebar.header("⚙️ Manage Pending Entries")

pending_df = df[df["Status"] == "Pending"]

if pending_df.empty:
    st.sidebar.write("No entries to manage yet.")
else:
    entry_names = pending_df["Name"].astype(str) + " (" + pending_df["Ph Number"].astype(str) + ")"
    selected_entry_name = st.sidebar.selectbox("Select entry:", entry_names)

    selected_entry = pending_df.loc[entry_names == selected_entry_name].iloc[0]
    selected_index = pending_df.loc[entry_names == selected_entry_name].index[0]

    st.sidebar.write(f"**Client:** {selected_entry['Name']}")
    st.sidebar.write(f"**Charge:** {selected_entry['Charge']}")
    st.sidebar.write(f"**LLC:** {selected_entry['LLC']}")

    selected_status = st.sidebar.radio("Update status to:", ["Charged", "Declined"], key="status_choice")

    if st.sidebar.button("Update Status"):
        df.loc[selected_index, "Status"] = selected_status

        # Convert datetime-like objects to string before upload
        row_data = df.loc[selected_index].apply(lambda x: str(x) if pd.notnull(x) else "").tolist()

        success = append_to_google_sheet(row_data)
        if success:
            st.sidebar.success(f"✅ Entry marked as '{selected_status}' and saved to Google Sheet.")
            # Remove from local pending list
            df.drop(index=selected_index, inplace=True)
            save_local_data(df)
            st.experimental_rerun()
        else:
            st.sidebar.error("❌ Failed to save entry to Google Sheet.")

# ---------------- DISPLAY LOCAL DATA ----------------
st.subheader("📋 Local Pending Entries")
if not df.empty:
    st.dataframe(df)
else:
    st.write("No local entries found.")
