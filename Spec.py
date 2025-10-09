import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, timedelta
import os
import time

# --- Google Sheets credentials ---
creds = st.secrets["gcp_service_account"]
gc = gspread.service_account_from_dict(creds)

# --- Configuration ---
GOOGLE_SHEET_NAME = "Company_Transactions"
LOCAL_FILE = "user_temp_inventory.csv"
DELETE_AFTER_MINUTES = 15

AGENTS = ["Select Agent", "Arham Kaleem", "Arham Ali", "Haziq", "Usama", "Areeb"]
LLC_OPTIONS = ["Select LLC", "Bite Bazaar LLC", "Apex Prime Solutions"]

# Standardized column names
COLUMNS = [
    "Agent Name", "Name", "Ph Number", "Address", "Email",
    "Card Holder Name", "Card Number", "Expiry Date", "CVC", "Charge",
    "LLC", "Date Of Charge", "TimeStamp", "Status"
]

st.set_page_config(page_title="Company Transactions Entry", layout="wide")

# --- Connect to Google Sheets ---
def connect_google_sheet():
    sh = gc.open(GOOGLE_SHEET_NAME)
    return sh.sheet1

# --- Save transaction locally ---
def save_data(form_data):
    form_data["TimeStamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    form_data["Status"] = "Pending"
    df = pd.DataFrame([form_data])
    df.to_csv(LOCAL_FILE, mode="a", header=not os.path.exists(LOCAL_FILE), index=False)
    st.info("Transaction saved locally as Pending.")

# --- Push single transaction to Google Sheets (append only) ---
def push_transaction_to_google_sheet(transaction):
    try:
        ws = connect_google_sheet()
        row_values = [transaction.get(col, "") for col in COLUMNS]
        ws.append_row(row_values)
        st.success(f"Transaction for {transaction['Name']} pushed to Google Sheet.")
        time.sleep(1)
    except Exception as e:
        st.error(f"Failed to push transaction to Google Sheet: {e}")

# --- Clean old local entries ---
def clean_old_entries():
    if not os.path.exists(LOCAL_FILE):
        return pd.DataFrame(columns=COLUMNS)
    df = pd.read_csv(LOCAL_FILE)
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df["TimeStamp"] = pd.to_datetime(df["TimeStamp"], errors="coerce")
    cutoff = datetime.now() - timedelta(minutes=DELETE_AFTER_MINUTES)
    df = df[df["TimeStamp"] > cutoff]
    df.to_csv(LOCAL_FILE, index=False)
    return df

# --- Transaction Form ---
def transaction_form():
    st.title("Company Transactions Entry")
    st.write("Enter transaction details below. Data syncs with Google Sheet and auto-clears locally after 15 minutes.")

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
                st.warning("Please fill in Name, Phone Number, select an Agent, and select an LLC.")
            else:
                form_data = {col: "" for col in COLUMNS}
                form_data.update({
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
                })
                save_data(form_data)
                st.rerun()

# --- Sidebar: Pending Transactions Approval ---
def status_sidebar():
    st.sidebar.title("Pending Transactions Approval")
    df = clean_old_entries()
    if df.empty or "Status" not in df.columns:
        st.sidebar.info("No pending transactions.")
        return

    pending_df = df[df["Status"] == "Pending"]
    if pending_df.empty:
        st.sidebar.info("No pending transactions.")
        return

    st.sidebar.subheader(f"Total Pending: {len(pending_df)}")
    for idx in pending_df.index:
        txn = pending_df.loc[idx]
        st.sidebar.markdown("---")
        st.sidebar.write(f"**Name:** {txn['Name']}")
        st.sidebar.write(f"**Agent:** {txn['Agent Name']}")
        st.sidebar.write(f"**Charge:** {txn['Charge']}")
        st.sidebar.write(f"**Card Number:** {txn['Card Number']}")
        st.sidebar.write(f"**Date:** {txn['Date Of Charge']}")

        col1, col2 = st.sidebar.columns(2)
        if col1.button(f"Charged {txn['Card Number']}", key=f"charged_{txn['Card Number']}"):
            df.at[idx, "Status"] = "Charged"
            df.to_csv(LOCAL_FILE, index=False)
            push_transaction_to_google_sheet(df.loc[idx].to_dict())
            st.rerun()

        if col2.button(f"Declined {txn['Card Number']}", key=f"declined_{txn['Card Number']}"):
            df.at[idx, "Status"] = "Declined"
            df.to_csv(LOCAL_FILE, index=False)
            push_transaction_to_google_sheet(df.loc[idx].to_dict())
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
