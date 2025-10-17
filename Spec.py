import streamlit as st
import gspread
import pandas as pd
from datetime import datetime, timedelta
import pytz
import json
import uuid
import requests
# --- CONFIG ---
st.set_page_config(page_title="Client Management System", layout="wide")
tz = pytz.timezone("Asia/Karachi")

# --- GOOGLE SHEET SETUP ---
creds = st.secrets["gcp_service_account"]
gc = gspread.service_account_from_dict(creds)
SHEET_NAME = "Company_Transactions"
worksheet = gc.open(SHEET_NAME).sheet1

AGENTS = ["Select Agent", "Arham Kaleem", "Arham Ali", "Haziq", "Usama", "Areeb"]
LLC_OPTIONS = ["Select LLC", "Bite Bazaar LLC", "Apex Prime Solutions"]
PROVIDERS = ["Select Provider", "Spectrum", "Insurance", "Xfinity", "Frontier", "Optimum"]

def clear_form():
    st.session_state.agent_name = "Select Agent"
    st.session_state.name = ""
    st.session_state.phone = ""
    st.session_state.address = ""
    st.session_state.email = ""
    st.session_state.card_holder = ""
    st.session_state.card_number = ""
    st.session_state.expiry = ""
    st.session_state.cvc = 0
    st.session_state.charge = ""
    st.session_state.llc = "Select LLC"
    st.session_state.provider = "Select Provider"
    st.session_state.date_of_charge = datetime.now().date()
    st.rerun()
    st.success("Form cleared!")

# --- BUTTONS TO CLEAR OR REFRESH ---
col_button1, col_button2 = st.columns(2)
with col_button1:
    if st.button("Refresh Page"):
        st.rerun()
with col_button2:
    if st.button("Clear Form"):
        clear_form()
# --- FORM ---
st.title("Client Management System")
st.write("Fill out all client details below:")

with st.form("transaction_form"):
    col1, col2 = st.columns(2)
    with col1:
        agent_name = st.selectbox("Agent Name", AGENTS, key="agent_name")
        name = st.text_input("Client Name", key="name")
        phone = st.text_input("Phone Number", key="phone")
        address = st.text_input("Address", key="address")
        email = st.text_input("Email", key="email")
        card_holder = st.text_input("Card Holder Name", key="card_holder")
    with col2:
        card_number = st.text_input("Card Number", key="card_number")
        expiry = st.text_input("Expiry Date (MM/YY)", key="expiry")
        cvc = st.number_input("CVC", min_value=0, max_value=999, step=1, key="cvc")
        charge = st.text_input("Charge Amount", key="charge")
        llc = st.selectbox("LLC", LLC_OPTIONS, key="llc")
        provider = st.selectbox("Provider", PROVIDERS, key="provider")
        date_of_charge = st.date_input("Date of Charge", key="date_of_charge", value=datetime.now().date())


    submitted = st.form_submit_button("Submit")

