import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import gspread
from datetime import datetime, timedelta
import os

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Company Transactions Entry", layout="wide")
# Auto-refresh every 60 seconds to allow timely cleanup
st_autorefresh(interval=60 * 1000, key="data_refresh")

GOOGLE_SHEET_NAME = "Company_Transactions"
LOCAL_FILE = "user_temp_inventory.csv"
DELETE_AFTER_MINUTES = 15  # change to 15 (minutes) as desired

# The exact column order we will use for both local CSV and Google Sheet
COLUMN_ORDER = [
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
    "Timestamp"
]


# ---------------- Google Sheets connection ----------------
def connect_google_sheet():
    # supports both Streamlit Secrets (deployed) and local JSON (development)
    try:
        creds = st.secrets["gcp_service_account"]
        gc = gspread.service_account_from_dict(creds)
    except Exception:
        # fallback to local file for testing
        gc = gspread.service_account(filename="forimage-466607-0d33a2e71146.json")
    sh = gc.open(GOOGLE_SHEET_NAME)
    worksheet = sh.sheet1
    return worksheet

# ---------------- Local CSV header helper ----------------
def ensure_local_header():
    if not os.path.exists(LOCAL_FILE):
        df = pd.DataFrame(columns=COLUMN_ORDER)
        df.to_csv(LOCAL_FILE, index=False)

# ---------------- Save a submission ----------------
def save_data(form_data):
    # build a row in the exact column order
    now_iso = datetime.now().isoformat()
    row = []
    for col in COLUMN_ORDER:
        if col == "Timestamp":
            row.append(now_iso)
        else:
            row.append(form_data.get(col, ""))

    # 1) Append to Google Sheet
    try:
        ws = connect_google_sheet()
        ws.append_row(row, value_input_option="USER_ENTERED")
        st.success("✅ Saved to Google Sheet.")
    except Exception as e:
        st.error(f"Failed to save to Google Sheet: {e}")

    # 2) Append to local CSV (temporary backup)
    ensure_local_header()
    row_dict = dict(zip(COLUMN_ORDER, row))
    pd.DataFrame([row_dict]).to_csv(LOCAL_FILE, mode="a", header=False, index=False)
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
    st.title("Company Transactions Entry")
    st.write("Fill the form. Data is saved to Google Sheet (permanent) and to a temporary local CSV (cleared after configured minutes).")

    with st.form("transaction_form"):
        name = st.text_input("Name")
        ph_number = st.text_input("Ph Number")
        # merged address field
        complete_address = st.text_input("Complete Address (Address, City, State, Zipcode)")
        email = st.text_input("Email")
        card_holder = st.text_input("Card Holder Name")
        card_number = st.text_input("Card Number")
        expiry_date = st.text_input("Expiry Date")
        cvc = st.text_input("CVC")
        charge = st.text_input("Charge")
        llc = st.text_input("LLC")
        date_of_charge = st.date_input("Date Of Charge")

        submitted = st.form_submit_button("Submit Transaction")

        if submitted:
            if not name or not ph_number:
                st.warning("Please fill in at least Name and Phone Number.")
            else:
                form_data = {
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
                    # "Timestamp" is added automatically in save_data()
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



