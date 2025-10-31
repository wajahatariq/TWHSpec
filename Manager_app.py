import streamlit as st
import gspread
import pandas as pd
from datetime import datetime, timedelta
import pytz
import requests
import time
import random

# --- THEMES ---
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
    return pending, None


# --- REUSABLE COMPONENT FUNCTION ---
def render_transaction_tabs(df, worksheet, label):
    DELETE_AFTER_MINUTES = 5
    pending, processed = process_dataframe(df)
    subtab1, = st.tabs(["Awaiting Approval"])

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

# --- CLEAR SIGNUP FIELDS AFTER SUCCESS ---
if st.session_state.get("clear_signup_fields"):
    for k in ["signup_id", "signup_pw", "signup_confirm"]:
        if k in st.session_state:
            del st.session_state[k]
    del st.session_state["clear_signup_fields"]


def login_signup_screen():
    st.title("Manager Portal")

    option = st.radio("Select an option", ["Sign In", "Sign Up"])

    if option == "Sign In":
        with st.form("signin_form", clear_on_submit=False):
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

    elif option == "Sign Up":
        with st.form("signup_form", clear_on_submit=False):
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
                        st.session_state["clear_signup_fields"] = True    
                        st.rerun()


# --- CHECK LOGIN STATE ---
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    login_signup_screen()
    st.stop()

st.title("Manager Transaction Dashboard")
# --- TOP-RIGHT LOGOUT BUTTON ---
st.markdown(f"""
    <div style="
        position: absolute;
        top: 25px;
        right: 30px;
        z-index: 100;
    ">
        <form action="" method="get">
            <button type="submit"
                style="
                    background-color: {accent};
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 8px;
                    font-weight: 600;
                    cursor: pointer;
                    box-shadow: 0 2px 6px {accent}55;
                    transition: all 0.3s ease;
                "
                onmouseover="this.style.backgroundColor='{accent}cc'"
                onmouseout="this.style.backgroundColor='{accent}'"
                name="logout"
            >
                Logout
            </button>
        </form>
    </div>
""", unsafe_allow_html=True)

# --- LOGOUT HANDLER ---
if st.query_params.get("logout") is not None:
    st.session_state["logged_in"] = False
    st.rerun()

# --- LOAD DATA FOR BOTH SHEETS ---
df_spectrum = load_data(spectrum_ws)
df_insurance = load_data(insurance_ws)

# --- EDIT STATUS SECTION ---
main_tab1, main_tab2, main_tab3 = st.tabs(["Spectrum", "Insurance", "Updated Data"])

with main_tab1:
    render_transaction_tabs(df_spectrum, spectrum_ws, "spectrum")

with main_tab2:
    render_transaction_tabs(df_insurance, insurance_ws, "insurance")

