import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
import jpholiday
import calendar

st.set_page_config(page_title="MyTool", layout="centered")

# --- 1. CSS & 持ち物データ (以前と同じなので省略可) ---
st.markdown("<style>.stAppHeader { display: none; } .main .block-container { padding-top: 0rem !important; } .calendar-wrapper { display: grid; grid-template-columns: repeat(7, 1fr); background: white; border: 1px solid #eee; } .cal-box { aspect-ratio: 1/1; display: flex; flex-direction: column; justify-content: center; align-items: center; text-decoration: none; border: 0.5px solid #f8f8f8; color: #444; } .head-box { font-size: 10px; font-weight: bold; background: #fafafa; height: 30px; } .date-box { font-size: 16px; position: relative; } .selected-box { background: #ff4b4b !important; color: white !important; border-radius: 8px; } .sun { color: #ff4b4b; } .sat { color: #007bff; } .has-event-dot { width: 6px; height: 6px; background-color: #ff9f00; border-radius: 50%; margin-top: 2px; }</style>", unsafe_allow_html=True)

BELONGINGS = {"現国": ["教科書", "ノート", "電子辞書", "核心漢字", "論理エンジン", "ステップ1.5"],"言語文化": ["教科書", "ノート", "電子辞書", "文法ノート", "グランステップ", "漢文必携"],"地総": ["教科書", "地図帳"], "歴総": ["教科書", "ワークノート"],"数基α": ["教科書I", "ノート", "CONNECT", "Focus Gold"],"数基β": ["教科書A", "ノート", "CONNECT", "Focus Gold"],"科技α": ["物理基礎", "セミナー", "ノート"], "科技β": ["生物基礎", "リードα", "ノート"],"保健": ["教科書", "図説"], "体育": ["体操服", "ルール本"], "音楽": ["教科書", "ファイル"],"コミュ I": ["Heartening", "LEAP", "Cutting Edge", "Navi"],"論表": ["EARTHRISE", "総合英語", "Workbook", "Listening"],"SP I": ["Heartening"], "家庭": ["教科書", "生活学Navi", "ファイル"],"探求基礎": ["テキスト「課題研究メソッド」"], "LT": ["（特になし）"]}
TIMETABLE = {"月":["科技β","数基α","家庭","地総","科技α","言語文化","論表"],"火":["科技α","音楽","歴総","体育","数基α","言語文化"],"水":["保健","探求基礎","論表","数基β","現国","コミュ I"],"木":["科技β","コミュ I","言語文化","家庭","音楽","数基α","LT"],"金":["地総","体育","数基β","現国","SP I","歴総"]}

# --- 2. GAS経由での読み込み (ここが重要！) ---
gas_url = st.secrets.get("GAS_URL")

@st.cache_data(ttl=5) # キャッシュを5秒にする
def load_via_gas(sheet_name):
    try:
        # GETリクエストでGASから直接データを取得
        res = requests.get(f"{gas_url}?sheet={sheet_name}")
        data = res.json()
        if sheet_name == "schedules":
            return pd.DataFrame(data, columns=["date", "content"])
        else:
            return pd.DataFrame(data, columns=["subject", "content", "deadline", "done"])
    except:
        return pd.DataFrame()

df_s = load_via_gas("schedules")
df_t = load_via_gas("tasks")

# 時間設定
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST)
if "d" in st.query_params:
    st.session_state.selected_date = datetime.strptime(st.query_params["d"], "%Y-%m-%d").date()
else:
    if 'selected_date' not in st.session_state: st.session_state.selected_date = now.date()
sel = st.session_state.selected_date

# --- 3. UI (タブ構成) ---
tabs = st.tabs(["📅 カレンダー", "🎒 持ち物", "📋 課題", "📝 予定一覧", "➕ 登録"])

with tabs[0]:
    st.write(f"### 📅 {sel.month}/{sel.day}")
    html = '<div class="calendar-wrapper">'
    for d, cls in [("日","sun"),("月",""),("火",""),("水",""),("木",""),("金",""),("土","sat")]:
        html += f'<div class="cal-box head-box {cls}">{d}</div>'
    for week in calendar.Calendar(firstweekday=6).monthdayscalendar(now.year, now.month):
        for i, day in enumerate(week):
            if day == 0: html += '<div class="cal-box"></div>'
            else:
                d_obj = datetime(now.year, now.month, day).date()
                d_str = d_obj.strftime("%Y-%m-%d")
                is_sel = "selected-box" if d_obj == sel else ""
                c_cls = "sun" if (i == 0 or jpholiday.is_holiday(d_obj)) else ("sat" if i == 6 else "")
                # 予定チェック (文字列一致で判定)
                has_ev = not df_s.empty and any(df_s["date"].astype(str) == d_str)
                dot = '<div class="has-event-dot"></div>' if has_ev else ""
                html += f'<a href="/?d={d_str}" target="_self" class="cal-box date-box {is_sel} {c_cls}">{day}{dot}</a>'
    st.markdown(html + '</div>', unsafe_allow_html=True)
    if not df_s.empty:
        today_evs = df_s[df_s["date"].astype(str) == sel.strftime("%Y-%m-%d")]
        for v in today_evs["content"]: st.info(v)

with tabs[1]:
    day_name = ["月","火","水","木","金","土","日"][sel.weekday()]
    st.write(f"### 🎒 {day_name}セット")
    if day_name in TIMETABLE:
        for sub in TIMETABLE[day_name]:
            st.write(f"**{sub}**: {' / '.join(BELONGINGS.get(sub, []))}"); st.divider()

with tabs[2]:
    st.write("### 📋 課題")
    if not df_t.empty:
        uncompleted = df_t[df_t["done"].astype(str).str.upper() == "FALSE"]
        for _, row in uncompleted.iterrows(): st.warning(f"**{row['subject']}**: {row['content']}")

with tabs[3]:
    st.write("### 📝 今後の予定")
    if not df_s.empty:
        df_s["date_dt"] = pd.to_datetime(df_s["date"])
        future = df_s[df_s["date_dt"].dt.date >= now.date()].sort_values("date_dt")
        for _, row in future.iterrows(): st.write(f"📅 {row['date_dt'].strftime('%m/%d')}: {row['content']}")

with tabs[4]:
    st.write(f"### ➕ 追加")
    mode = st.radio("種類", ["予定", "課題"], horizontal=True)
    with st.form("add", clear_on_submit=True):
        txt = st.text_input("内容")
        sub = st.selectbox("教科", list(BELONGINGS.keys())) if mode == "課題" else ""
        if st.form_submit_button("保存して更新"):
            if txt:
                payload = [sel.strftime("%Y-%m-%d"), txt] if mode == "予定" else [sub, txt, sel.strftime("%Y-%m-%d"), "FALSE"]
                requests.post(f"{gas_url}?sheet={'schedules' if mode == '予定' else 'tasks'}", json=payload)
                st.cache_data.clear()
                st.rerun()
