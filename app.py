import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import jpholiday
import calendar

# --- 1. ページ設定 ---
st.set_page_config(page_title="学生用ツール", layout="centered")

# 【鉄壁の横並びCSS】
st.markdown("""
    <style>
    .main .block-container { padding: 1rem 0.2rem !important; }
    
    /* スマホでも強制的に横並びを維持する設定 */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 2px !important;
    }
    div[data-testid="column"] {
        width: 14.28% !important;
        flex: 1 1 0% !important;
        min-width: 0 !important;
    }
    .stButton > button {
        width: 100% !important;
        aspect-ratio: 1 / 1.1;
        padding: 0 !important;
        font-size: 11px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ログイン管理（ここが今回の肝） ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 ログイン")
    pw = st.text_input("パスワード", type="password")
    if st.button("ログイン"):
        if pw == st.secrets.get("MY_PASSWORD"):
            st.session_state.authenticated = True
            st.rerun() # ここで1回だけリロードしてメイン画面へ
        else:
            st.error("パスワードが違います")
    st.stop()

# --- 3. ログイン後の処理（URLは一切触りません） ---
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
SUBJECTS = ["現国", "言語文化", "地総", "歴総", "数基α", "数基β", "科技α", "科技β", "コミュ I", "論表", "SP I", "保健", "体育", "音楽", "家庭", "探求基礎", "LT"]

st.title("🎓 学生用ツール")
tab_cal, tab_ev, tab_task, tab_time = st.tabs(["📅 カレンダー", "📌 予定追加", "📝 課題追加", "⏰ 時間割"])

with tab_cal:
    # --- カレンダー表示 ---
    c1, c2 = st.columns(2)
    # 選択肢が変わった時だけリロードされるように key を固定
    sel_year = c1.selectbox("年", [2025, 2026], index=1, key="year_sel")
    sel_month = c2.selectbox("月", list(range(1, 13)), index=datetime.now().month-1, key="month_sel")
    
    # 曜日ヘッダー
    cols_h = st.columns(7)
    days_h = [("日","red"), ("月","black"), ("火","black"), ("水","black"), ("木","black"), ("金","black"), ("土","blue")]
    for i, (d, color) in enumerate(days_h):
        cols_h[i].markdown(f"<div style='text-align:center; font-size:11px; font-weight:bold; color:{color};'>{d}</div>", unsafe_allow_html=True)

    cal_obj = calendar.Calendar(firstweekday=6)
    weeks = cal_obj.monthdayscalendar(sel_year, sel_month)

    for week in weeks:
        cols = st.columns(7) 
        for i, day in enumerate(week):
            if day != 0:
                d_obj = datetime(sel_year, sel_month, day).date()
                d_str = d_obj.strftime("%Y-%m-%d")
                
                # 祝日・予定判定
                is_hol = jpholiday.is_holiday(d_obj)
                has_ev = not df_s.empty and d_str in df_s.iloc[:, 0].astype(str).values
                
                label = f"{day}"
                if is_hol: label += "\n🎌"
                elif has_ev: label += "\n📍"
                
                # ボタンの種類（選択中は色を変える）
                btn_type = "primary" if d_obj == st.session_state.selected_date else "secondary"
                
                # ボタンが押されたら session_state を更新して st.rerun()
                # これが「タブを切り替える」のと同じ原理（内部リロード）
                if cols[i].button(label, key=f"d_{d_str}", type=btn_type):
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

# --- 他のタブは前回と同じ（session_state.selected_date を使う） ---
