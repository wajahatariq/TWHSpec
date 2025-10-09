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

# --- Connect to Google Sheets ---
DELETE_AFTER_MINUTES = 5

def clean_old_entries():
    if not os.path.exists(LOCAL_FILE):
        return pd.DataFrame()

    df = pd.read_csv(LOCAL_FILE)
    if "Timestamp" not in df.columns:
        return df

    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    cutoff = datetime.now() - timedelta(minutes=DELETE_AFTER_MINUTES)
    df = df[df["Timestamp"] > cutoff]  # keep only recent entries

    df.to_csv(LOCAL_FILE, index=False)  # overwrite CSV
    return df
    
def connect_google_sheet():
    sh = gc.open(GOOGLE_SHEET_NAME)
    worksheet = sh.sheet1
    return worksheet

# --- Save to Google Sheet ---
def save_to_google(form_data):
    ws = connect_google_sheet()
    ws.append_row(list(form_data.values()))
    st.success(f"Saved to Google Sheet.")

# --- Save to local CSV ---
def save_to_csv(form_data):
    file_exists = os.path.exists(LOCAL_FILE)
    df = pd.DataFrame([form_data])
    df.to_csv(LOCAL_FILE, mode="a", header=not file_exists, index=False)
    st.info(f"Saved to local CSV")

# --- Initialize session state ---
if "transactions" not in st.session_state:
    st.session_state.transactions = []

# --- Transaction form ---
def transaction_form():
    st.title("Company Transactions Entry")
    st.write("Enter transaction details. Approve or decline them in the sidebar.")

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

    if any(not v or (isinstance(v, str) and v.startswith("Select")) for v in form_fields.values()):
        st.warning("Please complete all details in the form."))
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
                st.success(f"{name} added to sidebar for approval.")

# --- Sidebar for approve/decline ---
def sidebar_transactions():
    st.sidebar.title("Approve / Decline Transactions")
    pending_txns = [t for t in st.session_state.transactions if t["Status"] == "Pending"]

    if not pending_txns:
        st.sidebar.info("No pending transactions.")
        return

    for idx, txn in enumerate(pending_txns):
        st.sidebar.write(f"**Card Number:** {txn['Card Number']}")
        st.sidebar.write(f"**CVV:** {txn['CVC']}")
        st.sidebar.write(f"**Card Holder Name:** {txn['Card Holder Name']}")
        st.sidebar.write(f"**Expiry Date:** {txn['Expiry Date']}")
        st.sidebar.write(f"**Address:** {txn['Address']}")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("Charged", key=f"charged_{idx}"):
                txn["Status"] = "Charged"
                save_to_google(txn)
                save_to_csv(txn)
                st.sidebar.success("Updated as Charged")
                st.rerun()
        with col2:
            if st.button("Declined", key=f"declined_{idx}"):
                txn["Status"] = "Declined"
                save_to_google(txn)
                save_to_csv(txn)
                st.sidebar.success("Updated as Declined")
                st.rerun()
                
# --- View processed transactions from CSV ---
def view_local_data():
    st.subheader(f"Temporary Data (last {DELETE_AFTER_MINUTES} minutes)")
    
    df = clean_old_entries()  # auto-clean old entries

    if df.empty:
        st.info("No transactions saved locally yet.")
    else:
        st.dataframe(df)

# --- Main App ---
def main():
    transaction_form()
    sidebar_transactions()
    st.divider()
    view_local_data()

if __name__ == "__main__":
    main()








