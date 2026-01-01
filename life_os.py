import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import jdatetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from streamlit_nej_datepicker import datepicker_component, Config

# --- تنظیمات صفحه ---
st.set_page_config(page_title="Life OS", layout="wide", page_icon="💎")

# --- استایل CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@100;300;400;500;600;700;800;900&display=swap');
    html, body, [class*="css"] { font-family: 'Vazirmatn', sans-serif !important; direction: rtl; text-align: right; }
    input, textarea, select, div[data-baseweb="select"] { font-family: 'Vazirmatn', sans-serif !important; direction: rtl; text-align: right; }
    h1, h2, h3, h4, h5, h6, p, label { font-family: 'Vazirmatn', sans-serif !important; text-align: right; direction: rtl; }
    .stButton > button { font-family: 'Vazirmatn', sans-serif !important; font-weight: bold; }
    [data-testid="stSidebarCollapseButton"] *, [data-testid="stSidebarExpandButton"] * { font-family: 'Material Symbols Rounded', sans-serif !important; direction: ltr !important; }
    div[data-testid="stMetricValue"] { font-family: 'Vazirmatn', sans-serif !important; direction: ltr !important; text-align: right; }
    .main .block-container, section[data-testid="stSidebar"] { direction: rtl; text-align: right; }
    div[data-testid="stDataFrame"] { direction: rtl; text-align: right; font-family: 'Vazirmatn', sans-serif; }
    div[data-testid="stMetric"] { background-color: #1E1E1E; border: 1px solid #333; border-radius: 12px; padding: 15px; }
    div[data-testid="stSlider"], div[data-testid="stSelectSlider"] { direction: ltr !important; }
    div[data-testid="stSlider"] > label, div[data-testid="stSelectSlider"] > label { direction: rtl !important; text-align: right !important; width: 100%; display: flex; justify-content: flex-end; }
    div[data-testid="stSliderTickBarMin"], div[data-testid="stSliderTickBarMax"] { font-family: 'Vazirmatn', sans-serif !important; }
    .user-card { background-color: #262730; padding: 20px; border-radius: 15px; border: 2px solid #444; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    .level-badge { font-size: 28px; font-weight: 800; color: #FFD700; }
    .xp-stats { font-size: 14px; color: #aaa; margin-top: 5px; font-family: 'Vazirmatn', sans-serif !important; }
    .stApp { overflow-x: hidden; }
</style>
""", unsafe_allow_html=True)

# --- اتصال به گوگل شیت ---
# کش کردن اتصال برای سرعت بیشتر
@st.cache_resource
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # خواندن اطلاعات اکانت از Secrets استریم‌لیت
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

def get_worksheet(sheet_name):
    """گرفتن ورک‌شیت خاص، اگر نباشد می‌سازد"""
    client = get_gspread_client()
    try:
        sh = client.open("Life-OS-DB") # اسم شیت اصلی باید دقیقاً این باشد
    except gspread.SpreadsheetNotFound:
        st.error("فایل گوگل شیت 'Life-OS-DB' پیدا نشد. لطفاً بسازید و به ربات دسترسی بدهید.")
        st.stop()
        
    try:
        worksheet = sh.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        # ساخت تب جدید با هدرهای مناسب
        worksheet = sh.add_worksheet(title=sheet_name, rows=100, cols=10)
        headers = {
            "finance": ["date", "type", "amount", "category", "description"],
            "trading": ["date", "pair", "direction", "result", "pnl", "notes"],
            "investments": ["date", "asset_name", "type", "amount_toman", "quantity", "notes"],
            "workouts": ["date", "muscle", "duration", "intensity", "notes"],
            "habits": ["date", "habit_name", "status"]
        }
        if sheet_name in headers:
            worksheet.append_row(headers[sheet_name])
            
    return worksheet

# --- توابع دیتابیس (جایگزین شده با GSheet) ---
def add_finance(date, type_, amount, category, desc):
    ws = get_worksheet("finance")
    ws.append_row([date, type_, amount, category, desc])

def add_trade(date, pair, direction, result, pnl, notes):
    ws = get_worksheet("trading")
    ws.append_row([date, pair, direction, result, pnl, notes])

def add_investment(date, asset_name, type_, amount_toman, quantity, notes):
    ws = get_worksheet("investments")
    ws.append_row([date, asset_name, type_, amount_toman, quantity, notes])

def add_workout(date, muscle, duration, intensity, notes):
    ws = get_worksheet("workouts")
    ws.append_row([date, muscle, duration, intensity, notes])

def toggle_habit(date, habit_name, is_checked):
    ws = get_worksheet("habits")
    status = 1 if is_checked else 0
    
    # جستجو برای آپدیت یا ایجاد (کمی کند است اما دقیق)
    data = ws.get_all_records()
    cell = ws.find(date) # جستجوی تاریخ
    
    # منطق ساده‌تر برای عادت‌ها: فقط اضافه می‌کنیم، آخرین وضعیت معتبر است
    # برای جلوگیری از پیچیدگی API، هر تغییر را به عنوان ردیف جدید ثبت می‌کنیم
    # و موقع خواندن آخرین رکورد را می‌گیریم.
    ws.append_row([date, habit_name, status])

def load_data(table_name):
    ws = get_worksheet(table_name)
    data = ws.get_all_records()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    
    # تبدیل ستون‌های عددی (چون شیت همه چیز را رشته می‌دهد)
    if 'amount' in df.columns: df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
    if 'pnl' in df.columns: df['pnl'] = pd.to_numeric(df['pnl'], errors='coerce').fillna(0)
    if 'amount_toman' in df.columns: df['amount_toman'] = pd.to_numeric(df['amount_toman'], errors='coerce').fillna(0)
    if 'quantity' in df.columns: df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0)
    
    return df

def get_habit_status(date, habit_name):
    ws = get_worksheet("habits")
    # گرفتن تمام داده‌ها و فیلتر کردن در پایتون (سریع‌تر از درخواست‌های مکرر API)
    data = ws.get_all_records()
    if not data: return False
    
    df = pd.DataFrame(data)
    # فیلتر کردن
    filtered = df[(df['date'] == date) & (df['habit_name'] == habit_name)]
    if not filtered.empty:
        # آخرین وضعیت ثبت شده
        last_status = filtered.iloc[-1]['status']
        return True if str(last_status) == "1" else False
    return False

def calculate_xp():
    # شمارش تعداد ردیف‌ها منهای هدر
    try:
        h_score = (len(get_worksheet("habits").get_all_values()) - 1) * 10
        w_score = (len(get_worksheet("workouts").get_all_values()) - 1) * 50
        t_score = (len(get_worksheet("trading").get_all_values()) - 1) * 30
        f_score = (len(get_worksheet("finance").get_all_values()) - 1) * 15
    except:
        return 1, 0, 0, 500
    
    total_xp = h_score + w_score + t_score + f_score
    if total_xp < 0: total_xp = 0
    
    level = int(total_xp / 500) + 1
    xp_in_current_level = total_xp % 500
    progress = xp_in_current_level / 500
    return level, total_xp, progress, (500 - xp_in_current_level)

# --- تابع کمکی انتخاب‌گر تاریخ ---
def native_shamsi_datepicker(key_prefix):
    today = jdatetime.date.today()
    c_year, c_month, c_day = st.columns([1.3, 1.5, 1])
    with c_year:
        years = list(range(1400, 1411))
        try: default_idx = years.index(today.year)
        except: default_idx = 0
        year = st.selectbox("سال", years, index=default_idx, key=f"{key_prefix}_y")
    with c_month:
        months = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
        default_month_idx = today.month - 1
        month_name = st.selectbox("ماه", months, index=default_month_idx, key=f"{key_prefix}_m")
        month_num = months.index(month_name) + 1
    with c_day:
        days = list(range(1, 32))
        default_day_idx = today.day - 1
        day = st.selectbox("روز", days, index=default_day_idx, key=f"{key_prefix}_d")
    return f"{year}/{month_num:02d}/{day:02d}"

# --- رابط کاربری (Frontend) ---

# چک کردن اتصال در ابتدای کار
try:
    level, total_xp, progress_val, xp_needed = calculate_xp()
except Exception as e:
    st.warning("در حال اتصال به دیتابیس... (اگر اولین بار است، لطفاً صبر کنید)")
    level, total_xp, progress_val, xp_needed = 1, 0, 0, 500

st.sidebar.markdown(f"""
<div class="user-card">
    <div style="font-size: 40px; margin-bottom: 10px;">🤴</div>
    <div class="level-badge">Level {level}</div>
    <div class="xp-stats">مجموع امتیاز: {total_xp} XP</div>
</div>
""", unsafe_allow_html=True)
st.sidebar.write(f"🚀 تا لول بعدی: {xp_needed} XP")
st.sidebar.progress(progress_val)
st.sidebar.markdown("---")

menu = st.sidebar.radio("منوی دسترسی", ["داشبورد مدیریت", "کیف پول (ریالی)", "پراپ تریدینگ (دلاری)", "سرمایه‌گذاری (Gold/Crypto)", "باشگاه و عادت‌ها"])

# --- 1. داشبورد ---
if menu == "داشبورد مدیریت":
    st.markdown("### 📊 نمای کلی وضعیت")
    
    df_fin = load_data("finance")
    df_trade = load_data("trading")
    df_invest = load_data("investments")

    total_income = df_fin[df_fin['type'] == 'درآمد']['amount'].sum() if not df_fin.empty else 0
    total_expense = df_fin[df_fin['type'] == 'هزینه']['amount'].sum() if not df_fin.empty else 0
    wallet_balance = total_income - total_expense
    
    invest_buy = df_invest[df_invest['type'] == 'خرید']['amount_toman'].sum() if not df_invest.empty else 0
    invest_sell = df_invest[df_invest['type'] == 'فروش']['amount_toman'].sum() if not df_invest.empty else 0
    total_invested = invest_buy - invest_sell
    
    total_net_worth = wallet_balance + total_invested
    trading_pnl = df_trade['pnl'].sum() if not df_trade.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("کل دارایی (تومان)", f"{total_net_worth:,.0f}")
    c2.metric("موجودی نقد", f"{wallet_balance:,.0f}")
    c3.metric("ارزش سرمایه‌گذاری", f"{total_invested:,.0f}")
    c4.metric("سود پراپ ($)", f"{trading_pnl}$")
    
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### 💸 نمودار مخارج")
        if not df_fin.empty:
            expenses = df_fin[df_fin['type'] == 'هزینه']
            if not expenses.empty:
                fig_exp = px.pie(expenses, values='amount', names='category', hole=0.5, color_discrete_sequence=px.colors.sequential.RdBu)
                st.plotly_chart(fig_exp, use_container_width=True)
            else:
                st.info("داده‌ای برای مخارج وجود ندارد.")
    
    with col2:
        st.markdown("##### 📈 رشد حساب ترید")
        if not df_trade.empty:
            df_trade_sorted = df_trade.sort_values(by='date')
            df_trade_sorted['cumulative_pnl'] = df_trade_sorted['pnl'].cumsum()
            fig_trade = px.line(df_trade_sorted, x='date', y='cumulative_pnl', markers=True)
            fig_trade.update_traces(line_color='#00e676' if trading_pnl >= 0 else '#ff1744')
            st.plotly_chart(fig_trade, use_container_width=True)
        else:
            st.info("داده‌ای برای ترید وجود ندارد.")

# --- 2. کیف پول ---
elif menu == "کیف پول (ریالی)":
    st.markdown("### 💰 ثبت تراکنش‌های مالی")
    with st.expander("➕ افزودن تراکنش جدید", expanded=True):
        with st.form("fin_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                final_date = native_shamsi_datepicker("fin")
            
            d_type = c2.selectbox("نوع تراکنش", ["هزینه", "درآمد"])
            d_cat = c3.selectbox("دسته‌بندی", ["حقوق", "اجاره/قسط", "مواد غذایی", "رفت و آمد", "مکمل ورزشی", "پوشاک", "سایر"])
            c4, c5 = st.columns(2)
            d_amount = c4.number_input("مبلغ (تومان)", step=10000.0, format="%.0f")
            d_desc = c5.text_input("توضیحات تراکنش")
            
            if st.form_submit_button("ثبت در سیستم (+15 XP)"):
                add_finance(final_date, d_type, d_amount, d_cat, d_desc)
                st.success(f"تراکنش ثبت شد! امتیاز گرفتی 🪙")
                st.cache_resource.clear() # پاک کردن کش برای آپدیت شدن داده‌ها
                st.rerun()
    
    st.markdown("##### تاریخچه تراکنش‌ها")
    df = load_data("finance")
    if not df.empty:
        df = df.sort_values(by='date', ascending=False)
        df = df.rename(columns={'date': 'تاریخ', 'type': 'نوع', 'amount': 'مبلغ', 'category': 'دسته‌بندی', 'description': 'توضیحات'})
        st.dataframe(df, use_container_width=True, hide_index=True)

# --- 3. پراپ تریدینگ ---
elif menu == "پراپ تریدینگ (دلاری)":
    st.markdown("### 📈 ژورنال معاملاتی پراپ")
    with st.expander("➕ ثبت ترید", expanded=True):
        with st.form("trade_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                final_date = native_shamsi_datepicker("trade")
                
            t_pair = c2.text_input("نماد (Symbol)", value="XAUUSD")
            t_dir = c3.selectbox("جهت", ["Long", "Short"])
            c4, c5, c6 = st.columns(3)
            t_res = c4.selectbox("نتیجه", ["Win", "Loss", "BE"])
            t_pnl = c5.number_input("سود/ضرر ($)", step=0.1)
            t_note = c6.text_input("یادداشت/استراتژی")
            if st.form_submit_button("ثبت ترید (+30 XP)"):
                add_trade(final_date, t_pair, t_dir, t_res, t_pnl, t_note)
                st.success("ترید ثبت شد! برو لول بعد 🔥")
                st.cache_resource.clear()
                st.rerun()
    
    st.markdown("##### عملکرد اخیر")
    df_t = load_data("trading")
    if not df_t.empty:
        df_t = df_t.sort_values(by='date', ascending=False)
        df_t = df_t.rename(columns={'date': 'تاریخ', 'pair': 'نماد', 'direction': 'جهت', 'result': 'نتیجه', 'pnl': 'سود/ضرر', 'notes': 'یادداشت'})
        st.dataframe(df_t, use_container_width=True, hide_index=True)

# --- 4. سرمایه‌گذاری ---
elif menu == "سرمایه‌گذاری (Gold/Crypto)":
    st.markdown("### 🏦 صندوق سرمایه‌گذاری (Asset Box)")
    with st.expander("➕ خرید/فروش دارایی", expanded=True):
        with st.form("invest_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                final_date = native_shamsi_datepicker("inv")
                
            i_asset = c2.text_input("نام دارایی (مثلا: طلای آب‌شده)")
            i_type = c3.selectbox("عملیات", ["خرید", "فروش"])
            c4, c5 = st.columns(2)
            i_amount = c4.number_input("مبلغ کل (تومان)", step=100000.0, format="%.0f")
            i_qty = c5.number_input("مقدار (گرم/تعداد)", step=0.01, format="%.3f")
            i_note = st.text_input("توضیحات")
            if st.form_submit_button("ثبت"):
                add_investment(final_date, i_asset, i_type, i_amount, i_qty, i_note)
                st.success("سرمایه‌گذاری ثبت شد! 💎")
                st.cache_resource.clear()
                st.rerun()

    df_inv = load_data("investments")
    if not df_inv.empty:
        st.markdown("##### موجودی پرتفوی")
        assets = df_inv['asset_name'].unique()
        cols = st.columns(len(assets) if len(assets) > 0 else 1)
        for idx, asset in enumerate(assets):
            df_asset = df_inv[df_inv['asset_name'] == asset]
            bought = df_asset[df_asset['type']=='خرید']['quantity'].sum()
            sold = df_asset[df_asset['type']=='فروش']['quantity'].sum()
            current = bought - sold
            with cols[idx % 4]:
                st.metric(label=asset, value=f"{current} واحد")
        
        st.markdown("---")
        st.markdown("##### ریز تراکنش‌ها")
        df_inv_show = df_inv.sort_values(by='date', ascending=False).rename(columns={'date': 'تاریخ', 'asset_name': 'نام دارایی', 'type': 'نوع', 'amount_toman': 'مبلغ کل', 'quantity': 'تعداد/مقدار', 'notes': 'توضیحات'})
        st.dataframe(df_inv_show, use_container_width=True, hide_index=True)

# --- 5. باشگاه ---
elif menu == "باشگاه و عادت‌ها":
    st.markdown("### 💪 سیستم‌سازی بدن و ذهن")
    
    today_shamsi_obj = jdatetime.date.today()
    today_str = today_shamsi_obj.strftime("%Y/%m/%d")
    
    st.markdown(f"##### 🦁 چک‌لیست روزانه ({today_str})")
    
    habits = ["🐍 پایتون (CS50)", "💊 کراتین/وی", "💧 ۳ لیتر آب", "🧘‍♂️ مدیتیشن"]
    cols = st.columns(4)
    for i, h in enumerate(habits):
        done = get_habit_status(today_str, h)
        if cols[i].checkbox(h, value=done, key=h):
            if not done: 
                toggle_habit(today_str, h, True)
                st.toast(f"ایول! {h} انجام شد. (+10 XP)")
                st.cache_resource.clear()
                st.rerun()
        else:
            if done: 
                toggle_habit(today_str, h, False)
                st.cache_resource.clear()
                st.rerun()

    st.markdown("---")
    st.markdown("##### 🏋️ لاگ تمرین")
    with st.expander("➕ ثبت جلسه تمرینی", expanded=True):
        with st.form("gym"):
            c1, c2 = st.columns(2)
            with c1:
                final_date = native_shamsi_datepicker("gym")
                
            w_mus = c2.selectbox("عضله", ["سینه/پشت بازو", "زیربغل/جلو بازو", "پا", "سرشانه", "هوازی/شکم"])
            c3, c4 = st.columns(2)
            w_dur = c3.slider("مدت (دقیقه)", 15, 120, 60)
            w_int = c4.select_slider("فشار", ["سبک", "متوسط", "سنگین", "وحشی!"])
            w_n = st.text_area("یادداشت")
            if st.form_submit_button("ثبت تمرین (+50 XP)"):
                add_workout(final_date, w_mus, w_dur, w_int, w_n)
                st.success(f"تمرین در تاریخ {final_date} ثبت شد! ۵۰ امتیاز گرفتی 💪")
                st.balloons()
                st.cache_resource.clear()
                st.rerun()
    
    df_gym = load_data("workouts")
    if not df_gym.empty:
        df_gym = df_gym.sort_values(by='date', ascending=False)
        df_gym = df_gym.rename(columns={'date': 'تاریخ', 'muscle': 'عضله هدف', 'duration': 'مدت (دقیقه)', 'intensity': 'شدت', 'notes': 'یادداشت'})
        st.dataframe(df_gym, use_container_width=True, hide_index=True)
        