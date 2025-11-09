# app.py
# Unified Streamlit app with single login and role-based views (Manager vs Agent).
# Adds Sign In / Sign Up, role + agent assignment, and password migration to SHA-256 if legacy plain text exists.
# Workflow, sheet names, agent names, providers, and data schema remain unchanged.
# Columns in Sheet3: ID | Password | Role | Agent Name

import streamlit as st
import gspread
import pandas as pd
import pytz
import requests
import hashlib
import random
from pathlib import Path
from datetime import datetime, timedelta, time as dtime

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



# ==============================
# Timezone and constants
# ==============================
tz = pytz.timezone("Asia/Karachi")
SHEET_NAME = "Company_Transactions"

# ==============================
# Google Sheets setup
# ==============================
creds = st.secrets["gcp_service_account"]
gc = gspread.service_account_from_dict(creds)
ws_spectrum = gc.open(SHEET_NAME).worksheet("Sheet1")
ws_insurance = gc.open(SHEET_NAME).worksheet("Sheet2")
ws_users = gc.open(SHEET_NAME).worksheet("Sheet3")

# ==============================
# Agent constants (unchanged)
# ==============================
AGENTS = ["Select Agent", "Arham Kaleem", "Arham Ali", "Haziq"]
LLC_OPTIONS = ["Select LLC", "Bite Bazaar LLC", "Apex Prime Solutions"]
PROVIDERS = ["Select Provider", "Spectrum", "Insurance", "Xfinity", "Frontier", "Optimum"]

# ==============================
# Auth utilities (Sheet3)
# ==============================
def load_users_df() -> pd.DataFrame:
    rows = ws_users.get_all_records()
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["ID", "Password", "Role", "Agent Name"])

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def migrate_plain_password_if_needed(user_id: str, input_plain: str) -> bool:
    """
    If the stored Password equals the plaintext the user typed,
    update it to SHA-256 hash in the sheet. Returns True if migrated.
    """
    data = ws_users.get_all_values()
    if not data:
        return False
    header = data[0]
    try:
        id_idx = header.index("ID")
        pw_idx = header.index("Password")
    except ValueError:
        return False
    for r_idx in range(1, len(data)):
        row = data[r_idx]
        if len(row) <= max(id_idx, pw_idx):
            continue
        if row[id_idx] == user_id:
            stored_pw = row[pw_idx]
            if stored_pw == input_plain:
                new_hash = hash_password(input_plain)
                ws_users.update_cell(r_idx + 1, pw_idx + 1, new_hash)  # +1: 1-based
                return True
            break
    return False

def validate_login(user_id: str, password: str):
    users = load_users_df()
    if users.empty:
        return None
    hashed = hash_password(password)
    row = users[(users["ID"] == user_id) & (users["Password"] == hashed)]
    if row.empty:
        # Try legacy plain-text migration path
        migrated = migrate_plain_password_if_needed(user_id, password)
        if migrated:
            users = load_users_df()
            row = users[(users["ID"] == user_id) & (users["Password"] == hash_password(password))]
    if row.empty:
        return None
    record = row.iloc[0].to_dict()
    role = str(record.get("Role", "")).strip()
    agent_name = str(record.get("Agent Name", "")).strip()
    return {"id": user_id, "role": role, "agent_name": agent_name}

def create_user(user_id: str, password: str, role: str, agent_name: str = "") -> str:
    """
    Returns empty string on success; else error message.
    """
    if not user_id or not password or not role:
        return "All fields are required."
    users = load_users_df()
    if not users.empty and user_id in users["ID"].values:
        return "User ID already exists."
    if role == "Agent":
        if agent_name not in AGENTS or agent_name == "Select Agent":
            return "Please select a valid Agent Name for role Agent."
    elif role != "Manager":
        return "Role must be Manager or Agent."
    hashed = hash_password(password)
    ws_users.append_row([user_id, hashed, role, agent_name if role == "Agent" else ""])
    return ""

# ==============================
# Pushbullet
# ==============================
def send_pushbullet(title: str, message: str):
    try:
        token = st.secrets["pushbullet_token"]
        headers = {"Access-Token": token, "Content-Type": "application/json"}
        data = {"type": "note", "title": title, "body": message}
        r = requests.post("https://api.pushbullet.com/v2/pushes", json=data, headers=headers, timeout=15)
        if r.status_code != 200:
            st.warning(f"Pushbullet failed: {r.status_code}")
    except Exception as e:
        st.error(f"Pushbullet error: {e}")

