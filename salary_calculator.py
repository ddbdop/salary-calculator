import streamlit as st
import pandas as pd
import datetime
import calendar
import math
import os
from dateutil.relativedelta import relativedelta
from fpdf import FPDF

st.set_page_config(page_title="Central Government Future Salary Dashboard", layout="wide")

# --- Helper Functions ---
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
                if valid_pays: matrix_dict[level_name] = valid_pays
        return levels, matrix_dict
    except Exception as e:
        st.error(f"Error processing matrix: {e}")
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
        if p >= target_amount: return p
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

# --- State Management ---
if 'dob' not in st.session_state:
    st.session_state.dob = datetime.date(1985, 6, 23)
if 'ret_date' not in st.session_state:
    st.session_state.ret_date = calc_retirement_date(st.session_state.dob)

def update_ret_date():
    st.session_state.ret_date = calc_retirement_date(st.session_state.dob)

def reset_app():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.dob = datetime.date(1985, 6, 23)
    st.session_state.ret_date = calc_retirement_date(st.session_state.dob)

# --- UI Setup ---
col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.title("🏛️ Central Government Pension & Salary Dashboard")
with col2:
    if st.button("🔄 Reset Calculator"):
        reset_app()
        st.rerun()

if os.path.exists("pay_matrix.csv"):
    levels, matrix_dict = load_pay_matrix("pay_matrix.csv")
else:
    st.warning("⚠️ 'pay_matrix.csv' not found. Please upload your 7th CPC Matrix file below:")
    uploaded_file = st.file_uploader("Upload Pay Matrix (CSV)", type=['csv'])
    if uploaded_file is not None:
        levels, matrix_dict = load_pay_matrix(uploaded_file)
    else:
        st.stop() 

