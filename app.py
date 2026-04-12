import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import jpholiday
import calendar

# --- ページ設定 ---
st.set_page_config(page_title="学生用ツール", layout="centered")

# 【隙間完全抹殺CSS】
st.markdown("""
    <style>
    /* 1. 画面端の余白を完全にゼロにする */
    .main .block-container { padding: 0.5rem 0rem !important; }
    
    /* 2. 横並びブロックの隙間をマイナスにしてボタン同士を密着させる */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 0px !important; /* 隙間ゼロ */
        margin-left: -5px !important; /* 左側の謎の余白を削る */
        margin-right: -5px !important;
    }
    
    /* 3. 各カラムの幅と余白を徹底管理 */
    [data-testid="column"] {
        width: 14.28% !important;
        flex: 1 1 0% !important;
        min-width: 0 !important;
        padding: 0px 1px !important; /* ボタン同士の最小限の隙間だけ残す */
    }

    /* 4. ボタンを巨大化させて余白を埋める */
    .stButton > button {
        width: 100% !important;
        padding: 0 !important;
        font-size: 12px !important;
        height: 50px !important; /* 高さを少し出して押しやすく */
        border-radius: 2px !important;
        margin: 0 !important;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    /* 曜日ヘッダーも密着 */
    .day-grid {
        display: flex !important;
        flex-direction: row !important;
        margin-bottom: 5px;
        padding: 0 2px;
    }
    .day-header {
        width: 14.28%;
        text-align: center;
        font-size: 11px;
        font-weight: bold;
    }

    /* 時間割の表 */
    .stTable td { white-space: nowrap !important; font-size: 11px !important; padding: 3px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 以下、ロジック部分は維持 ---

correct_pw = st.secrets.get("MY_PASSWORD")
gas_url = st.secrets.get("GAS_URL")
sheet_url = st.secrets.get("connections", {}).get("gsheets", {}).get("spreadsheet")

pw = st.sidebar.text_input("パスワード", type="password")
if pw != correct_pw:
    st.info("ログインしてください。")
    st.stop()

if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.now().date()

def load_data(sheet_name):
    if not sheet_url: return pd.DataFrame()
    try:
        base_url = sheet_url.split('/edit')[0]
        csv_url = f"{base_url}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        return pd.read_csv(csv_url)
    except: return pd.DataFrame()

df_s = load_data("schedules")
SUBJECTS = ["教科なし", "現国", "言語文化", "地総", "歴総", "数基α", "数基β", "科技α", "科技β", "コミュ I", "論表", "SP I", "保健", "体育", "音楽", "家庭", "探求基礎", "LT"]

st.title("🎓 学生用ツール")
tab_cal, tab_ev, tab_task, tab_time = st.tabs(["📅 カレンダー", "📌 予定追加", "📝 課題追加", "⏰ 時間割"])

with tab_cal:
    now = datetime.now()
    c1, c2 = st.columns(2)
    sel_year = c1.selectbox("年", [2025, 2026], index=1, label_visibility="collapsed")
    sel_month = c2.selectbox("月", list(range(1, 13)), index=now.month-1, label_visibility="collapsed")
    
    st.markdown(f"""
        <div class="day-grid">
            <div class="day-header" style="color:red;">日</div>
            <div class="day-header">月</div><div class="day-header">火</div><div class="day-header">水</div>
            <div class="day-header">木</div><div class="day-header">金</div>
            <div class="day-header" style="color:blue;">土</div>
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
                
                if cols[i].button(label, key=f"d_{d_str}", type=btn_type):
                    st.session_state.selected_date = d_obj
                    st.rerun()
            else:
                cols[i].empty()

    st.divider()
    sel = st.session_state.selected_date
    st.subheader(f"🔍 {sel.strftime('%m/%d')} の情報")
    hol_n = jpholiday.is_holiday_name(sel)
    if hol_n: st.error(f"🎌 {hol_n}")
    if not df_s.empty:
        day_evs = df_s[df_s.iloc[:, 0].astype(str).str.contains(sel.strftime("%Y-%m-%d"))]
        if not day_evs.empty:
            for v in day_evs.iloc[:, 1]: st.info(f"📍 {v}")
        else: st.write("予定なし")

# 予定追加・課題追加・時間割は前回と同じため維持
