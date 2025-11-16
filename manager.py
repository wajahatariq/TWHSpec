import streamlit as st
import gspread
import pandas as pd
from datetime import datetime, timedelta
import pytz
import requests
import time
import random
from datetime import datetime, timedelta, time
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
    
        if record_id_input:
            df_all["Record_ID"] = df_all["Record_ID"].astype(str).str.strip()
            record_id_input = record_id_input.strip()
            matched = df_all[df_all["Record_ID"] == record_id_input]
    
            if not matched.empty:
                st.info(f"Found {len(matched)} record(s) with Record ID: {record_id_input}")
    
                # Let user select one record if multiple found
                if len(matched) > 1:
                    options = matched.index.tolist()  # indexes of matched rows
                    selected_idx = st.selectbox("Select record to edit", options)
                    record = matched.loc[selected_idx]
                else:
                    record = matched.iloc[0]
    
                st.dataframe(matched)  # Optional: show all matched records
    
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
                    deleted = st.form_submit_button("Delete Record", help="Permanently delete this record")
    
                    if deleted:
                        try:
                            # Find the exact row index for this specific record to delete
                            row_indices = df_all.index[
                                (df_all["Record_ID"] == record["Record_ID"]) &
                                (df_all.index == record.name)
                            ].tolist()
    
                            if row_indices:
                                row_num = row_indices[0] + 2  # account for header row
                                worksheet.delete_rows(row_num)
                                st.success(f"Record {record['Record_ID']} deleted successfully!")
                                st.rerun()
                            else:
                                st.error("Record not found in sheet. Try refreshing the page.")
                        except Exception as e:
                            st.error(f"Error deleting record: {e}")
    
                    if updated:
                        try:
                            # Find the exact row index for this specific record to update
                            row_indices = df_all.index[
                                (df_all["Record_ID"] == record["Record_ID"]) &
                                (df_all.index == record.name)
                            ].tolist()
    
                            if row_indices:
                                row_num = row_indices[0] + 2  # header is row 1
    
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
                                        str(record["Timestamp"])
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
                                        str(record["Timestamp"])
                                    ]
                                    worksheet.update(f"A{row_num}:O{row_num}", [updated_data])
    
                                st.success(f"Record {record['Record_ID']} updated successfully!")
                                st.rerun()
                            else:
                                st.error("Record not found in sheet. Try refreshing the page.")
                        except Exception as e:
                            st.error(f"Error updating record: {e}")
    
            else:
                st.warning("No matching Record ID found.")
    else:
        st.info("No data available to edit.")


    st.divider()

    # --- Existing Data Display ---
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
    
    # JS code for conditional row styling based on Status column
    row_style_jscode = JsCode("""
    function(params) {
        if (!params.data) return null;
        const status = params.data.Status;
        if (status === 'Charged') {
            return {'background-color': 'darkgreen', 'color': 'white'};
        } else if (status === 'Charge Back') {
            return {'background-color': 'red', 'color': 'white'};
        } else if (status === 'Pending') {
            return {'background-color': 'yellow', 'color': 'black'};
        } else {
            return null;
        }
    }
    """)
    
    def display_aggrid_with_search(df, label):
        st.subheader(f"{label} Data")
    
        if df.empty:
            st.info(f"No data available in {label}.")
            return
    
        search_text = st.text_input(f"Search {label} Table")
    
        gb = GridOptionsBuilder.from_dataframe(df)
    
        # Configure grid options
        gb.configure_default_column(
            editable=True,
            filter=True,
            sortable=True,
            resizable=True,
            flex=1,
            min_width=100,
        )
    
        # Multi-row selection with checkboxes
        gb.configure_selection('multiple', use_checkbox=True)
    
        # Add JS for row styling based on Status
        gb.configure_grid_options(getRowStyle=row_style_jscode)
    
        # Set quick filter text from search input
        gb.configure_grid_options(quickFilterText=search_text)
    
        # Disable pagination for vertical scrolling
        gb.configure_pagination(enabled=False)
    
        grid_options = gb.build()
    
        grid_response = AgGrid(
            df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            theme="alpine-dark",   # Use built-in dark theme
            fit_columns_on_grid_load=True,
            allow_unsafe_jscode=True,
            height=600,  # Adjust for scrolling
        )
    
        return grid_response
    
    # Example usage
    # Replace df_spectrum and df_insurance with your actual dataframes
    display_aggrid_with_search(df_spectrum, "Spectrum (Sheet1)")
    st.divider()
    display_aggrid_with_search(df_insurance, "Insurance (Sheet2)")


    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import seaborn as sns
    
    st.divider()
    st.subheader("Transaction Analysis Chart")
    
    tz = pytz.timezone("Asia/Karachi")
    
    if not df_all.empty:
        # --- Preprocess timestamps and charges ---
        df_all["Timestamp"] = pd.to_datetime(df_all["Timestamp"], errors="coerce")
        df_all["ChargeFloat"] = pd.to_numeric(
            df_all["Charge"].replace('[\$,]', '', regex=True), errors='coerce'
        )
    
        # --- Filters ---
        col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
        with col_f1:
            AGENTS = ["All Agents"] + sorted(df_all["Agent Name"].dropna().unique().tolist())
            agent_filter = st.selectbox("Filter by Agent", AGENTS)
        with col_f2:
            STATUS = ["All Status"] + df_all["Status"].dropna().unique().tolist()
            status_filter = st.selectbox("Filter by Status", STATUS)
        with col_f3:
            chart_type = st.selectbox("Chart Type", ["Bar", "Line", "Stacked Bar"])
    
        # --- Timestamp range selection (compatible way) ---
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            start_date = st.date_input("From Date", value=df_all["Timestamp"].min().date())
            start_time = st.time_input("From Time", value=time(0, 0, 0))
        with col_d2:
            end_date = st.date_input("To Date", value=df_all["Timestamp"].max().date())
            end_time = st.time_input("To Time", value=time(23, 59, 59))
    
        # Combine date and time
        start_datetime = tz.localize(datetime.combine(start_date, start_time))
        end_datetime = tz.localize(datetime.combine(end_date, end_time))
    
        # --- Apply filters ---
        df_chart = df_all.copy()
        if agent_filter != "All Agents":
            df_chart = df_chart[df_chart["Agent Name"] == agent_filter]
        if status_filter != "All Status":
            df_chart = df_chart[df_chart["Status"] == status_filter]
    
        # Localize timestamps for comparison
        df_chart["Timestamp"] = df_chart["Timestamp"].dt.tz_localize("UTC").dt.tz_convert(tz)
        df_chart = df_chart[
            (df_chart["Timestamp"] >= start_datetime) &
            (df_chart["Timestamp"] <= end_datetime)
        ]
    
        # --- Check if data is available ---
        if df_chart.empty:
            st.info("No data available for selected filters and timestamp range.")
        else:
            # --- Aggregate data ---
            df_chart["Hour"] = df_chart["Timestamp"].dt.floor("h")
            hourly_sum = df_chart.groupby("Hour")["ChargeFloat"].sum().reset_index()
    
            # --- Chart setup ---
            sns.set_palette("tab20")
            fig, ax = plt.subplots(figsize=(12, 6))
    
            if chart_type == "Bar":
                ax.bar(hourly_sum["Hour"], hourly_sum["ChargeFloat"],
                       color=sns.color_palette("tab20", len(hourly_sum)))
            elif chart_type == "Line":
                ax.plot(hourly_sum["Hour"], hourly_sum["ChargeFloat"],
                        marker='o', linestyle='-', color='tab:blue')
            elif chart_type == "Stacked Bar":
                df_stack = df_chart.pivot_table(
                    index="Hour", columns="Status", values="ChargeFloat",
                    aggfunc="sum", fill_value=0
                )
                df_stack.plot(kind="bar", stacked=True, ax=ax, colormap="tab20")
    
            # --- Axis formatting ---
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M:%S"))
            plt.xticks(rotation=45)
            ax.set_xlabel("Timestamp")
            ax.set_ylabel("Total Charge ($)")
            ax.set_title(
                f"Total Charges from {start_datetime.strftime('%Y-%m-%d %H:%M:%S')} "
                f"to {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}",
                fontsize=16, fontweight='bold'
            )
            ax.grid(alpha=0.3)
            st.pyplot(fig)
    
            # --- Ultra Analytics ---
            st.markdown("### Ultra Analytics Options")
            col_u1, col_u2, col_u3, col_u4 = st.columns(4)
            with col_u1:
                st.metric("Total Charge", f"${df_chart['ChargeFloat'].sum():,.2f}")
            with col_u2:
                st.metric("Total Transactions", f"{len(df_chart):,}")
            with col_u3:
                st.metric("Average Charge per Hour", f"${hourly_sum['ChargeFloat'].mean():,.2f}")
            with col_u4:
                peak_time = hourly_sum.loc[hourly_sum['ChargeFloat'].idxmax(), 'Hour']
                st.metric("Peak Charge Timestamp", peak_time.strftime('%Y-%m-%d %H:%M:%S'))
    
            # --- Insights ---
            st.markdown("#### Top Agents by Total Charge")
            top_agents = df_chart.groupby("Agent Name")["ChargeFloat"].sum().sort_values(ascending=False).head(5)
            st.bar_chart(top_agents)
    
            st.markdown("#### Status Distribution")
            status_counts = df_chart["Status"].value_counts()
            st.bar_chart(status_counts)
    
    else:
        st.info("No transaction data available to generate chart.")

    st.divider()
    st.subheader("Find Duplicate Records by Order ID")

    # Choose which sheet to check duplicates in
    dup_sheet_option = st.selectbox("Select Sheet to check duplicates", ["Spectrum (Sheet1)", "Insurance (Sheet2)"])

    df_to_check = df_spectrum if dup_sheet_option.startswith("Spectrum") else df_insurance

    if df_to_check.empty:
        st.info(f"No data available in {dup_sheet_option} to check duplicates.")
    else:
        # Find duplicates by Record_ID
        duplicates = df_to_check[df_to_check.duplicated(subset=["Record_ID"], keep=False)]

        if duplicates.empty:
            st.success("No duplicate Order IDs found.")
        else:
            st.warning(f"Found {duplicates['Record_ID'].nunique()} duplicate Record ID(s).")
            # Optionally, show how many times each duplicate occurs
            dup_counts = duplicates.groupby("Record_ID").size().reset_index(name="Count").sort_values(by="Count", ascending=False)
            st.dataframe(dup_counts, use_container_width=True)

            # Show full duplicated records optionally
            with st.expander("Show duplicate records details"):
                st.dataframe(duplicates.sort_values(by="Record_ID"), use_container_width=True)

