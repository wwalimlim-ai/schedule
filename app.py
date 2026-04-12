import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
import jpholiday
import calendar

# --- 1. ページ設定 (最上部への固定と余白削除) ---
st.set_page_config(page_title="MyTool", layout="centered")

st.markdown("""
    <style>
    /* ページ上部の巨大な余白を消す */
    .stAppHeader { display: none; }
    .main .block-container { 
        padding-top: 0rem !important; 
        padding-left: 0.5rem !important; 
        padding-right: 0.5rem !important; 
    }
    /* タブのデザイン微調整 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        position: sticky;
        top: 0;
        z-index: 1000;
        background-color: white;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 12px;
        font-size: 14px;
    }
    .calendar-wrapper { display: grid; grid-template-columns: repeat(7, 1fr); background: white; border: 1px solid #eee; }
    .cal-box { aspect-ratio: 1/1; display: flex; flex-direction: column; justify-content: center; align-items: center; text-decoration: none; border: 0.5px solid #f8f8f8; color: #444; }
    .head-box { font-size: 10px; font-weight: bold; background: #fafafa; height: 30px; border: none; }
    .date-box { font-size: 16px; position: relative; }
    .selected-box { background: #ff4b4b !important; color: white !important; border-radius: 8px; font-weight: bold; }
    .sun { color: #ff4b4b; } .sat { color: #007bff; }
    .has-event-dot { width: 5px; height: 5px; background-color: #ff9f00; border-radius: 50%; margin-top: 2px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. データ読み込み ---
gas_url = st.secrets.get("GAS_URL")
sheet_url = st.secrets.get("connections", {}).get("gsheets", {}).get("spreadsheet")

@st.cache_data(ttl=60)
def load_data(sheet_name, clear_cache=False):
    if clear_cache: st.cache_data.clear()
    try:
        base = sheet_url.split('/edit')[0]
        return pd.read_csv(f"{base}/gviz/tq?tqx=out:csv&sheet={sheet_name}")
    except: return pd.DataFrame()

df_s = load_data("schedules")
df_t = load_data("tasks")

# 時間設定
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST)

if "d" in st.query_params:
    st.session_state.selected_date = datetime.strptime(st.query_params["d"], "%Y-%m-%d").date()
elif 'selected_date' not in st.session_state:
    st.session_state.selected_date = now.date()

sel = st.session_state.selected_date

# --- 3. メインUI (タブを一番上に配置) ---
# タイトルを消すか、タブの中に移動させて「一番上がタブ」の状態を作る
tabs = st.tabs(["📅 カレンダー", "🎒 持ち物", "📋 課題", "📝 予定一覧", "➕ 登録"])

# 【タブ1: カレンダー】
with tabs[0]:
    st.subheader(f"📅 {sel.month}/{sel.day}")
    
    with st.expander("月を変更"):
        y = st.selectbox("年", [2025, 2026], index=([2025, 2026].index(now.year)))
        m = st.selectbox("月", list(range(1, 13)), index=now.month - 1)
    if 'y' not in locals(): y, m = now.year, now.month

    html = '<div class="calendar-wrapper">'
    for d, cls in [("日","sun"),("月",""),("火",""),("水",""),("木",""),("金",""),("土","sat")]:
        html += f'<div class="cal-box head-box {cls}">{d}</div>'

    for week in calendar.Calendar(firstweekday=6).monthdayscalendar(y, m):
        for i, day in enumerate(week):
            if day == 0: html += '<div class="cal-box"></div>'
            else:
                d_obj = datetime(y, m, day).date()
                d_str = d_obj.strftime("%Y-%m-%d")
                is_sel = "selected-box" if d_obj == sel else ""
                c_cls = "sun" if (i == 0 or jpholiday.is_holiday(d_obj)) else ("sat" if i == 6 else "")
                has_ev = not df_s.empty and d_str in df_s.iloc[:, 0].astype(str).values
                dot = '<div class="has-event-dot"></div>' if has_ev else ""
                html += f'<a href="/?d={d_str}" target="_self" class="cal-box date-box {is_sel} {c_cls}">{day}{dot}</a>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    # 選択日の予定をカレンダーのすぐ下に表示
    evs = df_s[df_s.iloc[:, 0].astype(str).str.contains(sel.strftime("%Y-%m-%d"))] if not df_s.empty else []
    if len(evs) > 0:
        for v in evs.iloc[:, 1]: st.info(v)

# 【タブ2: 持ち物】
with tabs[1]:
    day_name = ["月","火","水","木","金","土","日"][sel.weekday()]
    st.write(f"### {day_name}曜日のセット")
    # ... (持ち物表示ロジックは以前と同じ) ...

# 【タブ3: 課題】
with tabs[2]:
    st.write("### 未完了の課題")
    # ... (課題表示ロジック) ...

# 【タブ4: 予定一覧】
with tabs[3]:
    st.write("### 今後の予定")
    # ... (予定一覧ロジック) ...

# 【タブ5: 登録】
with tabs[4]:
    st.write(f"### {sel.month}/{sel.day} に登録")
    # ... (登録フォーム) ...
