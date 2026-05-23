import streamlit as st
import pandas as pd
import datetime
import calendar
import math
import os
from dateutil.relativedelta import relativedelta
from fpdf import FPDF

st.set_page_config(page_title="Future Salary & Pension Dashboard", layout="wide")

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

# --- State Management (Reset Logic) ---
DEFAULT_DOB = datetime.date(1985, 5, 15)
DEFAULT_DOJ = datetime.date(2010, 8, 10)

def reset_app():
    for key in st.session_state.keys():
        del st.session_state[key]

# --- UI Setup ---
col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.title("🏛️ Central Government Pension & Salary Dashboard")
with col2:
    if st.button("🔄 Reset Calculator", on_click=reset_app):
        pass

# --- FILE UPLOAD LOGIC ---
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
    emp_name = st.text_input("Employee Name", "Employee", key='emp_name')
    dob = st.date_input("Date of Birth", DEFAULT_DOB, min_value=datetime.date(1950, 1, 1), format="DD/MM/YYYY", key='dob')
    doj = st.date_input("Date of Joining", DEFAULT_DOJ, min_value=datetime.date(1960, 1, 1), format="DD/MM/YYYY", key='doj')
    auto_retire = calc_retirement_date(dob)
    ret_date = st.date_input("Date of Retirement", auto_retire, format="DD/MM/YYYY", key='ret_date')

    st.header("2. Pension Scheme Selection")
    if doj < datetime.date(2004, 1, 1):
        scheme = st.selectbox("Applicable Pension Scheme", ["OPS"], key='scheme')
        st.info("Employees joining before 01/01/2004 default to OPS.")
    else:
        scheme = st.selectbox("Applicable Pension Scheme", ["NPS", "UPS"], key='scheme')
        
    if scheme in ["NPS", "UPS"]:
        current_corpus = st.number_input("Current Tier-1 Corpus (₹)", value=1000000, step=100000, key='corpus')
        nps_return_rate = st.number_input("Expected Annual Return on Corpus (%)", value=10.0, step=0.5, key='nps_ret')
        withdrawal_pct = st.slider("Corpus Lumpsum Withdrawal (%)", 0, 60, 60, key='with_pct', help="Max 60%. Remaining % funds the Annuity/Assured Pension.")
    if scheme == "NPS":
        annuity_rate = st.number_input("Expected Annuity Rate at Retirement (%)", value=6.0, step=0.5, key='ann_rate')

    st.header("3. Current Pay Details")
    sim_start_date = st.date_input("Simulation Start Date", datetime.date(2025, 1, 1), format="DD/MM/YYYY", key='sim_start')
    current_level = st.selectbox("Current Pay Level", levels if levels else ["1"], key='c_level')
    available_basics = matrix_dict.get(current_level, [18000]) if matrix_dict else [18000]
    current_basic = st.selectbox("Current Basic Pay", available_basics, key='c_basic')
    current_da = st.number_input("Current DA Rate (%)", value=50, step=1, key='c_da')
    hra_rate = st.selectbox("HRA Rate (%)", [10, 20, 30], index=2, key='hra')
    tpta_type = st.selectbox("TPTA City Category", ["Higher TPTA (X Class)", "Other Places (Y/Z Class)"], key='tpta')
    inc_month = st.selectbox("Annual Increment Month", [1, 7], format_func=lambda x: "January" if x==1 else "July", key='inc_m')

    st.header("4. Promotion / MACP Options")
    macp_list = []
    for i in range(1, 4):
        if st.checkbox(f"Apply MACP/Promotion {i}?", key=f'macp_check_{i}'):
            m_date = st.date_input(f"Date of Promotion {i}", datetime.date(2028 + (i*5), 8, 1), format="DD/MM/YYYY", key=f'mdate_{i}')
            m_target = st.selectbox(f"Target Level {i}", levels, key=f'mtarg_{i}')
            m_opt = st.radio(f"Fixation Option {i}", ["Date of Promotion", "Date of Next Increment (DNI)"], key=f'mopt_{i}')
            macp_list.append({"date": m_date, "target": m_target, "option": m_opt})

    st.header("5. Future Pay Commissions & DA")
    da_scenario = st.selectbox("Future DA Trajectory", ["Conservative (4% Annually)", "Balanced (5% Annually)", "Optimistic (6% Annually)"], index=1, key='da_scen')
    cpc_8_fitment = st.number_input("8th CPC Fitment Factor", value=2.57, step=0.01, key='cpc8_fit')
    
    # Delayed Implementation Options
    cpc_8_impl_choice = st.selectbox("8th CPC Tentative Implementation Date", 
                                     ["Jan 2026", "Jan 2027", "Jul 2027", "Jan 2028", "Jul 2028", "Jan 2029"], index=3, key='cpc8_impl')
    impl_map = {"Jan 2026": datetime.date(2026, 1, 1), "Jan 2027": datetime.date(2027, 1, 1), "Jul 2027": datetime.date(2027, 7, 1),
                "Jan 2028": datetime.date(2028, 1, 1), "Jul 2028": datetime.date(2028, 7, 1), "Jan 2029": datetime.date(2029, 1, 1)}
    cpc_8_impl_date = impl_map[cpc_8_impl_choice]
    
    st.header("6. Retirement Leaves & OPS Options")
    el_credit = st.number_input("Earned Leave (EL) at retirement", value=300, max_value=300, key='el')
    hpl_credit = st.number_input("Half Pay Leave (HPL) at retirement", value=120, key='hpl')
    if scheme == "OPS":
        commutation_pct = st.slider("OPS Commutation Choice (%)", 0, 40, 40, key='ops_com')