with st.sidebar:
    st.header("1. Personal Details")
    emp_name = st.text_input("Employee Name", "Deb Dutta Banerjee", key='emp_name')
    dob = st.date_input("Date of Birth", value=st.session_state.dob, min_value=datetime.date(1950, 1, 1), format="DD/MM/YYYY", on_change=update_ret_date, key='dob')
    doj = st.date_input("Date of Joining", datetime.date(2010, 9, 1), min_value=datetime.date(1960, 1, 1), format="DD/MM/YYYY", key='doj')
    ret_date = st.date_input("Date of Retirement", value=st.session_state.ret_date, format="DD/MM/YYYY", key='ret_date')

    st.header("2. Pension Scheme Selection")
    if doj < datetime.date(2004, 1, 1):
        scheme = st.selectbox("Applicable Pension Scheme", ["OPS"], key='scheme')
    else:
        scheme = st.selectbox("Applicable Pension Scheme", ["UPS", "NPS"], key='scheme')
        
    if scheme in ["NPS", "UPS"]:
        current_corpus = st.number_input("Current Tier-1 Corpus (₹)", value=1000000, step=100000, key='corpus')
        nps_return_rate = st.number_input("Expected Annual Return on Corpus (%)", value=10.0, step=0.5, key='nps_ret')
        withdrawal_pct = st.slider("Corpus Lumpsum Withdrawal (%)", 0, 60, 60, key='with_pct')
    if scheme == "NPS":
        annuity_rate = st.number_input("Expected Annuity Rate at Retirement (%)", value=6.0, step=0.5, key='ann_rate')

    st.header("3. Current Pay Details")
    sim_start_date = st.date_input("Simulation Start Date", datetime.date(2026, 1, 1), format="DD/MM/YYYY", key='sim_start')
    current_level = st.selectbox("Current Pay Level", levels if levels else ["1"], index=levels.index("8") if "8" in levels else 0, key='c_level')
    available_basics = matrix_dict.get(current_level, [18000]) if matrix_dict else [18000]
    current_basic = st.selectbox("Current Basic Pay (Includes latest increment)", available_basics, key='c_basic')
    current_da = st.number_input("Current DA Rate (%)", value=50, step=1, key='c_da')
    hra_rate = st.selectbox("HRA Rate (%)", [10, 20, 30], index=1, key='hra')
    tpta_type = st.selectbox("TPTA City Category", ["Higher TPTA (X Class)", "Other Places (Y/Z Class)"], index=1, key='tpta')
    inc_month = st.selectbox("Annual Increment Month", [1, 7], format_func=lambda x: "January" if x==1 else "July", key='inc_m')

    st.header("4. Promotion / MACP Options")
    macp_list = []
    for i in range(1, 4):
        if st.checkbox(f"Apply MACP/Promotion {i}?", key=f'macp_check_{i}'):
            m_date = st.date_input(f"Date of Promotion {i}", datetime.date(2028 + (i*5), 8, 1), format="DD/MM/YYYY", key=f'mdate_{i}')
            m_target = st.selectbox(f"Target Level {i}", levels, key=f'mtarg_{i}')
            m_opt = st.radio(f"Fixation Option {i}", ["Date of Promotion", "Date of Next Increment (DNI)"], key=f'mopt_{i}')
            macp_list.append({"date": m_date, "target": m_target, "option": m_opt})

    st.header("5. Future Pay Commissions")
    da_scenario = st.selectbox("Future DA Trajectory", ["Conservative (4%)", "Balanced (5%)", "Optimistic (6%)"], index=1, key='da_scen')
    
    st.subheader("8th CPC")
    cpc_8_fitment = st.number_input("8th CPC Fitment Factor", value=2.57, step=0.01, key='cpc8_fit')
    cpc_8_impl_choice = st.selectbox("8th CPC Tentative Implementation Date", ["Jan 2026", "Jan 2027", "Jul 2027", "Jan 2028", "Jul 2028", "Jan 2029"], index=3, key='cpc8_impl')
    impl_map = {"Jan 2026": datetime.date(2026, 1, 1), "Jan 2027": datetime.date(2027, 1, 1), "Jul 2027": datetime.date(2027, 7, 1),
                "Jan 2028": datetime.date(2028, 1, 1), "Jul 2028": datetime.date(2028, 7, 1), "Jan 2029": datetime.date(2029, 1, 1)}
    
    st.subheader("9th & 10th CPC")
    cpc_9_fitment = st.number_input("9th CPC Fitment Factor (Jan 2036)", value=2.57, step=0.01, key='cpc9_fit')
    cpc_10_fitment = st.number_input("10th CPC Fitment Factor (Jan 2046)", value=2.57, step=0.01, key='cpc10_fit')

    st.header("6. Mandatory Deductions")
    cghs_ded = st.number_input("CGHS Deduction (₹)", value=650, step=50, key='cghs')
    cgegis_ded = st.number_input("CGEGIS Deduction (₹)", value=60, step=10, key='cgegis')
    if scheme == "OPS":
        gpf_sub = st.number_input("GPF Subscription (₹)", value=15000, step=1000, key='gpf')

    st.header("7. Retirement Leaves")
    el_credit = st.number_input("Earned Leave (EL)", value=300, max_value=300, key='el')
    hpl_credit = st.number_input("Half Pay Leave (HPL)", value=120, key='hpl')
    if scheme == "OPS":
        commutation_pct = st.slider("OPS Commutation Choice (%)", 0, 40, 40, key='ops_com')

