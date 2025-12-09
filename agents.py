import streamlit as st
import gspread
import pandas as pd
from datetime import datetime, timedelta
import pytz
import json
import requests
import random
import time
from pathlib import Path
st.set_page_config(page_title="Client Management System — Techware Hub", layout="wide")

# ==============================
# Load external CSS (theme.css)
# ==============================
def load_css():
    try:
        css = Path("theme.css").read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"theme.css not found or failed to load: {e}")

load_css()

# ==============================
# Theme definitions (unchanged)
# ==============================
light_themes = {
    "Sunlit Coral":    {"bg1": "#fff8f2", "bg2": "#ffe8df", "accent": "#ff6f61"},
    "Skyline Blue":    {"bg1": "#f0f8ff", "bg2": "#dcefff", "accent": "#3b82f6"},
    "Golden Sand":     {"bg1": "#fffbea", "bg2": "#fff2d1", "accent": "#f59e0b"},
    "Lilac Mist":      {"bg1": "#faf5ff", "bg2": "#f3e8ff", "accent": "#a78bfa"},
    "Mint Breeze":     {"bg1": "#f0fff9", "bg2": "#d7fff0", "accent": "#10b981"},
    "Blush Quartz":    {"bg1": "#fff5f7", "bg2": "#ffe3eb", "accent": "#ec4899"},
    "Azure Frost":     {"bg1": "#f5fbff", "bg2": "#e0f2fe", "accent": "#0284c7"},
    "Citrus Bloom":    {"bg1": "#fffef2", "bg2": "#fff8d6", "accent": "#facc15"},
    "Pearl Sage":      {"bg1": "#f9fff9", "bg2": "#e6f7e6", "accent": "#65a30d"},
    "Creamy Mocha":    {"bg1": "#fffaf5", "bg2": "#f5ebe0", "accent": "#c08457"},
}
dark_themes = {
    "Midnight Gold":   {"bg1": "#0d0d0d", "bg2": "#1a1a1a", "accent": "#ffd700"},
    "Obsidian Night":  {"bg1": "#0b0c10", "bg2": "#1f2833", "accent": "#66fcf1"},
    "Crimson":  {"bg1": "#1c0b0b", "bg2": "#2a0f0f", "accent": "#ff4444"},
    "Neon Violet":     {"bg1": "#12001e", "bg2": "#1e0033", "accent": "#bb00ff"},
    "Emerald Abyss":   {"bg1": "#001a14", "bg2": "#00322b", "accent": "#00ff99"},
    "Cyber Pink":      {"bg1": "#0a0014", "bg2": "#1a0033", "accent": "#ff00aa"},
    "Deep Ocean":      {"bg1": "#0a1b2a", "bg2": "#0d2c4a", "accent": "#1f8ef1"},
    "Steel Indigo":    {"bg1": "#0c0f1a", "bg2": "#1c2333", "accent": "#7dd3fc"},
    "Velvet Crimson":  {"bg1": "#1a0000", "bg2": "#330000", "accent": "#e11d48"},
    "Arctic Noir":     {"bg1": "#050b12", "bg2": "#0e1822", "accent": "#38bdf8"},
}

if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Dark"
if "selected_theme" not in st.session_state:
    theme_set = dark_themes if st.session_state.theme_mode == "Dark" else light_themes
    random_theme_name = random.choice(list(theme_set.keys()))
    st.session_state.selected_theme = random_theme_name

def get_contrast_color(hex_color: str) -> str:
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    return "#000000" if brightness > 155 else "#ffffff"

def apply_theme_vars():
    themes = light_themes if st.session_state.theme_mode == "Light" else dark_themes
    if st.session_state.selected_theme not in themes:
        st.session_state.selected_theme = list(themes.keys())[0]
    selected = themes[st.session_state.selected_theme]
    bg1, bg2, accent = selected["bg1"], selected["bg2"], selected["accent"]
    text_color = "#111" if st.session_state.theme_mode == "Light" else "#e6e6e6"
    st.markdown(
        f"<style>:root{{--bg1:{bg1};--bg2:{bg2};--accent:{accent};--text:{text_color};}}</style>",
        unsafe_allow_html=True,
    )
    return bg1, bg2, accent, text_color

bg1, bg2, accent, text_color = apply_theme_vars()
title_text_color = get_contrast_color(accent)

st.markdown(
    f"""
<div class="app-title" style="font-size:22px; margin: 12px 0 22px;">
  Client Management System — Techware Hub
</div>
""",
    unsafe_allow_html=True,
)

