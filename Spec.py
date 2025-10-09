import gspread
from datetime import datetime, timedelta
import os
import pytz

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Company Transactions Entry", layout="wide")

GOOGLE_SHEET_NAME = "Company_Transactions"
LOCAL_FILE = "user_temp_inventory.csv"
DELETE_AFTER_MINUTES = 5
DELETE_AFTER_MINUTES = 500  # for testing (you can set to 5 later)

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
    st.success("✅ Entry saved locally (Pending review). You can add another now.")

# ---------------- GOOGLE SHEET AUTH ----------------
gc = gspread.service_account(filename="credentials.json")

# ---------------- LOAD LOCAL FILE ----------------
if os.path.exists(LOCAL_FILE):
    df = pd.read_csv(LOCAL_FILE)
else:
    df = pd.DataFrame(columns=["Name", "Ph Number", "Amount", "Card Number", "CVC", "Timestamp", "Status"])
# ---------------- Push approved/declined record to Google Sheet ----------------
def push_to_google_sheet(record):
    try:
        ws = connect_google_sheet()
        existing_headers = ws.row_values(1)

# Remove old records (auto cleanup)
now = datetime.now(pytz.timezone("Asia/Karachi"))
if not df.empty:
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    df = df[df["Timestamp"] > now - timedelta(minutes=DELETE_AFTER_MINUTES)]
    df.to_csv(LOCAL_FILE, index=False)
        if not existing_headers:
            ws.insert_row(COLUMN_ORDER, 1)

# ---------------- FORM SECTION ----------------
st.header("Enter Transaction")
        row_data = [record.get(col, "") for col in COLUMN_ORDER]
        ws.append_row(row_data, value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        st.sidebar.error(f"❌ Failed to push to Google Sheet: {e}")
        return False

with st.form("entry_form", clear_on_submit=True):
    name = st.text_input("Name")
    phone = st.text_input("Phone Number")
    amount = st.text_input("Amount")
    card = st.text_input("Card Number")
    cvc = st.text_input("CVC")

    submit = st.form_submit_button("Save Entry")
# ---------------- Clean old local entries ----------------
def clean_old_entries():
    if not os.path.exists(LOCAL_FILE):
        return pd.DataFrame(columns=COLUMN_ORDER)

if submit:
    if not all([name, phone, amount, card, cvc]):
        st.error("Please fill all fields.")
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
    st.caption("Fill the form below. Multiple entries can be saved before approval.")

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
                save_local(form_data)


# ---------------- Display Local Entries ----------------
def view_local_data():
    st.subheader(f"Local Records (Auto-clears after {DELETE_AFTER_MINUTES} minutes)")
    df = clean_old_entries()
    if df.empty:
        st.info("No entries found.")
else:
        new_entry = {
            "Name": name,
            "Ph Number": phone,
            "Amount": amount,
            "Card Number": card,
            "CVC": cvc,
            "Timestamp": now.isoformat(),
            "Status": "Pending"
        }
        st.dataframe(df)
    return df


        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        df.to_csv(LOCAL_FILE, index=False)
        st.success(f"✅ Entry saved locally for {name}")
# ---------------- Sidebar: Manage Status ----------------
def manage_status(df):
    st.sidebar.header("⚙️ Manage Pending Entries")

# ---------------- SIDEBAR SECTION ----------------
st.sidebar.header(f"Manage Pending Entries ({len(df)})")
    if df.empty:
        st.sidebar.info("No entries to manage yet.")
        return

if not df.empty:
    # Show dropdown of all pending names
    names = df["Name"].tolist()
    selected_name = st.sidebar.selectbox("Select client:", ["-- Select --"] + names)
    pending_entries = df[df["Status"] == "Pending"]

    if selected_name != "-- Select --":
        entry = df[df["Name"] == selected_name].iloc[0]
    if pending_entries.empty:
        st.sidebar.info("All entries processed ✅")
        return

        st.sidebar.write(f"**Phone:** {entry['Ph Number']}")
        st.sidebar.write(f"**Amount:** {entry['Amount']}")
        st.sidebar.write(f"**Card:** {entry['Card Number']}")
        st.sidebar.write(f"**CVC:** {entry['CVC']}")
    entry_labels = [f"{row['Name']} ({row['Ph Number']})" for _, row in pending_entries.iterrows()]
    selected_index = st.sidebar.selectbox("Select entry:", pending_entries.index, format_func=lambda i: entry_labels[pending_entries.index.get_loc(i)])

        status_choice = st.sidebar.radio("Update Status to:", ["Charged", "Declined"], horizontal=True)
    new_status = st.sidebar.radio("Update status to:", ["Charged", "Declined"], horizontal=True)

        if st.sidebar.button("Update Status"):
            try:
                # Update in local df
                df.loc[df["Name"] == selected_name, "Status"] = status_choice
    if st.sidebar.button("✅ Finalize Entry"):
        # Update local status
        df.at[selected_index, "Status"] = new_status

                # Push that record to Google Sheet
                record = df[df["Name"] == selected_name].copy()
                record = record.astype(str).iloc[0].tolist()
        # Prepare for Google upload
        record = df.loc[selected_index].apply(lambda x: str(x) if pd.notnull(x) else "").to_dict()

                sheet = gc.open(GOOGLE_SHEET_NAME).sheet1
                sheet.append_row(record)
        # Push to Google Sheets
        success = push_to_google_sheet(record)

                # Remove from local pending
                df = df[df["Name"] != selected_name]
                df.to_csv(LOCAL_FILE, index=False)
        if success:
            df.to_csv(LOCAL_FILE, index=False)
            st.sidebar.success(f"Status updated to '{new_status}' and saved to Google Sheet ✅")
            st.experimental_rerun()

                st.sidebar.success(f"✅ {selected_name} marked as {status_choice} and saved to Google Sheet")

                st.rerun()
# ---------------- Main ----------------
def main():
    ensure_local_header()
    transaction_form()
    st.divider()
    df = view_local_data()
    manage_status(df)

            except Exception as e:
                st.sidebar.error(f"❌ Failed to update Google Sheet: {e}")

else:
    st.sidebar.info("No pending entries found.")
if __name__ == "__main__":
    main()