# --- Calculation Engine ---
def simulate():
    records = []
    lvl_num = float(''.join(filter(str.isdigit, current_level))) if current_level else 1
    base_tpta_7cpc = 7200 if lvl_num >= 9 else (3600 if lvl_num >= 3 else 1350) if "Higher" in tpta_type else (3600 if lvl_num >= 9 else 1800 if lvl_num >= 3 else 900)

    curr_date = datetime.date(sim_start_date.year, sim_start_date.month, 1)
    if curr_date > ret_date: return [], 0

    da_jan, da_jul = (2, 2) if "Conservative" in da_scenario else ((2, 3) if "Balanced" in da_scenario else (3, 3))

    c_basic, c_level, c_da = current_basic, current_level, current_da
    pending_dni, old_level_for_dni, old_basic_for_dni = False, None, None
    
    arrears_accumulated = 0
    notional_basic, notional_level, notional_da, notional_tpta_base = 0, "", 0, 0
    notional_pending_dni, notional_old_level, notional_old_basic = False, None, None

    running_corpus = current_corpus if scheme in ["NPS", "UPS"] else 0
    active_fitment = 1.0

    while curr_date <= ret_date:
        is_arrear_period = (curr_date >= datetime.date(2026, 1, 1) and curr_date < impl_map[cpc_8_impl_choice])

        # 1. MACP Processing
        macp_hits = [m for m in macp_list if m["date"].year == curr_date.year and m["date"].month == curr_date.month]
        if macp_hits:
            m = macp_hits[0]
            if m["option"] == "Date of Promotion":
                if active_fitment == 1.0:
                    boosted = get_next_cell(c_level, c_basic, 1, matrix_dict)
                    c_level, c_basic = m["target"], fit_in_new_level(m["target"], boosted, matrix_dict)
                else:
                    c_level, c_basic = m["target"], round((c_basic * 1.03) / 100) * 100
                
                if is_arrear_period: 
                    notional_level, notional_basic = m["target"], round((notional_basic * 1.03)/100)*100
            else:
                old_level_for_dni, old_basic_for_dni, c_level, pending_dni = c_level, c_basic, m["target"], True
                if active_fitment == 1.0: c_basic = fit_in_new_level(c_level, c_basic, matrix_dict)
                if is_arrear_period:
                    notional_old_level, notional_old_basic, notional_level, notional_pending_dni = notional_level, notional_basic, m["target"], True

        # 2. Annual Increment (Prevent Jan 1 Double-Dip on Start Date)
        skip_increment = (curr_date == sim_start_date and inc_month == 1 and curr_date.month == 1)
        if curr_date.month == inc_month and not skip_increment:
            if pending_dni:
                if active_fitment == 1.0:
                    b_old = get_next_cell(old_level_for_dni, old_basic_for_dni, 2, matrix_dict)
                    c_basic = fit_in_new_level(c_level, b_old, matrix_dict)
                else:
                    c_basic = round((round((old_basic_for_dni * 1.03)/100)*100 * 1.03)/100)*100
                pending_dni = False
            else:
                c_basic = get_next_cell(c_level, c_basic, 1, matrix_dict) if active_fitment == 1.0 else round((c_basic * 1.03) / 100) * 100
            
            if is_arrear_period:
                if notional_pending_dni:
                    notional_basic = round((round((notional_old_basic * 1.03)/100)*100 * 1.03)/100)*100
                    notional_pending_dni = False
                else:
                    notional_basic = round((notional_basic * 1.03)/100)*100

        # 3. CPC Due Triggers
        # 8th CPC
        if curr_date == datetime.date(2026, 1, 1):
            if impl_map[cpc_8_impl_choice] == curr_date:
                c_basic, c_da, active_fitment = round((c_basic * cpc_8_fitment)/100)*100, 0, cpc_8_fitment
            else:
                notional_basic, notional_level, notional_da = round((c_basic * cpc_8_fitment)/100)*100, c_level, 0
                notional_tpta_base = round((base_tpta_7cpc * cpc_8_fitment)/100)*100
        
        # 9th & 10th CPCs (Instant Implementation)
        if curr_date == datetime.date(2036, 1, 1):
            c_basic, c_da, active_fitment = round((c_basic * cpc_9_fitment)/100)*100, 0, active_fitment * cpc_9_fitment
        if curr_date == datetime.date(2046, 1, 1):
            c_basic, c_da, active_fitment = round((c_basic * cpc_10_fitment)/100)*100, 0, active_fitment * cpc_10_fitment

        # 4. 8th CPC Actual Implementation Catch-Up
        if curr_date == impl_map[cpc_8_impl_choice] and curr_date > datetime.date(2026, 1, 1):
            c_basic, c_level, c_da, pending_dni, active_fitment = notional_basic, notional_level, notional_da, notional_pending_dni, cpc_8_fitment

        # DA Increments
        if curr_date.month == 1 and curr_date.year not in [2026, 2036, 2046]:
            c_da += da_jan
            if is_arrear_period: notional_da += da_jan
        if curr_date.month == 7:
            c_da += da_jul
            if is_arrear_period: notional_da += da_jul

        # Drawn Salary Calculation
        tpta_base = round((base_tpta_7cpc * active_fitment)/100)*100 if active_fitment > 1.0 else base_tpta_7cpc
        da_amt = c_basic * (c_da / 100.0)
        hra_amt = c_basic * (hra_rate / 100.0)
        tpta_amt = tpta_base + (tpta_base * (c_da / 100.0))
        gross = c_basic + da_amt + hra_amt + tpta_amt

        # Deductions & Net Pay
        nps_tier1_ded = (c_basic + da_amt) * 0.10 if scheme in ["NPS", "UPS"] else 0
        gpf_ded = gpf_sub if scheme == "OPS" else 0
        total_deductions = cghs_ded + cgegis_ded + nps_tier1_ded + gpf_ded
        net_pay = gross - total_deductions

        # Arrears Calculation (Strictly 8th CPC, with precise Net deductions)
        n_gross = 0
        if is_arrear_period:
            n_da_amt = notional_basic * (notional_da / 100.0)
            n_hra_amt = notional_basic * (hra_rate / 100.0)
            n_tpta_amt = notional_tpta_base + (notional_tpta_base * (notional_da / 100.0))
            n_gross = notional_basic + n_da_amt + n_hra_amt + n_tpta_amt
            
            diff_gross = n_gross - gross
            if diff_gross > 0:
                if scheme in ["NPS", "UPS"]:
                    # NPS/UPS Tier 1 deduction is 10% of the difference in Basic+DA
                    diff_pay_da = (notional_basic + n_da_amt) - (c_basic + da_amt)
                    arr_ded = max(0, diff_pay_da * 0.10)
                else:
                    # OPS deduction is lesser of GPF input or 6% of Notional Basic
                    arr_ded = min(gpf_sub, notional_basic * 0.06)
                
                net_arrear_month = diff_gross - arr_ded
                arrears_accumulated += max(0, net_arrear_month)

        # Corpus Addition
        if scheme in ["NPS", "UPS"]:
            monthly_interest = running_corpus * ((nps_return_rate / 100.0) / 12)
            monthly_nps_addition = (c_basic + da_amt) * 0.20 # 10% Emp + 10% Govt
            running_corpus = running_corpus + monthly_interest + monthly_nps_addition

        records.append({
            "Date": curr_date.strftime("%b %Y"),
            "Level": c_level,
            "Basic": round(c_basic),
            "DA%": c_da,
            "DA Amt": round(da_amt),
            "Drawn Gross": round(gross),
            "Net Salary": round(net_pay),
            "Due Gross (8th CPC)": round(n_gross) if is_arrear_period else "-",
            "Corpus": round(running_corpus) if scheme in ["NPS", "UPS"] else "-"
        })

        curr_date += relativedelta(months=1)
    return records, arrears_accumulated

