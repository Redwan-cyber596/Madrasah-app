import os
import json
import pandas as pd
from datetime import datetime
import streamlit as st

# পেজ কনফিগারেশন (ওয়েব অ্যাপের টাইটেল ও লেআউট)
st.set_page_config(
    page_title="আল জামিয়াতুল ইসলামিয়া মদীনাতুল উলূম জামতলা মাদরাসা",
    page_icon="🕌",
    layout="wide"
)

# বাংলা ফন্ট (SolaimanLipi) সুন্দর করার জন্য CSS কোড
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;600;700&display=swap');
    
    html, body, [data-testid="stSidebar"], .stMarkdown, p, h1, h2, h3, h4, h5, h6, label, input, select {
        font-family: 'SolaimanLipi', 'Hind Siliguri', sans-serif !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

DB_FILE = "madrasah_database.json"

# খানা নম্বরের জন্য স্ট্রিমলিট মেমোরি বা সেশন স্টেট সেটআপ
if 'khana_input' not in st.session_state:
    st.session_state.khana_input = ""  # শুরুতে খালি থাকবে

# ====== ডাটাবেজ লোড ও সেভ ফাংশন ======
def load_database():
    if "payment_records" not in st.session_state:
        st.session_state.payment_records = []
    if "student_database" not in st.session_state:
        st.session_state.student_database = {}

    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                st.session_state.payment_records = data.get("payments", [])
                saved_students = data.get("students", {})
                for cls, rows in saved_students.items():
                    st.session_state.student_database[cls] = pd.DataFrame(rows)
        except Exception as e:
            st.error(f"ডাটাবেজ লোড করতে সমস্যা হয়েছে: {e}")

def save_database():
    try:
        serializable_students = {}
        for cls, df in st.session_state.student_database.items():
            serializable_students[cls] = df.to_dict(orient="records")
            
        data = {
            "payments": st.session_state.payment_records,
            "students": serializable_students
        }
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"ডাটাবেজ সেভ করতে সমস্যা হয়েছে: {e}")

def clean_num(val):
    bangla_digits = {'০':'0','১':'1','২':'2','৩':'3','৪':'4','৫':'5','৬':'6','৭':'7','৮':'8','৯':'9'}
    s = str(val).strip()
    for b, e in bangla_digits.items():
        s = s.replace(b, e)
    try:
        return str(int(float(s)))
    except:
        return s

# ডাটাবেজ ইনিশিয়ালাইজেশন
load_database()

# ====== হেডার সেকশন ======
st.markdown("<h1 style='text-align: center; color: #0f172a;'>আল জামিয়াতুল ইসলামিয়া মদীনাতুল উলূম জামতলা মাদরাসা</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #475569; font-style: italic;'>পীরগঞ্জ, রংপুর — ডিজিটাল ক্লাউড ম্যানেজমেন্ট সিস্টেম</p>", unsafe_allow_html=True)
st.markdown("---")

# ====== নেভিগেশন মেনু (ট্যাব সিস্টেম) ======
tab_home, tab_payment, tab_student, tab_report = st.tabs([
    "🏠 মাসিক ফি আদায় প্যানেল", 
    "📝 ফি প্রদান লেজার", 
    "👥 ছাত্র তালিকা ডাটাবেজ", 
    "📊 আর্থিক খতিয়ান রিপোর্ট"
])

classes = list(st.session_state.student_database.keys()) if st.session_state.student_database else ["কোনো জামাত নেই"]
months = ["জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল", "মে", "জুন", "জুলাই", "আগস্ট", "সেপ্টেম্বর", "অক্টোবর", "নভেম্বর", "ডিসেম্বর"]

