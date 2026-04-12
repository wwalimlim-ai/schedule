import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import jpholiday
import calendar

# --- ページ設定 ---
st.set_page_config(page_title="学生用ツール", layout="centered")

# 【神レイアウトCSS】曜日も日付も強制的に7列固定
st.markdown("""
    <style>
    /* メインエリアの余白を最小化 */
    .main .block-container { padding: 1rem 0.5rem !important; }
    
    /* 7列グリッドの共通設定 */
    .grid-container {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 4px;
        text-align: center;
        align-items: center;
    }
    
    /* 曜日のスタイル */
    .cal-header {
        font-weight: bold;
        font-size: 13px;
        padding-bottom: 8px;
    }
    
    /* 時間割の表をスマホ最適化 */
    .stTable td {
        white-space: nowrap !important;
        font-size: 11px !important;
        padding: 4px !important;
    }

    /* ボタンの余白とサイズを強制固定 */
    div[data-testid="column"] {
        width: calc(14.28% - 4px) !important;
        flex: none !important;
        min-width: 0 !important;
    }
    .stButton > button {
        width: 100% !important;
        font-size: 12px !important;
        padding: 0 !important;
        height: 45px !important;
        line-height: 1.2 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Secrets & Data
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

# --- 1. カレンダータブ（日曜始まり & 7列固定） ---
with tab_cal:
    now = datetime.now()
    c1, c2 = st.columns(2)
    sel_year = c1.selectbox("年", [now.year, now.year+1], index=0, label_visibility="collapsed")
    sel_month = c2.selectbox("月", list(range(1, 13)), index=now.month-1, label_visibility="collapsed")
    
    # 曜日ヘッダーを日曜始まりで表示
    st.markdown(f"""
        <div class="grid-container">
            <div class="cal-header" style="color:red;">日</div>
            <div class="cal-header">月</div><div class="cal-header">火</div><div class="cal-header">水</div>
            <div class="cal-header">木</div><div class="cal-header">金</div>
            <div class="cal-header" style="color:blue;">土</div>
        </div>
    """, unsafe_allow_html=True)

    # 日曜始まりのカレンダーを生成
    # setfirstweekday(6) で日曜(6)を週の始まりに設定
    cal_obj = calendar.Calendar(firstweekday=6)
    weeks = cal_obj.monthdayscalendar(sel_year, sel_month)

    for week in weeks:
        cols = st.columns(7) # CSSで強制的に横一列に固定済み
        for i, day in enumerate(week):
            if day != 0:
                d_obj = datetime(sel_year, sel_month, day).date()
                d_str = d_obj.strftime("%Y-%m-%d")
                has_ev = not df_s.empty and d_str in df_s.iloc[:, 0].astype(str).values
                is_hol = jpholiday.is_holiday(d_obj)
                
                # ラベル作成
                label = str(day)
                if is_hol: label += "🎌"
                elif has_ev: label += "📍"
                
                if cols[i].button(label, key=f"d_{d_str}"):
                    st.session_state.selected_date = d_obj
            else:
                cols[i].write("")

    st.divider()
    sel = st.session_state.selected_date
    st.subheader(f"🔍 {sel.strftime('%m/%d')} の情報")
    hol_n = jpholiday.is_holiday_name(sel)
    if hol_n: st.error(f"🎌 {hol_n}")
    
    if not df_s.empty:
        day_evs = df_s[df_s.iloc[:, 0].astype(str) == sel.strftime("%Y-%m-%d")]
        if not day_evs.empty:
            for v in day_evs.iloc[:, 1]: st.info(f"📍 予定: {v}")
        else: st.write("予定なし")

# --- 2. 予定・3. 課題・4. 時間割はそのまま維持 ---
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
                st.success("保存完了")
                st.rerun()

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
