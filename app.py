import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import jpholiday
import calendar

# --- 1. ページ設定 ---
st.set_page_config(page_title="学生用ツール", layout="centered")

# 【隙間完全抹殺CSS】
st.markdown("""
    <style>
    /* 画面端の余白を極限まで削る */
    .main .block-container { padding: 1rem 0rem !important; }
    
    /* [重要] カラム同士の隙間を0にする */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 0px !important; /* 隙間をゼロに */
    }
    
    /* [重要] 各カラムのパディングを消してボタンを密着させる */
    div[data-testid="column"] {
        width: 14.28% !important;
        flex: 1 1 0% !important;
        min-width: 0 !important;
        padding: 0px 1px !important; /* 隣との間に1pxだけ隙間を作る */
    }

    /* ボタンを枠いっぱいに広げる */
    .stButton > button {
        width: 100% !important;
        aspect-ratio: 1 / 1.1 !important;
        padding: 0 !important;
        font-size: 12px !important;
        border-radius: 0px !important; /* 四角くして隙間を埋める */
        margin: 0 !important;
    }

    /* 曜日ヘッダー */
    .day-header-grid {
        display: flex;
        flex-direction: row;
        width: 100%;
        margin-bottom: 5px;
    }
    .day-header-item {
        width: 14.28%;
        text-align: center;
        font-size: 11px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ログイン管理（セッション維持） ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 ログイン")
    pw = st.text_input("パスワード", type="password")
    if st.button("ログイン"):
        if pw == st.secrets.get("MY_PASSWORD"):
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

# --- 3. メインロジック ---
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.now().date()

gas_url = st.secrets.get("GAS_URL")
sheet_url = st.secrets.get("connections", {}).get("gsheets", {}).get("spreadsheet")

def load_data(sheet_name):
    if not sheet_url: return pd.DataFrame()
    try:
        base_url = sheet_url.split('/edit')[0]
        csv_url = f"{base_url}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        return pd.read_csv(csv_url)
    except: return pd.DataFrame()

df_s = load_data("schedules")

st.title("🎓 学生用ツール")
tab_cal, tab_ev, tab_task, tab_time = st.tabs(["📅 カレンダー", "📌 予定追加", "📝 課題追加", "⏰ 時間割"])

with tab_cal:
    now = datetime.now()
    c1, c2 = st.columns(2)
    sel_year = c1.selectbox("年", [2025, 2026], index=1, key="y_sel")
    sel_month = c2.selectbox("月", list(range(1, 13)), index=now.month-1, key="m_sel")
    
    # 曜日ヘッダー
    st.markdown("""
        <div class="day-header-grid">
            <div class="day-header-item" style="color:red;">日</div><div class="day-header-item">月</div>
            <div class="day-header-item">火</div><div class="day-header-item">水</div>
            <div class="day-header-item">木</div><div class="day-header-item">金</div>
            <div class="day-header-item" style="color:blue;">土</div>
        </div>
    """, unsafe_allow_html=True)

    cal_obj = calendar.Calendar(firstweekday=6)
    weeks = cal_obj.monthdayscalendar(sel_year, sel_month)

    for week in weeks:
        cols = st.columns(7) 
        for i, day in enumerate(week):
            if day != 0:
                d_obj = datetime(sel_year, sel_month, day).date()
                d_str = d_obj.strftime("%Y-%m-%d")
                has_ev = not df_s.empty and d_str in df_s.iloc[:, 0].astype(str).values
                is_hol = jpholiday.is_holiday(d_obj)
                
                label = f"{day}"
                if is_hol: label += "\n🎌"
                elif has_ev: label += "\n📍"
                
                btn_type = "primary" if d_obj == st.session_state.selected_date else "secondary"
                
                if cols[i].button(label, key=f"btn_{d_str}", type=btn_type):
                    st.session_state.selected_date = d_obj
                    st.rerun()
            else:
                cols[i].empty()

    st.divider()
    sel = st.session_state.selected_date
    st.subheader(f"🔍 {sel.strftime('%m/%d')} の情報")
    if not df_s.empty:
        day_evs = df_s[df_s.iloc[:, 0].astype(str).str.contains(sel.strftime("%Y-%m-%d"))]
        if not day_evs.empty:
            for v in day_evs.iloc[:, 1]: st.info(f"📍 {v}")
        else: st.write("予定なし")