# --- NIGHT WINDOW CHARGED TRANSACTIONS & DISPLAY ---
from datetime import datetime, time, timedelta
import pytz

tz = pytz.timezone("Asia/Karachi")
now = datetime.now(tz).replace(tzinfo=None)  # naive for comparison with naive timestamps

if time(7, 0) <= now.time() < time(19, 0):
    # Daytime: last night 7 PM → today 6 AM
    window_start_1 = datetime.combine(now.date() - timedelta(days=1), time(19, 0))
    window_end_1 = datetime.combine(now.date() - timedelta(days=1), time(23, 59, 59, 999999))
    window_start_2 = datetime.combine(now.date(), time(0, 0))
    window_end_2 = datetime.combine(now.date(), time(6, 0))
else:
    # Nighttime: today 7 PM → tomorrow 6 AM
    if now.time() >= time(19, 0):
        window_start_1 = datetime.combine(now.date(), time(19, 0))
        window_end_1 = datetime.combine(now.date(), time(23, 59, 59, 999999))
        window_start_2 = datetime.combine(now.date() + timedelta(days=1), time(0, 0))
        window_end_2 = datetime.combine(now.date() + timedelta(days=1), time(6, 0))
    else:  # between midnight and 6 AM
        window_start_1 = datetime.combine(now.date() - timedelta(days=1), time(19, 0))
        window_end_1 = datetime.combine(now.date() - timedelta(days=1), time(23, 59, 59, 999999))
        window_start_2 = datetime.combine(now.date(), time(0, 0))
        window_end_2 = datetime.combine(now.date(), time(6, 0))

# Now filter your dataframe:
def in_night_window(ts):
    return ((ts >= window_start_1) and (ts <= window_end_1)) or ((ts >= window_start_2) and (ts <= window_end_2))

df_all['Timestamp'] = pd.to_datetime(df_all['Timestamp'], errors='coerce')
night_charged_df = df_all[
    (df_all['Status'] == "Charged") & 
    (df_all['Timestamp'].apply(in_night_window))
]

total_night_charge = night_charged_df['ChargeFloat'].sum()
total_night_charge_str = f"${total_night_charge:,.2f}"
amount_text_color = get_contrast_color(accent)

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
    <!-- Sub-label for clarity -->
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
