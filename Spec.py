import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, timedelta
import os

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Company Transactions Entry", layout="wide")

GOOGLE_SHEET_NAME = "Company_Transactions"
LOCAL_FILE = "user_temp_inventory.csv"
DELETE_AFTER_MINUTES = 5

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


# ---------------- Local CSV header helper ----------------
def ensure_local_header():
    if not os.path.exists(LOCAL_FILE):
        pd.DataFrame(columns=COLUMN_ORDER).to_csv(LOCAL_FILE, index=False)


# ---------------- Save a submission ----------------
def save_data(form_data):
    now_iso = datetime.now().isoformat()
    form_data["Timestamp"] = now_iso
    form_data["Status"] = "Pending"

    row_data = [form_data.get(col, "") for col in COLUMN_ORDER]

    # Save to Google Sheet
    try:
        ws = connect_google_sheet()

        # Ensure headers exist
        existing_headers = ws.row_values(1)
        if not existing_headers:
            ws.insert_row(COLUMN_ORDER, 1)

        ws.append_row(row_data, value_input_option="USER_ENTERED")
        st.success("Saved to Google Sheet.")
    except Exception as e:
        st.error(f"Failed to save to Google Sheet: {e}")

    # Save to local CSV
    ensure_local_header()
    pd.DataFrame([form_data]).to_csv(LOCAL_FILE, mode="a", header=False, index=False)
    st.info("Saved locally (temporary).")


# ---------------- Clean expired local entries ----------------
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


# ---------------- UI: transaction form ----------------
def transaction_form():
    st.title("Client Management System")
    st.write(
        "Fill the form. Data is saved to Google Sheet (permanent) and to a temporary local CSV (cleared automatically after 5 minutes)."
    )

    with st.form("transaction_form"):
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
                save_data(form_data)


# ---------------- UI: show temporary local data ----------------
def view_local_data():
    st.subheader(f"Temporary Data (Last {DELETE_AFTER_MINUTES} minutes)")
    df = clean_old_entries()
    if df.empty:
        st.info("No recent transactions found.")
    else:
        st.dataframe(df)
    st.write(f"Loaded {len(df)} entries from local CSV")  # for debugging
    return df


# ---------------- Sidebar: Manage Entry Status ----------------
def manage_status(df):
    st.sidebar.header("Manage Entry Status")

    if df.empty:
        st.sidebar.info("No entries to manage yet.")
        return

    if "Status" not in df.columns:
        df["Status"] = "Pending"

    pending_entries = df[df["Status"] == "Pending"]

    if not pending_entries.empty:
        selected_row = st.sidebar.selectbox(
            "Select a pending entry:",
            pending_entries.index,
            format_func=lambda i: f"{pending_entries.loc[i, 'Name']} ({pending_entries.loc[i, 'Ph Number']})"
        )

        new_status = st.sidebar.radio("Update status to:", ["Charged", "Declined"], horizontal=True)

        if st.sidebar.button("✅ Update Status"):
            selected_timestamp = str(df.loc[selected_row, "Timestamp"])
            df.at[selected_row, "Status"] = new_status
            df.to_csv(LOCAL_FILE, index=False)

            # Update Google Sheet by Timestamp match
            try:
                ws = connect_google_sheet()
                sheet_data = ws.get_all_records()
                for idx, row in enumerate(sheet_data, start=2):
                    if str(row.get("Timestamp")) == selected_timestamp:
                        ws.update_cell(idx, COLUMN_ORDER.index("Status") + 1, new_status)
                        break
                st.sidebar.success(f"Status updated to {new_status}")
            except Exception as e:
                st.sidebar.error(f"Failed to update Google Sheet: {e}")

            st.rerun()
    else:
        st.sidebar.info("All entries have been processed ✅")


# ---------------- Main ----------------
def main():
    ensure_local_header()
    transaction_form()
    st.divider()
    df = view_local_data()
    manage_status(df)


if __name__ == "__main__":
    main()



