import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import jpholiday
import calendar

# --- ページ設定 ---
st.set_page_config(page_title="学生用ツール", layout="centered")

# 【強化版CSS】改行を絶対に許さず、文字サイズをスマホに最適化
st.markdown("""
    <style>
    /* 表全体のフォントサイズを調整し、改行を禁止 */
    .stTable {
        font-size: 12px !important;
    }
    .stTable td {
        white-space: nowrap !important;
        padding: 5px !important;
        min-width: 60px !important;
    }
    /* カレンダーのボタンの文字を少し小さくして収まりを良くする */
    div.stButton > button {
        font-size: 14px !important;
        padding: 0px !important;
        height: 50px !important;
    }
    /* 予定がある日の📍や🎌を小さく表示 */
    div.stButton > button p {
        line-height: 1.2 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 以下、前回のロジックと同じ（ここから下を丸ごと上書きしてください） ---

# Secrets & Data Loading
correct_pw = st.secrets.get("MY_PASSWORD")
gas_url = st.secrets.get("GAS_URL")
sheet_url = st.secrets.get("connections", {}).get("gsheets", {}).get("spreadsheet")

# サイドバー：ログイン
st.sidebar.title("🔐 Login")
pw = st.sidebar.text_input("パスワード", type="password")

if pw != correct_pw:
    st.info("パスワードを入力してください。")
    st.stop()

# --- 状態保持 ---
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.now().date()

# --- データ読み込み ---
def load_data(sheet_name):
    if not sheet_url: return pd.DataFrame()
    try:
        base_url = sheet_url.split('/edit')[0]
        csv_url = f"{base_url}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        return pd.read_csv(csv_url)
    except: return pd.DataFrame()

df_s = load_data("schedules")
df_t = load_data("tasks")

SUBJECTS = ["教科なし", "現国", "言語文化", "地総", "歴総", "数基α", "数基β", "科技α", "科技β", "コミュ I", "論表", "SP I", "保健", "体育", "音楽", "家庭", "探求基礎", "LT"]

st.title("🎓 学生用ツール")
tab_cal, tab_ev, tab_task, tab_time = st.tabs(["📅 カレンダー", "📌 予定追加", "📝 課題追加", "⏰ 時間割"])

# --- 1. カレンダータブ ---
with tab_cal:
    now = datetime.now()
    col1, col2 = st.columns([2, 1])
    sel_year = col1.selectbox("年", [now.year, now.year+1], index=0, label_visibility="collapsed")
    sel_month = col2.selectbox("月", list(range(1, 13)), index=now.month-1, label_visibility="collapsed")
    cal = calendar.monthcalendar(sel_year, sel_month)
    days_labels = ["月", "火", "水", "木", "金", "土", "日"]
    cols = st.columns(7)
    for i, label in enumerate(days_labels): cols[i].write(f"**{label}**")
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day != 0:
                d_obj = datetime(sel_year, sel_month, day).date()
                d_str = d_obj.strftime("%Y-%m-%d")
                has_ev = not df_s.empty and d_str in df_s.iloc[:, 0].astype(str).values
                is_hol = jpholiday.is_holiday(d_obj)
                label = str(day)
                if is_hol: label += "\n🎌"
                elif has_ev: label += "\n📍"
                if cols[i].button(label, key=f"d_{d_str}_{i}"):
                    st.session_state.selected_date = d_obj
            else: cols[i].write("")
    st.divider()
    sel = st.session_state.selected_date
    st.subheader(f"🔍 {sel.strftime('%m月%d日')} の情報")
    hol_n = jpholiday.is_holiday_name(sel)
    if hol_n: st.error(f"🎌 祝日: {hol_n}")
    if not df_s.empty:
        day_evs = df_s[df_s.iloc[:, 0].astype(str) == sel.strftime("%Y-%m-%d")]
        if not day_evs.empty:
            for v in day_evs.iloc[:, 1]: st.info(f"📍 予定: {v}")
        else: st.write("予定なし")

# --- 2. 予定追加 ---
with tab_ev:
    st.subheader("予定の登録")
    st.write(f"選択中: **{st.session_state.selected_date}**")
    ev_text = st.text_input("予定の内容を入力")
    if st.button("この日で保存"):
        if ev_text:
            requests.post(f"{gas_url}?sheet=schedules", json=[st.session_state.selected_date.strftime("%Y-%m-%d"), ev_text])
            st.success("保存完了！")
            st.rerun()

# --- 3. 課題追加 ---
with tab_task:
    st.subheader("課題の登録")
    st.write(f"期限日: **{st.session_state.selected_date}**")
    with st.form("task_f"):
        t_sub = st.selectbox("教科", SUBJECTS)
        t_msg = st.text_input("課題内容")
        if st.form_submit_button("課題を保存"):
            if t_msg:
                requests.post(f"{gas_url}?sheet=tasks", json=[t_sub, t_msg, st.session_state.selected_date.strftime("%Y-%m-%d"), "FALSE"])
                st.success("課題を保存しました")
                st.rerun()

# --- 4. 時間割 ---
with tab_time:
    st.subheader("週間時間割")
    timetable = {
        "月": ["科技β", "数基α", "家庭", "地総", "科技α", "言語文化", "論表"],
        "火": ["科技α", "音楽", "歴総", "体育", "数基α", "言語文化", "-"],
        "水": ["保健", "探求", "論表", "数基β", "現国", "コミュI", "-"],
        "木": ["科技β", "コミュI", "言語文化", "家庭", "音楽", "数基α", "LT"],
        "金": ["地総", "体育", "数基β", "現国", "SP I", "歴総", "-"]
    }
    st.table(pd.DataFrame(timetable, index=[f"{i+1}限" for i in range(7)]))
    st.divider()
    st.subheader("🎒 持ち物チェック")
    belongings = {"科技": "レポート・実験着", "体育": "体操服・ジャージ", "音楽": "ファイル・楽譜", "家庭": "エプロン・セット"}
    today_w = datetime.now().weekday()
    days_map = ["月", "火", "水", "木", "金", "土", "日"]
    if today_w < 5:
        today_subs = timetable[days_map[today_w]]
        needed = [v for k, v in belongings.items() if any(k in s for s in today_subs)]
        if needed: st.warning("今日の持ち物: " + " / ".join(set(needed)))
        else: st.write("特別な持ち物は不要です。")
