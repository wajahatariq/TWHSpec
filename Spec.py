import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, timedelta
import os

# --- Google Sheets setup ---
creds = st.secrets["gcp_service_account"]
gc = gspread.service_account_from_dict(creds)
GOOGLE_SHEET_NAME = "Company_Transactions"
LOCAL_FILE = "user_temp_inventory.csv"
DELETE_AFTER_MINUTES = 15  # Auto delete after 15 mins

AGENTS = ["Select Agent", "Arham Kaleem", "Arham Ali", "Haziq", "Usama", "Areeb"]
LLC_OPTIONS = ["Select LLC", "Bite Bazaar LLC", "Apex Prime Solutions"]

st.set_page_config(page_title="Company Transactions Entry", layout="wide")

# --- Connect to Google Sheets ---
def connect_google_sheet():
    sh = gc.open(GOOGLE_SHEET_NAME)
    worksheet = sh.sheet1
    return worksheet

# --- Save data ---
def save_data(form_data):
    # Initially status is Pending
    form_data["Status"] = "Pending"
    form_data["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Save locally
    df = pd.DataFrame([form_data])
    df.to_csv(LOCAL_FILE, mode="a", header=not os.path.exists(LOCAL_FILE), index=False)
    st.info("Data saved locally (temporary view).")

    # Save to Google Sheet
    try:
        ws = connect_google_sheet()
        ws.append_row(list(form_data.values()))
        st.success("Data saved to Google Sheet successfully!")
    except Exception as e:
        st.error(f"Failed to save to Google Sheet: {e}")

# --- Clean old entries ---
def clean_old_entries():
    if not os.path.exists(LOCAL_FILE):
        return pd.DataFrame()

    df = pd.read_csv(LOCAL_FILE)
    if "Timestamp" not in df.columns:
        return df

    now = datetime.now()
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    cutoff = now - timedelta(minutes=DELETE_AFTER_MINUTES)
    df = df[df["Timestamp"] > cutoff]

    df.to_csv(LOCAL_FILE, index=False)
    return df

# --- Update status locally ---
def update_local_status(client_name, status):
    df = pd.read_csv(LOCAL_FILE)
    df.loc[df["Name"] == client_name, "Status"] = status
    df.to_csv(LOCAL_FILE, index=False)

# --- Update status in Google Sheet ---
def update_google_status(client_name, status):
    ws = connect_google_sheet()
    all_data = ws.get_all_records()
    
    for i, row in enumerate(all_data, start=2):  # start=2 because row 1 is header
        if row["Name"] == client_name:
            # Assuming Status column is at the end (last column)
            col_index = len(row)  # Column index in Google Sheet
            ws.update_cell(i, col_index + 1, status)
            break

# --- Transaction form ---
def transaction_form():
    st.title("Company Transactions Entry")
    st.write("Enter transaction details below. Data will sync with Google Sheet and auto-clear locally after 15 minutes.")

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
                    "Date Of Charge": date_of_charge.strftime("%Y-%m-%d")
                }
                save_data(form_data)

# --- Manage transactions with Charge/Decline ---
def manage_transactions():
    st.subheader("Pending Transactions")
    df = clean_old_entries()
    if df.empty:
        st.info("No recent transactions found.")
        return
    
    pending_df = df[df["Status"] == "Pending"]
    if pending_df.empty:
        st.info("No pending transactions.")
        return

    for idx, row in pending_df.iterrows():
        st.write(f"**Client:** {row['Name']} | **Charge:** {row['Charge']}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"Charge {row['Name']}", key=f"charge_{idx}"):
                update_local_status(row["Name"], "Charged")
                update_google_status(row["Name"], "Charged")
                st.success(f"{row['Name']} has been Charged.")
        with col2:
            if st.button(f"Decline {row['Name']}", key=f"decline_{idx}"):
                update_local_status(row["Name"], "Declined")
                update_google_status(row["Name"], "Declined")
                st.error(f"{row['Name']} has been Declined.")

# --- Main App ---
def main():
    transaction_form()
    st.divider()
    manage_transactions()

if __name__ == "__main__":
    main()