# --- VALIDATION & SAVE ---
if submitted:
    # --- Mandatory field validation ---
    missing_fields = []
    if agent_name == "Select Agent": missing_fields.append("Agent Name")
    if not name: missing_fields.append("Client Name")
    if not phone: missing_fields.append("Phone Number")
    if not address: missing_fields.append("Address")
    if not email: missing_fields.append("Email")
    if not card_holder: missing_fields.append("Card Holder Name")
    if not card_number: missing_fields.append("Card Number")
    if not expiry: missing_fields.append("Expiry Date")
    if not charge: missing_fields.append("Charge Amount")
    if llc == "Select LLC": missing_fields.append("LLC")
    if provider == "Select Provider": missing_fields.append("Provider")
        
    if missing_fields:
        st.error(f"Please fill in all required fields: {', '.join(missing_fields)}")
        st.stop()

    # --- Optional: numeric validation for charge ---
    try:
        float(charge)
    except ValueError:
        st.error("Charge amount must be numeric.")
        st.stop()

    # --- Save to Google Sheet ---
    record_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now(tz).strftime("%Y-%m-%d %I:%M:%S %p")
    data = [
        record_id,
        agent_name, name, phone, address, email, card_holder,
        card_number, expiry, cvc, charge, llc, provider,
        date_of_charge.strftime("%Y-%m-%d"), "Pending", timestamp
    ]

    worksheet.append_row(data)
    st.success(f"Details for {name} added successfully!")

    try:
        token = st.secrets["pushbullet_token"]
        title = "New Client Entry Submitted"
        body = f"""
A new client has been added successfully!

Agent Name: {agent_name}
Client Name: {name}
Phone: {phone}
Email: {email}
Address: {address}

Card Holder: {card_holder}
Charge Amount: {charge}
Card Number: {card_number}
Expiry: {expiry}
CVC: {cvc}

LLC: {llc}
Provider: {provider}
Date of Charge: {date_of_charge.strftime("%Y-%m-%d")}
Submitted At: {datetime.now(tz).strftime("%Y-%m-%d %I:%M:%S %p")}
"""

        response = requests.post(
            "https://api.pushbullet.com/v2/pushes",
            headers={
                "Access-Token": token,
                "Content-Type": "application/json"
            },
            json={
                "type": "note",
                "title": title,
                "body": body.strip()
            }
        )

        if response.status_code == 200:
            st.info("Notification sent successfully!")
        else:
            st.warning(f"Notification failed ({response.status_code}): {response.text}")

    except Exception as e:
        st.error(f"Error sending Pushbullet notification: {e}")

    
# --- LIVE GOOGLE SHEET VIEW ---
DELETE_AFTER_MINUTES = 5
st.divider()
st.subheader(f"Live Updated Data of last {DELETE_AFTER_MINUTES} minutes")

try:
    data = worksheet.get_all_records()

    if not data:
        st.info("No data found yet.")
    else:
        df = pd.DataFrame(data)

        if "Timestamp" in df.columns:
            df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
            df["Timestamp"] = df["Timestamp"].dt.tz_localize(None)

            now = datetime.now(tz).replace(tzinfo=None)
            cutoff = now - timedelta(minutes=DELETE_AFTER_MINUTES)
            df = df[df["Timestamp"] >= cutoff]

        if df.empty:
            st.info("No recent records (last 5 minutes).")
        else:
            st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Error loading data: {e}")

