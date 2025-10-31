import streamlit as st
import gspread
import pandas as pd
from datetime import datetime, timedelta
import pytz
import json
import uuid
import requests

def style_status_rows(df):
    """
    Apply conditional styling based on Status column:
    Charged = green, Charge Back = red, Declined/Pending = default.
    """
    if "Status" not in df.columns or df.empty:
        return df  # nothing to style

    def highlight_row(row):
        if row["Status"] == "Charged":
            return ["background-color: darkgreen"] * len(row)
        elif row["Status"] == "Charge Back":
            return ["background-color: red"] * len(row)
        else:  # Declined or Pending
            return [""] * len(row)

    return df.style.apply(highlight_row, axis=1)


# --- LIGHT THEMES ---
light_themes = {
    "Sunlit Coral":       {"bg1": "#fff8f2", "bg2": "#ffe8df", "accent": "#ff6f61"},
    "Skyline Blue":       {"bg1": "#f0f8ff", "bg2": "#dcefff", "accent": "#3b82f6"},
    "Golden Sand":        {"bg1": "#fffbea", "bg2": "#fff2d1", "accent": "#f59e0b"},
    "Lilac Mist":         {"bg1": "#faf5ff", "bg2": "#f3e8ff", "accent": "#a78bfa"},
    "Mint Breeze":        {"bg1": "#f0fff9", "bg2": "#d7fff0", "accent": "#10b981"},
    "Peachy Glow":        {"bg1": "#fff4f0", "bg2": "#ffe4d9", "accent": "#ff7e5f"},
    "Icy Lavender":       {"bg1": "#f7f5ff", "bg2": "#e7e0ff", "accent": "#b57dfb"},
    "Sky Dusk":           {"bg1": "#f0f4ff", "bg2": "#d9e3ff", "accent": "#5f7fff"},
    "Creamy Amber":       {"bg1": "#fff9f2", "bg2": "#fff1d6", "accent": "#ffb347"},
    "Aqua Pearl":         {"bg1": "#f2fffe", "bg2": "#d9fff9", "accent": "#34d399"},
    "Rose Petal":         {"bg1": "#fff0f0", "bg2": "#ffe0e0", "accent": "#ff4d6d"},
    "Lemon Chiffon":      {"bg1": "#fffde7", "bg2": "#fff7c7", "accent": "#facc15"},
    "Frosted Mint":       {"bg1": "#f0fff4", "bg2": "#d0ffe0", "accent": "#12b886"},
    "Powder Blue":        {"bg1": "#f0f7ff", "bg2": "#dceaff", "accent": "#5dade2"},
    "Lavender Lace":      {"bg1": "#faf6ff", "bg2": "#eae0ff", "accent": "#9f7aea"},
    "Coral Cream":        {"bg1": "#fff6f0", "bg2": "#ffe5d5", "accent": "#ff7f50"},
    "Sky Morning":        {"bg1": "#f4f9ff", "bg2": "#dceeff", "accent": "#4dabf7"},
    "Vanilla Glow":       {"bg1": "#fffaf0", "bg2": "#fff2d8", "accent": "#fbbf24"},
    "Seaside Mist":       {"bg1": "#f0fdfa", "bg2": "#d4f7f0", "accent": "#22d3ee"},
    "Blush Petal":        {"bg1": "#fff5f7", "bg2": "#ffe4ec", "accent": "#f43f5e"},
}


# --- DARK THEMES (10 upgraded) ---
dark_themes = {
    "Obsidian Night":     {"bg1": "#0b0c10", "bg2": "#1f2833", "accent": "#66fcf1"},
    "Crimson Shadow":     {"bg1": "#1c0b0b", "bg2": "#2a0f0f", "accent": "#ff4444"},
    "Deep Ocean":         {"bg1": "#0a1b2a", "bg2": "#0d2c4a", "accent": "#1f8ef1"},
    "Neon Violet":        {"bg1": "#12001e", "bg2": "#1e0033", "accent": "#bb00ff"},
    "Emerald Abyss":      {"bg1": "#001a14", "bg2": "#00322b", "accent": "#00ff99"},
    "Cyber Red":          {"bg1": "#100000", "bg2": "#300000", "accent": "#ff1e56"},
    "Royal Teal":         {"bg1": "#001f1f", "bg2": "#003333", "accent": "#00d4d4"},
    "Midnight Purple":    {"bg1": "#0d001d", "bg2": "#1b0035", "accent": "#9b59b6"},
    "Steel Grey":         {"bg1": "#121212", "bg2": "#1f1f1f", "accent": "#7f8c8d"},
    "Aurora Pulse":       {"bg1": "#080808", "bg2": "#151515", "accent": "#f72585"},
    "Lava Core":          {"bg1": "#1a0000", "bg2": "#330000", "accent": "#ff5733"},
    "Galactic Blue":      {"bg1": "#000a1a", "bg2": "#001f33", "accent": "#4da8da"},
    "Neon Green":         {"bg1": "#001000", "bg2": "#002200", "accent": "#00ff66"},
    "Golden Chrome":      {"bg1": "#0d0d0d", "bg2": "#1a1a1a", "accent": "#ffd700"},
    "Midnight Cyan":      {"bg1": "#001f1f", "bg2": "#003737", "accent": "#00ffff"},
    "Red Ember":          {"bg1": "#140000", "bg2": "#2a0000", "accent": "#ff4b4b"},
    "Electric Indigo":    {"bg1": "#0a001a", "bg2": "#1a0033", "accent": "#8c00ff"},
    "Cosmic Teal":        {"bg1": "#001f1a", "bg2": "#003333", "accent": "#00e5ff"},
    "Steel Violet":       {"bg1": "#0f0d1a", "bg2": "#1b1833", "accent": "#9b59b6"},
    "Aurora Green":       {"bg1": "#001a0d", "bg2": "#00331a", "accent": "#00ff99"},
}

