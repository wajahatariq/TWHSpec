import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, timedelta
import os

# --- Google Sheets setup ---
creds = st.secrets["gcp_service_account"]
gc = gspread.service_account_from_dict(creds)
GOOGLE_SHEET_NAME = "Company_Transactions"
LOCAL_FILE = "company_transactions.csv"

AGENTS = ["Select Agent", "Arham Kaleem", "Arham Ali", "Haziq", "Usama", "Areeb"]
LLC_OPTIONS = ["Select LLC", "Bite Bazaar LLC", "Apex Prime Solutions"]

st.set_page_config(page_title="Company Transactions Entry", layout="wide")

DELETE_AFTER_MINUTES = 5

# --- Helper functions ---
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

def connect_google_sheet():
    sh = gc.open(GOOGLE_SHEET_NAME)
    worksheet = sh.sheet1
    return worksheet

def save_to_google(form_data):
    ws = connect_google_sheet()
    ws.append_row(list(form_data.values()))
    st.success(f"Saved to Google Sheet.")

def save_to_csv(form_data):
    file_exists = os.path.exists(LOCAL_FILE)
    df = pd.DataFrame([form_data])
    df.to_csv(LOCAL_FILE, mode="a", header=not file_exists, index=False)
    st.info(f"Saved to local CSV")

# --- Initialize session state ---
if "transactions" not in st.session_state:
    st.session_state.transactions = []

# --- Transaction Form ---
def transaction_form():
    st.title("Company Transactions Entry")
    st.write("Enter transaction details. Approve or decline them in 'Awaiting Transactions' tab.")

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
                    "Date Of Charge": date_of_charge.strftime("%Y-%m-%d"),
                    "Status": "Pending",
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.transactions.append(form_data)
                st.success(f"{name} added for approval.")

# --- Inline Table for Pending Transactions ---
def inline_table_pending():
    pending_txns = [t for t in st.session_state.transactions if t["Status"] == "Pending"]

    if not pending_txns:
        st.info("No pending transactions.")
        return

    for idx, txn in enumerate(pending_txns):
        cols = st.columns([3, 1])  # left for details, right for buttons
        with cols[0]:
            st.markdown(f"""
            <h3>Card Holder: {txn['Card Holder Name']}</h3>
            <h4>Address: {txn['Address']}</h4>
            <h4>Card Number: {txn['Card Number']}</h4>
            <h4>LLC: {txn['LLC']}</h4>
            <h4>CVV: {txn['CVC']}</h4>
            <h4>Expiry Date: {txn['Expiry Date']}</h4>
            """, unsafe_allow_html=True)
        with cols[1]:
            if st.button("Charged", key=f"charged_{idx}"):
                txn["Status"] = "Charged"
                save_to_google(txn)
                save_to_csv(txn)
                st.experimental_rerun()
            if st.button("Declined", key=f"declined_{idx}"):
                txn["Status"] = "Declined"
                save_to_google(txn)
                save_to_csv(txn)
                st.experimental_rerun()

# --- View Temporary Local CSV ---
def view_local_data():
    st.subheader(f"Temporary Data (last {DELETE_AFTER_MINUTES} minutes)")
    df = clean_old_entries()
    if df.empty:
        st.info("No transactions saved locally yet.")
    else:
        st.dataframe(df)

# --- Main App ---
def main():
    transaction_form()
    st.divider()

    # Tabs
    tab1, tab2 = st.tabs(["Awaiting Transactions", "Processed / Local Data"])

    with tab1:
        st.subheader("Awaiting Transactions")
        inline_table_pending()

    with tab2:
        view_local_data()

if __name__ == "__main__":
    main()
