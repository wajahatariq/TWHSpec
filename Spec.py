import streamlit as st
import gspread
import pandas as pd
from datetime import datetime, timedelta
import pytz
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
            # --- Load sheet data ---
            records = worksheet.get_all_records()
            if not records:
                st.warning("No transaction data found in sheet.")
                return

            df = pd.DataFrame(records)

            # --- Column validation ---
            required_cols = {"Date of Charge", "Charge", "Status", "Agent Name"}
            if not required_cols.issubset(df.columns):
                st.error(f"Missing required columns: {required_cols - set(df.columns)}")
                return

            # --- Clean dates ---
            df["Date of Charge"] = (
                pd.to_datetime(df["Date of Charge"], errors="coerce")
                .dt.tz_localize(None)
                .dt.date
            )
            df = df.dropna(subset=["Date of Charge"])

            # --- Clean numeric charges ---
            df["Charge"] = (
                df["Charge"]
                .astype(str)
                .str.replace(r"[^\d\.\-]+", "", regex=True)
                .str.strip()
            )
            df["Charge"] = pd.to_numeric(df["Charge"], errors="coerce")
            df = df.dropna(subset=["Charge"])

            # --- Normalize status and agent ---
            df["Status"] = df["Status"].astype(str).str.lower().str.strip()
            df["Agent Name"] = df["Agent Name"].astype(str).str.strip()

            # --- Successful transactions ---
            charged_df = df[
                df["Status"].str.contains(
                    r"\b(charged|completed|done|success|paid)\b", regex=True, na=False
                )
            ].copy()

            if charged_df.empty:
                st.warning("No successful transactions found.")
                return

            # --- Add string date for grouping ---
            charged_df["Date_str"] = charged_df["Date of Charge"].apply(
                lambda d: d.strftime("%Y-%m-%d")
            )

            # --- Compute standard time frames ---
            now = datetime.now(tz)
            today = now.date()
            yesterday = today - timedelta(days=1)
            week_ago = today - timedelta(days=7)

            # --- Daily revenue ---
            daily_revenue = charged_df.groupby("Date_str")["Charge"].sum().to_dict()
            today_revenue = float(daily_revenue.get(today.strftime("%Y-%m-%d"), 0))
            yesterday_revenue = float(daily_revenue.get(yesterday.strftime("%Y-%m-%d"), 0))

            # --- Last 7 days ---
            last_7_days_df = charged_df[
                (charged_df["Date of Charge"] >= week_ago)
                & (charged_df["Date of Charge"] <= today)
            ]
            weekly_revenue = round(float(last_7_days_df["Charge"].sum()), 2)

            # --- Custom monthly period 15th-to-14th ---
            if today.day >= 15:
                custom_month_start = today.replace(day=15)
                # compute 14th of next month
                next_month = today.replace(day=28) + timedelta(days=4)
                custom_month_end = next_month.replace(day=14)
            else:
                last_month = today.replace(day=1) - timedelta(days=1)
                custom_month_start = last_month.replace(day=15)
                custom_month_end = today.replace(day=14)

            custom_month_df = charged_df[
                (charged_df["Date of Charge"] >= custom_month_start)
                & (charged_df["Date of Charge"] <= custom_month_end)
            ]
            custom_month_revenue = round(float(custom_month_df["Charge"].sum()), 2)
            custom_month_transactions = int(len(custom_month_df))
            custom_month_average = (
                round(float(custom_month_df["Charge"].mean()), 2)
                if not custom_month_df.empty
                else 0
            )

            # --- Total / overall stats ---
            total_revenue = round(float(charged_df["Charge"].sum()), 2)
            total_transactions = int(len(charged_df))
            average_charge = round(float(charged_df["Charge"].mean()), 2)

            # --- Agent-level stats ---
            agent_summary = (
                charged_df.groupby("Agent Name")["Charge"]
                .agg(["count", "sum"])
                .sort_values("sum", ascending=False)
                .reset_index()
            )
            agent_summary_dict = agent_summary.set_index("Agent Name").to_dict("index")

            # --- Build summary dict ---
            summary = {
                "total_revenue": total_revenue,
                "total_transactions": total_transactions,
                "average_charge": average_charge,
                "today_date": today.strftime("%Y-%m-%d"),
                "today_revenue": today_revenue,
                "yesterday_revenue": yesterday_revenue,
                "weekly_revenue": weekly_revenue,
                "daily_revenue": daily_revenue,
                "custom_month_start": custom_month_start.strftime("%Y-%m-%d"),
                "custom_month_end": custom_month_end.strftime("%Y-%m-%d"),
                "custom_month_revenue": custom_month_revenue,
                "custom_month_transactions": custom_month_transactions,
                "custom_month_average": custom_month_average,
                "agents": agent_summary_dict,
            }

            # --- Compact context for LLM ---
            compact_data = charged_df[
                ["Agent Name", "Name", "Charge", "LLC", "Provider", "Status", "Date_str"]
            ].rename(columns={"Date_str": "Date of Charge"}).to_dict(orient="records")

            # --- Prompt ---
            current_time = now.strftime("%Y-%m-%d %I:%M:%S %p")
            prompt = f"""
You are a financial analytics assistant.
Current system time: {current_time}

### Summary Data (pre-calculated)
{summary}

### Context (sample transactions)
{compact_data[:20]}

### User Question
{query}

Instructions:
- Always use precomputed summary numbers for answers.
- For "today", use summary["today_revenue"].
- For "yesterday", use summary["yesterday_revenue"].
- For "this week" or "last 7 days", use summary["weekly_revenue"].
- For "this month" or "custom month", use summary["custom_month_revenue"]; month runs 15th–14th.
- For agent-specific queries, use summary["agents"].
- For totals or overall, use summary["total_revenue"] and summary["total_transactions"].
- Never invent or recalculate numeric values yourself.
- Keep answers concise, factual, and accurate.
"""

            with st.spinner("Analyzing your performance..."):
                response = litellm.completion(
                    model="groq/llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a precise and professional financial data analyst who only uses the numeric data provided.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    api_key=st.secrets["GROQ_API_KEY"],
                )

            answer = response["choices"][0]["message"]["content"].strip()
            st.success(answer)

            # --- Optional: Debug summary ---
            with st.expander("View Computed Summary (for verification)"):
                st.json(summary)

        except Exception as e:
            st.error(f"Error while analyzing data: {e}")
ask_transaction_agent()
