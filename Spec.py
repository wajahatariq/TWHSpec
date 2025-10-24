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

# --- LIGHT THEMES ---
light_themes = {
    "Blush White": {"bg1": "#ffffff", "bg2": "#f9f3f2", "accent": "#ff5f6d"},
    "Ocean Mist": {"bg1": "#f2fbfd", "bg2": "#e4f9ff", "accent": "#00aaff"},
    "Ivory Gold": {"bg1": "#fffaf0", "bg2": "#fdf5e6", "accent": "#d4af37"},
    "Rose Quartz": {"bg1": "#fff0f5", "bg2": "#ffe4e1", "accent": "#ff69b4"},
    "Arctic Blue": {"bg1": "#f7fbff", "bg2": "#e8f1fa", "accent": "#4682b4"},
    "Peach Glow": {"bg1": "#fff7f3", "bg2": "#ffe9df", "accent": "#ff7e5f"},
    "Lavender Sky": {"bg1": "#f8f4ff", "bg2": "#ede7ff", "accent": "#a780ff"},
    "Mint Dream": {"bg1": "#f3fff9", "bg2": "#e3fdf3", "accent": "#34d399"},
    "Champagne": {"bg1": "#fffaf5", "bg2": "#fff3e9", "accent": "#ffb347"},
    "Powder Blue": {"bg1": "#f5faff", "bg2": "#e9f2ff", "accent": "#5dade2"},
}

# --- DARK THEMES ---
dark_themes = {
    "Crimson Dark": {"bg1": "#0f0f0f", "bg2": "#1b1b1b", "accent": "#ff4b4b"},
    "Emerald Noir": {"bg1": "#0f1a14", "bg2": "#13221a", "accent": "#00c781"},
    "Royal Blue": {"bg1": "#0d1b2a", "bg2": "#1b263b", "accent": "#4da8da"},
    "Golden Luxe": {"bg1": "#1a120b", "bg2": "#2b1b10", "accent": "#ffcc00"},
    "Cyber Neon": {"bg1": "#060606", "bg2": "#101010", "accent": "#00ffff"},
    "Violet Eclipse": {"bg1": "#140019", "bg2": "#1e0027", "accent": "#b537f2"},
    "Aqua Blaze": {"bg1": "#001a1f", "bg2": "#002b33", "accent": "#00f0ff"},
    "Rose Inferno": {"bg1": "#1a0008", "bg2": "#29000d", "accent": "#ff1e56"},
    "Steel Night": {"bg1": "#121212", "bg2": "#1f1f1f", "accent": "#7f8c8d"},
    "Aurora Pulse": {"bg1": "#080808", "bg2": "#151515", "accent": "#f72585"},
}

# --- Session Defaults ---
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Dark"
if "selected_theme" not in st.session_state:
    st.session_state.selected_theme = None

# --- Mode Toggle ---
col1, col2, _ = st.columns([1, 1, 6])
with col1:
    if st.button("🌞 Light Mode", use_container_width=True):
        st.session_state.theme_mode = "Light"
with col2:
    if st.button("🌙 Dark Mode", use_container_width=True):
        st.session_state.theme_mode = "Dark"

themes = light_themes if st.session_state.theme_mode == "Light" else dark_themes
if st.session_state.selected_theme not in themes:
    st.session_state.selected_theme = list(themes.keys())[0]

# --- Capsule Buttons ---
cols = st.columns(len(themes))
for i, (theme_name, data) in enumerate(themes.items()):
    accent = data["accent"]
    if cols[i].button(theme_name, key=f"theme_{theme_name}"):
        st.session_state.selected_theme = theme_name

# --- Extract Selected Theme ---
selected = themes[st.session_state.selected_theme]
bg1, bg2, accent = selected["bg1"], selected["bg2"], selected["accent"]
text_color = "#111" if st.session_state.theme_mode == "Light" else "#e6e6e6"

# --- Header ---
st.markdown(f"""
<div style="
    background: linear-gradient(90deg, {accent}, {accent}cc);
    color: white;
    padding: 18px 24px;
    border-radius: 12px;
    font-size: 20px;
    font-weight: 600;
    text-align:center;
    box-shadow: 0 4px 18px {accent}55;
    margin-bottom: 28px;
">
Client Management System — Techware Hub
</div>
""", unsafe_allow_html=True)

