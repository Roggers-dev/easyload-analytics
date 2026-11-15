import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
import sqlite3
import hashlib
from datetime import datetime

# ==========================================
# 1. PAGE CONFIGURATION & HIGH-IMPACT STYLING
# ==========================================
st.set_page_config(
    page_title="Voices - Secure Enterprise Analytics",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); color: #f8fafc; }
    .stSidebar { background-color: #090d16; border-right: 1px solid #1e293b; }
    
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #38bdf8;
        padding: 18px;
        border-radius: 14px;
        text-align: center;
        box-shadow: 0 8px 20px -4px rgba(56, 189, 248, 0.18);
    }
    .metric-title { color: #94a3b8; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { color: #38bdf8; font-size: 24px; font-weight: 800; margin-top: 5px; }
    
    .anomaly-alert {
        background: rgba(239, 68, 68, 0.15);
        border-left: 5px solid #ef4444;
        border: 1px solid #7f1d1d;
        padding: 16px;
        border-radius: 0 10px 10px 0;
        margin-bottom: 16px;
        font-size: 14px;
        color: #fca5a5;
    }
    .winner-box {
        background: rgba(34, 197, 94, 0.12);
        border-left: 5px solid #22c55e;
        border: 1px solid #14532d;
        padding: 16px;
        border-radius: 0 10px 10px 0;
        margin-bottom: 12px;
        font-size: 14px;
        color: #bbf7d0;
    }
    .loser-box {
        background: rgba(245, 158, 11, 0.12);
        border-left: 5px solid #f59e0b;
        border: 1px solid #78350f;
        padding: 16px;
        border-radius: 0 10px 10px 0;
        margin-bottom: 12px;
        font-size: 14px;
        color: #fde68a;
    }
    .decision-box {
        background: rgba(30, 41, 59, 0.85);
        border-left: 5px solid #38bdf8;
        border: 1px solid #334155;
        padding: 16px;
        border-radius: 0 10px 10px 0;
        margin-bottom: 16px;
        font-size: 14px;
        color: #e2e8f0;
    }
    
    .phone-outer {
        width: 310px;
        height: 600px;
        background: #020617;
        border: 9px solid #1e293b;
        border-radius: 38px;
        margin: 15px auto;
        padding: 14px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.8);
        overflow-y: auto;
    }
    .phone-notch {
        width: 90px;
        height: 15px;
        background: #1e293b;
        margin: 0 auto 14px auto;
        border-radius: 10px;
    }
    
    .developer-footer {
        text-align: center; color: #94a3b8; font-size: 12px;
        margin-top: 45px; border-top: 1px solid #1e293b; padding-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SECURE PASSWORD HASHING & AUTO-MIGRATING DB
# ==========================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect('voices_enterprise.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
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
    
    # Auto-migration check: add 'requested_at' if an older table version exists without it
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN requested_at TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass # Column already exists, safe to ignore
        
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            comment TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    
    # Default Master Admin Seed (Hashed)
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        secure_admin_pass = hash_password("Admin2026!")
        cursor.execute("INSERT INTO users (username, password, role, status, requested_at) VALUES (?, ?, ?, ?, ?)",
                       ("admin", secure_admin_pass, "admin", "approved", datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
    conn.close()

init_db()

def run_query(query, params=(), fetch=False):
    conn = sqlite3.connect('voices_enterprise.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(query, params)
    if fetch:
        result = cursor.fetchall()
        conn.close()
        return result
    conn.commit()
    conn.close()

# ==========================================
# 3. PERFORMANCE OPTIMIZED DEMO DATA GENERATOR
# ==========================================
@st.cache_data
def generate_demo_data(mode="Store Sales"):
    np.random.seed(42)
    if mode == "Store Sales":
        branches = [f"Branch_{i:03d}" for i in range(1, 151)]
        regions = np.random.choice(["Greater Accra", "Ashanti", "Western", "Northern"], 150)
        ad_spend = np.random.uniform(500, 5000, 150).round(2)
        revenue = (ad_spend * 4.2 + np.random.normal(1500, 1200, 150)).round(2)
        revenue[5] = 48500.00
        revenue[42] = 1900.00
        return pd.DataFrame({
            "Branch_Name": branches,
            "Region": regions,
            "Ad_Spend_GHS": ad_spend,
            "Monthly_Revenue_GHS": revenue,
            "Customer_Footfall": (revenue / 45).astype(int)
        })
    else:
        patients = [f"Patient_{i:03d}" for i in range(1, 151)]
        wards = np.random.choice(["General Ward", "Cardiology", "Outpatient", "Wellness Clinic"], 150)
        bmi = np.random.uniform(19.5, 34.0, 150).round(1)
        systolic_bp = (95 + bmi * 1.1 + np.random.normal(0, 6, 150)).round(0)
        systolic_bp[12] = 182.0  
        systolic_bp[88] = 171.0 
        return pd.DataFrame({
            "Patient_ID": patients,
            "Department": wards,
            "BMI_Index": bmi,
            "Systolic_BP": systolic_bp,
            "Heart_Rate_BPM": np.random.randint(62, 105, 150)
        })

# ==========================================
# 4. SECURE AUTHENTICATION GATE
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["username"] = ""
    st.session_state["role"] = ""

if not st.session_state["authenticated"]:
    st.markdown("<h1 style='text-align: center; color: #38bdf8;'>🛡️ Voices Secure Enterprise Gateway</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8;'>Strict authentication required. Unauthorized access is blocked.</p>", unsafe_allow_html=True)
    
    tab_login, tab_register = st.tabs(["🔑 Secure Sign In", "📝 Request Platform Access"])
    
    with tab_login:
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            with st.form("login_form"):
                u_input = st.text_input("Username")
                p_input = st.text_input("Password", type="password")
                login_btn = st.form_submit_button("Authenticate & Enter", use_container_width=True)
                
                if login_btn:
                    user_record = run_query("SELECT password, role, status FROM users WHERE username = ?", (u_input,), fetch=True)
                    if user_record:
                        db_pass, db_role, db_status = user_record[0]
                        hashed_input_pass = hash_password(p_input)
                        
                        if db_pass == hashed_input_pass:
                            if db_status == "approved":
                                st.session_state["authenticated"] = True
                                st.session_state["username"] = u_input
                                st.session_state["role"] = db_role
                                st.rerun()
                            else:
                                st.warning("🔒 Access Pending: Your account requires administrator approval.")
                        else:
                            st.error("❌ Authentication Failed: Incorrect password.")
                    else:
                        st.error("❌ Authentication Failed: Username not recognized.")
                        
    with tab_register:
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            with st.form("register_form"):
                new_user = st.text_input("Choose Username")
                new_pass = st.text_input("Choose Secure Password", type="password")
                reg_btn = st.form_submit_button("Submit Access Request", use_container_width=True)
                
                if reg_btn:
                    if new_user and new_pass:
                        try:
                            hashed_new_pass = hash_password(new_pass)
                            run_query("INSERT INTO users (username, password, role, status, requested_at) VALUES (?, ?, ?, ?, ?)",
                                      (new_user, hashed_new_pass, "user", "pending", datetime.now().strftime("%Y-%m-%d %H:%M")))
                            st.success("✅ Request submitted securely! Await administrator approval.")
                        except sqlite3.IntegrityError:
                            st.error("❌ Username already taken. Choose another.")
                    else:
                        st.error("⚠️ Please complete all fields.")
                        
    st.markdown("<div class='developer-footer'>Secured & Engineered by <b>Rogers</b> | Contact: <b>0542470810</b></div>", unsafe_allow_html=True)
    st.stop()

# ==========================================
# 5. GLOBAL PERSISTENT DATA & SIDEBAR
# ==========================================
st.sidebar.markdown(f"👤 **User:** `{st.session_state['username']}` | 🔑 `{st.session_state['role'].upper()}`")
if st.sidebar.button("Secure Logout", use_container_width=True):
    st.session_state["authenticated"] = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 📂 Data & Traffic Manager")

uploaded_file = st.sidebar.file_uploader("Upload CSV or Excel File", type=["csv", "xlsx"], key="global_dataset")

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            st.session_state["df"] = pd.read_csv(uploaded_file)
        else:
            st.session_state["df"] = pd.read_excel(uploaded_file)
        st.session_state["data_source"] = uploaded_file.name
    except Exception as e:
        st.sidebar.error(f"Error loading file: {e}")

st.sidebar.markdown("**Or Load Optimized Demo Data:**")
demo_col1, demo_col2 = st.sidebar.columns(2)
with demo_col1:
    if st.button("🛍️ Store Demo", use_container_width=True):
        st.session_state["df"] = generate_demo_data("Store Sales")
        st.session_state["data_source"] = "Demo: Retail Store Branches"
        st.rerun()
with demo_col2:
    if st.button("🏥 Health Demo", use_container_width=True):
        st.session_state["df"] = generate_demo_data("Health Data")
        st.session_state["data_source"] = "Demo: Clinical Patient Vitals"
        st.rerun()

if "df" in st.session_state and st.session_state["df"] is not None:
    st.sidebar.success(f"Active: {st.session_state.get('data_source', 'Dataset')} ({st.session_state['df'].shape[0]:,} rows)")

st.sidebar.markdown("---")
nav_choice = st.sidebar.radio("Navigation Menu", [
    "📈 Regression, Trends & Performers", 
    "📊 Global & Selected Metrics",
    "🔀 Pivot Summaries & Counts",
    "📱 Live Mobile Simulator", 
    "💬 Team Discussions", 
    "⚙️ Manager Access Control" if st.session_state["role"] == "admin" else None
])

if not nav_choice:
    nav_choice = "📈 Regression, Trends & Performers"

st.sidebar.markdown("---")
st.sidebar.markdown("<div style='font-size: 11px; color: #94a3b8; text-align: center;'>Rogers | 0542470810</div>", unsafe_allow_html=True)

def get_active_data():
    return st.session_state.get("df", None)

# ==========================================
# 6. VIEW: REGRESSION, TRENDS & PERFORMERS
# ==========================================
if nav_choice == "📈 Regression, Trends & Performers":
    st.markdown("<h1 style='color: #f8fafc; text-align: center;'>📈 Regression Trends, Anomalies & Decision Hub</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8;'>Optimized high-performance analytics engine with anomaly detection.</p>", unsafe_allow_html=True)
    st.markdown("---")

    df = get_active_data()

    if df is not None:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        all_cols = df.columns.tolist()

        if numeric_cols:
            g_mean = df[numeric_cols].mean().mean()
            g_med = df[numeric_cols].median().median()
            g_sd = df[numeric_cols].std().mean()
            
            st.markdown("#### 🌐 Dataset Global Baseline (All Numeric Columns)")
            gm1, gm2, gm3 = st.columns(3)
            with gm1: st.markdown(f"<div class='metric-card'><div class='metric-title'>Total Global Mean</div><div class='metric-value'>{g_mean:,.2f}</div></div>", unsafe_allow_html=True)
            with gm2: st.markdown(f"<div class='metric-card'><div class='metric-title'>Total Global Median</div><div class='metric-value'>{g_med:,.2f}</div></div>", unsafe_allow_html=True)
            with gm3: st.markdown(f"<div class='metric-card'><div class='metric-title'>Total Global Deviation</div><div class='metric-value'>{g_sd:,.2f}</div></div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

        if len(numeric_cols) >= 2:
            sel1, sel2, sel3 = st.columns(3)
            with sel1:
                col_x = st.selectbox("1️⃣ Driver Variable (X-Axis):", numeric_cols, index=0)
            with sel2:
                col_y = st.selectbox("2️⃣ Outcome Variable (Y-Axis):", numeric_cols, index=min(1, len(numeric_cols)-1))
            with sel3:
                label_col = st.selectbox("3️⃣ Name / ID Column:", all_cols, index=0)

            work_df = df[[label_col, col_x, col_y]].dropna().copy()
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
                    • <b>Trustworthiness ($R^2$ Accuracy):</b> <b>{r_sq*100:.1f}%</b> ({'High confidence—use this trend to plan targets!' if r_sq >= 0.5 else 'Moderate confidence—other factors are also at play.'})
                </div>
            """, unsafe_allow_html=True)

            st.markdown("#### 🔮 Interactive 'What-If' Decision Simulator")
            sim_col1, sim_col2 = st.columns([1, 2])
            with sim_col1:
                sim_input = st.number_input(f"Test an input value for {col_x}:", value=float(work_df[col_x].mean()))
            with sim_col2:
                pred_outcome = model.predict([[sim_input]])[0]
                st.metric(label=f"Expected Outcome for {col_y}", value=f"{pred_outcome:,.2f}", delta=f"{pred_outcome - work_df[col_y].mean():,.2f} vs average")

        else:
            st.warning("⚠️ Please upload a dataset with at least **two numeric columns** to run regression models.")

        # ------------------------------------------
        # PERFORMANCE-OPTIMIZED PAGINATED TABLE
        # ------------------------------------------
        st.markdown("---")
        st.markdown("### 📂 Filter Dataset & Anti-Freeze Pagination")
        st.markdown("<p style='color: #94a3b8; font-size: 13px;'>Filtered results are paginated in chunks to prevent browser freezing under heavy traffic.</p>", unsafe_allow_html=True)
        
        f_col1, f_col2 = st.columns([1, 2])
        with f_col1:
            filter_col = st.selectbox("Choose Column to Filter:", df.columns.tolist())
        with f_col2:
            unique_vals = df[filter_col].dropna().unique()
            if len(unique_vals) <= 50:
                selected_vals = st.multiselect(f"Select specific '{filter_col}' values:", options=unique_vals)
                filtered_df = df[df[filter_col].isin(selected_vals)] if selected_vals else df
            else:
                search_val = st.text_input(f"Search inside '{filter_col}':")
                filtered_df = df[df[filter_col].astype(str).str.contains(search_val, case=False, na=False)] if search_val else df

        page_size = 25
        total_rows = len(filtered_df)
        total_pages = max(1, (total_rows - 1) // page_size + 1)
        
        p_col1, p_col2 = st.columns([1, 3])
        with p_col1:
            page_num = st.number_input("Page Number:", min_value=1, max_value=total_pages, value=1)
        with p_col2:
            st.markdown(f"<p style='margin-top: 28px; color: #94a3b8; font-size: 12px;'>Showing page {page_num} of {total_pages} ({total_rows:,} total records)</p>", unsafe_allow_html=True)

        start_idx = (page_num - 1) * page_size
        end_idx = start_idx + page_size
        paginated_df = filtered_df.iloc[start_idx:end_idx]

        st.dataframe(paginated_df, use_container_width=True)
    else:
        st.info("👈 Upload your CSV/Excel file in the sidebar—or click **🛍️ Store Demo** / **🏥 Health Demo** to test live data instantly!")

# ==========================================
# 7. VIEW: GLOBAL & SELECTED METRICS
# ==========================================
elif nav_choice == "📊 Global & Selected Metrics":
    st.markdown("<h1 style='color: #f8fafc; text-align: center;'>📊 Global & Selected Column Statistics</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8;'>Compare overall dataset averages against any specific column you pick.</p>", unsafe_allow_html=True)
    st.markdown("---")

    df = get_active_data()
    if df is not None:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            st.markdown("### 🌐 Total Global Baseline (All Numeric Columns)")
            g_mean = df[numeric_cols].mean().mean()
            g_med = df[numeric_cols].median().median()
            g_sd = df[numeric_cols].std().mean()

            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f"<div class='metric-card'><div class='metric-title'>Total Global Mean</div><div class='metric-value'>{g_mean:,.2f}</div></div>", unsafe_allow_html=True)
            with c2: st.markdown(f"<div class='metric-card'><div class='metric-title'>Total Global Median</div><div class='metric-value'>{g_med:,.2f}</div></div>", unsafe_allow_html=True)
            with c3: st.markdown(f"<div class='metric-card'><div class='metric-title'>Total Global Deviation</div><div class='metric-value'>{g_sd:,.2f}</div></div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 🎯 Inspect Specific Column")
            target_col = st.selectbox("Select Column for Detailed Stats:", numeric_cols)
            
            m_val = df[target_col].mean()
            med_val = df[target_col].median()
            sd_val = df[target_col].std()
            min_v = df[target_col].min()
            max_v = df[target_col].max()

            sc1, sc2, sc3, sc4, sc5 = st.columns(5)
            with sc1: st.markdown(f"<div class='metric-card'><div class='metric-title'>Column Mean</div><div class='metric-value'>{m_val:,.2f}</div></div>", unsafe_allow_html=True)
            with sc2: st.markdown(f"<div class='metric-card'><div class='metric-title'>Column Median</div><div class='metric-value'>{med_val:,.2f}</div></div>", unsafe_allow_html=True)
            with sc3: st.markdown(f"<div class='metric-card'><div class='metric-title'>Std Deviation</div><div class='metric-value'>{sd_val:,.2f}</div></div>", unsafe_allow_html=True)
            with sc4: st.markdown(f"<div class='metric-card'><div class='metric-title'>Minimum</div><div class='metric-value'>{min_v:,.2f}</div></div>", unsafe_allow_html=True)
            with sc5: st.markdown(f"<div class='metric-card'><div class='metric-title'>Maximum</div><div class='metric-value'>{max_v:,.2f}</div></div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"""
                <div class='decision-box'>
                    <b>📖 Plain-English Explanation for `{target_col}`:</b><br>
                    • <b>Mean ({m_val:,.2f}) vs. Median ({med_val:,.2f}):</b> {'Your average is higher than the middle value—extreme high records are pulling the average up. Rely on the Median for realistic planning!' if m_val > med_val * 1.15 else 'Your average and middle value are well-balanced.'}<br>
                    • <b>Spread ({sd_val:,.2f}):</b> {'High spread—expect wide variance record-to-record.' if sd_val > m_val * 0.3 else 'Low spread—performance is steady.'}
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("👈 Load a dataset from the sidebar first.")

# ==========================================
# 8. VIEW: PIVOT SUMMARIES & COUNTS
# ==========================================
elif nav_choice == "🔀 Pivot Summaries & Counts":
    st.markdown("<h1 style='color: #f8fafc; text-align: center;'>🔀 Group Counts & Summary Tables</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8;'>Count records and compare category totals cleanly.</p>", unsafe_allow_html=True)
    st.markdown("---")

    df = get_active_data()
    if df is not None:
        cols = df.columns.tolist()
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        p1, p2, p3 = st.columns(3)
        with p1: grp = st.selectbox("Group By Category:", cols)
        with p2: val = st.selectbox("Measure Column:", num_cols if num_cols else cols)
        with p3: func = st.selectbox("Calculation:", ["Count Records", "Average (Mean)", "Total Sum"])

        if func == "Count Records":
            res = df.groupby(grp).size().reset_index(name="Record_Count").sort_values(by="Record_Count", ascending=False)
        elif func == "Average (Mean)":
            res = df.groupby(grp)[val].mean().reset_index().sort_values(by=val, ascending=False)
        else:
            res = df.groupby(grp)[val].sum().reset_index().sort_values(by=val, ascending=False)

        st.dataframe(res, use_container_width=True)
    else:
        st.info("👈 Load a dataset from the sidebar first.")

# ==========================================
# 9. VIEW: LIVE MOBILE SIMULATOR
# ==========================================
elif nav_choice == "📱 Live Mobile Simulator":
    st.markdown("<h1 style='text-align: center; color: #f8fafc;'>📱 Live Smartphone Preview</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8;'>See your active data insights formatted for mobile users.</p>", unsafe_allow_html=True)
    st.markdown("---")

    df = get_active_data()
    source_name = st.session_state.get("data_source", "No Dataset Loaded")
    row_count = f"{len(df):,} Active Rows" if df is not None else "Waiting for data..."

    st.markdown(f"""
        <div class="phone-outer">
            <div class="phone-notch"></div>
            <h3 style="color: #38bdf8; text-align: center; font-size: 17px; margin-bottom: 2px;">Voices Mobile</h3>
            <p style="color: #94a3b8; text-align: center; font-size: 11px;">{source_name}</p>
            <hr style="border-color: #334155;">
            <div style="background: #1e293b; padding: 12px; border-radius: 10px; margin-bottom: 10px; border-left: 3px solid #22c55e;">
                <b style="color: #f8fafc; font-size: 13px;">🛡️ Secure & Optimized</b>
                <p style="color: #38bdf8; font-size: 11px; margin: 4px 0;">{row_count}</p>
                <p style="color: #94a3b8; font-size: 10px; margin: 0;">SHA-256 Auth & Pagination Active.</p>
            </div>
            <div style="text-align: center; margin-top: 60px; color: #64748b; font-size: 10px;">
                Engineered by Rogers<br>0542470810
            </div>
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# 10. VIEW: TEAM DISCUSSIONS
# ==========================================
elif nav_choice == "💬 Team Discussions":
    st.markdown("<h1 style='color: #f8fafc;'>💬 Team Decision Notes</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8;'>Log decisions, anomaly findings, and action items with your team.</p>", unsafe_allow_html=True)
    st.markdown("---")

    with st.form("comment_form"):
        txt = st.text_area("Share an insight or decision note:")
        if st.form_submit_button("Post Note") and txt.strip():
            run_query("INSERT INTO comments (username, comment, timestamp) VALUES (?, ?, ?)",
                      (st.session_state["username"], txt, datetime.now().strftime("%Y-%m-%d %H:%M")))
            st.success("Note saved!")
            st.rerun()

    for u, c, t in run_query("SELECT username, comment, timestamp FROM comments ORDER BY id DESC", fetch=True):
        st.markdown(f"<div class='decision-box'><b>@{u}</b> <span style='color:#94a3b8;font-size:11px;'>({t})</span><p style='margin:6px 0 0 0;'>{c}</p></div>", unsafe_allow_html=True)

# ==========================================
# 11. VIEW: MANAGER ACCESS CONTROL (Admin Only)
# ==========================================
elif nav_choice == "⚙️ Manager Access Control" and st.session_state["role"] == "admin":
    st.markdown("<h1 style='color: #f8fafc;'>⚙️ Individual Request Management</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8;'>Review pending requests, assign specific roles, and manage access.</p>", unsafe_allow_html=True)
    st.markdown("---")

    pendings = run_query("SELECT id, username, requested_at FROM users WHERE status = 'pending'", fetch=True)
    if pendings:
        for uid, uname, req_time in pendings:
            c1, c2, c3, c4 = st.columns([2, 1.5, 1, 1])
            with c1:
                st.write(f"**@{uname}**")
                st.caption(f"Requested: {req_time or 'Recently'}")
            with c2:
                role_pick = st.selectbox("Role", ["user", "analyst", "health_specialist"], key=f"role_{uid}")
            with c3:
                if st.button("Approve", key=f"app_{uid}", use_container_width=True):
                    run_query("UPDATE users SET status = 'approved', role = ? WHERE id = ?", (role_pick, uid))
                    st.rerun()
            with c4:
                if st.button("Reject", key=f"rej_{uid}", use_container_width=True):
                    run_query("DELETE FROM users WHERE id = ?", (uid,))
                    st.rerun()
            st.markdown("---")
    else:
        st.info("No pending requests in the queue.")

    st.markdown("### 👥 Approved Active Directory")
    for uname, urole in run_query("SELECT username, role FROM users WHERE status = 'approved'", fetch=True):
        st.markdown(f"- **@{uname}** — Role: `{urole.upper()}`")

# Global Developer Footer
st.markdown("<div class='developer-footer'>Engineered by <b>Rogers</b> &nbsp;|&nbsp; Contact: <b>0542470810</b></div>", unsafe_allow_html=True)