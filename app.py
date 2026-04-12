import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- ページ設定 ---
st.set_page_config(page_title="最強カレンダー", layout="centered")

# Secretsから設定を取得
correct_pw = st.secrets.get("MY_PASSWORD")
gas_url = st.secrets.get("GAS_URL")
# 読み込み用にスプレッドシートのURLが必要（Secretsの connections.gsheets.spreadsheet）
sheet_url = st.secrets.get("connections", {}).get("gsheets", {}).get("spreadsheet")

# ログイン画面
pw = st.sidebar.text_input("パスワードを入力", type="password")
if pw != correct_pw:
    st.info("パスワードを入力してください。")
    st.stop()

# --- データ読み込み関数 ---
def load_data(sheet_name):
    if not sheet_url:
        return pd.DataFrame()
    try:
        # スプレッドシートをCSV形式で読み込む（これならログイン不要で読み込めます）
        base_url = sheet_url.split('/edit')[0]
        csv_url = f"{base_url}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        df = pd.read_csv(csv_url)
        return df
    except:
        return pd.DataFrame()

# アプリ起動時にデータを読み込む
df_schedules = load_data("schedules")
df_tasks = load_data("tasks")

# --- メイン画面 ---
st.title("共有カレンダー＆課題")

tab1, tab2, tab3 = st.tabs(["📅 予定一覧", "⏰ 時間割", "📝 課題管理"])

# --- タブ1: 予定一覧 ---
with tab1:
    st.subheader("保存されている予定")
    
    if not df_schedules.empty:
        # 日付順に並び替え
        df_schedules = df_schedules.sort_values(by=df_schedules.columns[0])
        for _, row in df_schedules.iterrows():
            # 日付と内容を表示
            st.info(f"**{row.iloc[0]}** : {row.iloc[1]}")
    else:
        st.write("予定はまだ登録されていません。")
    
    with st.expander("➕ 新しい予定を追加"):
        input_date = st.date_input("日付", datetime.now())
        input_ev = st.text_input("予定内容")
        if st.button("予定を保存"):
            if input_ev and gas_url:
                requests.post(f"{gas_url}?sheet=schedules", json=[input_date.strftime("%Y-%m-%d"), input_ev])
                st.success("保存しました！更新ボタン（またはF5）を押してください")
                st.rerun()

# --- タブ2: 時間割 ---
with tab2:
    st.subheader("週間時間割")
    timetable = {
        "月": ["科技β", "数基α", "家庭", "地総", "科技α", "言語文化", "論表"],
        "火": ["科技α", "音楽", "歴総", "体育", "数基α", "言語文化"],
        "水": ["保健", "探求基礎", "論表", "数基β", "現国", "コミュ I"],
        "木": ["科技β", "コミュ I", "言語文化", "家庭", "音楽", "数基α", "LT"],
        "金": ["地総", "体育", "数基β", "現国", "SP I", "歴総"],
    }
    day = st.selectbox("曜日を選択", ["月", "火", "水", "木", "金"])
    for i, sub in enumerate(timetable[day]):
        col1, col2 = st.columns([1, 5])
        col1.markdown(f"**{i+1}**")
        col2.write(sub)

# --- タブ3: 課題管理 ---
with tab3:
    st.subheader("未完了の課題リスト")
    if not df_tasks.empty:
        # 完了フラグが FALSE のものだけ表示
        incomplete = df_tasks[df_tasks.iloc[:, 3].astype(str).str.upper() == "FALSE"]
        if not incomplete.empty:
            for _, row in incomplete.iterrows():
                st.warning(f"**【{row.iloc[0]}】** {row.iloc[1]}  \n📅 期限: {row.iloc[2]}")
        else:
            st.success("現在、未完了の課題はありません！")
    
    with st.expander("➕ 新しい課題を追加"):
        with st.form("task_form"):
            t_sub = st.selectbox("教科", ["科技β", "数基α", "英語", "現国", "地総", "その他"])
            t_msg = st.text_input("内容")
            t_due = st.date_input("期限", datetime.now())
            if st.form_submit_button("課題を保存"):
                if t_msg and gas_url:
                    requests.post(f"{gas_url}?sheet=tasks", json=[t_sub, t_msg, t_due.strftime("%Y-%m-%d"), "FALSE"])
                    st.rerun()
