import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- ページ設定 ---
st.set_page_config(page_title="カレンダーなど", layout="centered")

# Secretsから設定を取得
correct_pw = st.secrets.get("MY_PASSWORD")
gas_url = st.secrets.get("GAS_URL")

# ログイン画面
pw = st.sidebar.text_input("パスワードを入力", type="password")
if pw != correct_pw:
    st.info("左のメニューからパスワードを入力してください。")
    st.stop()

# --- ログイン成功後のメイン画面 ---
st.title("カレンダーなど")

tab1, tab2, tab3 = st.tabs(["予定の追加", "時間割", "課題の追加"])

# --- タブ1: 予定の追加 ---
with tab1:
    st.subheader("新しい予定を保存")
    selected_date = st.date_input("日付を選択", datetime.now(), key="date_ev")
    new_event = st.text_input("予定の内容を入力", key="input_ev")

    if st.button("予定を保存", key="btn_ev"):
        if new_event and gas_url:
            with st.spinner("保存中..."):
                data = [selected_date.strftime("%Y-%m-%d"), new_event]
                res = requests.post(f"{gas_url}?sheet=schedules", json=data)
                if res.status_code == 200:
                    st.success("予定を保存しました！")
                else:
                    st.error("エラーが発生しました。")
        else:
            st.warning("内容を入力してください。")

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
    day_opt = st.selectbox("曜日を選択", ["月", "火", "水", "木", "金"])
    for i, sub in enumerate(timetable.get(day_opt, [])):
        col1, col2 = st.columns([1, 4])
        col1.button(f"{i+1}", key=f"p_{day_opt}_{i}", disabled=True)
        col2.write(f"**{sub}**")

# --- タブ3: 課題の追加 ---
with tab3:
    st.subheader("新しい課題を保存")
    with st.form("task_form"):
        t_subject = st.selectbox("教科", ["科技β", "数基α", "英語", "現国", "地総", "その他"])
        t_name = st.text_input("課題の内容（例：ワークP.20まで）")
        t_date = st.date_input("期限", datetime.now())
        submit_task = st.form_submit_button("課題を登録")

        if submit_task and t_name and gas_url:
            with st.spinner("保存中..."):
                # スプレッドシートの tasks シートに送るデータ
                # [教科, 内容, 期限, 完了フラグ(False)]
                task_data = [t_subject, t_name, t_date.strftime("%Y-%m-%d"), "FALSE"]
                res = requests.post(f"{gas_url}?sheet=tasks", json=task_data)
                if res.status_code == 200:
                    st.success(f"【{t_subject}】の課題を保存しました！")
                else:
                    st.error("保存に失敗しました。")