col_tm1, col_tm2, _ = st.columns([1, 1, 6])
with col_tm1:
    st.markdown("<div style='display:flex; justify-content:center;'>", unsafe_allow_html=True)
    if st.button("Light Mode", use_container_width=True):
        if st.session_state.theme_mode != "Light":
            st.session_state.theme_mode = "Light"
            st.session_state.selected_theme = list(light_themes.keys())[0]
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with col_tm2:
    st.markdown("<div style='display:flex; justify-content:center;'>", unsafe_allow_html=True)
    if st.button("Dark Mode", use_container_width=True):
        if st.session_state.theme_mode != "Dark":
            st.session_state.theme_mode = "Dark"
            st.session_state.selected_theme = list(dark_themes.keys())[0]
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

themes = light_themes if st.session_state.theme_mode == "Light" else dark_themes

cols_palette = st.columns(len(themes))
for i, (theme_name, data) in enumerate(themes.items()):
    if cols_palette[i].button(theme_name.replace(" ", "\n"), key=f"theme_{theme_name}"):
        if st.session_state.selected_theme != theme_name:
            st.session_state.selected_theme = theme_name
            st.rerun()

tz = pytz.timezone("Asia/Karachi")

# --- GOOGLE SHEET SETUP ---
creds = st.secrets["gcp_service_account"]
gc = gspread.service_account_from_dict(creds)
SHEET_NAME = "Company_Transactions"
worksheet = gc.open(SHEET_NAME).sheet1

AGENTS = ["Select Agent", "Arham Kaleem", "Arham Ali", "Haziq"]
LLC_OPTIONS = ["Select LLC", "Visionary Pathways"]
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
    st.session_state.cvc = ""
    st.session_state.charge = ""
    st.session_state.llc = "Select LLC"
    st.session_state.provider = "Select Provider"
    st.session_state.order_id = ""
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

try:
    all_records = worksheet.get_all_records()
    df_all = pd.DataFrame(all_records) if all_records else pd.DataFrame()
except Exception as e:
    st.error(f"Error loading sheet data: {e}")
    df_all = pd.DataFrame()

with st.form("transaction_form"):
    col1, col2 = st.columns(2)
    with col1:
        agent_name = st.selectbox("Agent Name", AGENTS, key="agent_name")
        record_id_input = st.text_input("Order ID (unique)", key="order_id")
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
        # New PIN code input:
        pin_code_disabled = (provider != "Spectrum")
        pin_code_value = st.text_input(
            "4-digit PIN Code",
            value="" if not pin_code_disabled else "nil",
            max_chars=4,
            key="pin_code",
            disabled=pin_code_disabled,
            help="Required if provider is Spectrum, else 'nil' will be set automatically."
        )
        date_of_charge = st.date_input("Date of Charge", key="date_of_charge", value=datetime.now().date())

    submitted = st.form_submit_button("Submit")

