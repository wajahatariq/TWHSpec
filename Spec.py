import streamlit as st
import gspread
import pandas as pd
from datetime import datetime, timedelta
import pytz
import json
import uuid
import requests
# --- CONFIG ---
import firebase_admin
from firebase_admin import credentials, db

def init_firebase():
    if "firebase_app" in st.session_state:
        return st.session_state["firebase_app"]

    fb = st.secrets["firebase"]  # structure we populated in secrets.toml or Streamlit Cloud
    # If your secrets are nested, adjust accordingly.
    cred_dict = {
        "type": fb["type"],
        "project_id": fb["project_id"],
        "private_key_id": fb["private_key_id"],
        "private_key": fb["private_key"],
        "client_email": fb["client_email"],
        "client_id": fb["client_id"],
        "auth_uri": fb.get("auth_uri", "https://accounts.google.com/o/oauth2/auth"),
        "token_uri": fb.get("token_uri", "https://oauth2.googleapis.com/token"),
        "auth_provider_x509_cert_url": fb.get("auth_provider_x509_cert_url"),
        "client_x509_cert_url": fb.get("client_x509_cert_url"),
    }

    cred = credentials.Certificate(cred_dict)
    app = firebase_admin.initialize_app(cred, {
        "databaseURL": fb["databaseURL"]
    })
    st.session_state["firebase_app"] = app
    return app

# call it once
init_firebase()

from firebase_admin import db

def send_message(sender, receiver, body, txn_id=None):
    ref = db.reference("chat")
    item = {
        "timestamp": datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S"),
        "sender": sender,
        "receiver": receiver,
        "body": body,
        "read_by": { sender: True },  # sender already "read" it
    }
    if txn_id:
        item["txn_id"] = txn_id
    ref.push(item)

def load_messages(limit=200):
    ref = db.reference("chat")
    data = ref.order_by_key().limit_to_last(limit).get()  # returns dict of messages
    # convert dict->list sorted by timestamp (if no timestamps guarantee use keys order)
    messages = []
    if data:
        for k, v in data.items():
            v["id"] = k
            messages.append(v)
        # sort by timestamp if present
        messages.sort(key=lambda x: x.get("timestamp", ""))
    return messages

def mark_as_read(msg_id, user):
    msg_ref = db.reference(f"chat/{msg_id}/read_by")
    current = msg_ref.get() or {}
    current[user] = True
    msg_ref.set(current)

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
from chat_utils import send_message, load_messages, mark_as_read
from firebase_admin import db

# ensure firebase initialized already
init_firebase()

agent_name = st.session_state.get("agent_name", "Unknown Agent")

st.divider()
st.subheader("Chat with Manager")

msg_col1, msg_col2 = st.columns([4,1])
with msg_col1:
    new_msg = st.text_input("Message to Manager:", key="chat_input")
with msg_col2:
    if st.button("Send", key="send_chat"):
        if agent_name in ("Select Agent", "", "Unknown Agent"):
            st.warning("Select your agent name first.")
        elif new_msg.strip() == "":
            st.warning("Cannot send empty message.")
        else:
            send_message(sender=agent_name, receiver="Manager", body=new_msg.strip())
            st.success("Message sent.")
            st.experimental_rerun()

# cached loader - TTL short (e.g., 3 or 5 sec)
@st.cache_data(ttl=5)
def cached_load():
    return load_messages(200)

msgs = cached_load()
if not msgs:
    st.info("No messages yet.")
else:
    for m in msgs:
        # show only messages involving this agent or sent to All
        if m["receiver"] in (agent_name, "All", "Manager") or m["sender"] == agent_name:
            sender = "You" if m["sender"] == agent_name else m["sender"]
            st.markdown(f"**{sender}** — {m.get('timestamp','')}  \n{m.get('body')}")
            # optionally mark read for manager messages
            if m["sender"] == "Manager" and not m.get("read_by", {}).get(agent_name):
                mark_as_read(m["id"], agent_name)


