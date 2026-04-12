import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import jpholiday
import calendar

# --- 1. ページ設定 ---
st.set_page_config(page_title="学生用ツール", layout="centered")

# 【枠線＆数字配置CSS】
# これで「先に枠線を用意して中に数字を配置」を完璧に再現します
st.markdown("""
    <style>
    .main .block-container { padding: 1rem 0.2rem !important; }
    
    /* カレンダー全体の枠組み */
    .cal-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        border-top: 1px solid #ddd;
        border-left: 1px solid #ddd;
        background-color: white;
    }

    /* 曜日のヘッダー */
    .cal-header {
        background-color: #f8f9fa;
        font-weight: bold;
        text-align: center;
        padding: 5px 0;
        font-size: 11px;
        border-right: 1px solid #ddd;
        border-bottom: 1px solid #ddd;
    }

    /* 日付の枠（これがボタン代わり） */
    .cal-cell {
        aspect-ratio: 1 / 1;
        border-right: 1px solid #ddd;
        border-bottom: 1px solid #ddd;
        position: relative;
        cursor: pointer;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        align-items: center;
        padding-top: 4px;
        transition: 0.2s;
        text-decoration: none;
        color: #333;
    }
    
    /* 押した時の反応 */
    .cal-cell:active { background-color: #eee; }
    
    /* 選択中の日の色 */
    .cal-cell.selected {
        background-color: #ff4b4b !important;
        color: white !important;
    }

    /* 数字の配置 */
    .day-num { font-size: 13px; font-weight: 500; }
    
    /* 予定・祝日のマーク */
    .mark { font-size: 10px; margin-top: 1px; }

    /* 土日の色 */
    .sun { color: red; }
    .sat { color: blue; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ログイン管理（URLを変えないので消えません） ---
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
# 日付選択をクエリパラメータ（?d=...）で管理
# これが「ボタンを押すと移動する」原理の正体です
query_params = st.query_params
if "d" in query_params:
    st.session_state.selected_date = datetime.strptime(query_params["d"], "%Y-%m-%d").date()
elif 'selected_date' not in st.session_state:
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
tabs = st.tabs(["📅 カレンダー", "📌 予定追加", "📝 課題追加", "⏰ 時間割"])

# --- カレンダータブ ---
with tabs[0]:
    now = datetime.now()
    c1, c2 = st.columns(2)
    sel_year = c1.selectbox("年", [2025, 2026], index=1)
    sel_month = c2.selectbox("月", list(range(1, 13)), index=now.month-1)

    # 自作カレンダーの構築
    html = '<div class="cal-grid">'
    # ヘッダー
    for i, d in enumerate(["日", "月", "火", "水", "木", "金", "土"]):
        color = "sun" if i == 0 else ("sat" if i == 6 else "")
        html += f'<div class="cal-header {color}">{d}</div>'
    
    # 日付
    cal_obj = calendar.Calendar(firstweekday=6)
    weeks = cal_obj.monthdayscalendar(sel_year, sel_month)
    
    for week in weeks:
        for i, day in enumerate(week):
            if day == 0:
                html += '<div style="border-right: 1px solid #ddd; border-bottom: 1px solid #ddd; background:#fafafa;"></div>'
            else:
                d_obj = datetime(sel_year, sel_month, day).date()
                d_str = d_obj.strftime("%Y-%m-%d")
                
                # スタイル判定
                is_sel = "selected" if d_obj == st.session_state.selected_date else ""
                is_hol = jpholiday.is_holiday(d_obj)
                color_class = "sun" if (i == 0 or is_hol) else ("sat" if i == 6 else "")
                
                mark = "🎌" if is_hol else ("📍" if not df_s.empty and d_str in df_s.iloc[:, 0].astype(str).values else "")
                
                # ★ここがポイント：aタグでURLの末尾に日付を付けて「自分自身」に飛ばす
                # target="_self" なので、ブラウザは「移動」とみなさずログインを維持します
                html += f'''
                    <a href="/?d={d_str}" target="_self" class="cal-cell {is_sel} {color_class}">
                        <span class="day-num">{day}</span>
                        <span class="mark">{mark}</span>
                    </a>
                '''
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    st.divider()
    sel = st.session_state.selected_date
    st.subheader(f"🔍 {sel.strftime('%m/%d')} の情報")
    if not df_s.empty:
        day_evs = df_s[df_s.iloc[:, 0].astype(str).str.contains(sel.strftime("%Y-%m-%d"))]
        if not day_evs.empty:
            for v in day_evs.iloc[:, 1]: st.info(f"📍 {v}")
        else: st.write("予定なし")

# (予定追加・課題追加などのタブは以前のままでOK)
