import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- ページ設定 ---
st.set_page_config(page_title="カレンダーなど", layout="centered")

# パスワード設定
if "MY_PASSWORD" in st.secrets:
    correct_pw = st.secrets["MY_PASSWORD"]
else:
    st.error("管理画面でパスワードを設定してください")
    st.stop()

# ログイン画面
pw = st.sidebar.text_input("パスワードを入力", type="password")
if pw != correct_pw:
    st.info("左のメニューからパスワードを入力してください。")
    st.stop()

# --- Googleスプレッドシート接続 ---
conn = st.connection("gsheets", type=GSheetsConnection)

# データ読み込み用関数
def load_data(sheet_name):
    try:
        return conn.read(worksheet=sheet_name, ttl="0s")
    except:
        return pd.DataFrame()

# 予定と課題の読み込み
df_schedules = load_data("schedules")
df_tasks = load_data("tasks")

# 時間割（固定データ）
timetable = {
    "月": ["科技β", "数基α", "家庭", "地総", "科技α", "言語文化", "論表"],
    "火": ["科技α", "音楽", "歴総", "体育", "数基α", "言語文化"],
    "水": ["保健", "探求基礎", "論表", "数基β", "現国", "コミュ I"],
    "木": ["科技β", "コミュ I", "言語文化", "家庭", "音楽", "数基α", "LT"],
    "金": ["地総", "体育", "数基β", "現国", "SP I", "歴総"],
}

st.title("カレンダーなど")
tab1, tab2, tab3 = st.tabs(["予定", "時間割", "課題"])

# --- タブ1: 予定 ---
with tab1:
    st.subheader("予定の確認・追加")
    selected_date = st.date_input("日付を選択", datetime.now())
    date_str = selected_date.strftime("%Y-%m-%d")
    
    # 予定の表示
    if not df_schedules.empty:
        day_events = df_schedules[df_schedules["date"] == date_str]
        if not day_events.empty:
            for idx, row in day_events.iterrows():
                col1, col2 = st.columns([4, 1])
                col1.info(f"📌 {row['event']}")
                if col2.button("🗑️", key=f"del_ev_{idx}"):
                    df_schedules = df_schedules.drop(idx)
                    conn.update(worksheet="schedules", data=df_schedules)
                    st.rerun()
        else:
            st.write("予定はありません")
    
    with st.expander("＋ 新しい予定を追加"):
        new_event = st.text_input("予定名")
        if st.button("予定を保存"):
            if new_event:
                new_row = pd.DataFrame([{"date": date_str, "event": new_event}])
                df_schedules = pd.concat([df_schedules, new_row], ignore_index=True)
                conn.update(worksheet="schedules", data=df_schedules)
                st.success("保存しました！")
                st.rerun()

# --- タブ2: 時間割 ---
with tab2:
    st.subheader("週間時間割")
    day_opt = st.selectbox("曜日を選択", ["月", "火", "水", "木", "金"])
    day_subjects = timetable.get(day_opt, [])
    for i, sub in enumerate(day_subjects):
        col1, col2 = st.columns([1, 4])
        col1.button(f"{i+1}", key=f"p_{day_opt}_{i}", disabled=True)
        col2.write(f"**{sub}**")

# --- タブ3: 課題 ---
with tab3:
    st.subheader("課題の管理")
    with st.expander("➕ 新しい課題を追加"):
        with st.form("add_task_form"):
            t_subject = st.selectbox("教科", ["科技β", "数基α", "英語", "現国", "地総", "その他"])
            t_name = st.text_input("課題の内容")
            t_date = st.date_input("期限", datetime.now())
            submit_task = st.form_submit_button("課題を登録")
            
            if submit_task and t_name:
                new_task = pd.DataFrame([{
                    "subject": t_subject, "name": t_name, 
                    "date": t_date.strftime("%Y-%m-%d"), "completed": False
                }])
                df_tasks = pd.concat([df_tasks, new_task], ignore_index=True)
                conn.update(worksheet="tasks", data=df_tasks)
                st.success("追加しました！")
                st.rerun()

    st.write("未完了の課題一覧")
    if not df_tasks.empty:
        # 未完了のみ表示
        incomplete_tasks = df_tasks[df_tasks["completed"] == False].sort_values("date")
        for idx, task in incomplete_tasks.iterrows():
            col1, col2 = st.columns([4, 1])
            col1.write(f"**【{task['subject']}】**\n{task['name']} (期限: {task['date']})")
            if col2.button("完了", key=f"done_{idx}"):
                df_tasks = df_tasks.drop(idx) # 今回はシンプルに削除
                conn.update(worksheet="tasks", data=df_tasks)
                st.rerun()
    else:
        st.info("課題はありません。")
