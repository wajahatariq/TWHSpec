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
DELETE_AFTER_MINUTES = 5  # Local records auto-delete after X minutes

COLUMN_ORDER = [
    "Agent Name",
    "Name",
    "Ph Number",
    "Complete Address",
    "Email",
    "Card Holder Name",
    "Card Number",
    "Expiry Date",
    "CVC",
    "Charge",
    "LLC",
    "Date Of Charge",
    "Timestamp",
]

AGENTS = ["Select Agent", "Arham Kaleem", "Arham Ali", "Haziq", "Usama", "Areeb"]
LLC = ["Select LLC", "Bite Bazaar LLC", "Apex Prime Solutions"]
# ---------------- Google Sheets connection ----------------
def connect_google_sheet():
    try:
        creds = st.secrets["gcp_service_account"]
        gc = gspread.service_account_from_dict(creds)
    except Exception:
        gc = gspread.service_account(filename="forimage-466607-0d33a2e71146.json")
    sh = gc.open(GOOGLE_SHEET_NAME)
    return sh.sheet1

# ---------------- Local CSV header helper ----------------
def ensure_local_header():
    if not os.path.exists(LOCAL_FILE):
        pd.DataFrame(columns=COLUMN_ORDER).to_csv(LOCAL_FILE, index=False)

# ---------------- Save a submission ----------------
def save_data(form_data):
    now_iso = datetime.now(pytz.timezone("Asia/Karachi")).strftime("%Y-%m-%d %H:%M:%S")
    row = []
    for col in COLUMN_ORDER:
        if col == "Timestamp":
            row.append(now_iso)
        else:
            row.append(form_data.get(col, ""))

    try:
        ws = connect_google_sheet()
        ws.append_row(row, value_input_option="USER_ENTERED")
        st.success("Saved to Google Sheet.")
    except Exception as e:
        st.error(f"Failed to save to Google Sheet: {e}")

    ensure_local_header()
    pd.DataFrame([dict(zip(COLUMN_ORDER, row))]).to_csv(
        LOCAL_FILE, mode="a", header=False, index=False
    )
    st.info("Saved locally (temporary).")


# ---------------- Clean expired local entries ----------------
def clean_old_entries():
    if not os.path.exists(LOCAL_FILE):
        return pd.DataFrame(columns=COLUMN_ORDER)

    df = pd.read_csv(LOCAL_FILE)
    if "Timestamp" not in df.columns:
        return df

    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    cutoff = datetime.now() - timedelta(minutes=DELETE_AFTER_MINUTES)
    df = df[df["Timestamp"] > cutoff]
    df.to_csv(LOCAL_FILE, index=False)
    return df

# ---------------- UI: transaction form ----------------
def transaction_form():
    st.title("Client Management System")
    st.write(
        "Fill the form. Data is saved to Google Sheet (permanent) and to a temporary local CSV (cleared automatically after 5 minutes) ."
    )

    with st.form("transaction_form"):
        agent_name = st.selectbox("Agent Name", AGENTS)
        name = st.text_input("Name")
        ph_number = st.text_input("Ph Number")
        complete_address = st.text_input("Complete Address (Address, City, State, Zipcode)")
        email = st.text_input("Email")
        card_holder = st.text_input("Card Holder Name")
        card_number = st.text_input("Card Number")
        expiry_date = st.text_input("Expiry Date")
        cvc = st.text_input("CVC")
        charge = st.text_input("Charge")
        llc = st.selectbox("LLC",LLC)
        date_of_charge = st.date_input("Date Of Charge")

        submitted = st.form_submit_button("Submit Details")

        if submitted:
            # ✅ proper validation inside the form
            if not name or not ph_number or agent_name == "Select Agent":
                st.warning("Please fill in Name, Phone Number, and select an Agent.")
            else:
                form_data = {
                    "Agent Name": agent_name,
                    "Name": name,
                    "Ph Number": ph_number,
                    "Complete Address": complete_address,
                    "Email": email,
                    "Card Holder Name": card_holder,
                    "Card Number": card_number,
                    "Expiry Date": expiry_date,
                    "CVC": cvc,
                    "Charge": charge,
                    "LLC": llc,
                    "Date Of Charge": date_of_charge.strftime("%Y-%m-%d"),
                }
                save_data(form_data)

# ---------------- UI: show temporary local data ----------------
def view_local_data():
    st.subheader(f"Temporary Data (Last {DELETE_AFTER_MINUTES} minutes)")
    df = clean_old_entries()
    if df.empty:
        st.info("No recent transactions found.")
    else:
        st.dataframe(df)

# ---------------- Main ----------------
def main():
    ensure_local_header()
    transaction_form()
    st.divider()
    view_local_data()

if __name__ == "__main__":
    main()






