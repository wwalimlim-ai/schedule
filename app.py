import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
import jpholiday
import calendar

# --- 1. ページ設定 & デザイン ---
st.set_page_config(page_title="学生用マイ・ツール Pro Max", layout="centered")

st.markdown("""
    <style>
    .main .block-container { padding: 1rem 0.2rem !important; }
    .calendar-wrapper { display: grid; grid-template-columns: repeat(7, 1fr); width: 100%; border-top: 1px solid #ddd; border-left: 1px solid #ddd; background-color: white; }
    .cal-box { border-right: 1px solid #ddd; border-bottom: 1px solid #ddd; text-align: center; text-decoration: none; display: flex; flex-direction: column; justify-content: center; align-items: center; color: #333; }
    .head-box { background-color: #f8f9fa; font-weight: bold; font-size: 11px; padding: 8px 0; }
    .date-box { aspect-ratio: 1 / 1; cursor: pointer; }
    .selected-box { background-color: #ff4b4b !important; color: white !important; font-weight: bold; }
    .sun { color: red !important; }
    .sat { color: blue !important; }
    .day-text { font-size: 14px; }
    .mark-text { font-size: 9px; margin-top: -2px; }
    .belonging-item { background: #f0f2f6; padding: 5px 10px; border-radius: 5px; margin-bottom: 5px; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. PC版から移植したデータ ---
BELONGINGS = {
    "現国": ["教科書「現代の国語」", "ノート", "電子辞書", "核心漢字2500", "論理エンジン⑧-1", "現代文ステップ1.5"],
    "言語文化": ["教科書「言語文化」", "ノート", "電子辞書", "古典文法ノート", "グランステップ古典1.5", "漢文必携"],
    "地総": ["教科書「新地理総合」", "地図帳「新詳高等地図」"],
    "歴総": ["教科書「歴史総合」", "副教材「歴史総合ワークノート」"],
    "数基α": ["教科書「NEXT数学I」", "ノート", "CONNECT", "完成ノート", "Focus Gold", "短期完成ノート"],
    "数基β": ["教科書「NEXT数学A」", "ノート", "CONNECT", "完成ノート", "Focus Gold", "短期完成ノート"],
    "科技α": ["教科書「物理基礎」", "セミナー物理基礎", "ノート"],
    "科技β": ["教科書「生物基礎」", "リードα生物基礎", "コンセプトノート"],
    "保健": ["教科書「現代高等保健体育」", "図説現代高等保健"],
    "体育": ["体操服", "最新スポーツルール'26"],
    "音楽": ["教科書", "ファイル"],
    "コミュ I": ["Heartening教科書", "LEAP", "Cutting Edge Yellow", "Navi Book"],
    "論表": ["EARTHRISE", "GRAND EARTH 総合英語", "Workbook", "Listening Pre-Std", "Listening Std"],
    "SP I": ["Heartening教科書"],
    "家庭": ["教科書「新図説 家庭基礎」", "2026 生活学 Navi", "ファイル"],
    "探求基礎": ["テキスト「課題研究メソッド」"],
    "LT": ["（特になし）"]
}

# --- 3. ログイン管理 ---
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

# --- 4. 共通設定とデータ読み込み関数の定義 ---
gas_url = st.secrets.get("GAS_URL")
sheet_url = st.secrets.get("connections", {}).get("gsheets", {}).get("spreadsheet")

def load_data(sheet_name):
    """スプレッドシートからデータを読み込む関数"""
    try:
        if not sheet_url:
            return pd.DataFrame(columns=['date', 'content'])
        base_url = sheet_url.split('/edit')[0]
        csv_url = f"{base_url}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        return pd.read_csv(csv_url)
    except Exception:
        return pd.DataFrame(columns=['date', 'content'])

# ★重要：ここで先に読み込んでおく
df_s = load_data("schedules")

# 日本時間(JST)の取得
JST = timezone(timedelta(hours=+9), 'JST')
now_jst = datetime.now(JST).date()

# 状態管理
params = st.query_params
if "d" in params:
    st.session_state.selected_date = datetime.strptime(params["d"], "%Y-%m-%d").date()
elif 'selected_date' not in st.session_state:
    st.session_state.selected_date = now_jst

default_year = now_jst.year
default_month = now_jst.month

# --- 5. メイン画面 ---
st.title("🎓 学生用ツール Pro")
tabs = st.tabs(["📅 カレンダー", "🎒 持ち物/時間割", "📝 課題/予定追加"])

# 【タブ1: カレンダー】
with tabs[0]:
    c1, c2 = st.columns(2)
    y = c1.selectbox("年", [2025, 2026], index=([2025, 2026].index(default_year)))
    m = c2.selectbox("月", list(range(1, 13)), index=default_month - 1)
    
    html = '<div class="calendar-wrapper">'
    for d, cls in [("日","sun"), ("月",""), ("火",""), ("水",""), ("木",""), ("金",""), ("土","sat")]:
        html += f'<div class="cal-box head-box {cls}">{d}</div>'

    weeks = calendar.Calendar(firstweekday=6).monthdayscalendar(y, m)
    for week in weeks:
        for i, day in enumerate(week):
            if day == 0: html += '<div class
weeks = calendar.Calendar(firstweekday=6).monthdayscalendar(y, m)
    for week in weeks:
        for i, day in enumerate(week):
            if day == 0:
                # ここを1行で書くか、正しく閉じます
                html += '<div class="cal-box" style="background:#fcfcfc;"></div>'
            else:
                d_obj = datetime(y, m, day).date()
                d_str = d_obj.strftime("%Y-%m-%d")
                is_sel = "selected-box" if d_obj == st.session_state.selected_date else ""
                is_hol = jpholiday.is_holiday(d_obj)
                c_cls = "sun" if (i == 0 or is_hol) else ("sat" if i == 6 else "")
                
                # 予定があるかチェック
                has_event = not df_s.empty and d_str in df_s.iloc[:, 0].astype(str).values
                mark = "🎌" if is_hol else ("📍" if has_event else "")
                
                # aタグの生成（ここも途中で改行されないよう注意）
                link_html = f'<a href="/?d={d_str}" target="_self" class="cal-box date-box {is_sel} {c_cls}">'
                html += f'{link_html}<span class="day-text">{day}</span><span class="mark-text">{mark}</span></a>'
