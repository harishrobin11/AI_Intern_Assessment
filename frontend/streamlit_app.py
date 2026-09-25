"""
SupportIQ — Premium AI Customer Support Intelligence Platform
Frontend Dashboard (Streamlit)
"""

import os
import sys
import json
import math
import html
import textwrap
import httpx
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime

# ---------------------------------------------------------------------------
# Path & Page Config
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

st.set_page_config(
    page_title="SupportIQ — AI Support Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# ---------------------------------------------------------------------------
# DESIGN TOKENS
# ---------------------------------------------------------------------------
COLORS = {
    "bg_main": "#080B12",
    "bg_secondary": "#0D121C",
    "bg_surface": "#111827",
    "bg_card": "#151E2D",
    "bg_card_hover": "#1A2640",
    "border": "rgba(148,163,184,0.08)",
    "border_accent": "rgba(96,165,250,0.18)",
    "text_primary": "#E2E8F0",
    "text_secondary": "#94A3B8",
    "text_muted": "#64748B",
    "accent_cyan": "#38BDF8",
    "accent_blue": "#3B82F6",
    "accent_violet": "#8B5CF6",
    "accent_emerald": "#10B981",
    "accent_amber": "#F59E0B",
    "accent_red": "#EF4444",
    "accent_coral": "#F97316",
}

SEVERITY_COLORS = {
    "critical": "#EF4444",
    "high": "#F97316",
    "medium": "#F59E0B",
    "low": "#38BDF8",
}

STATUS_COLORS = {
    "Resolved": "#10B981",
    "Open": "#3B82F6",
    "Escalated": "#F59E0B",
}

PRIORITY_COLORS = {
    "Low": "#64748B",
    "Medium": "#F59E0B",
    "High": "#F97316",
    "Critical": "#EF4444",
}

# ---------------------------------------------------------------------------
# PLOTLY DARK THEME TEMPLATE
# ---------------------------------------------------------------------------
_GRID = "rgba(148,163,184,0.06)"

def plotly_layout(**overrides):
    """Return a dark-themed Plotly layout dict, deep-merging dict-type keys."""
    # Base defaults for dict-type keys
    bases = {
        "xaxis": dict(gridcolor=_GRID, zerolinecolor=_GRID),
        "yaxis": dict(gridcolor=_GRID, zerolinecolor=_GRID),
        "legend": dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8")),
        "hoverlabel": dict(bgcolor="#1E293B", font_color="#E2E8F0", bordercolor="rgba(148,163,184,0.15)"),
        "font": dict(family="Inter, system-ui, sans-serif", color="#94A3B8", size=12),
        "margin": dict(l=24, r=24, t=40, b=24),
    }
    # Deep-merge any overrides for these dict keys
    for key in list(bases.keys()):
        if key in overrides and isinstance(overrides[key], dict):
            bases[key].update(overrides.pop(key))
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        **bases,
    )
    layout.update(overrides)
    return layout