# --- Session Defaults ---
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Dark"
if "selected_theme" not in st.session_state:
    st.session_state.selected_theme = None

# --- SELECT THEME ---
themes = light_themes if st.session_state.theme_mode == "Light" else dark_themes

# Only set default if selected_theme is None or not in current themes
if st.session_state.selected_theme is None or st.session_state.selected_theme not in themes:
    st.session_state.selected_theme = list(themes.keys())[0]

# --- Mode Toggle ---
col1, col2, _ = st.columns([1, 1, 6])
with col1:
    if st.button("Light Mode", use_container_width=True):
        st.session_state.theme_mode = "Light"
with col2:
    if st.button("Dark Mode", use_container_width=True):
        st.session_state.theme_mode = "Dark"

themes = light_themes if st.session_state.theme_mode == "Light" else dark_themes
if st.session_state.selected_theme not in themes:
    st.session_state.selected_theme = list(themes.keys())[0]

# --- Capsule Buttons ---
theme_names = list(themes.keys())
st.markdown('<div class="theme-scroll">', unsafe_allow_html=True)
for theme_name in theme_names:
    data = themes[theme_name]
    accent = data["accent"]
    if st.button(theme_name, key=f"theme_{theme_name}"):
        st.session_state.selected_theme = theme_name
st.markdown('</div>', unsafe_allow_html=True)
            
# --- Extract Selected Theme ---
selected = themes[st.session_state.selected_theme]
bg1, bg2, accent = selected["bg1"], selected["bg2"], selected["accent"]
text_color = "#111" if st.session_state.theme_mode == "Light" else "#e6e6e6"

# --- CSS (must be before .theme-scroll div is rendered) ---
st.markdown(f"""
<style>
/* --- SCROLLABLE SINGLE-LINE THEMES ROW --- */
.theme-scroll {{
    display: flex;
    flex-wrap: nowrap;
    overflow-x: auto;
    padding: 8px 0;
    gap: 10px;
}}
.theme-scroll::-webkit-scrollbar {{
    height: 6px;
}}
.theme-scroll::-webkit-scrollbar-thumb {{
    background: {accent};
    border-radius: 10px;
}}
.theme-scroll > div {{
    flex: 0 0 auto;
}}
</style>
""", unsafe_allow_html=True)

# --- Capsule Buttons (after CSS defined) ---
theme_names = list(themes.keys())
st.markdown('<div class="theme-scroll">', unsafe_allow_html=True)
for theme_name in theme_names:
    data = themes[theme_name]
    accent = data["accent"]
    if st.button(theme_name, key=f"theme_{theme_name}"):

        st.session_state.selected_theme = theme_name
st.markdown('</div>', unsafe_allow_html=True)