# --- VALIDATION & SAVE ---
if submitted:
    missing_fields = []

    # Validate Order ID (user input instead of UUID)
    record_id_input = st.session_state.get("order_id", "").strip()
    if not record_id_input:
        missing_fields.append("Order ID")

    # Check if Order ID already exists (to avoid duplicates)
    if not df_all.empty and record_id_input in df_all["Record_ID"].values:
        st.error("Order ID already exists. Please enter a unique Order ID.")
        st.stop()
        
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

    # PIN Code validation only if Spectrum is selected
    if provider == "Spectrum":
        pin_code = st.session_state.get("pin_code", "").strip()
        if not pin_code or len(pin_code) != 4 or not pin_code.isdigit():
            missing_fields.append("Valid 4-digit PIN Code")
    else:
        pin_code = "nil"

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
    record_id = record_id_input.strip()
    timestamp = datetime.now(tz).strftime("%Y-%m-%d %I:%M:%S %p")
    data = [
        record_id, agent_name, name, phone, address, email, card_holder,
        card_number, expiry, cvc, charge, llc, provider,
        date_of_charge.strftime("%Y-%m-%d"), "Pending", timestamp,
        pin_code  # Add this as the last field or as per your sheet column order
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

DELETE_AFTER_MINUTES = 20
st.divider()
st.subheader("Edit Lead")

# --- FETCH ALL DATA ---

record = None  # default

# --- SAFELY PROCESS TIMESTAMP ---
if not df_all.empty and "Timestamp" in df_all.columns:
    # Convert to datetime and coerce invalid entries
    df_all["Timestamp"] = pd.to_datetime(df_all["Timestamp"], errors="coerce")

    # Remove rows with invalid timestamps
    df_all = df_all.dropna(subset=["Timestamp"])

    # Ensure datetime64 dtype (naive)
    df_all["Timestamp"] = df_all["Timestamp"].astype("datetime64[ns]")

    now = datetime.now(tz).replace(tzinfo=None)  # naive datetime for comparison
    cutoff = now - timedelta(minutes=DELETE_AFTER_MINUTES)

    # Filter recent records safely
    df_recent = df_all[df_all["Timestamp"] >= cutoff]
else:
    df_recent = pd.DataFrame()

# --- SELECT MODE ---
mode = st.radio("Edit by:", [f"Recent (Last {DELETE_AFTER_MINUTES} mins) - Name", "All-time - Record ID"])

# --- MODE LOGIC ---
if mode.startswith("Recent"):
    if not df_recent.empty:
        st.subheader(f"Recent Records Last {DELETE_AFTER_MINUTES} Minutes")
        st.dataframe(df_recent)  # Show recent records
        
        client_names = df_recent["Name"].unique().tolist()
        selected_client = st.selectbox("Select Client", ["Select Client"] + client_names)
        if selected_client != "Select Client":
            record = df_recent[df_recent["Name"] == selected_client].iloc[0]
    else:
        st.info("No recent records in the last 5 minutes.")

elif mode.startswith("All-time"):
    record_id_value = record["Record_ID"] if record and "Record_ID" in record else ""
    record_id_input = st.text_input("Order ID", value=record_id_value)

    if record_id_input and not df_all.empty:
        # Normalize types
        df_all["Record_ID"] = df_all["Record_ID"].astype(str).str.strip()
        record_id_input = str(record_id_input).strip()

        if record_id_input in df_all["Record_ID"].values:
            record = df_all[df_all["Record_ID"] == record_id_input].iloc[0]
        else:
            st.warning("No matching Record ID found.")

# --- EDIT FORM ---
if record is not None:
    st.info(f"Editing Record ID: {record['Record_ID']}")

    # Determine current PIN code value or default to 'nil' if missing
    current_pin_code = record.get("PIN Code", "nil") if "PIN Code" in record else "nil"

    with st.form("edit_lead_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_agent_name = st.selectbox(
                "Agent Name",
                AGENTS,
                index=AGENTS.index(record["Agent Name"]) if record["Agent Name"] in AGENTS else 0,
            )
            new_name = st.text_input("Client Name", value=record["Name"])
            new_phone = st.text_input("Phone Number", value=record["Ph Number"])
            new_address = st.text_input("Address", value=record["Address"])
            new_email = st.text_input("Email", value=record["Email"])
            new_card_holder = st.text_input("Card Holder Name", value=record["Card Holder Name"])
        with col2:
            new_card_number = st.text_input("Card Number", value=record["Card Number"])
            new_card_number = new_card_number.replace(" ", "").replace("-", "")
            new_expiry = st.text_input("Expiry Date (MM/YY)", value=record["Expiry Date"])
            new_expiry = new_expiry.replace("/", "").replace("-", "").replace(" ", "")
            new_cvc = st.text_input("CVC", value=str(record["CVC"]))
            new_charge = st.text_input("Charge Amount", value=str(record["Charge"]))
            new_llc = st.selectbox(
                "LLC", LLC_OPTIONS, index=LLC_OPTIONS.index(record["LLC"]) if record["LLC"] in LLC_OPTIONS else 0
            )
            new_provider = st.selectbox(
                "Provider",
                PROVIDERS,
                index=PROVIDERS.index(record["Provider"]) if record["Provider"] in PROVIDERS else 0,
                key="edit_provider"  # new key to track changes separately if needed
            )

            # PIN code field with logic
            pin_code_disabled = (new_provider != "Spectrum")
            new_pin_code = st.text_input(
                "4-digit PIN Code",
                value=current_pin_code if not pin_code_disabled else "nil",
                max_chars=4,
                disabled=pin_code_disabled,
                help="Required if provider is Spectrum, else 'nil' will be set automatically.",
                key="edit_pin_code"
            )

            new_date_of_charge = st.date_input(
                "Date of Charge",
                value=pd.to_datetime(record["Date of Charge"]).date() if record["Date of Charge"] else datetime.now().date(),
            )

        # --- STATUS LOGIC ---
        current_status = record["Status"]
        if current_status == "Charged":
            status_options = ["Charged", "Pending", "Charge Back"]
            status_disabled = False
        elif current_status == "Declined":
            status_options = ["Declined", "Pending", "Charge Back"]
            status_disabled = False
        else:  # Pending or Charge Back
            status_options = [current_status]
            status_disabled = True

        new_status = st.selectbox("Status", status_options, index=0, disabled=status_disabled)
        updated = st.form_submit_button("Update Lead")

    if updated:
        # Validate PIN code if Spectrum is selected
        if new_provider == "Spectrum":
            if not new_pin_code or len(new_pin_code) != 4 or not new_pin_code.isdigit():
                st.error("Please enter a valid 4-digit PIN Code for Spectrum provider.")
                st.stop()
        else:
            new_pin_code = "nil"

        try:
            row_index = df_all.index[df_all["Record_ID"] == record["Record_ID"]].tolist()
            if row_index:
                row_num = row_index[0] + 2
                new_timestamp = datetime.now(tz).strftime("%Y-%m-%d %I:%M:%S %p")
                updated_data = [
                    record["Record_ID"], new_agent_name, new_name, new_phone, new_address, new_email,
                    new_card_holder, new_card_number, new_expiry, new_cvc, new_charge,
                    new_llc, new_provider, new_date_of_charge.strftime("%Y-%m-%d"),
                    new_status, new_timestamp,
                    new_pin_code  # Add PIN Code as the last column or match your sheet layout
                ]
                worksheet.update(f"A{row_num}:Q{row_num}", [updated_data])  # Adjust 'Q' if columns change
                st.success(f"Lead for {new_name} updated successfully!")
                st.rerun()
            else:
                st.error("Record not found in sheet. Try refreshing the page.")
        except Exception as e:
            st.error(f"Error updating lead: {e}")


from datetime import datetime, time, timedelta
import pytz
import pandas as pd

tz = pytz.timezone("Asia/Karachi")
now = datetime.now(tz)

# Determine night window (7 PM → 6 AM)
if now.time() >= time(7, 0) and now.time() < time(19, 0):
    # Daytime: night window was yesterday 19:00 → today 06:00
    window_start = datetime.combine(now.date() - timedelta(days=1), time(19, 0))
    window_end = datetime.combine(now.date(), time(6, 0))
else:
    # Nighttime
    if now.time() >= time(19, 0):
        window_start = datetime.combine(now.date(), time(19, 0))
        window_end = datetime.combine(now.date() + timedelta(days=1), time(6, 0))
    else:  # 00:00 → 06:00
        window_start = datetime.combine(now.date() - timedelta(days=1), time(19, 0))
        window_end = datetime.combine(now.date(), time(6, 0))

# --- Ensure Timestamp is datetime and Charge is numeric ---
if not df_all.empty:
    # Convert Timestamp to datetime safely
    if 'Timestamp' in df_all.columns:
        df_all['Timestamp'] = pd.to_datetime(df_all['Timestamp'], errors='coerce')
        df_all = df_all.dropna(subset=['Timestamp'])
    
    # Convert Charge to float safely
    if 'Charge' in df_all.columns:
        df_all['ChargeFloat'] = pd.to_numeric(
            df_all['Charge'].replace('[\$,]', '', regex=True),
            errors='coerce'
        ).fillna(0.0)
    else:
        df_all['ChargeFloat'] = 0.0

    # Filter Charged transactions in night window
    night_charged_df = df_all[
        (df_all['Status'] == "Charged") &
        (df_all['Timestamp'] >= window_start) &
        (df_all['Timestamp'] <= window_end)
    ]

    total_night_charge = night_charged_df['ChargeFloat'].sum()
    total_night_charge_str = f"${total_night_charge:,.2f}"
else:
    total_night_charge_str = "$0.00"

amount_text_color = get_contrast_color(accent)
label_text_color = get_contrast_color(accent)

# --- NIGHT WINDOW TOTAL WIDGET ---
amount_text_color = get_contrast_color(accent)
label_text_color = get_contrast_color(accent)

st.markdown(f"""
<div style="
    position: fixed;
    top: 20px;
    right: 30px;
    background: {accent};
    padding: 16px 24px;
    border-radius: 16px;
    font-size: 18px;
    font-weight: 700;
    box-shadow: 0 8px 24px {accent}77;
    z-index: 9999;
    text-align: center;
    transition: all 0.3s ease;
    backdrop-filter: blur(6px);
">
    <!-- Label -->
    <div style='font-size:14px; opacity:0.85; color:{label_text_color}; margin-bottom:2px;'>
        🌙 Night Charged Total
    </div>
    <!-- Sub-label -->
    <div style='font-size:12px; opacity:0.75; color:{label_text_color}; margin-bottom:4px;'>
        Today's Total
    </div>
    <!-- Amount -->
    <div style='font-size:26px; font-weight:800; color:{amount_text_color};'>
        {total_night_charge_str}
    </div>
</div>

<style>
@keyframes pulseGlow {{
    0% {{ box-shadow: 0 0 0px {accent}44; }}
    50% {{ box-shadow: 0 0 20px {accent}aa; }}
    100% {{ box-shadow: 0 0 0px {accent}44; }}
}}
div[style*="{total_night_charge_str}"] {{
    animation: pulseGlow 2s infinite;
}}
</style>
""", unsafe_allow_html=True)
