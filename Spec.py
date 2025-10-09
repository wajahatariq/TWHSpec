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

COLUMN_ORDER = [
    "Agent Name", "Name", "Ph Number", "Complete Address", "Email",
    "Card Holder Name", "Card Number", "Expiry Date", "CVC",
    "Charge", "LLC", "Date of Charge", "TimeStamp", "Status"
]

st.set_page_config(page_title="Company Transactions Entry", layout="wide")

# --- Google Sheet connection ---
def connect_google_sheet():
    sh = gc.open(GOOGLE_SHEET_NAME)
    worksheet = sh.sheet1
    return worksheet

# --- Save locally ---
def save_data(form_data):
    form_data["TimeStamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    form_data["Status"] = "Pending"

    # Align with column order
    row = [form_data.get(col, "") for col in COLUMN_ORDER]

    # Save locally
    df = pd.DataFrame([form_data])
    df.to_csv(LOCAL_FILE, mode="a", header=not os.path.exists(LOCAL_FILE), index=False)
    st.info("Transaction saved locally as Pending.")

# --- Append transaction to Google Sheet ---
def append_to_google_sheet(form_data):
    try:
        ws = connect_google_sheet()
        row = [form_data.get(col, "") for col in COLUMN_ORDER]
        ws.append_row(row)
        st.success(f"Transaction for {form_data['Name']} inserted into Google Sheet with status {form_data['Status']}")
    except Exception as e:
        st.error(f"Failed to insert into Google Sheet: {e}")

# --- Clean old entries ---
def clean_old_entries():
    if not os.path.exists(LOCAL_FILE):
        return pd.DataFrame()
    df = pd.read_csv(LOCAL_FILE)
    # Ensure required columns
    if "TimeStamp" not in df.columns:
        df["TimeStamp"] = datetime.now()
    else:
        df["TimeStamp"] = pd.to_datetime(df["TimeStamp"], errors="coerce")
    if "Status" not in df.columns:
        df["Status"] = "Pending"
    cutoff = datetime.now() - timedelta(minutes=DELETE_AFTER_MINUTES)
    df = df[df["TimeStamp"] > cutoff]
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
        address = st.text_input("Complete Address")
        email = st.text_input("Email")
        card_holder = st.text_input("Card Holder Name")
        card_number = st.text_input("Card Number")
        expiry_date = st.text_input("Expiry Date")
        cvc = st.text_input("CVC")
        charge = st.text_input("Charge")
        llc = st.selectbox("LLC", LLC_OPTIONS)
        date_of_charge = st.date_input("Date of Charge")

        submitted = st.form_submit_button("Submit Transaction")

        if submitted:
            if not name or not ph_number or agent_name == "Select Agent" or llc == "Select LLC":
                st.warning("Please fill required fields and select Agent/LLC.")
            else:
                form_data = {
                    "Agent Name": agent_name,
                    "Name": name,
                    "Ph Number": ph_number,
                    "Complete Address": address,
                    "Email": email,
                    "Card Holder Name": card_holder,
                    "Card Number": card_number,
                    "Expiry Date": expiry_date,
                    "CVC": cvc,
                    "Charge": charge,
                    "LLC": llc,
                    "Date of Charge": date_of_charge.strftime("%Y-%m-%d")
                }
                save_data(form_data)
                st.rerun()

# --- Sidebar for Status Approval ---
def status_sidebar():
    st.sidebar.title("Pending Transactions Approval")
    df = clean_old_entries()

    if "Status" not in df.columns or df.empty:
        st.sidebar.info("No pending transactions.")
        return

    pending_df = df[df["Status"] == "Pending"]
    if pending_df.empty:
        st.sidebar.info("No pending transactions.")
        return

    st.sidebar.subheader(f"Total Pending: {len(pending_df)}")

    # Scrollable sidebar using expander
    with st.sidebar.expander("Pending Transactions", expanded=True):
        for idx in pending_df.index:
            txn = pending_df.loc[idx]
            st.markdown("---")
            st.write(f"**Name:** {txn['Name']}")
            st.write(f"**Agent:** {txn['Agent Name']}")
            st.write(f"**Charge:** {txn['Charge']}")
            st.write(f"**Card Number:** {txn['Card Number']}")
            st.write(f"**Date:** {txn['Date of Charge']}")

            col1, col2 = st.columns(2)
            if col1.button(f"Charged {txn['Card Number']}", key=f"charged_{txn['Card Number']}"):
                df.at[idx, "Status"] = "Charged"
                df.to_csv(LOCAL_FILE, index=False)
                append_to_google_sheet(df.loc[idx].to_dict())
                st.rerun()

            if col2.button(f"Declined {txn['Card Number']}", key=f"declined_{txn['Card Number']}"):
                df.at[idx, "Status"] = "Declined"
                df.to_csv(LOCAL_FILE, index=False)
                append_to_google_sheet(df.loc[idx].to_dict())
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