# --- Calculation Engine ---
def simulate():
    records = []
    
    lvl_num = float(''.join(filter(str.isdigit, current_level))) if current_level else 1
    base_tpta_7cpc = 7200 if lvl_num >= 9 else (3600 if lvl_num >= 3 else 1350) if "Higher" in tpta_type else (3600 if lvl_num >= 9 else 1800 if lvl_num >= 3 else 900)

    curr_date = datetime.date(sim_start_date.year, sim_start_date.month, 1)
    if curr_date > ret_date:
        st.warning("Retirement date is before Simulation Start Date!")
        return [], 0

    # DA Split Logic
    da_jan, da_jul = 2, 2
    if "Balanced" in da_scenario: da_jan, da_jul = 2, 3
    elif "Optimistic" in da_scenario: da_jan, da_jul = 3, 3

    # State Variables
    c_basic, c_level, c_da = current_basic, current_level, current_da
    pending_dni, old_level_for_dni, old_basic_for_dni = False, None, None
    is_post_cpc = False
    
    # 8th CPC Arrears Tracking Variables
    arrears_accumulated = 0
    notional_basic = 0
    notional_level = ""
    notional_da = 0
    notional_tpta_base = 0
    notional_pending_dni, notional_old_level, notional_old_basic = False, None, None

    running_corpus = current_corpus if scheme in ["NPS", "UPS"] else 0

    while curr_date <= ret_date:
        # Check CPC Phase
        is_arrear_period = (curr_date >= datetime.date(2026, 1, 1)) and (curr_date < cpc_8_impl_date)
        
        # --- ORDER OF OPERATIONS: 1. Pay Fixation (MACP) -> 2. Increment -> 3. CPC Multiplier ---
        
        # 1. MACP Processing
        macp_hits = [m for m in macp_list if m["date"].year == curr_date.year and m["date"].month == curr_date.month]
        if macp_hits:
            m = macp_hits[0] # Execute first matching MACP
            if m["option"] == "Date of Promotion":
                if not is_post_cpc:
                    boosted = get_next_cell(c_level, c_basic, 1, matrix_dict)
                    c_level, c_basic = m["target"], fit_in_new_level(m["target"], boosted, matrix_dict)
                else:
                    c_level, c_basic = m["target"], round((c_basic * 1.03) / 100) * 100
                if is_arrear_period: # Apply to notional track too
                    n_boosted = get_next_cell(notional_level, notional_basic, 1, matrix_dict)
                    notional_level, notional_basic = m["target"], round((notional_basic * 1.03)/100)*100
            else: # DNI Option
                old_level_for_dni, old_basic_for_dni, c_level, pending_dni = c_level, c_basic, m["target"], True
                if not is_post_cpc: c_basic = fit_in_new_level(c_level, c_basic, matrix_dict)
                
                if is_arrear_period:
                    notional_old_level, notional_old_basic, notional_level, notional_pending_dni = notional_level, notional_basic, m["target"], True

        # 2. Annual Increment Processing
        if curr_date.month == inc_month:
            # Actual Track
            if pending_dni:
                if not is_post_cpc:
                    b_old = get_next_cell(old_level_for_dni, old_basic_for_dni, 2, matrix_dict)
                    c_basic = fit_in_new_level(c_level, b_old, matrix_dict)
                else:
                    c_basic = round((round((old_basic_for_dni * 1.03)/100)*100 * 1.03)/100)*100
                pending_dni = False
            else:
                c_basic = get_next_cell(c_level, c_basic, 1, matrix_dict) if not is_post_cpc else round((c_basic * 1.03) / 100) * 100
            
            # Notional Track
            if is_arrear_period:
                if notional_pending_dni:
                    notional_basic = round((round((notional_old_basic * 1.03)/100)*100 * 1.03)/100)*100
                    notional_pending_dni = False
                else:
                    notional_basic = round((notional_basic * 1.03)/100)*100

        # 3. Pay Commission Processing
        if curr_date == datetime.date(2026, 1, 1):
            if cpc_8_impl_date == datetime.date(2026, 1, 1):
                # Implemented Immediately
                c_basic = round((c_basic * cpc_8_fitment) / 100) * 100
                c_da = 0  
                is_post_cpc = True
            else:
                # Arrear Tracking Begins - Setup Notional values
                notional_basic = round((c_basic * cpc_8_fitment) / 100) * 100
                notional_level = c_level
                notional_da = 0
                notional_tpta_base = round((base_tpta_7cpc * cpc_8_fitment)/100)*100

        # 4. CPC Implementation Catch-up
        if curr_date == cpc_8_impl_date and curr_date > datetime.date(2026, 1, 1):
            c_basic = notional_basic
            c_level = notional_level
            c_da = notional_da
            pending_dni = notional_pending_dni
            is_post_cpc = True

        # DA Increments
        if curr_date.month == 1 and not (curr_date.month == 1 and curr_date.year in [2026, 2036, 2046]):
            c_da += da_jan
            if is_arrear_period: notional_da += da_jan
        if curr_date.month == 7:
            c_da += da_jul
            if is_arrear_period: notional_da += da_jul

        # Standard Salary Calculation
        tpta_base = round((base_tpta_7cpc * cpc_8_fitment)/100)*100 if is_post_cpc else base_tpta_7cpc
        da_amt = c_basic * (c_da / 100.0)
        hra_amt = c_basic * (hra_rate / 100.0)
        tpta_amt = tpta_base + (tpta_base * (c_da / 100.0))
        gross = c_basic + da_amt + hra_amt + tpta_amt

        # Arrears Calculation (Unrevised vs Notional Revised)
        if is_arrear_period:
            n_da_amt = notional_basic * (notional_da / 100.0)
            n_hra_amt = notional_basic * (hra_rate / 100.0)
            n_tpta_amt = notional_tpta_base + (notional_tpta_base * (notional_da / 100.0))
            n_gross = notional_basic + n_da_amt + n_hra_amt + n_tpta_amt
            monthly_arrear = n_gross - gross
            arrears_accumulated += max(0, monthly_arrear)

        # NPS / UPS Corpus Accumulation (10% Employee + 10% Employer in Tier 1)
        if scheme in ["NPS", "UPS"]:
            monthly_interest = running_corpus * ((nps_return_rate / 100.0) / 12)
            monthly_nps_addition = (c_basic + da_amt) * 0.20 # Exact 10% + 10% rules
            running_corpus = running_corpus + monthly_interest + monthly_nps_addition

        records.append({
            "Date": curr_date.strftime("%b %Y"),
            "Level": c_level,
            "Basic": round(c_basic),
            "DA Rate (%)": c_da,
            "DA Amt (₹)": round(da_amt),
            "Gross": round(gross),
            "Corpus": round(running_corpus) if scheme in ["NPS", "UPS"] else 0
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
        last_da_amt = float(last_month["DA Amt (₹)"])
        last_emoluments = last_basic + last_da_amt
        final_corpus = float(last_month["Corpus"]) if scheme in ["NPS", "UPS"] else 0
        
        if len(projection) >= 12:
            avg_12m_basic = sum([p["Basic"] for p in projection[-12:]]) / 12.0
        else: avg_12m_basic = last_basic
        
        days_of_service = (ret_date - doj).days
        if days_of_service < 0: days_of_service = 0
        qualifying_half_years = min(math.floor(days_of_service / 182.5), 66)
        
        # --- Dashboard UI ---
        st.subheader(f"📊 Dashboard: {emp_name} ({scheme})")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Final Basic Pay", f"₹ {last_basic:,.0f}")
        m2.metric("Final Gross Salary", f"₹ {last_month['Gross']:,.0f}")
        m3.metric("Final DA % & Amount", f"{last_month['DA Rate (%)']}% (₹ {last_da_amt:,.0f})")
        
        if total_arrears > 0: m4.metric("Calculated 8th CPC Arrears", f"₹ {total_arrears:,.0f}")
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
            commuted_value = (basic_pension * (commutation_pct/100.0)) * 12 * 8.194
            residual_pension = basic_pension - (basic_pension * (commutation_pct/100.0))
            c1.info(f"**Basic Pension:** ₹ {basic_pension:,.0f} / month\n\n*(Residual: ₹ {residual_pension:,.0f})*")
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
            
            # Withdrawal Impact Mathematics
            corpus_withdrawal = final_corpus * (withdrawal_pct/100.0)
            reduction_ratio = withdrawal_pct / 100.0
            reduced_assured_pension = assured_pension * (1 - reduction_ratio)
            
            c1.info(f"**UPS Assured Pension:** ₹ {reduced_assured_pension:,.0f} / month\n\n*(Reduced due to {withdrawal_pct}% Corpus Withdrawal)*")
            if withdrawal_pct > 0:
                st.error(f"**UPS Corpus Withdrawal ({withdrawal_pct}%):** ₹ {corpus_withdrawal:,.0f}\n\n*(In addition to Gratuity & Superannuation Lumpsum)*")
            st.success(f"**UPS Superannuation Lumpsum:** ₹ {ups_lumpsum:,.0f}\n\n*(1/10th Emoluments per 6 months)*")

        st.markdown("---")
        st.subheader("🗓️ Data Output & Export Options")
        
        csv_data = df_proj.to_csv(index=False).encode('utf-8')
        
        # Safe PDF Generation
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, txt=f"Salary & Pension Projection: {emp_name}", ln=True, align='C')
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, txt=f"Scheme: {scheme} | Retirement Date: {ret_date.strftime('%d/%m/%Y')}", ln=True, align='C')
        pdf.cell(0, 10, txt=f"Final Basic: Rs. {last_basic:,.0f} | Final Gross: Rs. {last_month['Gross']:,.0f}", ln=True)
        pdf.cell(0, 10, txt=f"Estimated Gratuity: Rs. {gratuity:,.0f} | Leave Encashment: Rs. {leave_encashment:,.0f}", ln=True)
        if total_arrears > 0: pdf.cell(0, 10, txt=f"Calculated 8th CPC Arrears: Rs. {total_arrears:,.0f}", ln=True)

        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, txt="Month-by-Month Data", ln=True, align='C')
        pdf.set_font("Arial", 'B', 9)
        
        cols = ["Date", "Level", "Basic", "DA %", "DA Amt", "Gross", "Corpus"]
        col_widths = [25, 15, 25, 15, 25, 30, 35]
        for i, header in enumerate(cols):
            pdf.cell(col_widths[i], 10, txt=header, border=1, align='C')
        pdf.ln()
        
        pdf.set_font("Arial", '', 8)
        for row in projection:
            pdf.cell(col_widths[0], 8, txt=str(row['Date']), border=1, align='C')
            pdf.cell(col_widths[1], 8, txt=str(row['Level']), border=1, align='C')
            pdf.cell(col_widths[2], 8, txt=str(row['Basic']), border=1, align='C')
            pdf.cell(col_widths[3], 8, txt=str(row['DA Rate (%)']), border=1, align='C')
            pdf.cell(col_widths[4], 8, txt=str(row['DA Amt (₹)']), border=1, align='C')
            pdf.cell(col_widths[5], 8, txt=str(row['Gross']), border=1, align='C')
            pdf.cell(col_widths[6], 8, txt=str(row['Corpus']), border=1, align='C')
            pdf.ln()

        pdf_out = pdf.output(dest='S')
        pdf_bytes = pdf_out.encode('latin1') if isinstance(pdf_out, str) else bytes(pdf_out)
        
        e1, e2 = st.columns(2)
        e1.download_button("📥 Download as CSV", data=csv_data, file_name="Projection_Data.csv", mime="text/csv")
        e2.download_button("🖨️ Export Summary & Table as PDF", data=pdf_bytes, file_name="Retirement_Summary.pdf", mime="application/pdf")
        
        st.dataframe(df_proj, use_container_width=True, height=400)
