import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import jpholiday
import calendar

# --- ページ設定 ---
st.set_page_config(page_title="学生用ツール", layout="centered")

# 【超強力CSS】カレンダーの曜日と時間割の改行を徹底的に防ぐ
st.markdown("""
    <style>
    /* 画面全体の余白を削る */
    .main .block-container { padding-top: 1rem; padding-left: 0.5rem; padding-right: 0.5rem; }
    
    /* カレンダーの曜日・ボタンの文字サイズと余白 */
    div[data-testid="column"] {
        padding: 0 !important;
        min-width: 0 !important;
    }
    div.stButton > button {
        font-size: 12px !important;
        padding: 0 !important;
        height: 40px !important;
        min-width: 0 !important;
    }
    
    /* 曜日ヘッダーの文字を小さくして横に並べる */
    .stMarkdown p {
        font-size: 12px !important;
        text-align: center;
        margin-bottom: 0px;
    }

    /* 時間割の表をスマホでも横一行に */
    .stTable td {
        white-space: nowrap !important;
        font-size: 11px !important;
        padding: 4px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 以下、ロジック ---

# Secrets & Data Loading
correct_pw = st.secrets.get("MY_PASSWORD")
gas_url = st.secrets.get("GAS_URL")
sheet_url = st.secrets.get("connections", {}).get("gsheets", {}).get("spreadsheet")

pw = st.sidebar.text_input("パスワード", type="password")
if pw != correct_pw:
    st.info("パスワードを入力してください。")
    st.stop()

if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.now().date()

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
    col_sel1, col_sel2 = st.columns([1, 1])
    sel_year = col_sel1.selectbox("年", [now.year, now.year+1], index=0, label_visibility="collapsed")
    sel_month = col_sel2.selectbox("月", list(range(1, 13)), index=now.month-1, label_visibility="collapsed")
    
    cal = calendar.monthcalendar(sel_year, sel_month)
    days_labels = ["月", "火", "水", "木", "金", "土", "日"]
    
    # 曜日を一行に並べる
    header_cols = st.columns(7)
    for i, label in enumerate(days_labels):
        header_cols[i].markdown(f"**{label}**")

    # 日付を一行に並べる
    for week in cal:
        day_cols = st.columns(7)
        for i, day in enumerate(week):
            if day != 0:
                d_obj = datetime(sel_year, sel_month, day).date()
                d_str = d_obj.strftime("%Y-%m-%d")
                has_ev = not df_s.empty and d_str in df_s.iloc[:, 0].astype(str).values
                is_hol = jpholiday.is_holiday(d_obj)
                
                label = str(day)
                if is_hol: label += "🎌"
                elif has_ev: label += "📍"
                
                if day_cols[i].button(label, key=f"d_{d_str}"):
                    st.session_state.selected_date = d_obj
            else:
                day_cols[i].write("")

    st.divider()
    sel = st.session_state.selected_date
    st.subheader(f"🔍 {sel.strftime('%m/%d')} の情報")
    hol_n = jpholiday.is_holiday_name(sel)
    if hol_n: st.error(f"🎌 {hol_n}")
    
    if not df_s.empty:
        day_evs = df_s[df_s.iloc[:, 0].astype(str) == sel.strftime("%Y-%m-%d")]
        if not day_evs.empty:
            for v in day_evs.iloc[:, 1]: st.info(f"📍 {v}")
        else: st.write("予定なし")

# --- 2. 予定追加 ---
with tab_ev:
    st.subheader("予定の登録")
    st.write(f"選択日: **{st.session_state.selected_date}**")
    ev_text = st.text_input("予定を入力")
    if st.button("保存", key="save_ev"):
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
        t_msg = st.text_input("内容")
        if st.form_submit_button("課題を保存"):
            if t_msg:
                requests.post(f"{gas_url}?sheet=tasks", json=[t_sub, t_msg, st.session_state.selected_date.strftime("%Y-%m-%d"), "FALSE"])
                st.success("保存完了")
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
