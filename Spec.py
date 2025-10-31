import streamlit as st
import gspread
import pandas as pd
from datetime import datetime, timedelta
import pytz
import json
import uuid
import requests
import random

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
    "Crimson Shadow":  {"bg1": "#1c0b0b", "bg2": "#2a0f0f", "accent": "#ff4444"},
    "Deep Ocean":      {"bg1": "#0a1b2a", "bg2": "#0d2c4a", "accent": "#1f8ef1"},
    "Neon Violet":     {"bg1": "#12001e", "bg2": "#1e0033", "accent": "#bb00ff"},
    "Emerald Abyss":   {"bg1": "#001a14", "bg2": "#00322b", "accent": "#00ff99"},
    "Cyber Pink":      {"bg1": "#0a0014", "bg2": "#1a0033", "accent": "#ff00aa"},
    "Steel Indigo":    {"bg1": "#0c0f1a", "bg2": "#1c2333", "accent": "#7dd3fc"},
    "Velvet Crimson":  {"bg1": "#1a0000", "bg2": "#330000", "accent": "#e11d48"},
    "Arctic Noir":     {"bg1": "#050b12", "bg2": "#0e1822", "accent": "#38bdf8"},
}

# ------------------ THEME RANDOMIZATION ------------------
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Dark"

theme_set = dark_themes if st.session_state.theme_mode == "Dark" else light_themes
random_theme_name = random.choice(list(theme_set.keys()))
st.session_state.selected_theme = random_theme_name
st.session_state.theme_colors = theme_set[random_theme_name]

# ------------------ MODE TOGGLE ------------------
col1, col2, _ = st.columns([1, 1, 6])
with col1:
    if st.button("🌞 Light Mode", use_container_width=True):
        if st.session_state.theme_mode != "Light":
            st.session_state.theme_mode = "Light"
            st.session_state.selected_theme = list(light_themes.keys())[0]
            st.session_state["show_toast"] = "Switched to Light Mode 🌞"
            st.rerun()

with col2:
    if st.button("🌙 Dark Mode", use_container_width=True):
        if st.session_state.theme_mode != "Dark":
            st.session_state.theme_mode = "Dark"
            st.session_state.selected_theme = list(dark_themes.keys())[0]
            st.session_state["show_toast"] = "Switched to Dark Mode 🌙"
            st.rerun()

# ------------------ SELECT THEME SET ------------------
themes = light_themes if st.session_state.theme_mode == "Light" else dark_themes
if st.session_state.selected_theme not in themes:
    st.session_state.selected_theme = list(themes.keys())[0]

# ------------------ THEME BUTTONS ------------------
cols = st.columns(len(themes))
for i, (theme_name, data) in enumerate(themes.items()):
    accent = data["accent"]
    display_name = theme_name.replace(" ", "\n")  # show theme name in 2 lines
    if cols[i].button(display_name, key=f"theme_{theme_name}"):
        if st.session_state.selected_theme != theme_name:
            st.session_state.selected_theme = theme_name
            st.session_state["show_toast"] = f"🎨 Switched to {theme_name}"
            st.rerun()

# ------------------ SELECTED THEME ------------------
selected = themes[st.session_state.selected_theme]
bg1, bg2, accent = selected["bg1"], selected["bg2"], selected["accent"]
text_color = "#111" if st.session_state.theme_mode == "Light" else "#e6e6e6"

# ------------------ TOAST MESSAGE ------------------
if "show_toast" in st.session_state:
    toast_message = st.session_state["show_toast"]
    st.markdown(f"""
    <div style="
        position: fixed;
        top: 20px;
        right: 20px;
        background: {accent};
        color: white;
        padding: 12px 20px;
        border-radius: 10px;
        font-weight: 600;
        box-shadow: 0 4px 12px {accent}77;
        z-index: 9999;
        animation: fadeIn 0.3s ease, fadeOut 0.6s ease 2.5s forwards;
    ">
        {toast_message}
    </div>
    <style>
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(-10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes fadeOut {{
        from {{ opacity: 1; }}
        to {{ opacity: 0; transform: translateY(-10px); }}
    }}
    </style>
    """, unsafe_allow_html=True)
    time.sleep(2.5)
    del st.session_state["show_toast"]

# ------------------ HEADER & APP STYLING ------------------
def get_contrast_color(hex_color):
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    return "#000000" if brightness > 155 else "#ffffff"

title_text_color = get_contrast_color(accent)

st.markdown(f"""
<style>
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
[data-testid="stAppViewContainer"] {{
    background: radial-gradient(circle at top left, {bg2}, {bg1});
    font-family: "Inter", sans-serif;
    background-size: 400% 400%;
    animation: bgShift 60s ease infinite;
    transition: all 0.3s ease-in-out;
}}
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
tbody tr:hover {{
    background-color: {accent}11 !important;
    transform: scale(1.01);
    transition: all 0.2s ease;
    box-shadow: 0 0 8px {accent}55;
}}
::-webkit-scrollbar {{
    width: 10px;
}}
::-webkit-scrollbar-thumb {{
    background: linear-gradient({accent}, {accent}cc);
    border-radius: 10px;
}}
</style>
""", unsafe_allow_html=True)

# ------------------ APP TITLE ------------------
st.markdown(f"""
<div style="
    background-color: {accent};
    color: {title_text_color};
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
















