import streamlit as st
import gspread
import pandas as pd
from datetime import datetime, timedelta
import pytz
import requests
import time

# --- CONFIG ---
st.set_page_config(page_title="Manager Dashboard", layout="wide")
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
    "Obsidian Night":  {"bg1": "#0b0c10", "bg2": "#1f2833", "accent": "#66fcf1"},
    "Crimson Shadow":  {"bg1": "#1c0b0b", "bg2": "#2a0f0f", "accent": "#ff4444"},
    "Deep Ocean":      {"bg1": "#0a1b2a", "bg2": "#0d2c4a", "accent": "#1f8ef1"},
    "Neon Violet":     {"bg1": "#12001e", "bg2": "#1e0033", "accent": "#bb00ff"},
    "Emerald Abyss":   {"bg1": "#001a14", "bg2": "#00322b", "accent": "#00ff99"},
    "Midnight Gold":   {"bg1": "#0d0d0d", "bg2": "#1a1a1a", "accent": "#ffd700"},
    "Cyber Pink":      {"bg1": "#0a0014", "bg2": "#1a0033", "accent": "#ff00aa"},
    "Steel Indigo":    {"bg1": "#0c0f1a", "bg2": "#1c2333", "accent": "#7dd3fc"},
    "Velvet Crimson":  {"bg1": "#1a0000", "bg2": "#330000", "accent": "#e11d48"},
    "Arctic Noir":     {"bg1": "#050b12", "bg2": "#0e1822", "accent": "#38bdf8"},
}

# ------------------ SESSION STATE ------------------
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Dark"

if "selected_theme" not in st.session_state:
    default_themes = dark_themes if st.session_state.theme_mode == "Dark" else light_themes
    st.session_state.selected_theme = list(default_themes.keys())[0]

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
    if cols[i].button(theme_name, key=f"theme_{theme_name}"):
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

# ------------------ HEADER ------------------
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

main_tab1, main_tab2, main_tab3 = st.tabs(["Spectrum", "Insurance", "Updated Data"])

with main_tab1:
    render_transaction_tabs(df_spectrum, spectrum_ws, "spectrum")

with main_tab2:
    render_transaction_tabs(df_insurance, insurance_ws, "insurance")

with main_tab3:
    st.subheader("Spectrum Data (Sheet1)")
    if df_spectrum.empty:
        st.info("No data available in Spectrum (Sheet1).")
    else:
        st.dataframe(df_spectrum, use_container_width=True)

    st.divider()

    st.subheader("Insurance Data (Sheet2)")
    if df_insurance.empty:
        st.info("No data available in Insurance (Sheet2).")
    else:
        st.dataframe(df_insurance, use_container_width=True)

try:
    from litellm import completion
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
    from tabulate import tabulate
    import io
    import base64
except Exception as e:
    st.error(f"Missing AI/pdf deps: {e}. Install litellm, reportlab, tabulate.")
    raise

st.markdown("---")
st.markdown("### 🤖 AI Insights (Groq via LiteLLM)")

def clean_currency_columns(df):
    """Remove $ and commas from any object columns that look like money, convert to numeric when possible."""
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == "object":
            # Check if column has $ or commas in many rows
            sample = df[col].dropna().astype(str).head(50).to_list()
            looks_like_money = any('$' in s or ',' in s for s in sample)
            if looks_like_money:
                # remove $ and commas
                df[col] = df[col].astype(str).str.replace(r'[\$,]', '', regex=True).str.strip()
                # try convert to numeric; if all convertable make numeric, else keep as object
                df[col] = pd.to_numeric(df[col], errors='ignore')
    return df

def df_head_markdown(df, rows=20):
    return df.head(rows).to_markdown(index=False)

def create_pdf_from_df(df, filename):
    """Create a simple PDF table (ReportLab). Returns bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    # prepare data
    data = [list(df.columns)]
    # Limit rows to 60 for PDF
    for i, row in df.head(60).iterrows():
        data.append([str(x) for x in row.tolist()])
    table = Table(data, repeatRows=1)
    style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f0f0f0")),
        ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 8),
    ])
    table.setStyle(style)
    doc.build([table])
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

# Prepare dataframes (use your app df variables)
df1 = df_spectrum.copy() if 'df_spectrum' in globals() else load_data(spectrum_ws)
df2 = df_insurance.copy() if 'df_insurance' in globals() else load_data(insurance_ws)

# Clean them
df1_clean = clean_currency_columns(df1)
df2_clean = clean_currency_columns(df2)

st.markdown("**Preview — cleaned heads**")
col1, col2 = st.columns(2)
with col1:
    st.markdown("**Sheet1 (Spectrum) — head**")
    st.dataframe(df1_clean.head(10), use_container_width=True)
with col2:
    st.markdown("**Sheet2 (Insurance) — head**")
    st.dataframe(df2_clean.head(10), use_container_width=True)

# Create small diagnostic summary BEFORE sending to AI (so AI has the numbers too)
def numeric_summary(df):
    nums = df.select_dtypes(include=['number'])
    if nums.shape[1] == 0:
        return "No numeric columns detected."
    out = []
    for c in nums.columns:
        out.append(f"{c}: count={nums[c].count()}, sum={nums[c].sum():,.2f}, mean={nums[c].mean():.2f}, min={nums[c].min()}, max={nums[c].max()}")
    return "\n".join(out)

summary_text = (
    "Sheet1 summary:\n" + numeric_summary(df1_clean) +
    "\n\nSheet2 summary:\n" + numeric_summary(df2_clean)
)

# Optional: create PDFs and provide download links (for manual review / archival)
if st.button("Make PDFs for both sheets (for archival)"):
    try:
        pdf1 = create_pdf_from_df(df1_clean, "sheet1.pdf")
        pdf2 = create_pdf_from_df(df2_clean, "sheet2.pdf")
        b1 = base64.b64encode(pdf1).decode()
        b2 = base64.b64encode(pdf2).decode()
        href1 = f'<a href="data:application/pdf;base64,{b1}" download="sheet1.pdf">Download Sheet1 PDF</a>'
        href2 = f'<a href="data:application/pdf;base64,{b2}" download="sheet2.pdf">Download Sheet2 PDF</a>'
        st.markdown(href1, unsafe_allow_html=True)
        st.markdown(href2, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"PDF creation failed: {e}")

# Prepare AI input (keep it small — use heads and numeric summary)
ai_input = f"""
You are a helpful financial analyst.

Provide:
- A clean numeric summary.
- Totals and averages for numeric columns.
- Top 3 largest numeric values (by column).
- Any obvious anomalies.

Sheet1 (Spectrum) head:
{df_head_markdown(df1_clean, rows=12)}

Sheet2 (Insurance) head:
{df_head_markdown(df2_clean, rows=12)}

Numeric summaries:
{summary_text}

Only return a concise structured answer (bullet points / short paragraphs).
"""

if st.button("Analyze with AI"):
    with st.spinner("Analyzing data with AI..."):
        ai_response = completion(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": ai_input}],
            api_key=st.secrets["GROQ_API_KEY"],
        )
    
    st.success("Analysis Complete")
    
    st.subheader("AI summary / insights")
    
    try:
        ai_summary = ai_response.choices[0].message.content
        st.markdown(f"### AI Summary\n\n{ai_summary}")
    except Exception as e:
        st.error(f"AI analysis failed to display: {e}")