# ---------------------------------------------------------------------------
# GLOBAL CSS — PREMIUM DARK THEME
# ---------------------------------------------------------------------------
st.markdown(f"""
<style>
/* ─── Google Font + Material Symbols ─── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

/* ─── Root Variables ─── */
:root {{
    --bg-main: {COLORS["bg_main"]};
    --bg-secondary: {COLORS["bg_secondary"]};
    --bg-surface: {COLORS["bg_surface"]};
    --bg-card: {COLORS["bg_card"]};
    --border: {COLORS["border"]};
    --text-primary: {COLORS["text_primary"]};
    --text-secondary: {COLORS["text_secondary"]};
    --accent-cyan: {COLORS["accent_cyan"]};
    --accent-blue: {COLORS["accent_blue"]};
    --accent-violet: {COLORS["accent_violet"]};
    --accent-emerald: {COLORS["accent_emerald"]};
    --accent-amber: {COLORS["accent_amber"]};
    --accent-red: {COLORS["accent_red"]};
}}

/* ─── Global Reset ─── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"],
.main, [data-testid="stMainBlockContainer"] {{
    background-color: var(--bg-main) !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
}}

/* ─── Sidebar ─── */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #0B1120 0%, #080B12 100%) !important;
    border-right: 1px solid rgba(148,163,184,0.06) !important;
}}
section[data-testid="stSidebar"] * {{
    color: #94A3B8 !important;
    font-family: 'Inter', system-ui, sans-serif !important;
}}
section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label {{
    padding: 10px 16px !important;
    border-radius: 10px !important;
    margin-bottom: 4px !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    background: transparent !important;
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
}}
section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label > div:first-child,
section[data-testid="stSidebar"] [data-testid="stRadio"] label input {{
    display: none !important;
    width: 0 !important;
    height: 0 !important;
    opacity: 0 !important;
    visibility: hidden !important;
}}
section[data-testid="stSidebar"] [data-testid="stRadio"] label p,
section[data-testid="stSidebar"] [data-testid="stRadio"] label span {{
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    color: #94A3B8 !important;
    width: 100% !important;
}}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {{
    background: rgba(56,189,248,0.08) !important;
}}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover p,
section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover span {{
    color: #E2E8F0 !important;
}}
section[data-testid="stSidebar"] [data-testid="stRadio"] label[aria-checked="true"],
section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {{
    background: linear-gradient(90deg, rgba(56,189,248,0.16) 0%, rgba(56,189,248,0.03) 100%) !important;
    border-left: 3px solid #38BDF8 !important;
}}
section[data-testid="stSidebar"] [data-testid="stRadio"] label[aria-checked="true"] p,
section[data-testid="stSidebar"] [data-testid="stRadio"] label[aria-checked="true"] span,
section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) p,
section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) span {{
    color: #38BDF8 !important;
    font-weight: 600 !important;
}}

/* ─── Content Container ─── */
.main .block-container {{
    padding: 1.5rem 2rem 3rem 2rem !important;
    max-width: 1440px !important;
}}

/* ─── Headings ─── */
h1, h2, h3, h4, h5, h6, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
    color: #E2E8F0 !important;
    font-family: 'Inter', system-ui, sans-serif !important;
    font-weight: 700 !important;
}}
h1 {{ font-size: 1.75rem !important; letter-spacing: -0.02em; }}
h2 {{ font-size: 1.35rem !important; letter-spacing: -0.01em; }}
h3 {{ font-size: 1.1rem !important; }}
p, span, div, li {{ font-family: 'Inter', system-ui, sans-serif !important; }}

/* ─── Hide Default Streamlit Elements ─── */
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: var(--bg-main) !important; }}

/* ─── Sidebar Collapse / Expand Button Fix ─── */
button[data-testid="stSidebarCollapseButton"],
button[data-testid="collapsedControl"] {{
    background: rgba(21,30,45,0.9) !important;
    border: 1px solid rgba(148,163,184,0.12) !important;
    border-radius: 8px !important;
    width: 32px !important;
    height: 32px !important;
    min-width: 32px !important;
    min-height: 32px !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    overflow: hidden !important;
    transition: all 0.2s ease !important;
    z-index: 999 !important;
}}
button[data-testid="stSidebarCollapseButton"]:hover,
button[data-testid="collapsedControl"]:hover {{
    background: rgba(56,189,248,0.10) !important;
    border-color: rgba(56,189,248,0.30) !important;
    box-shadow: 0 0 12px rgba(56,189,248,0.12) !important;
}}
/* Fix: hide the raw text icon name and replace with a proper symbol */
button[data-testid="stSidebarCollapseButton"] span,
button[data-testid="collapsedControl"] span {{
    font-family: 'Material Symbols Rounded' !important;
    font-size: 20px !important;
    color: #94A3B8 !important;
    -webkit-font-smoothing: antialiased !important;
    font-feature-settings: 'liga' !important;
}}
button[data-testid="stSidebarCollapseButton"]:hover span,
button[data-testid="collapsedControl"]:hover span {{
    color: #E2E8F0 !important;
}}
/* Fallback: if icon font still fails, clip text and show a CSS arrow */
@supports not (font-variation-settings: normal) {{
    button[data-testid="stSidebarCollapseButton"] span,
    button[data-testid="collapsedControl"] span {{
        font-size: 0 !important;
    }}
    button[data-testid="stSidebarCollapseButton"]::after,
    button[data-testid="collapsedControl"]::after {{
        content: '◂' !important;
        font-size: 16px !important;
        color: #94A3B8 !important;
        font-family: 'Inter', system-ui, sans-serif !important;
    }}
}}

/* ─── Metric Cards ─── */
div[data-testid="stMetric"] {{
    background: linear-gradient(135deg, rgba(21,30,45,0.95) 0%, rgba(13,18,28,0.95) 100%);
    border: 1px solid rgba(148,163,184,0.08);
    border-radius: 12px;
    padding: 20px 24px !important;
    transition: all 0.25s ease;
}}
div[data-testid="stMetric"]:hover {{
    border-color: rgba(56,189,248,0.20);
    box-shadow: 0 4px 24px rgba(56,189,248,0.06);
    transform: translateY(-1px);
}}
div[data-testid="stMetricValue"] {{
    font-size: 2rem !important;
    font-weight: 800 !important;
    color: #E2E8F0 !important;
    font-family: 'Inter', system-ui, sans-serif !important;
}}
div[data-testid="stMetricLabel"] {{
    color: #64748B !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}}
div[data-testid="stMetricDelta"] {{
    font-size: 0.8rem !important;
    color: #94A3B8 !important;
}}

/* ─── Buttons ─── */
button[data-testid="stBaseButton-primary"],
.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 28px !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    letter-spacing: 0.01em !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 12px rgba(59,130,246,0.25) !important;
}}
button[data-testid="stBaseButton-primary"]:hover {{
    box-shadow: 0 4px 20px rgba(59,130,246,0.35) !important;
    transform: translateY(-1px) !important;
}}
.stButton > button[kind="secondary"],
button[data-testid="stBaseButton-secondary"] {{
    background: rgba(21,30,45,0.8) !important;
    color: #94A3B8 !important;
    border: 1px solid rgba(148,163,184,0.12) !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    transition: all 0.2s ease !important;
}}
.stButton > button[kind="secondary"]:hover,
button[data-testid="stBaseButton-secondary"]:hover {{
    background: rgba(56,189,248,0.08) !important;
    border-color: rgba(56,189,248,0.25) !important;
    color: #E2E8F0 !important;
}}

/* ─── Inputs & Selectboxes ─── */
input, textarea, [data-testid="stTextInput"] input,
.stTextInput input {{
    background-color: #0D121C !important;
    color: #E2E8F0 !important;
    border: 1px solid rgba(148,163,184,0.12) !important;
    border-radius: 10px !important;
    font-family: 'Inter', system-ui, sans-serif !important;
    font-size: 0.95rem !important;
    padding: 12px 16px !important;
    transition: border-color 0.2s ease !important;
}}
input:focus, textarea:focus, .stTextInput input:focus {{
    border-color: rgba(56,189,248,0.40) !important;
    box-shadow: 0 0 0 3px rgba(56,189,248,0.08) !important;
}}
[data-testid="stSelectbox"] > div > div {{
    background-color: #0D121C !important;
    border: 1px solid rgba(148,163,184,0.12) !important;
    border-radius: 10px !important;
    color: #E2E8F0 !important;
}}

/* ─── Expanders ─── */
details[data-testid="stExpander"] {{
    background: rgba(21,30,45,0.6) !important;
    border: 1px solid rgba(148,163,184,0.08) !important;
    border-radius: 12px !important;
}}
details[data-testid="stExpander"] summary {{
    color: #94A3B8 !important;
    font-weight: 600 !important;
}}
details[data-testid="stExpander"] summary [data-testid="stExpanderToggleIcon"] {{
    font-size: 0 !important;
    width: 18px !important;
    display: inline-block !important;
    visibility: hidden !important;
}}
details[data-testid="stExpander"] summary p,
details[data-testid="stExpander"] summary span {{
    color: #E2E8F0 !important;
    font-size: 0.95rem !important;
}}

/* ─── Dataframes ─── */
[data-testid="stDataFrame"], .stDataFrame {{
    border-radius: 12px !important;
    overflow: hidden !important;
}}

/* ─── Tabs ─── */
button[data-testid="stTab"] {{
    background: transparent !important;
    color: #64748B !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    font-weight: 600 !important;
    padding: 12px 20px !important;
    transition: all 0.2s ease !important;
}}
button[data-testid="stTab"]:hover {{
    color: #E2E8F0 !important;
    background: rgba(56,189,248,0.04) !important;
}}
button[data-testid="stTab"][aria-selected="true"] {{
    color: #38BDF8 !important;
    border-bottom-color: #38BDF8 !important;
}}

/* ─── Card Component ─── */
.sq-card {{
    background: linear-gradient(135deg, rgba(21,30,45,0.85) 0%, rgba(13,18,28,0.90) 100%);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(148,163,184,0.08);
    border-radius: 14px;
    padding: 24px;
    margin-bottom: 16px;
    transition: all 0.25s ease;
    box-sizing: border-box;
}}
.sq-card:hover {{
    border-color: rgba(56,189,248,0.15);
    box-shadow: 0 4px 30px rgba(0,0,0,0.2);
}}
/* Ensure columns holding KPI cards stretch equally */
div[data-testid="stHorizontalBlock"] {{
    align-items: stretch !important;
}}
div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {{
    display: flex !important;
    flex-direction: column !important;
}}
div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] > div {{
    flex: 1 !important;
}}

/* ─── KPI Card ─── */
.kpi-card {{
    background: linear-gradient(135deg, rgba(21,30,45,0.90) 0%, rgba(13,18,28,0.95) 100%);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(148,163,184,0.07);
    border-radius: 14px;
    padding: 20px 16px;
    text-align: center;
    position: relative;
    overflow: hidden;
    min-height: 160px;
    height: 160px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    box-sizing: border-box;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}}
.kpi-card:hover {{
    border-color: rgba(56,189,248,0.18);
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.25);
}}
.kpi-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 14px 14px 0 0;
}}
.kpi-card.accent-cyan::before {{ background: linear-gradient(90deg, transparent, #38BDF8, transparent); }}
.kpi-card.accent-blue::before {{ background: linear-gradient(90deg, transparent, #3B82F6, transparent); }}
.kpi-card.accent-red::before {{ background: linear-gradient(90deg, transparent, #EF4444, transparent); }}
.kpi-card.accent-emerald::before {{ background: linear-gradient(90deg, transparent, #10B981, transparent); }}
.kpi-card.accent-amber::before {{ background: linear-gradient(90deg, transparent, #F59E0B, transparent); }}
.kpi-card.accent-violet::before {{ background: linear-gradient(90deg, transparent, #8B5CF6, transparent); }}

.kpi-icon {{ font-size: 1.3rem; margin-bottom: 4px; opacity: 0.7; flex-shrink: 0; }}
.kpi-value {{ font-size: 1.9rem; font-weight: 800; color: #E2E8F0; line-height: 1.15; margin: 2px 0; white-space: nowrap; flex-shrink: 0; }}
.kpi-label {{ font-size: 0.72rem; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px; flex-shrink: 0; }}
.kpi-context {{ font-size: 0.7rem; color: #475569; margin-top: 2px; flex-shrink: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100%; }}

/* ─── AI Response Card ─── */
.ai-response {{
    background: linear-gradient(135deg, rgba(21,30,45,0.92) 0%, rgba(13,18,28,0.95) 100%);
    border: 1px solid rgba(56,189,248,0.12);
    border-radius: 14px;
    padding: 28px;
    margin: 16px 0;
    position: relative;
    overflow: hidden;
}}
.ai-response::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #3B82F6, #8B5CF6, #38BDF8);
}}
.ai-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.72rem;
    font-weight: 600;
    color: #38BDF8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 12px;
    background: rgba(56,189,248,0.08);
    padding: 4px 12px;
    border-radius: 20px;
}}
.ai-answer-text {{
    font-size: 1.15rem;
    color: #E2E8F0;
    line-height: 1.7;
    margin-bottom: 12px;
}}
.ai-metric {{
    font-size: 2.8rem;
    font-weight: 800;
    color: #38BDF8;
    line-height: 1;
    margin: 8px 0 4px 0;
}}
.ai-metric-label {{
    font-size: 0.82rem;
    color: #64748B;
    font-weight: 500;
}}
.ai-context {{ font-size: 0.82rem; color: #475569; margin-top: 8px; }}

/* ─── Severity Badges ─── */
.sev-badge {{
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}}
.sev-critical {{ background: rgba(239,68,68,0.12); color: #FCA5A5; }}
.sev-high {{ background: rgba(249,115,22,0.12); color: #FDBA74; }}
.sev-medium {{ background: rgba(245,158,11,0.12); color: #FCD34D; }}
.sev-low {{ background: rgba(56,189,248,0.12); color: #7DD3FC; }}

/* ─── Status Badges ─── */
.status-badge {{
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}}
.status-resolved {{ background: rgba(16,185,129,0.12); color: #6EE7B7; }}
.status-open {{ background: rgba(59,130,246,0.12); color: #93C5FD; }}
.status-escalated {{ background: rgba(245,158,11,0.12); color: #FCD34D; }}

/* ─── Query Suggestion Chips ─── */
.query-chip {{
    display: inline-block;
    background: rgba(21,30,45,0.8);
    border: 1px solid rgba(148,163,184,0.10);
    border-radius: 10px;
    padding: 10px 16px;
    font-size: 0.85rem;
    color: #94A3B8;
    cursor: pointer;
    transition: all 0.2s ease;
    margin: 4px;
}}
.query-chip:hover {{
    border-color: rgba(56,189,248,0.25);
    color: #E2E8F0;
    background: rgba(56,189,248,0.06);
}}

/* ─── Page Header ─── */
.page-header {{
    margin-bottom: 28px;
    padding-bottom: 20px;
    border-bottom: 1px solid rgba(148,163,184,0.06);
}}
.page-header h1 {{
    font-size: 1.65rem !important;
    font-weight: 700 !important;
    margin-bottom: 4px !important;
}}
.page-subtitle {{
    color: #64748B;
    font-size: 0.92rem;
    margin: 0;
    line-height: 1.5;
}}

/* ─── Section Header ─── */
.section-header {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 28px 0 16px 0;
    color: #94A3B8;
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}}
.section-header::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: rgba(148,163,184,0.08);
}}

/* ─── Health Indicators ─── */
.health-dot {{
    display: inline-block;
    width: 8px; height: 8px;
    border-radius: 50%;
    margin-right: 6px;
    vertical-align: middle;
}}
.health-dot.healthy {{ background: #10B981; box-shadow: 0 0 6px rgba(16,185,129,0.4); }}
.health-dot.unhealthy {{ background: #EF4444; box-shadow: 0 0 6px rgba(239,68,68,0.4); }}

/* ─── Sidebar Brand ─── */
.sidebar-brand {{
    padding: 20px 16px 24px 16px;
    border-bottom: 1px solid rgba(148,163,184,0.06);
    margin-bottom: 16px;
}}
.sidebar-brand-name {{
    font-size: 1.2rem;
    font-weight: 800;
    color: #E2E8F0 !important;
    letter-spacing: -0.02em;
}}
.sidebar-brand-tag {{
    font-size: 0.7rem;
    color: #475569 !important;
    font-weight: 500;
    letter-spacing: 0.02em;
    margin-top: 2px;
}}

/* ─── Anomaly Explanation ─── */
.anomaly-explain {{
    background: rgba(21,30,45,0.6);
    border-left: 3px solid rgba(245,158,11,0.5);
    border-radius: 0 10px 10px 0;
    padding: 14px 18px;
    margin: 8px 0;
    font-size: 0.88rem;
    color: #94A3B8;
}}

/* ─── Empty State ─── */
.empty-state {{
    text-align: center;
    padding: 48px 24px;
    color: #475569;
}}
.empty-state-icon {{ font-size: 2.5rem; margin-bottom: 12px; opacity: 0.5; }}
.empty-state-text {{ font-size: 0.95rem; }}

/* ─── Divider ─── */
hr {{ border-color: rgba(148,163,184,0.06) !important; }}

/* ─── Scrollbar ─── */
::-webkit-scrollbar {{ width: 6px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: rgba(148,163,184,0.15); border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: rgba(148,163,184,0.25); }}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# API HELPER FUNCTIONS (preserved from original)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=10)
def fetch_health():
    try:
        resp = httpx.get(f"{API_BASE_URL}/health", timeout=3.0)
        if resp.status_code == 200:
            return resp.json(), True
    except Exception:
        pass
    try:
        from app.services.data_service import data_service
        from app.config import settings
        h = data_service.get_health_status()
        h["groq_configured"] = bool(settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("replace_with"))
        h["groq_model"] = settings.GROQ_MODEL
        return h, False
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, False


@st.cache_data(ttl=10)
def fetch_summary():
    try:
        resp = httpx.get(f"{API_BASE_URL}/summary", timeout=3.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    from app.services.data_service import data_service
    return data_service.get_summary_stats()


def post_query(question: str):
    try:
        resp = httpx.post(f"{API_BASE_URL}/query", json={"question": question}, timeout=15.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    from app.services.query_service import query_service
    q_resp = query_service.process_query(question)
    return q_resp.model_dump()


@st.cache_data(ttl=10)
def fetch_anomalies(anomaly_type=None, severity=None):
    params = {}
    if anomaly_type:
        params["anomaly_type"] = anomaly_type
    if severity:
        params["severity"] = severity
    try:
        resp = httpx.get(f"{API_BASE_URL}/anomalies", params=params, timeout=5.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    from app.services.anomaly_service import anomaly_service
    a_resp = anomaly_service.detect_anomalies(anomaly_type_filter=anomaly_type, severity_filter=severity)
    return a_resp.model_dump()


@st.cache_data(ttl=10)
def fetch_tickets(category=None, priority=None, status_val=None, search=None, agent_id=None, limit=100):
    params = {"limit": limit}
    if category and category != "All":
        params["category"] = category
    if priority and priority != "All":
        params["priority"] = priority
    if status_val and status_val != "All":
        params["status"] = status_val
    if search:
        params["search"] = search
    if agent_id and agent_id != "All":
        params["agent_id"] = agent_id
    try:
        resp = httpx.get(f"{API_BASE_URL}/tickets", params=params, timeout=5.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    from app.services.data_service import data_service
    df = data_service.get_df().copy()
    if category and category != "All":
        df = df[df["category"] == category]
    if priority and priority != "All":
        df = df[df["priority"] == priority]
    if status_val and status_val != "All":
        df = df[df["status"] == status_val]
    if agent_id and agent_id != "All":
        df = df[df["agent_id"] == agent_id]
    if search:
        s = search.lower().strip()
        df = df[df["issue_summary"].str.lower().str.contains(s, na=False) | df["ticket_id"].str.lower().str.contains(s, na=False)]
    recs = []
    for _, row in df.head(limit).iterrows():
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
            "issue_summary": str(row["issue_summary"]),
        })
    return {"total": len(df), "tickets": recs}


# ---------------------------------------------------------------------------
# COMPONENT HELPERS
# ---------------------------------------------------------------------------

def render_kpi(icon: str, value, label: str, accent: str = "cyan", context: str = ""):
    st.markdown(f"""
    <div class="kpi-card accent-{accent}">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-context">{context}</div>
    </div>
    """, unsafe_allow_html=True)


def render_page_header(title: str, subtitle: str):
    st.markdown(f"""
    <div class="page-header">
        <h1>{title}</h1>
        <p class="page-subtitle">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def render_section(label: str):
    st.markdown(f'<div class="section-header">{label}</div>', unsafe_allow_html=True)


def severity_badge_html(severity: str) -> str:
    s = severity.lower() if severity else "low"
    return f'<span class="sev-badge sev-{s}">{s}</span>'


def status_badge_html(status: str) -> str:
    s = status.lower() if status else "open"
    return f'<span class="status-badge status-{s}">{s}</span>'


def get_greeting():
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"


# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-brand-name">⚡ SupportIQ</div>
        <div class="sidebar-brand-tag">Intelligence Platform</div>
    </div>
    """, unsafe_allow_html=True)

    health_data, is_api_online = fetch_health()
    api_status = "healthy" if is_api_online else "unhealthy"
    st.markdown(f"""
    <div style="padding: 0 16px 16px 16px; font-size: 0.78rem;">
        <span class="health-dot {api_status}"></span>
        <span style="color: #64748B;">API {'Online' if is_api_online else 'Offline'}</span>
        &nbsp;&nbsp;
        <span class="health-dot {'healthy' if health_data.get('row_count', 0) > 0 else 'unhealthy'}"></span>
        <span style="color: #64748B;">{health_data.get('row_count', 0)} records</span>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        ["📊 Overview", "💬 Ask SupportIQ", "🚨 Anomaly Center", "🔍 Ticket Explorer", "📈 Analytics", "⚙️ System Health"],
        label_visibility="collapsed",
    )


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 1 : OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════
if page == "📊 Overview":
    summary = fetch_summary()

    greeting = get_greeting()
    render_page_header(
        f"{greeting}, SupportIQ",
        "Monitor customer support performance, discover emerging risks, and make data-driven decisions."
    )

    # ── KPI Row ──
    c1, c2, c3, c4, c5 = st.columns(5)
    total = summary.get("total_tickets", 0)
    unresolved = summary.get("unresolved_tickets", 0)
    crit = summary.get("critical_unresolved_tickets", 0)
    avg_res = summary.get("avg_resolution_time_hrs", 0)
    avg_rat = summary.get("avg_customer_rating", 0)

    with c1:
        render_kpi("📋", total, "Total Tickets", "cyan", f"Across all categories")
    with c2:
        render_kpi("⏳", unresolved, "Open / Escalated", "blue", f"{round(unresolved/total*100, 1)}% of total" if total else "")
    with c3:
        render_kpi("🔴", crit, "Critical Unresolved", "red", "Needs immediate attention" if crit > 0 else "All clear")
    with c4:
        render_kpi("⏱️", f"{avg_res}h", "Avg Resolution", "violet", "Based on resolved tickets")
    with c5:
        render_kpi("⭐", f"{avg_rat}", "Customer Rating", "emerald" if avg_rat and avg_rat >= 3.5 else "amber", "Out of 5.0")

    st.markdown("")

    # ── Charts Row 1 ──
    render_section("Distribution Analysis")
    ch1, ch2 = st.columns(2)

    with ch1:
        status_counts = summary.get("status_counts", {})
        if status_counts:
            labels = list(status_counts.keys())
            values = list(status_counts.values())
            colors = [STATUS_COLORS.get(l, "#64748B") for l in labels]
            fig = go.Figure(data=[go.Pie(
                labels=labels, values=values, hole=0.6,
                marker=dict(
                    colors=colors,
                    line=dict(color="#080B12", width=3),
                ),
                textinfo="label+value",
                textfont=dict(size=13, color="#E2E8F0", family="Inter"),
                hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>",
                pull=[0.03] * len(labels),
                rotation=90,
            )])
            fig.update_layout(
                **plotly_layout(
                    title=dict(text="Ticket Volume by Status", font=dict(size=14, color="#E2E8F0"), x=0.01),
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, font=dict(size=12, color="#94A3B8")),
                    annotations=[dict(text=f"<b>{total}</b><br><span style='font-size:11px;color:#64748B'>Total</span>", x=0.5, y=0.5, font_size=24, font_color="#E2E8F0", showarrow=False)],
                    height=380,
                )
            )
            st.plotly_chart(fig, use_container_width=True)

    with ch2:
        priority_counts = summary.get("priority_counts", {})
        if priority_counts:
            order = ["Low", "Medium", "High", "Critical"]
            labels = [p for p in order if p in priority_counts]
            values = [priority_counts[p] for p in labels]
            colors = [PRIORITY_COLORS.get(l, "#64748B") for l in labels]
            fig = go.Figure()
            for i, (lbl, val, clr) in enumerate(zip(labels, values, colors)):
                fig.add_trace(go.Bar(
                    y=[lbl], x=[val], orientation="h", name=lbl,
                    marker=dict(
                        color=clr,
                        line=dict(color=clr, width=1),
                        cornerradius=6,
                        opacity=0.85,
                    ),
                    text=[val], textposition="outside",
                    textfont=dict(color=clr, size=14, family="Inter"),
                    hovertemplate=f"<b>{lbl}</b><br>Count: {val}<extra></extra>",
                    showlegend=False,
                ))
            fig.update_layout(
                **plotly_layout(
                    yaxis=dict(categoryorder="array", categoryarray=list(reversed(order)), gridcolor="rgba(0,0,0,0)"),
                    xaxis=dict(gridcolor="rgba(148,163,184,0.04)", showgrid=True),
                ),
                title=dict(text="Priority Distribution", font=dict(size=14, color="#E2E8F0"), x=0.01),
                height=380, bargap=0.35,
            )
            st.plotly_chart(fig, use_container_width=True)

    # ── Charts Row 2 ──
    ch3, ch4 = st.columns(2)

    with ch3:
        cat_counts = summary.get("category_counts", {})
        if cat_counts:
            labels = list(cat_counts.keys())
            values = list(cat_counts.values())
            cat_colors = ["#3B82F6", "#8B5CF6", "#38BDF8", "#10B981", "#F59E0B"][:len(labels)]
            fig = go.Figure()
            for i, (lbl, val, clr) in enumerate(zip(labels, values, cat_colors)):
                fig.add_trace(go.Bar(
                    x=[lbl], y=[val], name=lbl,
                    marker=dict(color=clr, cornerradius=8, opacity=0.88, line=dict(color=clr, width=1)),
                    text=[val], textposition="outside",
                    textfont=dict(color=clr, size=14, family="Inter"),
                    hovertemplate=f"<b>{lbl}</b><br>Count: {val}<extra></extra>",
                    showlegend=False,
                ))
            fig.update_layout(
                **plotly_layout(),
                title=dict(text="Tickets by Category", font=dict(size=14, color="#E2E8F0"), x=0.01),
                height=380, bargap=0.4,
            )
            st.plotly_chart(fig, use_container_width=True)

    with ch4:
        render_section("Performance Snapshot")
        p1, p2 = st.columns(2)
        with p1:
            render_kpi("🚀", f"{summary.get('avg_response_time_hrs', 'N/A')}h", "Avg Response Time", "cyan")
        with p2:
            anom_data = fetch_anomalies()
            render_kpi("⚠️", anom_data.get('total_anomalies', 0), "Flagged Anomalies", "amber")

    # ── Recent Critical Anomalies ──
    render_section("Recent Critical Alerts")
    crit_anomalies = fetch_anomalies(severity="critical")
    crit_list = crit_anomalies.get("anomalies", [])[:5]
    if crit_list:
        for a in crit_list:
            st.markdown(f"""
            <div class="sq-card" style="padding: 14px 20px; display: flex; align-items: center; gap: 16px;">
                <span class="sev-badge sev-critical">critical</span>
                <span style="color: #E2E8F0; font-weight: 600; font-size: 0.9rem;">{a.get('ticket_id')}</span>
                <span style="color: #64748B; font-size: 0.85rem; flex: 1;">{a.get('reason', '')[:80]}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state"><div class="empty-state-icon">✅</div><div class="empty-state-text">No critical anomalies detected.</div></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 2 : ASK SUPPORTIQ
# ═══════════════════════════════════════════════════════════════════════════
elif page == "💬 Ask SupportIQ":
    render_page_header(
        "Ask your support data anything",
        "Explore ticket trends, operational metrics, and customer experience insights using natural language."
    )

    # ── Suggestion chips ──
    render_section("Suggested Queries")
    sample_queries = [
        "How many tickets are currently open?",
        "How many critical tickets are unresolved?",
        "What is the average customer rating for Technical tickets?",
        "Which agent resolved the most tickets?",
        "Show Critical tickets not resolved within 12 hours.",
        "What are the top three categories by ticket volume?",
        "List unresolved high-priority tickets.",
    ]

    if "active_question" not in st.session_state:
        st.session_state["active_question"] = ""

    cols = st.columns(4)
    for i, q in enumerate(sample_queries):
        if cols[i % 4].button(q, key=f"sq_{i}", use_container_width=True):
            st.session_state["active_question"] = q
            st.rerun()

    st.markdown("")

    # ── Query Input Form ──
    with st.form("query_form", clear_on_submit=False):
        question_input = st.text_input(
            "Your question",
            value=st.session_state["active_question"],
            placeholder="e.g. What is the average customer rating for Technical tickets?",
            label_visibility="collapsed",
        )
        col_btn, _ = st.columns([1, 4])
        with col_btn:
            form_submit = st.form_submit_button("Ask SupportIQ →", type="primary", use_container_width=True)

    if form_submit:
        query_text = question_input.strip()
        if not query_text:
            st.warning("Please enter a question before submitting.")
        else:
            st.session_state["active_question"] = query_text
            with st.spinner("Processing query..."):
                st.markdown(textwrap.dedent(f"""
                <div class="sq-card" style="padding: 14px 20px; margin-bottom: 8px;">
                    <span style="color: #64748B; font-size: 0.78rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em;">Your Question</span>
                    <div style="color: #E2E8F0; font-size: 1.05rem; margin-top: 4px;">{html.escape(query_text)}</div>
                </div>
                """), unsafe_allow_html=True)

                res = post_query(query_text)
                answer = res.get("answer", "No answer available.")
                result_data = res.get("result", {})
                plan = res.get("query_plan", {})
                evidence = res.get("evidence", [])

                value = result_data.get("value")
                record_count = result_data.get("record_count", 0)
                operation = plan.get("operation", "")

                metric_html = ""
                if operation in ["count"] and isinstance(value, (int, float)):
                    metric_html = f'<div class="ai-metric">{int(value)}</div><div class="ai-metric-label">matching tickets</div>'
                elif operation in ["average", "mean"] and isinstance(value, (int, float)):
                    metric_html = f'<div class="ai-metric">{value}</div><div class="ai-metric-label">{plan.get("metric", "metric")}</div>'
                elif operation in ["sum", "min", "max"] and isinstance(value, (int, float)):
                    metric_html = f'<div class="ai-metric">{value}</div><div class="ai-metric-label">{plan.get("metric", "metric")}</div>'

                clean_answer = str(answer).replace("\n", "<br>")

                st.markdown(f"""<div class="ai-response">
<div class="ai-badge">⚡ Computed Analytics Response</div>
{metric_html}
<div class="ai-answer-text">{clean_answer}</div>
<div class="ai-context">Records analyzed: {record_count} · Operation: {operation}</div>
</div>""", unsafe_allow_html=True)

                with st.expander("🔧 Query Plan (LLM → Pydantic Validated JSON)", expanded=False):
                    st.json(plan)

                if evidence:
                    render_section(f"Supporting Evidence ({len(evidence)} records)")
                    df_ev = pd.DataFrame(evidence)
                    st.dataframe(df_ev, use_container_width=True, height=320)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 3 : ANOMALY CENTER
# ═══════════════════════════════════════════════════════════════════════════
elif page == "🚨 Anomaly Center":
    render_page_header(
        "Anomaly Center",
        "Identify unusual patterns, SLA breaches, and tickets requiring operational review."
    )

    # ── Filters ──
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        sev_filter = st.selectbox("Severity", ["All", "critical", "high", "medium", "low"])
    with fc2:
        type_filter = st.selectbox(
            "Anomaly Type",
            ["All", "critical_unresolved", "aging_unresolved", "resolution_time_outlier", "low_customer_rating", "slow_first_response"],
        )
    with fc3:
        st.markdown("<br>", unsafe_allow_html=True)
        refresh = st.button("🔄 Refresh", use_container_width=True)

    s_val = None if sev_filter == "All" else sev_filter
    t_val = None if type_filter == "All" else type_filter

    anom_res = fetch_anomalies(anomaly_type=t_val, severity=s_val)
    anomalies = anom_res.get("anomalies", [])

    # ── Summary KPIs ──
    all_anoms = fetch_anomalies()
    all_list = all_anoms.get("anomalies", [])
    sev_counts = {}
    for a in all_list:
        s = a.get("severity", "low")
        sev_counts[s] = sev_counts.get(s, 0) + 1

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi("⚠️", all_anoms.get("total_anomalies", 0), "Total Anomalies", "amber")
    with k2:
        render_kpi("🔴", sev_counts.get("critical", 0), "Critical", "red")
    with k3:
        render_kpi("🟠", sev_counts.get("high", 0), "High", "coral")
    with k4:
        render_kpi("🟡", sev_counts.get("medium", 0) + sev_counts.get("low", 0), "Medium + Low", "blue")

    st.markdown("")

    # ── Anomaly Table ──
    render_section(f"Anomaly Records ({len(anomalies)} shown)")

    if anomalies:
        df_anom = pd.DataFrame(anomalies)
        if "detected_value" in df_anom.columns:
            df_anom["detected_value"] = df_anom["detected_value"].astype(str)
        if "threshold" in df_anom.columns:
            df_anom["threshold"] = df_anom["threshold"].astype(str)
        display_cols = ["ticket_id", "severity", "anomaly_type", "reason", "detected_value", "threshold"]
        existing_cols = [c for c in display_cols if c in df_anom.columns]
        st.dataframe(df_anom[existing_cols], use_container_width=True, height=460)

        # ── Explanation panel ──
        render_section("Why are these flagged?")
        st.markdown("""
        <div class="anomaly-explain">
            <strong>Rule-based detection:</strong> SupportIQ flags tickets using transparent, configurable business rules.
            Each anomaly includes the specific rule, detected value, and threshold. No opaque ML model — every flag is explainable and auditable.
        </div>
        """, unsafe_allow_html=True)

        rules = [
            ("critical_unresolved", "Critical priority tickets that remain Open or Escalated."),
            ("aging_unresolved", "High/Critical tickets unresolved for more than 24 hours."),
            ("resolution_time_outlier", "Resolution time exceeding Q3 + 1.5×IQR statistical upper bound."),
            ("low_customer_rating", "Resolved tickets with customer rating ≤ 2.0."),
            ("slow_first_response", "First response time exceeding 4.0 hours SLA threshold."),
        ]
        for rule_id, desc in rules:
            st.markdown(f"""
            <div style="padding: 8px 0; border-bottom: 1px solid rgba(148,163,184,0.04); display: flex; gap: 12px; align-items: baseline;">
                <code style="color: #38BDF8; font-size: 0.8rem; background: rgba(56,189,248,0.08); padding: 2px 8px; border-radius: 4px; white-space: nowrap;">{rule_id}</code>
                <span style="color: #94A3B8; font-size: 0.88rem;">{desc}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state"><div class="empty-state-icon">✅</div><div class="empty-state-text">No anomalies match the current filters.</div></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 4 : TICKET EXPLORER
# ═══════════════════════════════════════════════════════════════════════════
elif page == "🔍 Ticket Explorer":
    render_page_header(
        "Ticket Explorer",
        "Search, filter, and inspect individual support ticket records across the entire dataset."
    )

    # ── Filters ──
    f1, f2, f3, f4, f5 = st.columns(5)
    with f1:
        cat = st.selectbox("Category", ["All", "Billing", "Technical", "General"])
    with f2:
        prio = st.selectbox("Priority", ["All", "Low", "Medium", "High", "Critical"])
    with f3:
        stat_val = st.selectbox("Status", ["All", "Open", "Resolved", "Escalated"])
    with f4:
        agent = st.selectbox("Agent", ["All", "AGT-01", "AGT-02", "AGT-03", "AGT-04", "AGT-05", "AGT-06", "AGT-07", "AGT-08", "AGT-09", "AGT-10", "AGT-11", "AGT-12"])
    with f5:
        search_query = st.text_input("Search issue / ticket ID", "", placeholder="e.g. TKT-042 or invoice")

    tickets_data = fetch_tickets(category=cat, priority=prio, status_val=stat_val, search=search_query, agent_id=agent)
    tickets = tickets_data.get("tickets", [])
    total = tickets_data.get("total", 0)

    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin: 8px 0 16px 0;">
        <span style="color: #94A3B8; font-size: 0.88rem;">Showing <strong style="color: #E2E8F0;">{len(tickets)}</strong> of <strong style="color: #E2E8F0;">{total}</strong> tickets</span>
    </div>
    """, unsafe_allow_html=True)

    if tickets:
        df_tickets = pd.DataFrame(tickets)
        st.dataframe(df_tickets, use_container_width=True, height=520)

        # ── Ticket Detail Panel ──
        render_section("Ticket Inspector")
        ticket_ids = [t["ticket_id"] for t in tickets[:50]]
        selected_ticket_id = st.selectbox("Select a ticket to inspect", ticket_ids, index=0)
        selected_ticket = next((t for t in tickets if t["ticket_id"] == selected_ticket_id), None)

        if selected_ticket:
            d1, d2, d3 = st.columns(3)
            with d1:
                st.markdown(f"""
                <div class="sq-card">
                    <div style="font-size: 0.78rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 12px;">Ticket Details</div>
                    <div style="margin-bottom: 8px;"><span style="color: #64748B;">ID:</span> <span style="color: #E2E8F0; font-weight: 600;">{selected_ticket['ticket_id']}</span></div>
                    <div style="margin-bottom: 8px;"><span style="color: #64748B;">Category:</span> <span style="color: #E2E8F0;">{selected_ticket['category']}</span></div>
                    <div style="margin-bottom: 8px;"><span style="color: #64748B;">Priority:</span> <span style="color: #E2E8F0;">{selected_ticket['priority']}</span></div>
                    <div style="margin-bottom: 8px;"><span style="color: #64748B;">Status:</span> {status_badge_html(selected_ticket['status'])}</div>
                    <div><span style="color: #64748B;">Agent:</span> <span style="color: #E2E8F0;">{selected_ticket['agent_id']}</span></div>
                </div>
                """, unsafe_allow_html=True)
            with d2:
                st.markdown(f"""
                <div class="sq-card">
                    <div style="font-size: 0.78rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 12px;">Timing & Rating</div>
                    <div style="margin-bottom: 8px;"><span style="color: #64748B;">Created:</span> <span style="color: #E2E8F0;">{selected_ticket.get('created_at', 'N/A')}</span></div>
                    <div style="margin-bottom: 8px;"><span style="color: #64748B;">Response Time:</span> <span style="color: #E2E8F0;">{selected_ticket.get('response_time_hrs', 'N/A')}h</span></div>
                    <div style="margin-bottom: 8px;"><span style="color: #64748B;">Resolution Time:</span> <span style="color: #E2E8F0;">{selected_ticket.get('resolution_time_hrs') or 'Unresolved'}{'h' if selected_ticket.get('resolution_time_hrs') else ''}</span></div>
                    <div><span style="color: #64748B;">Customer Rating:</span> <span style="color: #E2E8F0;">{selected_ticket.get('customer_rating') or 'N/A'}{'/5' if selected_ticket.get('customer_rating') else ''}</span></div>
                </div>
                """, unsafe_allow_html=True)
            with d3:
                st.markdown(f"""
                <div class="sq-card">
                    <div style="font-size: 0.78rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 12px;">Issue Summary</div>
                    <div style="color: #E2E8F0; font-size: 0.95rem; line-height: 1.6;">{selected_ticket.get('issue_summary', 'No summary available.')}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state"><div class="empty-state-icon">🔍</div><div class="empty-state-text">No tickets match the current filters. Try adjusting your search criteria.</div></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 5 : ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════
elif page == "📈 Analytics":
    render_page_header(
        "Analytics Workspace",
        "Deep-dive into category performance, agent workload, resolution patterns, and customer satisfaction."
    )

    summary = fetch_summary()
    all_tickets = fetch_tickets(limit=500)
    tickets_list = all_tickets.get("tickets", [])
    df = pd.DataFrame(tickets_list) if tickets_list else pd.DataFrame()

    # ── Category Performance ──
    render_section("Category Performance")
    if not df.empty:
        cat_group = df.groupby("category").agg(
            ticket_count=("ticket_id", "count"),
            avg_rating=("customer_rating", lambda x: round(x.dropna().mean(), 2) if x.dropna().any() else None),
            avg_resolution=("resolution_time_hrs", lambda x: round(x.dropna().mean(), 2) if x.dropna().any() else None),
        ).reset_index()

        cc1, cc2 = st.columns(2)
        with cc1:
            cat_colors_r = ["#3B82F6", "#8B5CF6", "#38BDF8"][:len(cat_group)]
            fig = go.Figure()
            for i, row in cat_group.iterrows():
                clr = cat_colors_r[i % len(cat_colors_r)]
                val = row["avg_rating"] if pd.notna(row["avg_rating"]) else 0
                fig.add_trace(go.Bar(
                    x=[row["category"]], y=[val], name=row["category"],
                    marker=dict(color=clr, cornerradius=8, opacity=0.85, line=dict(color=clr, width=1)),
                    text=[f"{val:.2f}" if val else "N/A"], textposition="outside",
                    textfont=dict(color=clr, size=14, family="Inter"),
                    hovertemplate=f"<b>{row['category']}</b><br>Avg Rating: {val}<extra></extra>",
                    showlegend=False,
                ))
            fig.update_layout(**plotly_layout(yaxis=dict(range=[0, 5.5])), title=dict(text="Avg Customer Rating by Category", font=dict(size=14, color="#E2E8F0"), x=0.01), height=380, bargap=0.4)
            st.plotly_chart(fig, use_container_width=True)

        with cc2:
            res_colors = ["#10B981", "#F59E0B", "#EF4444"][:len(cat_group)]
            fig = go.Figure()
            for i, row in cat_group.iterrows():
                clr = res_colors[i % len(res_colors)]
                val = row["avg_resolution"] if pd.notna(row["avg_resolution"]) else 0
                fig.add_trace(go.Bar(
                    x=[row["category"]], y=[val], name=row["category"],
                    marker=dict(color=clr, cornerradius=8, opacity=0.85, line=dict(color=clr, width=1)),
                    text=[f"{val:.1f}h" if val else "N/A"], textposition="outside",
                    textfont=dict(color=clr, size=14, family="Inter"),
                    hovertemplate=f"<b>{row['category']}</b><br>Avg Resolution: {val}h<extra></extra>",
                    showlegend=False,
                ))
            fig.update_layout(**plotly_layout(), title=dict(text="Avg Resolution Time by Category (hours)", font=dict(size=14, color="#E2E8F0"), x=0.01), height=380, bargap=0.4)
            st.plotly_chart(fig, use_container_width=True)

    # ── Agent Workload ──
    render_section("Agent Workload")
    if not df.empty:
        agent_group = df.groupby("agent_id").agg(
            total=("ticket_id", "count"),
            resolved=("status", lambda x: (x == "Resolved").sum()),
        ).reset_index()
        agent_group["resolution_rate"] = (agent_group["resolved"] / agent_group["total"] * 100).round(1)
        agent_group = agent_group.sort_values("total", ascending=False)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Total Assigned", y=agent_group["agent_id"], x=agent_group["total"],
            orientation="h",
            marker=dict(color="rgba(59,130,246,0.25)", cornerradius=6, line=dict(color="rgba(59,130,246,0.6)", width=1)),
            hovertemplate="<b>%{y}</b><br>Total: %{x}<extra></extra>",
        ))
        fig.add_trace(go.Bar(
            name="Resolved", y=agent_group["agent_id"], x=agent_group["resolved"],
            orientation="h",
            marker=dict(color="rgba(16,185,129,0.75)", cornerradius=6, line=dict(color="rgba(16,185,129,0.9)", width=1)),
            text=agent_group.apply(lambda r: f"{r['resolved']}/{r['total']} ({r['resolution_rate']}%)", axis=1),
            textposition="outside",
            textfont=dict(color="#94A3B8", size=11, family="Inter"),
            hovertemplate="<b>%{y}</b><br>Resolved: %{x}<extra></extra>",
        ))
        fig.update_layout(
            **plotly_layout(
                yaxis=dict(gridcolor="rgba(0,0,0,0)"),
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
                barmode="overlay",
                title=dict(text="Agent Ticket Volume & Resolution Rate", font=dict(size=14, color="#E2E8F0"), x=0.01),
                height=420, bargap=0.3,
            )
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Resolution Time Distribution ──
    render_section("Resolution Time Distribution")
    if not df.empty:
        res_times = df["resolution_time_hrs"].dropna()
        if len(res_times) > 0:
            fig = go.Figure(data=[go.Histogram(
                x=res_times, nbinsx=30,
                marker=dict(
                    color="rgba(139,92,246,0.45)",
                    line=dict(color="rgba(139,92,246,0.85)", width=1.5),
                    pattern=dict(shape="", solidity=0.6),
                ),
                hovertemplate="Range: %{x}h<br>Count: %{y}<extra></extra>",
            )])
            q1, q3 = res_times.quantile(0.25), res_times.quantile(0.75)
            iqr = q3 - q1
            upper = q3 + 1.5 * iqr
            median = res_times.median()
            fig.add_vline(x=median, line_dash="dot", line_color="#38BDF8", line_width=2,
                          annotation_text=f"Median: {median:.1f}h", annotation_font_color="#38BDF8",
                          annotation_position="top left")
            fig.add_vline(x=upper, line_dash="dash", line_color="#EF4444", line_width=2,
                          annotation_text=f"Outlier Threshold: {upper:.1f}h", annotation_font_color="#EF4444")
            fig.add_vrect(x0=upper, x1=res_times.max() * 1.05, fillcolor="rgba(239,68,68,0.06)", line_width=0,
                          annotation_text="Anomaly Zone", annotation_position="top right",
                          annotation_font_color="#EF4444", annotation_font_size=10)
            fig.update_layout(**plotly_layout(), title=dict(text="Resolution Time Distribution", font=dict(size=14, color="#E2E8F0"), x=0.01), height=380, xaxis_title="Hours", yaxis_title="Ticket Count")
            st.plotly_chart(fig, use_container_width=True)

    # ── Customer Satisfaction ──
    render_section("Customer Satisfaction")
    if not df.empty:
        ratings = df["customer_rating"].dropna()
        if len(ratings) > 0:
            sr1, sr2 = st.columns(2)
            with sr1:
                rating_dist = ratings.value_counts().sort_index()
                star_colors = ["#EF4444", "#F97316", "#F59E0B", "#38BDF8", "#10B981"]
                fig = go.Figure()
                for i, (r, cnt) in enumerate(zip(rating_dist.index, rating_dist.values)):
                    clr = star_colors[i % len(star_colors)]
                    fig.add_trace(go.Bar(
                        x=[f"{int(r)} ★"], y=[cnt], name=f"{int(r)} Star",
                        marker=dict(color=clr, cornerradius=8, opacity=0.85, line=dict(color=clr, width=1)),
                        text=[cnt], textposition="outside",
                        textfont=dict(color=clr, size=14, family="Inter"),
                        hovertemplate=f"<b>{int(r)} Star</b><br>Count: {cnt}<extra></extra>",
                        showlegend=False,
                    ))
                fig.update_layout(**plotly_layout(), title=dict(text="Rating Distribution", font=dict(size=14, color="#E2E8F0"), x=0.01), height=380, bargap=0.35)
                st.plotly_chart(fig, use_container_width=True)

            with sr2:
                cat_rating = df.groupby("category")["customer_rating"].apply(lambda x: round(x.dropna().mean(), 2)).reset_index()
                cat_rating.columns = ["Category", "Avg Rating"]
                ar_colors = ["#3B82F6", "#8B5CF6", "#38BDF8"][:len(cat_rating)]
                fig = go.Figure()
                for i, row in cat_rating.iterrows():
                    clr = ar_colors[i % len(ar_colors)]
                    fig.add_trace(go.Bar(
                        x=[row["Category"]], y=[row["Avg Rating"]], name=row["Category"],
                        marker=dict(color=clr, cornerradius=8, opacity=0.85, line=dict(color=clr, width=1)),
                        text=[f"{row['Avg Rating']:.2f}"], textposition="outside",
                        textfont=dict(color=clr, size=14, family="Inter"),
                        hovertemplate=f"<b>{row['Category']}</b><br>Avg Rating: {row['Avg Rating']}<extra></extra>",
                        showlegend=False,
                    ))
                fig.update_layout(**plotly_layout(yaxis=dict(range=[0, 5.5])), title=dict(text="Avg Rating by Category", font=dict(size=14, color="#E2E8F0"), x=0.01), height=380, bargap=0.4)
                st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 6 : SYSTEM HEALTH
# ═══════════════════════════════════════════════════════════════════════════
elif page == "⚙️ System Health":
    render_page_header(
        "System Health",
        "Diagnostic overview of API connectivity, dataset status, and LLM provider configuration."
    )

    h1, h2, h3 = st.columns(3)

    api_ok = is_api_online
    ds_ok = health_data.get("row_count", 0) > 0
    llm_ok = health_data.get("groq_configured", False)

    with h1:
        st.markdown(f"""
        <div class="sq-card" style="text-align: center;">
            <div class="health-dot {'healthy' if api_ok else 'unhealthy'}" style="width: 12px; height: 12px; margin: 0 auto 10px auto;"></div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #E2E8F0; margin-bottom: 4px;">{'Online' if api_ok else 'Offline'}</div>
            <div style="font-size: 0.78rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.06em;">FastAPI Backend</div>
            <div style="font-size: 0.82rem; color: #475569; margin-top: 8px;">{API_BASE_URL}</div>
        </div>
        """, unsafe_allow_html=True)
    with h2:
        st.markdown(f"""
        <div class="sq-card" style="text-align: center;">
            <div class="health-dot {'healthy' if ds_ok else 'unhealthy'}" style="width: 12px; height: 12px; margin: 0 auto 10px auto;"></div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #E2E8F0; margin-bottom: 4px;">{'Loaded' if ds_ok else 'Error'}</div>
            <div style="font-size: 0.78rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.06em;">Dataset Status</div>
            <div style="font-size: 0.82rem; color: #475569; margin-top: 8px;">{health_data.get('row_count', 0)} records</div>
        </div>
        """, unsafe_allow_html=True)
    with h3:
        st.markdown(f"""
        <div class="sq-card" style="text-align: center;">
            <div class="health-dot {'healthy' if llm_ok else 'unhealthy'}" style="width: 12px; height: 12px; margin: 0 auto 10px auto;"></div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #E2E8F0; margin-bottom: 4px;">{'Configured' if llm_ok else 'Not Configured'}</div>
            <div style="font-size: 0.78rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.06em;">LLM Provider</div>
            <div style="font-size: 0.82rem; color: #475569; margin-top: 8px;">{health_data.get('groq_model', 'N/A')}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")
    render_section("Configuration")

    st.markdown(f"""
    <div class="sq-card">
        <table style="width: 100%; border-collapse: collapse;">
            <tr style="border-bottom: 1px solid rgba(148,163,184,0.06);">
                <td style="padding: 12px 0; color: #64748B; font-size: 0.88rem; width: 220px;">API Base URL</td>
                <td style="padding: 12px 0; color: #E2E8F0; font-size: 0.88rem;"><code style="background: rgba(56,189,248,0.08); padding: 2px 8px; border-radius: 4px; color: #38BDF8;">{API_BASE_URL}</code></td>
            </tr>
            <tr style="border-bottom: 1px solid rgba(148,163,184,0.06);">
                <td style="padding: 12px 0; color: #64748B; font-size: 0.88rem;">Dataset Path</td>
                <td style="padding: 12px 0; color: #E2E8F0; font-size: 0.88rem;">{health_data.get('dataset_path', 'N/A')}</td>
            </tr>
            <tr style="border-bottom: 1px solid rgba(148,163,184,0.06);">
                <td style="padding: 12px 0; color: #64748B; font-size: 0.88rem;">Row Count</td>
                <td style="padding: 12px 0; color: #E2E8F0; font-size: 0.88rem;">{health_data.get('row_count', 0)}</td>
            </tr>
            <tr style="border-bottom: 1px solid rgba(148,163,184,0.06);">
                <td style="padding: 12px 0; color: #64748B; font-size: 0.88rem;">Groq API Key</td>
                <td style="padding: 12px 0; color: #E2E8F0; font-size: 0.88rem;">{'●●●●●●●● (set)' if llm_ok else '⚠️ Not configured'}</td>
            </tr>
            <tr>
                <td style="padding: 12px 0; color: #64748B; font-size: 0.88rem;">LLM Model</td>
                <td style="padding: 12px 0; color: #E2E8F0; font-size: 0.88rem;">{health_data.get('groq_model', 'N/A')}</td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)
