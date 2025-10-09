import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, timedelta
import os

# --- Configuration ---
GOOGLE_SHEET_NAME = "Company_Transactions"
LOCAL_FILE = "user_temp_inventory.csv"
DELETE_AFTER_MINUTES = 15  # Auto delete after 15 mins

st.set_page_config(page_title="Company Transactions Entry", layout="wide")

# --- Connect to Google Sheets ---
def connect_google_sheet():
    gc = gspread.service_account(filename="forimage-466607-0d33a2e71146.json")
    sh = gc.open(GOOGLE_SHEET_NAME)
    worksheet = sh.sheet1
    return worksheet

# --- Save to Google Sheet + Local File ---
def save_data(form_data):
    # Save to Google Sheet
    try:
        ws = connect_google_sheet()
        ws.append_row(list(form_data.values()))
        st.success("Data saved to Google Sheet successfully!")
    except Exception as e:
        st.error(f"Failed to save to Google Sheet: {e}")

    # Save locally (temporary data)
    form_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df = pd.DataFrame([form_data])
    df.to_csv(LOCAL_FILE, mode="a", header=not os.path.exists(LOCAL_FILE), index=False)
    st.info("Data also saved locally (temporary view).")

# --- Auto-delete old local entries ---
def clean_old_entries():
    if not os.path.exists(LOCAL_FILE):
        return pd.DataFrame()

    df = pd.read_csv(LOCAL_FILE)
    if "timestamp" not in df.columns:
        return df

    now = datetime.now()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    cutoff = now - timedelta(minutes=DELETE_AFTER_MINUTES)
    df = df[df["timestamp"] > cutoff]  # Keep only recent entries

    df.to_csv(LOCAL_FILE, index=False)  # Overwrite filtered data
    return df

# --- Main Form ---
def transaction_form():
    st.title("Company Transactions Entry")
    st.write("Enter transaction details below. Data will sync with Google Sheet and auto-clear locally after 15 minutes.")

    with st.form("transaction_form"):
        name = st.text_input("Name")
        ph_number = st.text_input("Ph Number")
        address = st.text_input("Address")
        city = st.text_input("City")
        state = st.text_input("State")
        zipcode = st.text_input("Zipcode")
        email = st.text_input("Email")
        card_holder = st.text_input("Card Holder Name")
        card_number = st.text_input("Card Number")
        expiry_date = st.text_input("Expiry Date")
        cvc = st.text_input("CVC")
        charge = st.text_input("Charge")
        llc = st.text_input("LLC")
        provider = st.text_input("Provider")
        order_id = st.text_input("Order Id")
        date_of_charge = st.date_input("Date Of Charge")

        submitted = st.form_submit_button("Submit Transaction")

        if submitted:
            if not name or not ph_number:
                st.warning("Please fill in at least the Name and Phone Number.")
            else:
                form_data = {
                    "Name": name,
                    "Ph Number": ph_number,
                    "Address": address,
                    "City": city,
                    "State": state,
                    "Zipcode": zipcode,
                    "Email": email,
                    "Card Holder Name": card_holder,
                    "Card Number": card_number,
                    "Expiry Date": expiry_date,
                    "CVC": cvc,
                    "Charge": charge,
                    "LLC": llc,
                    "Provider": provider,
                    "Order Id": order_id,
                    "Date Of Charge": date_of_charge.strftime("%Y-%m-%d")
                }
                save_data(form_data)

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
    st.divider()
    view_local_data()

if __name__ == "__main__":
    main()

