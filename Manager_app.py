
spectrum_ws = gc.open(SHEET_NAME).worksheet("Sheet1")
insurance_ws = gc.open(SHEET_NAME).worksheet("Insurance")

# --- REFRESH BUTTON ---
if st.button("Refresh Now"):
    st.rerun()

# --- LOAD DATA FUNCTION ---
def load_data(ws):
    records = ws.get_all_records()
    return pd.DataFrame(records)

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
                    st.write(f"**Card Holder Name:** {row['Card Holder Name']}")
                    st.write(f"**Card Number:** {row['Card Number']}")
                    st.write(f"**CVC:** {row['CVC']}")
                    st.write(f"**Expiry Date:** {row['Expiry Date']}")
                    st.write(f"**Address:** {row['Address']}")
                    st.write(f"**Charge:** {row['Charge']}")

                    row_number = i + 2  # header is row 1
                    col_number = df.columns.get_loc("Status") + 1

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Approve", key=f"approve_{label}_{i}"):
                            worksheet.update_cell(row_number, col_number, "Charged")
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

# --- PAGE TITLE ---
st.title("Manager Transaction Dashboard")

# --- LOAD DATA FOR BOTH SHEETS ---
df_spectrum = load_data(spectrum_ws)
df_insurance = load_data(insurance_ws)

# --- MAIN TABS ---
main_tab1, main_tab2 = st.tabs(["Spectrum", "Insurance"])

# --- SPECTRUM TAB CONTENT ---
with main_tab1:
    render_transaction_tabs(df_spectrum, spectrum_ws, "spectrum")

# --- INSURANCE TAB CONTENT ---
with main_tab2:
    render_transaction_tabs(df_insurance, insurance_ws, "insurance")