# --- CSS + ANIMATIONS ---
st.markdown(f"""
<style>
@keyframes pulseGlow {{
    0% {{ box-shadow: 0 0 0px {accent}55; }}
    50% {{ box-shadow: 0 0 20px {accent}aa; }}
    100% {{ box-shadow: 0 0 0px {accent}55; }}
}}
@keyframes bounce {{
    0%,100% {{ transform: translateY(0); }}
    50% {{ transform: translateY(-3px); }}
}}
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], [data-testid="stHeader"] {{
    background-color: {bg1} !important;
    color: {text_color} !important;
    color-scheme: {"light" if st.session_state.theme_mode=="Light" else "dark"} !important;
}}
[data-testid="stAppViewContainer"] {{
    background: radial-gradient(circle at top left, {bg2}, {bg1});
    font-family: "Inter", sans-serif;
    transition: all 0.3s ease-in-out;
}}
h1,h2,h3,h4,h5,h6 {{
    color: {accent} !important;
    text-shadow: 0px 0px 10px {accent}33;
}}
div[data-testid="column"] > div > button {{
    border-radius: 999px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}}
div[data-testid="column"] > div > button:hover {{
    background: {accent}22 !important;
    color: white !important;
    box-shadow: 0 0 22px {accent}99, inset 0 0 12px {accent}66 !important;
    transform: scale(1.07);
    animation: bounce 0.4s ease;
}}
div[data-testid="column"] > div > button:has(span:contains('{st.session_state.selected_theme}')) {{
    background: {accent}33 !important;
    color: white !important;
    border: 1px solid {accent}cc !important;
    animation: pulseGlow 2.3s infinite ease-in-out;
    box-shadow: 0 0 18px {accent}bb !important;
}}
::-webkit-scrollbar-thumb {{
    background: linear-gradient({accent}, {accent}cc);
    border-radius: 10px;
}}
thead tr th {{
    background-color: {accent} !important;
    color: white !important;
    font-weight: 600 !important;
}}
tbody tr:hover {{
    background-color: {accent}11 !important;
}}
.stAlert {{
    border-radius: 10px !important;
    background: {accent}14 !important;
    border-left: 5px solid {accent} !important;
}}
</style>
""", unsafe_allow_html=True)

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
        cvc = st.text_input("CVC", key="cvc")
        charge = st.text_input("Charge Amount", key="charge")
        llc = st.selectbox("LLC", LLC_OPTIONS, key="llc")
        provider = st.selectbox("Provider", PROVIDERS, key="provider")
        date_of_charge = st.date_input("Date of Charge", key="date_of_charge", value=datetime.now().date())
    submitted = st.form_submit_button("Submit")
# --- VALIDATION & SAVE ---
if submitted:
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
    # --- Clean up formatting ---
    card_number = card_number.replace(" ", "").replace("-", "")
    expiry = expiry.replace("/", "").replace("-", "").replace(" ", "")

    # --- Format Charge Amount ---
    try:
        charge_value = float(charge.replace("$", "").strip())
        charge = f"${charge_value:.2f}"
    except ValueError:
        st.error("Charge amount must be numeric (e.g., 29 or 29.00).")
        st.stop()

    # --- Save to Google Sheet ---
    record_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now(tz).strftime("%Y-%m-%d %I:%M:%S %p")
    data = [
        record_id, agent_name, name, phone, address, email, card_holder,
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
            headers={"Access-Token": token, "Content-Type": "application/json"},
            json={"type": "note", "title": title, "body": body.strip()}
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
            st.dataframe(
                df.style.set_properties(
                    **{'background-color': '#1E2A38', 'color': 'white', 'border-color': '#444'}
                ),
                use_container_width=True,
            )

except Exception as e:
    st.error(f"Error loading data: {e}")

# --- EDIT LEAD SECTION ---
st.divider()
st.subheader("Edit Lead (From Last 5 Minutes)")

if 'df' in locals() and not df.empty:
    client_names = df["Name"].unique().tolist()
    selected_client = st.selectbox("Select Client to Edit", ["Select Client"] + client_names)

    if selected_client != "Select Client":
        record = df[df["Name"] == selected_client].iloc[0]
        record_id = record["Record_ID"]

        st.info(f"Editing Record ID: {record_id}")

        with st.form("edit_lead_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_agent_name = st.selectbox("Agent Name", AGENTS, index=AGENTS.index(record["Agent Name"]) if record["Agent Name"] in AGENTS else 0)
                new_name = st.text_input("Client Name", value=record["Name"])
                new_phone = st.text_input("Phone Number", value=record["Ph Number"])
                new_address = st.text_input("Address", value=record["Address"])
                new_email = st.text_input("Email", value=record["Email"])
                new_card_holder = st.text_input("Card Holder Name", value=record["Card Holder Name"])
            with col2:
                new_card_number = st.text_input("Card Number", value=record["Card Number"])
                new_expiry = st.text_input("Expiry Date (MM/YY)", value=record["Expiry Date"])
                new_cvc = st.number_input("CVC", min_value=0, max_value=999, step=1, value=int(record["CVC"]) if str(record["CVC"]).isdigit() else 0)
                new_charge = st.text_input("Charge Amount", value=str(record["Charge"]))
                new_llc = st.selectbox("LLC", LLC_OPTIONS, index=LLC_OPTIONS.index(record["LLC"]) if record["LLC"] in LLC_OPTIONS else 0)
                new_provider = st.selectbox("Provider", PROVIDERS, index=PROVIDERS.index(record["Provider"]) if record["Provider"] in PROVIDERS else 0)
                new_date_of_charge = st.date_input("Date of Charge", value=pd.to_datetime(record["Date of Charge"]).date() if record["Date of Charge"] else datetime.now().date())

            updated = st.form_submit_button("Update Lead")

        if updated:
            try:
                all_records = worksheet.get_all_records()
                df_all = pd.DataFrame(all_records)
                if "Record_ID" in df_all.columns:
                    row_index = df_all.index[df_all["Record_ID"] == record_id].tolist()
                    if row_index:
                        row_num = row_index[0] + 2  # +2 because sheet rows start at 1 and header row is row 1
                        updated_data = [
                            record_id, new_agent_name, new_name, new_phone, new_address, new_email,
                            new_card_holder, new_card_number, new_expiry, new_cvc, new_charge,
                            new_llc, new_provider, new_date_of_charge.strftime("%Y-%m-%d"),
                            record["Status"], str(record["Timestamp"])
                        ]
                        worksheet.update(f"A{row_num}:P{row_num}", [updated_data])
                        st.success(f"Lead for {new_name} updated successfully!")
                        st.rerun()
                    else:
                        st.error("Record not found in sheet. Try refreshing the page.")
                else:
                    st.error("No 'Record_ID' column found in sheet.")
            except Exception as e:
                st.error(f"Error updating lead: {e}")
else:
    st.info("No recent data to edit (last 5 minutes).")































