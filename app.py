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

tab1, tab2 = st.tabs(["予定の追加", "時間割"])

# --- タブ1: 予定の追加 ---
with tab1:
    st.subheader("新しい予定をスプレッドシートに保存")
    
    selected_date = st.date_input("日付を選択", datetime.now())
    new_event = st.text_input("予定の内容を入力")

    if st.button("スプレッドシートに保存"):
        if not gas_url:
            st.error("SecretsにGAS_URLが設定されていません。")
        elif new_event:
            with st.spinner("保存中..."):
                # GASに送るデータ（日付と内容）
                data = [selected_date.strftime("%Y-%m-%d"), new_event]
                try:
                    # GASへ送信（?sheet=schedules でシート名を指定）
                    response = requests.post(f"{gas_url}?sheet=schedules", json=data)
                    
                    if response.status_code == 200:
                        st.success("スプレッドシートへ保存完了！")
                    else:
                        st.error(f"保存失敗（エラーコード: {response.status_code}）")
                except Exception as e:
                    st.error(f"通信エラーが発生しました: {e}")
        else:
            st.warning("予定の内容を入力してください。")

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
