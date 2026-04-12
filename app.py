import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import calendar

# --- ページ設定 ---
st.set_page_config(page_title="学生用ツール", layout="wide")

# Secrets
correct_pw = st.secrets.get("MY_PASSWORD")
gas_url = st.secrets.get("GAS_URL")
sheet_url = st.secrets.get("connections", {}).get("gsheets", {}).get("spreadsheet")

# サイドバー：ログイン & 年月選択
st.sidebar.title("🔐 Login / Settings")
pw = st.sidebar.text_input("パスワード", type="password")

if pw != correct_pw:
    st.info("パスワードを入力してください。")
    st.stop()

# カレンダー用の年月選択
now = datetime.now()
sel_year = st.sidebar.selectbox("年", range(now.year-1, now.year+2), index=1)
sel_month = st.sidebar.selectbox("月", range(1, 13), index=now.month-1)

# --- データ読み込み ---
def load_data(sheet_name):
    if not sheet_url: return pd.DataFrame()
    try:
        base_url = sheet_url.split('/edit')[0]
        csv_url = f"{base_url}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        return pd.read_csv(csv_url)
    except:
        return pd.DataFrame()

df_s = load_data("schedules")
df_t = load_data("tasks")

# --- メインコンテンツ ---
st.title("🎓 学生用ツール")

tab_cal, tab_ev, tab_time, tab_task = st.tabs(["📅 カレンダー", "📌 予定追加", "⏰ 時間割", "📝 課題追加"])

# --- 1. カレンダータブ ---
with tab_cal:
    st.subheader(f"{sel_year}年 {sel_month}月")
    cal = calendar.monthcalendar(sel_year, sel_month)
    cols = st.columns(7)
    days = ["月", "火", "水", "木", "金", "土", "日"]
    
    for i, day_name in enumerate(days):
        cols[i].write(f"**{day_name}**")
    
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write(" ")
            else:
                target_date = f"{sel_year}-{sel_month:02d}-{day:02d}"
                # 予定があるかチェック
                has_ev = not df_s.empty and target_date in df_s.iloc[:, 0].values
                if has_ev:
                    cols[i].info(f"{day}\n📍")
                else:
                    cols[i].write(f"{day}")

# --- 2. 予定タブ ---
with tab_ev:
    st.subheader("予定の追加")
    # キーボードを出さないために、selectboxやdate_inputを活用
    ev_date = st.date_input("予定日", datetime.now(), help="カレンダーから選択してください")
    ev_text = st.text_input("予定の内容", placeholder="例：〇〇の練習")
    
    if st.button("予定を保存"):
        if ev_text:
            requests.post(f"{gas_url}?sheet=schedules", json=[ev_date.strftime("%Y-%m-%d"), ev_text])
            st.success("予定を保存しました")
            st.rerun()

# --- 3. 時間割タブ ---
with tab_time:
    st.subheader("週間時間割")
    timetable = {
        "月": ["科技β", "数基α", "家庭", "地総", "科技α", "言語文化", "論表"],
        "火": ["科技α", "音楽", "歴総", "体育", "数基α", "言語文化", ""],
        "水": ["保健", "探求", "論表", "数基β", "現国", "コミュI", ""],
        "木": ["科技β", "コミュI", "言語文化", "家庭", "音楽", "数基α", "LT"],
        "金": ["地総", "体育", "数基β", "現国", "SP I", "歴総", ""]
    }
    # 表形式で表示
    df_tt = pd.DataFrame(timetable)
    df_tt.index = [f"{i+1}限" for i in range(len(df_tt))]
    st.table(df_tt)

# --- 4. 課題タブ ---
with tab_task:
    st.subheader("課題の登録")
    with st.form("task_form"):
        # 教科は選択のみ（入力不可）
        t_sub = st.selectbox("教科名", [
            "科技α", "科技β", "数基α", "数基β", "現国", 
            "言語文化", "論表", "コミュ I", "歴総", "地総", 
            "保健", "体育", "家庭", "音楽", "探求基礎", "その他"
        ])
        t_msg = st.text_input("課題内容", placeholder="例：問題集 P.10-15")
        t_due = st.date_input("期限日", datetime.now())
        
        if st.form_submit_button("課題を保存"):
            if t_msg:
                requests.post(f"{gas_url}?sheet=tasks", json=[t_sub, t_msg, t_due.strftime("%Y-%m-%d"), "FALSE"])
                st.success("課題を保存しました")
                st.rerun()