# --- Render Output ---
if st.button("Generate Complete Projection", type="primary"):
    with st.spinner("Calculating complex progression & arrears..."):
        projection, total_arrears = simulate()
        
    if projection:
        df_proj = pd.DataFrame(projection)
        
        last_month = projection[-1]
        last_basic = float(last_month["Basic"])
        last_da_pct = float(last_month["DA%"])
        last_da_amt = float(last_month["DA Amt"])
        last_emoluments = last_basic + last_da_amt
        last_net = float(last_month["Net Salary"])
        final_corpus = float(last_month["Corpus"]) if scheme in ["NPS", "UPS"] else 0
        
        if len(projection) >= 12: avg_12m_basic = sum([p["Basic"] for p in projection[-12:]]) / 12.0
        else: avg_12m_basic = last_basic
        
        days_of_service = (ret_date - doj).days
        qualifying_half_years = min(math.floor(max(0, days_of_service) / 182.5), 66)
        
        # --- Dashboard UI ---
        st.subheader(f"📊 Dashboard: {emp_name} ({scheme})")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Final Basic Pay", f"₹ {last_basic:,.0f}")
        m2.metric("Final Net Salary", f"₹ {last_net:,.0f}")
        m3.metric("Final DA % & Amt", f"{last_da_pct}% (₹ {last_da_amt:,.0f})")
        
        if total_arrears > 0: m4.metric("Net Payable 8th CPC Arrears", f"₹ {total_arrears:,.0f}")
        elif scheme in ["NPS", "UPS"]: m4.metric("Final Tier-1 Corpus", f"₹ {final_corpus:,.0f}")
        else: m4.metric("Total Months Simulated", len(projection))

        st.markdown("---")
        st.subheader(f"💼 Estimated Retirement Benefits ({scheme} Rules)")
        
        gratuity = (1.0/4.0) * last_emoluments * qualifying_half_years
        total_leaves = min(el_credit + hpl_credit, 300)
        leave_encashment = last_emoluments * (total_leaves / 30.0)
        
        c1, c2, c3 = st.columns(3)
        c2.success(f"**Retirement Gratuity:** ₹ {gratuity:,.0f}")
        c3.warning(f"**Leave Encashment:** ₹ {leave_encashment:,.0f}")

        if scheme == "OPS":
            basic_pension = last_basic * 0.50
            pension_da = basic_pension * (last_da_pct / 100.0)
            commuted_value = (basic_pension * (commutation_pct/100.0)) * 12 * 8.194
            residual_pension = basic_pension - (basic_pension * (commutation_pct/100.0))
            
            c1.info(f"**Estimated Basic Pension:** ₹ {basic_pension:,.0f} / month\n\n**Est. Pension DA Amount:** ₹ {pension_da:,.0f}\n\n*(Residual Basic after Commutation: ₹ {residual_pension:,.0f})*")
            if commutation_pct > 0: st.error(f"**Commutation Payout (at {commutation_pct}%):** ₹ {commuted_value:,.0f}")
                
        elif scheme == "NPS":
            annuity_amt = final_corpus * ((100 - withdrawal_pct)/100.0) 
            lumpsum_amt = final_corpus * (withdrawal_pct/100.0) 
            monthly_pension = (annuity_amt * (annuity_rate/100.0)) / 12
            c1.info(f"**Estimated NPS Pension:** ₹ {monthly_pension:,.0f} / month\n\n*(Generated from {100 - withdrawal_pct}% Annuity)*")
            st.error(f"**NPS Lumpsum Withdrawal ({withdrawal_pct}%):** ₹ {lumpsum_amt:,.0f}")
            
        elif scheme == "UPS":
            assured_pension = avg_12m_basic * 0.50
            ups_lumpsum = last_emoluments * 0.10 * qualifying_half_years
            corpus_withdrawal = final_corpus * (withdrawal_pct/100.0)
            reduced_assured_pension = assured_pension * (1 - (withdrawal_pct / 100.0))
            pension_da = reduced_assured_pension * (last_da_pct / 100.0)
            
            c1.info(f"**UPS Assured Basic Pension:** ₹ {reduced_assured_pension:,.0f} / month\n\n**Est. Pension DA Amount:** ₹ {pension_da:,.0f}\n\n*(Basic reduced due to {withdrawal_pct}% Corpus Withdrawal)*")
            if withdrawal_pct > 0:
                st.error(f"**UPS Corpus Withdrawal ({withdrawal_pct}%):** ₹ {corpus_withdrawal:,.0f}")
            st.success(f"**UPS Superannuation Lumpsum:** ₹ {ups_lumpsum:,.0f}\n\n*(1/10th Emoluments per 6 months)*")

        st.markdown("---")
        st.subheader("🗓️ Transparent Projection Table")
        st.dataframe(df_proj, use_container_width=True, height=500)