# ==============================
# Data helpers
# ==============================
def load_df(ws) -> pd.DataFrame:
    records = ws.get_all_records()
    df = pd.DataFrame(records) if records else pd.DataFrame()
    if "Expiry Date" in df.columns:
        df["Expiry Date"] = (
            df["Expiry Date"].astype(str).str.replace("/", "", regex=False).str.strip().str.zfill(4)
        )
    return df

def style_status_rows(df: pd.DataFrame):
    if "Status" not in df.columns or df.empty:
        return df
    def highlight_row(row):
        if row["Status"] == "Charged":
            return ["background-color: darkgreen"] * len(row)
        elif row["Status"] == "Charge Back":
            return ["background-color: red"] * len(row)
        else:
            return [""] * len(row)
    try:
        return df.style.apply(highlight_row, axis=1)
    except Exception:
        return df

def ensure_numeric_charge(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if "ChargeFloat" not in df.columns:
        df["ChargeFloat"] = pd.to_numeric(
            df.get("Charge", pd.Series(dtype=str)).replace('[\$,]', '', regex=True),
            errors='coerce'
        ).fillna(0.0)
    return df

def time_in_range(start: dtime, end: dtime, x: dtime) -> bool:
    if start <= end:
        return start <= x < end
    return start <= x or x < end

from datetime import datetime, timedelta, time as dtime

def compute_night_window_totals(df_all: pd.DataFrame, agent_filter: str = None) -> float:
    if df_all.empty:
        return 0.0

    df = df_all.copy()
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    df = df.dropna(subset=["Timestamp"])
    df = ensure_numeric_charge(df)

    now = datetime.now(tz)

    # Night window always from today 6 PM to tomorrow 9 AM
    window_start = datetime.combine(now.date(), dtime(10, 0))  # 6:00 PM today
    window_end = datetime.combine(now.date() + timedelta(days=1), dtime(9, 0))  # 9:00 AM tomorrow

    def in_window(ts):
        return window_start <= ts <= window_end

    if agent_filter:
        df = df[df["Agent Name"] == agent_filter]

    night_df = df[(df["Status"] == "Charged") & (df["Timestamp"].apply(in_window))]

    return float(night_df["ChargeFloat"].sum())


# ==============================
# Unified Auth screen (Sign In / Sign Up)
# ==============================
def auth_screen():
    st.title("Authentication")

    tabs = st.tabs(["Sign In", "Sign Up"])
    with tabs[0]:
        with st.form("login_form", clear_on_submit=False):
            user_id = st.text_input("User ID")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In")
        if submitted:
            profile = validate_login(user_id, password)
            if not profile:
                st.error("Invalid credentials.")
                st.stop()
            # Agent must have a valid agent name
            if profile["role"] == "Agent":
                if profile["agent_name"] not in AGENTS or profile["agent_name"] == "Select Agent":
                    st.error("Agent Name in users sheet is missing or not recognized.")
                    st.stop()
            st.session_state["logged_in"] = True
            st.session_state["user_id"] = profile["id"]
            st.session_state["role"] = profile["role"]
            st.session_state["agent_name"] = profile["agent_name"]
            st.rerun()

    with tabs[1]:
        users_now = load_users_df()
        bootstrap_mode = users_now.empty  # allow first user creation if sheet is empty
        st.caption("Create an account. Role determines what you can see after login.")
        with st.form("signup_form", clear_on_submit=False):
            new_id = st.text_input("New User ID")
            new_pw = st.text_input("New Password", type="password")
            new_pw2 = st.text_input("Confirm Password", type="password")
            role = st.selectbox("Role", ["Manager", "Agent"])
            agent_name = ""
            if role == "Agent":
                agent_name = st.selectbox("Agent Name (must match list)", AGENTS, index=0)
            submitted_signup = st.form_submit_button("Create Account")

        if submitted_signup:
            if new_pw != new_pw2:
                st.error("Passwords do not match.")
                st.stop()
            err = create_user(new_id, new_pw, role, agent_name if role == "Agent" else "")
            if err:
                st.error(err)
            else:
                st.success("Account created. You can now sign in.")
                # Optional: auto login after signup
                st.session_state["logged_in"] = True
                st.session_state["user_id"] = new_id
                st.session_state["role"] = role
                st.session_state["agent_name"] = agent_name if role == "Agent" else ""
                st.rerun()

# Guard: show auth if not logged in
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    auth_screen()
    st.stop()

# Logout button
st.markdown(
    f"""
    <div style="position:absolute;top:18px;right:24px;z-index:1000;">
        <form action="" method="get">
            <button type="submit"
                style="
                    background-color:{accent};
                    color:{get_contrast_color(accent)};
                    border:none;padding:8px 14px;border-radius:10px;font-weight:700;cursor:pointer;
                    box-shadow:0 2px 6px {accent}55;transition:all .2s ease;"
                name="logout"
            >
                Logout
            </button>
        </form>
    </div>
""",
    unsafe_allow_html=True,
)

if st.query_params.get("logout") is not None:
    st.session_state.clear()
    st.rerun()

# ==============================
# Load data for views
# ==============================
df_spectrum = load_df(ws_spectrum)
df_insurance = load_df(ws_insurance)

# ==============================
# MANAGER VIEW
# ==============================
def manager_view():
    st.title("Manager Transaction Dashboard")

    def process_dataframe(df):
        DELETE_AFTER_MINUTES = 5
        if df.empty:
            return df, df
        if "Timestamp" in df.columns:
            df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
            df["Timestamp"] = df["Timestamp"].apply(
                lambda x: x.tz_localize(None) if hasattr(x, "tzinfo") and x.tzinfo else x
            )
            now_naive = datetime.now(tz).replace(tzinfo=None)
            cutoff = now_naive - timedelta(minutes=DELETE_AFTER_MINUTES)
            df = df[
                (df["Status"] == "Pending") |
                ((df["Status"].isin(["Charged", "Declined"])) & (df["Timestamp"] >= cutoff))
            ]
        pending = df[df["Status"] == "Pending"]
        return pending, None

    def render_transaction_tabs(df, worksheet, label):
        pending, _ = process_dataframe(df)
        (subtab1,) = st.tabs(["Awaiting Approval"])
        with subtab1:
            st.subheader("Pending Transactions")
            if pending.empty:
                st.info("No pending transactions.")
            else:
                for i, row in pending.iterrows():
                    with st.expander(f"{row['Agent Name']} — {row['Charge']} ({row['LLC']})"):
                        st.write(f"Card Number: {row['Card Number']}")
                        st.write(f"Expiry Date: {row['Expiry Date']}")
                        st.write(f"Charge: {row['Charge']}")
                        card_holder = str(row.get("Card Holder Name", "")).strip()
                        name_parts = card_holder.split()
                        first_name = name_parts[0] if len(name_parts) > 0 else ""
                        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
                        st.write(f"First Name: {first_name}")
                        st.write(f"Last Name: {last_name}")
                        st.write(f"Address: {row['Address']}")
                        st.write(f"CVC: {row['CVC']}")
                        st.write(f"Card Holder Name: {card_holder}")

                        row_number = i + 2
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
                                send_pushbullet("Transaction Approved", message)
                                st.success("Approved successfully.")
                                st.rerun()
                        with col2:
                            if st.button("Decline", key=f"decline_{label}_{i}"):
                                worksheet.update_cell(row_number, col_number, "Declined")
                                st.error("Declined successfully.")
                                st.rerun()
    if st.button("Refresh Page", key="agent_refresh_btn"):
        st.rerun()
    tab1, tab2, tab3 = st.tabs(["Spectrum", "Insurance", "Updated Data"])
    with tab1:
        render_transaction_tabs(df_spectrum, ws_spectrum, "spectrum")
    with tab2:
        render_transaction_tabs(df_insurance, ws_insurance, "insurance")
    with tab3:
        st.subheader("Edit Transaction Status (by Record ID)")
        sheet_option = st.selectbox("Select Sheet", ["Spectrum (Sheet1)", "Insurance (Sheet2)"])
        worksheet = ws_spectrum if sheet_option.startswith("Spectrum") else ws_insurance

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
                df_all["Record_ID"] = df_all["Record_ID"].astype(str).str.strip()
                matched = df_all[df_all["Record_ID"] == record_id_input]
                if not matched.empty:
                    record = matched.iloc[0]
                else:
                    st.warning("No matching Record ID found.")

            if record is not None:
                st.info(f"Editing Record ID: {record['Record_ID']}")
                with st.form("edit_charge_status_form"):
                    col1, col2 = st.columns(2)
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
                            disabled=True,
                        )
                        new_charge = st.text_input("Charge Amount", value=str(record["Charge"]))
                        new_status = st.selectbox(
                            "Status",
                            ["Pending", "Charged", "Declined", "Charge Back"],
                            index=["Pending", "Charged", "Declined", "Charge Back"].index(record["Status"]),
                        )
                        updated = st.form_submit_button("Update Record")
                        deleted = st.form_submit_button("Delete Record")

                if deleted:
                    try:
                        row_index = df_all.index[df_all["Record_ID"] == record["Record_ID"]].tolist()
                        if row_index:
                            row_num = row_index[0] + 2
                            worksheet.delete_rows(row_num)
                            st.success(f"Record {record['Record_ID']} deleted successfully.")
                            st.rerun()
                        else:
                            st.error("Record not found in sheet.")
                    except Exception as e:
                        st.error(f"Error deleting record: {e}")

                if updated:
                    try:
                        row_index = df_all.index[df_all["Record_ID"] == record["Record_ID"]].tolist()
                        if row_index:
                            row_num = row_index[0] + 2
                            if sheet_option.startswith("Spectrum"):
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
                                    str(record["Timestamp"]),
                                ]
                                worksheet.update(f"A{row_num}:P{row_num}", [updated_data])
                            else:
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
                                    str(record["Date of Charge"]),
                                    str(new_status),
                                    str(record["Timestamp"]),
                                ]
                                worksheet.update(f"A{row_num}:O{row_num}", [updated_data])
                            st.success(f"Record {record['Record_ID']} updated successfully.")
                            st.rerun()
                        else:
                            st.error("Record not found in sheet.")
                    except Exception as e:
                        st.error(f"Error updating record: {e}")
        else:
            st.info("No data available to edit.")

        # --- Existing Data Display (scoped to the selected sheet) ---
        st.divider()
        if sheet_option.startswith("Spectrum"):
            st.subheader("Spectrum Data (Sheet1)")
        else:
            st.subheader("Insurance Data (Sheet2)")
        
        if df_all.empty:
            st.info("No data available in the selected sheet.")
        else:
            st.dataframe(style_status_rows(df_all), use_container_width=True)
        
        # --- Per-sheet analysis (scoped to the selected sheet) ---
        st.divider()
        st.subheader("Transaction Analysis (Selected Sheet)")
        
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            import seaborn as sns
        except Exception:
            st.info("Matplotlib/Seaborn not available. Skipping charts.")
        else:
            if df_all.empty:
                st.info("No data available for analysis in the selected sheet.")
            else:
                df_analysis = df_all.copy()
        
                # Parse fields
                df_analysis["Timestamp"] = pd.to_datetime(df_analysis["Timestamp"], errors="coerce")
                df_analysis = df_analysis.dropna(subset=["Timestamp"])
                df_analysis["ChargeFloat"] = pd.to_numeric(
                    df_analysis["Charge"].replace('[\\$,]', '', regex=True), errors="coerce"
                ).fillna(0.0)
        
                # Filters
                c1, c2, c3 = st.columns(3)
                with c1:
                    ag_list = ["All Agents"] + sorted(df_analysis["Agent Name"].dropna().unique().tolist())
                    agent_filter = st.selectbox("Filter by Agent", ag_list, key="ud_agent_filter")
                with c2:
                    st_list = ["All Status"] + df_analysis["Status"].dropna().unique().tolist()
                    status_filter = st.selectbox("Filter by Status", st_list, key="ud_status_filter")
                with c3:
                    chart_type = st.selectbox("Chart Type", ["Bar", "Line", "Stacked Bar"], key="ud_chart_type")
        
                d1, d2 = st.columns(2)
                with d1:
                    min_ts = df_analysis["Timestamp"].min()
                    start_date = st.date_input(
                        "From Date",
                        value=min_ts.date() if pd.notna(min_ts) else datetime.now().date(),
                        key="ud_start_date",
                    )
                    start_time = st.time_input("From Time", value=dtime(0, 0, 0), key="ud_start_time")
                with d2:
                    max_ts = df_analysis["Timestamp"].max()
                    end_date = st.date_input(
                        "To Date",
                        value=max_ts.date() if pd.notna(max_ts) else datetime.now().date(),
                        key="ud_end_date",
                    )
                    end_time = st.time_input("To Time", value=dtime(23, 59, 59), key="ud_end_time")
        
                start_dt = tz.localize(datetime.combine(start_date, start_time))
                end_dt = tz.localize(datetime.combine(end_date, end_time))
        
                # Apply filters
                df_plot = df_analysis.copy()
                if agent_filter != "All Agents":
                    df_plot = df_plot[df_plot["Agent Name"] == agent_filter]
                if status_filter != "All Status":
                    df_plot = df_plot[df_plot["Status"] == status_filter]
        
                # Localize to PKT for display range
                # If your timestamps are already PKT (not UTC), remove the next line and just filter directly
                try:
                    df_plot["Timestamp"] = df_plot["Timestamp"].dt.tz_localize("UTC").dt.tz_convert(tz)
                except (TypeError, AttributeError, ValueError):
                    # Already tz-aware or naive: fall back to naive filtering
                    pass
        
                df_plot = df_plot[(df_plot["Timestamp"] >= start_dt) & (df_plot["Timestamp"] <= end_dt)]
        
                if df_plot.empty:
                    st.info("No data available for selected filters and date range.")
                else:
                    df_plot["Hour"] = df_plot["Timestamp"].dt.floor("h")
                    hourly_sum = df_plot.groupby("Hour")["ChargeFloat"].sum().reset_index()
        
                    sns.set_palette("tab20")
                    fig, ax = plt.subplots(figsize=(12, 6))
                    if chart_type == "Bar":
                        ax.bar(hourly_sum["Hour"], hourly_sum["ChargeFloat"])
                    elif chart_type == "Line":
                        ax.plot(hourly_sum["Hour"], hourly_sum["ChargeFloat"], marker="o", linestyle="-")
                    else:
                        df_stack = df_plot.pivot_table(
                            index="Hour", columns="Status", values="ChargeFloat", aggfunc="sum", fill_value=0
                        )
                        df_stack.plot(kind="bar", stacked=True, ax=ax)
        
                    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M:%S"))
                    plt.xticks(rotation=45)
                    ax.set_xlabel("Timestamp")
                    ax.set_ylabel("Total Charge ($)")
                    ax.set_title(
                        f"Total Charges from {start_dt.strftime('%Y-%m-%d %H:%M:%S')} "
                        f"to {end_dt.strftime('%Y-%m-%d %H:%M:%S')} — {sheet_option.split()[0]}"
                    )
                    ax.grid(alpha=0.3)
                    st.pyplot(fig)
        
                    # Summary metrics (selected sheet only)
                    m1, m2, m3, m4 = st.columns(4)
                    with m1:
                        st.metric("Total Charge (Selected Sheet)", f"${df_plot['ChargeFloat'].sum():,.2f}")
                    with m2:
                        st.metric("Total Transactions", f"{len(df_plot):,}")
                    with m3:
                        avg_per_hour = hourly_sum["ChargeFloat"].mean() if not hourly_sum.empty else 0.0
                        st.metric("Average per Hour", f"${avg_per_hour:,.2f}")
                    with m4:
                        if not hourly_sum.empty:
                            peak_time = hourly_sum.loc[hourly_sum["ChargeFloat"].idxmax(), "Hour"]
                            st.metric("Peak Time", peak_time.strftime("%Y-%m-%d %H:%M:%S"))
                        else:
                            st.metric("Peak Time", "—")
                    
