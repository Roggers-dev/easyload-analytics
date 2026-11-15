import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import hashlib
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression

# ==========================================
# 1. PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="EasyLoad All Data Analyzer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Global Theme Styling */
    .stApp { background-color: #0f172a; color: #f8fafc; }
    
    /* Hide Streamlit Community Cloud Deploy Button, Toolbar, Footer & Manage App Badge */
    [data-testid="stToolbar"] { visibility: hidden !important; display: none !important; }
    #MainMenu { visibility: hidden !important; display: none !important; }
    .viewerBadge_container__1QSob { display: none !important; }
    .stDeployButton { visibility: hidden !important; display: none !important; }
    header { visibility: hidden !important; display: none !important; }
    footer { visibility: hidden !important; display: none !important; }

    /* Custom Cards & Alerts */
    .anomaly-alert {
        background-color: #7f1d1d;
        border-left: 5px solid #ef4444;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
        color: #fef2f2;
    }
    .winner-box {
        background-color: #064e3b;
        border-left: 5px solid #22c55e;
        padding: 15px;
        border-radius: 8px;
        color: #ecfdf5;
    }
    .loser-box {
        background-color: #78350f;
        border-left: 5px solid #f59e0b;
        padding: 15px;
        border-radius: 8px;
        color: #fffbeb;
    }
    .decision-box {
        background-color: #1e293b;
        border: 1px solid #334155;
        padding: 20px;
        border-radius: 10px;
        margin-top: 20px;
        color: #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SECURE DATABASE & AUTO-MIGRATION
# ==========================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect('voices_enterprise.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,
            status TEXT,
            requested_at TEXT
        )
    ''')
    
    # Auto-migration for legacy databases
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN requested_at TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass 
        
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            comment TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    
    # Seed default Master Admin if empty
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        secure_pass = hash_password("Admin2026!")
        cursor.execute("INSERT INTO users (username, password, role, status, requested_at) VALUES (?, ?, ?, ?, ?)",
                       ("admin", secure_pass, "admin", "approved", datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
    conn.close()

init_db()

def run_query(query, params=()):
    conn = sqlite3.connect('voices_enterprise.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = cursor.fetchall()
    conn.close()
    return result

def execute_query(query, params=()):
    conn = sqlite3.connect('voices_enterprise.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()

# ==========================================
# 3. AUTHENTICATION SESSION STATE
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "role" not in st.session_state:
    st.session_state["role"] = ""

# ==========================================
# 4. AUTHENTICATION GATEWAY
# ==========================================
if not st.session_state["authenticated"]:
    st.markdown("<h2 style='text-align: center; color: #38bdf8;'>⚡ EasyLoad All Data Analyzer</h2>", unsafe_allow_html=True)
    st.markdown("""
        <p style='text-align: center; color: #94a3b8; max-width: 600px; margin: 0 auto 15px auto;'>
            A secure, professional enterprise intelligence platform designed for deep regression analysis, 
            trend forecasting, anomaly detection, and evidence-based decision-making.
        </p>
    """, unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748b; font-size: 13px;'>Strict authentication required. Unauthorized access is blocked.</p>", unsafe_allow_html=True)
    
    tab_login, tab_request = st.tabs(["🔑 Secure Sign In", "📝 Request Platform Access"])
    
    with tab_login:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form"):
                u_input = st.text_input("Username")
                p_input = st.text_input("Password", type="password")
                submit_btn = st.form_submit_button("Authenticate & Enter", use_container_width=True)
                
                if submit_btn:
                    hashed_p = hash_password(p_input)
                    user_record = run_query("SELECT role, status FROM users WHERE username = ? AND password = ?", (u_input, hashed_p))
                    if user_record:
                        role, status = user_record[0]
                        if status == "approved":
                            st.session_state["authenticated"] = True
                            st.session_state["username"] = u_input
                            st.session_state["role"] = role
                            st.success("Access Granted! Loading system...")
                            st.rerun()
                        else:
                            st.error("⚠️ Your account access request is pending administrator approval.")
                    else:
                        st.error("❌ Invalid username or password.")
                        
    with tab_request:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("request_form"):
                new_user = st.text_input("Desired Username")
                new_pass = st.text_input("Desired Password", type="password")
                req_btn = st.form_submit_button("Submit Access Request", use_container_width=True)
                
                if req_btn:
                    if new_user and new_pass:
                        try:
                            hashed_np = hash_password(new_pass)
                            execute_query("INSERT INTO users (username, password, role, status, requested_at) VALUES (?, ?, ?, ?, ?)",
                                          (new_user, hashed_np, "user", "pending", datetime.now().strftime("%Y-%m-%d %H:%M")))
                            st.success("✅ Request submitted! An administrator will review your credentials.")
                        except sqlite3.IntegrityError:
                            st.error("⚠️ Username already exists. Choose a different username.")
                    else:
                        st.warning("⚠️ Please fill in both fields.")
                        
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #64748b; font-size: 12px;'>Secured & Engineered by <b>Rogers</b> | Contact: 0542470810</p>", unsafe_allow_html=True)
    st.stop()

# ==========================================
# 5. SIDEBAR & NAVIGATION SETUP
# ==========================================
st.sidebar.markdown(f"### 👤 Logged in as: `{st.session_state['username']}`")
st.sidebar.markdown(f"**Role:** `{st.session_state['role'].upper()}`")
if st.sidebar.button("🔒 Secure Sign Out", use_container_width=True):
    st.session_state["authenticated"] = False
    st.session_state["username"] = ""
    st.session_state["role"] = ""
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🗂️ Data & Traffic Manager")
uploaded_file = st.sidebar.file_uploader("Upload CSV or Excel File", type=["csv", "xlsx"])

# Optimized Demo Data Generator
st.sidebar.markdown("### ⚡ Optimized Demo Data:")
col_d1, col_d2 = st.sidebar.columns(2)
demo_mode = None
with col_d1:
    if st.button("🛍️ Store Demo", use_container_width=True):
        demo_mode = "store"
with col_d2:
    if st.button("🏥 Health Demo", use_container_width=True):
        demo_mode = "health"

st.sidebar.markdown("---")

# Dynamic Sidebar Navigation (Strictly hiding Manager panel from non-admins)
nav_options = [
    "📈 Regression, Trends & Performers", 
    "📊 Global & Selected Metrics",
    "🔀 Pivot Summaries & Counts",
    "📱 Live Mobile Simulator", 
    "💬 Team Discussions"
]

if st.session_state["role"] == "admin":
    nav_options.append("⚙️ Manager Access Control")

nav_choice = st.sidebar.radio("Navigation Menu", nav_options)

# ==========================================
# 6. DATA LOADER ENGINE
# ==========================================
if demo_mode == "store":
    np.random.seed(42)
    n = 200
    st.session_state['df'] = pd.DataFrame({
        "Store_ID": [f"Store-{i:03d}" for i in range(1, n+1)],
        "Region": np.random.choice(["North", "South", "East", "West"], n),
        "Ad_Spend": np.random.randint(1000, 15000, n),
        "Sales_Revenue": np.random.randint(5000, 75000, n),
        "Customer_Rating": np.round(np.random.uniform(3.0, 5.0, n), 1)
    })
elif demo_mode == "health":
    np.random.seed(100)
    n = 200
    st.session_state['df'] = pd.DataFrame({
        "Patient_ID": [f"PT-{i:04d}" for i in range(1, n+1)],
        "Department": np.random.choice(["Cardiology", "Neurology", "Pediatrics", "Oncology"], n),
        "Treatment_Hours": np.random.randint(5, 50, n),
        "Recovery_Score": np.random.randint(40, 100, n),
        "Satisfaction": np.round(np.random.uniform(2.5, 5.0, n), 1)
    })

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            st.session_state['df'] = pd.read_csv(uploaded_file)
        else:
            st.session_state['df'] = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error reading file: {e}")

if 'df' not in st.session_state:
    # Default initial fallback demo data
    np.random.seed(42)
    n = 100
    st.session_state['df'] = pd.DataFrame({
        "Entity_ID": [f"ID-{i:03d}" for i in range(1, n+1)],
        "Category": np.random.choice(["Type A", "Type B", "Type C"], n),
        "Driver_Variable": np.random.randint(10, 100, n),
        "Outcome_Variable": np.random.randint(50, 500, n),
        "Quality_Score": np.round(np.random.uniform(1.0, 5.0, n), 1)
    })

df = st.session_state['df']
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
all_cols = df.columns.tolist()

# ==========================================
# 7. MODULE ROUTING & EXECUTION
# ==========================================
if nav_choice == "📈 Regression, Trends & Performers":
    st.markdown("## 📈 OLS Regression, Trend Forecasting & Performance Judgment")
    st.markdown("Analyze driver relationships, detect statistical anomalies, and identify top performers.")
    
    if len(numeric_cols) >= 2:
        sel1, sel2, sel3 = st.columns(3)
        with sel1:
            col_x = st.selectbox("1️⃣ Driver Variable (X-Axis):", numeric_cols, index=0)
        with sel2:
            col_y = st.selectbox("2️⃣ Outcome Variable (Y-Axis):", numeric_cols, index=min(1, len(numeric_cols)-1))
        with sel3:
            label_col = st.selectbox("3️⃣ Name / ID Column:", all_cols, index=0)

        # Prevent crash if user picks the exact same column for X and Y
        if col_x == col_y:
            st.warning("⚠️ Please select **two different columns** for the Driver (X-axis) and Outcome (Y-axis) to run regression modeling.")
        else:
            work_df = df[[label_col, col_x, col_y]].dropna().copy()
            
            if len(work_df) > 5:
                X = work_df[[col_x]].values
                y = work_df[col_y].values

                model = LinearRegression().fit(X, y)
                work_df["Expected_Trend"] = model.predict(X)
                work_df["Performance_Gap"] = work_df[col_y] - work_df["Expected_Trend"]
                
                std_resid = work_df["Performance_Gap"].std()
                if np.isnan(std_resid) or std_resid == 0:
                    std_resid = 1.0

                work_df["Status"] = np.where(
                    np.abs(work_df["Performance_Gap"]) > (2.0 * std_resid),
                    "🚨 Anomaly (Outlier)",
                    np.where(work_df["Performance_Gap"] >= 0, "✅ Doing Well (Above Trend)", "⚠️ Doing Bad (Below Trend)")
                )

                anomalies = work_df[work_df["Status"] == "🚨 Anomaly (Outlier)"]
                if not anomalies.empty:
                    st.markdown(f"""
                        <div class='anomaly-alert'>
                            🚨 <b>ANOMALY NOTIFICATION: {len(anomalies)} Unusual Record(s) Detected!</b><br>
                            These records break away sharply from the normal trend. Review them below to maintain high decision quality.
                        </div>
                    """, unsafe_allow_html=True)
                    with st.expander("🔍 Inspect Flagged Anomaly Records"):
                        st.dataframe(anomalies[[label_col, col_x, col_y, "Expected_Trend", "Performance_Gap"]], use_container_width=True)

                st.markdown(f"### 🎯 Scatter Diagram & Regression Trendline: `{col_y}` vs `{col_x}`")
                
                fig_scatter = px.scatter(
                    work_df, x=col_x, y=col_y, color="Status",
                    hover_name=label_col,
                    color_discrete_map={
                        "✅ Doing Well (Above Trend)": "#22c55e",
                        "⚠️ Doing Bad (Below Trend)": "#f59e0b",
                        "🚨 Anomaly (Outlier)": "#ef4444"
                    },
                    title=f"Performance Scatter Map ({col_x} vs {col_y})"
                )
                x_range = np.linspace(work_df[col_x].min(), work_df[col_x].max(), 100)
                y_range = model.predict(x_range.reshape(-1, 1))
                fig_scatter.add_trace(go.Scatter(x=x_range, y=y_range, mode='lines', name='OLS Trendline (Expected)', line=dict(color='#38bdf8', width=3, dash='dash')))
                
                fig_scatter.update_layout(paper_bgcolor='#1e293b', plot_bgcolor='#1e293b', font_color='#f8fafc')
                st.plotly_chart(fig_scatter, use_container_width=True)

                st.markdown("### 🏆 Performance Judgment: Who's Doing Well vs. Who's Doing Bad")
                w_col, l_col = st.columns(2)
                
                top_performers = work_df.sort_values(by="Performance_Gap", ascending=False).head(3)
                bottom_performers = work_df.sort_values(by="Performance_Gap", ascending=True).head(3)

                with w_col:
                    top_list = "<br>".join([f"• <b>{row[label_col]}</b>: Actual <b>{row[col_y]:,.1f}</b> vs Expected {row['Expected_Trend']:,.1f} (<b>+{row['Performance_Gap']:,.1f}</b> ahead)" for _, row in top_performers.iterrows()])
                    st.markdown(f"""
                        <div class='winner-box'>
                            <b>🌟 WHO'S DOING WELL (Top Performers):</b><br>
                            {top_list}<br><br>
                            <i>Real-Life Judgment:</i> Replicate their strategy across other units!
                        </div>
                    """, unsafe_allow_html=True)

                with l_col:
                    bot_list = "<br>".join([f"• <b>{row[label_col]}</b>: Actual <b>{row[col_y]:,.1f}</b> vs Expected {row['Expected_Trend']:,.1f} (<b>{row['Performance_Gap']:,.1f}</b> behind)" for _, row in bottom_performers.iterrows()])
                    st.markdown(f"""
                        <div class='loser-box'>
                            <b>⚠️ WHO'S DOING BAD (Underperformers):</b><br>
                            {bot_list}<br><br>
                            <i>Real-Life Judgment:</i> Audit these entities immediately for operational friction or risk.
                        </div>
                    """, unsafe_allow_html=True)
                    r_sq = model.score(X, y)
                slope = model.coef_[0]
                direction = "increases" if slope > 0 else "decreases"
                
                st.markdown(f"""
                    <div class='decision-box'>
                        <b>🧠 Trend Education & Right Judgment Guide:</b><br>
                        • <b>What the Trend Shows:</b> Every 1-unit increase in <b>{col_x}</b> {direction} <b>{col_y}</b> by <b>{abs(slope):,.2f}</b>.<br>
                        • <b>Trustworthiness ($R^2$ Accuracy):</b> <b>{r_sq*100:.1f}%</b>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("Not enough valid data points to run regression.")
    else:
        st.warning("⚠️ Please upload a dataset with at least **two numeric columns** to run regression models.")

elif nav_choice == "📊 Global & Selected Metrics":
    st.markdown("## 📊 Global & Selected Metrics Overview")
    st.dataframe(df, use_container_width=True)

elif nav_choice == "🔀 Pivot Summaries & Counts":
    st.markdown("## 🔀 Pivot Summaries & Aggregations")
    if len(numeric_cols) > 0 and len(all_cols) > 1:
        cat_col = st.selectbox("Select Category Column:", [c for c in all_cols if c not in numeric_cols] or all_cols)
        num_col = st.selectbox("Select Metric to Aggregate:", numeric_cols)
        summary_df = df.groupby(cat_col)[num_col].agg(['count', 'mean', 'sum']).reset_index()
        st.dataframe(summary_df, use_container_width=True)
    else:
        st.warning("Insufficient categorical or numeric columns for aggregation.")

elif nav_choice == "📱 Live Mobile Simulator":
    st.markdown("## 📱 Live Mobile Responsive View")
    st.info("Simulating mobile layout scaling for enterprise field agents.")
    st.metric("Total Records Loaded", len(df))
    st.metric("Active Data Columns", len(df.columns))

elif nav_choice == "💬 Team Discussions":
    st.markdown("## 💬 Enterprise Team Discussions & Notes")
    
    with st.form("comment_form"):
        new_comment = st.text_area("Add an insight or management note:")
        post_btn = st.form_submit_button("Post Discussion")
        if post_btn and new_comment:
            execute_query("INSERT INTO comments (username, comment, timestamp) VALUES (?, ?, ?)",
                          (st.session_state["username"], new_comment, datetime.now().strftime("%Y-%m-%d %H:%M")))
            st.success("Note posted successfully!")
            st.rerun()
            
    st.markdown("### Recent Notes:")
    comments = run_query("SELECT username, comment, timestamp FROM comments ORDER BY id DESC")
    for usr, comm, ts in comments:
        st.markdown(f"> **{usr}** *({ts})*:<br>{comm}", unsafe_allow_html=True)
        st.markdown("---")

elif nav_choice == "⚙️ Manager Access Control" and st.session_state["role"] == "admin":
    st.markdown("## ⚙️ Manager Access Control & Pending Requests")
    st.markdown("Review pending user requests and manage authorization status.")
    
    pendings = run_query("SELECT id, username, requested_at FROM users WHERE status = 'pending'")
    if pendings:
        for uid, uname, req_time in pendings:
            col_a, col_b, col_c = st.columns([2, 2, 1])
            with col_a:
                st.write(f"**User:** `{uname}`")
                st.caption(f"Requested at: {req_time}")
            with col_b:
                action = st.selectbox("Assign Action", ["Pending", "Approve", "Reject"], key=f"act_{uid}")
            with col_c:
                if st.button("Apply", key=f"btn_{uid}"):
                    if action == "Approve":
                        execute_query("UPDATE users SET status = 'approved' WHERE id = ?", (uid,))
                        st.success(f"Approved {uname}!")
                        st.rerun()
                    elif action == "Reject":
                        execute_query("DELETE FROM users WHERE id = ?", (uid,))
                        st.warning(f"Rejected and removed {uname}.")
                        st.rerun()
    else:
        st.info("No pending access requests at this time.")

# ==========================================
# FOOTER WATERMARK
# ==========================================
st.markdown("---")
st.markdown(f"<p style='text-align: center; color: #64748b; font-size: 12px;'>EasyLoad All Data Analyzer | Developed by <b>Rogers</b> | Contact: 0542470810</p>", unsafe_allow_html=True)