import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- ページ設定 ---
st.set_page_config(page_title="学生用ツール", layout="centered")

# Secrets
correct_pw = st.secrets.get("MY_PASSWORD")
gas_url = st.secrets.get("GAS_URL")
sheet_url = st.secrets.get("connections", {}).get("gsheets", {}).get("spreadsheet")

# サイドバー：ログイン
st.sidebar.title("🔐 Login")
pw = st.sidebar.text_input("パスワード", type="password")

if pw != correct_pw:
    st.info("パスワードを入力して開始してください。")
    st.stop()

# --- データ読み込み ---
def load_data(sheet_name):
    if not sheet_url: return pd.DataFrame()
    try:
        base_url = sheet_url.split('/edit')[0]
        csv_url = f"{base_url}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        return pd.read_csv(csv_url)
    except:
        return pd.DataFrame()

# --- メインコンテンツ ---
st.title("🎓 学生用ツール")

tabs = st.tabs(["📅 予定", "📝 課題", "⏰ 時間割"])

# --- タブ1：予定 (Schedules) ---
with tabs[0]:
    st.subheader("今後の予定一覧")
    df_s = load_data("schedules")
    if not df_s.empty:
        # 日付でソート
        df_s.columns = ["date", "event"]
        df_s = df_s.sort_values("date")
        for _, row in df_s.iterrows():
            st.info(f"**{row['date']}** ： {row['event']}")
    
    with st.expander("➕ 予定を追加する"):
        new_date = st.date_input("日付", datetime.now())
        new_event = st.text_input("予定の内容")
        if st.button("予定を保存"):
            requests.post(f"{gas_url}?sheet=schedules", json=[new_date.strftime("%Y-%m-%d"), new_event])
            st.rerun()

# --- タブ2：課題 (Tasks) ---
with tabs[1]:
    st.subheader("未完了の課題")
    df_t = load_data("tasks")
    if not df_t.empty:
        df_t.columns = ["subject", "task", "deadline", "completed"]
        # FALSE（未完了）のものだけ表示
        incomplete = df_t[df_t["completed"].astype(str).str.upper() == "FALSE"]
        if not incomplete.empty:
            for _, row in incomplete.iterrows():
                # 教科ごとに色を変える等の演出はできませんが、見やすく表示
                st.warning(f"📒 **{row['subject']}**\n内容：{row['task']}\n期限：{row['deadline']}")
        else:
            st.success("全ての課題が完了しています！ 🎉")

    with st.expander("➕ 課題を追加する"):
        with st.form("add_task"):
            subj = st.selectbox("教科", ["科技α", "科技β", "数基α", "数基β", "現国", "言語文化", "論表", "コミュ I", "歴総", "地総", "保健", "体育", "家庭", "音楽", "探求基礎", "その他"])
            task_msg = st.text_input("課題の内容")
            limit_date = st.date_input("期限", datetime.now())
            if st.form_submit_button("課題を保存"):
                requests.post(f"{gas_url}?sheet=tasks", json=[subj, task_msg, limit_date.strftime("%Y-%m-%d"), "FALSE"])
                st.rerun()

# --- タブ3：時間割 (Timetable) ---
with tabs[2]:
    st.subheader("週間時間割")
    timetable = {
        "月": ["科技β", "数基α", "家庭", "地総", "科技α", "言語文化", "論表"],
        "火": ["科技α", "音楽", "歴総", "体育", "数基α", "言語文化"],
        "水": ["保健", "探求基礎", "論表", "数基β", "現国", "コミュ I"],
        "木": ["科技β", "コミュ I", "言語文化", "家庭", "音楽", "数基α", "LT"],
        "金": ["地総", "体育", "数基β", "現国", "SP I", "歴総"]
    }
    day = st.selectbox("曜日を選択", list(timetable.keys()))
    
    # PC版のように表形式で見やすく
    df_time = pd.DataFrame({"限目": range(1, len(timetable[day])+1), "教科": timetable[day]})
    st.table(df_time.set_index("限目"))
