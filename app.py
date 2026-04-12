import streamlit as st
import pandas as pd
from datetime import datetime

# --- ページ設定 ---
st.set_page_config(page_title="カレンダーなど", layout="centered")

# パスワード設定 (Secretsから取得)
correct_pw = st.secrets.get("MY_PASSWORD", "default_password")
sheet_url = st.secrets.get("connections", {}).get("gsheets", {}).get("spreadsheet")

# ログインチェック
pw = st.sidebar.text_input("パスワードを入力", type="password")
if pw != correct_pw:
    st.info("パスワードを入力してください。")
    st.stop()

# --- スプレッドシート読み書き関数 ---
# URLをCSVエクスポート用に変換する魔法の関数
def get_csv_url(url, sheet_name):
    base_url = url.split('/edit')[0]
    return f"{base_url}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

def load_data(sheet_name):
    try:
        csv_url = get_csv_url(sheet_url, sheet_name)
        return pd.read_csv(csv_url)
    except:
        # 失敗した場合は空のデータフレームを作る
        if sheet_name == "schedules":
            return pd.DataFrame(columns=["date", "event"])
        else:
            return pd.DataFrame(columns=["subject", "name", "date", "completed"])

# 保存は「Google Apps Script」を使わない場合、今のライブラリでは制限がかかるため
# 一旦、画面表示と読み込みを優先させます。
