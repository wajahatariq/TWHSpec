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
spreadsheet = gc.open(SHEET_NAME)

# ✅ Load both Sheet1 and Sheet2
worksheet1 = spreadsheet.get_worksheet(0)  # Sheet1
worksheet2 = spreadsheet.get_worksheet(1)  # Sheet2

# --- REFRESH BUTTON ---
if st.button("Refresh Now"):
    st.rerun()

# --- LOAD DATA ---
def load_data():
    data1 = worksheet1.get_all_records()
    data2 = worksheet2.get_all_records()

    df1 = pd.DataFrame(data1)
    df2 = pd.DataFrame(data2)

    # ✅ Add sheet name column (optional for tracking)
    if not df1.empty:
        df1["Source Sheet"] = "Sheet1"
    if not df2.empty:
        df2["Source Sheet"] = "Sheet2"

    # Combine both
    if not df1.empty and not df2.empty:
        df = pd.concat([df1, df2], ignore_index=True)
    elif not df1.empty:
        df = df1
    elif not df2.empty:
        df = df2
    else:
        df = pd.DataFrame()

    return df

st.title("Manager Transaction Dashboard")

df = load_data()
if df.empty:
    st.info("No transactions available yet.")
    st.stop()

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
                st.write(f"**Expiry Date:** {row['Expiry Date']}")
                st.write(f"**Address:** {row['Address']}")
                st.write(f"**Charge:** {row['Charge']}")

                record_id = row["Record_ID"]

                # ✅ Decide which sheet to update
                sheet_source = row.get("Source Sheet", "Sheet1")
                target_ws = worksheet1 if sheet_source == "Sheet1" else worksheet2

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Approve", key=f"approve_{i}"):
                        cell = target_ws.find(record_id)
                        if cell:
                            target_ws.update_cell(cell.row, df.columns.get_loc("Status") + 1, "Charged")
                            st.success("Approved successfully!")
                            st.rerun()
                with col2:
                    if st.button("Decline", key=f"decline_{i}"):
                        cell = target_ws.find(record_id)
                        if cell:
                            target_ws.update_cell(cell.row, df.columns.get_loc("Status") + 1, "Declined")
                            st.error("Declined successfully!")
                            st.rerun()

# --- PROCESSED TAB ---
with tab2:
    st.subheader(f"Processed Transactions (last {DELETE_AFTER_MINUTES} minutes)")
    if processed.empty:
        st.info("No processed transactions yet.")
    else:
        st.dataframe(processed, use_container_width=True)
