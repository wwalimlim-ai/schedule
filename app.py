import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import jpholiday
import calendar

# --- ページ設定 ---
st.set_page_config(page_title="学生用ツール", layout="centered")

# 【最終兵器CSS】標準レイアウトを無視して強制的に7列グリッドを作る
st.markdown("""
    <style>
    /* 全体の余白削除 */
    .main .block-container { padding: 1rem 0.2rem !important; }

    /* 7列固定グリッド */
    .grid-parent {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 2px;
        width: 100%;
    }

    /* 曜日のスタイル */
    .day-header {
        text-align: center;
        font-weight: bold;
        font-size: 12px;
        padding: 5px 0;
    }

    /* ボタンの強制スタイル（スマホでも絶対横並び） */
    div.stButton > button {
        width: 100% !important;
        aspect-ratio: 1 / 1 !important; /* 正方形に近づける */
        padding: 0 !important;
        font-size: 12px !important;
        min-width: 0 !important;
        height: auto !important;
        line-height: 1.2 !important;
        border-radius: 4px !important;
    }

    /* 時間割表の改行防止 */
    .stTable td {
        white-space: nowrap !important;
        font-size: 11px !important;
        padding: 4px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Secrets & Data Loading
correct_pw = st.secrets.get("MY_PASSWORD")
gas_url = st.secrets.get("GAS_URL")
sheet_url = st.secrets.get("connections", {}).get("gsheets", {}).get("spreadsheet")

pw = st.sidebar.text_input("パスワード", type="password")
if pw != correct_pw:
    st.info("ログインしてください。")
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

# --- 1. カレンダータブ（完全固定7列） ---
with tab_cal:
    now = datetime.now()
    c1, c2 = st.columns(2)
    sel_year = c1.selectbox("年", [now.year, now.year+1], index=0, label_visibility="collapsed")
    sel_month = c2.selectbox("月", list(range(1, 13)), index=now.month-1, label_visibility="collapsed")
    
    # 曜日ヘッダー
    st.markdown(f"""
        <div class="grid-parent">
            <div class="day-header" style="color:red;">日</div>
            <div class="day-header">月</div><div class="day-header">火</div><div class="day-header">水</div>
            <div class="day-header">木</div><div class="day-header">金</div>
            <div class="day-header" style="color:blue;">土</div>
        </div>
    """, unsafe_allow_html=True)

    # 日曜始まりのカレンダー
    cal_obj = calendar.Calendar(firstweekday=6)
    weeks = cal_obj.monthdayscalendar(sel_year, sel_month)

    # 日付ボタンエリア
    for week in weeks:
        # st.columns(7) の引数 gap="extra-small" を指定しつつ、
        # CSSで強制的に横並びを維持する
        cols = st.columns(7, gap="small") 
        for i, day in enumerate(week):
            if day != 0:
                d_obj = datetime(sel_year, sel_month, day).date()
                d_str = d_obj.strftime("%Y-%m-%d")
                has_ev = not df_s.empty and d_str in df_s.iloc[:, 0].astype(str).values
                is_hol = jpholiday.is_holiday(d_obj)
                
                label = str(day)
                if is_hol: label += "🎌"
                elif has_ev: label += "📍"
                
                if cols[i].button(label, key=f"d_{d_str}"):
                    st.session_state.selected_date = d_obj
            else:
                cols[i].empty() # 空白セル

    st.divider()
    sel = st.session_state.selected_date
    st.subheader(f"🔍 {sel.strftime('%m/%d')} の情報")
    hol_n = jpholiday.is_holiday_name(sel)
    if hol_n: st.error(f"🎌 {hol_n}")
    
    if not df_s.empty:
        # スプレッドシートの日付形式に合わせて比較
        day_evs = df_s[df_s.iloc[:, 0].astype(str).str.contains(sel.strftime("%Y-%m-%d"))]
        if not day_evs.empty:
            for v in day_evs.iloc[:, 1]: st.info(f"📍 予定: {v}")
        else: st.write("予定なし")

# --- 2. 予定・3. 課題・4. 時間割 ---
with tab_ev:
    st.subheader("予定の登録")
    st.write(f"選択日: **{st.session_state.selected_date}**")
    ev_text = st.text_input("予定を入力")
    if st.button("保存", key="save_ev"):
        if ev_text:
            requests.post(f"{gas_url}?sheet=schedules", json=[st.session_state.selected_date.strftime("%Y-%m-%d"), ev_text])
            st.success("保存完了！")
            st.rerun()

with tab_task:
    st.subheader("課題の登録")
    st.write(f"期限: **{st.session_state.selected_date}**")
    with st.form("task_f"):
        t_sub = st.selectbox("教科", SUBJECTS)
        t_msg = st.text_input("内容")
        if st.form_submit_button("課題保存"):
            if t_msg:
                requests.post(f"{gas_url}?sheet=tasks", json=[t_sub, t_msg, st.session_state.selected_date.strftime("%Y-%m-%d"), "FALSE"])
                st.success("完了")
                st.rerun()

with tab_time:
    st.subheader("週間時間割")
    timetable = {
        "月": ["科技β", "数基α", "家庭", "地総", "科技α", "言語文化", "論表"],
        "火": ["科技α", "音楽", "歴総", "体育", "数基α", "言語文化", "-"],
        "水": ["保健", "探求", "論表", "数基β", "現国", "コミュ I", "-"],
        "木": ["科技β", "コミュ I", "言語文化", "家庭", "音楽", "数基α", "LT"],
        "金": ["地総", "体育", "数基β", "現国", "SP I", "歴総", "-"]
    }
    st.table(pd.DataFrame(timetable, index=[f"{i+1}限" for i in range(7)]))

