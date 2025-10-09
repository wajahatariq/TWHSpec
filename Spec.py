import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, timedelta
import os

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Company Transactions Entry", layout="wide")

GOOGLE_SHEET_NAME = "Company_Transactions"
LOCAL_FILE = "user_temp_inventory.csv"
DELETE_AFTER_MINUTES = 500  # change to 5 in production

COLUMN_ORDER = [
    "Agent Name",
    "Name",
    "Ph Number",
    "Complete Address",
    "Email",
    "Card Holder Name",
    "Card Number",
    "Expiry Date",
    "CVC",
    "Charge",
    "LLC",
    "Date Of Charge",
    "Timestamp",
    "Status"
]

AGENTS = ["Select Agent", "Arham Kaleem", "Arham Ali", "Haziq", "Usama", "Areeb"]
LLC = ["Select LLC", "Bite Bazaar LLC", "Apex Prime Solutions"]

# ---------------- Google Sheets connection ----------------
def connect_google_sheet():
    try:
        creds = st.secrets["gcp_service_account"]
        gc = gspread.service_account_from_dict(creds)
    except Exception:
        gc = gspread.service_account(filename="forimage-466607-0d33a2e71146.json")
    sh = gc.open(GOOGLE_SHEET_NAME)
    return sh.sheet1

# ---------------- Ensure local CSV header ----------------
def ensure_local_header():
    if not os.path.exists(LOCAL_FILE):
        pd.DataFrame(columns=COLUMN_ORDER).to_csv(LOCAL_FILE, index=False)

# ---------------- Save locally (Pending) ----------------
def save_local(form_data):
    now_iso = datetime.now().isoformat()
    form_data["Timestamp"] = now_iso
    form_data["Status"] = "Pending"
    ensure_local_header()
    df = pd.read_csv(LOCAL_FILE)
    df = pd.concat([df, pd.DataFrame([form_data])], ignore_index=True)
    df.to_csv(LOCAL_FILE, index=False)

# ---------------- Push approved/declined record to Google Sheet ----------------
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
        st.sidebar.error(f"❌ Failed to push to Google Sheet: {e}")
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
    st.title("Client Management System")
    st.caption("Fill the form below. Multiple entries can be saved as Pending before approval.")

    with st.form("transaction_form", clear_on_submit=True):
        agent_name = st.selectbox("Agent Name", AGENTS)
        name = st.text_input("Name")
        ph_number = st.text_input("Ph Number")
        complete_address = st.text_input("Complete Address (Address, City, State, Zipcode)")
        email = st.text_input("Email")
        card_holder = st.text_input("Card Holder Name")
        card_number = st.text_input("Card Number")
        expiry_date = st.text_input("Expiry Date")
        cvc = st.text_input("CVC")
        charge = st.text_input("Charge")
        llc = st.selectbox("LLC", LLC)
        date_of_charge = st.date_input("Date Of Charge")
        submitted = st.form_submit_button("Submit Details")

        if submitted:
            if not name or not ph_number or agent_name == "Select Agent":
                st.warning("⚠️ Please fill in Name, Phone Number, and select an Agent.")
            else:
                form_data = {
                    "Agent Name": agent_name,
                    "Name": name,
                    "Ph Number": ph_number,
                    "Complete Address": complete_address,
                    "Email": email,
                    "Card Holder Name": card_holder,
                    "Card Number": card_number,
                    "Expiry Date": expiry_date,
                    "CVC": cvc,
                    "Charge": charge,
                    "LLC": llc,
                    "Date Of Charge": date_of_charge.strftime("%Y-%m-%d"),
                }
                save_local(form_data)
                st.success("✅ Entry saved locally as Pending. You can manage it in the sidebar now.")

# ---------------- Display Local Entries ----------------
def view_local_data():
    st.subheader(f"Local Records (Auto-clears after {DELETE_AFTER_MINUTES} minutes)")
    df = clean_old_entries()
    if df.empty:
        st.info("No entries found.")
    else:
        st.dataframe(df)
    return df

# ---------------- Sidebar: Manage Status with Bulk Update ----------------
def manage_status():
    st.sidebar.header("Manage Pending Entries")

    # Always read fresh CSV immediately after saving
    if os.path.exists(LOCAL_FILE):
        df = pd.read_csv(LOCAL_FILE)
    else:
        df = pd.DataFrame(columns=COLUMN_ORDER)

    # Only consider Pending entries
    pending_entries = df[df["Status"] == "Pending"].reset_index(drop=True)
    num_pending = len(pending_entries)

    if num_pending == 0:
        st.sidebar.info("No pending entries to manage.")
        st.session_state.selected_entries = []
        return

    st.sidebar.subheader(f"Pending Entries ({num_pending})")

    # Initialize checkboxes if not in session_state or length changed
    if ("selected_entries" not in st.session_state) or (len(st.session_state.selected_entries) != num_pending):
        st.session_state.selected_entries = [False] * num_pending

    selected_indices = []
    for i, row in pending_entries.iterrows():
        st.session_state.selected_entries[i] = st.sidebar.checkbox(
            f"{row['Name']} ({row['Ph Number']})",
            value=st.session_state.selected_entries[i]
        )
        if st.session_state.selected_entries[i]:
            selected_indices.append(i)

    new_status = st.sidebar.radio("Update status to:", ["Charged", "Declined"], horizontal=True)

    if st.sidebar.button("✅ Finalize Selected Entries"):
        if not selected_indices:
            st.sidebar.warning("⚠️ No entries selected!")
        else:
            for idx in selected_indices:
                original_index = pending_entries.index[idx]
                df.at[original_index, "Status"] = new_status
                record = df.loc[original_index].apply(lambda x: str(x) if pd.notnull(x) else "").to_dict()
                push_to_google_sheet(record)

            df.to_csv(LOCAL_FILE, index=False)
            st.sidebar.success(f"{len(selected_indices)} entries updated to '{new_status}' and pushed to Google Sheet ✅")
            # Reset checkboxes for next iteration
            st.session_state.selected_entries = [False] * num_pending


# ---------------- Main ----------------
def main():
    ensure_local_header()
    transaction_form()
    st.divider()
    view_local_data()
    manage_status()

if __name__ == "__main__":
    main()

