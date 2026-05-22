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
        # engine='python' and names=range(30) makes it immune to uneven comma errors
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

# --- State Management ---
if 'reset_trigger' not in st.session_state:
    st.session_state.reset_trigger = False

def reset_app():
    st.session_state.clear()
    st.session_state.reset_trigger = True

# --- UI Setup ---
col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.title("🏛️ Central Government Pension & Salary Dashboard")
with col2:
    if st.button("🔄 Reset Calculator"):
        reset_app()
        st.rerun()

st.markdown("Detailed projection incorporating 7th/8th/9th CPC rules, FR 22, and OPS/NPS/UPS metrics.")

# --- FILE UPLOAD LOGIC ---
if os.path.exists("pay_matrix.csv"):
    levels, matrix_dict = load_pay_matrix("pay_matrix.csv")
else:
    st.warning("⚠️ 'pay_matrix.csv' not found automatically. Please upload your 7th CPC Matrix file below:")
    uploaded_file = st.file_uploader("Upload Pay Matrix (CSV)", type=['csv'])
    if uploaded_file is not None:
        levels, matrix_dict = load_pay_matrix(uploaded_file)
    else:
        st.stop() 

with st.sidebar:
    st.header("1. Personal Details")
    emp_name = st.text_input("Employee Name", "Employee")
    dob = st.date_input("Date of Birth", datetime.date(1985, 5, 15), min_value=datetime.date(1950, 1, 1))
    doj = st.date_input("Date of Joining", datetime.date(2002, 8, 10), min_value=datetime.date(1960, 1, 1))
    auto_retire = calc_retirement_date(dob)
    ret_date = st.date_input("Date of Retirement", auto_retire)

    st.header("2. Pension Scheme Selection")
    if doj < datetime.date(2004, 1, 1):
        scheme = st.selectbox("Applicable Pension Scheme", ["OPS"])
        st.info("Employees joining before Jan 1, 2004 are mapped to OPS.")
    else:
        scheme = st.selectbox("Applicable Pension Scheme", ["NPS", "UPS"])
        
    if scheme in ["NPS", "UPS"]:
        current_corpus = st.number_input("Current NPS/UPS Corpus (₹)", value=1000000, step=100000)
        nps_return_rate = st.number_input("Expected Annual Return on Corpus (%)", value=10.0, step=0.5)
    if scheme == "NPS":
        annuity_rate = st.number_input("Expected Annuity Rate at Retirement (%)", value=6.0, step=0.5)

    st.header("3. Current Pay Details")
    sim_start_date = st.date_input("Simulation Start Date", datetime.date(2026, 1, 1))
    current_level = st.selectbox("Current Pay Level", levels if levels else ["1"])
    available_basics = matrix_dict.get(current_level, [18000]) if matrix_dict else [18000]
    current_basic = st.selectbox("Current Basic Pay", available_basics)
    current_da = st.number_input("Current DA Rate (%)", value=50, step=1)
    hra_rate = st.selectbox("HRA Rate (%)", [10, 20, 30], index=2)
    tpta_type = st.selectbox("TPTA City Category", ["Higher TPTA (X Class)", "Other Places (Y/Z Class)"])
    inc_month = st.selectbox("Annual Increment Month", [1, 7], format_func=lambda x: "January" if x==1 else "July")

    st.header("4. Promotion / MACP")
    apply_macp = st.checkbox("Apply Expected MACP/Promotion?")
    if apply_macp:
        macp_date = st.date_input("Expected Promotion Date", datetime.date(2028, 8, 10))
        macp_target = st.selectbox("Target Pay Level", levels if levels else ["2"])
        macp_option = st.radio("Pay Fixation Option", ["Date of Promotion", "Date of Next Increment (DNI)"])
    else:
        macp_date, macp_target, macp_option = None, None, None

    st.header("5. Future Pay Commissions")
    cpc_8_fitment = st.number_input("8th CPC Fitment Factor (Jan 2026)", value=2.57, step=0.01)
    cpc_9_fitment = st.number_input("9th CPC Fitment Factor (Jan 2036)", value=2.57, step=0.01)
    cpc_10_fitment = st.number_input("10th CPC Fitment Factor (Jan 2046)", value=2.57, step=0.01)
    
    st.header("6. Retirement Leaves")
    el_credit = st.number_input("Earned Leave (EL) at retirement", value=300, max_value=300)
    hpl_credit = st.number_input("Half Pay Leave (HPL) at retirement", value=120)
    
    if scheme == "OPS":
        commutation_pct = st.slider("Commutation Choice (%)", 0, 40, 40)
    else:
        commutation_pct = 0 

