import streamlit as st
import pandas as pd
import datetime
import calendar
import math
from dateutil.relativedelta import relativedelta
import plotly.express as px

st.set_page_config(page_title="Future Salary & Pension Calculator", layout="wide")

# --- Helper Functions ---
@st.cache_data
def load_pay_matrix():
    try:
        df = pd.read_csv("pay_matrix.csv", header=None)
        levels = [str(x).replace('.0', '') for x in df.iloc[2, 1:].dropna().values]
        
        matrix_dict = {}
        for idx, col in enumerate(df.columns[1:]):
            if idx < len(levels):
                level_name = levels[idx]
                pays = pd.to_numeric(df.iloc[3:, col], errors='coerce').dropna().tolist()
                matrix_dict[level_name] = sorted([int(p) for p in pays])
        return levels, matrix_dict
    except Exception as e:
        st.error(f"Error loading matrix: {e}. Please ensure pay_matrix.csv is available.")
        return [], {}

def get_next_cell(level, current_basic, increments=1, matrix_dict=None):
    pays = matrix_dict.get(level, [])
    if not pays: return current_basic
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

# --- UI Setup ---
st.title("🏛️ Central Government Future Salary & Pension Calculator")
st.markdown("Detailed projection incorporating 7th CPC rules, FR 22 Fixation, MACP, and future Pay Commissions.")

levels, matrix_dict = load_pay_matrix()

with st.sidebar:
    st.header("1. Personal Details")
    emp_name = st.text_input("Employee Name", "Employee")
    dob = st.date_input("Date of Birth", datetime.date(1985, 5, 15), min_value=datetime.date(1960, 1, 1))
    doj = st.date_input("Date of Joining", datetime.date(2010, 8, 10))
    auto_retire = calc_retirement_date(dob)
    ret_date = st.date_input("Date of Retirement", auto_retire)

    st.header("2. Current Pay Details")
    sim_start_date = st.date_input("Simulation Start Date", datetime.date(2026, 1, 1), help="Start from Jan 2026 to ensure 8th CPC applies perfectly.")
    current_level = st.selectbox("Current Pay Level (as of Start Date)", levels if levels else ["1"])
    available_basics = matrix_dict.get(current_level, [18000]) if matrix_dict else [18000]
    current_basic = st.selectbox("Current Basic Pay", available_basics)
    current_da = st.number_input("Current DA Rate (%)", value=50, step=1)
    hra_rate = st.selectbox("HRA Rate (%)", [10, 20, 30], index=2)
    tpta_type = st.selectbox("TPTA City Category", ["Higher TPTA (X Class)", "Other Places (Y/Z Class)"])
    inc_month = st.selectbox("Annual Increment Month", [1, 7], format_func=lambda x: "January" if x==1 else "July")

    st.header("3. Promotion / MACP (FR 22)")
    macp_date = st.date_input("Expected MACP/Promotion Date", datetime.date(2028, 8, 10))
    macp_target = st.selectbox("Target Pay Level", levels if levels else ["2"])
    macp_option = st.radio("Pay Fixation Option", ["Date of Promotion", "Date of Next Increment (DNI)"])

    st.header("4. Future Pay Commissions")
    cpc_8_fitment = st.number_input("8th CPC Fitment Factor (Jan 2026)", value=2.57, step=0.01)
    cpc_9_fitment = st.number_input("9th CPC Fitment Factor (Jan 2036)", value=2.57, step=0.01)
    cpc_10_fitment = st.number_input("10th CPC Fitment Factor (Jan 2046)", value=2.57, step=0.01)
    
    st.header("5. Retirement Leaves")
    el_credit = st.number_input("Earned Leave (EL) at retirement (Max 300)", value=300, max_value=300)
    hpl_credit = st.number_input("Half Pay Leave (HPL) at retirement", value=120)
    commutation_pct = st.slider("Commutation Choice (%)", 0, 40, 40)

