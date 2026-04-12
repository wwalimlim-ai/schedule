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

# ログイン
pw = st.sidebar.text_input("パスワードを入力", type="password")
if pw != correct_pw:
    st.info("左のメニューからパスワードを入力してください。")
    st.stop()

# --- スプレッドシート接続 ---
# Secretsに設定したURLを使って接続
conn = st.connection("gsheets", type=GSheetsConnection)

# データの読み込み
def load_data(sheet_name):
    try:
        # ttl=0で毎回最新のデータを読み込む
        return conn.read(worksheet=sheet_name, ttl=0)
    except:
        return pd.DataFrame()

df_schedules = load_data("schedules")
df_tasks = load_data("tasks")

# 時間割データ
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
    
    if not df_schedules.empty:
        # 日付が一致するものを表示
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
                # 新しい行を作成
                new_row = pd.DataFrame([{"date": date_str, "event": new_event}])
                # 既存のデータと結合
                df_schedules = pd.concat([df_schedules, new_row], ignore_index=True)
                # スプレッドシートを更新
                conn.update(worksheet="schedules", data=df_schedules)
                st.success("保存しました！")
                st.rerun()

# --- タブ2: 時間割 ---
with tab2:
    st.subheader("週間時間割")
    day_opt = st.selectbox("曜日を選択", ["月", "火", "水", "木", "金"])
    for i, sub in enumerate(timetable.get(day_opt, [])):
        col1, col2 = st.columns([1, 4])
        col1.button(f"{i+1}", key=f"p_{day_opt}_{i}", disabled=True)
        col2.write(f"**{sub}**")

# --- タブ3: 課題 ---
with tab3:
    st.subheader("課題の管理")
    with st.expander("➕ 新しい課題を追加"):
        with st.form("add_task_form"):
            t_subject = st.selectbox("教科", ["科技β", "数基α", "英語", "現国", "地総", "その他"])
            t_name = st.text_input("課題内容")
            t_date = st.date_input("期限", datetime.now())
            if st.form_submit_button("登録"):
                if t_name:
                    new_task = pd.DataFrame([{
                        "subject": t_subject, "name": t_name, 
                        "date": t_date.strftime("%Y-%m-%d"), "completed": False
                    }])
                    df_tasks = pd.concat([df_tasks, new_task], ignore_index=True)
                    conn.update(worksheet="tasks", data=df_tasks)
                    st.rerun()

    if not df_tasks.empty:
        # 未完了の課題を表示
        inc_tasks = df_tasks[df_tasks["completed"] == False]
        for idx, task in inc_tasks.iterrows():
            col1, col2 = st.columns([4, 1])
            col1.write(f"**【{task['subject']}】** {task['name']} ({task['date']})")
            if col2.button("完了", key=f"done_{idx}"):
                # 削除（または完了フラグ更新）して更新
                df_tasks = df_tasks.drop(idx)
                conn.update(worksheet="tasks", data=df_tasks)
                st.rerun()
