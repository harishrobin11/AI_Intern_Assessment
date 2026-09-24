import os
import sys
import json
import httpx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ensure workspace root is in python path for local fallback imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Page Configuration
st.set_page_config(
    page_title="SupportIQ — AI Ticket Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configurable API URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Custom CSS for Modern Aesthetic
st.markdown("""
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    
    /* Header banner */
    .header-banner {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 12px;
        padding: 24px 32px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }
    .header-banner h1 {
        color: #60a5fa;
        font-weight: 700;
        margin-bottom: 6px;
        font-size: 2.2rem;
    }
    .header-banner p {
        color: #94a3b8;
        font-size: 1.05rem;
        margin: 0;
    }
    
    /* Metric KPI Cards */
    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #2563eb !important;
    }
    
    /* Answer Card */
    .answer-card {
        background-color: #f8fafc;
        border-left: 5px solid #2563eb;
        border-radius: 8px;
        padding: 20px;
        margin-top: 16px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .answer-card h3 {
        color: #1e293b;
        margin-top: 0;
    }
    .answer-text {
        font-size: 1.15rem;
        color: #0f172a;
        line-height: 1.6;
    }
    
    /* Severity badges */
    .badge-critical {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
    }
    .badge-high {
        background-color: #ffedd5;
        color: #c2410c;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
    }
    .badge-medium {
        background-color: #fef3c7;
        color: #b45309;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
    }
    .badge-low {
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions to call API with local fallback
@st.cache_data(ttl=5)
def fetch_health():
    try:
        resp = httpx.get(f"{API_BASE_URL}/health", timeout=3.0)
        if resp.status_code == 200:
            return resp.json(), True
    except Exception:
        pass
    
    # Fallback to local services
    try:
        from app.services.data_service import data_service
        from app.config import settings
        h = data_service.get_health_status()
        h["groq_configured"] = bool(settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("replace_with"))
        h["groq_model"] = settings.GROQ_MODEL
        return h, False
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, False

@st.cache_data(ttl=5)
def fetch_summary():
    try:
        resp = httpx.get(f"{API_BASE_URL}/summary", timeout=3.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    
    # Fallback to local
    from app.services.data_service import data_service
    return data_service.get_summary_stats()

def post_query(question: str):
    try:
        resp = httpx.post(f"{API_BASE_URL}/query", json={"question": question}, timeout=15.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass

    # Local service fallback
    from app.services.query_service import query_service
    q_resp = query_service.process_query(question)
    return q_resp.model_dump()

@st.cache_data(ttl=5)
def fetch_anomalies(anomaly_type=None, severity=None):
    params = {}
    if anomaly_type: params["anomaly_type"] = anomaly_type
    if severity: params["severity"] = severity
    
    try:
        resp = httpx.get(f"{API_BASE_URL}/anomalies", params=params, timeout=5.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    
    from app.services.anomaly_service import anomaly_service
    a_resp = anomaly_service.detect_anomalies(anomaly_type_filter=anomaly_type, severity_filter=severity)
    return a_resp.model_dump()

@st.cache_data(ttl=5)
def fetch_tickets(category=None, priority=None, status_val=None, search=None):
    params = {}
    if category and category != "All": params["category"] = category
    if priority and priority != "All": params["priority"] = priority
    if status_val and status_val != "All": params["status"] = status_val
    if search: params["search"] = search
    
    try:
        resp = httpx.get(f"{API_BASE_URL}/tickets", params=params, timeout=5.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    
    # Fallback to local dataframe
    from app.services.data_service import data_service
    df = data_service.get_df().copy()
    if category and category != "All": df = df[df["category"] == category]
    if priority and priority != "All": df = df[df["priority"] == priority]
    if status_val and status_val != "All": df = df[df["status"] == status_val]
    if search:
        s = search.lower().strip()
        df = df[df["issue_summary"].str.lower().str.contains(s, na=False) | df["ticket_id"].str.lower().str.contains(s, na=False)]
    
    recs = []
    for _, row in df.head(100).iterrows():
        recs.append({
            "ticket_id": str(row["ticket_id"]),
            "created_at": row["created_at"].strftime("%Y-%m-%d %H:%M") if pd.notna(row["created_at"]) else None,
            "category": str(row["category"]),
            "priority": str(row["priority"]),
            "status": str(row["status"]),
            "response_time_hrs": float(row["response_time_hrs"]) if pd.notna(row["response_time_hrs"]) else None,
            "resolution_time_hrs": float(row["resolution_time_hrs"]) if pd.notna(row["resolution_time_hrs"]) else None,
            "agent_id": str(row["agent_id"]),
            "customer_rating": float(row["customer_rating"]) if pd.notna(row["customer_rating"]) else None,
            "issue_summary": str(row["issue_summary"])
        })
    return {"total": len(df), "tickets": recs}


# Header Banner
st.markdown("""
<div class="header-banner">
    <h1>SupportIQ 🛡️</h1>
    <p>AI-Powered Customer Support Ticket Analytics & Explainable Anomaly Intelligence</p>
</div>
""", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["📊 Overview", "💬 Ask SupportIQ", "🚨 Anomaly Center", "🔍 Ticket Explorer", "⚙️ System Health"]
)

health_data, is_api_online = fetch_health()
if not is_api_online:
    st.sidebar.warning("⚠️ FastAPI Backend offline. Operating in direct local service mode.")

# PAGE 1: OVERVIEW
if page == "📊 Overview":
    st.title("Executive Dashboard Overview")
    
    summary = fetch_summary()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Tickets", summary.get("total_tickets", 0))
    with col2:
        st.metric("Unresolved Tickets", summary.get("unresolved_tickets", 0))
    with col3:
        st.metric("Critical Unresolved", summary.get("critical_unresolved_tickets", 0))
    with col4:
        st.metric("Avg Customer Rating", f"{summary.get('avg_customer_rating', 0.0)} / 5.0")

    st.markdown("---")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("Tickets by Status")
        status_counts = summary.get("status_counts", {})
        if status_counts:
            df_status = pd.DataFrame(list(status_counts.items()), columns=["Status", "Count"])
            fig_status = px.pie(
                df_status, names="Status", values="Count", hole=0.4,
                color="Status",
                color_discrete_map={"Resolved": "#22c55e", "Open": "#3b82f6", "Escalated": "#ef4444"}
            )
            st.plotly_chart(fig_status, use_container_width=True)
            
    with chart_col2:
        st.subheader("Tickets by Priority")
        priority_counts = summary.get("priority_counts", {})
        if priority_counts:
            df_prio = pd.DataFrame(list(priority_counts.items()), columns=["Priority", "Count"])
            fig_prio = px.bar(
                df_prio, x="Priority", y="Count", color="Priority",
                color_discrete_map={"Low": "#94a3b8", "Medium": "#f59e0b", "High": "#f97316", "Critical": "#dc2626"}
            )
            st.plotly_chart(fig_prio, use_container_width=True)

    chart_col3, chart_col4 = st.columns(2)
    with chart_col3:
        st.subheader("Tickets by Category")
        cat_counts = summary.get("category_counts", {})
        if cat_counts:
            df_cat = pd.DataFrame(list(cat_counts.items()), columns=["Category", "Count"])
            fig_cat = px.bar(df_cat, x="Category", y="Count", color="Category", color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_cat, use_container_width=True)
            
    with chart_col4:
        st.subheader("Performance Indicators")
        st.write(f"• **Avg Response Time**: {summary.get('avg_response_time_hrs')} hours")
        st.write(f"• **Avg Resolution Time**: {summary.get('avg_resolution_time_hrs')} hours")
        st.write(f"• **Customer Satisfaction Score**: {summary.get('avg_customer_rating')} / 5.0")
        
        anom_data = fetch_anomalies()
        st.write(f"• **Total Flagged Anomalies**: {anom_data.get('total_anomalies', 0)}")


# PAGE 2: ASK SUPPORTIQ
elif page == "💬 Ask SupportIQ":
    st.title("Natural Language Ticket Analytics")
    st.write("Ask natural language questions about customer support tickets. Groq converts your question into a validated query plan, and Python calculates deterministic results.")
    
    st.subheader("Recommended Sample Queries")
    sample_queries = [
        "How many tickets are currently open?",
        "How many critical tickets are unresolved?",
        "What is the average customer rating for Technical tickets?",
        "Which agent resolved the most tickets?",
        "Show Critical tickets not resolved within 12 hours.",
        "What are the top three categories by ticket volume?",
        "Are there anomalies in resolution times?"
    ]
    
    selected_sample = None
    cols = st.columns(3)
    for i, q in enumerate(sample_queries):
        if cols[i % 3].button(q, key=f"sample_{i}"):
            selected_sample = q
            
    question_input = st.text_input("Enter your question:", value=selected_sample or "", placeholder="e.g. What is the average rating for Billing tickets?")
    
    if st.button("Ask SupportIQ 🚀", type="primary") and question_input.strip():
        with st.spinner("Analyzing question with Groq LLM & Pandas..."):
            res = post_query(question_input.strip())
            
            st.markdown("### Answer")
            st.markdown(f"""
            <div class="answer-card">
                <div class="answer-text">{res.get('answer')}</div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("🛠️ View LLM Query Plan & Schema Validation", expanded=False):
                st.json(res.get("query_plan", {}))
                
            evidence = res.get("evidence", [])
            if evidence:
                st.subheader(f"📋 Supporting Evidence Records ({len(evidence)} returned)")
                st.dataframe(pd.DataFrame(evidence), use_container_width=True)


# PAGE 3: ANOMALY CENTER
elif page == "🚨 Anomaly Center":
    st.title("Explainable Anomaly Detection Center")
    st.write("Rule-based business anomalies and statistical IQR outliers flagged for human review.")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        sev_filter = st.selectbox("Filter by Severity", ["All", "critical", "high", "medium", "low"])
    with col_f2:
        type_filter = st.selectbox(
            "Filter by Anomaly Type",
            ["All", "critical_unresolved", "aging_unresolved", "resolution_time_outlier", "low_customer_rating", "slow_first_response"]
        )
        
    s_val = None if sev_filter == "All" else sev_filter
    t_val = None if type_filter == "All" else type_filter
    
    anom_res = fetch_anomalies(anomaly_type=t_val, severity=s_val)
    anomalies = anom_res.get("anomalies", [])
    
    st.metric("Flagged Anomalies Count", anom_res.get("total_anomalies", 0))
    
    if anomalies:
        df_anom = pd.DataFrame(anomalies)
        st.dataframe(
            df_anom[["ticket_id", "severity", "anomaly_type", "reason", "detected_value", "threshold"]],
            use_container_width=True
        )
    else:
        st.success("No anomalies found matching the selected filter criteria.")


# PAGE 4: TICKET EXPLORER
elif page == "🔍 Ticket Explorer":
    st.title("Support Ticket Explorer")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        cat = st.selectbox("Category", ["All", "Billing", "Technical", "General"])
    with c2:
        prio = st.selectbox("Priority", ["All", "Low", "Medium", "High", "Critical"])
    with c3:
        stat_val = st.selectbox("Status", ["All", "Open", "Resolved", "Escalated"])
    with c4:
        search_query = st.text_input("Search issue / ticket ID", "")
        
    tickets_data = fetch_tickets(category=cat, priority=prio, status_val=stat_val, search=search_query)
    tickets = tickets_data.get("tickets", [])
    
    st.write(f"Showing **{len(tickets)}** of **{tickets_data.get('total', 0)}** matching tickets")
    
    if tickets:
        st.dataframe(pd.DataFrame(tickets), use_container_width=True)
    else:
        st.info("No tickets found matching your search parameters.")


# PAGE 5: SYSTEM HEALTH
elif page == "⚙️ System Health":
    st.title("System Health & Diagnostic Status")
    
    st.json(health_data)
    
    st.markdown("### Configuration Details")
    st.write(f"• **Backend API Base URL**: `{API_BASE_URL}`")
    st.write(f"• **Dataset Path**: `{health_data.get('dataset_path')}`")
    st.write(f"• **Row Count**: `{health_data.get('row_count')}`")
    st.write(f"• **Groq Configured**: `{health_data.get('groq_configured')}`")
    st.write(f"• **Groq Model**: `{health_data.get('groq_model')}`")
