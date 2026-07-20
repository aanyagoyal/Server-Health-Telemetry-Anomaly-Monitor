import html
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data.telemetry_generator import generate_server_stream
from src.diagnostics import RootCauseDiagnostic
from src.itsm_export import ITSMExporter
from src.model import AnomalyEngine, ModelBenchmark


# ----------------------------------------------------------------------
# Page setup
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="NexGuard | Intelligent Server Monitoring",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ----------------------------------------------------------------------
# Design system
# ----------------------------------------------------------------------
st.markdown(
    """
<style>
:root {
    --bg: #070b14;
    --panel: #0d1422;
    --panel-2: #101a2b;
    --border: #1d2a3d;
    --border-soft: #172337;
    --text: #f8fafc;
    --muted: #8291a8;
    --muted-2: #5d6b80;
    --blue: #4f8cff;
    --cyan: #22d3ee;
    --green: #34d399;
    --amber: #fbbf24;
    --red: #fb7185;
}

.stApp {
    background:
        radial-gradient(circle at 85% 0%, rgba(37, 99, 235, .10), transparent 28%),
        radial-gradient(circle at 15% 20%, rgba(34, 211, 238, .045), transparent 25%),
        var(--bg);
    color: var(--text);
}

.main .block-container {
    max-width: 1540px;
    padding: 1.25rem 2rem 2.5rem;
}

#MainMenu, footer { visibility: hidden; }

[data-testid="stSidebar"] {
    background: #080e19;
    border-right: 1px solid var(--border-soft);
}

[data-testid="stSidebar"] .block-container {
    padding: 1.2rem 1rem 1.5rem;
}

/* ---------- Brand ---------- */
.brand-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
    margin: 4px 0 18px;
}
.brand-left { display:flex; align-items:center; gap:13px; }
.brand-mark {
    width: 44px; height:44px; border-radius:13px;
    display:flex; align-items:center; justify-content:center;
    background: linear-gradient(145deg, #2563eb, #4f46e5);
    box-shadow: 0 10px 30px rgba(37,99,235,.22);
    font-size: 22px;
}
.brand-name { font-size: 25px; font-weight: 800; letter-spacing:-.7px; }
.brand-sub { color:var(--muted); font-size:12px; margin-top:2px; }

.live-pill {
    display:inline-flex; align-items:center; gap:7px;
    padding:7px 11px; border-radius:999px;
    background:rgba(52,211,153,.08);
    border:1px solid rgba(52,211,153,.20);
    color:#9ce7c7; font-size:11px; font-weight:700;
    letter-spacing:.4px;
}
.live-dot { width:7px; height:7px; border-radius:50%; background:#34d399; box-shadow:0 0 0 4px rgba(52,211,153,.10); }

/* ---------- Hero ---------- */
.hero {
    position:relative; overflow:hidden;
    border:1px solid var(--border);
    background:linear-gradient(135deg, rgba(15,28,48,.96), rgba(10,18,31,.98));
    border-radius:18px;
    padding:20px 22px;
    margin-bottom:17px;
}
.hero:after {
    content:""; position:absolute; width:240px; height:240px; right:-80px; top:-110px;
    border-radius:50%; background:rgba(79,140,255,.10); filter:blur(10px);
}
.hero-kicker { color:#79a7ff; font-size:10px; font-weight:800; letter-spacing:1.4px; text-transform:uppercase; }
.hero-title { font-size:26px; font-weight:800; margin-top:5px; letter-spacing:-.6px; }
.hero-copy { color:var(--muted); font-size:12px; margin-top:5px; max-width:720px; }
.hero-meta { color:#607087; font-size:11px; margin-top:13px; }

/* ---------- Status ---------- */
.status-bar {
    display:flex; align-items:center; justify-content:space-between; gap:15px;
    padding:11px 14px; border-radius:12px;
    background:rgba(13,20,34,.85); border:1px solid var(--border);
    margin-bottom:18px;
}
.status-left { display:flex; align-items:center; gap:9px; }
.status-dot { width:9px; height:9px; border-radius:50%; }
.status-main { font-size:13px; font-weight:750; }
.status-detail { color:var(--muted-2); font-size:11px; }

/* ---------- KPI cards ---------- */
.kpi {
    background:linear-gradient(145deg, #0e1727, #0b1320);
    border:1px solid var(--border);
    border-radius:14px;
    padding:14px 15px;
    min-height:116px;
    box-shadow:0 8px 30px rgba(0,0,0,.10);
}
.kpi-top { display:flex; align-items:center; justify-content:space-between; }
.kpi-label { color:#8b9ab0; font-size:10px; font-weight:800; letter-spacing:.8px; }
.kpi-icon { color:#63748d; font-size:14px; }
.kpi-value { font-size:25px; font-weight:800; letter-spacing:-.7px; margin-top:12px; }
.kpi-sub { color:#5f6f85; font-size:10px; margin-top:5px; }
.kpi-accent { color:#8ab2ff; }
.kpi-good { color:#62d9ae; }
.kpi-warn { color:#f8c85d; }
.kpi-bad { color:#ff8495; }

/* ---------- Section headers ---------- */
.section-head { display:flex; align-items:end; justify-content:space-between; margin:22px 0 10px; }
.section-title { font-size:14px; font-weight:800; letter-spacing:-.1px; }
.section-caption { color:var(--muted-2); font-size:10px; margin-top:3px; }
.section-tag { color:#71829a; font-size:10px; }

/* ---------- Panels ---------- */
.panel {
    background:var(--panel);
    border:1px solid var(--border);
    border-radius:14px;
    padding:15px;
}
.panel-title { font-size:12px; font-weight:750; }
.panel-muted { color:var(--muted); font-size:11px; line-height:1.65; }

/* ---------- Incident cards ---------- */
.incident-card {
    background:#0c1421; border:1px solid var(--border); border-radius:12px;
    padding:13px 14px; margin-bottom:9px;
}
.incident-row { display:flex; align-items:center; justify-content:space-between; gap:10px; }
.incident-name { font-size:12px; font-weight:750; }
.incident-time { color:#5f6f85; font-size:10px; }
.badge { display:inline-block; padding:4px 7px; border-radius:999px; font-size:9px; font-weight:800; letter-spacing:.4px; }
.badge-red { color:#ff9aaa; background:rgba(251,113,133,.09); border:1px solid rgba(251,113,133,.16); }
.badge-amber { color:#ffd978; background:rgba(251,191,36,.08); border:1px solid rgba(251,191,36,.15); }
.badge-green { color:#79e5ba; background:rgba(52,211,153,.08); border:1px solid rgba(52,211,153,.15); }
.incident-cause { color:#8b9ab0; font-size:10px; margin-top:7px; }

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"] {
    gap:4px; padding:4px; border-radius:12px;
    background:#0b1320; border:1px solid var(--border);
}
.stTabs [data-baseweb="tab"] {
    height:35px; padding:0 14px; color:#7e8da3; border-radius:8px;
    font-size:11px; font-weight:650;
}
.stTabs [aria-selected="true"] { color:#fff !important; background:#172337; }
.stTabs [data-baseweb="tab-highlight"] { background:#4f8cff; }

/* ---------- Buttons / inputs ---------- */
.stButton > button, .stDownloadButton > button {
    border-radius:9px !important; border:1px solid #26364d !important;
    background:#111c2c !important; color:#dce6f4 !important;
    font-size:11px !important; font-weight:650 !important;
}
.stButton > button:hover, .stDownloadButton > button:hover { border-color:#4169a8 !important; }
[data-testid="stSidebar"] .stSlider label, [data-testid="stSidebar"] .stCheckbox label { color:#9aa9bd !important; font-size:11px !important; }

/* ---------- Dataframes ---------- */
[data-testid="stDataFrame"] { border:1px solid var(--border); border-radius:11px; overflow:hidden; }

/* ---------- Footer ---------- */
.project-footer { text-align:center; color:#3f4c60; font-size:10px; padding:25px 0 5px; }

/* ---------- Login ---------- */
.login-wrap { max-width:430px; margin:8vh auto 0; }
.login-brand { text-align:center; margin-bottom:22px; }
.login-logo {
    width:56px; height:56px; margin:0 auto 12px; border-radius:16px;
    display:flex; align-items:center; justify-content:center; font-size:27px;
    background:linear-gradient(145deg,#2563eb,#4f46e5);
    box-shadow:0 14px 45px rgba(37,99,235,.22);
}
.login-title { font-size:29px; font-weight:850; letter-spacing:-.8px; }
.login-sub { color:#708096; font-size:12px; margin-top:4px; }
.login-card { padding:22px; border:1px solid var(--border); background:#0d1422; border-radius:16px; }
.login-note { text-align:center; color:#5f6f85; font-size:10px; margin-top:14px; line-height:1.6; }

@media (max-width: 900px) {
    .main .block-container { padding:1rem; }
    .brand-row { align-items:flex-start; }
    .live-pill { display:none; }
}
</style>
""",
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------
# Demo login
# ----------------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "users" not in st.session_state:
    st.session_state.users = {
        "admin": {"password": "nexguard", "email": "admin@nexguard.local"}
    }


if not st.session_state.authenticated:
    st.markdown(
        """
        <div class="login-wrap">
            <div class="login-brand">
                <div class="login-logo">🛡️</div>
                <div class="login-title">NexGuard</div>
                <div class="login-sub">Intelligent Server Monitoring & Anomaly Detection</div>
            </div>
            <div class="login-card">
        """,
        unsafe_allow_html=True,
    )

    login_tab, create_tab = st.tabs(["Sign in", "Create account"])

    with login_tab:
        with st.form("nexguard_login", clear_on_submit=False):
            username = st.text_input("Username / Email", placeholder="Enter username or email")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            remember = st.checkbox("Remember me")
            submitted = st.form_submit_button("Sign in", use_container_width=True, type="primary")

        if submitted:
            key = username.strip().lower()
            matched_user = st.session_state.users.get(key)
            if matched_user is None:
                for user_key, details in st.session_state.users.items():
                    if details["email"].lower() == key:
                        matched_user = details
                        key = user_key
                        break
            if matched_user and password == matched_user["password"]:
                st.session_state.authenticated = True
                st.session_state.username = key
                st.rerun()
            else:
                st.error("Incorrect username/email or password.")

    with create_tab:
        with st.form("nexguard_create_account", clear_on_submit=False):
            new_name = st.text_input("Username", placeholder="Choose a username")
            new_email = st.text_input("Email", placeholder="you@example.com")
            new_password = st.text_input("Password", type="password", placeholder="Create a password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password")
            create_submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")

        if create_submitted:
            clean_name = new_name.strip().lower()
            clean_email = new_email.strip().lower()
            if not clean_name or not clean_email or not new_password:
                st.warning("Please fill in all fields.")
            elif len(clean_name) < 3:
                st.warning("Username must contain at least 3 characters.")
            elif "@" not in clean_email:
                st.warning("Please enter a valid email address.")
            elif new_password != confirm_password:
                st.warning("Passwords do not match.")
            elif clean_name in st.session_state.users:
                st.warning("That username already exists.")
            elif any(d["email"].lower() == clean_email for d in st.session_state.users.values()):
                st.warning("That email is already registered.")
            else:
                st.session_state.users[clean_name] = {"password": new_password, "email": clean_email}
                st.success("Account created successfully. You can now log in.")

    st.markdown(
        """
            </div>
            <div class="login-note">
                Demo account: <strong>admin</strong> / <strong>nexguard</strong><br>
                Local project authentication for demonstration purposes.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()


# ----------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="brand-left" style="margin-bottom:10px;">
            <div class="brand-mark" style="width:38px;height:38px;font-size:18px;">🛡️</div>
            <div>
                <div style="font-size:18px;font-weight:800;">NexGuard</div>
                <div class="brand-sub">Infrastructure Intelligence</div>
            </div>
        </div>
        <div class="live-pill"><span class="live-dot"></span> MONITORING ACTIVE</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    st.markdown("**MONITORING CONTROLS**")

    sample_count = st.slider("Monitor Window (Minutes)", 60, 480, 240, step=30)
    has_spikes = st.checkbox("Simulate outage / spikes", value=True)
    sensitivity = st.slider("Anomaly Sensitivity (%)", 1, 10, 4) / 100

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    st.markdown("**SYSTEM**")
    st.markdown(
        """
        <div class="panel" style="padding:11px 12px;">
            <div style="color:#64748b;font-size:9px;letter-spacing:.7px;font-weight:800;">SERVER</div>
            <div style="font-size:12px;font-weight:700;margin-top:4px;">Rack-Server-01</div>
            <div style="color:#66768d;font-size:10px;margin-top:3px;">Edge infrastructure node</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    if st.button("↻  Refresh telemetry", use_container_width=True):
        st.rerun()

    st.markdown("<div style='height:5px'></div>", unsafe_allow_html=True)
    if st.button("Log out", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.rerun()

    st.markdown(
        f"<div style='color:#56667b;font-size:10px;margin-top:12px;'>Signed in as <b>{html.escape(st.session_state.username)}</b></div>",
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------
# Data pipeline — backend unchanged
# ----------------------------------------------------------------------
df = generate_server_stream(sample_count, has_spikes)
engine = AnomalyEngine(contamination=sensitivity)
df = engine.run_detection(df)
df = RootCauseDiagnostic.annotate(df)
incidents = df[df["Is_Incident"]].copy()


# ----------------------------------------------------------------------
# Derived dashboard values
# ----------------------------------------------------------------------
latest = df.iloc[-1]
incident_count = int(df["Is_Incident"].sum())
incident_rate = incident_count / max(len(df), 1)

# Health score is a presentation metric derived from the current incident rate.
health_score = max(0, min(100, int(round(100 - incident_rate * 220))))
if health_score >= 90:
    health_label, health_class = "Healthy", "kpi-good"
elif health_score >= 75:
    health_label, health_class = "Degraded", "kpi-warn"
else:
    health_label, health_class = "Critical", "kpi-bad"

now_text = datetime.now().strftime("%d %b %Y · %I:%M:%S %p")


# ----------------------------------------------------------------------
# Plot helpers
# ----------------------------------------------------------------------
PLOT_BG = "#0d1422"
GRID = "rgba(117,137,165,.10)"


def base_plot(fig, height=280):
    fig.update_layout(
        template="plotly_dark",
        height=height,
        margin=dict(l=8, r=8, t=42, b=10),
        paper_bgcolor=PLOT_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(color="#8291a8", size=10),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.01,
            xanchor="right", x=1, font=dict(size=9),
        ),
        hoverlabel=dict(bgcolor="#111c2c", bordercolor="#26364d", font_size=10),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, showline=False)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, showline=False)
    return fig


def metric_chart(dataframe, incident_df, title, y_col, unit, line_color):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dataframe["Timestamp"], y=dataframe[y_col], mode="lines",
        name="Telemetry", line=dict(color=line_color, width=2),
        hovertemplate=f"%{{x|%H:%M}}<br><b>%{{y:.2f}}</b> {unit}<extra></extra>",
    ))
    if len(incident_df):
        fig.add_trace(go.Scatter(
            x=incident_df["Timestamp"], y=incident_df[y_col], mode="markers",
            name="Anomaly", marker=dict(color="#fb7185", size=7, symbol="circle"),
            hovertemplate=f"Anomaly<br><b>%{{y:.2f}}</b> {unit}<extra></extra>",
        ))
    fig.update_layout(title=dict(text=f"<b>{title}</b>", font=dict(size=13, color="#e6edf7")))
    fig.update_yaxes(title_text=unit)
    return base_plot(fig)


