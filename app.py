import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import jpholiday
import calendar

# --- ページ設定 ---
st.set_page_config(page_title="学生用ツール", layout="centered")

# 【最終解決CSS】Streamlitのカラムを使わず、HTMLグリッドでボタンを自作
st.markdown("""
    <style>
    /* 画面端の余白を抹殺 */
    .main .block-container { padding: 1rem 0.2rem !important; }
    
    /* 物理的に7等分するグリッドコンテナ */
    .cal-wrapper {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 3px;
        width: 100%;
        margin-bottom: 10px;
    }
    
    /* 曜日・日付ボタンの共通スタイル */
    .cal-item {
        text-align: center;
        text-decoration: none;
        color: #31333F;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        border-radius: 4px;
        font-size: 12px;
        min-height: 50px;
        transition: 0.1s;
    }

    /* 曜日の見た目 */
    .header-item { font-weight: bold; font-size: 11px; min-height: 30px; }

    /* 日付ボタンの見た目 */
    .date-item {
        background-color: #f0f2f6;
        border: 1px solid transparent;
        cursor: pointer;
    }
    .date-item:active { background-color: #e0e2e6; }
    
    /* 選択中の日の強調 */
    .date-selected {
        background-color: #ff4b4b !important;
        color: white !important;
        font-weight: bold;
    }

    /* 祝日・予定のマーク */
    .marker { font-size: 10px; margin-top: -2px; }

    /* 時間割表の改行防止 */
    .stTable td { white-space: nowrap !important; font-size: 11px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 状態管理 ---
# クエリパラメータで選択された日付を受け取る
params = st.query_params
if "date" in params:
    st.session_state.selected_date = datetime.strptime(params["date"], "%Y-%m-%d").date()
elif 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.now().date()

# --- データ読み込み ---
correct_pw = st.secrets.get("MY_PASSWORD")
gas_url = st.secrets.get("GAS_URL")
sheet_url = st.secrets.get("connections", {}).get("gsheets", {}).get("spreadsheet")

# ログイン
pw = st.sidebar.text_input("パスワード", type="password")
if pw != correct_pw:
    st.info("ログインしてください。")
    st.stop()

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

# --- 1. カレンダータブ（HTMLグリッド） ---
with tab_cal:
    now = datetime.now()
    c1, c2 = st.columns(2)
    sel_year = c1.selectbox("年", [2025, 2026], index=1, label_visibility="collapsed")
    sel_month = c2.selectbox("月", list(range(1, 13)), index=now.month-1, label_visibility="collapsed")
    
    # グリッド開始
    html_code = '<div class="cal-wrapper">'
    
    # 曜日ヘッダー
    days = [("日","red"), ("月",""), ("火",""), ("水",""), ("木",""), ("金",""), ("土","blue")]
    for d, color in days:
        html_code += f'<div class="cal-item header-item" style="color:{color};">{d}</div>'

    # カレンダー計算
    cal_obj = calendar.Calendar(firstweekday=6)
    weeks = cal_obj.monthdayscalendar(sel_year, sel_month)

    for week in weeks:
        for i, day in enumerate(week):
            if day != 0:
                d_obj = datetime(sel_year, sel_month, day).date()
                d_str = d_obj.strftime("%Y-%m-%d")
                has_ev = not df_s.empty and d_str in df_s.iloc[:, 0].astype(str).values
                is_hol = jpholiday.is_holiday(d_obj)
                
                # スタイル判定
                color = "inherit"
                if i == 0 or is_hol: color = "red"
                elif i == 6: color = "blue"
                
                active_class = "date-selected" if d_obj == st.session_state.selected_date else "date-item"
                
                marker = ""
                if is_hol: marker = '<span class="marker">🎌</span>'
                elif has_ev: marker = '<span class="marker">📍</span>'
                
                # リンクとして作成（URLを書き換えて再読み込みさせるが、target="_self"で爆速に）
                html_code += f'<a href="/?date={d_str}" target="_self" class="cal-item {active_class}" style="color:{color};">{day}{marker}</a>'
            else:
                html_code += '<div class="cal-item"></div>'
    
    html_code += '</div>'
    st.markdown(html_code, unsafe_allow_html=True)

    st.divider()
    # 選択中の情報表示
    sel = st.session_state.selected_date
    st.subheader(f"🔍 {sel.strftime('%m/%d')} の情報")
    hol_n = jpholiday.is_holiday_name(sel)
    if hol_n: st.error(f"🎌 {hol_n}")
    if not df_s.empty:
        day_evs = df_s[df_s.iloc[:, 0].astype(str).str.contains(sel.strftime("%Y-%m-%d"))]
        if not day_evs.empty:
            for v in day_evs.iloc[:, 1]: st.info(f"📍 {v}")
        else: st.write("予定なし")

# --- 他のタブ（予定追加・課題追加・時間割）は以前のコードを維持 ---
