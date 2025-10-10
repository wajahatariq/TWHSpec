import streamlit as st
import pandas as pd
import gspread
from datetime import datetime
import pytz

# Google Sheets setup
creds = st.secrets["gcp_service_account"]
gc = gspread.service_account_from_dict(creds)
sheet = gc.open("Company_Transactions").sheet1

tz = pytz.timezone("Asia/Karachi")

st.set_page_config(page_title="Agent - Company Transactions", layout="wide")

AGENTS = ["Select Agent", "Arham Kaleem", "Arham Ali", "Haziq", "Usama", "Areeb"]
LLC_OPTIONS = ["Select LLC", "Bite Bazaar LLC", "Apex Prime Solutions"]

st.title("🧾 Agent Transaction Entry")
st.write("Fill the form below to add a new client transaction.")

with st.form("transaction_form"):
    col1, col2 = st.columns(2)

    with col1:
        agent_name = st.selectbox("Agent Name", AGENTS)
        name = st.text_input("Client Name")
        ph_number = st.text_input("Phone Number")
        address = st.text_input("Address")
        email = st.text_input("Email")
        card_holder = st.text_input("Card Holder Name")

    with col2:
        card_number = st.text_input("Card Number")
        expiry_date = st.text_input("Expiry Date (MM/YYYY)")
        cvc = st.text_input("CVC")
        charge = st.text_input("Charge Amount")
        llc = st.selectbox("LLC", LLC_OPTIONS)
        date_of_charge = st.date_input("Date Of Charge")

    submitted = st.form_submit_button("Submit Transaction")

    if submitted:
        if not all([agent_name != "Select Agent", name, ph_number, address, email,
                    card_holder, card_number, expiry_date, cvc, charge, llc != "Select LLC"]):
            st.warning("Please fill in all fields.")
        else:
            form_data = [
                agent_name,
                name,
                ph_number,
                address,
                email,
                card_holder,
                card_number,
                expiry_date,
                cvc,
                charge,
                llc,
                date_of_charge.strftime("%Y-%m-%d"),
                "Pending",
                datetime.now(tz).strftime("%Y-%m-%d %I:%M:%S %p")
            ]
            sheet.append_row(form_data)
            st.success(f"✅ Transaction for {name} submitted successfully.")
