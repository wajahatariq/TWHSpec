import streamlit as st
import gspread
import pandas as pd
from datetime import datetime
import pytz

# --- CONFIG ---
st.set_page_config(page_title="Agent Transactions", layout="wide")
tz = pytz.timezone("Asia/Karachi")

# --- GOOGLE SHEET SETUP ---
creds = st.secrets["gcp_service_account"]
gc = gspread.service_account_from_dict(creds)
SHEET_NAME = "Company_Transactions"
worksheet = gc.open(SHEET_NAME).sheet1

AGENTS = ["Select Agent", "Arham Kaleem", "Arham Ali", "Haziq", "Usama", "Areeb"]
LLC_OPTIONS = ["Select LLC", "Bite Bazaar LLC", "Apex Prime Solutions"]

# --- FORM ---
st.title("Agent Transaction Form")
st.write("Fill out all client details below:")

with st.form("transaction_form"):
    col1, col2 = st.columns(2)
    with col1:
        agent_name = st.selectbox("Agent Name", AGENTS)
        name = st.text_input("Client Name")
        phone = st.text_input("Phone Number")
        address = st.text_input("Address")
        email = st.text_input("Email")
        card_holder = st.text_input("Card Holder Name")
    with col2:
        card_number = st.text_input("Card Number")
        expiry = st.text_input("Expiry Date (MM/YY)")
        cvc = st.text_input("CVC")
        charge = st.text_input("Charge Amount")
        llc = st.selectbox("LLC", LLC_OPTIONS)
        date_of_charge = st.date_input("Date of Charge")

    submitted = st.form_submit_button("Submit")

if submitted:
    if not all([agent_name != "Select Agent", name, phone, address, email,
                card_holder, card_number, expiry, cvc, charge, llc != "Select LLC"]):
        st.warning("⚠️ Please fill in all required fields.")
    else:
        timestamp = datetime.now(tz).strftime("%Y-%m-%d %I:%M:%S %p")
        data = [agent_name, name, phone, address, email, card_holder,
                card_number, expiry, cvc, charge, llc,
                date_of_charge.strftime("%Y-%m-%d"), "Pending", timestamp]

        worksheet.append_row(data)
        st.success(f"✅ Transaction for {name} added successfully!")

        st.experimental_rerun()  # Refresh UI to show new record below


# --- LIVE GOOGLE SHEET VIEW ---
st.divider()
st.subheader("📋 Live Transaction Data")

try:
    # Get all data from the sheet
    data = worksheet.get_all_records()

    if not data:
        st.info("No data found yet.")
    else:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
except Exception as e:
    st.error(f"Error loading data: {e}")
