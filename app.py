import streamlit as st
import pd as pd
import requests
from datetime import datetime
import jpholiday
import calendar

# --- 1. ページ設定 ---
st.set_page_config(page_title="学生用ツール", layout="centered")

# 【7分割・鉄壁グリッドCSS】
st.markdown("""
    <style>
    .main .block-container { padding: 1rem 0.2rem !important; }
    
    /* カレンダー全体の器（7分割を絶対死守） */
    .calendar-board {
        display: grid;
        grid-template-columns: repeat(7, 1fr); /* 7等分 */
        width: 100%;
        border-top: 1px solid #ddd;
        border-left: 1px solid #ddd;
        background-color: white;
    }

    /* 曜日・日付 共通のセル設定 */
    .cal-cell {
        text-align: center;
        border-right: 1px solid #ddd;
        border-bottom: 1px solid #ddd;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-decoration: none;
        color: #333;
    }

    /* 曜日ヘッダー（上段） */
    .header-cell {
        background-color: #f8f9fa;
        font-weight: bold;
        font-size: 12px;
        padding: 8px 0;
    }

    /* 日付セル（下段以降） */
    .date-cell {
        aspect-ratio: 1 / 1; /* 正方形 */
        cursor: pointer;
        transition: 0.1s;
    }
    .date-cell:active { background-color: #f0f0f0; }
    
    /* 選択中の日 */
    .selected {
        background-color: #ff4b4b !important;
        color: white !important;
        font-weight: bold;
    }

    /* 文字サイズとマーク */
    .day-num { font-size: 14px; }
    .mark { font-size: 10px; margin-top: -2px; }

    /* 土日の色付け */
    .sun { color: #ff0000; }
    .sat { color: #0000ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ログイン & 状態管理 ---
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

# 日付選択の管理
query_params = st.query_params
if "d" in query_params:
    st.session_state.selected_date = datetime.strptime(query_params["d"], "%Y-%m-%d").date()
elif 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.now().date()

# データ読み込み
gas_url = st.secrets.get("GAS_URL")
sheet_url = st.secrets.get("connections", {}).get("gsheets", {}).get("spreadsheet")
def load_data(n):
    try:
        url = f"{sheet_url.split('/edit')[0]}/gviz/tq?tqx=out:csv&sheet={n}"
        return pd.read_csv(url)
    except: return pd.DataFrame()
df_s = load_data("schedules")

# --- 3. カレンダー描画 ---
st.title("🎓 学生用ツール")
t_cal, t_ev, t_task, t_time = st.tabs(["📅 カレンダー", "📌 予定追加", "📝 課題追加", "⏰ 時間割"])

with t_cal:
    c1, c2 = st.columns(2)
    y = c1.selectbox("年", [2025, 2026], index=1)
    m = c2.selectbox("月", list(range(1, 13)), index=datetime.now().month-1)

    # 【7分割グリッド開始】
    html = '<div class="calendar-board">'
    
    # 曜日ヘッダー（ここも同じグリッドに入れることで完璧に揃う）
    days = [("日","sun"), ("月",""), ("火",""), ("水",""), ("木",""), ("金",""), ("土","sat")]
    for d, cls in days:
        html += f'<div class="cal-cell header-cell {cls}">{d}</div>'

    # 日付の流し込み
    cal = calendar.Calendar(firstweekday=6)
    weeks = cal.monthdayscalendar(y, m)
    
    for week in weeks:
        for i, day in enumerate(week):
            if day == 0:
                html += '<div class="cal-cell" style="background:#fafafa;"></div>'
            else:
                d_obj = datetime(y, m, day).date()
                d_str = d_obj.strftime("%Y-%m-%d")
                is_sel = "selected" if d_obj == st.session_state.selected_date else ""
                is_hol = jpholiday.is_holiday(d_obj)
                
                # 色分け
                c_cls = "sun" if (i == 0 or is_hol) else ("sat" if i == 6 else "")
                mark = "🎌" if is_hol else ("📍" if not df_s.empty and d_str in df_s.iloc[:, 0].astype(str).values else "")
                
                html += f'''
                    <a href="/?d={d_str}" target="_self" class="cal-cell date-cell {is_sel} {c_cls}">
                        <span class="day-num">{day}</span>
                        <span class="mark">{mark}</span>
                    </a>
                '''
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    st.divider()
    # 選択情報の表示
    sel = st.session_state.selected_date
    st.subheader(f"🔍 {sel.strftime('%m/%d')} の予定")
    if not df_s.empty:
        evs = df_s[df_s.iloc[:, 0].astype(str).str.contains(sel.strftime("%Y-%m-%d"))]
        if not evs.empty:
            for v in evs.iloc[:, 1]: st.info(f"📍 {v}")
        else: st.write("予定なし")

# 予定追加等のタブは以前のロジックを維持