# --- Calculation Engine ---
def simulate():
    records = []
    lvl_num = float(''.join(filter(str.isdigit, current_level))) if current_level else 1
    if lvl_num <= 2: base_tpta = 1350 if "Higher" in tpta_type else 900
    elif 3 <= lvl_num <= 8: base_tpta = 3600 if "Higher" in tpta_type else 1800
    else: base_tpta = 7200 if "Higher" in tpta_type else 3600

    curr_date = datetime.date(sim_start_date.year, sim_start_date.month, 1)
    if curr_date > ret_date:
        st.warning("Retirement date is before the Simulation Start Date!")
        return []

    c_basic, c_level, c_da, c_tpta_base = current_basic, current_level, current_da, base_tpta
    pending_dni, old_level_for_dni, old_basic_for_dni = False, None, None
    is_post_cpc = False 
    running_corpus = current_corpus if scheme in ["NPS", "UPS"] else 0

    while curr_date <= ret_date:
        if curr_date.month == 1 and curr_date.year in [2026, 2036, 2046]:
            fitment = cpc_8_fitment if curr_date.year == 2026 else (cpc_9_fitment if curr_date.year == 2036 else cpc_10_fitment)
            c_basic = round((c_basic * fitment) / 100) * 100
            c_da = 0  
            c_tpta_base = round((c_tpta_base * fitment) / 100) * 100
            is_post_cpc = True

        if curr_date.month in [1, 7] and not (curr_date.month == 1 and curr_date.year in [2026, 2036, 2046]):
            c_da += 2

        if apply_macp and curr_date.year == macp_date.year and curr_date.month == macp_date.month:
            if macp_option == "Date of Promotion":
                if not is_post_cpc:
                    boosted_basic = get_next_cell(c_level, c_basic, 1, matrix_dict)
                    c_level = macp_target
                    c_basic = fit_in_new_level(c_level, boosted_basic, matrix_dict)
                else:
                    c_basic = round((c_basic * 1.03) / 100) * 100 
                    c_level = macp_target 
            else:
                old_level_for_dni, old_basic_for_dni, c_level, pending_dni = c_level, c_basic, macp_target, True
                if not is_post_cpc:
                    c_basic = fit_in_new_level(c_level, c_basic, matrix_dict)

        if curr_date.month == inc_month:
            if pending_dni:
                if not is_post_cpc:
                    boosted_old = get_next_cell(old_level_for_dni, old_basic_for_dni, 2, matrix_dict)
                    c_basic = fit_in_new_level(c_level, boosted_old, matrix_dict)
                else:
                    c_basic = round((old_basic_for_dni * 1.03) / 100) * 100
                    c_basic = round((c_basic * 1.03) / 100) * 100
                pending_dni = False
            else:
                c_basic = get_next_cell(c_level, c_basic, 1, matrix_dict) if not is_post_cpc else round((c_basic * 1.03) / 100) * 100

        da_amt = c_basic * (c_da / 100.0)
        hra_amt = c_basic * (hra_rate / 100.0)
        tpta_amt = c_tpta_base + (c_tpta_base * (c_da / 100.0))
        gross = c_basic + da_amt + hra_amt + tpta_amt

        monthly_nps_addition = 0
        if scheme in ["NPS", "UPS"]:
            monthly_interest = running_corpus * ((nps_return_rate / 100.0) / 12)
            monthly_nps_addition = (c_basic + da_amt) * 0.24 
            running_corpus = running_corpus + monthly_interest + monthly_nps_addition

        records.append({
            "Date": curr_date.strftime("%b %Y"),
            "Level": c_level,
            "Basic": round(c_basic),
            "DA Rate (%)": c_da,
            "DA Amount": round(da_amt),
            "HRA": round(hra_amt),
            "TPTA": round(tpta_amt),
            "Gross Salary": round(gross),
            "Accumulated Corpus": round(running_corpus) if scheme in ["NPS", "UPS"] else 0
        })

        curr_date += relativedelta(months=1)
    return records

