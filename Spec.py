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

import streamlit.components.v1 as components

# compute active_index (1-based) if not already computed
theme_keys = list(themes.keys())
active_index = theme_keys.index(st.session_state.selected_theme) + 1

# --- Animated header + CSS (shimmer, capsule entry, hover, pulse) ---
st.markdown(f"""
<style>
/* ---------------- keyframes ---------------- */
@keyframes pulseGlow {{
  0% {{ box-shadow: 0 0 0px {accent}44; }}
  50% {{ box-shadow: 0 0 20px {accent}aa; }}
  100% {{ box-shadow: 0 0 0px {accent}44; }}
}}
@keyframes bounce {{
  0%,100% {{ transform: translateY(0); }}
  50% {{ transform: translateY(-4px); }}
}}
@keyframes slideUp {{
  0% {{ opacity: 0; transform: translateY(8px); }}
  100% {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes shimmerText {{
  0% {{ background-position: -200% 0; }}
  100% {{ background-position: 200% 0; }}
}}
@keyframes themeFade {{
  0% { opacity: 0.25; filter: blur(3px); transform: scale(0.995); }
  100% { opacity: 1; filter: blur(0); transform: scale(1); }
}

/* ---------------- global / container ---------------- */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], [data-testid="stHeader"] {{
    background-color: {bg1} !important;
    color: {"#111" if st.session_state.theme_mode=="Light" else "#e6e6e6"} !important;
    color-scheme: {"light" if st.session_state.theme_mode == "Light" else "dark"} !important;
}}
[data-testid="stAppViewContainer"] {{
    background: radial-gradient(circle at top left, {bg2}, {bg1});
    background-size: 200% 200%;
    transition: background 0.6s ease, color 0.3s ease;
    font-family: "Inter", system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
}}

/* ---------- header shimmer (subtle) ---------- */
.app-header {{
  display: block;
  width: 100%;
  margin-bottom: 22px;
  border-radius: 12px;
  padding: 16px 22px;
  color: white;
  text-align: center;
  font-weight: 700;
  font-size: 20px;
  box-shadow: 0 6px 22px {accent}33;
  background: linear-gradient(90deg, {accent}, {accent}cc);
  position: relative;
  overflow: hidden;
}}
.app-header .shimmer {{
  display: inline-block;
  background: linear-gradient(90deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.28) 50%, rgba(255,255,255,0.08) 100%);
  background-size: 200% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: shimmerText 3.8s linear infinite;
}}

/* ---------- capsule entry + glow + hover + active pulse ---------- */
div[data-testid="column"] > div > button {{
  border-radius: 999px !important;
  font-weight: 700 !important;
  padding: 8px 14px !important;
  margin: 6px 8px 10px 0 !important;
  background: transparent !important;
  transition: transform 260ms cubic-bezier(.2,.9,.2,1), box-shadow 260ms;
  box-shadow: 0 0 8px {accent}22;
  color: {accent} !important;
  border: 1px solid {accent}33 !important;
  opacity: 0;
  transform: translateY(8px);
}
/* staggered slideUp for capsules (using nth-child based on position) */
{"".join([f"div[data-testid='column'] > div > button:nth-child({i+1}) {{ animation: slideUp 420ms ease forwards; animation-delay: {i*45}ms; }}\n" for i in range(len(theme_keys))])}

/* hover: glow and bounce */
div[data-testid="column"] > div > button:hover {{
  background: {accent}22 !important;
  color: white !important;
  box-shadow: 0 0 28px {accent}aa, inset 0 0 10px {accent}55 !important;
  transform: translateY(-4px) scale(1.06);
  animation: bounce 420ms ease;
}
/* active: target via nth-child using Python computed index */
div[data-testid="column"] > div:nth-child({active_index}) > button {{
  background: {accent}33 !important;
  color: white !important;
  border: 1px solid {accent}cc !important;
  animation: pulseGlow 2.4s infinite ease-in-out;
  box-shadow: 0 0 26px {accent}bb !important;
  transform: translateY(-2px);
}}

/* tables, alerts, scrollbar */
thead tr th {{ background-color: {accent} !important; color: white !important; font-weight: 600 !important; }}
tbody tr:hover {{ background-color: {accent}11 !important; transition: background 160ms; }}
.stAlert {{ border-radius: 10px !important; background: {accent}14 !important; border-left: 5px solid {accent} !important; }}

/* theme fade helper class toggled by JS */
.theme-fade {{
  animation: themeFade 340ms ease forwards;
}}
</style>
""", unsafe_allow_html=True)

# --- Header (uses the .app-header class) ---
st.markdown(f"""
<div class="app-header">
  <span class="shimmer">Client Management System — Techware Hub</span>
</div>
""", unsafe_allow_html=True)

# --- Tiny JS to trigger .theme-fade on DOM changes (smooth transitions on theme switch) ---
# We embed a MutationObserver to add .theme-fade to the main container briefly whenever content updates.
components.html(f"""
<script>
(function() {{
  const container = document.querySelector('[data-testid="stAppViewContainer"]');
  if (!container) return;
  let timer = null;
  const obs = new MutationObserver((mutations) => {{
    // skip if no visible mutation
    if (timer) {{
      clearTimeout(timer);
    }}
    container.classList.remove('theme-fade');
    // reflow to restart animation
    void container.offsetWidth;
    container.classList.add('theme-fade');
    timer = setTimeout(() => container.classList.remove('theme-fade'), 420);
  }});
  obs.observe(container, {{ childList: true, subtree: true, attributes: true }});
  // run once on load to animate in
  container.classList.add('theme-fade');
  setTimeout(() => container.classList.remove('theme-fade'), 420);
}})();
</script>
""", height=0)

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























