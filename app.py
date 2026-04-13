import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime, timedelta, timezone
import jpholiday
import calendar

# --- 1. ページ設定 ---
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

# --- 3. GAS通信ロジック ---
gas_url = st.secrets.get("GAS_URL")

@st.cache_data(ttl=5)
def load_data(sheet_name):
    try:
        res = requests.get(f"{gas_url}?sheet={sheet_name}", timeout=10)
        data = res.json()
        if not data: return pd.DataFrame()
        df = pd.DataFrame(data)
        if sheet_name == "schedules":
            df = df.iloc[:, [0, 1]]
            df.columns = ["date", "content"]
        else:
            df = df.iloc[:, [0, 1, 2, 3]]
            df.columns = ["subject", "content", "deadline", "done"]
        return df
    except Exception as e:
        return pd.DataFrame()

df_s = load_data("schedules")
df_t = load_data("tasks")

# 【重要】日本の現在時刻を確実に取得
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST)
today_date = now.date()

if "d" in st.query_params:
    st.session_state.selected_date = datetime.strptime(st.query_params["d"], "%Y-%m-%d").date()
elif 'selected_date' not in st.session_state:
    st.session_state.selected_date = today_date
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
                # --- これに書き換える ---
html += f'<a href="/?d={d_str}" target="_self" class="cal-box {is_sel}">{day}</a>'
    st.markdown(html + '</div>', unsafe_allow_html=True)
    if not df_s.empty:
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

with tabs[3]: # 【予定一覧：ISO形式対応版】
    st.write("### 📝 今後の予定")
    if not df_s.empty:
        list_df = df_s.copy()
        
        # 1. ISO形式（TやZが入った形式）を考慮して変換
        # utc=Trueにすることで、末尾の'Z'を正しく処理します
        list_df["dt_obj"] = pd.to_datetime(list_df.iloc[:, 0], errors='coerce', utc=True)
        
        # 2. 日本時間(JST)に変換してから、タイムゾーン情報を消す（比較のため）
        list_df["dt_obj"] = list_df["dt_obj"].dt.tz_convert('Asia/Tokyo').dt.tz_localize(None)
        
        # 3. 変換失敗（NaT）を削除
        list_df = list_df.dropna(subset=["dt_obj"])
        
        # 4. 「今日」も含む判定（今日の0時0分より後のデータを取得）
        today_start = datetime(now.year, now.month, now.day)
        future = list_df[list_df["dt_obj"] >= today_start].sort_values("dt_obj")
        
        if not future.empty:
            for _, row in future.iterrows():
                # 日本語で見やすく表示
                d_disp = row['dt_obj'].strftime('%m/%d')
                st.write(f"📅 **{d_disp}**: {row.iloc[1]}")
                st.divider()
        else:
            st.info("今日以降の予定はありません。")
    else:
        st.write("予定データがありません。")

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