# --- Header ---
st.markdown(f"""
<div style="
    background-color: {accent};
    color: white;
    padding: 18px 24px;
    border-radius: 12px;
    font-size: 22px;
    font-weight: 700;
    text-align:center;
    box-shadow: 0 4px 18px {accent}55;
    margin-bottom: 28px;
    animation: fadeIn 1s ease;
">
Client Management System — Techware Hub
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<style>
/* ---------------- keyframes ---------------- */
@keyframes pulseGlow {{
  0% {{ box-shadow: 0 0 0px {accent}44; }}
  50% {{ box-shadow: 0 0 20px {accent}aa; }}
  100% {{ box-shadow: 0 0 0px {accent}44; }}
}}

@keyframes bounce {{
  0%, 100% {{ transform: translateY(0); }}
  50% {{ transform: translateY(-3px); }}
}}

@keyframes fadeIn {{
  0% {{ opacity: 0; transform: translateY(8px); }}
  100% {{ opacity: 1; transform: translateY(0); }}
}}

@keyframes shimmerText {{
  0% {{ background-position: -200% 0; }}
  100% {{ background-position: 200% 0; }}
}}

@keyframes bgShift {{
  0% {{ background-position: 0% 0%; }}
  50% {{ background-position: 50% 50%; }}
  100% {{ background-position: 0% 0%; }}
}}

/* ---------------- BODY & BACKGROUND ---------------- */
[data-testid="stAppViewContainer"] {{
    background: radial-gradient(circle at top left, {bg2}, {bg1});
    font-family: "Inter", sans-serif;
    background-size: 400% 400%;
    animation: bgShift 60s ease infinite;
    transition: all 0.3s ease-in-out;
}}

/* ---------------- HEADER ---------------- */
div[style*="Client Management System"] {{
    background: linear-gradient(90deg, {accent}, #ffffff, {accent});
    color: transparent;
    padding: 18px 24px;
    border-radius: 12px;
    font-size: 22px;
    font-weight: 700;
    text-align:center;
    box-shadow: 0 4px 18px {accent}55;
    margin-bottom: 28px;
    background-clip: text;
    -webkit-background-clip: text;
    animation: shimmerText 3s linear infinite, fadeIn 1s ease;
}}

/* ---------------- CAPSULE THEME BUTTONS ---------------- */
div.stButton > button {{
    border-radius: 999px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    padding: 0.45rem 1rem !important;
    box-shadow: 0 0 6px {accent}33;
    background-color: transparent !important;
    color: {accent} !important;
    border: 1px solid {accent}55 !important;
}}

div.stButton > button:hover {{
    background: {accent}22 !important;
    color: white !important;
    box-shadow: 0 0 22px {accent}99, inset 0 0 12px {accent}66 !important;
    transform: scale(1.07);
    animation: bounce 0.4s ease;
}}

/* ---------------- TABLE ROWS ---------------- */
tbody tr:hover {{
    background-color: {accent}11 !important;
    transform: scale(1.01);
    transition: all 0.2s ease;
    box-shadow: 0 0 8px {accent}55;
}}

/* ---------------- SCROLLBAR ---------------- */
::-webkit-scrollbar {{
    width: 10px;
}}
::-webkit-scrollbar-thumb {{
    background: linear-gradient({accent}, {accent}cc);
    border-radius: 10px;
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
    st.session_state.cvc = ""
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

DELETE_AFTER_MINUTES = 20
st.divider()
st.subheader("Edit Lead")

# --- FETCH ALL DATA ---
try:
    all_records = worksheet.get_all_records()
    df_all = pd.DataFrame(all_records) if all_records else pd.DataFrame()
except Exception as e:
    st.error(f"Error loading sheet data: {e}")
    df_all = pd.DataFrame()

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
    record_id_input = st.text_input("Enter Record ID")
    if record_id_input and not df_all.empty:
        if record_id_input in df_all["Record_ID"].values:
            record = df_all[df_all["Record_ID"] == record_id_input].iloc[0]
        else:
            st.warning("No matching Record ID found.")

# --- EDIT FORM ---
if record is not None:
    st.info(f"Editing Record ID: {record['Record_ID']}")
    
    with st.form("edit_lead_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_agent_name = st.selectbox("Agent Name", AGENTS,
                                          index=AGENTS.index(record["Agent Name"]) if record["Agent Name"] in AGENTS else 0)
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
            new_llc = st.selectbox("LLC", LLC_OPTIONS,
                                   index=LLC_OPTIONS.index(record["LLC"]) if record["LLC"] in LLC_OPTIONS else 0)
            new_provider = st.selectbox("Provider", PROVIDERS,
                                        index=PROVIDERS.index(record["Provider"]) if record["Provider"] in PROVIDERS else 0)
            new_date_of_charge = st.date_input("Date of Charge",
                                               value=pd.to_datetime(record["Date of Charge"]).date() if record["Date of Charge"] else datetime.now().date())

        # --- STATUS LOGIC ---
        current_status = record["Status"]
        if current_status == "Charged":
            status_options = ["Charged", "Pending Charge Back"]
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
        try:
            row_index = df_all.index[df_all["Record_ID"] == record["Record_ID"]].tolist()
            if row_index:
                row_num = row_index[0] + 2
                updated_data = [
                    record["Record_ID"], new_agent_name, new_name, new_phone, new_address, new_email,
                    new_card_holder, new_card_number, new_expiry, new_cvc, new_charge,
                    new_llc, new_provider, new_date_of_charge.strftime("%Y-%m-%d"),
                    new_status, str(record["Timestamp"])
                ]
                worksheet.update(f"A{row_num}:P{row_num}", [updated_data])
                st.success(f"Lead for {new_name} updated successfully!")
                st.rerun()
            else:
                st.error("Record not found in sheet. Try refreshing the page.")
        except Exception as e:
            st.error(f"Error updating lead: {e}")











