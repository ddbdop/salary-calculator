"""
Central Government Salary & Pension Projection Dashboard
Improved version — Government Blue Theme | Plotly Charts | PDF Export | Mobile Friendly
"""

import streamlit as st
import streamlit.components.v1 as _stc
import pandas as pd
import datetime
import calendar
import math
import os
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go
import io

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False

# ══════════════════════════════════════════════════════════════════════
# FORCE LIGHT THEME via .streamlit/config.toml (most reliable input-
# visibility fix — overrides system dark-mode before Streamlit renders)
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
    <style>
    /* Force Input Boxes to be opaque and high contrast */
    div[data-baseweb="input"] {
        background-color: #ffffff !important;
        border: 2px solid #333333 !important;
    }
    input {
        color: #000000 !important;
        font-weight: bold !important;
    }
    /* Force Selectbox visibility */
    div[data-baseweb="select"] {
        background-color: #ffffff !important;
    }
    div[role="listbox"] {
        background-color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="CG Salary & Pension Dashboard",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════════════════════
# GLOBAL CSS — Government Blue Theme + Mobile Responsive
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
.main .block-container {
    padding: 0.9rem 1.4rem;
    max-width: 1400px;
}

/* ══ GLOBAL input text fix — works across ALL Streamlit versions ══
   Nuclear selector: targets every input/textarea on the page first,
   then sidebar overrides re-apply white text.                       */
input, textarea, select {
    color: #1a1a2e !important;
    background-color: #ffffff !important;
    -webkit-text-fill-color: #1a1a2e !important;
    caret-color: #003366 !important;
}
input::placeholder, textarea::placeholder {
    color: #8ea8be !important;
    -webkit-text-fill-color: #8ea8be !important;
    opacity: 1 !important;
}
/* Selectbox value text */
[data-baseweb="select"] span,
[data-baseweb="select"] [data-baseweb="tag"] {
    color: #1a1a2e !important;
    -webkit-text-fill-color: #1a1a2e !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(175deg, #001a33 0%, #003366 55%, #1a5276 100%);
    border-right: 2px solid rgba(41,128,185,0.4);
}
/* Sidebar text — target only non-input elements to avoid cascade bleed */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div:not([data-baseweb]),
[data-testid="stSidebar"] li,
[data-testid="stSidebar"] .stMarkdown { color: #e8f4fd !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    font-size: 0.76rem !important;
    font-weight: 700 !important;
    color: #aed6f1 !important;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    border-bottom: 1px solid rgba(174,214,241,0.25);
    padding-bottom: 5px;
    margin: 14px 0 6px !important;
}
/* Sidebar inputs — white text on dark bg (overrides global rule above) */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea {
    background: rgba(255,255,255,0.12) !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    caret-color: #aed6f1 !important;
    border-radius: 6px !important;
}
[data-testid="stSidebar"] input::placeholder,
[data-testid="stSidebar"] textarea::placeholder {
    color: rgba(255,255,255,0.45) !important;
    -webkit-text-fill-color: rgba(255,255,255,0.45) !important;
}
/* Sidebar selectbox */
[data-testid="stSidebar"] .stSelectbox > div > div {
    background: rgba(255,255,255,0.1) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    border-radius: 6px !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] span,
[data-testid="stSidebar"] [data-baseweb="select"] [data-baseweb="tag"] {
    color: #e8f4fd !important;
}
[data-testid="stSidebar"] .stSlider > div > div > div > div {
    background: #2980b9 !important;
}
[data-testid="stSidebar"] label {
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    color: #cce4f5 !important;
}

/* ── Header Banner ── */
.gov-header {
    background: linear-gradient(135deg, #001a33 0%, #003366 50%, #1a5276 80%, #2980b9 100%);
    border-radius: 12px;
    padding: 1.1rem 1.6rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 6px 22px rgba(0,26,51,0.3);
    border: 1px solid rgba(41,128,185,0.3);
}
.gov-header-left h1 {
    color: white !important;
    font-size: 1.25rem !important;
    font-weight: 700 !important;
    margin: 0 !important;
    line-height: 1.3;
}
.gov-header-left p {
    color: #85c1e9;
    font-size: 0.73rem;
    margin: 5px 0 0;
}
.gov-emblem { font-size: 2.6rem; opacity: 0.8; }

/* ── KPI Grid ── */
.kpi-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(145px, 1fr));
    gap: 0.7rem;
    margin: 0.8rem 0;
}
.kpi {
    background: white;
    border-radius: 10px;
    padding: 0.85rem 0.9rem;
    border-top: 3px solid #2980b9;
    box-shadow: 0 2px 10px rgba(0,51,102,0.08);
}
.kpi.g  { border-top-color: #1e8449; }
.kpi.o  { border-top-color: #d68910; }
.kpi.r  { border-top-color: #c0392b; }
.kpi.n  { border-top-color: #001a33; }
.kpi-lbl {
    font-size: 0.64rem;
    color: #5d6d7e;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.kpi-val {
    font-size: 1.12rem;
    font-weight: 700;
    color: #003366;
    margin-top: 3px;
}
.kpi-sub { font-size: 0.62rem; color: #95a5a6; margin-top: 2px; }

/* ── Section Header ── */
.sec-hd {
    background: linear-gradient(90deg, #003366, #1a5276);
    color: white;
    padding: 0.42rem 0.9rem;
    border-radius: 6px;
    font-size: 0.84rem;
    font-weight: 600;
    margin: 0.9rem 0 0.55rem;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* ── Benefit Cards ── */
.ben-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(155px, 1fr));
    gap: 0.7rem;
    margin: 0.5rem 0;
}
.ben-card {
    background: #f4f8fb;
    border: 1px solid #d5e8f5;
    border-radius: 10px;
    padding: 0.85rem;
    text-align: center;
}
.ben-card.hi { background: #eaf4fb; border-color: #2980b9; }
.b-lbl { font-size: 0.64rem; color: #5d6d7e; font-weight: 600; text-transform: uppercase; }
.b-val { font-size: 1.0rem; font-weight: 700; color: #003366; margin-top: 5px; }
.b-sub { font-size: 0.62rem; color: #7f8c8d; margin-top: 3px; }

/* ── Arrears / Corpus Banner ── */
.arr-banner {
    background: linear-gradient(135deg, #c87f0a, #f39c12);
    color: white;
    padding: 0.75rem 1.2rem;
    border-radius: 9px;
    font-weight: 700;
    text-align: center;
    font-size: 0.95rem;
    box-shadow: 0 4px 12px rgba(200,127,10,0.28);
    margin: 0.6rem 0;
}
.corpus-banner {
    background: linear-gradient(135deg, #1a5276, #2980b9);
    color: white;
    padding: 0.75rem 1.2rem;
    border-radius: 9px;
    font-weight: 700;
    text-align: center;
    font-size: 0.95rem;
    box-shadow: 0 4px 12px rgba(26,82,118,0.28);
    margin: 0.6rem 0;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #eaf4fb;
    border-radius: 8px;
    padding: 4px;
    gap: 3px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 6px;
    color: #1a5276 !important;
    font-weight: 500;
    font-size: 0.8rem;
}
.stTabs [aria-selected="true"] {
    background: #003366 !important;
    color: white !important;
}

/* ── Primary Button ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #001a33, #003366) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    width: 100% !important;
    padding: 0.58rem !important;
    font-size: 0.95rem !important;
    box-shadow: 0 4px 14px rgba(0,26,51,0.32) !important;
    transition: all 0.2s !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #003366, #1a5276) !important;
    box-shadow: 0 6px 18px rgba(0,26,51,0.4) !important;
}
.stButton > button { border-radius: 6px !important; }

/* ── Disclaimer / Footer ── */
.gov-footer {
    text-align: center;
    color: #aab4be;
    font-size: 0.67rem;
    padding: 0.9rem 0;
    border-top: 1px solid #d5e8f5;
    margin-top: 1.2rem;
    line-height: 1.7;
}

/* ── Mobile Responsive ── */
@media (max-width: 768px) {
    .main .block-container { padding: 0.4rem 0.5rem; }
    .gov-header { padding: 0.7rem 0.9rem; flex-direction: column; gap: 0.5rem; }
    .gov-header-left h1 { font-size: 0.95rem !important; }
    .gov-emblem { font-size: 1.8rem; }
    .kpi-row { grid-template-columns: repeat(2, 1fr); }
    .kpi-val { font-size: 0.9rem; }
    .ben-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# JS STYLE INJECTION — inject <style> into parent <head> via iframe.
# This is the ONLY method guaranteed to override Streamlit's theme CSS
# because it runs after the full DOM is painted.
# ══════════════════════════════════════════════════════════════════════
_stc.html("""
<script>
(function injectInputStyles() {
    var css = `
        /* ── Main area inputs: dark text on white ── */
        input, textarea {
            color: #1a1a2e !important;
            -webkit-text-fill-color: #1a1a2e !important;
            background-color: #ffffff !important;
            caret-color: #003366 !important;
        }
        input::placeholder, textarea::placeholder {
            color: #8ea8be !important;
            -webkit-text-fill-color: #8ea8be !important;
            opacity: 1 !important;
        }
        /* ── Sidebar inputs: white text on dark ── */
        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] textarea {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            background-color: rgba(255,255,255,0.12) !important;
            border: 1px solid rgba(255,255,255,0.25) !important;
            caret-color: #aed6f1 !important;
        }
        [data-testid="stSidebar"] input::placeholder,
        [data-testid="stSidebar"] textarea::placeholder {
            color: rgba(255,255,255,0.45) !important;
            -webkit-text-fill-color: rgba(255,255,255,0.45) !important;
        }
    `;
    /* Inject into parent document head */
    var pd = window.parent.document;
    var existing = pd.getElementById('__salary_calc_input_fix__');
    if (existing) { existing.remove(); }
    var tag = pd.createElement('style');
    tag.id = '__salary_calc_input_fix__';
    tag.innerHTML = css;
    pd.head.appendChild(tag);

    /* MutationObserver keeps re-applying when Streamlit re-renders widgets */
    new MutationObserver(function() {
        pd.querySelectorAll('input, textarea').forEach(function(el) {
            var inSidebar = pd.querySelector('[data-testid="stSidebar"]');
            inSidebar = inSidebar && inSidebar.contains(el);
            el.style.setProperty('color',                    inSidebar ? '#ffffff' : '#1a1a2e', 'important');
            el.style.setProperty('-webkit-text-fill-color',  inSidebar ? '#ffffff' : '#1a1a2e', 'important');
            el.style.setProperty('background-color',         inSidebar ? 'rgba(255,255,255,0.12)' : '#ffffff', 'important');
        });
    }).observe(pd.body, { childList: true, subtree: true });
})();
</script>
""", height=0, scrolling=False)



# ══════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS (logic unchanged from original)
# ══════════════════════════════════════════════════════════════════════
@st.cache_data
def load_pay_matrix(file_buffer):
    try:
        df = pd.read_csv(file_buffer, header=None, names=range(30), engine='python')
        levels = [str(x).replace('.0', '') for x in df.iloc[2, 1:].dropna().values]
        matrix_dict = {}
        for idx, col in enumerate(df.columns[1:]):
            if idx < len(levels):
                level_name = levels[idx]
                pays = pd.to_numeric(df.iloc[3:, col], errors='coerce').dropna().tolist()
                valid_pays = sorted([int(p) for p in pays if p > 0])
                if valid_pays:
                    matrix_dict[level_name] = valid_pays
        return levels, matrix_dict
    except Exception as e:
        st.error(f"Error processing matrix: {e}")
        return [], {}


def get_next_cell(level, current_basic, increments=1, matrix_dict=None):
    pays = matrix_dict.get(level, [])
    if not pays:
        return current_basic
    try:
        current_idx = pays.index(current_basic)
        next_idx = min(current_idx + increments, len(pays) - 1)
        return pays[next_idx]
    except ValueError:
        for p in pays:
            if p >= current_basic:
                current_idx = pays.index(p)
                next_idx = min(current_idx + increments, len(pays) - 1)
                return pays[next_idx]
        return current_basic


def fit_in_new_level(new_level, target_amount, matrix_dict):
    pays = matrix_dict.get(new_level, [])
    for p in pays:
        if p >= target_amount:
            return p
    return pays[-1] if pays else target_amount


def calc_retirement_date(dob):
    ret_year = dob.year + 60
    if dob.day == 1:
        ret_month = dob.month - 1
        if ret_month == 0:
            ret_month = 12
            ret_year -= 1
    else:
        ret_month = dob.month
    last_day = calendar.monthrange(ret_year, ret_month)[1]
    return datetime.date(ret_year, ret_month, last_day)


# ══════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════
if 'dob' not in st.session_state:
    st.session_state.dob = datetime.date(1985, 1, 1)
if 'ret_date' not in st.session_state:
    st.session_state.ret_date = calc_retirement_date(st.session_state.dob)


def update_ret_date():
    st.session_state.ret_date = calc_retirement_date(st.session_state.dob)


def reset_app():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.dob = datetime.date(1985, 1, 1)
    st.session_state.ret_date = calc_retirement_date(st.session_state.dob)
    st.session_state.emp_name = "Employee Name"


# ══════════════════════════════════════════════════════════════════════
# DEFAULT VALUES FOR CONDITIONAL VARIABLES (avoid NameError)
# ══════════════════════════════════════════════════════════════════════
gpf_sub       = 0
commutation_pct = 0
annuity_rate  = 6.0
current_corpus = 0
nps_return_rate = 10.0
withdrawal_pct = 60


# ══════════════════════════════════════════════════════════════════════
# LOAD PAY MATRIX
# ══════════════════════════════════════════════════════════════════════
if os.path.exists("pay_matrix.csv"):
    levels, matrix_dict = load_pay_matrix("pay_matrix.csv")
else:
    st.warning("⚠️ 'pay_matrix.csv' not found. Please upload your 7th CPC Pay Matrix CSV file below.")
    uploaded_file = st.file_uploader("Upload Pay Matrix (CSV)", type=["csv"])
    if uploaded_file is not None:
        levels, matrix_dict = load_pay_matrix(uploaded_file)
    else:
        st.stop()


# ══════════════════════════════════════════════════════════════════════
# SIDEBAR — INPUTS
# ══════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        '<div style="text-align:center;padding:6px 0 14px;">'
        '<span style="font-size:1.9rem;">🏛️</span>'
        '<div style="color:#85c1e9;font-size:0.65rem;margin-top:4px;letter-spacing:0.08em;">'
        'GOVT. OF INDIA | DoT</div></div>',
        unsafe_allow_html=True
    )

    # 1. Personal Details
    st.header("1. Personal Details")
    emp_name = st.text_input("Employee Name", value="Employee Name", key="emp_name")
    dob = st.date_input(
        "Date of Birth", value=st.session_state.dob,
        min_value=datetime.date(1950, 1, 1),
        format="DD/MM/YYYY", on_change=update_ret_date, key="dob"
    )
    doj = st.date_input(
        "Date of Joining", datetime.date(2010, 9, 1),
        min_value=datetime.date(1960, 1, 1),
        format="DD/MM/YYYY", key="doj"
    )
    ret_date = st.date_input(
        "Date of Retirement", value=st.session_state.ret_date,
        format="DD/MM/YYYY", key="ret_date"
    )

    # 2. Pension Scheme
    st.header("2. Pension Scheme")
    if doj < datetime.date(2004, 1, 1):
        scheme = st.selectbox("Applicable Scheme", ["OPS"], key="scheme")
    else:
        scheme = st.selectbox("Applicable Scheme", ["UPS", "NPS"], key="scheme")

    if scheme in ["NPS", "UPS"]:
        current_corpus   = st.number_input("Current Tier-1 Corpus (₹)", value=1000000, step=100000, key="corpus")
        nps_return_rate  = st.number_input("Expected Annual Return (%)", value=10.0, step=0.5, key="nps_ret")
        withdrawal_pct   = st.slider("Corpus Lumpsum Withdrawal (%)", 0, 60, 60, key="with_pct")
    if scheme == "NPS":
        annuity_rate = st.number_input("Expected Annuity Rate (%)", value=6.0, step=0.5, key="ann_rate")

    # 3. Current Pay Details
    st.header("3. Current Pay Details")
    sim_start_date = st.date_input(
        "Simulation Start Date", datetime.date(2026, 1, 1),
        format="DD/MM/YYYY", key="sim_start"
    )
    current_level = st.selectbox(
        "Current Pay Level",
        levels if levels else ["1"],
        index=levels.index("8") if "8" in levels else 0,
        key="c_level"
    )
    available_basics = matrix_dict.get(current_level, [18000]) if matrix_dict else [18000]
    current_basic = st.selectbox("Current Basic Pay (₹)", available_basics, key="c_basic")
    current_da    = st.number_input("Current DA Rate (%)", value=50, step=1, key="c_da")
    hra_rate      = st.selectbox("HRA Rate (%)", [10, 20, 30], index=1, key="hra")
    tpta_type     = st.selectbox(
        "TPTA City Category",
        ["Higher TPTA (X Class)", "Other Places (Y/Z Class)"],
        index=1, key="tpta"
    )
    inc_month = st.selectbox(
        "Annual Increment Month", [1, 7],
        format_func=lambda x: "January" if x == 1 else "July",
        key="inc_m"
    )

    # 4. Promotion / MACP
    st.header("4. Promotion / MACP")
    macp_list = []
    for i in range(1, 4):
        if st.checkbox(f"Apply MACP / Promotion {i}?", key=f"macp_check_{i}"):
            m_date   = st.date_input(f"Date {i}", datetime.date(2028 + (i * 5), 8, 1), format="DD/MM/YYYY", key=f"mdate_{i}")
            m_target = st.selectbox(f"Target Level {i}", levels, key=f"mtarg_{i}")
            m_opt    = st.radio(f"Fixation Option {i}", ["Date of Promotion", "Date of Next Increment (DNI)"], key=f"mopt_{i}")
            macp_list.append({"date": m_date, "target": m_target, "option": m_opt})

    # 5. Pay Commissions
    st.header("5. Pay Commissions")
    da_scenario = st.selectbox(
        "Future DA Trajectory",
        ["Conservative (4%)", "Balanced (5%)", "Optimistic (6%)"],
        index=1, key="da_scen"
    )
    st.subheader("8th CPC")
    cpc_8_fitment    = st.number_input("Fitment Factor", value=2.57, step=0.01, key="cpc8_fit")
    cpc_8_impl_choice = st.selectbox(
        "Implementation Date",
        ["Jan 2026", "Jan 2027", "Jul 2027", "Jan 2028", "Jul 2028", "Jan 2029"],
        index=3, key="cpc8_impl"
    )
    impl_map = {
        "Jan 2026": datetime.date(2026, 1, 1),
        "Jan 2027": datetime.date(2027, 1, 1),
        "Jul 2027": datetime.date(2027, 7, 1),
        "Jan 2028": datetime.date(2028, 1, 1),
        "Jul 2028": datetime.date(2028, 7, 1),
        "Jan 2029": datetime.date(2029, 1, 1),
    }
    st.subheader("9th & 10th CPC")
    cpc_9_fitment  = st.number_input("9th CPC Fitment (Jan 2036)", value=2.57, step=0.01, key="cpc9_fit")
    cpc_10_fitment = st.number_input("10th CPC Fitment (Jan 2046)", value=2.57, step=0.01, key="cpc10_fit")

    # 6. Deductions
    st.header("6. Deductions")
    cghs_ded   = st.number_input("CGHS (₹)", value=650, step=50, key="cghs")
    cgegis_ded = st.number_input("CGEGIS (₹)", value=60, step=10, key="cgegis")
    if scheme == "OPS":
        gpf_sub = st.number_input("GPF Subscription (₹)", value=15000, step=1000, key="gpf")

    # 7. Retirement Leaves
    st.header("7. Retirement Leaves")
    el_credit  = st.number_input("Earned Leave (EL)", value=300, max_value=300, key="el")
    hpl_credit = st.number_input("Half Pay Leave (HPL)", value=120, key="hpl")
    if scheme == "OPS":
        commutation_pct = st.slider("OPS Commutation (%)", 0, 40, 40, key="ops_com")

    st.markdown("---")
    if st.button("🔄 Reset Calculator", use_container_width=True):
        reset_app()
        st.rerun()


# ══════════════════════════════════════════════════════════════════════
# HEADER BANNER
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="gov-header">
  <div class="gov-header-left">
    <h1>🏛️ Central Government Salary &amp; Pension Projection</h1>
    <p>7th CPC Pay Matrix &nbsp;|&nbsp; 8th / 9th / 10th CPC Scenarios &nbsp;|&nbsp; OPS / NPS / UPS Benefits</p>
  </div>
  <div class="gov-emblem">⚖️</div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# SIMULATION ENGINE (logic identical to original; HRA & TPTA added to records)
# ══════════════════════════════════════════════════════════════════════
def simulate():
    records = []
    lvl_num = float("".join(filter(str.isdigit, current_level))) if current_level else 1
    base_tpta_7cpc = (
        (7200 if lvl_num >= 9 else (3600 if lvl_num >= 3 else 1350))
        if "Higher" in tpta_type
        else (3600 if lvl_num >= 9 else 1800 if lvl_num >= 3 else 900)
    )

    curr_date = datetime.date(sim_start_date.year, sim_start_date.month, 1)
    if curr_date > ret_date:
        return [], 0

    da_jan, da_jul = (
        (2, 2) if "Conservative" in da_scenario
        else ((2, 3) if "Balanced" in da_scenario else (3, 3))
    )

    c_basic, c_level, c_da = current_basic, current_level, current_da
    pending_dni, old_level_for_dni, old_basic_for_dni = False, None, None

    arrears_accumulated = 0
    notional_basic, notional_level, notional_da, notional_tpta_base = 0, "", 0, 0
    notional_pending_dni, notional_old_level, notional_old_basic = False, None, None

    running_corpus = current_corpus if scheme in ["NPS", "UPS"] else 0
    active_fitment = 1.0

    while curr_date <= ret_date:
        is_arrear_period = (
            curr_date >= datetime.date(2026, 1, 1)
            and curr_date < impl_map[cpc_8_impl_choice]
        )

        # 1. MACP Processing
        macp_hits = [
            m for m in macp_list
            if m["date"].year == curr_date.year and m["date"].month == curr_date.month
        ]
        if macp_hits:
            m = macp_hits[0]
            if m["option"] == "Date of Promotion":
                if active_fitment == 1.0:
                    boosted = get_next_cell(c_level, c_basic, 1, matrix_dict)
                    c_level, c_basic = m["target"], fit_in_new_level(m["target"], boosted, matrix_dict)
                else:
                    c_level, c_basic = m["target"], round((c_basic * 1.03) / 100) * 100
                if is_arrear_period:
                    notional_level, notional_basic = m["target"], round((notional_basic * 1.03) / 100) * 100
            else:
                old_level_for_dni, old_basic_for_dni, c_level, pending_dni = c_level, c_basic, m["target"], True
                if active_fitment == 1.0:
                    c_basic = fit_in_new_level(c_level, c_basic, matrix_dict)
                if is_arrear_period:
                    notional_old_level  = notional_level
                    notional_old_basic  = notional_basic
                    notional_level      = m["target"]
                    notional_pending_dni = True

        # 2. Annual Increment
        skip_increment = (curr_date == sim_start_date and inc_month == 1 and curr_date.month == 1)
        if curr_date.month == inc_month and not skip_increment:
            if pending_dni:
                if active_fitment == 1.0:
                    b_old   = get_next_cell(old_level_for_dni, old_basic_for_dni, 2, matrix_dict)
                    c_basic = fit_in_new_level(c_level, b_old, matrix_dict)
                else:
                    c_basic = round((round((old_basic_for_dni * 1.03) / 100) * 100 * 1.03) / 100) * 100
                pending_dni = False
            else:
                c_basic = (
                    get_next_cell(c_level, c_basic, 1, matrix_dict)
                    if active_fitment == 1.0
                    else round((c_basic * 1.03) / 100) * 100
                )
            if is_arrear_period:
                if notional_pending_dni:
                    notional_basic = round((round((notional_old_basic * 1.03) / 100) * 100 * 1.03) / 100) * 100
                    notional_pending_dni = False
                else:
                    notional_basic = round((notional_basic * 1.03) / 100) * 100

        # 3. CPC Due Trigger — 8th CPC
        if curr_date == datetime.date(2026, 1, 1):
            if impl_map[cpc_8_impl_choice] == curr_date:
                c_basic, c_da, active_fitment = round((c_basic * cpc_8_fitment) / 100) * 100, 0, cpc_8_fitment
            else:
                notional_basic    = round((c_basic * cpc_8_fitment) / 100) * 100
                notional_level    = c_level
                notional_da       = 0
                notional_tpta_base = round((base_tpta_7cpc * cpc_8_fitment) / 100) * 100

        # 9th CPC
        if curr_date == datetime.date(2036, 1, 1):
            c_basic, c_da, active_fitment = (
                round((c_basic * cpc_9_fitment) / 100) * 100, 0, active_fitment * cpc_9_fitment
            )
        # 10th CPC
        if curr_date == datetime.date(2046, 1, 1):
            c_basic, c_da, active_fitment = (
                round((c_basic * cpc_10_fitment) / 100) * 100, 0, active_fitment * cpc_10_fitment
            )

        # 4. 8th CPC Actual Implementation
        if curr_date == impl_map[cpc_8_impl_choice] and curr_date > datetime.date(2026, 1, 1):
            c_basic      = notional_basic
            c_level      = notional_level
            c_da         = notional_da
            pending_dni  = notional_pending_dni
            active_fitment = cpc_8_fitment

        # DA Increments
        if curr_date.month == 1 and curr_date.year not in [2026, 2036, 2046]:
            c_da += da_jan
            if is_arrear_period:
                notional_da += da_jan
        if curr_date.month == 7:
            c_da += da_jul
            if is_arrear_period:
                notional_da += da_jul

        # Salary Calculation
        tpta_base = (
            round((base_tpta_7cpc * active_fitment) / 100) * 100
            if active_fitment > 1.0 else base_tpta_7cpc
        )
        da_amt   = c_basic * (c_da / 100.0)
        hra_amt  = c_basic * (hra_rate / 100.0)
        tpta_amt = tpta_base + (tpta_base * (c_da / 100.0))
        gross    = c_basic + da_amt + hra_amt + tpta_amt

        # Deductions & Net
        nps_tier1_ded  = (c_basic + da_amt) * 0.10 if scheme in ["NPS", "UPS"] else 0
        gpf_ded        = gpf_sub if scheme == "OPS" else 0
        total_deductions = cghs_ded + cgegis_ded + nps_tier1_ded + gpf_ded
        net_pay        = gross - total_deductions

        # Arrears
        n_gross = 0
        if is_arrear_period:
            n_da_amt   = notional_basic * (notional_da / 100.0)
            n_hra_amt  = notional_basic * (hra_rate / 100.0)
            n_tpta_amt = notional_tpta_base + (notional_tpta_base * (notional_da / 100.0))
            n_gross    = notional_basic + n_da_amt + n_hra_amt + n_tpta_amt
            diff_gross = n_gross - gross
            if diff_gross > 0:
                if scheme in ["NPS", "UPS"]:
                    diff_pay_da = (notional_basic + n_da_amt) - (c_basic + da_amt)
                    arr_ded = max(0, diff_pay_da * 0.10)
                else:
                    arr_ded = min(gpf_sub, notional_basic * 0.06)
                arrears_accumulated += max(0, diff_gross - arr_ded)

        # Corpus Growth
        if scheme in ["NPS", "UPS"]:
            monthly_interest    = running_corpus * ((nps_return_rate / 100.0) / 12)
            monthly_nps_addition = (c_basic + da_amt) * 0.20  # 10% Emp + 10% Govt
            running_corpus      += monthly_interest + monthly_nps_addition

        records.append({
            "Date":               curr_date.strftime("%b %Y"),
            "Level":              c_level,
            "Basic":              round(c_basic),
            "DA%":                c_da,
            "DA Amt":             round(da_amt),
            "HRA":                round(hra_amt),
            "TPTA":               round(tpta_amt),
            "Drawn Gross":        round(gross),
            "NPS/GPF Ded":        round(nps_tier1_ded + gpf_ded),
            "Net Salary":         round(net_pay),
            "Due Gross (8CPC)":   round(n_gross) if is_arrear_period else "-",
            "Corpus":             round(running_corpus) if scheme in ["NPS", "UPS"] else "-",
        })

        curr_date += relativedelta(months=1)

    return records, arrears_accumulated


# ══════════════════════════════════════════════════════════════════════
# PDF GENERATOR
# ══════════════════════════════════════════════════════════════════════
def generate_pdf(emp_name, scheme, ret_date, doj, kpi_rows, benefit_rows, arrears, df_annual):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    # ── Header block ──
    pdf.set_fill_color(0, 51, 102)
    pdf.rect(0, 0, 210, 38, "F")
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(10, 7)
    pdf.cell(190, 8, "Central Government Salary & Pension Projection", align="C", ln=True)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_xy(10, 17)
    pdf.cell(190, 5, f"Employee: {emp_name}   |   Scheme: {scheme}   |   Generated: {datetime.date.today().strftime('%d/%m/%Y')}", align="C", ln=True)
    pdf.set_xy(10, 24)
    pdf.cell(190, 5, f"Date of Joining: {doj.strftime('%d/%m/%Y')}   |   Superannuation: {ret_date.strftime('%d/%m/%Y')}", align="C")
    pdf.set_text_color(0, 0, 0)

    # ── KPI Section ──
    pdf.set_xy(10, 44)
    pdf.set_fill_color(26, 82, 118)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(190, 7, "  Key Salary Metrics at Retirement", fill=True, ln=True)
    pdf.set_text_color(0, 0, 0)

    y = pdf.get_y() + 3
    for i in range(0, len(kpi_rows), 2):
        pdf.set_xy(10, y)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(45, 5, kpi_rows[i][0] + ":")
        pdf.set_font("Helvetica", "", 8.5)
        pdf.cell(45, 5, kpi_rows[i][1])
        if i + 1 < len(kpi_rows):
            pdf.set_font("Helvetica", "B", 8)
            pdf.cell(45, 5, kpi_rows[i + 1][0] + ":")
            pdf.set_font("Helvetica", "", 8.5)
            pdf.cell(45, 5, kpi_rows[i + 1][1])
        y += 8

    # ── Arrears banner (if any) ──
    if arrears > 0:
        pdf.set_xy(10, y + 2)
        pdf.set_fill_color(200, 127, 10)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(190, 7, f"  Estimated Net Payable 8th CPC Arrears:  Rs. {arrears:,.0f}", fill=True)
        y += 14
        pdf.set_text_color(0, 0, 0)

    # ── Benefits Section ──
    pdf.set_xy(10, y + 6)
    pdf.set_fill_color(26, 82, 118)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(190, 7, "  Estimated Retirement Benefits", fill=True, ln=True)
    pdf.set_text_color(0, 0, 0)

    y = pdf.get_y() + 3
    for label, value, note in benefit_rows:
        pdf.set_xy(10, y)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(70, 5.5, label + ":")
        pdf.set_font("Helvetica", "", 8.5)
        pdf.cell(60, 5.5, value)
        pdf.set_font("Helvetica", "I", 7.5)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(55, 5.5, note)
        pdf.set_text_color(0, 0, 0)
        y += 7.5

    # ── Annual Snapshot Table ──
    pdf.add_page()
    pdf.set_fill_color(0, 51, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(190, 7, "  Annual Salary Snapshot (January of each year)", fill=True, ln=True)
    pdf.set_text_color(0, 0, 0)

    cols      = ["Date",  "Level", "Basic",   "DA%",  "Drawn Gross", "Net Salary"]
    col_w     = [22,      14,      30,         14,     40,             40]
    align_map = ["C",     "C",     "C",        "C",    "C",            "C"]

    pdf.set_fill_color(209, 231, 246)
    pdf.set_font("Helvetica", "B", 8)
    for col, w, al in zip(cols, col_w, align_map):
        pdf.cell(w, 6, col, border=1, fill=True, align=al)
    pdf.ln()

    pdf.set_font("Helvetica", "", 7.5)
    for idx, (_, row) in enumerate(df_annual.iterrows()):
        fill = (idx % 2 == 0)
        if fill:
            pdf.set_fill_color(245, 250, 255)
        for col, w, al in zip(cols, col_w, align_map):
            raw = str(row.get(col, ""))
            if col in ["Basic", "Drawn Gross", "Net Salary"]:
                try:
                    raw = f"Rs.{int(raw):,}"
                except Exception:
                    pass
            pdf.cell(w, 5.5, raw, border=1, fill=fill, align=al)
        pdf.ln()

    # ── Disclaimer footer ──
    pdf.set_y(-14)
    pdf.set_font("Helvetica", "I", 6.5)
    pdf.set_text_color(140, 140, 140)
    pdf.cell(190, 5,
             "Disclaimer: Projection tool for planning only. Not an official document. "
             "Actual figures subject to Government orders & notifications.",
             align="C")

    return pdf.output(dest="S").encode("latin-1")


# ══════════════════════════════════════════════════════════════════════
# GENERATE BUTTON + MAIN OUTPUT
# ══════════════════════════════════════════════════════════════════════
btn_col, info_col = st.columns([1, 2])
with btn_col:
    generate = st.button("🚀 Generate Salary Projection", type="primary")
with info_col:
    st.caption(
        f"👤 **{st.session_state.get('emp_name', '—')}** &nbsp;|&nbsp; "
        f"📅 {sim_start_date.strftime('%b %Y')} → {ret_date.strftime('%b %Y')} &nbsp;|&nbsp; "
        f"🏦 Scheme: **{scheme}**"
    )

if generate:
    with st.spinner("⚙️ Computing month-by-month salary progression…"):
        projection, total_arrears = simulate()

    if not projection:
        st.error("⚠️ Simulation produced no output. Please verify the input dates.")
        st.stop()

    df_proj = pd.DataFrame(projection)

    # ── Derived Metrics ──
    last        = projection[-1]
    last_basic  = float(last["Basic"])
    last_da_pct = float(last["DA%"])
    last_da_amt = float(last["DA Amt"])
    last_hra    = float(last["HRA"])
    last_tpta   = float(last["TPTA"])
    last_emoluments = last_basic + last_da_amt
    last_gross  = float(last["Drawn Gross"])
    last_net    = float(last["Net Salary"])
    final_corpus = float(last["Corpus"]) if scheme in ["NPS", "UPS"] else 0.0

    avg_12m_basic = sum(p["Basic"] for p in projection[-12:]) / min(12, len(projection))
    days_of_service = (ret_date - doj).days
    qualifying_half_years = min(math.floor(max(0, days_of_service) / 182.5), 66)
    total_leaves   = min(el_credit + hpl_credit, 300)
    leave_encashment = last_emoluments * (total_leaves / 30.0)
    gratuity = min((1.0 / 4.0) * last_emoluments * qualifying_half_years, 2500000)
    service_years   = days_of_service / 365.25

    # ── Scheme-specific benefit calculation ──
    benefit_rows = []   # (label, formatted_value, note)  — for both UI & PDF

    if scheme == "OPS":
        basic_pension     = last_basic * 0.50
        pension_da        = basic_pension * (last_da_pct / 100.0)
        commuted_value    = (basic_pension * (commutation_pct / 100.0)) * 12 * 8.194
        residual_pension  = basic_pension * (1 - commutation_pct / 100.0)
        benefit_rows = [
            ("Monthly Basic Pension",   f"₹ {basic_pension:,.0f}",   "50% of last basic"),
            ("Monthly Pension DA",       f"₹ {pension_da:,.0f}",      f"@ {last_da_pct:.0f}% DA"),
            ("Commutation Payout",       f"₹ {commuted_value:,.0f}",  f"@ {commutation_pct}% | factor 8.194"),
            ("Residual Monthly Pension", f"₹ {residual_pension:,.0f}", "Post commutation"),
            ("DCRG (Gratuity)",          f"₹ {gratuity:,.0f}",        "Max ₹25 L (Jan 2024)"),
            ("Leave Encashment",         f"₹ {leave_encashment:,.0f}", f"{int(total_leaves)} days"),
        ]

    elif scheme == "NPS":
        annuity_amt    = final_corpus * ((100 - withdrawal_pct) / 100.0)
        lumpsum_amt    = final_corpus * (withdrawal_pct / 100.0)
        monthly_pension = (annuity_amt * (annuity_rate / 100.0)) / 12
        benefit_rows = [
            ("Estimated NPS Monthly Pension", f"₹ {monthly_pension:,.0f}", f"{100-withdrawal_pct}% annuity"),
            ("NPS Lumpsum Withdrawal",        f"₹ {lumpsum_amt:,.0f}",     f"{withdrawal_pct}% of corpus"),
            ("DCRG (Gratuity)",               f"₹ {gratuity:,.0f}",        "Max ₹25 L (Jan 2024)"),
            ("Leave Encashment",              f"₹ {leave_encashment:,.0f}", f"{int(total_leaves)} days"),
        ]

    elif scheme == "UPS":
        assured_pension        = avg_12m_basic * 0.50
        corpus_withdrawal      = final_corpus * (withdrawal_pct / 100.0)
        reduced_assured_pension = assured_pension * (1 - withdrawal_pct / 100.0)
        pension_da             = reduced_assured_pension * (last_da_pct / 100.0)
        ups_lumpsum            = last_emoluments * 0.10 * qualifying_half_years
        benefit_rows = [
            ("UPS Assured Monthly Pension",  f"₹ {reduced_assured_pension:,.0f}", f"50% avg basic × {1-withdrawal_pct/100:.0%}"),
            ("Monthly Pension DA",           f"₹ {pension_da:,.0f}",              f"@ {last_da_pct:.0f}% DA"),
            ("UPS Superannuation Lumpsum",   f"₹ {ups_lumpsum:,.0f}",             "1/10 emoluments × half-yrs"),
            ("Corpus Withdrawal",            f"₹ {corpus_withdrawal:,.0f}",       f"{withdrawal_pct}% of corpus"),
            ("DCRG (Gratuity)",              f"₹ {gratuity:,.0f}",                "Max ₹25 L (Jan 2024)"),
            ("Leave Encashment",             f"₹ {leave_encashment:,.0f}",        f"{int(total_leaves)} days"),
        ]

    # PDF-compatible benefit rows (label, value, note) already in benefit_rows — same structure
    kpi_rows_pdf = [
        ("Final Basic Pay",       f"Rs.{last_basic:,.0f}"),
        ("Final Gross Salary",    f"Rs.{last_gross:,.0f}"),
        ("Final Net Salary",      f"Rs.{last_net:,.0f}"),
        ("Final DA Rate",         f"{last_da_pct:.0f}%"),
        ("Service Length",        f"{service_years:.1f} years"),
        ("Qualifying Half-Years", str(qualifying_half_years)),
    ]

    # ════════════════════════════════════════════════════════════
    # OUTPUT TABS
    # ════════════════════════════════════════════════════════════
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋  Summary",
        "📈  Charts",
        "🗓️  Projection Table",
        "📄  Export PDF"
    ])

    # ────────────────────────────────────────
    # TAB 1 — SUMMARY
    # ────────────────────────────────────────
    with tab1:
        st.markdown('<div class="sec-hd">📊 Key Salary Metrics at Retirement</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="kpi-row">
          <div class="kpi n">
            <div class="kpi-lbl">Final Basic Pay</div>
            <div class="kpi-val">₹ {last_basic:,.0f}</div>
            <div class="kpi-sub">Level {last["Level"]}</div>
          </div>
          <div class="kpi g">
            <div class="kpi-lbl">Final Gross Salary</div>
            <div class="kpi-val">₹ {last_gross:,.0f}</div>
            <div class="kpi-sub">Before deductions</div>
          </div>
          <div class="kpi">
            <div class="kpi-lbl">Final Net Salary</div>
            <div class="kpi-val">₹ {last_net:,.0f}</div>
            <div class="kpi-sub">Take-home</div>
          </div>
          <div class="kpi o">
            <div class="kpi-lbl">Final DA Rate</div>
            <div class="kpi-val">{last_da_pct:.0f}%</div>
            <div class="kpi-sub">₹ {last_da_amt:,.0f} / month</div>
          </div>
          <div class="kpi">
            <div class="kpi-lbl">Service Length</div>
            <div class="kpi-val">{service_years:.1f} Yrs</div>
            <div class="kpi-sub">{qualifying_half_years} qualifying half-yrs</div>
          </div>
          <div class="kpi r">
            <div class="kpi-lbl">Months Simulated</div>
            <div class="kpi-val">{len(projection)}</div>
            <div class="kpi-sub">{sim_start_date.strftime("%b %Y")} → {ret_date.strftime("%b %Y")}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        if total_arrears > 0:
            st.markdown(
                f'<div class="arr-banner">💰 Estimated Net Payable 8th CPC Arrears: ₹ {total_arrears:,.0f}</div>',
                unsafe_allow_html=True
            )
        elif scheme in ["NPS", "UPS"] and final_corpus > 0:
            st.markdown(
                f'<div class="corpus-banner">🏦 Final Tier-1 Corpus at Retirement: ₹ {final_corpus:,.0f}</div>',
                unsafe_allow_html=True
            )

        st.markdown('<div class="sec-hd">💼 Estimated Retirement Benefits</div>', unsafe_allow_html=True)
        cards_html = '<div class="ben-grid">'
        for label, value, note in benefit_rows:
            cards_html += (
                f'<div class="ben-card hi">'
                f'<div class="b-lbl">{label}</div>'
                f'<div class="b-val">{value}</div>'
                f'<div class="b-sub">{note}</div>'
                f'</div>'
            )
        cards_html += '</div>'
        st.markdown(cards_html, unsafe_allow_html=True)

    # ────────────────────────────────────────
    # TAB 2 — CHARTS
    # ────────────────────────────────────────
    with tab2:
        # Numeric helpers
        df_num = df_proj.copy()
        for col in ["Basic", "Drawn Gross", "Net Salary", "DA%"]:
            df_num[col] = pd.to_numeric(df_num[col], errors="coerce")
        df_num["Corpus_num"] = pd.to_numeric(df_num["Corpus"], errors="coerce")

        # Annual snapshots (January)
        df_ann = df_num[df_num["Date"].str.startswith("Jan")].copy()
        if df_ann.empty:
            df_ann = df_num.iloc[::12].copy()

        PLOTLY_DEFAULTS = dict(
            template="plotly_white",
            margin=dict(l=10, r=10, t=36, b=10),
            plot_bgcolor="rgba(244,248,251,0.5)",
            paper_bgcolor="white",
            font=dict(family="Inter", color="#1a1a2e"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        CPC_EVENTS = [
            (impl_map[cpc_8_impl_choice].strftime("%b %Y"), "8th CPC", "#d68910"),
            ("Jan 2036",  "9th CPC",  "#c0392b"),
            ("Jan 2046",  "10th CPC", "#8e44ad"),
        ]

        # ── Chart 1: Salary Progression ──
        st.markdown('<div class="sec-hd">📈 Salary Progression Over Career</div>', unsafe_allow_html=True)
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=df_ann["Date"], y=df_ann["Basic"],
            name="Basic Pay",
            line=dict(color="#003366", width=2.5),
            mode="lines+markers", marker=dict(size=4)
        ))
        fig1.add_trace(go.Scatter(
            x=df_ann["Date"], y=df_ann["Drawn Gross"],
            name="Gross Salary",
            line=dict(color="#2980b9", width=2, dash="dot"),
            mode="lines+markers", marker=dict(size=4)
        ))
        fig1.add_trace(go.Scatter(
            x=df_ann["Date"], y=df_ann["Net Salary"],
            name="Net Salary",
            line=dict(color="#1e8449", width=2),
            mode="lines+markers", marker=dict(size=4),
            fill="tozeroy", fillcolor="rgba(30,132,73,0.06)"
        ))
        for evt_date, evt_label, evt_color in CPC_EVENTS:
            if evt_date in df_ann["Date"].values:
                fig1.add_shape(
                    type="line",
                    x0=evt_date, x1=evt_date,
                    y0=0, y1=1,
                    xref="x", yref="paper",
                    line=dict(color=evt_color, dash="dash", width=1.5)
                )
                fig1.add_annotation(
                    x=evt_date, y=1.02,
                    xref="x", yref="paper",
                    text=evt_label,
                    showarrow=False,
                    font=dict(color=evt_color, size=9, family="Inter"),
                    bgcolor="rgba(255,255,255,0.85)",
                    bordercolor=evt_color,
                    borderwidth=1,
                    borderpad=2,
                )
        fig1.update_layout(
            **PLOTLY_DEFAULTS,
            height=360,
            yaxis=dict(tickprefix="₹", tickformat=",.0f", title="Amount (₹)"),
            xaxis=dict(title="", tickangle=-45, nticks=20)
        )
        st.plotly_chart(fig1, use_container_width=True)

        # ── Chart 2: DA% Trajectory ──
        st.markdown('<div class="sec-hd">📊 DA% Trajectory Over Career</div>', unsafe_allow_html=True)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=df_ann["Date"], y=df_ann["DA%"],
            name="DA %",
            marker=dict(
                color=df_ann["DA%"],
                colorscale=[[0, "#aed6f1"], [0.5, "#2980b9"], [1.0, "#001a33"]],
                showscale=False
            )
        ))
        fig2.update_layout(
            **PLOTLY_DEFAULTS,
            height=280,
            yaxis=dict(title="DA (%)", ticksuffix="%"),
            xaxis=dict(title="", tickangle=-45, nticks=20),
            showlegend=False
        )
        st.plotly_chart(fig2, use_container_width=True)

        # ── Chart 3: Corpus Growth (NPS/UPS only) ──
        if scheme in ["NPS", "UPS"]:
            st.markdown('<div class="sec-hd">🏦 NPS / UPS Corpus Growth</div>', unsafe_allow_html=True)
            corpus_df = df_ann[df_ann["Corpus_num"].notna()].copy()
            if not corpus_df.empty:
                fig3 = go.Figure()
                fig3.add_trace(go.Scatter(
                    x=corpus_df["Date"], y=corpus_df["Corpus_num"],
                    name="Corpus Value",
                    line=dict(color="#1a5276", width=2.5),
                    fill="tozeroy",
                    fillcolor="rgba(26,82,118,0.10)",
                    mode="lines+markers", marker=dict(size=4)
                ))
                fig3.update_layout(
                    **PLOTLY_DEFAULTS,
                    height=280,
                    yaxis=dict(tickprefix="₹", tickformat=",.0f", title="Corpus (₹)"),
                    xaxis=dict(title="", tickangle=-45, nticks=20),
                    showlegend=False
                )
                st.plotly_chart(fig3, use_container_width=True)

        # ── Chart 4: Salary Composition at Retirement (Donut) ──
        st.markdown('<div class="sec-hd">🥧 Gross Salary Composition at Retirement</div>', unsafe_allow_html=True)
        fig4 = go.Figure(go.Pie(
            labels=["Basic Pay", "DA Amount", "HRA", "TPTA"],
            values=[last_basic, last_da_amt, last_hra, last_tpta],
            hole=0.48,
            marker=dict(colors=["#003366", "#2980b9", "#1e8449", "#d68910"]),
            textinfo="label+percent",
            textfont=dict(size=11, family="Inter"),
            direction="clockwise"
        ))
        fig4.update_layout(
            height=300,
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor="white",
            font=dict(family="Inter", color="#1a1a2e"),
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
            annotations=[dict(
                text=f"₹{last_gross:,.0f}",
                x=0.5, y=0.5,
                font=dict(size=12, family="Inter", color="#003366"),
                showarrow=False
            )]
        )
        st.plotly_chart(fig4, use_container_width=True)

    # ────────────────────────────────────────
    # TAB 3 — PROJECTION TABLE
    # ────────────────────────────────────────
    with tab3:
        st.markdown('<div class="sec-hd">🗓️ Month-by-Month Projection</div>', unsafe_allow_html=True)

        # Filter controls
        fc1, fc2 = st.columns([2, 1])
        years_avail = sorted({d.split(" ")[1] for d in df_proj["Date"]})
        with fc1:
            year_filter = st.multiselect("Filter by Year(s)", years_avail, placeholder="All years shown")
        with fc2:
            show_annual = st.checkbox("Annual snapshot (Jan only)", value=True)

        df_display = df_proj.copy()
        if year_filter:
            df_display = df_display[df_display["Date"].str.contains("|".join(year_filter))]
        if show_annual:
            df_display = df_display[df_display["Date"].str.startswith("Jan")]

        # Format monetary columns
        money_cols = ["Basic", "DA Amt", "HRA", "TPTA", "Drawn Gross", "NPS/GPF Ded", "Net Salary"]
        df_fmt = df_display.copy()
        for col in money_cols:
            if col in df_fmt.columns:
                df_fmt[col] = df_fmt[col].apply(
                    lambda x: f"₹ {int(x):,}" if str(x).replace(".", "", 1).isdigit() else x
                )

        st.dataframe(df_fmt, use_container_width=True, height=500, hide_index=True)

        # CSV download
        csv_io = io.StringIO()
        df_proj.to_csv(csv_io, index=False)
        st.download_button(
            "⬇️ Download Full Data (CSV)",
            data=csv_io.getvalue(),
            file_name=f"Salary_Projection_{emp_name.replace(' ', '_')}.csv",
            mime="text/csv"
        )

    # ────────────────────────────────────────
    # TAB 4 — PDF EXPORT
    # ────────────────────────────────────────
    with tab4:
        st.markdown('<div class="sec-hd">📄 Generate PDF Summary Report</div>', unsafe_allow_html=True)

        if not FPDF_AVAILABLE:
            st.warning("⚠️ `fpdf2` library not installed. Run: `pip install fpdf2`")
        else:
            df_annual_pdf = df_proj[df_proj["Date"].str.startswith("Jan")].copy()
            st.info(
                "The PDF will include: key salary metrics, retirement benefit estimates, "
                "8th CPC arrears figure, and an annual salary snapshot table."
            )
            if st.button("📥 Generate & Download PDF Report", use_container_width=True):
                with st.spinner("Rendering PDF…"):
                    pdf_bytes = generate_pdf(
                        emp_name=emp_name,
                        scheme=scheme,
                        ret_date=ret_date,
                        doj=doj,
                        kpi_rows=kpi_rows_pdf,
                        benefit_rows=benefit_rows,
                        arrears=total_arrears,
                        df_annual=df_annual_pdf
                    )
                st.download_button(
                    label="✅ Click to Download PDF",
                    data=pdf_bytes,
                    file_name=f"Salary_Projection_{emp_name.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )

# ══════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="gov-footer">
  🏛️ Central Government Salary &amp; Pension Projection Tool &nbsp;|&nbsp; Based on 7th CPC Pay Matrix<br>
  Projection tool for personal planning purposes only. Not an official Government document.<br>
  Figures are subject to applicable Government orders, notifications, and actual service records.
</div>
""", unsafe_allow_html=True)
