import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, timedelta
import os

# --- Config ---
creds = st.secrets["gcp_service_account"]
gc = gspread.service_account_from_dict(creds)

GOOGLE_SHEET_NAME = "Company_Transactions"
LOCAL_FILE = "user_temp_inventory.csv"
DELETE_AFTER_MINUTES = 15

AGENTS = ["Select Agent", "Arham Kaleem", "Arham Ali", "Haziq", "Usama", "Areeb"]
LLC_OPTIONS = ["Select LLC", "Bite Bazaar LLC", "Apex Prime Solutions"]

st.set_page_config(page_title="Company Transactions Entry", layout="wide")

# --- Google Sheet ---
def connect_google_sheet():
    sh = gc.open(GOOGLE_SHEET_NAME)
    worksheet = sh.sheet1
    return worksheet

# --- Save locally + Google Sheet ---
def save_data(form_data):
    # Save locally first
    form_data["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    form_data["Status"] = "Pending"
    df = pd.DataFrame([form_data])
    df.to_csv(LOCAL_FILE, mode="a", header=not os.path.exists(LOCAL_FILE), index=False)
    st.info("Transaction saved locally as Pending.")

# --- Update status locally + Google Sheet ---
def update_status(index, new_status):
    if not os.path.exists(LOCAL_FILE):
        return
    df = pd.read_csv(LOCAL_FILE)
    if index >= len(df):
        return

    card_number = df.at[index, "Card Number"]
    df.at[index, "Status"] = new_status
    df.to_csv(LOCAL_FILE, index=False)

    # Update Google Sheet by Card Number
    try:
        ws = connect_google_sheet()
        all_values = ws.get_all_records()
        for i, row in enumerate(all_values):
            if str(row.get("Card Number")) == str(card_number):
                ws.update(f"L{i+2}", new_status)  # Column L = Status
                st.success(f"Status updated to {new_status} in Google Sheet.")
                break
    except Exception as e:
        st.error(f"Failed to update Google Sheet: {e}")


# --- Clean old entries ---
def clean_old_entries():
    if not os.path.exists(LOCAL_FILE):
        return pd.DataFrame()
    df = pd.read_csv(LOCAL_FILE)
    if "Timestamp" not in df.columns:
        return df
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    cutoff = datetime.now() - timedelta(minutes=DELETE_AFTER_MINUTES)
    df = df[df["Timestamp"] > cutoff]
    df.to_csv(LOCAL_FILE, index=False)
    return df

# --- Transaction Form ---
def transaction_form():
    st.title("Company Transactions Entry")
    st.write("Enter transaction details below. Transactions wait for status approval.")

    with st.form("transaction_form"):
        agent_name = st.selectbox("Agent Name", AGENTS)
        name = st.text_input("Name")
        ph_number = st.text_input("Ph Number")
        address = st.text_input("Address")
        email = st.text_input("Email")
        card_holder = st.text_input("Card Holder Name")
        card_number = st.text_input("Card Number")
        expiry_date = st.text_input("Expiry Date")
        cvc = st.text_input("CVC")
        charge = st.text_input("Charge")
        llc = st.selectbox("LLC", LLC_OPTIONS)
        date_of_charge = st.date_input("Date Of Charge")

        submitted = st.form_submit_button("Submit Transaction")

        if submitted:
            if not name or not ph_number or agent_name == "Select Agent" or llc == "Select LLC":
                st.warning("Please fill required fields and select Agent/LLC.")
            else:
                form_data = {
                    "Agent Name": agent_name,
                    "Name": name,
                    "Ph Number": ph_number,
                    "Address": address,
                    "Email": email,
                    "Card Holder Name": card_holder,
                    "Card Number": card_number,
                    "Expiry Date": expiry_date,
                    "CVC": cvc,
                    "Charge": charge,
                    "LLC": llc,
                    "Date Of Charge": date_of_charge.strftime("%Y-%m-%d")
                }
                save_data(form_data)
                st.rerun()  # Refresh so sidebar shows new entry

# --- Sidebar for Status Approval ---
def status_sidebar():
    st.sidebar.title("Pending Transactions Approval")
    df = clean_old_entries()
    pending_df = df[df["Status"] == "Pending"]

    if pending_df.empty:
        st.sidebar.info("No pending transactions.")
        return

    # Show the most recent pending transaction
    latest_index = pending_df.index[-1]
    latest = pending_df.loc[latest_index]
    st.sidebar.write(f"**Name:** {latest['Name']}")
    st.sidebar.write(f"**Agent:** {latest['Agent Name']}")
    st.sidebar.write(f"**Charge:** {latest['Charge']}")
    st.sidebar.write(f"**Date:** {latest['Date Of Charge']}")

    if st.sidebar.button("Charged"):
        update_status(latest_index, "Charged")
        st.rerun()

    if st.sidebar.button("Declined"):
        update_status(latest_index, "Declined")
        st.rerun()

# --- Display Local Data ---
def view_local_data():
    st.subheader("Temporary Data (Last 15 Minutes)")
    df = clean_old_entries()
    if df.empty:
        st.info("No recent transactions found.")
    else:
        st.dataframe(df)

# --- Main App ---
def main():
    transaction_form()
    status_sidebar()
    st.divider()
    view_local_data()

if __name__ == "__main__":
    main()