# --- Render Output ---
if st.button("Generate Dashboard Projection", type="primary"):
    with st.spinner("Calculating future progression..."):
        projection = simulate()
        
    if projection:
        df_proj = pd.DataFrame(projection)
        
        last_month = projection[-1]
        last_basic = float(last_month["Basic"])
        last_da_amt = float(last_month["DA Amount"])
        last_emoluments = last_basic + last_da_amt
        final_corpus = float(last_month["Accumulated Corpus"])
        
        if len(projection) >= 12:
            avg_12m_basic = sum([p["Basic"] for p in projection[-12:]]) / 12.0
        else:
            avg_12m_basic = last_basic
        
        days_of_service = (ret_date - doj).days
        if days_of_service < 0: days_of_service = 0
        qualifying_half_years = min(math.floor(days_of_service / 182.5), 66)
        
        # --- Dashboard UI ---
        st.subheader(f"📊 Dashboard: {emp_name} ({scheme})")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Final Basic Pay", f"₹ {last_basic:,.0f}")
        m2.metric("Final Gross Salary", f"₹ {last_month['Gross Salary']:,.0f}")
        m3.metric("Final DA Rate", f"{last_month['DA Rate (%)']}%")
        
        if scheme in ["NPS", "UPS"]:
            m4.metric("Final Pension Corpus", f"₹ {final_corpus:,.0f}")
        else:
            m4.metric("Total Months Simulated", len(projection))

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
            if commutation_pct > 0:
                st.error(f"**Commutation Payout (at {commutation_pct}%):** ₹ {commuted_value:,.0f}")
                
        elif scheme == "NPS":
            annuity_amt = final_corpus * 0.40 
            lumpsum_amt = final_corpus * 0.60 
            monthly_pension = (annuity_amt * (annuity_rate/100.0)) / 12
            
            c1.info(f"**Estimated NPS Pension:** ₹ {monthly_pension:,.0f} / month\n\n*(Generated from 40% Annuity)*")
            st.error(f"**NPS Lumpsum Withdrawal (60%):** ₹ {lumpsum_amt:,.0f}")
            
        elif scheme == "UPS":
            assured_pension = avg_12m_basic * 0.50
            ups_lumpsum = last_emoluments * 0.10 * qualifying_half_years
            
            c1.info(f"**UPS Assured Pension:** ₹ {assured_pension:,.0f} / month\n\n*(50% of Last 12 Months Avg Basic)*")
            st.error(f"**UPS Superannuation Lumpsum:** ₹ {ups_lumpsum:,.0f}\n\n*(In addition to Gratuity)*")

        # --- Data & Export Section ---
        st.markdown("---")
        st.subheader("🗓️ Data Output & Export Options")
        
        csv_data = df_proj.to_csv(index=False).encode('utf-8')
        
        # Safe PDF Generation
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, txt=f"Salary & Pension Projection: {emp_name}", ln=True, align='C')
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, txt=f"Scheme: {scheme} | Retirement Date: {ret_date.strftime('%d-%b-%Y')}", ln=True, align='C')
        pdf.cell(0, 10, txt=f"Final Basic: Rs. {last_basic:,.0f} | Final Gross: Rs. {last_month['Gross Salary']:,.0f}", ln=True)
        pdf.cell(0, 10, txt=f"Estimated Gratuity: Rs. {gratuity:,.0f}", ln=True)
        pdf.cell(0, 10, txt=f"Leave Encashment: Rs. {leave_encashment:,.0f}", ln=True)
        
        if scheme == "OPS":
            pdf.cell(0, 10, txt=f"Basic Pension: Rs. {basic_pension:,.0f} / month", ln=True)
        elif scheme == "NPS":
            pdf.cell(0, 10, txt=f"Final Corpus: Rs. {final_corpus:,.0f}", ln=True)
            pdf.cell(0, 10, txt=f"Est. Pension: Rs. {monthly_pension:,.0f} / month", ln=True)
        elif scheme == "UPS":
            pdf.cell(0, 10, txt=f"Assured Pension: Rs. {assured_pension:,.0f} / month", ln=True)
            pdf.cell(0, 10, txt=f"UPS Lumpsum: Rs. {ups_lumpsum:,.0f}", ln=True)

        # Draw the table inside the PDF
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, txt="Month-by-Month Projection Data", ln=True, align='C')
        pdf.set_font("Arial", 'B', 9)
        
        # Configure columns based on Scheme
        if scheme in ["NPS", "UPS"]:
            cols = ["Date", "Level", "Basic", "DA %", "DA Amt", "Gross", "Corpus"]
            col_widths = [25, 15, 25, 15, 25, 30, 35] # Total width approx 170
        else:
            cols = ["Date", "Level", "Basic", "DA %", "DA Amt", "HRA", "Gross"]
            col_widths = [30, 20, 25, 20, 25, 25, 30]

        for i, header in enumerate(cols):
            pdf.cell(col_widths[i], 10, txt=header, border=1, align='C')
        pdf.ln()
        
        pdf.set_font("Arial", '', 8)
        for row in projection:
            pdf.cell(col_widths[0], 8, txt=str(row['Date']), border=1, align='C')
            pdf.cell(col_widths[1], 8, txt=str(row['Level']), border=1, align='C')
            pdf.cell(col_widths[2], 8, txt=str(row['Basic']), border=1, align='C')
            pdf.cell(col_widths[3], 8, txt=str(row['DA Rate (%)']), border=1, align='C')
            pdf.cell(col_widths[4], 8, txt=str(row['DA Amount']), border=1, align='C')
            
            if scheme in ["NPS", "UPS"]:
                pdf.cell(col_widths[5], 8, txt=str(row['Gross Salary']), border=1, align='C')
                pdf.cell(col_widths[6], 8, txt=str(row['Accumulated Corpus']), border=1, align='C')
            else:
                pdf.cell(col_widths[5], 8, txt=str(row['HRA']), border=1, align='C')
                pdf.cell(col_widths[6], 8, txt=str(row['Gross Salary']), border=1, align='C')
            pdf.ln()

        # Fix for the Byte Array Crash
        pdf_out = pdf.output(dest='S')
        pdf_bytes = pdf_out.encode('latin1') if isinstance(pdf_out, str) else bytes(pdf_out)
        
        e1, e2 = st.columns(2)
        e1.download_button("📥 Download as CSV (Excel)", data=csv_data, file_name="Projection_Data.csv", mime="text/csv")
        e2.download_button("🖨️ Export Summary & Table as PDF", data=pdf_bytes, file_name="Retirement_Summary.pdf", mime="application/pdf")
        
        # Display table on the webpage (This will now appear!)
        st.dataframe(df_proj, use_container_width=True, height=400)
