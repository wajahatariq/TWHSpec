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
# --- Ask Transaction Agent ---
def ask_transaction_agent():
    import litellm
    st.subheader("Ask your Analysis Agent")

    query = st.text_input("Ask a question about your performance")
    if st.button("Get Answer"):
        # Load full data
        df = pd.DataFrame(worksheet.get_all_records())

        # Filter only this month's data
        if "Timestamp" in df.columns:
            df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
            now = pd.Timestamp.now()
            df = df[(df["Timestamp"].dt.year == now.year) & (df["Timestamp"].dt.month == now.month)]

        # Convert filtered df to string for LLM
        df_str = df.to_string(index=False)

        # Build prompt without changing your existing prompt
        full_prompt = f"""
You are a Data analysis Intelligence Assistant. 
Answer with only the final result — no reasoning or steps.
Never show or mention sensitive data (card number, CVC, expiry) or any card details.
You can show the amount of charge, client details or agent details 
Our data:
{df_str}

Question: {query}
"""
        try:
            response = litellm.completion(
                model="groq/llama-3.3-70b-versatile",  # recommended current model
                messages=[
                    {"role": "system", "content": "You are a data analysis expert."},
                    {"role": "user", "content": full_prompt}
                ],
                api_key=st.secrets["GROQ_API_KEY"]
            )
            st.success(response['choices'][0]['message']['content'])
        except Exception as e:
            st.error(f"Error: {e}")
ask_transaction_agent()

