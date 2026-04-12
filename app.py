import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
import jpholiday
import calendar

# --- 1. ページ設定（極限までシンプルに） ---
st.set_page_config(page_title="MyTool", layout="centered")

st.markdown("""
    <style>
    .main .block-container { padding: 0.5rem 0.5rem !important; }
    .calendar-wrapper { display: grid; grid-template-columns: repeat(7, 1fr); background: white; border: 1px solid #eee; }
    .cal-box { aspect-ratio: 1/1; display: flex; flex-direction: column; justify-content: center; align-items: center; text-decoration: none; border: 0.5px solid #f0f0f0; color: #444; }
    .head-box { font-size: 10px; font-weight: bold; background: #fafafa; height: 30px; }
    .date-box { font-size: 16px; }
    .selected-box { background: #ff4b4b !important; color: white !important; border-radius: 5px; }
    .sun { color: #ff4b4b; } .sat { color: #007bff; }
    .mark { font-size: 8px; color: #ff9f00; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. データ読み込み（キャッシュあり） ---
gas_url = st.secrets.get("GAS_URL")
sheet_url = st.secrets.get("connections", {}).get("gsheets", {}).get("spreadsheet")

@st.cache_data(ttl=60)
def load_data(sheet_name):
    try:
        base = sheet_url.split('/edit')[0]
        return pd.read_csv(f"{base}/gviz/tq?tqx=out:csv&sheet={sheet_name}")
    except: return pd.DataFrame()

df_s = load_data("schedules")
df_t = load_data("tasks")

# 時間設定
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST)

# 選択日付の管理
if "d" in st.query_params:
    st.session_state.selected_date = datetime.strptime(st.query_params["d"], "%Y-%m-%d").date()
else:
    st.session_state.selected_date = now.date()

sel = st.session_state.selected_date

# --- 3. メインUI ---
# ヘッダーをコンパクトに
st.title(f"📅 {sel.month}/{sel.day}")

# 【カレンダー設定】めったにいじらないので折りたたむ
with st.expander("📅 月を切り替える"):
    y = st.selectbox("年", [2025, 2026], index=([2025, 2026].index(now.year)))
    m = st.selectbox("月", list(range(1, 13)), index=now.month - 1)
else:
    y, m = now.year, now.month

# 【カレンダー本体】
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
            mark = "●" if not df_s.empty and d_str in df_s.iloc[:, 0].astype(str).values else ""
            html += f'<a href="/?d={d_str}" target="_self" class="cal-box date-box {is_sel} {c_cls}">{day}<span class="mark">{mark}</span></a>'
html += '</div>'
st.markdown(html, unsafe_allow_html=True)

# 【本日のクイック確認】
st.divider()
tabs = st.tabs(["📌 予定", "🎒 持ち物", "📋 課題", "➕ 登録"])

with tabs[0]:
    evs = df_s[df_s.iloc[:, 0].astype(str).str.contains(sel.strftime("%Y-%m-%d"))] if not df_s.empty else []
    if len(evs) > 0:
        for v in evs.iloc[:, 1]: st.info(v)
    else: st.caption("予定なし")

with tabs[1]:
    # 持ち物リスト（中身は省略せず以前のBELONGINGSを使用してください）
    day_name = ["月","火","水","木","金","土","日"][sel.weekday()]
    st.write(f"**{day_name}曜日のセット**")
    # ここに以前の時間割ロジックを入れる

with tabs[2]:
    if not df_t.empty:
        uncompleted = df_t[df_t.iloc[:, 3].astype(str).str.upper() == "FALSE"]
        for _, row in uncompleted.head(5).iterrows(): # 直近5件だけ表示
            st.checkbox(f"{row[0]}: {row[1]}", key=row[1])

with tabs[3]:
    # 登録フォーム（ここも最小限に）
    mode = st.radio(None, ["予定", "課題清"], horizontal=True)
    with st.form("quick_add"):
        txt = st.text_input("内容")
        if st.form_submit_button("追加"):
            # 保存ロジック
            st.success("OK")
