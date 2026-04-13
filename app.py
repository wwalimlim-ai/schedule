import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime, timedelta, timezone
import calendar

# --- 1. ページ設定 ---
st.set_page_config(page_title="MyTool", layout="centered")

st.markdown("""
    <style>
    .stAppHeader { display: none; }
    .main .block-container { padding-top: 0rem !important; padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 2px; position: sticky; top: 0; z-index: 1000; background-color: white; }
    .calendar-wrapper { display: grid; grid-template-columns: repeat(7, 1fr); background: white; border: 1px solid #eee; }
    .cal-box { aspect-ratio: 1/1; display: flex; flex-direction: column; justify-content: center; align-items: center; text-decoration: none; border: 0.5px solid #f8f8f8; color: #444; font-size: 16px; }
    .selected-box { background: #ff4b4b !important; color: white !important; border-radius: 8px; font-weight: bold; }
    .today-box { border: 2px solid #ff4b4b !important; border-radius: 8px; color: #ff4b4b; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. データ定義（更新済み） ---
BELONGINGS = {
    "現国": ["教科書「現代の国語」", "ノート", "電子辞書", "大学入試に出た核心漢字2500+語彙1000", "論理エンジンスパイラルレベル⑧-1", "力をつける現代文ステップ1.5"],
    "言語文化": ["教科書「言語文化」", "ノート", "電子辞書", "完全マスター古典文法＆準拠ノート", "グランステップ1.5", "漢文必携"],
    "地総": ["教科書「新地理総合」", "地図帳「新詳高等地図」"],
    "歴総": ["教科書「歴史総合」", "副教材「歴史総合ワークノート」"],
    "数基α": ["教科書「NEXT数学I」", "ノート", "CONNECT「数学I+A」", "Focus Gold", "完成ノート", "短期完成ノート"],
    "数基β": ["教科書「数学A」", "ノート", "CONNECT数学I+A", "Focus Gold", "完成ノート", "短期完成ノート"],
    "科技α": ["教科書「物理基礎」", "副教材「セミナー物理基礎」", "ノート"],
    "科技β": ["教科書「生物基礎」", "問題集「リードα 生物基礎」", "コンセプトノート 生物基礎"],
    "保健": ["教科書「現代高等保健体育」", "図説現代高等保健"],
    "体育": ["体操服", "イラストでみる最新スポーツルール'26"],
    "コミュ I": ["Heartening教科書", "LEAP", "Cutting Edge Yellow本体", "Navi Book"],
    "論表": ["EARTHRISE教科書", "GRAND EARTH 新々総合英語", "GRAND EARTH 48 Stages Workbook", "Focus on Listening Pre-Standard(月曜日のみ)", "Focus on Listening Standard(Preの後)"],
    "SP I": ["Heartening教科書"],
    "家庭": ["教科書「新図説 家庭基礎」", "2026 生活学Navi", "ファイル"],
    "探求基礎": ["課題研究メソッド"],
    "LT": ["（特になし）"]
}
TIMETABLE = {"月":["科技β","数基α","家庭","地総","科技α","言語文化","論表"],"火":["科技α","音楽","歴総","体育","数基α","言語文化"],"水":["保健","探求基礎","論表","数基β","現国","コミュ I"],"木":["科技β","コミュ I","言語文化","家庭","音楽","数基α","LT"],"金":["地総","体育","数基β","現国","SP I","歴総"]}

gas_url = st.secrets.get("GAS_URL")

@st.cache_data(ttl=5)
def load_data(sheet_name):
    try:
        res = requests.get(f"{gas_url}?sheet={sheet_name}", timeout=10)
        data = res.json()
        if not data: return pd.DataFrame()
        df = pd.DataFrame(data)
        if sheet_name == "schedules":
            df = df.iloc[:, [0, 1, 2]]; df.columns = ["date", "content", "done"]
        else:
            df = df.iloc[:, [0, 1, 2, 3]]; df.columns = ["subject", "content", "deadline", "done"]
        return df
    except: return pd.DataFrame()

df_s = load_data("schedules")
df_t = load_data("tasks")

JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST)
today_date = now.date()

if 'view_year' not in st.session_state: st.session_state.view_year = now.year
if 'view_month' not in st.session_state: st.session_state.view_month = now.month
if 'selected_date' not in st.session_state: st.session_state.selected_date = today_date

if "d" in st.query_params:
    st.session_state.selected_date = datetime.strptime(st.query_params["d"], "%Y-%m-%d").date()

sel = st.session_state.selected_date

# --- 4. メインUI ---
tabs = st.tabs(["📅 カレ", "🎒 時間割", "📋 課題", "📝 予定一覧", "➕ 登録"])

with tabs[0]: # カレンダー
    # 年月の選択用UI
    c1, c2 = st.columns(2)
    
    # 【ここを修正！】現在の年から前後5年分を自動でリストにする
    year_options = list(range(now.year - 2, now.year + 6)) 
    view_y = c1.selectbox("年", year_options, index=year_options.index(now.year))
    
    view_m = c2.selectbox("月", range(1, 13), index=st.session_state.view_month-1)
    
    html = '<div class="calendar-wrapper">'
    for d, c in [("日","red"),("月",""),("火",""),("水",""),("木",""),("金",""),("土","blue")]:
        html += f'<div class="cal-box" style="font-size:10px; color:{c};">{d}</div>'
    for week in calendar.Calendar(firstweekday=6).monthdayscalendar(view_y, view_m):
        for day in week:
            if day == 0: html += '<div class="cal-box"></div>'
            else:
                d_obj = datetime(view_y, view_m, day).date()
                d_str = d_obj.strftime("%Y-%m-%d")
                is_sel = "selected-box" if d_obj == sel else ""
                is_today = "today-box" if d_obj == today_date else ""
                html += f'<a href="/?d={d_str}" target="_self" class="cal-box {is_sel} {is_today}">{day}</a>'
    st.markdown(html + '</div>', unsafe_allow_html=True)
    
    st.write("")
    st.subheader(f"📌 {sel.month}/{sel.day} の予定")
    if not df_s.empty:
        day_evs = df_s[(df_s["date"].astype(str).str.contains(sel.strftime("%Y-%m-%d"))) & (df_s["done"].astype(str).str.upper() == "FALSE")]
        if not day_evs.empty:
            for _, row in day_evs.iterrows():
                col1, col2 = st.columns([4, 1])
                col1.write(f"・ {row['content']}")
                if col2.button("✅", key=f"done_cal_{row['content']}"):
                    requests.post(f"{gas_url}?sheet=schedules&action=complete", json=["", row["content"]])
                    st.cache_data.clear(); st.rerun()
        else: st.write("（予定はありません）")

with tabs[1]: # 時間割
    day_name = ["月","火","水","木","金","土","日"][sel.weekday()]
    st.write(f"### 🎒 {day_name}の時間割")
    if day_name in TIMETABLE:
        for sub in TIMETABLE[day_name]:
            st.write(f"**{sub}**")
            for item in BELONGINGS.get(sub, []):
                st.write(f"　- {item}")
            st.divider()
    else: st.write("お休みです")

with tabs[2]: # 課題
    st.write("### 📋 未完了の課題")
    if not df_t.empty:
        uncompleted = df_t[df_t["done"].astype(str).str.upper() == "FALSE"]
        for _, row in uncompleted.iterrows():
            col1, col2 = st.columns([4, 1])
            col1.warning(f"**{row['subject']}**: {row['content']}")
            if col2.button("✅", key=f"done_task_{row['content']}"):
                requests.post(f"{gas_url}?sheet=tasks&action=complete", json=["", row["content"]])
                st.cache_data.clear(); st.rerun()
    else: st.success("課題は全部完了！")

with tabs[3]: # 予定一覧
    st.write("### 📝 今後の予定")
    if not df_s.empty:
        list_df = df_s[df_s["done"].astype(str).str.upper() == "FALSE"].copy()
        list_df["dt_obj"] = pd.to_datetime(list_df["date"], errors='coerce', utc=True)
        list_df["dt_obj"] = list_df["dt_obj"].dt.tz_convert('Asia/Tokyo').dt.tz_localize(None)
        list_df = list_df.dropna(subset=["dt_obj"])
        future = list_df[list_df["dt_obj"] >= datetime(now.year, now.month, now.day)].sort_values("dt_obj")
        for _, row in future.iterrows():
            col1, col2 = st.columns([4, 1])
            col1.write(f"📅 **{row['dt_obj'].strftime('%m/%d')}**: {row['content']}")
            if col2.button("✅", key=f"done_list_{row['content']}"):
                requests.post(f"{gas_url}?sheet=schedules&action=complete", json=["", row["content"]])
                st.cache_data.clear(); st.rerun()
    else: st.write("予定なし")

with tabs[4]: # 登録
    st.write(f"### ➕ 追加")
    mode = st.radio("種類", ["予定", "課題"], horizontal=True)
    with st.form("add", clear_on_submit=True):
        txt = st.text_input("内容")
        sub = st.selectbox("教科(課題のみ)", list(BELONGINGS.keys())) if mode == "課題" else ""
        if st.form_submit_button("保存して更新"):
            if txt:
                p = [sel.strftime("%Y-%m-%d"), txt, "FALSE"] if mode == "予定" else [sub, txt, sel.strftime("%Y-%m-%d"), "FALSE"]
                requests.post(f"{gas_url}?sheet={'schedules' if mode == '予定' else 'tasks'}", json=p)
                st.cache_data.clear(); time.sleep(1); st.rerun()
