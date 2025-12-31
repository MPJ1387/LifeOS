import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import datetime
import jdatetime

# --- تنظیمات صفحه ---
st.set_page_config(page_title="Life OS", layout="wide", page_icon="💎")

# --- استایل CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@100;300;400;500;600;700;800;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Vazirmatn', sans-serif !important;
        direction: rtl;
        text-align: right;
    }
    
    /* تنظیم فونت همه ورودی‌ها */
    input, textarea, select, div[data-baseweb="select"] {
        font-family: 'Vazirmatn', sans-serif !important;
        direction: rtl;
        text-align: right;
    }

    h1, h2, h3, h4, h5, h6, p, label {
        font-family: 'Vazirmatn', sans-serif !important;
        text-align: right;
        direction: rtl;
    }
    
    .stButton > button {
        font-family: 'Vazirmatn', sans-serif !important;
        font-weight: bold;
    }

    /* آیکون‌ها */
    [data-testid="stSidebarCollapseButton"] *, 
    [data-testid="stSidebarExpandButton"] * {
        font-family: 'Material Symbols Rounded', sans-serif !important;
        direction: ltr !important;
    }

    /* اعداد و متریک‌ها */
    div[data-testid="stMetricValue"] {
        font-family: 'Vazirmatn', sans-serif !important;
        direction: ltr !important; 
        text-align: right;
    }
    
    /* لی‌اوت */
    .main .block-container, section[data-testid="stSidebar"] {
        direction: rtl;
        text-align: right;
    }

    div[data-testid="stDataFrame"] {
        direction: rtl;
        text-align: right;
        font-family: 'Vazirmatn', sans-serif;
    }
    
    div[data-testid="stMetric"] {
        background-color: #1E1E1E;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 15px;
    }

    /* فیکس اسلایدر */
    div[data-testid="stSlider"], div[data-testid="stSelectSlider"] {
        direction: ltr !important; 
    }
    div[data-testid="stSlider"] > label, div[data-testid="stSelectSlider"] > label {
        direction: rtl !important;
        text-align: right !important;
        width: 100%;
        display: flex;
        justify-content: flex-end;
    }
    div[data-testid="stSliderTickBarMin"], div[data-testid="stSliderTickBarMax"] {
        font-family: 'Vazirmatn', sans-serif !important;
    }

    .user-card {
        background-color: #262730;
        padding: 20px;
        border-radius: 15px;
        border: 2px solid #444;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .level-badge {
        font-size: 28px;
        font-weight: 800;
        color: #FFD700;
    }
    .xp-stats {
        font-size: 14px;
        color: #aaa;
        margin-top: 5px;
        font-family: 'Vazirmatn', sans-serif !important;
    }

    .stApp { overflow-x: hidden; }
