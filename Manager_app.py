import streamlit as st
import gspread
import pandas as pd
from datetime import datetime, timedelta
import pytz

# --- CONFIG ---
st.set_page_config(page_title="Manager Dashboard", layout="wide")
tz = pytz.timezone("Asia/Karachi")

# --- GOOGLE SHEET SETUP ---
creds = st.secrets["gcp_service_account"]
gc = gspread.service_account_from_dict(creds)
SHEET_NAME = "Company_Transactions"
worksheet = gc.open(SHEET_NAME).sheet1

# --- REFRESH BUTTON ---
if st.button("Refresh Now"):
    st.rerun()

# --- LOAD DATA ---
def load_data():
    records = worksheet.get_all_records()
    return pd.DataFrame(records)

st.title("Manager Transaction Dashboard")

df = load_data()
if df.empty:
    st.info("No transactions available yet.")
    st.stop()

# --- FILTER OUT OLD PROCESSED (ONLY LOCALLY) ---
DELETE_AFTER_MINUTES = 5
if "Timestamp" in df.columns:
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    now = datetime.now(tz)
    cutoff = now - timedelta(minutes=DELETE_AFTER_MINUTES)

    # Keep all Pending + processed within 5 minutes
    df = df[
        (df["Status"] == "Pending") |
        ((df["Status"].isin(["Charged", "Declined"])) & (df["Timestamp"] >= cutoff))
    ]

# --- FILTERING ---
pending = df[df["Status"] == "Pending"]
processed = df[df["Status"].isin(["Charged", "Declined"])]

# --- TABS ---
tab1, tab2 = st.tabs(["Awaiting Approval", "Processed Transactions"])

# --- PENDING TAB ---
with tab1:
    st.subheader("Pending Transactions")
    if pending.empty:
        st.info("No pending transactions.")
    else:
        for i, row in pending.iterrows():
            with st.expander(f"{row['Agent Name']} — {row['Charge']} ({row['LLC']})"):
                st.write(f"**Card Holder Name:** {row['Card Holder Name']}")
                st.write(f"**Card Number:** {row['Card Number']}")
                st.write(f"**CVC:** {row['CVC']}")
                st.write(f"**Address:** {row['Address']}")
                st.write(f"**Charge:** {row['Charge']}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Approve", key=f"approve_{i}"):
                        worksheet.update_cell(i + 2, df.columns.get_loc("Status") + 1, "Charged")
                        st.success("Approved successfully!")
                        st.rerun()
                with col2:
                    if st.button(f"Decline", key=f"decline_{i}"):
                        worksheet.update_cell(i + 2, df.columns.get_loc("Status") + 1, "Declined")
                        st.error("Declined successfully!")
                        st.rerun()

# --- PROCESSED TAB ---
with tab2:
    st.subheader(f"Processed Transactions (last {DELETE_AFTER_MINUTES} minutes)")
    if processed.empty:
        st.info("No processed transactions yet.")
    else:
        st.dataframe(processed)
