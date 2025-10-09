import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, timedelta
import os
import pytz

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Company Transactions Entry", layout="wide")

GOOGLE_SHEET_NAME = "Company_Transactions"
LOCAL_FILE = "user_temp_inventory.csv"
DELETE_AFTER_MINUTES = 5  # Local records auto-delete after X minutes

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
    "Status",
    "Timestamp",
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
    now_iso = datetime.now(pytz.timezone("Asia/Karachi")).strftime("%Y-%m-%d %H:%M:%S")
    form_data["Status"] = "Pending"

    row = [form_data.get(col, "") if col != "Timestamp" else now_iso for col in COLUMN_ORDER]

    try:
        ws = connect_google_sheet()
        ws.append_row(row, value_input_option="USER_ENTERED")
        st.success("Saved to Google Sheet.")
    except Exception as e:
        st.error(f"Failed to save to Google Sheet: {e}")

    ensure_local_header()
    pd.DataFrame([dict(zip(COLUMN_ORDER, row))]).to_csv(
        LOCAL_FILE, mode="a", header=False, index=False
    )
    st.info("Saved locally (temporary).")

def update_status_in_files(name, ph_number, new_status):
    df = pd.read_csv(LOCAL_FILE)
    match = (df["Name"] == name) & (df["Ph Number"] == ph_number)
    df.loc[match, "Status"] = new_status
    df.to_csv(LOCAL_FILE, index=False)

    try:
        ws = connect_google_sheet()
        records = ws.get_all_records()
        for i, rec in enumerate(records):
            if rec["Name"] == name and rec["Ph Number"] == ph_number:
                ws.update_cell(i + 2, COLUMN_ORDER.index("Status") + 1, new_status)
                break
        st.success(f"Status updated to {new_status}")
    except Exception as e:
        st.error(f"Failed to update Google Sheet: {e}")


# ---------------- Clean expired local entries ----------------
def clean_old_entries():
    if not os.path.exists(LOCAL_FILE):
        return pd.DataFrame(columns=COLUMN_ORDER)

    df = pd.read_csv(LOCAL_FILE)
    if "Timestamp" not in df.columns:
        return df

    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    cutoff = datetime.now(pytz.timezone("Asia/Karachi")) - timedelta(minutes=DELETE_AFTER_MINUTES)
    df = df[df["Timestamp"] > cutoff]
    df.to_csv(LOCAL_FILE, index=False)
    return df


def update_status_in_files(row_index, new_status):
    # Update local CSV
    df = pd.read_csv(LOCAL_FILE)
    if row_index >= len(df):
        st.error("Invalid row index.")
        return

    df.at[row_index, "Status"] = new_status
    df.to_csv(LOCAL_FILE, index=False)

    # Update Google Sheet
    try:
        ws = connect_google_sheet()
        records = ws.get_all_records()
        if row_index < len(records):
            ws.update_cell(row_index + 2, COLUMN_ORDER.index("Status") + 1, new_status)
        st.success(f"Status updated to {new_status}")
    except Exception as e:
        st.error(f"Failed to update Google Sheet: {e}")


# ---------------- UI: transaction form ----------------
def transaction_form():
    st.title("Client Management System")
    st.write(
        "Fill the form. Data is saved to Google Sheet (permanent) and to a temporary local CSV (cleared automatically after 5 minutes) ."
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
        llc = st.selectbox("LLC",LLC)
        date_of_charge = st.date_input("Date Of Charge")

        submitted = st.form_submit_button("Submit Details")

        if submitted:
            # ✅ proper validation inside the form
            if not name or not ph_number or agent_name == "Select Agent":
                st.warning("Please fill in Name, Phone Number, and select an Agent.")
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
    st.subheader(f"Recent Entries (Last {DELETE_AFTER_MINUTES} mins)")
    df = clean_old_entries()

    if df.empty:
        st.info("No recent transactions found.")
        return

    # Create an editable dataframe view
    edited_df = st.data_editor(
        df,
        column_config={
            "Status": st.column_config.Column(
                "Status",
                help="Mark as Charged or Declined",
                width="medium"
            )
        },
        disabled=[col for col in df.columns if col != "Status"],
        hide_index=True,
        key="editable_table",
    )

    # Compare before & after edits
    changed_rows = edited_df.loc[edited_df["Status"] != df["Status"]]
    if not changed_rows.empty:
        for _, row in changed_rows.iterrows():
            update_status_in_files(row["Name"], row["Ph Number"], row["Status"])


# ---------------- Main ----------------
def main():
    ensure_local_header()
    transaction_form()
    st.divider()
    view_local_data()

if __name__ == "__main__":
    main()








