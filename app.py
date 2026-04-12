import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import jpholiday
import calendar

# --- 1. ページ設定 ---
st.set_page_config(page_title="学生用ツール", layout="centered")

# 【スマホ特化型CSS】
# 枠線を先に用意し、その中に数字を配置する「グリッド・テーブル」方式
st.markdown("""
    <style>
    .main .block-container { padding: 1rem 0.2rem !important; }
    
    /* カレンダーの外枠 */
    .cal-table {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        width: 100%;
        border-top: 1px solid #ccc;
        border-left: 1px solid #ccc;
        background-color: white;
    }

    /* 共通セル（曜日・日付） */
    .cal-cell {
        border-right: 1px solid #ccc;
        border-bottom: 1px solid #ccc;
        text-align: center;
        text-decoration: none;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        color: #333;
    }

    /* 曜日ヘッダー */
    .header-cell {
        background-color: #f0f2f6;
        font-weight: bold;
        font-size: 11px;
        padding: 8px 0;
    }

    /* 日付セル */
    .date-cell {
        aspect-ratio: 1 / 1;
        cursor: pointer;
        position: relative;
    }
    .date-cell:active { background-color: #e0e0e0; }
    
    /* 選択中の日（赤丸ではなく背景色で視認性アップ） */
    .selected {
        background-color: #ff4b4b !important;
        color: white !important;
        font-weight: bold;
    }

    .day-num { font-size: 14px; }
    .mark { font-size: 9px; margin-top: -2px; }

    /* 土日の色 */
    .sun { color: #ff0000 !important; }
    .sat { color: #0000ff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ログイン管理（セッション維持） ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 ログイン")
    with st.form("login_form"):
        pw = st.text_input("パスワード", type="password")
        if st.form_submit_button("ログイン"):
            if pw == st.secrets.get("MY_PASSWORD"):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("パスワードが違います")
    st.stop()

# --- 3. データ読み込み & 日付管理 ---
# URLパラメータ(?d=...)から日付を取得する（ログイン維持の秘訣）
query_params = st.query_params
if "d" in query_params:
    st.session_state.selected_date = datetime.strptime(query_params["d"], "%Y-%m-%d").date()
elif 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.now().date()

gas_url = st.secrets.get("GAS_URL")
sheet_url = st.secrets.get("connections", {}).get("gsheets", {}).get("spreadsheet")

def load_data(sheet_name):
    if not sheet_url: return pd.DataFrame()
    try:
        base_url = sheet_url.split('/edit')[0]
        csv_url = f"{base_url}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        return pd.read_csv(csv_url)
    except: return pd.DataFrame()

df_s = load_data("schedules")
SUBJECTS = ["現国", "言語文化", "地総", "歴総", "数基α", "数基β", "科技α", "科技β", "コミュ I", "論表", "SP I", "保健", "体育", "音楽", "家庭", "探求基礎", "LT"]

# --- 4. メイン画面 ---
st.title("🎓 学生用ツール")
tabs = st.tabs(["📅 カレンダー", "📌 予定追加", "📝 課題追加", "⏰ 時間割"])

# カレンダータブ
with tabs[0]:
    c1, c2 = st.columns(2)
    y = c1.selectbox("年", [2025, 2026], index=1, key="sel_y")
    m = c2.selectbox("月", list(range(1, 13)), index=datetime.now().month-1, key="sel_m")

    # グリッド描画開始
    html = '<div class="cal-table">'
    
    # 曜日ヘッダー
    days_head = [("日","sun"), ("月",""), ("火",""), ("水",""), ("木",""), ("金",""), ("土","sat")]
    for d, cls in days_head:
        html += f'<div class="cal-cell header-cell {cls}">{d}</div>'

    # 日付流し込み