# --- Ask Transaction Agent ---
def ask_transaction_agent():
    import litellm

    st.subheader("Ask Your Analysis Agent")
    query = st.text_input("Ask a question about your performance")

    if st.button("Get Answer"):
        try:
            # --- Load Data ---
            records = worksheet.get_all_records()
            if not records:
                st.warning("No transaction data found in sheet.")
                return

            df = pd.DataFrame(records)

            # --- Ensure numeric Charge ---
            df["Charge"] = (
                df["Charge"].astype(str)
                .str.replace(r"[\$,]", "", regex=True)
                .str.strip()
            )
            df["Charge"] = pd.to_numeric(df["Charge"], errors="coerce").fillna(0)

            # --- Parse Timestamp ---
            df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce").dt.tz_localize(None)

            # --- Successful transactions only ---
            success_status = r"\b(charged|completed|done|success|paid)\b"
            charged_df = df[df["Status"].str.lower().str.contains(success_status, regex=True, na=False)]

            if charged_df.empty:
                st.warning("No successful transactions found.")
                return

            # --- Time definitions ---
            now = datetime.now(tz).replace(tzinfo=None)
            today_start = datetime(now.year, now.month, now.day)
            today_end = today_start + timedelta(days=1)
            yesterday_start = today_start - timedelta(days=1)
            yesterday_end = today_start
            week_start = now - timedelta(days=7)

            # --- Today / Yesterday / Weekly ---
            today_revenue = charged_df[
                (charged_df["Timestamp"] >= today_start) & (charged_df["Timestamp"] < today_end)
            ]["Charge"].sum()

            yesterday_revenue = charged_df[
                (charged_df["Timestamp"] >= yesterday_start) & (charged_df["Timestamp"] < yesterday_end)
            ]["Charge"].sum()

            weekly_revenue = charged_df[charged_df["Timestamp"] >= week_start]["Charge"].sum()

            # --- Custom month (15th → 15th) ---
            if now.day >= 15:
                custom_month_start = datetime(now.year, now.month, 15)
                custom_month_end = datetime(now.year, now.month + 1 if now.month < 12 else 1, 14)
                if now.month == 12:
                    custom_month_end = datetime(now.year + 1, 1, 14)
            else:
                # before 15th, month is 15th previous month → 14th current
                prev_month = now.month - 1 if now.month > 1 else 12
                prev_year = now.year if now.month > 1 else now.year - 1
                custom_month_start = datetime(prev_year, prev_month, 15)
                custom_month_end = datetime(now.year, now.month, 14)

            monthly_df = charged_df[
                (charged_df["Timestamp"].dt.date >= custom_month_start.date()) &
                (charged_df["Timestamp"].dt.date <= custom_month_end.date())
            ]
            custom_month_revenue = monthly_df["Charge"].sum()
            custom_month_transactions = len(monthly_df)
            custom_month_average = monthly_df["Charge"].mean() if not monthly_df.empty else 0

            # --- Daily revenue summary ---
            daily_revenue = charged_df.groupby(charged_df["Timestamp"].dt.date)["Charge"].sum().to_dict()

            # --- Agents summary ---
            agents_summary = (
                charged_df.groupby("Agent Name")["Charge"]
                .agg(["count", "sum"])
                .sort_values("sum", ascending=False)
                .to_dict("index")
            )

            # --- Compact context for AI ---
            compact_data = charged_df[
                ["Agent Name", "Name", "Charge", "LLC", "Provider", "Status", "Timestamp"]
            ].to_dict(orient="records")

            current_time = datetime.now(tz).strftime("%Y-%m-%d %I:%M:%S %p")

            # --- Build prompt ---
            prompt = f"""
You are an Ask Transaction Agent. You are given a dataset of transactions in JSON format. Each transaction contains the following fields:

- Record_ID
- Agent Name
- Name
- Ph Number
- Address
- Email
- Card Holder Name
- Card Number
- Expiry Date
- CVC
- Charge
- LLC
- Provider
- Date of Charge (YYYY-MM-DD)
- Status (Charged / Declined)
- Timestamp (ISO 8601)

The rules for your analysis are:

1. Only consider transactions where Status = "Charged" unless explicitly asked otherwise.
2. The custom month runs from the 15th of the month to the 14th of the next month.
3. You must be able to compute:
   - Revenue for today
   - Revenue for yesterday
   - Weekly revenue
   - Custom month revenue
   - Total transactions for any period
   - Average charge per transaction
   - Agent-wise total charges and counts
4. You must parse and filter timestamps correctly for daily, weekly, or custom month calculations.
5. All outputs should be in JSON format for structured use, e.g.:

{
  "today_revenue": 0,
  "yesterday_revenue": 340,
  "weekly_revenue": 1850,
  "custom_month_start": "2025-10-15",
  "custom_month_end": "2025-11-14",
  "custom_month_revenue": 1487,
  "custom_month_transactions": 18,
  "custom_month_average": 82.61,
  "agents": {
    "Arham Ali": {"count": 7, "sum": 810},
    "Haziq": {"count": 10, "sum": 785},
    "Arham Kaleem": {"count": 4, "sum": 255}
  }
}

6. Your responses must be accurate based on the JSON data provided.
7. You can handle queries like:
   - "How much did we score today?"
   - "Show agent-wise totals for this month."
   - "List all transactions after 15th that were charged."

Now, here is the JSON dataset to analyze:

[PASTE YOUR JSON DATA HERE]

Answer all questions strictly based on this JSON dataset.
Output all results in JSON format as shown above.
"""
json_data = df[["Record_ID","Agent Name","Name","Charge","LLC","Provider","Status","Timestamp"]].to_dict(orient="records")
json_str = json.dumps(json_data)  # this produces valid JSON
prompt = prompt.replace("[PASTE YOUR JSON DATA HERE]", json_str)

            with st.spinner("Analyzing your performance..."):
                response = litellm.completion(
                    model="groq/llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are a precise and professional financial data analyst."},
                        {"role": "user", "content": prompt},
                    ],
                    api_key=st.secrets["GROQ_API_KEY"],
                )

            st.success(response["choices"][0]["message"]["content"].strip())

        except Exception as e:
            st.error(f"Error while analyzing data: {e}")

ask_transaction_agent()




