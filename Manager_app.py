import streamlit as st
import gspread
import pandas as pd
from datetime import datetime, timedelta
import pytz
import requests

def send_pushbullet_notification(title, message):
    try:
        access_token = st.secrets["pushbullet_token"]
        headers = {"Access-Token": access_token, "Content-Type": "application/json"}
        data = {"type": "note", "title": title, "body": message}
        response = requests.post("https://api.pushbullet.com/v2/pushes", json=data, headers=headers)
        if response.status_code != 200:
            st.warning("Pushbullet notification failed to send.")
    except Exception as e:
        st.error(f"Pushbullet error: {e}")

# --- CONFIG ---
st.set_page_config(page_title="Manager Dashboard", layout="wide")
tz = pytz.timezone("Asia/Karachi")

# --- GOOGLE SHEET SETUP ---
creds = st.secrets["gcp_service_account"]
gc = gspread.service_account_from_dict(creds)
SHEET_NAME = "Company_Transactions"

# Access the two worksheets
spectrum_ws = gc.open(SHEET_NAME).worksheet("Sheet1")
insurance_ws = gc.open(SHEET_NAME).worksheet("Sheet2")

# --- REFRESH BUTTON ---
if st.button("Refresh Now"):
    st.rerun()

# --- LOAD DATA FUNCTION ---
def load_data(ws):
    records = ws.get_all_records()
    df = pd.DataFrame(records)

    # Ensure 'Expiry Date' keeps leading zeros and no slashes
    if "Expiry Date" in df.columns:
        df["Expiry Date"] = (
            df["Expiry Date"]
            .astype(str)
            .str.replace("/", "", regex=False)  # remove any slashes if present
            .str.strip()
            .str.zfill(4)  # pad with zeros to make sure it's 4 digits
        )

    return df

    return df

# --- FILTER FUNCTION ---
def process_dataframe(df):
    DELETE_AFTER_MINUTES = 5
    if df.empty:
        return df, df
    if "Timestamp" in df.columns:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        df["Timestamp"] = df["Timestamp"].apply(
            lambda x: x.tz_localize(None) if hasattr(x, "tzinfo") and x.tzinfo else x
        )
        now = datetime.now(tz).replace(tzinfo=None)
        cutoff = now - timedelta(minutes=DELETE_AFTER_MINUTES)
        df = df[
            (df["Status"] == "Pending") |
            ((df["Status"].isin(["Charged", "Declined"])) & (df["Timestamp"] >= cutoff))
        ]
    pending = df[df["Status"] == "Pending"]
    processed = df[df["Status"].isin(["Charged", "Declined"])]
    return pending, processed

# --- REUSABLE COMPONENT FUNCTION ---
def render_transaction_tabs(df, worksheet, label):
    DELETE_AFTER_MINUTES = 5
    pending, processed = process_dataframe(df)
    subtab1, subtab2 = st.tabs(["Awaiting Approval", "Processed Transactions"])

    # --- PENDING TAB ---
    with subtab1:
        st.subheader("Pending Transactions")
        if pending.empty:
            st.info("No pending transactions.")
        else:
            for i, row in pending.iterrows():
                with st.expander(f"{row['Agent Name']} — {row['Charge']} ({row['LLC']})"):
                    st.write(f"**Card Number:** {row['Card Number']}")
                    st.write(f"**Expiry Date:** {row['Expiry Date']}")
                    st.write(f"**Charge:** {row['Charge']}")
                    # Safely split the Card Holder Name
                    card_holder = str(row.get('Card Holder Name', '')).strip()
                    name_parts = card_holder.split()
                    
                    first_name = name_parts[0] if len(name_parts) > 0 else ''
                    last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                    
                    st.write(f"**First Name:** {first_name}")
                    st.write(f"**Last Name:** {last_name}")

                    st.write(f"**Address:** {row['Address']}")
                    st.write(f"**CVC:** {row['CVC']}")
                    st.write(f"**Card Holder Name:** {card_holder}")

                    row_number = i + 2  # header is row 1
                    col_number = df.columns.get_loc("Status") + 1

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Approve", key=f"approve_{label}_{i}"):
                            worksheet.update_cell(row_number, col_number, "Charged")
                            message = (
                                f"Charge: {row.get('Charge', 'Nil')}\n"
                                f"Client Name: {row.get('Name', 'Nil')}\n"
                                f"Phone Number: {row.get('Ph Number', 'Nil')}\n"
                                f"Address: {row.get('Address', 'Nil')}\n"
                                f"Email: {row.get('Email', 'Nil')}\n"
                                f"Provider: {row.get('Provider', 'Nil')}"
                            )
                            send_pushbullet_notification("Transaction Approved ✅", message)
                            st.success("Approved successfully!")
                            st.rerun()
                    with col2:
                        if st.button("Decline", key=f"decline_{label}_{i}"):
                            worksheet.update_cell(row_number, col_number, "Declined")
                            st.error("Declined successfully!")
                            st.rerun()

    # --- PROCESSED TAB ---
    with subtab2:
        st.subheader(f"Processed Transactions (last {DELETE_AFTER_MINUTES} minutes)")
        if processed.empty:
            st.info("No processed transactions yet.")
        else:
            st.dataframe(processed)

st.title("Manager Transaction Dashboard")

# --- LOAD DATA FOR BOTH SHEETS ---
df_spectrum = load_data(spectrum_ws)
df_insurance = load_data(insurance_ws)

main_tab1, main_tab2 = st.tabs(["Spectrum", "Insurance"])

# --- SPECTRUM TAB ---
with main_tab1:
    render_transaction_tabs(df_spectrum, spectrum_ws, "spectrum")

# --- INSURANCE TAB ---
with main_tab2:
    render_transaction_tabs(df_insurance, insurance_ws, "insurance")