st.divider()
                    
if not df_all.empty:
    night_total = compute_night_window_totals(df_all.copy())

    # This won't render multiline label properly in st.metric
    st.metric(
        "Night Charged Total — Selected Sheet (Today's Window)",
        f"${night_total:,.2f}"
    )
                    
                        # Floating badge with multiline labels (corrected)
badge_amount = f"${night_total:,.2f}"
st.markdown(
    f"""
    <div class="badge-fixed-top-right"
        style="
            background-color: {accent};
            box-shadow: 0 2px 6px {accent}55;
            border-radius: 10px;
            padding: 8px 14px;
            font-weight: 900;
        "
    >
      <span class="badge-label" style="color: {get_contrast_color(accent)};">Night Charged Total</span>
      <span class="badge-label" style="color: {get_contrast_color(accent)};">Today's Total</span>
      <span class="badge-amount" style="color: {get_contrast_color(accent)};">{badge_amount}</span>
    </div>
    """,
    unsafe_allow_html=True,
)


else:
    st.metric("Night Charged Total — Selected Sheet (Today's Window)", "$0.00")


# ==============================
# AGENT VIEW
# ==============================
def agent_view(agent_name: str):
    st.title(f"Agent Dashboard — {agent_name}")

    # ---------------------------------------------------------
    # Top actions
    # ---------------------------------------------------------
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("Refresh Page", key="agent_refresh_btn"):
            st.rerun()
    with col_b2:
        if st.button("Clear Form", key="agent_clear_btn"):
            for k in [
                "order_id", "name", "phone", "address", "email",
                "card_holder", "card_number", "expiry", "cvc",
                "charge", "llc", "provider", "date_of_charge"
            ]:
                if k in st.session_state:
                    del st.session_state[k]
            st.success("Form cleared.")
            st.rerun()

    # ---------------------------------------------------------
    # Load Spectrum rows for duplicate check + "My Submissions"
    # ---------------------------------------------------------
    try:
        all_records = ws_spectrum.get_all_records()
        df_all = pd.DataFrame(all_records) if all_records else pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading Spectrum data: {e}")
        df_all = pd.DataFrame()

    # ---------------------------------------------------------
    # Submit New Client (writes to Spectrum / Sheet1)
    # ---------------------------------------------------------
    st.subheader("Submit New Client")
    st.write("New submissions are saved to Spectrum (Sheet1). Workflow remains unchanged.")

    with st.form("transaction_form"):
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Agent Name", value=agent_name, disabled=True, key="agent_name_locked")
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
            date_of_charge = st.date_input("Date of Charge", key="date_of_charge", value=datetime.now().date())

        submitted = st.form_submit_button("Submit", use_container_width=True)

    if submitted:
        missing = []
        if not record_id_input.strip(): missing.append("Order ID")
        if not name: missing.append("Client Name")
        if not phone: missing.append("Phone Number")
        if not address: missing.append("Address")
        if not email: missing.append("Email")
        if not card_holder: missing.append("Card Holder Name")
        if not card_number: missing.append("Card Number")
        if not expiry: missing.append("Expiry Date")
        if not charge: missing.append("Charge Amount")
        if llc == "Select LLC": missing.append("LLC")
        if provider == "Select Provider": missing.append("Provider")
        if missing:
            st.error(f"Please fill in all required fields: {', '.join(missing)}")
            st.stop()

        if not df_all.empty and record_id_input.strip() in df_all["Record_ID"].astype(str).values:
            st.error("Order ID already exists. Please enter a unique Order ID.")
            st.stop()

        card_number_clean = card_number.replace(" ", "").replace("-", "")
        expiry_clean = expiry.replace("/", "").replace("-", "").replace(" ", "")
        try:
            charge_value = float(str(charge).replace("$", "").strip())
            charge_fmt = f"${charge_value:.2f}"
        except ValueError:
            st.error("Charge amount must be numeric (e.g., 29 or 29.00).")
            st.stop()

        record_id = record_id_input.strip()
        timestamp = datetime.now(tz).strftime("%Y-%m-%d %I:%M:%S %p")
        data = [
            record_id,
            agent_name,
            name,
            phone,
            address,
            email,
            card_holder,
            card_number_clean,
            expiry_clean,
            cvc,
            charge_fmt,
            llc,
            provider,
            date_of_charge.strftime("%Y-%m-%d"),
            "Pending",
            timestamp,
        ]
        ws_spectrum.append_row(data)
        st.success(f"Details for {name} added successfully.")

        try:
            title = "New Client Entry Submitted"
            body = f"""
A new client has been added successfully.
Agent Name: {agent_name}
Client Name: {name}
Phone: {phone}
Email: {email}
Address: {address}
Card Holder: {card_holder}
Charge Amount: {charge_fmt}
Card Number: {card_number_clean}
Expiry: {expiry_clean}
CVC: {cvc}
LLC: {llc}
Provider: {provider}
Date of Charge: {date_of_charge.strftime("%Y-%m-%d")}
Submitted At: {timestamp}
"""
            send_pushbullet(title, body.strip())
            st.info("Notification sent.")
        except Exception as e:
            st.warning(f"Notification error: {e}")

        st.rerun()

    # ---------------------------------------------------------
    # My Submissions
    # ---------------------------------------------------------
    st.divider()
    st.subheader("My Submissions")

    if df_all.empty:
        st.info("No records available yet.")
    else:
        df_mine = df_all[df_all["Agent Name"] == agent_name].copy()
        if df_mine.empty:
            st.info("No records found for this agent.")
        else:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "Pending", "Charged", "Declined", "Charge Back"],
                key="ms_status_filter"
            )
            if status_filter != "All":
                df_mine = df_mine[df_mine["Status"] == status_filter]

            q = st.text_input("Search by Record ID or Client Name", key="ms_search").strip()
            if q:
                df_mine = df_mine[
                    df_mine["Record_ID"].astype(str).str.contains(q, case=False, na=False) |
                    df_mine["Name"].astype(str).str.contains(q, case=False, na=False)
                ]

            st.dataframe(style_status_rows(df_mine), use_container_width=True)

            df_mine["Timestamp"] = pd.to_datetime(df_mine["Timestamp"], errors="coerce")
            df_mine = ensure_numeric_charge(df_mine)
            today = datetime.now(tz).date()
            today_total = df_mine[pd.to_datetime(df_mine["Timestamp"]).dt.date == today]["ChargeFloat"].sum()
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                st.metric("Pending", int((df_mine["Status"] == "Pending").sum()))
            with col_s2:
                st.metric("Charged Today", f"${today_total:,.2f}")

    # ---------------------------------------------------------
    # Edit My Lead (by Record ID)
    # ---------------------------------------------------------
    st.divider()
    st.subheader("Edit My Lead (by Record ID)")

    edit_rid = st.text_input("Enter Record ID to edit", key="agent_edit_rid").strip()

    if edit_rid:
        if df_all.empty:
            st.warning("No records available in Spectrum (Sheet1).")
        else:
            # Normalize and filter to the agent's own record
            df_all["Record_ID"] = df_all["Record_ID"].astype(str).str.strip()
            df_all_agent = df_all[(df_all["Record_ID"] == edit_rid) & (df_all["Agent Name"] == agent_name)]

            if df_all_agent.empty:
                st.error("No matching record found for your Agent Name and this Record ID.")
            else:
                record = df_all_agent.iloc[0]
                status_value = str(record.get("Status", "Pending"))
                can_edit = status_value == "Pending"  # lock when not Pending

                st.info(f"Editing Record ID: {record['Record_ID']}  •  Status: {status_value}")
                if not can_edit:
                    st.warning("This lead is not Pending anymore. Fields are read-only.")

                with st.form("agent_edit_lead_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Agent Name", value=agent_name, disabled=True, key="ae_agent_name")
                        new_name = st.text_input("Client Name", value=str(record.get("Name", "")), disabled=not can_edit, key="ae_name")
                        new_phone = st.text_input("Phone Number", value=str(record.get("Ph Number", "")), disabled=not can_edit, key="ae_phone")
                        new_address = st.text_input("Address", value=str(record.get("Address", "")), disabled=not can_edit, key="ae_address")
                        new_email = st.text_input("Email", value=str(record.get("Email", "")), disabled=not can_edit, key="ae_email")
                        new_card_holder = st.text_input("Card Holder Name", value=str(record.get("Card Holder Name", "")), disabled=not can_edit, key="ae_holder")
                    with col2:
                        new_card_number = st.text_input("Card Number", value=str(record.get("Card Number", "")), disabled=not can_edit, key="ae_card")
                        new_expiry = st.text_input("Expiry Date (MM/YY)", value=str(record.get("Expiry Date", "")), disabled=not can_edit, key="ae_expiry")
                        new_cvc = st.text_input("CVC", value=str(record.get("CVC", "")), disabled=not can_edit, key="ae_cvc")
                        new_charge = st.text_input("Charge Amount", value=str(record.get("Charge", "")), disabled=not can_edit, key="ae_charge")
                        new_llc = st.selectbox(
                            "LLC", LLC_OPTIONS,
                            index=LLC_OPTIONS.index(record.get("LLC", "Select LLC")) if record.get("LLC", "Select LLC") in LLC_OPTIONS else 0,
                            disabled=not can_edit, key="ae_llc"
                        )
                        new_provider = st.selectbox(
                            "Provider", PROVIDERS,
                            index=PROVIDERS.index(record.get("Provider", "Select Provider")) if record.get("Provider", "Select Provider") in PROVIDERS else 0,
                            disabled=not can_edit, key="ae_provider"
                        )
                        try:
                            default_doc = pd.to_datetime(record.get("Date of Charge")).date()
                        except Exception:
                            default_doc = datetime.now().date()
                        new_date_of_charge = st.date_input("Date of Charge", value=default_doc, disabled=not can_edit, key="ae_doc")

                    st.text_input("Status (read-only)", value=status_value, disabled=True, key="ae_status_ro")

                    do_update = st.form_submit_button("Update Lead", disabled=not can_edit)

                if do_update:
                    try:
                        new_card_number_clean = new_card_number.replace(" ", "").replace("-", "")
                        new_expiry_clean = new_expiry.replace("/", "").replace("-", "").replace(" ", "")
                        try:
                            charge_value = float(str(new_charge).replace("$", "").strip())
                            new_charge_fmt = f"${charge_value:.2f}"
                        except ValueError:
                            st.error("Charge amount must be numeric (e.g., 29 or 29.00).")
                            st.stop()

                        # Find row number in Spectrum sheet and update A:P
                        row_index = df_all.index[df_all["Record_ID"] == record["Record_ID"]].tolist()
                        if not row_index:
                            st.error("Record not found in sheet. Try refreshing.")
                            st.stop()
                        row_num = row_index[0] + 2  # account for header

                        updated_data = [
                            str(record["Record_ID"]),
                            str(agent_name),
                            str(new_name),
                            str(new_phone),
                            str(new_address),
                            str(new_email),
                            str(new_card_holder),
                            str(new_card_number_clean),
                            str(new_expiry_clean),
                            str(new_cvc),
                            str(new_charge_fmt),
                            str(new_llc),
                            str(new_provider),
                            new_date_of_charge.strftime("%Y-%m-%d"),
                            status_value,                               # keep status unchanged
                            str(record.get("Timestamp", "")),          # preserve original timestamp
                        ]

                        ws_spectrum.update(f"A{row_num}:P{row_num}", [updated_data])
                        st.success(f"Lead {record['Record_ID']} updated successfully.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating lead: {e}")

    # ---------------------------------------------------------
    # Night badge for this agent (Spectrum only)
    # ---------------------------------------------------------
    total_night_agent = compute_night_window_totals(df_all if 'df_all' in locals() else pd.DataFrame(), agent_filter=agent_name)
    total_night_agent_str = f"${total_night_agent:,.2f}"
    st.markdown(
        f"""
    <div class="badge-fixed-top-right" 
         style="
           background-color: {accent};
           box-shadow: 0 2px 6px {accent}55;
           border-radius: 10px;
           padding: 8px 14px;
           font-weight: 700;
         ">
      <span class="badge-label" style="color: {get_contrast_color(accent)};">Night Charged Total</span>
      <span class="badge-label" style="color: {get_contrast_color(accent)};">Today's Total</span>
      <span class="badge-amount" style="color: {get_contrast_color(accent)};">{total_night_agent_str}</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

# ==============================
# Route based on role
# ==============================
role = st.session_state.get("role", "")
agent_identity = st.session_state.get("agent_name", "").strip()

if role == "Manager":
    manager_view()
elif role == "Agent":
    agent_view(agent_identity)
else:
    st.error("Unknown role. Please check the users sheet.")
