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
# --- FILTER OUT OLD PROCESSED (ONLY LOCALLY) ---
DELETE_AFTER_MINUTES = 5
if "Timestamp" in df.columns:
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")

    # Normalize timezone safely — make all timestamps naive (no tz)
    df["Timestamp"] = df["Timestamp"].apply(
        lambda x: x.tz_localize(None) if hasattr(x, "tzinfo") and x.tzinfo else x
    )

    now = datetime.now(tz).replace(tzinfo=None)
    cutoff = now - timedelta(minutes=DELETE_AFTER_MINUTES)

    # Keep Pending + recently processed (last 5 min)
    df = df[
        (df["Status"] == "Pending") |
        ((df["Status"].isin(["Charged", "Declined"])) & (df["Timestamp"] >= cutoff))
    ]

# --- FILTERING ---
pending = df[df["Status"] == "Pending"]
processed = df[df["Status"].isin(["Charged", "Declined"])]

# --- MAIN TAB ---
# --- MAIN TAB ---
main_tab1, main_tab2 = st.tabs(["Spectrum", "Insurance"])

# --- FUNCTION TO RENDER SUBTABS (to reuse logic) ---
def render_transaction_tabs(pending_df, processed_df):
    subtab1, subtab2 = st.tabs(["Awaiting Approval", "Processed Transactions"])

    # --- PENDING TAB ---
    with subtab1:
        st.subheader("Pending Transactions")
        if pending_df.empty:
            st.info("No pending transactions.")
        else:
            for i, row in pending_df.iterrows():
                with st.expander(f"{row['Agent Name']} — {row['Charge']} ({row['LLC']})"):
                    st.write(f"**Card Holder Name:** {row['Card Holder Name']}")
                    st.write(f"**Card Number:** {row['Card Number']}")
                    st.write(f"**CVC:** {row['CVC']}")
                    st.write(f"**Expiry Date:** {row['Expiry Date']}")
                    st.write(f"**Address:** {row['Address']}")
                    st.write(f"**Charge:** {row['Charge']}")

                    row_number = i + 2  # 1 for header, 1 for 1-based index
                    col_number = df.columns.get_loc("Status") + 1

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Approve", key=f"approve_{i}_{row['LLC']}"):
                            worksheet.update_cell(row_number, col_number, "Charged")
                            st.success("Approved successfully!")
                            st.rerun()
                    with col2:
                        if st.button("Decline", key=f"decline_{i}_{row['LLC']}"):
                            worksheet.update_cell(row_number, col_number, "Declined")
                            st.error("Declined successfully!")
                            st.rerun()

    # --- PROCESSED TAB ---
    with subtab2:
        st.subheader(f"Processed Transactions (last {DELETE_AFTER_MINUTES} minutes)")
        if processed_df.empty:
            st.info("No processed transactions yet.")
        else:
            st.dataframe(processed_df)

# --- SPECTRUM TAB CONTENT ---
with main_tab1:
    render_transaction_tabs(pending, processed)

# --- INSURANCE TAB CONTENT ---
with main_tab2:
    render_transaction_tabs(pending, processed)
