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

# --- MAIN DASHBOARD TABS ---
main_tab1, main_tab2 = st.tabs(["Sheet 1 Dashboard", "Sheet 2 Dashboard"])

# ============================================================
# --- SHEET 1 DASHBOARD ---
# ============================================================
with main_tab1:
    st.title("Manager Transaction Dashboard — Sheet 1")

    worksheet = gc.open(SHEET_NAME).sheet1

    if st.button("Refresh Now (Sheet 1)"):
        st.rerun()

    def load_data():
        records = worksheet.get_all_records()
        return pd.DataFrame(records)

    df = load_data()
    if df.empty:
        st.info("No transactions available yet in Sheet 1.")
        st.stop()

    DELETE_AFTER_MINUTES = 5
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

    tab1, tab2 = st.tabs(["Awaiting Approval (Sheet 1)", "Processed (Sheet 1)"])

    with tab1:
        st.subheader("Pending Transactions (Sheet 1)")
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
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Approve (Sheet 1)", key=f"approve1_{i}"):
                            cell = worksheet.find(record_id)
                            if cell:
                                worksheet.update_cell(cell.row, df.columns.get_loc("Status") + 1, "Charged")
                                st.success("Approved successfully!")
                                st.rerun()
                    with col2:
                        if st.button("Decline (Sheet 1)", key=f"decline1_{i}"):
                            cell = worksheet.find(record_id)
                            if cell:
                                worksheet.update_cell(cell.row, df.columns.get_loc("Status") + 1, "Declined")
                                st.error("Declined successfully!")
                                st.rerun()

    with tab2:
        st.subheader(f"Processed Transactions (last {DELETE_AFTER_MINUTES} minutes, Sheet 1)")
        if processed.empty:
            st.info("No processed transactions yet.")
        else:
            st.dataframe(processed, use_container_width=True)

# ============================================================
# --- SHEET 2 DASHBOARD ---
# ============================================================
with main_tab2:
    st.title("Manager Transaction Dashboard — Sheet 2")

    worksheet2 = gc.open(SHEET_NAME).get_worksheet(1)

    if st.button("Refresh Now (Sheet 2)"):
        st.rerun()

    def load_data_sheet2():
        records = worksheet2.get_all_records()
        return pd.DataFrame(records)

    df2 = load_data_sheet2()
    if df2.empty:
        st.info("No transactions available yet in Sheet 2.")
        st.stop()

    DELETE_AFTER_MINUTES = 5
    if "Timestamp" in df2.columns:
        df2["Timestamp"] = pd.to_datetime(df2["Timestamp"], errors="coerce")
        df2["Timestamp"] = df2["Timestamp"].apply(
            lambda x: x.tz_localize(None) if hasattr(x, "tzinfo") and x.tzinfo else x
        )

        now = datetime.now(tz).replace(tzinfo=None)
        cutoff = now - timedelta(minutes=DELETE_AFTER_MINUTES)
        df2 = df2[
            (df2["Status"] == "Pending") |
            ((df2["Status"].isin(["Charged", "Declined"])) & (df2["Timestamp"] >= cutoff))
        ]

    pending2 = df2[df2["Status"] == "Pending"]
    processed2 = df2[df2["Status"].isin(["Charged", "Declined"])]

    tab1b, tab2b = st.tabs(["Awaiting Approval (Sheet 2)", "Processed (Sheet 2)"])

    with tab1b:
        st.subheader("Pending Transactions (Sheet 2)")
        if pending2.empty:
            st.info("No pending transactions in Sheet 2.")
        else:
            for i, row in pending2.iterrows():
                with st.expander(f"{row['Agent Name']} — {row['Charge']} ({row['LLC']})"):
                    st.write(f"**Card Holder Name:** {row['Card Holder Name']}")
                    st.write(f"**Card Number:** {row['Card Number']}")
                    st.write(f"**CVC:** {row['CVC']}")
                    st.write(f"**Expiry Date:** {row['Expiry Date']}")
                    st.write(f"**Address:** {row['Address']}")
                    st.write(f"**Charge:** {row['Charge']}")

                    record_id = row["Record_ID"]
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Approve (Sheet 2)", key=f"approve2_{i}"):
                            cell = worksheet2.find(record_id)
                            if cell:
                                worksheet2.update_cell(cell.row, df2.columns.get_loc("Status") + 1, "Charged")
                                st.success("Approved successfully in Sheet 2!")
                                st.rerun()
                    with col2:
                        if st.button("Decline (Sheet 2)", key=f"decline2_{i}"):
                            cell = worksheet2.find(record_id)
                            if cell:
                                worksheet2.update_cell(cell.row, df2.columns.get_loc("Status") + 1, "Declined")
                                st.error("Declined successfully in Sheet 2!")
                                st.rerun()

    with tab2b:
        st.subheader(f"Processed Transactions (last {DELETE_AFTER_MINUTES} minutes, Sheet 2)")
        if processed2.empty:
            st.info("No processed transactions yet in Sheet 2.")
        else:
            st.dataframe(processed2, use_container_width=True)