def severity_for_row(row):
    score = 0
    if row["CPU_Load_%"] > 85: score += 2
    elif row["CPU_Load_%"] > 75: score += 1
    if row["Temperature_C"] > 85: score += 2
    elif row["Temperature_C"] > 75: score += 1
    if row["RAM_Usage_%"] > 90: score += 2
    elif row["RAM_Usage_%"] > 80: score += 1
    if row["Network_Latency_ms"] > 180: score += 2
    elif row["Network_Latency_ms"] > 100: score += 1
    if row["Packet_Loss_%"] > 5: score += 2
    elif row["Packet_Loss_%"] > 2: score += 1
    if score >= 4:
        return "CRITICAL", "badge-red"
    if score >= 2:
        return "HIGH", "badge-amber"
    return "MEDIUM", "badge-amber"


# ----------------------------------------------------------------------
# Main header
# ----------------------------------------------------------------------
st.markdown(
    f"""
    <div class="brand-row">
        <div class="brand-left">
            <div class="brand-mark">🛡️</div>
            <div>
                <div class="brand-name">NexGuard</div>
                <div class="brand-sub">Intelligent Server Monitoring & Anomaly Detection</div>
            </div>
        </div>
        <div class="live-pill"><span class="live-dot"></span> LIVE MONITORING</div>
    </div>

    <div class="hero">
        <div class="hero-kicker">Infrastructure Intelligence Platform</div>
        <div class="hero-title">Server health, anomalies and root cause — in one view.</div>
        <div class="hero-copy">NexGuard analyses multi-variate telemetry with unsupervised ML and an explainable diagnostic layer to surface infrastructure anomalies.</div>
        <div class="hero-meta">Rack-Server-01 &nbsp;•&nbsp; Isolation Forest &nbsp;•&nbsp; {sample_count}-minute window &nbsp;•&nbsp; Last refresh {now_text}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

status_color = "#fb7185" if incident_count else "#34d399"
status_text = "ATTENTION REQUIRED" if incident_count else "SYSTEM OPERATIONAL"
st.markdown(
    f"""
    <div class="status-bar">
        <div class="status-left">
            <span class="status-dot" style="background:{status_color};box-shadow:0 0 0 4px {status_color}22;"></span>
            <div><div class="status-main">{status_text}</div><div class="status-detail">{incident_count} anomaly event(s) detected in the current window</div></div>
        </div>
        <div class="status-detail">Sensitivity {sensitivity:.0%} &nbsp;•&nbsp; {len(df):,} telemetry points</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------
# Tabs
# ----------------------------------------------------------------------
tab_overview, tab_incidents, tab_benchmark, tab_trends = st.tabs(
    ["◉  Overview", "⚠  Incidents", "◎  Model Analysis", "⌁  Historical Trends"]
)


# ----------------------------------------------------------------------
# TAB 1: Overview
# ----------------------------------------------------------------------
with tab_overview:
    st.markdown(
        """
        <div class="section-head">
            <div><div class="section-title">Current system state</div><div class="section-caption">Latest values from the active telemetry stream</div></div>
            <div class="section-tag">AUTO-ANALYSED</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    kpis = [
        ("CPU LOAD", f"{latest['CPU_Load_%']:.1f}%", "Current processor utilization", "▣", "kpi-accent"),
        ("MEMORY", f"{latest['RAM_Usage_%']:.1f}%", "Current memory utilization", "◫", "kpi-accent"),
        ("TEMPERATURE", f"{latest['Temperature_C']:.1f}°C", "Server thermal reading", "♨", "kpi-warn" if latest["Temperature_C"] > 75 else "kpi-good"),
        ("LATENCY", f"{latest['Network_Latency_ms']:.1f} ms", "Network response time", "↔", "kpi-bad" if latest["Network_Latency_ms"] > 100 else "kpi-good"),
        ("HEALTH SCORE", f"{health_score}/100", health_label, "♥", health_class),
    ]
    cols = st.columns(5)
    for col, (label, value, sub, icon, cls) in zip(cols, kpis):
        with col:
            st.markdown(
                f"""
                <div class="kpi">
                    <div class="kpi-top"><div class="kpi-label">{label}</div><div class="kpi-icon">{icon}</div></div>
                    <div class="kpi-value {cls}">{value}</div>
                    <div class="kpi-sub">{sub}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        """
        <div class="section-head">
            <div><div class="section-title">Telemetry signals</div><div class="section-caption">Anomalies are highlighted directly on the time series</div></div>
            <div class="section-tag">LIVE STREAM</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(metric_chart(df, incidents, "CPU Load", "CPU_Load_%", "%", "#4f8cff"), use_container_width=True, config={"displayModeBar": False})
    with c2:
        st.plotly_chart(metric_chart(df, incidents, "Server Temperature", "Temperature_C", "°C", "#f59e0b"), use_container_width=True, config={"displayModeBar": False})

    c3, c4 = st.columns(2)
    with c3:
        st.plotly_chart(metric_chart(df, incidents, "RAM Consumption", "RAM_Usage_%", "%", "#a78bfa"), use_container_width=True, config={"displayModeBar": False})
    with c4:
        st.plotly_chart(metric_chart(df, incidents, "Network Latency", "Network_Latency_ms", "ms", "#22d3ee"), use_container_width=True, config={"displayModeBar": False})

    c5, c6 = st.columns(2)
    with c5:
        st.plotly_chart(metric_chart(df, incidents, "Packet Loss", "Packet_Loss_%", "%", "#34d399"), use_container_width=True, config={"displayModeBar": False})
    with c6:
        st.markdown(
            f"""
            <div class="panel" style="min-height:280px;">
                <div class="panel-title">Detection pipeline</div>
                <div class="panel-muted" style="margin-top:6px;">Telemetry moves through the same backend pipeline already present in the project.</div>
                <div style="margin-top:17px;display:grid;gap:9px;">
                    <div style="padding:10px;border:1px solid #1b2a40;border-radius:9px;background:#0b1320;"><span style="color:#79a7ff;font-size:10px;font-weight:800;">01</span> &nbsp; Telemetry generation <span style="float:right;color:#5f6f85;font-size:9px;">{len(df)} points</span></div>
                    <div style="padding:10px;border:1px solid #1b2a40;border-radius:9px;background:#0b1320;"><span style="color:#79a7ff;font-size:10px;font-weight:800;">02</span> &nbsp; Isolation Forest <span style="float:right;color:#ff9aaa;font-size:9px;">{incident_count} flagged</span></div>
                    <div style="padding:10px;border:1px solid #1b2a40;border-radius:9px;background:#0b1320;"><span style="color:#79a7ff;font-size:10px;font-weight:800;">03</span> &nbsp; Root-cause diagnostics <span style="float:right;color:#62d9ae;font-size:9px;">Explainable</span></div>
                    <div style="padding:10px;border:1px solid #1b2a40;border-radius:9px;background:#0b1320;"><span style="color:#79a7ff;font-size:10px;font-weight:800;">04</span> &nbsp; Incident / ITSM output <span style="float:right;color:#8b9ab0;font-size:9px;">Jira + ServiceNow</span></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ----------------------------------------------------------------------
# TAB 2: Incidents
# ----------------------------------------------------------------------
with tab_incidents:
    st.markdown(
        """
        <div class="section-head">
            <div><div class="section-title">Incident center</div><div class="section-caption">Detected anomalies enriched with explainable root-cause diagnostics</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if len(incidents) > 0:
        recent = incidents.tail(8).iloc[::-1]
        for _, row in recent.iterrows():
            severity, badge_class = severity_for_row(row)
            cause = html.escape(str(row["Root_Cause"]))
            ts = pd.to_datetime(row["Timestamp"]).strftime("%d %b · %H:%M:%S")
            st.markdown(
                f"""
                <div class="incident-card">
                    <div class="incident-row">
                        <div><span class="badge {badge_class}">{severity}</span> <span class="incident-name">{cause}</span></div>
                        <div class="incident-time">{ts}</div>
                    </div>
                    <div class="incident-cause">CPU {row['CPU_Load_%']:.1f}% &nbsp;•&nbsp; Temp {row['Temperature_C']:.1f}°C &nbsp;•&nbsp; RAM {row['RAM_Usage_%']:.1f}% &nbsp;•&nbsp; Latency {row['Network_Latency_ms']:.1f} ms &nbsp;•&nbsp; Loss {row['Packet_Loss_%']:.2f}%</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div class='section-head'><div><div class='section-title'>Incident telemetry table</div><div class='section-caption'>Full flagged records for technical inspection</div></div></div>", unsafe_allow_html=True)
        display_incidents = incidents[[
            "Timestamp", "CPU_Load_%", "Temperature_C", "RAM_Usage_%",
            "Network_Latency_ms", "Packet_Loss_%", "Anomaly_Score", "Root_Cause"
        ]].copy()
        st.dataframe(display_incidents, use_container_width=True, hide_index=True)

        st.markdown("<div class='section-head'><div><div class='section-title'>Incident exports</div><div class='section-caption'>Send the current incident set into common ITSM workflows</div></div></div>", unsafe_allow_html=True)
        e1, e2 = st.columns(2)
        with e1:
            jira_csv = ITSMExporter.to_jira_csv(incidents).to_csv(index=False).encode("utf-8")
            st.download_button("↗  Export for Jira · CSV", jira_csv, "nexguard_incidents_jira.csv", "text/csv", use_container_width=True)
        with e2:
            snow_csv = ITSMExporter.to_servicenow_csv(incidents).to_csv(index=False).encode("utf-8")
            st.download_button("↗  Export for ServiceNow · CSV", snow_csv, "nexguard_incidents_servicenow.csv", "text/csv", use_container_width=True)

        cause_counts = incidents["Root_Cause"].value_counts().reset_index()
        cause_counts.columns = ["Root Cause", "Count"]
        fig = go.Figure(go.Bar(
            x=cause_counts["Count"], y=cause_counts["Root Cause"], orientation="h",
            marker_color="#4f8cff", hovertemplate="%{y}<br><b>%{x}</b> incidents<extra></extra>"
        ))
        fig.update_layout(title=dict(text="<b>Root-cause distribution</b>", font=dict(size=13, color="#e6edf7")))
        fig.update_xaxes(title="Incidents")
        fig = base_plot(fig, 300)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.markdown(
            """
            <div class="panel" style="text-align:center;padding:45px 20px;">
                <div style="font-size:28px;">✓</div>
                <div style="font-size:15px;font-weight:800;margin-top:8px;">No active incidents</div>
                <div class="panel-muted" style="margin-top:5px;">All monitored signals are within the current anomaly threshold.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ----------------------------------------------------------------------
# TAB 3: Model benchmark
# ----------------------------------------------------------------------
with tab_benchmark:
    st.markdown(
        """
        <div class="section-head">
            <div><div class="section-title">Multi-model anomaly analysis</div><div class="section-caption">Isolation Forest, LOF and One-Class SVM evaluated on the same telemetry</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    benchmark = ModelBenchmark(contamination=sensitivity)
    benchmark_df, summary_df = benchmark.run(df)

    bcols = st.columns(3)
    for col, (_, row) in zip(bcols, summary_df.iterrows()):
        with col:
            model_name = html.escape(str(row["Model"]))
            st.markdown(
                f"""
                <div class="kpi" style="min-height:126px;">
                    <div class="kpi-label">{model_name}</div>
                    <div class="kpi-value kpi-accent">{int(row['Anomalies Flagged'])}</div>
                    <div class="kpi-sub">{row['% of Records']:.2f}% flagged &nbsp;•&nbsp; {row['Runtime (ms)']:.2f} ms</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div class='section-head'><div><div class='section-title'>Benchmark matrix</div><div class='section-caption'>Raw comparison returned by the existing ModelBenchmark class</div></div></div>", unsafe_allow_html=True)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    agreement_counts = benchmark_df["Model_Agreement_Count"].value_counts().sort_index()
    fig_agreement = go.Figure(go.Bar(
        x=[str(x) + "/3" for x in agreement_counts.index], y=agreement_counts.values,
        marker_color="#22d3ee", hovertemplate="Agreement %{x}<br><b>%{y}</b> records<extra></extra>"
    ))
    fig_agreement.update_layout(title=dict(text="<b>Model agreement across telemetry</b>", font=dict(size=13, color="#e6edf7")))
    fig_agreement.update_xaxes(title="Models flagging the same record")
    fig_agreement.update_yaxes(title="Records")
    st.plotly_chart(base_plot(fig_agreement, 280), use_container_width=True, config={"displayModeBar": False})

    agreement_view = benchmark_df[benchmark_df["Model_Agreement_Count"] > 0][
        ["Timestamp", "Model_Agreement_Count", "Root_Cause"]
    ].sort_values("Model_Agreement_Count", ascending=False)

    st.markdown("<div class='section-head'><div><div class='section-title'>Flagged agreement records</div><div class='section-caption'>Rows where one or more models identify an anomaly</div></div></div>", unsafe_allow_html=True)
    if len(agreement_view):
        st.dataframe(agreement_view, use_container_width=True, hide_index=True)
    else:
        st.info("No model currently flags anomalies at this sensitivity level.")


# ----------------------------------------------------------------------
# TAB 4: Historical trends
# ----------------------------------------------------------------------
with tab_trends:
    st.markdown(
        """
        <div class="section-head">
            <div><div class="section-title">Historical telemetry trends</div><div class="section-caption">Rolling averages reveal gradual drift beyond single-point anomalies</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    rolling_window = max(5, sample_count // 20)
    trend_df = df.copy()
    trend_columns = [
        "CPU_Load_%", "Temperature_C", "RAM_Usage_%", "Network_Latency_ms", "Packet_Loss_%"
    ]
    for col in trend_columns:
        trend_df[f"{col}_MA"] = trend_df[col].rolling(window=rolling_window, min_periods=1).mean()

    trend_metrics = [
        ("CPU_Load_%", "CPU Load", "%", "#4f8cff"),
        ("Temperature_C", "Server Temperature", "°C", "#f59e0b"),
        ("RAM_Usage_%", "RAM Consumption", "%", "#a78bfa"),
        ("Network_Latency_ms", "Network Latency", "ms", "#22d3ee"),
        ("Packet_Loss_%", "Packet Loss", "%", "#34d399"),
    ]

    def trend_chart(metric_col, title, unit, color):
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trend_df["Timestamp"], y=trend_df[metric_col], name="Raw",
            line=dict(color=color, width=1), opacity=.28,
            hovertemplate=f"%{{x|%H:%M}}<br>Raw <b>%{{y:.2f}}</b> {unit}<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=trend_df["Timestamp"], y=trend_df[f"{metric_col}_MA"],
            name=f"{rolling_window}-min avg", line=dict(color=color, width=3),
            hovertemplate=f"%{{x|%H:%M}}<br>Avg <b>%{{y:.2f}}</b> {unit}<extra></extra>",
        ))
        fig.update_layout(title=dict(text=f"<b>{title}</b>", font=dict(size=13, color="#e6edf7")))
        fig.update_yaxes(title=unit)
        return base_plot(fig, 275)

    for i in range(0, len(trend_metrics), 2):
        cols = st.columns(2)
        for widget, metric in zip(cols, trend_metrics[i:i+2]):
            with widget:
                st.plotly_chart(trend_chart(*metric), use_container_width=True, config={"displayModeBar": False})

    st.markdown("<div class='section-head'><div><div class='section-title'>Summary statistics</div><div class='section-caption'>Distribution of the current telemetry window</div></div></div>", unsafe_allow_html=True)
    st.dataframe(df[trend_columns].describe().round(2), use_container_width=True)


# ----------------------------------------------------------------------
# Footer
# ----------------------------------------------------------------------
st.markdown(
    "<div class='project-footer'>NexGuard · Intelligent Server Monitoring & Anomaly Detection · Data Science Internship Project</div>",
    unsafe_allow_html=True,
)
