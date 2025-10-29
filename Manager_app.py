import streamlit as st
import gspread
import pandas as pd
from datetime import datetime, timedelta
import pytz
import requests

# --- CONFIG ---
st.set_page_config(page_title="Manager Dashboard", layout="wide")
light_themes = {
    "Sunlit Coral":    {"bg1": "#fff8f2", "bg2": "#ffe8df", "accent": "#ff6f61"},
    "Skyline Blue":    {"bg1": "#f0f8ff", "bg2": "#dcefff", "accent": "#3b82f6"},
    "Golden Sand":     {"bg1": "#fffbea", "bg2": "#fff2d1", "accent": "#f59e0b"},
    "Lilac Mist":      {"bg1": "#faf5ff", "bg2": "#f3e8ff", "accent": "#a78bfa"},
    "Mint Breeze":     {"bg1": "#f0fff9", "bg2": "#d7fff0", "accent": "#10b981"},
}

dark_themes = {
    "Obsidian Night":  {"bg1": "#0b0c10", "bg2": "#1f2833", "accent": "#66fcf1"},
    "Crimson Shadow":  {"bg1": "#1c0b0b", "bg2": "#2a0f0f", "accent": "#ff4444"},
    "Deep Ocean":      {"bg1": "#0a1b2a", "bg2": "#0d2c4a", "accent": "#1f8ef1"},
    "Neon Violet":     {"bg1": "#12001e", "bg2": "#1e0033", "accent": "#bb00ff"},
    "Emerald Abyss":   {"bg1": "#001a14", "bg2": "#00322b", "accent": "#00ff99"},
}

# --- SESSION STATE ---
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Dark"
if "selected_theme" not in st.session_state:
    st.session_state.selected_theme = None

# --- MODE TOGGLE ---
col1, col2, _ = st.columns([1,1,6])
with col1:
    if st.button("🌞 Light Mode", use_container_width=True):
        st.session_state.theme_mode = "Light"
with col2:
    if st.button("🌙 Dark Mode", use_container_width=True):
        st.session_state.theme_mode = "Dark"

themes = light_themes if st.session_state.theme_mode == "Light" else dark_themes
if st.session_state.selected_theme not in themes:
    st.session_state.selected_theme = list(themes.keys())[0]

# --- CAPSULE BUTTONS ---
cols = st.columns(len(themes))
for i, (theme_name, data) in enumerate(themes.items()):
    accent = data["accent"]
    if cols[i].button(theme_name, key=f"theme_{theme_name}"):
        st.session_state.selected_theme = theme_name

# --- SELECTED THEME ---
selected = themes[st.session_state.selected_theme]
bg1, bg2, accent = selected["bg1"], selected["bg2"], selected["accent"]
text_color = "#111" if st.session_state.theme_mode=="Light" else "#e6e6e6"

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

# --- HEADER ---
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


def send_pushbullet_notification(title, message):
    try:
        access_token = st.secrets["pushbullet_token"]
        headers = {"Access-Token": access_token, "Content-Type": "application/json"}
        data = {"type": "note", "title": title, "body": message}
        response = requests.post("https://api.pushbullet.com/v2/pushes", json=data, headers=headers)
        if response.status_code != 200:
            st.warning("Pushbullet notification failed to send.")
    except Exception as e:
        st.error(f"Pushbullet error: {e}")
# --- GOOGLE SHEET SETUP ---
creds = st.secrets["gcp_service_account"]
gc = gspread.service_account_from_dict(creds)
SHEET_NAME = "Company_Transactions"

import hashlib

# --- USERS SHEET ---
users_ws = gc.open(SHEET_NAME).worksheet("Sheet3")

# --- FUNCTIONS FOR USERS ---
def load_users():
    """Load users from Sheet3 into a DataFrame."""
    records = users_ws.get_all_records()
    return pd.DataFrame(records)

def hash_password(password):
    """Return a SHA-256 hash of the password."""
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(user_id, password):
    """Add a new user to Sheet3 (hashed password)."""
    hashed_pw = hash_password(password)
    users_ws.append_row([user_id, hashed_pw])

def validate_login(user_id, password):
    """Check login credentials."""
    users_df = load_users()
    if users_df.empty:
        return False
    hashed_pw = hash_password(password)
    match = users_df[(users_df["ID"] == user_id) & (users_df["Password"] == hashed_pw)]
    return not match.empty

# Access the two worksheets
spectrum_ws = gc.open(SHEET_NAME).worksheet("Sheet1")
insurance_ws = gc.open(SHEET_NAME).worksheet("Sheet2")

# --- REFRESH BUTTON ---
if st.button("Refresh Now"):
    st.rerun()

# --- LOAD DATA FUNCTION ---
def load_data(ws):
    records = ws.get_all_records()
    df = pd.DataFrame(records)

    # Ensure 'Expiry Date' keeps leading zeros and no slashes
    if "Expiry Date" in df.columns:
        df["Expiry Date"] = (
            df["Expiry Date"]
            .astype(str)
            .str.replace("/", "", regex=False)  # remove any slashes if present
            .str.strip()
            .str.zfill(4)  # pad with zeros to make sure it's 4 digits
        )

    return df

    return df