</style>
""", unsafe_allow_html=True)

DB_FILE = 'life_os.db'

# --- تابع کمکی: انتخاب‌گر تاریخ شمسی (اصلاح شده برای تراز دقیق) ---
def native_shamsi_datepicker(key_prefix):
    """ایجاد ۳ منوی کشویی که دقیقاً با فیلدهای کناری هم‌تراز هستند"""
    # دریافت تاریخ امروز شمسی
    today = jdatetime.date.today()
    
    # ستون‌بندی داخلی: سال (راست)، ماه (وسط)، روز (چپ)
    # توجه: در حالت RTL، ستون اول سمت راست قرار می‌گیرد
    c_year, c_month, c_day = st.columns([1.3, 1.5, 1])
    
    with c_year:
        years = list(range(1400, 1411))
        try: default_idx = years.index(today.year)
        except: default_idx = 0
        # لیبل "سال" را مستقیم به خود باکس می‌دهیم تا تراز عمودی درست شود
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

# --- توابع دیتابیس ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS finance (id INTEGER PRIMARY KEY, date TEXT, type TEXT, amount REAL, category TEXT, description TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS trading (id INTEGER PRIMARY KEY, date TEXT, pair TEXT, direction TEXT, result TEXT, pnl REAL, notes TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS investments (id INTEGER PRIMARY KEY, date TEXT, asset_name TEXT, type TEXT, amount_toman REAL, quantity REAL, notes TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS workouts (id INTEGER PRIMARY KEY, date TEXT, muscle TEXT, duration INTEGER, intensity TEXT, notes TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS habits (date TEXT, habit_name TEXT, status INTEGER, PRIMARY KEY (date, habit_name))''')
    conn.commit()
    conn.close()

def add_finance(date, type_, amount, category, desc):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO finance (date, type, amount, category, description) VALUES (?, ?, ?, ?, ?)", (date, type_, amount, category, desc))
    conn.commit()
    conn.close()

def add_trade(date, pair, direction, result, pnl, notes):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO trading (date, pair, direction, result, pnl, notes) VALUES (?, ?, ?, ?, ?, ?)", (date, pair, direction, result, pnl, notes))
    conn.commit()
    conn.close()

def add_investment(date, asset_name, type_, amount_toman, quantity, notes):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO investments (date, asset_name, type, amount_toman, quantity, notes) VALUES (?, ?, ?, ?, ?, ?)", (date, asset_name, type_, amount_toman, quantity, notes))
    conn.commit()
    conn.close()

def add_workout(date, muscle, duration, intensity, notes):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO workouts (date, muscle, duration, intensity, notes) VALUES (?, ?, ?, ?, ?)", (date, muscle, duration, intensity, notes))
    conn.commit()
    conn.close()

def toggle_habit(date, habit_name, is_checked):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    status = 1 if is_checked else 0
    c.execute("INSERT OR REPLACE INTO habits (date, habit_name, status) VALUES (?, ?, ?)", (date, habit_name, status))
    conn.commit()
    conn.close()

def load_data(table_name):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df

def get_habit_status(date, habit_name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT status FROM habits WHERE date = ? AND habit_name = ?", (date, habit_name))
    result = c.fetchone()
    conn.close()
    return True if result and result[0] == 1 else False

def calculate_xp():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try: c.execute("SELECT COUNT(*) FROM habits WHERE status=1"); h_score = c.fetchone()[0] * 10
    except: h_score = 0
    try: c.execute("SELECT COUNT(*) FROM workouts"); w_score = c.fetchone()[0] * 50
    except: w_score = 0
    try: c.execute("SELECT COUNT(*) FROM trading"); t_score = c.fetchone()[0] * 30
    except: t_score = 0
    try: c.execute("SELECT COUNT(*) FROM finance"); f_score = c.fetchone()[0] * 15
    except: f_score = 0
    conn.close()
    total_xp = h_score + w_score + t_score + f_score
    level = int(total_xp / 500) + 1
    xp_in_current_level = total_xp % 500
    progress = xp_in_current_level / 500
    return level, total_xp, progress, (500 - xp_in_current_level)

init_db()

# --- رابط کاربری (Frontend) ---

level, total_xp, progress_val, xp_needed = calculate_xp()
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
                # فراخوانی تابع اصلاح شده (حذف آرگومان اول)
                final_date = native_shamsi_datepicker("fin")
            
            d_type = c2.selectbox("نوع تراکنش", ["هزینه", "درآمد"])
            d_cat = c3.selectbox("دسته‌بندی", ["حقوق", "اجاره/قسط", "مواد غذایی", "رفت و آمد", "مکمل ورزشی", "پوشاک", "سایر"])
            c4, c5 = st.columns(2)
            d_amount = c4.number_input("مبلغ (تومان)", step=10000.0, format="%.0f")
            d_desc = c5.text_input("توضیحات تراکنش")
            
            if st.form_submit_button("ثبت در سیستم (+15 XP)"):
                add_finance(final_date, d_type, d_amount, d_cat, d_desc)
                st.success(f"تراکنش با تاریخ {final_date} ثبت شد! ۱۵ امتیاز گرفتی 🪙")
                st.rerun()
    
    st.markdown("##### تاریخچه تراکنش‌ها")
    df = load_data("finance").sort_values(by='date', ascending=False)
    df = df.drop(columns=['id']).rename(columns={'date': 'تاریخ', 'type': 'نوع', 'amount': 'مبلغ', 'category': 'دسته‌بندی', 'description': 'توضیحات'})
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
                st.success(f"ترید در تاریخ {final_date} ثبت شد! ۳۰ امتیاز گرفتی 🎯")
                st.rerun()
    
    st.markdown("##### عملکرد اخیر")
    df_t = load_data("trading").sort_values(by='date', ascending=False)
    df_t = df_t.drop(columns=['id']).rename(columns={'date': 'تاریخ', 'pair': 'نماد', 'direction': 'جهت', 'result': 'نتیجه', 'pnl': 'سود/ضرر', 'notes': 'یادداشت'})
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
        df_inv_show = df_inv.sort_values(by='date', ascending=False).drop(columns=['id']).rename(columns={'date': 'تاریخ', 'asset_name': 'نام دارایی', 'type': 'نوع', 'amount_toman': 'مبلغ کل', 'quantity': 'تعداد/مقدار', 'notes': 'توضیحات'})
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
                st.rerun()
        else:
            if done: 
                toggle_habit(today_str, h, False)
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
                st.rerun()
    
    df_gym = load_data("workouts").sort_values(by='date', ascending=False)
    df_gym = df_gym.drop(columns=['id']).rename(columns={'date': 'تاریخ', 'muscle': 'عضله هدف', 'duration': 'مدت (دقیقه)', 'intensity': 'شدت', 'notes': 'یادداشت'})
    st.dataframe(df_gym, use_container_width=True, hide_index=True)