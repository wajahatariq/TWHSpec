import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, timedelta
import os

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Company Transactions Entry", layout="wide")

GOOGLE_SHEET_NAME = "Company_Transactions"
LOCAL_FILE = "user_temp_inventory.csv"
DELETE_AFTER_MINUTES = 15  # Auto delete old entries

AGENTS = ["Select Agent", "Arham Kaleem", "Arham Ali", "Haziq", "Usama", "Areeb"]
LLC_OPTIONS = ["Select LLC", "Bite Bazaar LLC", "Apex Prime Solutions"]

COLUMN_ORDER = [
    "Agent Name",
    "Name",
    "Ph Number",
    "Address",
    "Email",
    "Card Holder Name",
    "Card Number",
    "Expiry Date",
    "CVC",
    "Charge",
    "LLC",
    "Provider",
    "Order Id",
    "Date Of Charge",
    "Timestamp",
    "Status"
]

# ---------------- Google Sheets ----------------
def connect_google_sheet():
    gc = gspread.service_account(filename="forimage-466607-0d33a2e71146.json")
    sh = gc.open(GOOGLE_SHEET_NAME)
    return sh.sheet1

# ---------------- Ensure Local CSV ----------------
def ensure_local_file():
    if not os.path.exists(LOCAL_FILE):
        pd.DataFrame(columns=COLUMN_ORDER).to_csv(LOCAL_FILE, index=False)

# ---------------- Save locally ----------------
def save_local(form_data):
    form_data["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    form_data["Status"] = "Pending"
    ensure_local_file()
    df = pd.read_csv(LOCAL_FILE)
    df = pd.concat([df, pd.DataFrame([form_data])], ignore_index=True)
    df.to_csv(LOCAL_FILE, index=False)

# ---------------- Push to Google Sheet ----------------
def push_to_google_sheet(record):
    try:
        ws = connect_google_sheet()
        existing_headers = ws.row_values(1)
        if not existing_headers:
            ws.insert_row(COLUMN_ORDER, 1)
        row_data = [record.get(col, "") for col in COLUMN_ORDER]
        ws.append_row(row_data, value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        st.sidebar.error(f"Failed to push to Google Sheet: {e}")
        return False

# ---------------- Clean old local entries ----------------
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

# ---------------- Transaction Form ----------------
def transaction_form():
    st.title("Company Transactions Entry")
    st.caption("Fill transaction details. Data saved locally as Pending first.")

    with st.form("transaction_form", clear_on_submit=True):
        agent_name = st.selectbox("Agent Name", AGENTS)
        name = st.text_input("Name")
        ph_number = st.text_input("Ph Number")
        address = st.text_input("Address")  # Single address column
        email = st.text_input("Email")
        card_holder = st.text_input("Card Holder Name")
        card_number = st.text_input("Card Number")
        expiry_date = st.text_input("Expiry Date")
        cvc = st.text_input("CVC")
        charge = st.text_input("Charge")
        llc = st.selectbox("LLC", LLC_OPTIONS)
        provider = st.text_input("Provider")
        order_id = st.text_input("Order Id")
        date_of_charge = st.date_input("Date Of Charge")

        submitted = st.form_submit_button("Submit Transaction")

        if submitted:
            if not name or not ph_number or agent_name == "Select Agent" or llc == "Select LLC":
                st.warning("Please fill in Name, Phone Number, select an Agent, and select an LLC.")
            else:
                form_data = {
                    "Agent Name": agent_name,
                    "Name": name,
                    "Ph Number": ph_number,
                    "Address": address,
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
                save_local(form_data)
                st.success("✅ Entry saved locally as Pending. Manage it in the sidebar now.")

# ---------------- Sidebar: Manage Pending Entries ----------------
def manage_pending():
    st.sidebar.header("Pending Transactions")
    df = clean_old_entries()
    pending = df[df["Status"] == "Pending"].reset_index(drop=True)
    num_pending = len(pending)

    if num_pending == 0:
        st.sidebar.info("No pending entries.")
        st.session_state.selected_entries = []
        return

    if "selected_entries" not in st.session_state or len(st.session_state.selected_entries) != num_pending:
        st.session_state.selected_entries = [False] * num_pending

    selected_indices = []
    for i, row in pending.iterrows():
        st.session_state.selected_entries[i] = st.sidebar.checkbox(
            f"{row['Name']} ({row['Ph Number']})",
            value=st.session_state.selected_entries[i]
        )
        if st.session_state.selected_entries[i]:
            selected_indices.append(i)

    new_status = st.sidebar.radio("Update status to:", ["Charged", "Declined"], horizontal=True)

    if st.sidebar.button("✅ Finalize Selected"):
        if not selected_indices:
            st.sidebar.warning("Select entries first!")
        else:
            for idx in selected_indices:
                original_index = pending.index[idx]
                df.at[original_index, "Status"] = new_status
                record = df.loc[original_index].apply(lambda x: str(x) if pd.notnull(x) else "").to_dict()
                push_to_google_sheet(record)

            df.to_csv(LOCAL_FILE, index=False)
            st.sidebar.success(f"{len(selected_indices)} entries updated to '{new_status}' and pushed to Google Sheet ✅")
            st.session_state.selected_entries = [False] * num_pending

# ---------------- Display Local Data ----------------
def view_local_data():
    st.subheader(f"Local Transactions (last {DELETE_AFTER_MINUTES} mins)")
    df = clean_old_entries()
    if df.empty:
        st.info("No recent transactions.")
    else:
        st.dataframe(df)

# ---------------- Main ----------------
def main():
    ensure_local_file()
    transaction_form()
    st.divider()
    view_local_data()
    manage_pending()

if __name__ == "__main__":
    main()
