import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime, timedelta, timezone
import jpholiday
import calendar

# --- 1. ページ設定（スマホ爆速UI用） ---
st.set_page_config(page_title="MyTool", layout="centered")

st.markdown("""
    <style>
    .stAppHeader { display: none; }
    .main .block-container { padding-top: 0rem !important; padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 2px; position: sticky; top: 0; z-index: 1000; background-color: white; }
    .calendar-wrapper { display: grid; grid-template-columns: repeat(7, 1fr); background: white; border: 1px solid #eee; }
    .cal-box { aspect-ratio: 1/1; display: flex; flex-direction: column; justify-content: center; align-items: center; text-decoration: none; border: 0.5px solid #f8f8f8; color: #444; }
    .selected-box { background: #ff4b4b !important; color: white !important; border-radius: 8px; font-weight: bold; }
    .has-event-dot { width: 6px; height: 6px; background-color: #ff9f00; border-radius: 50%; margin-top: 2px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. データ定義 ---
BELONGINGS = {"現国": ["教科書", "ノート", "電子辞書", "核心漢字", "論理エンジン", "ステップ1.5"],"言語文化": ["教科書", "ノート", "電子辞書", "文法ノート", "グランステップ", "漢文必携"],"地総": ["教科書", "地図帳"], "歴総": ["教科書", "ワークノート"],"数基α": ["教科書I", "ノート", "Focus Gold"],"数基β": ["教科書A", "ノート", "Focus Gold"],"科技α": ["物理基礎", "セミナー", "ノート"], "科技β": ["生物基礎", "リードα", "ノート"],"保健": ["教科書", "図説"], "体育": ["体操服", "ルール本"],"コミュ I": ["Heartening", "LEAP", "Cutting Edge"],"論表": ["EARTHRISE", "Workbook"],"SP I": ["Heartening"],"家庭": ["教科書", "生活学Navi"],"探求基礎": ["課題研究メソッド"],"LT": ["（特になし）"]}
TIMETABLE = {"月":["科技β","数基α","家庭","地総","科技α","言語文化","論表"],"火":["科技α","音楽","歴総","体育","数基α","言語文化"],"水":["保健","探求基礎","論表","数基β","現国","コミュ I"],"木":["科技β","コミュ I","言語文化","家庭","音楽","数基α","LT"],"金":["地総","体育","数基β","現国","SP I","歴総"]}

# --- 3. GAS通信ロジック（ここを強化しました） ---
gas_url = st.secrets.get("GAS_URL")

@st.cache_data(ttl=5)
def load_data(sheet_name):
    try:
        res = requests.get(f"{gas_url}?sheet={sheet_name}", timeout=10)
        data = res.json()
        if not data: return pd.DataFrame()
        
        df = pd.DataFrame(data)
        
        # 列の数に関わらず、必要な列だけを抜き出して名前を付ける
        if sheet_name == "schedules":
            # 1列目が日付、2列目が内容
            df = df.iloc[:, [0, 1]]
            df.columns = ["date", "content"]
        else:
            # 1教科, 2内容, 3期限, 4完了
            df = df.iloc[:, [0, 1, 2, 3]]
            df.columns = ["subject", "content", "deadline", "done"]
        return df
    except Exception as e:
        # エラーが起きたら画面の端に出す（デバッグ用）
        st.sidebar.write(f"Error ({sheet_name}): {e}")
        return pd.DataFrame()

df_s = load_data("schedules")
df_t = load_data("tasks")

# 時間・日付管理
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST)
if "d" in st.query_params:
    st.session_state.selected_date = datetime.strptime(st.query_params["d"], "%Y-%m-%d").date()
elif 'selected_date' not in st.session_state:
    st.session_state.selected_date = now.date()
sel = st.session_state.selected_date

# --- 4. メインUI ---
tabs = st.tabs(["📅 カレ", "🎒 持ち物", "📋 課題", "📝 予定一覧", "➕ 登録"])

with tabs[0]: # カレンダー
    st.write(f"### 📅 {sel.month}/{sel.day}")
    html = '<div class="calendar-wrapper">'
    for d, c in [("日","red"),("月",""),("火",""),("水",""),("木",""),("金",""),("土","blue")]:
        html += f'<div class="cal-box" style="font-size:10px; color:{c};">{d}</div>'
    for week in calendar.Calendar(firstweekday=6).monthdayscalendar(now.year, now.month):
        for day in week:
            if day == 0: html += '<div class="cal-box"></div>'
            else:
                d_obj = datetime(now.year, now.month, day).date()
                d_str = d_obj.strftime("%Y-%m-%d")
                is_sel = "selected-box" if d_obj == sel else ""
                # 予定チェック（日付を文字列にして比較）
                has_ev = not df_s.empty and any(df_s["date"].astype(str).str.contains(d_str))
                dot = '<div class="has-event-dot"></div>' if has_ev else ""
                html += f'<a href="/?d={d_str}" target="_self" class="cal-box {is_sel}">{day}{dot}</a>'
    st.markdown(html + '</div>', unsafe_allow_html=True)
    if not df_s.empty:
        # 今日の予定を表示
        today_evs = df_s[df_s["date"].astype(str).str.contains(sel.strftime("%Y-%m-%d"))]
        for v in today_evs["content"]: st.info(v)

with tabs[1]: # 持ち物
    day_name = ["月","火","水","木","金","土","日"][sel.weekday()]
    st.write(f"### 🎒 {day_name}曜日のセット")
    if day_name in TIMETABLE:
        for sub in TIMETABLE[day_name]:
            st.write(f"**{sub}**: {' / '.join(BELONGINGS.get(sub, []))}")
            st.divider()
    else: st.write("お休みです")

with tabs[2]: # 課題
    st.write("### 📋 未完了の課題")
    if not df_t.empty:
        uncompleted = df_t[df_t["done"].astype(str).str.upper() == "FALSE"]
        for _, row in uncompleted.iterrows():
            st.warning(f"**{row['subject']}**: {row['content']} ({row['deadline']})")
    else: st.success("課題は全部完了！")

with tabs[3]: # 予定一覧
    st.write("### 📝 今後の予定")
    if not df_s.empty:
        df_s["dt"] = pd.to_datetime(df_s["date"], errors='coerce')
        future = df_s[df_s["dt"].dt.date >= now.date()].sort_values("dt")
        for _, row in future.iterrows():
            st.write(f"📅 {row['dt'].strftime('%m/%d')}: {row['content']}")

with tabs[4]: # 登録
    st.write(f"### ➕ {sel.month}/{sel.day} に追加")
    mode = st.radio("種類", ["予定", "課題"], horizontal=True)
    with st.form("add", clear_on_submit=True):
        txt = st.text_input("内容")
        sub = st.selectbox("教科(課題のみ)", list(BELONGINGS.keys())) if mode == "課題" else ""
        if st.form_submit_button("保存して更新"):
            if txt:
                payload = [sel.strftime("%Y-%m-%d"), txt] if mode == "予定" else [sub, txt, sel.strftime("%Y-%m-%d"), "FALSE"]
                requests.post(f"{gas_url}?sheet={'schedules' if mode == '予定' else 'tasks'}", json=payload)
                st.success("保存しました！")
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()