# --- Calculation Engine ---
def simulate():
    records = []
    
    lvl_num = float(''.join(filter(str.isdigit, current_level))) if current_level else 1
    if lvl_num <= 2:
        base_tpta = 1350 if "Higher" in tpta_type else 900
    elif 3 <= lvl_num <= 8:
        base_tpta = 3600 if "Higher" in tpta_type else 1800
    else:
        base_tpta = 7200 if "Higher" in tpta_type else 3600

    # Ensure start date is 1st of the month
    curr_date = datetime.date(sim_start_date.year, sim_start_date.month, 1)
    
    if curr_date > ret_date:
        st.warning("Retirement date is before the Simulation Start Date!")
        return []

    c_basic = current_basic
    c_level = current_level
    c_da = current_da
    c_tpta_base = base_tpta
    
    pending_dni = False
    old_level_for_dni = None
    old_basic_for_dni = None
    is_post_cpc = False # Tracks if we are "Off Matrix" mathematically

    while curr_date <= ret_date:
        # 1. Check for Pay Commissions
        if curr_date.month == 1 and curr_date.year == 2026:
            c_basic = round((c_basic * cpc_8_fitment) / 100) * 100
            c_da = 0  
            c_tpta_base = round((c_tpta_base * cpc_8_fitment) / 100) * 100
            is_post_cpc = True

        elif curr_date.month == 1 and curr_date.year == 2036:
            c_basic = round((c_basic * cpc_9_fitment) / 100) * 100
            c_da = 0  
            c_tpta_base = round((c_tpta_base * cpc_9_fitment) / 100) * 100
            is_post_cpc = True
            
        elif curr_date.month == 1 and curr_date.year == 2046:
            c_basic = round((c_basic * cpc_10_fitment) / 100) * 100
            c_da = 0  
            c_tpta_base = round((c_tpta_base * cpc_10_fitment) / 100) * 100
            is_post_cpc = True

        # 2. DA Increment (4% annually -> 2% Jan, 2% Jul)
        if curr_date.month in [1, 7]:
            # Don't add DA on the exact month of a CPC implementation (already reset to 0)
            if not (curr_date.month == 1 and curr_date.year in [2026, 2036, 2046]):
                c_da += 2

        # 3. Handle MACP / Promotion
        if curr_date.year == macp_date.year and curr_date.month == macp_date.month:
            if macp_option == "Date of Promotion":
                if not is_post_cpc:
                    boosted_basic = get_next_cell(c_level, c_basic, 1, matrix_dict)
                    c_level = macp_target
                    c_basic = fit_in_new_level(c_level, boosted_basic, matrix_dict)
                else:
                    c_basic = round((c_basic * 1.03) / 100) * 100 # Mathematical +1 increment
                    c_level = macp_target 
            else: # DNI Logic
                old_level_for_dni = c_level
                old_basic_for_dni = c_basic
                c_level = macp_target
                
                if not is_post_cpc:
                    c_basic = fit_in_new_level(c_level, c_basic, matrix_dict)
                # If post CPC, we just wait for the double increment math on DNI month
                
                pending_dni = True

        # 4. Handle Annual Increment
        if curr_date.month == inc_month:
            if pending_dni:
                if not is_post_cpc:
                    boosted_old = get_next_cell(old_level_for_dni, old_basic_for_dni, 2, matrix_dict)
                    c_basic = fit_in_new_level(c_level, boosted_old, matrix_dict)
                else:
                    # Mathematical +2 increments on old basic
                    c_basic = round((old_basic_for_dni * 1.03) / 100) * 100
                    c_basic = round((c_basic * 1.03) / 100) * 100
                pending_dni = False
            else:
                if not is_post_cpc:
                    c_basic = get_next_cell(c_level, c_basic, 1, matrix_dict)
                else:
                    # Standard 3% Govt math increment, rounded to nearest 100
                    c_basic = round((c_basic * 1.03) / 100) * 100

        # 5. Salary Calculation
        da_amt = c_basic * (c_da / 100.0)
        hra_amt = c_basic * (hra_rate / 100.0)
        tpta_amt = c_tpta_base + (c_tpta_base * (c_da / 100.0))
        gross = c_basic + da_amt + hra_amt + tpta_amt

        records.append({
            "Date": curr_date.strftime("%b %Y"),
            "Level": c_level,
            "Basic": round(c_basic),
            "DA Rate (%)": c_da,
            "DA Amount": round(da_amt),
            "HRA": round(hra_amt),
            "TPTA": round(tpta_amt),
            "Gross Salary": round(gross)
        })

        curr_date += relativedelta(months=1)

    return records

# --- Render Output ---
if st.button("Generate Salary & Pension Projection", type="primary"):
    with st.spinner("Calculating future progression..."):
        projection = simulate()
        
    if projection:
        df_proj = pd.DataFrame(projection)
        
        last_month = projection[-1]
        last_basic = float(last_month["Basic"])
        last_da_amt = float(last_month["DA Amount"])
        last_emoluments = last_basic + last_da_amt
        
        st.subheader("📊 Career Progression Summary")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Expected Last Basic Pay", f"₹ {last_basic:,.0f}")
        m2.metric("Final Gross Salary", f"₹ {last_month['Gross Salary']:,.0f}")
        m3.metric("Final DA Rate", f"{last_month['DA Rate (%)']}%")
        m4.metric("Total Months simulated", len(projection))

        st.subheader("📈 Projected Salary Growth (Gross vs Basic)")
        fig = px.area(df_proj, x="Date", y=["Basic", "Gross Salary"], 
                      color_discrete_sequence=["#1f77b4", "#2ca02c"])
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("💼 Estimated Retirement Benefits")
        
        try:
            # 1. Pension
            basic_pension = last_basic * 0.50
            
            # 2. Gratuity
            days_of_service = (ret_date - doj).days
            if days_of_service < 0: days_of_service = 0
            qualifying_half_years = min(math.floor(days_of_service / 182.5), 66)
            gratuity = (1.0/4.0) * last_emoluments * qualifying_half_years
            
            # 3. Leave Encashment
            total_leaves = min(el_credit + hpl_credit, 300)
            leave_encashment = last_emoluments * (total_leaves / 30.0)
            
            # 4. Commutation
            commutation_factor = 8.194 
            commuted_value = (basic_pension * (commutation_pct/100.0)) * 12 * commutation_factor
            residual_pension = basic_pension - (basic_pension * (commutation_pct/100.0))
            
            b1, b2, b3 = st.columns(3)
            b1.info(f"**Basic Pension:** ₹ {basic_pension:,.0f} / month\n\n*(Residual post-commutation: ₹ {residual_pension:,.0f})*")
            b2.success(f"**Estimated Gratuity:** ₹ {gratuity:,.0f}\n\n*(Based on {qualifying_half_years} half-yearly periods)*")
            b3.warning(f"**Leave Encashment:** ₹ {leave_encashment:,.0f}\n\n*(Based on {total_leaves} valid days)*")
            
            if commutation_pct > 0:
                st.error(f"**Commutation Payout (at {commutation_pct}%):** ₹ {commuted_value:,.0f} *(Lumpsum payout at retirement)*")
        except Exception as e:
            st.error(f"An error occurred while calculating retirement benefits: {e}. Please check your dates.")

        st.markdown("---")
        st.subheader("🗓️ Month-by-Month Projection Data")
        st.dataframe(df_proj, use_container_width=True, height=400)