# ==========================================
# ১. হোম প্যানেল (ফি আদায়)
# ==========================================
with tab_home:
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.subheader("অনুসন্ধান ফিল্টার")
        selected_class = st.selectbox("জামাআত নির্বাচন করুন", classes, key="home_class")
        
        khana_entry = st.text_input("খানা নম্বর লিখুন", value=st.session_state.khana_input, key="khana_field_unique")
        
        student_found = None
        if khana_entry:
            khana_clean = clean_num(khana_entry)
            if selected_class in st.session_state.student_database:
                df = st.session_state.student_database[selected_class]
                khana_col = [c for c in df.columns if 'খানা' in str(c)]
                if khana_col:
                    res = df[df[khana_col[0]].apply(clean_num) == khana_clean]
                    if not res.empty:
                        student_found = res.iloc[0]
                    else:
                        st.info("এই খানা নম্বরের কোনো ছাত্র পাওয়া যায়নি।")
    
    with col_right:
        st.subheader(f"ফি এন্ট্রি ফর্ম — {selected_class}")
        
        # ছাত্রের ডিটেইলস লোড করা
        name_val = ""
        father_val = ""
        fee_val = 0
        prev_due_val = 0
        
        if student_found is not None:
            df = st.session_state.student_database[selected_class]
            name_col = [c for c in df.columns if 'নাম' in str(c)][0] if [c for c in df.columns if 'নাম' in str(c)] else 'নাম'
            father_col = [c for c in df.columns if 'পিতা' in str(c) or 'pita' in str(c).lower()]
            father_col = father_col[0] if father_col else 'পিতা'
            fee_col = [c for c in df.columns if 'ফি' in str(c)]
            fee_col = fee_col[0] if fee_col else 'নির্ধারিত ফি'
            
            name_val = str(student_found.get(name_col, ''))
            father_val = str(student_found.get(father_col, ''))
            fee_val = int(clean_num(student_found.get(fee_col, 0)))
            
            # পূর্ব বকেয়া হিসাব (নিরাপদ লুপ)
            for rec in st.session_state.payment_records:
                if isinstance(rec, dict):
                    if rec.get("জামাআত") == selected_class and clean_num(rec.get("খানা নং", "")) == clean_num(khana_entry):
                        try: prev_due_val += int(clean_num(rec.get("বকেয়া", 0)))
                        except: pass

        # ডিসপ্লে ফিল্ড (Read-only এর মতো দেখানোর জন্য)
        st.text_input("ছাত্রের নাম", value=name_val, disabled=True)
        st.text_input("পিতার নাম", value=father_val, disabled=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.number_input("নির্ধারিত ফি", value=fee_val, disabled=True)
        with c2:
            st.number_input("পূর্ব বকেয়া", value=prev_due_val, disabled=True)
            
        st.markdown("### আদায় ইনপুট")
        c3, c4 = st.columns(2)
        with c3:
            selected_month = st.selectbox("মাস", months, index=datetime.now().month - 1)
        with c4:
            payment_date = st.text_input("তারিখ", value=datetime.now().strftime("%d-%m-%Y"))
            
        c5, c6 = st.columns(2)
        with c5:
            paid_amount = st.number_input("ফি প্রদান (টাকা)", min_value=0, step=10, key="paid_input")
        with c6:
            receipt_no = st.text_input("রশিদ নং")
            
        # লাইভ বকেয়া হিসাব
        current_due = fee_val - paid_amount
        if current_due < 0: current_due = 0
        total_ledger_due = prev_due_val + current_due
        
        st.warning(f"চলতি মাসের বকেয়া: {current_due} /- | মোট লেজার বকেয়া: {total_ledger_due} /-")
        
        if st.button("দাখিল করুন (Submit)", type="primary", use_container_width=True):
            if not khana_entry or not name_val:
                st.error("অনুগ্রহ করে খানা নম্বর দিয়ে ছাত্র সার্চ করুন!")
            else:
                khana_clean = clean_num(khana_entry)
                
                # পুরাতন ডুপ্লিকেট রেকর্ড রিমুভ করা (নিরাপদ ফিল্টারিং)
                st.session_state.payment_records = [
                    r for r in st.session_state.payment_records 
                    if isinstance(r, dict) and not (r.get("জামাআত") == selected_class and clean_num(r.get("খানা নং", "")) == khana_clean and r.get("মাস") == selected_month)
                ]
                
                # নতুন রেকর্ড যুক্ত করা
                record = {
                    "জاماআত": selected_class,
                    "খানা নং": khana_entry,
                    "নাম": name_val,
                    "পিতা": father_val,
                    "মাস": selected_month,
                    "তারিখ": payment_date,
                    "ফি প্রদান": str(paid_amount),
                    "বকেয়া": str(total_ledger_due),
                    "রшив নং": receipt_no
                }
                st.session_state.payment_records.append(record)
                save_database()
                
                # সফলভাবে সেভ হওয়ার পর পরবর্তী খানা নম্বর সেট করা
                try:
                    next_khana = int(khana_clean) + 1
                    st.session_state.khana_input = str(next_khana)
                except:
                    st.session_state.khana_input = ""
                    
                st.rerun()

# ==========================================
# ২. ফি প্রদান লেজার ও বাল্ক আপলোড
# ==========================================
with tab_payment:
    st.subheader("বাল্ক পেমেন্ট এক্সেল ফাইল আপলোড")
    uploaded_pay_file = st.file_uploader("এখানে এক্সেল ফাইলটি ড্রপ করুন বা আপলোড করতে ক্লিক করুন", type=["xlsx", "xls"], key="pay_upload")
    
    c1, c2 = st.columns(2)
    with c1:
        pay_filter_month = st.selectbox("মাস ফিল্টার", months, index=datetime.now().month - 1)
    with c2:
        pay_filter_class = st.selectbox("জামাআত ফিল্টার", classes)
        
    if uploaded_pay_file and pay_filter_class != "কোনো জামাত নেই":
        if st.button("এক্সেল ডাটা ডাটাবেজে যুক্ত করুন"):
            try:
                df_pay = pd.read_excel(uploaded_pay_file)
                df_pay.columns = df_pay.columns.astype(str).str.strip()
                name_col = [col for col in df_pay.columns if 'নাম' in str(col)][0] if [col for col in df_pay.columns if 'নাম' in str(col)] else 'নাম'
                khana_col = [col for col in df_pay.columns if 'খানা' in str(col)][0] if [col for col in df_pay.columns if 'খানা' in str(col)] else 'খানা নং'
                paid_col = [col for col in df_pay.columns if 'প্রদান' in str(col) or 'paid' in str(col).lower()][0] if [col for col in df_pay.columns if 'প্রদান' in str(col) or 'paid' in str(col).lower()] else 'ফি প্রদান'
                due_col = [col for col in df_pay.columns if 'বকেয়া' in str(col) or 'due' in str(col).lower()][0] if [col for col in df_pay.columns if 'বকেয়া' in str(col) or 'due' in str(col).lower()] else 'বকেয়া'
                
                count = 0
                for _, row in df_pay.iterrows():
                    if pd.notna(row.get(name_col)):
                        k_clean = clean_num(row.get(khana_col, ""))
                        st.session_state.payment_records = [r for r in st.session_state.payment_records if isinstance(r, dict) and not (r.get("জاماআত") == pay_filter_class and clean_num(r.get("খানা নং", "")) == k_clean and r.get("মাস") == pay_filter_month)]
                        
                        st.session_state.payment_records.append({
                            "জاماআত": pay_filter_class, "খানা নং": k_clean, "নাম": str(row.get(name_col, "")),
                            "পিতা": str(row.get('পিতা', '')), "মাস": pay_filter_month, "তারিখ": datetime.now().strftime("%d-%m-%Y"),
                            "ফি প্রদান": clean_num(row.get(paid_col, "0")), "বকেয়া": clean_num(row.get(due_col, "0")), "রшив নং": ""
                        })
                        count += 1
                save_database()
                st.success(f"সফলভাবে {count} জনের তথ্য আপলোড হয়েছে!")
                st.rerun()
            except Exception as e:
                st.error(f"ফাইল প্রসেস করতে সমস্যা হয়েছে: {e}")

    # ফিল্টারিং ও লেজার টেবিল প্রদর্শন
    report_list = [r for r in st.session_state.payment_records if isinstance(r, dict) and r.get("জاماআত") == pay_filter_class and r.get("মাস") == pay_filter_month]
    if report_list:
        df_report = pd.DataFrame(report_list)[["খানা নং", "নাম", "পিতা", "তারিখ", "ফি প্রদান", "বকেয়া", "রшив নং"]]
        st.dataframe(df_report, use_container_width=True)
        
        # রিপোর্ট ফাইল তৈরি
        df_report.to_excel("madrasah_report.xlsx", index=False, header=True)
        st.download_button("এক্সেল ফাইল ডাউনলোড করুন 📥", data=df_report.to_csv(index=False).encode('utf-8'), file_name=f"{pay_filter_class}_{pay_filter_month}.csv", mime="text/csv")
    else:
        st.info("এই ফিল্টারে কোনো ডাটা পাওয়া যায়নি।")

# ==========================================
# ৩. ছাত্র তালিকা ডাটাবেজ
# ==========================================
with tab_student:
    st.subheader("নতুন জামাআতের ছাত্র তালিকা এক্সেল আপলোড")
    uploaded_student_file = st.file_uploader("ছাত্র তালিকা এক্সেল ফাইল (.xlsx)", type=["xlsx", "xls"])
    
    if uploaded_student_file:
        jamator_name = os.path.splitext(uploaded_student_file.name)[0]
        if st.button(f"'{jamator_name}' জামাআত হিসেবে ডাটাবেজে সেভ করুন"):
            try:
                df_st = pd.read_excel(uploaded_student_file)
                df_st.columns = df_st.columns.astype(str).str.strip()
                st.session_state.student_database[jamator_name] = df_st
                save_database()
                st.success(f"'{jamator_name}' জামাআতের তালিকা সফলভাবে সেভ হয়েছে!")
                st.rerun()
            except Exception as e:
                st.error(f"ত্রুটি: {e}")
                
    st.markdown("---")
    view_class = st.selectbox("জামাআত তালিকা দেখুন", classes, key="view_st_class")
    
    if view_class in st.session_state.student_database:
        df_display = st.session_state.student_database[view_class]
        st.dataframe(df_display, use_container_width=True)
        
        html_rows = ""
        for idx, row in df_display.iterrows():
            html_rows += f"<tr><td>{idx+1}</td><td>{str(row.get('খানা নং','')).split('.')[0]}</td><td>{row.get('নাম','')}</td><td>{row.get('পিতা','')}</td></tr>"
            
        print_html = f"""
        <html><head><meta charset='utf-8'><style>
        body {{ font-family: Arial, sans-serif; padding: 20px; }}
        table {{ width:100%; border-collapse:collapse; }} th, td {{ border:1px solid #000; padding:8px; text-align:left; }}
        </style></head><body>
        <h2>মাদরাসা ছাত্র তালিকা রিপোর্ট - জামাআত: {view_class}</h2>
        <table><tr><th>ক্রঃ</th><th>খানা নং</th><th>নাম</th><th>পিতার নাম</th></tr>{html_rows}</table>
        <script>window.print();</script>
        </body></html>
        """
        st.download_button("রিপোর্ট প্রিন্ট এইচটিএমএল ডাউনলোড 📄", data=print_html, file_name=f"{view_class}_list.html", mime="text/html")

# ==========================================
# ৪. হিসাব খতিয়ান ও রিপোর্ট
# ==========================================
with tab_report:
    c1, c2 = st.columns(2)
    with c1:
        rep_month = st.selectbox("মাস খতিয়ান", months, index=datetime.now().month - 1, key="rep_m")
    with c2:
        rep_class = st.selectbox("জামাআত খতিয়ান", classes, key="rep_c")
        
    total_target_fee = 0
    if rep_class in st.session_state.student_database:
        df = st.session_state.student_database[rep_class]
        fee_col = [col for col in df.columns if 'ফি' in str(col)]
        fee_col = fee_col[0] if fee_col else None
        name_col = [col for col in df.columns if 'নাম' in str(col)][0] if [col for col in df.columns if 'নাম' in str(col)] else 'নাম'
        if fee_col:
            for _, row in df.iterrows():
                if pd.notna(row.get(name_col)):
                    try: total_target_fee += int(float(clean_num(row.get(fee_col, 0))))
                    except: pass
                    
    total_paid, total_due = 0, 0
    for r in st.session_state.payment_records:
        if isinstance(r, dict) and r.get("জاماআত") == rep_class and r.get("মাস") == rep_month:
            try: total_paid += int(clean_num(r.get("ফি প্রদান", 0)))
            except: pass
            try: total_due += int(clean_num(r.get("বকেয়া", 0)))
            except: pass
            
    m1, m2, m3 = st.columns(3)
    m1.metric(label="মোট নির্ধারিত ফি", value=f"{total_target_fee} /- টাকা")
    m2.metric(label="মোট আদায়কৃত ফি", value=f"{total_paid} /- টাকা")
    m3.metric(label="মোট বকেয়া পরিমাণ", value=f"{total_due} /- টাকা")
    
    report_html = f"""
    <html><head><meta charset='utf-8'><style>
    body {{ font-family: Arial, sans-serif; padding: 40px; text-align: center; }}
    .box {{ border: 2px solid #000; padding: 20px; border-radius: 10px; max-width: 500px; margin: auto; text-align: left; }}
    </style></head><body>
    <div class='box'>
        <h2>মাসিক আর্থিক খতিয়ান রিপোর্ট</h2>
        <p><b>জاماআত:</b> {rep_class} | <b>মাস:</b> {rep_month}</p><hr>
        <p style='color:blue;'><b>মোট নির্ধারিত ফি:</b> {total_target_fee} টাকা</p>
        <p style='color:green;'><b>মোট আদায়কৃত ফি:</b> {total_paid} টাকা</p>
        <p style='color:red;'><b>মোট বকেয়া:</b> {total_due} টাকা</p>
    </div>
    <script>window.print();</script>
    </body></html>
    """
    st.download_button("হিসাব খতিয়ান প্রিন্ট ফাইল 📄", data=report_html, file_name=f"Report_{rep_class}_{rep_month}.html", mime="text/html")
