import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import jpholiday
import calendar

# --- ページ設定 ---
st.set_page_config(page_title="学生用ツール", layout="centered")

# 【究極CSS】Streamlitの標準カラムを使わず、自作グリッドで横並びを強制
st.markdown("""
    <style>
    .main .block-container { padding: 1rem 0.2rem !important; }
    
    /* 物理的に7等分するグリッド */
    .ultra-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 4px;
        width: 100%;
        margin-bottom: 10px;
    }
    
    .grid-item {
        width: 100%;
    }

    /* 曜日のスタイル */
    .day-head {
        text-align: center;
        font-weight: bold;
        font-size: 12px;
        padding-bottom: 5px;
    }

    /* Streamlitのボタンを無理やりこの中に収めるためのCSS */
    div[data-testid="column"] {
        flex: 1 1 0% !important;
        min-width: 0 !important;
    }
    
    /* ボタンの中身のテキストが溢れないように調整 */
    .stButton > button {
        width: 100% !important;
        padding: 0 !important;
        font-size: 11px !important;
        height: 45px !important;
        min-width: 0 !important;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }

    /* 時間割表 */
    .stTable td { white-space: nowrap !important; font-size: 11px !important; }
    </style>
    """, unsafe_allow_html=True)

# Secrets & Data
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

# --- 1. カレンダータブ ---
with tab_cal:
    now = datetime.now()
    c1, c2 = st.columns(2)
    sel_year = c1.selectbox("年", [2025, 2026], index=1, label_visibility="collapsed")
    sel_month = c2.selectbox("月", list(range(1, 13)), index=now.month-1, label_visibility="collapsed")
    
    # 曜日ヘッダーをHTMLのグリッドで表示（これは確実に並ぶ）
    st.markdown(f"""
        <div class="ultra-grid">
            <div class="day-head" style="color:red;">日</div>
            <div class="day-head">月</div><div class="day-head">火</div><div class="day-head">水</div>
            <div class="day-head">木</div><div class="day-head">金</div>
            <div class="day-head" style="color:blue;">土</div>
        </div>
    """, unsafe_allow_html=True)

    # 日曜始まりのカレンダー
    cal_obj = calendar.Calendar(firstweekday=6)
    weeks = cal_obj.monthdayscalendar(sel_year, sel_month)

    # 日付ボタンエリア
    for week in weeks:
        # st.columns ではなく、あえて「ボタン専用のコンテナ」を1行ずつ作る
        # 1行を強制的に横並びにするためにHTMLタグの力を借りる
        st.write('<div class="ultra-grid">', unsafe_allow_html=True)
        cols = st.columns(7) 
        for i, day in enumerate(week):
            if day != 0:
                d_obj = datetime(sel_year, sel_month, day).date()
                d_str = d_obj.strftime("%Y-%m-%d")
                has_ev = not df_s.empty and d_str in df_s.iloc[:, 0].astype(str).values
                is_hol = jpholiday.is_holiday(d_obj)
                
                label = f"{day}"
                if is_hol: label += "\n🎌"
                elif has_ev: label += "\n📍"
                
                if cols[i].button(label, key=f"d_{d_str}"):
                    st.session_state.selected_date = d_obj
            else:
                cols[i].write("")
        st.write('</div>', unsafe_allow_html=True)

    st.divider()
    sel = st.session_state.selected_date
    st.subheader(f"🔍 {sel.strftime('%m/%d')} の情報")
    hol_n = jpholiday.is_holiday_name(sel)
    if hol_n: st.error(f"🎌 {hol_n}")
    
    if not df_s.empty:
        day_evs = df_s[df_s.iloc[:, 0].astype(str).str.contains(sel.strftime("%Y-%m-%d"))]
        if not day_evs.empty:
            for v in day_evs.iloc[:, 1]: st.info(f"📍 予定: {v}")
        else: st.write("予定なし")

# --- 2〜4のタブは前回のものを維持 ---
with tab_ev:
    st.subheader("予定の登録")
    st.write(f"選択日: **{st.session_state.selected_date}**")
    ev_text = st.text_input("予定を入力")
    if st.button("保存", key="save_ev"):
        if ev_text:
            requests.post(f"{gas_url}?sheet=schedules", json=[st.session_state.selected_date.strftime("%Y-%m-%d"), ev_text])
            st.success("完了！")
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
