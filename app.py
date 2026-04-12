import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import jpholiday
import calendar

# --- ページ設定 ---
st.set_page_config(page_title="学生用ツール", layout="centered")

# 【超・神ハックCSS】Streamlitのボタンコンテナを強制的にグリッド化する
st.markdown("""
    <style>
    /* メインエリアの幅を最大化 */
    .main .block-container { padding: 1rem 0.2rem !important; }
    
    /* ボタンが並ぶ親要素を強制的に7列のグリッドにする */
    div[data-testid="column"] {
        flex: 1 1 0% !important;
        min-width: 0 !important;
    }
    
    /* 1行分のボタンを囲むコンテナに適用 */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 2px !important;
    }

    /* ボタン自体の見た目調整 */
    .stButton > button {
        width: 100% !important;
        aspect-ratio: 1 / 1 !important;
        padding: 0 !important;
        font-size: 11px !important;
        min-width: 0 !important;
        height: auto !important;
        border-radius: 4px !important;
    }

    /* 曜日ヘッダー用グリッド */
    .day-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 2px;
        text-align: center;
        margin-bottom: 5px;
    }
    .day-header { font-size: 12px; font-weight: bold; padding: 5px 0; }

    /* 時間割表の改行防止 */
    .stTable td { white-space: nowrap !important; font-size: 11px !important; }
    </style>
    """, unsafe_allow_html=True)

# Secrets & Data Loading
correct_pw = st.secrets.get("MY_PASSWORD")
gas_url = st.secrets.get("GAS_URL")
sheet_url = st.secrets.get("connections", {}).get("gsheets", {}).get("spreadsheet")

pw = st.sidebar.text_input("パスワード", type="password")
if pw != correct_pw:
    st.info("ログインしてください。")
    st.stop()

# 状態管理（リロードなしで状態を保つ）
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

st.title("🎓 学生用ツール")
tab_cal, tab_ev, tab_task, tab_time = st.tabs(["📅 カレンダー", "📌 予定追加", "📝 課題追加", "⏰ 時間割"])

# --- 1. カレンダータブ（公式ボタンを強制横並び） ---
with tab_cal:
    now = datetime.now()
    c1, c2 = st.columns(2)
    sel_year = c1.selectbox("年", [2025, 2026], index=1, label_visibility="collapsed")
    sel_month = c2.selectbox("月", list(range(1, 13)), index=now.month-1, label_visibility="collapsed")
    
    # 曜日ヘッダー（HTMLで固定）
    st.markdown(f"""
        <div class="day-grid">
            <div class="day-header" style="color:red;">日</div>
            <div class="day-header">月</div><div class="day-header">火</div><div class="day-header">水</div>
            <div class="day-header">木</div><div class="day-header">金</div>
            <div class="day-header" style="color:blue;">土</div>
        </div>
    """, unsafe_allow_html=True)

    # 日曜始まりのカレンダー
    cal_obj = calendar.Calendar(firstweekday=6)
    weeks = cal_obj.monthdayscalendar(sel_year, sel_month)

    # 日付ボタンエリア
    for week in weeks:
        # この columns(7) がスマホで縦にならないように CSS で flex-direction: row を強制している
        cols = st.columns(7) 
        for i, day in enumerate(week):
            if day != 0:
                d_obj = datetime(sel_year, sel_month, day).date()
                d_str = d_obj.strftime("%Y-%m-%d")
                
                # 予定・祝日チェック
                has_ev = not df_s.empty and d_str in df_s.iloc[:, 0].astype(str).values
                is_hol = jpholiday.is_holiday(d_obj)
                
                label = f"{day}"
                if is_hol: label += "\n🎌"
                elif has_ev: label += "\n📍"
                
                # 公式ボタンなので、押してもURLは飛ばない（リロードなし）
                # 選択中の日は primary（色付き）にする
                btn_type = "primary" if d_obj == st.session_state.selected_date else "secondary"
                
                if cols[i].button(label, key=f"d_{d_str}", type=btn_type):
                    st.session_state.selected_date = d_obj
                    st.rerun() # 自分の状態を更新して再描画（高速）
            else:
                cols[i].empty()

    st.divider()
    sel = st.session_state.selected_date
    st.subheader(f"🔍 {sel.strftime('%m/%d')} の情報")
    # 以下、予定表示ロジック（前回と同じ）
    hol_n = jpholiday.is_holiday_name(sel)
    if hol_n: st.error(f"🎌 {hol_n}")
    if not df_s.empty:
        day_evs = df_s[df_s.iloc[:, 0].astype(str).str.contains(sel.strftime("%Y-%m-%d"))]
        if not day_evs.empty:
            for v in day_evs.iloc[:, 1]: st.info(f"📍 予定: {v}")
        else: st.write("予定なし")

# --- 他のタブは変更なし ---
# (予定追加・課題追加・時間割のコードをそのまま貼り付け)
