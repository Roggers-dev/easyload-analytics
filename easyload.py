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

    /* Scorecard KPI Outlined Cards (Inspired by Enterprise Data Quality Dashboards) */
    .kpi-card-green {
        background-color: #1e293b;
        border: 2px solid #10b981;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
    }
    .kpi-card-yellow {
        background-color: #1e293b;
        border: 2px solid #eab308;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
    }
    .kpi-card-orange {
        background-color: #1e293b;
        border: 2px solid #f97316;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
    }
    .kpi-card-red {
        background-color: #1e293b;
        border: 2px solid #ef4444;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
    }
    .kpi-title {
        font-size: 13px;
        color: #94a3b8;
        margin-bottom: 4px;
        font-weight: 600;
    }
    .kpi-value {
        font-size: 26px;
        font-weight: 800;
        color: #f8fafc;
    }
    .kpi-sub {
        font-size: 14px;
        font-weight: 600;
        margin-top: 2px;
    }

    /* Section Header Bar */
    .section-banner {
        background-color: #1e293b;
        border-left: 4px solid #38bdf8;
        padding: 8px 14px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 15px;
        color: #e2e8f0;
        margin-bottom: 12px;
    }

    /* Custom Alerts & Boxes */
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
    .filter-explanation-box {
        background-color: #1e293b;
        border: 1px solid #38bdf8;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
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
        <p style='text-align: center; color: #94a3b8; max-width: 650px; margin: 0 auto 15px auto;'>
            An advanced enterprise observability & intelligence platform for KPI scorecards, data quality auditing, 
            OLS regression forecasting, anomaly detection, and statistical reporting.
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

# Dynamic Sidebar Navigation
nav_options = [
    "🎯 KPIs Scorecard & Data Quality",
    "📊 Global & Filtered Statistical Summary",
    "📈 Regression, Trends & Performers", 
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
    n = 300
    months = ["Jun 2026", "Jul 2026", "Aug 2026", "Sep 2026", "Oct 2026", "Nov 2026"]
    st.session_state['df'] = pd.DataFrame({
        "Store_ID": [f"Store-{i:03d}" for i in range(1, n+1)],
        "Region": np.random.choice(["North", "South", "East", "West"], n),
        "Period": np.random.choice(months, n),
        "Quality_Dimension": np.random.choice(["Completeness", "Accuracy", "Consistency", "Timeliness"], n),
        "Ad_Spend": np.random.randint(1000, 15000, n),
        "Sales_Revenue": np.random.randint(5000, 75000, n),
        "Customer_Rating": np.round(np.random.uniform(1.5, 5.0, n), 1)
    })
elif demo_mode == "health":
    np.random.seed(100)
    n = 300
    months = ["Jun 2026", "Jul 2026", "Aug 2026", "Sep 2026", "Oct 2026", "Nov 2026"]
    st.session_state['df'] = pd.DataFrame({
        "Patient_ID": [f"PT-{i:04d}" for i in range(1, n+1)],
        "Department": np.random.choice(["Cardiology", "Neurology", "Pediatrics", "Oncology"], n),
        "Period": np.random.choice(months, n),
        "Quality_Dimension": np.random.choice(["Vitals Integrity", "Lab Precision", "Discharge Speed", "Protocol Match"], n),
        "Treatment_Hours": np.random.randint(5, 50, n),
        "Recovery_Score": np.random.randint(40, 100, n),
        "Satisfaction": np.round(np.random.uniform(1.8, 5.0, n), 1)
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
    np.random.seed(42)
    n = 240
    months = ["Jun 2026", "Jul 2026", "Aug 2026", "Sep 2026", "Oct 2026", "Nov 2026"]
    st.session_state['df'] = pd.DataFrame({
        "Entity_ID": [f"ID-{i:03d}" for i in range(1, n+1)],
        "Category": np.random.choice(["Operations", "Finance", "Logistics", "Compliance"], n),
        "Period": np.random.choice(months, n),
        "Quality_Dimension": np.random.choice(["Completeness", "Validity", "Uniqueness", "Accuracy"], n),
        "Driver_Variable": np.random.randint(10, 100, n),
        "Outcome_Variable": np.random.randint(50, 500, n),
        "Quality_Score": np.round(np.random.uniform(1.0, 5.0, n), 1)
    })

df = st.session_state['df']
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
all_cols = df.columns.tolist()

# ==========================================
# 7. MODULE ROUTING & EXECUTION
# ==========================================

# ---------------------------------------------------------
# MODULE 1: EXECUTIVE KPIs SCORECARD & DATA QUALITY DASHBOARD
# ---------------------------------------------------------
if nav_choice == "🎯 KPIs Scorecard & Data Quality":
    st.markdown("## 🎯 KPIs Scorecard - Executive Summary")
    
    # --- TOP MULTI-FILTER BAR (Inspired by DQOps Top Toolbar) ---
    f1, f2, f3, f4 = st.columns([1.2, 1.2, 1.2, 1.4])
    
    filtered_df = df.copy()
    
    with f1:
        filter_col_1 = cat_cols[0] if len(cat_cols) > 0 else None
        if filter_col_1:
            opts1 = ["All"] + sorted(df[filter_col_1].dropna().unique().astype(str).tolist())
            sel1 = st.selectbox(f"Filter: {filter_col_1}", opts1)
            if sel1 != "All":
                filtered_df = filtered_df[filtered_df[filter_col_1].astype(str) == sel1]
        else:
            st.selectbox("Category Filter", ["All"])

    with f2:
        filter_col_2 = cat_cols[1] if len(cat_cols) > 1 else None
        if filter_col_2:
            opts2 = ["All"] + sorted(df[filter_col_2].dropna().unique().astype(str).tolist())
            sel2 = st.selectbox(f"Filter: {filter_col_2}", opts2)
            if sel2 != "All":
                filtered_df = filtered_df[filtered_df[filter_col_2].astype(str) == sel2]
        else:
            st.selectbox("Dimension Filter", ["All"])

    with f3:
        target_metric = st.selectbox("Primary KPI Metric:", numeric_cols if numeric_cols else all_cols)

    with f4:
        search_val = st.text_input("🔎 Search / Table Filter:", placeholder="Enter keyword or ID...")
        if search_val:
            mask = filtered_df.astype(str).apply(lambda x: x.str.contains(search_val, case=False, na=False)).any(axis=1)
            filtered_df = filtered_df[mask]

    # --- COMPUTE DATA QUALITY & PERFORMANCE TIERS ---
    if target_metric in numeric_cols and len(filtered_df) > 0:
        series = filtered_df[target_metric].dropna()
        q75, q50, q25 = np.percentile(series, [75, 50, 25])
        mean_val = series.mean()
        std_val = series.std() if series.std() > 0 else 1.0
        
        # Classify every record into 4 Enterprise Quality Statuses
        def classify_record(val):
            z = (val - mean_val) / std_val
            if val >= q25 and abs(z) <= 1.8:
                return "Correct / Optimal"
            elif val < q25 and abs(z) <= 1.5:
                return "Warning"
            elif abs(z) > 1.8 and abs(z) <= 2.3:
                return "Error"
            else:
                return "Fatal / Outlier"

        filtered_df = filtered_df.copy()
        filtered_df["_Audit_Status"] = filtered_df[target_metric].apply(classify_record)
    else:
        filtered_df = filtered_df.copy()
        filtered_df["_Audit_Status"] = "Correct / Optimal"

    total_checks = len(filtered_df)
    correct_cnt = (filtered_df["_Audit_Status"] == "Correct / Optimal").sum()
    warning_cnt = (filtered_df["_Audit_Status"] == "Warning").sum()
    error_cnt = (filtered_df["_Audit_Status"] == "Error").sum()
    fatal_cnt = (filtered_df["_Audit_Status"] == "Fatal / Outlier").sum()

    passed_total = correct_cnt + warning_cnt
    kpi_pct = (passed_total / total_checks * 100) if total_checks > 0 else 0.0
    
    # Global baseline comparison
    global_pct = (len(filtered_df) / len(df) * 100) if len(df) > 0 else 100.0
    delta_pct = kpi_pct - 85.0

    # --- PERIOD COMPARISON SPLIT BAR ---
    st.markdown(f"""
        <div style="display: flex; width: 100%; border-radius: 8px; overflow: hidden; margin: 10px 0 18px 0; font-weight: 700; font-size: 14px;">
            <div style="width: {max(min(kpi_pct, 85), 25)}%; background-color: #0d9488; color: white; padding: 10px; text-align: center;">
                Active Scope ({total_checks:,} checks | {kpi_pct:.1f}% Pass Rate)
            </div>
            <div style="flex-grow: 1; background-color: #334155; color: #cbd5e1; padding: 10px; text-align: center;">
                Global Baseline ({len(df):,} total records)
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- ROW 1: SEMI-CIRCULAR GAUGE & KPI HISTORY BAR CHART ---
    g_col, h_col = st.columns([1, 1.3])
    
    with g_col:
        st.markdown("<div class='section-banner'>Percentage of Passed Checks (KPI Score)</div>", unsafe_allow_html=True)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=kpi_pct,
            number={'suffix': "%", 'font': {'size': 42, 'color': '#f8fafc'}},
            delta={'reference': 85.0, 'increasing': {'color': '#10b981'}, 'decreasing': {'color': '#ef4444'}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#94a3b8"},
                'bar': {'color': "#0284c7"},
                'bgcolor': "#334155",
                'borderwidth': 0,
                'steps': [
                    {'range': [0, 60], 'color': 'rgba(239, 68, 68, 0.25)'},
                    {'range': [60, 85], 'color': 'rgba(234, 179, 8, 0.25)'},
                    {'range': [85, 100], 'color': 'rgba(16, 185, 129, 0.25)'}
                ],
            }
        ))
        fig_gauge.update_layout(
            height=270,
            margin=dict(l=20, r=20, t=30, b=10),
            paper_bgcolor='#1e293b',
            font={'color': "#f8fafc"}
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    with h_col:
        st.markdown("<div class='section-banner'>KPIs History by Period / Category</div>", unsafe_allow_html=True)
        group_col = "Period" if "Period" in filtered_df.columns else (cat_cols[0] if cat_cols else all_cols[0])
        
        hist_df = filtered_df.groupby(group_col).apply(
            lambda g: ((g["_Audit_Status"].isin(["Correct / Optimal", "Warning"])).sum() / len(g) * 100) if len(g) > 0 else 0
        ).reset_index(name="Pass_Rate")
        
        fig_hist = px.bar(
            hist_df, x=group_col, y="Pass_Rate",
            text=hist_df["Pass_Rate"].apply(lambda x: f"{x:.1f}%"),
            color_discrete_sequence=["#38bdf8"]
        )
        fig_hist.update_traces(textposition='outside')
        fig_hist.update_layout(
            height=270,
            yaxis=dict(range=[0, 115], title="KPI %"),
            xaxis=dict(title=""),
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor='#1e293b',
            plot_bgcolor='#1e293b',
            font_color='#f8fafc'
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    # --- ROW 2: COLOR-CODED SCORECARD CARDS & DONUT CHART ---
    cards_col, donut_col = st.columns([1.3, 1])
    
    with cards_col:
        st.markdown("<div class='section-banner'>Passed Data Quality & Performance Checks</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            c_pct = (correct_cnt / total_checks * 100) if total_checks > 0 else 0
            st.markdown(f"""
                <div class="kpi-card-green">
                    <div class="kpi-title">Correct / Optimal Results</div>
                    <div class="kpi-value">{correct_cnt:,}</div>
                    <div class="kpi-sub" style="color: #10b981;">{c_pct:.1f}% of total</div>
                </div>
            """, unsafe_allow_html=True)
        with c2:
            w_pct = (warning_cnt / total_checks * 100) if total_checks > 0 else 0
            st.markdown(f"""
                <div class="kpi-card-yellow">
                    <div class="kpi-title">Warnings (Near Threshold)</div>
                    <div class="kpi-value">{warning_cnt:,}</div>
                    <div class="kpi-sub" style="color: #eab308;">{w_pct:.1f}% of total</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<div class='section-banner' style='margin-top: 16px;'>Failed Data Quality & Anomaly Checks</div>", unsafe_allow_html=True)
        c3, c4 = st.columns(2)
        with c3:
            e_pct = (error_cnt / total_checks * 100) if total_checks > 0 else 0
            st.markdown(f"""
                <div class="kpi-card-orange">
                    <div class="kpi-title">Errors (Below Standard)</div>
                    <div class="kpi-value">{error_cnt:,}</div>
                    <div class="kpi-sub" style="color: #f97316;">{e_pct:.1f}% of total</div>
                </div>
            """, unsafe_allow_html=True)
        with c4:
            f_pct = (fatal_cnt / total_checks * 100) if total_checks > 0 else 0
            st.markdown(f"""
                <div class="kpi-card-red">
                    <div class="kpi-title">Fatal Errors / Severe Outliers</div>
                    <div class="kpi-value">{fatal_cnt:,}</div>
                    <div class="kpi-sub" style="color: #ef4444;">{f_pct:.1f}% of total</div>
                </div>
            """, unsafe_allow_html=True)

    with donut_col:
        st.markdown("<div class='section-banner'>Percentage of Executed Checks</div>", unsafe_allow_html=True)
        status_counts = pd.DataFrame({
            "Status": ["Correct / Optimal", "Warning", "Error", "Fatal / Outlier"],
            "Count": [correct_cnt, warning_cnt, error_cnt, fatal_cnt]
        })
        fig_donut = px.pie(
            status_counts, values="Count", names="Status", hole=0.58,
            color="Status",
            color_discrete_map={
                "Correct / Optimal": "#10b981",
                "Warning": "#eab308",
                "Error": "#f97316",
                "Fatal / Outlier": "#ef4444"
            }
        )
        fig_donut.update_traces(textinfo='percent', textfont_size=13)
        fig_donut.update_layout(
            height=305,
            margin=dict(l=10, r=10, t=20, b=20),
            paper_bgcolor='#1e293b',
            font_color='#f8fafc',
            legend=dict(orientation="v", yanchor="middle", y=0.5)
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    # --- ROW 3: GROUPED DISTRIBUTION BAR CHART ---
    st.markdown("<div class='section-banner' style='margin-top: 10px;'>Distribution of Check Results Across Segments</div>", unsafe_allow_html=True)
    dist_df = filtered_df.groupby([group_col, "_Audit_Status"]).size().reset_index(name="Records")
    fig_grouped = px.bar(
        dist_df, x=group_col, y="Records", color="_Audit_Status", barmode="group",
        color_discrete_map={
            "Correct / Optimal": "#10b981",
            "Warning": "#eab308",
            "Error": "#f97316",
            "Fatal / Outlier": "#ef4444"
        }
    )
    fig_grouped.update_layout(
        height=320,
        xaxis_title="",
        yaxis_title="Number of Records",
        legend_title="Audit Status",
        paper_bgcolor='#1e293b',
        plot_bgcolor='#1e293b',
        font_color='#f8fafc'
    )
    st.plotly_chart(fig_grouped, use_container_width=True)

# ---------------------------------------------------------
# MODULE 2: GLOBAL & FILTERED STATISTICAL SUMMARY
# ---------------------------------------------------------
elif nav_choice == "📊 Global & Filtered Statistical Summary":
    st.markdown("## 📊 Global & Filtered Statistical Summary")
    st.markdown("Automatic computation of summation, mean (average), median, standard deviation, and frequency curves across your dataset.")
    
    # --- INTERACTIVE FILTER SECTION ---
    filtered_df = df.copy()
    if cat_cols:
        with st.expander("🛠️ Filter Data by Categories (Dynamic Subset Computation)", expanded=True):
            selected_filters = {}
            f_cols = st.columns(min(len(cat_cols), 3))
            for i, c_col in enumerate(cat_cols[:3]):
                with f_cols[i]:
                    unique_vals = sorted(df[c_col].dropna().unique().astype(str).tolist())
                    chosen_vals = st.multiselect(f"Filter {c_col}:", unique_vals, default=[])
                    if chosen_vals:
                        selected_filters[c_col] = chosen_vals
            
            if selected_filters:
                for col_name, vals in selected_filters.items():
                    filtered_df = filtered_df[filtered_df[col_name].astype(str).isin(vals)]

    # --- FILTER EXPLANATION BOX ---
    global_count = len(df)
    filtered_count = len(filtered_df)
    pct_scope = (filtered_count / global_count * 100) if global_count > 0 else 0
    
    filter_summary_text = "No category filters active (showing 100% of global data)."
    if cat_cols and 'selected_filters' in locals() and selected_filters:
        active_parts = [f"<b>{k}</b> in [{', '.join(v)}]" for k, v in selected_filters.items()]
        filter_summary_text = "Active Filters: " + " AND ".join(active_parts)

    st.markdown(f"""
        <div class='filter-explanation-box'>
            <b>📌 Statistical Scope & Filter Explanation:</b><br>
            • <b>Global Dataset Records:</b> <b>{global_count:,}</b> | <b>Filtered Records:</b> <b>{filtered_count:,}</b> ({pct_scope:.1f}% of total)<br>
            • {filter_summary_text}<br>
            <i>Analytical Note:</i> Every placeholder card below compares the filtered subset metric directly against the global baseline.
        </div>
    """, unsafe_allow_html=True)

    # --- INDIVIDUAL COLUMN INFORMATION PLACEHOLDERS ---
    st.markdown("### 📌 Individual Column Computed Placeholders")
    if numeric_cols:
        for num_c in numeric_cols:
            st.markdown(f"#### 📊 Column: `{num_c}`")
            col_full = df[num_c].dropna()
            col_filt = filtered_df[num_c].dropna()
            
            if len(col_filt) > 0:
                m1, m2, m3, m4, m5, m6 = st.columns(6)
                with m1:
                    st.metric("Summation (Total)", f"{col_filt.sum():,.1f}", delta=f"Global: {col_full.sum():,.1f}")
                with m2:
                    st.metric("Mean (Average)", f"{col_filt.mean():,.2f}", delta=f"Global: {col_full.mean():,.2f}")
                with m3:
                    st.metric("Median", f"{col_filt.median():,.2f}", delta=f"Global: {col_full.median():,.2f}")
                with m4:
                    st.metric("Count", f"{len(col_filt):,}", delta=f"{len(col_filt)/len(col_full)*100:.0f}% scope")
                with m5:
                    st.metric("Std Deviation", f"{col_filt.std():,.2f}")
                with m6:
                    st.metric("Min / Max", f"{col_filt.min():,.1f} / {col_filt.max():,.1f}")
            st.markdown("---")

        # --- FREQUENCY DISTRIBUTION CURVE ---
        st.markdown("### 📈 Frequency Distribution Curve & Density")
        dist_col = st.selectbox("Select Numeric Column for Frequency Curve:", numeric_cols)
        fig_freq = px.histogram(
            filtered_df, x=dist_col, nbins=25, marginal="box",
            title=f"Frequency Distribution & Box Spread for {dist_col}",
            color_discrete_sequence=["#38bdf8"]
        )
        fig_freq.update_layout(paper_bgcolor='#1e293b', plot_bgcolor='#1e293b', font_color='#f8fafc')
        st.plotly_chart(fig_freq, use_container_width=True)
    else:
        st.warning("No numeric columns available for statistical cards.")

    st.markdown("### 📋 Filtered Data Table")
    st.dataframe(filtered_df, use_container_width=True)

# ---------------------------------------------------------
# MODULE 3: OLS REGRESSION, TRENDS & PERFORMERS
# ---------------------------------------------------------
elif nav_choice == "📈 Regression, Trends & Performers":
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

# ---------------------------------------------------------
# MODULE 4: PIVOT SUMMARIES & COUNTS
# ---------------------------------------------------------
elif nav_choice == "🔀 Pivot Summaries & Counts":
    st.markdown("## 🔀 Pivot Summaries & Aggregations")
    if len(numeric_cols) > 0 and len(all_cols) > 1:
        cat_col = st.selectbox("Select Category Column:", cat_cols if cat_cols else all_cols)
        num_col = st.selectbox("Select Metric to Aggregate:", numeric_cols)
        summary_df = df.groupby(cat_col)[num_col].agg(['count', 'sum', 'mean', 'median', 'std']).reset_index()
        st.dataframe(summary_df, use_container_width=True)
    else:
        st.warning("Insufficient categorical or numeric columns for aggregation.")

# ---------------------------------------------------------
# MODULE 5: LIVE MOBILE SIMULATOR
# ---------------------------------------------------------
elif nav_choice == "📱 Live Mobile Simulator":
    st.markdown("## 📱 Live Mobile Responsive View")
    st.info("Simulating mobile layout scaling for enterprise field agents.")
    st.metric("Total Records Loaded", len(df))
    st.metric("Active Data Columns", len(df.columns))

# ---------------------------------------------------------
# MODULE 6: TEAM DISCUSSIONS
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# MODULE 7: MANAGER ACCESS CONTROL (ADMIN ONLY)
# ---------------------------------------------------------
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