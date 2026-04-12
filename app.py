import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import jpholiday

# --- ページ設定 ---
st.set_page_config(page_title="学生用ツール", layout="centered")

# CSS: 時間割の改行防止
st.markdown("""
    <style>
    .stTable td { white-space: nowrap !important; }
    </style>
    """, unsafe_allow_html=True)

# Secrets & Data Loading
correct_pw = st.secrets.get("MY_PASSWORD")
gas_url = st.secrets.get("GAS_URL")
sheet_url = st.secrets.get("connections", {}).get("gsheets", {}).get("spreadsheet")

pw = st.sidebar.text_input("パスワード", type="password")
if pw != correct_pw:
    st.info("パスワードを入力してください。")
    st.stop()

def load_data(sheet_name):
    if not sheet_url: return pd.DataFrame()
    try:
        base_url = sheet_url.split('/edit')[0]
        csv_url = f"{base_url}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        return pd.read_csv(csv_url)
    except: return pd.DataFrame()

df_s = load_data("schedules")
df_t = load_data("tasks")

SUBJECTS = [
    "教科なし", "現国", "言語文化", "地総", "歴総", "数基α", "数基β", 
    "科技α", "科技β", "コミュ I", "論表", "SP I", "保健", "体育", 
    "音楽", "家庭", "探求基礎", "LT"
]

# --- メインコンテンツ ---
st.title("🎓 学生用ツール")

tab_cal, tab_ev, tab_task, tab_time = st.tabs(["📅 カレンダー", "📌 予定追加", "📝 課題追加", "⏰ 時間割"])

# --- 1. カレンダータブ ---
with tab_cal:
    st.subheader("予定・祝日の確認")
    check_date = st.date_input("確認したい日を選択", datetime.now(), key="cal_check")
    
    # 祝日
    hol_n = jpholiday.is_holiday_name(check_date)
    if hol_n: st.error(f"🎌 祝日: {hol_n}")
    
    # 予定
    d_str = check_date.strftime("%Y-%m-%d")
    if not df_s.empty:
        evs = df_s[df_s.iloc[:, 0].astype(str) == d_str]
        if not evs.empty:
            for v in evs.iloc[:, 1]: st.info(f"📍 予定: {v}")
        else: st.write("予定なし")

# --- 2. 予定追加（内容を自由入力に変更） ---
with tab_ev:
    st.subheader("予定の登録")
    ev_date = st.date_input("日にちを選択", datetime.now(), key="ev_date_input")
    # 入力フォームに変更
    ev_text = st.text_input("予定の内容を入力", placeholder="例：部活、塾、〇〇の誕生日など")
    
    if st.button("予定を保存"):
        if ev_text:
            requests.post(f"{gas_url}?sheet=schedules", json=[ev_date.strftime("%Y-%m-%d"), ev_text])
            st.success("保存完了！")
            st.rerun()
        else:
            st.warning("内容を入力してください")

# --- 3. 課題追加 ---
with tab_task:
    st.subheader("課題の登録")
    with st.form("task_f"):
        t_sub = st.selectbox("教科", SUBJECTS)
        t_msg = st.text_input("課題内容")
        t_due = st.date_input("期限", datetime.now())
        if st.form_submit_button("課題を保存"):
            if t_msg:
                requests.post(f"{gas_url}?sheet=tasks", json=[t_sub, t_msg, t_due.strftime("%Y-%m-%d"), "FALSE"])
                st.success("課題を保存しました")
                st.rerun()

# --- 4. 時間割タブ ---
with tab_time:
    st.subheader("週間時間割")
    timetable = {
        "月": ["科技β", "数基α", "家庭", "地総", "科技α", "言語文化", "論表"],
        "火": ["科技α", "音楽", "歴総", "体育", "数基α", "言語文化", "-"],
        "水": ["保健", "探求基礎", "論表", "数基β", "現国", "コミュ I", "-"],
        "木": ["科技β", "コミュ I", "言語文化", "家庭", "音楽", "数基α", "LT"],
        "金": ["地総", "体育", "数基β", "現国", "SP I", "歴総", "-"]
    }
    st.table(pd.DataFrame(timetable, index=[f"{i+1}限" for i in range(7)]))