# --- FILTER FUNCTION ---
def process_dataframe(df):
    DELETE_AFTER_MINUTES = 5
    if df.empty:
        return df, df
    if "Timestamp" in df.columns:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        df["Timestamp"] = df["Timestamp"].apply(
            lambda x: x.tz_localize(None) if hasattr(x, "tzinfo") and x.tzinfo else x
        )
        now = datetime.now(tz).replace(tzinfo=None)
        cutoff = now - timedelta(minutes=DELETE_AFTER_MINUTES)
        df = df[
            (df["Status"] == "Pending") |
            ((df["Status"].isin(["Charged", "Declined"])) & (df["Timestamp"] >= cutoff))
        ]
    pending = df[df["Status"] == "Pending"]
    processed = df[df["Status"].isin(["Charged", "Declined"])]
    return pending, processed

# --- REUSABLE COMPONENT FUNCTION ---
def render_transaction_tabs(df, worksheet, label):
    DELETE_AFTER_MINUTES = 5
    pending, processed = process_dataframe(df)
    subtab1, subtab2 = st.tabs(["Awaiting Approval", "Processed Transactions"])

    # --- PENDING TAB ---
    with subtab1:
        st.subheader("Pending Transactions")
        if pending.empty:
            st.info("No pending transactions.")
        else:
            for i, row in pending.iterrows():
                with st.expander(f"{row['Agent Name']} — {row['Charge']} ({row['LLC']})"):
                    st.write(f"**Card Number:** {row['Card Number']}")
                    st.write(f"**Expiry Date:** {row['Expiry Date']}")
                    st.write(f"**Charge:** {row['Charge']}")
                    # Safely split the Card Holder Name
                    card_holder = str(row.get('Card Holder Name', '')).strip()
                    name_parts = card_holder.split()
                    
                    first_name = name_parts[0] if len(name_parts) > 0 else ''
                    last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                    
                    st.write(f"**First Name:** {first_name}")
                    st.write(f"**Last Name:** {last_name}")

                    st.write(f"**Address:** {row['Address']}")
                    st.write(f"**CVC:** {row['CVC']}")
                    st.write(f"**Card Holder Name:** {card_holder}")

                    row_number = i + 2  # header is row 1
                    col_number = df.columns.get_loc("Status") + 1

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Approve", key=f"approve_{label}_{i}"):
                            worksheet.update_cell(row_number, col_number, "Charged")
                            message = (
                                f"Charge: {row.get('Charge', 'Nil')}\n"
                                f"Client Name: {row.get('Name', 'Nil')}\n"
                                f"Phone Number: {row.get('Ph Number', 'Nil')}\n"
                                f"Address: {row.get('Address', 'Nil')}\n"
                                f"Email: {row.get('Email', 'Nil')}\n"
                                f"Provider: {row.get('Provider', 'Nil')}"
                            )
                            send_pushbullet_notification("Transaction Approved ✅", message)
                            st.success("Approved successfully!")
                            st.rerun()
                    with col2:
                        if st.button("Decline", key=f"decline_{label}_{i}"):
                            worksheet.update_cell(row_number, col_number, "Declined")
                            st.error("Declined successfully!")
                            st.rerun()

    # --- PROCESSED TAB ---
    with subtab2:
        st.subheader(f"Processed Transactions (last {DELETE_AFTER_MINUTES} minutes)")
        if processed.empty:
            st.info("No processed transactions yet.")
        else:
            st.dataframe(processed)

st.title("Manager Portal")
# --- AUTHENTICATION SYSTEM ---
def login_signup_screen():

option = st.radio("Select an option", ["Sign In", "Sign Up"])

if option == "Sign In":
    with st.form("signin_form"):
        user_id = st.text_input("User ID", key="signin_id")
        password = st.text_input("Password", type="password", key="signin_pw")
        submitted = st.form_submit_button("Login")

        if submitted:
            if validate_login(user_id, password):
                st.session_state["logged_in"] = True
                st.session_state["user_id"] = user_id
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error("❌ Invalid ID or password")

elif option == "Sign Up":   # ✅ This should be OUTSIDE and aligned with the first `if`
    with st.form("signup_form"):
        new_id = st.text_input("Choose User ID", key="signup_id")
        new_pw = st.text_input("Choose Password", type="password", key="signup_pw")
        confirm_pw = st.text_input("Confirm Password", type="password", key="signup_confirm")
        submitted = st.form_submit_button("Register")

        if submitted:
            if not new_id or not new_pw:
                st.warning("Please fill in all fields.")
            elif new_pw != confirm_pw:
                st.warning("Passwords do not match.")
            else:
                users_df = load_users()
                if not users_df.empty and new_id in users_df["ID"].values:
                    st.error("User ID already exists. Try another.")
                else:
                    add_user(new_id, new_pw)
                    st.success("🎉 Account created! You can now log in.")
                    st.session_state["signup_id"] = ""
                    st.session_state["signup_pw"] = ""
                    st.session_state["signup_confirm"] = ""
                    st.rerun()



# --- CHECK LOGIN STATE ---
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    login_signup_screen()
    st.stop()

st.title("Manager Transaction Dashboard")
st.sidebar.success(f"Welcome, {st.session_state['user_id']}")
if st.sidebar.button("Logout"):
    st.session_state["logged_in"] = False
    st.rerun()


# --- LOAD DATA FOR BOTH SHEETS ---
df_spectrum = load_data(spectrum_ws)
df_insurance = load_data(insurance_ws)

main_tab1, main_tab2 = st.tabs(["Spectrum", "Insurance"])

# --- SPECTRUM TAB ---
with main_tab1:
    render_transaction_tabs(df_spectrum, spectrum_ws, "spectrum")

# --- INSURANCE TAB ---
with main_tab2:
    render_transaction_tabs(df_insurance, insurance_ws, "insurance")