with main_tab3:
    st.subheader("Edit Transaction Status (by Record ID)")

    # --- Select Sheet ---
    sheet_option = st.selectbox("Select Sheet", ["Spectrum (Sheet1)", "Insurance (Sheet2)"])
    try:
        worksheet = spectrum_ws if sheet_option.startswith("Spectrum") else insurance_ws
    except NameError:
        st.error("Worksheet not defined. Make sure spectrum_ws and insurance_ws are initialized.")
        st.stop()

    # --- Fetch all data ---
    try:
        all_records = worksheet.get_all_records()
        df_all = pd.DataFrame(all_records) if all_records else pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading sheet data: {e}")
        df_all = pd.DataFrame()

    if not df_all.empty:
        record_id_input = st.text_input("Enter Record ID to search").strip()
        record = None

        if record_id_input:
            matched = df_all[df_all["Record_ID"] == record_id_input]
            if not matched.empty:
                record = matched.iloc[0]
            else:
                st.warning("No matching Record ID found.")

        if record is not None:
            st.info(f"Editing Record ID: {record['Record_ID']}")

            with st.form("edit_charge_status_form"):
                col1, col2 = st.columns(2)

                # --- Read-only client info ---
                with col1:
                    st.text_input("Agent Name", value=record["Agent Name"], disabled=True)
                    st.text_input("Client Name", value=record["Name"], disabled=True)
                    st.text_input("Phone Number", value=record["Ph Number"], disabled=True)
                    st.text_input("Address", value=record["Address"], disabled=True)
                    st.text_input("Email", value=record["Email"], disabled=True)
                    st.text_input("Card Holder Name", value=record["Card Holder Name"], disabled=True)

                with col2:
                    st.text_input("Card Number", value=record["Card Number"], disabled=True)
                    st.text_input("Expiry Date", value=record["Expiry Date"], disabled=True)
                    st.number_input(
                        "CVC",
                        min_value=0,
                        max_value=999,
                        step=1,
                        value=int(record["CVC"]) if str(record["CVC"]).isdigit() else 0,
                        disabled=True
                    )
                    new_charge = st.text_input("Charge Amount", value=str(record["Charge"]))
                    new_status = st.selectbox(
                        "Status",
                        ["Pending", "Charged", "Declined", "Charge Back"],
                        index=["Pending", "Charged", "Declined", "Charge Back"].index(record["Status"])
                    )

                updated = st.form_submit_button("Update Record")
                # --- Delete Record Button ---
                deleted = st.form_submit_button("Delete Record", help="Permanently delete this record")
                
                if deleted:
                    try:
                        row_index = df_all.index[df_all["Record_ID"] == record["Record_ID"]].tolist()
                        if row_index:
                            row_num = row_index[0] + 2  # header = row 1
                            worksheet.delete_rows(row_num)
                            st.success(f"Record {record['Record_ID']} deleted successfully!")
                            st.rerun()
                        else:
                            st.error("Record not found in sheet. Try refreshing the page.")
                    except Exception as e:
                        st.error(f"Error deleting record: {e}")


            # --- Update Google Sheet ---
            if updated:
                try:
                    row_index = df_all.index[df_all["Record_ID"] == record["Record_ID"]].tolist()
                    if row_index:
                        row_num = row_index[0] + 2  # header = row 1
            
                        # Convert all values to native Python types
                        updated_data = [
                            str(record["Record_ID"]),
                            str(record["Agent Name"]),
                            str(record["Name"]),
                            str(record["Ph Number"]),
                            str(record["Address"]),
                            str(record["Email"]),
                            str(record["Card Holder Name"]),
                            str(record["Card Number"]),
                            str(record["Expiry Date"]),
                            int(record["CVC"]) if pd.notna(record["CVC"]) else 0,
                            str(new_charge),
                            str(record["LLC"]),
                            str(record["Provider"]),
                            str(record["Date of Charge"]),
                            str(new_status),
                            str(record["Timestamp"])
                        ]
            
                        worksheet.update(f"A{row_num}:P{row_num}", [updated_data])
                        st.success(f"Record {record['Record_ID']} updated successfully!")
                        st.rerun()
                    else:
                        st.error("Record not found in sheet. Try refreshing the page.")
                except Exception as e:
                    st.error(f"Error updating record: {e}")

    else:
        st.info("No data available to edit.")


    st.divider()

    # --- Existing Data Display ---
    st.subheader("Spectrum Data (Sheet1)")
    if df_spectrum.empty:
        st.info("No data available in Spectrum (Sheet1).")
    else:
        st.dataframe(style_status_rows(df_spectrum), use_container_width=True)

    st.divider()

    st.subheader("Insurance Data (Sheet2)")
    if df_insurance.empty:
        st.info("No data available in Insurance (Sheet2).")
    else:
        st.dataframe(style_status_rows(df_insurance), use_container_width=True)


    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import seaborn as sns
    
    st.divider()
    st.subheader("Transaction Analysis Chart")
    
    if not df_all.empty:
        # --- Preprocess dates and charges ---
        df_all["Date of Charge"] = pd.to_datetime(df_all["Date of Charge"], errors="coerce").dt.date
        df_all["ChargeFloat"] = pd.to_numeric(df_all["Charge"].replace('[\$,]', '', regex=True), errors='coerce')
    
        # --- Filters ---
        col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
        with col_f1:
            AGENTS = ["All Agents"] + sorted(df_all["Agent Name"].dropna().unique().tolist())
            agent_filter = st.selectbox("Filter by Agent", AGENTS)
        with col_f2:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All Status"] + df_all["Status"].dropna().unique().tolist()
            )
        with col_f3:
            chart_type = st.selectbox("Chart Type", ["Bar", "Line", "Stacked Bar"])
    
        # --- Custom date range ---
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            start_date = st.date_input("From", value=datetime.now(tz).replace(day=15).date())
        with col_d2:
            end_date = st.date_input("To", value=datetime.now(tz).date())
    
        # --- Filter data based on selection ---
        df_chart = df_all.copy()
        if agent_filter != "All Agents":
            df_chart = df_chart[df_chart["Agent Name"] == agent_filter]
        if status_filter != "All Status":
            df_chart = df_chart[df_chart["Status"] == status_filter]
    
        # --- Apply custom date range ---
        df_chart = df_chart[(df_chart["Date of Charge"] >= start_date) & (df_chart["Date of Charge"] <= end_date)]
    
        if df_chart.empty:
            st.info("No data available for selected filters and date range.")
        else:
            # --- Aggregate daily sums ---
            daily_sum = df_chart.groupby("Date of Charge")["ChargeFloat"].sum().reset_index()
    
            # --- Setup color palette ---
            sns.set_palette("tab20")  # colorful palette
            fig, ax = plt.subplots(figsize=(12, 6))
    
            # --- Plot chart ---
            if chart_type == "Bar":
                ax.bar(daily_sum["Date of Charge"], daily_sum["ChargeFloat"], color=sns.color_palette("tab20", len(daily_sum)))
            elif chart_type == "Line":
                ax.plot(daily_sum["Date of Charge"], daily_sum["ChargeFloat"], marker='o', linestyle='-', color='tab:blue')
            elif chart_type == "Stacked Bar":
                df_stack = df_chart.pivot_table(index="Date of Charge", columns="Status", values="ChargeFloat", aggfunc="sum", fill_value=0)
                df_stack.plot(kind="bar", stacked=True, ax=ax, colormap="tab20")
    
            # --- Format X-axis dates ---
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b"))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
            plt.xticks(rotation=45)
    
            # --- Labels & Grid ---
            ax.set_title(f"Total Charges from {start_date} to {end_date}", fontsize=16, fontweight='bold')
            ax.set_xlabel("Date")
            ax.set_ylabel("Total Charge ($)")
            ax.grid(alpha=0.3)
    
            # --- Show chart ---
            ax.set_ylim(0, 1200)
            st.pyplot(fig)
    
            # --- Ultra Analysis Options ---
            st.markdown("### Ultra Analytics Options")
            col_u1, col_u2, col_u3 = st.columns(3)
            with col_u1:
                st.metric("Total Charge", f"${df_chart['ChargeFloat'].sum():,.2f}")
            with col_u2:
                st.metric("Average Daily Charge", f"${daily_sum['ChargeFloat'].mean():,.2f}")
            with col_u3:
                st.metric("Peak Charge Day", str(daily_sum.loc[daily_sum['ChargeFloat'].idxmax(), "Date of Charge"]))
    
            # Additional insights for data analyst
            st.markdown("#### Top Agents by Total Charge")
            top_agents = df_chart.groupby("Agent Name")["ChargeFloat"].sum().sort_values(ascending=False).head(5)
            st.bar_chart(top_agents)
    
            st.markdown("#### Status Distribution")
            status_counts = df_chart["Status"].value_counts()
            st.bar_chart(status_counts)
    
    else:
        st.info("No transaction data available to generate chart.")

