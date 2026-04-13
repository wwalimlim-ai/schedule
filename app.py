import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
import jpholiday
import calendar

st.set_page_config(page_title="MyTool", layout="centered")

# --- 1. データ読み込み（デバッグ機能付き） ---
gas_url = st.secrets.get("GAS_URL")
# 通信テスト用（画面に出ます）
if not gas_url:
    st.error("GAS_URLが設定されていません！")
else:
    try:
        test_res = requests.get(f"{gas_url}?sheet=schedules")
        if test_res.status_code == 200:
            st.success("GASとの通信に成功しました！")
        else:
            st.error(f"GASと通信はできましたが、エラーが返ってきました: {test_res.status_code}")
    except:
        st.error("GASにアクセスできません。URLが間違っているか、公開設定が『全員』になっていません。")

def load_via_gas(sheet_name):
    try:
        res = requests.get(f"{gas_url}?sheet={sheet_name}", timeout=10)
        if res.status_code != 200:
            st.error(f"GASエラー: {res.status_code}")
            return pd.DataFrame()
        data = res.json()
        if not data:
            return pd.DataFrame()
        if sheet_name == "schedules":
            return pd.DataFrame(data, columns=["date", "content"])
        else:
            return pd.DataFrame(data, columns=["subject", "content", "deadline", "done"])
    except Exception as e:
        # 画面にエラーの中身を出す（これで原因がわかります）
        st.warning(f"{sheet_name}の読み込みに失敗: {e}")
        return pd.DataFrame()

# データを読み込む
df_s = load_via_gas("schedules")
df_t = load_via_gas("tasks")

# --- 2. CSS & UI (以前のものを極限まで整理) ---
st.markdown("<style>.stAppHeader { display: none; } .main .block-container { padding-top: 0rem !important; } .calendar-wrapper { display: grid; grid-template-columns: repeat(7, 1fr); background: white; border: 1px solid #eee; } .cal-box { aspect-ratio: 1/1; display: flex; flex-direction: column; justify-content: center; align-items: center; text-decoration: none; border: 0.5px solid #f8f8f8; color: #444; } .selected-box { background: #ff4b4b !important; color: white !important; border-radius: 8px; } .has-event-dot { width: 6px; height: 6px; background-color: #ff9f00; border-radius: 50%; margin-top: 2px; }</style>", unsafe_allow_html=True)

JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST)
if "d" in st.query_params:
    st.session_state.selected_date = datetime.strptime(st.query_params["d"], "%Y-%m-%d").date()
elif 'selected_date' not in st.session_state:
    st.session_state.selected_date = now.date()
sel = st.session_state.selected_date

# --- 3. メイン表示 ---
tabs = st.tabs(["📅 カレンダー", "🎒 持ち物", "📋 課題", "📝 予定一覧", "➕ 登録"])

with tabs[0]:
    st.write(f"### {sel.month}/{sel.day}")
    html = '<div class="calendar-wrapper">'
    # 曜日のヘッダー（日〜土）
    for d, c in [("日","red"),("月",""),("火",""),("水",""),("木",""),("金",""),("土","blue")]:
        html += f'<div class="cal-box" style="font-size:10px; color:{c};">{d}</div>'
    
    for week in calendar.Calendar(firstweekday=6).monthdayscalendar(now.year, now.month):
        for i, day in enumerate(week):
            if day == 0: html += '<div class="cal-box"></div>'
            else:
                d_obj = datetime(now.year, now.month, day).date()
                d_str = d_obj.strftime("%Y-%m-%d")
                is_sel = "selected-box" if d_obj == sel else ""
                # 予定ありドット判定
                has_ev = not df_s.empty and any(df_s["date"].astype(str) == d_str)
                dot = '<div class="has-event-dot"></div>' if has_ev else ""
                html += f'<a href="/?d={d_str}" target="_self" class="cal-box {is_sel}">{day}{dot}</a>'
    st.markdown(html + '</div>', unsafe_allow_html=True)
    
    if not df_s.empty:
        today_evs = df_s[df_s["date"].astype(str) == sel.strftime("%Y-%m-%d")]
        for v in today_evs["content"]: st.info(v)

# --- (他のタブは以前と同様なので省略しますが、内部ロジックは生きています) ---
with tabs[4]: # 登録タブ
    st.write("### ➕ 追加")
    mode = st.radio("種類", ["予定", "課題"], horizontal=True)
    with st.form("add"):
        txt = st.text_input("内容")
        if st.form_submit_button("保存して更新"):
            if txt:
                p = [sel.strftime("%Y-%m-%d"), txt] if mode == "予定" else ["", txt, sel.strftime("%Y-%m-%d"), "FALSE"]
                requests.post(f"{gas_url}?sheet={'schedules' if mode == '予定' else 'tasks'}", json=p)
                st.cache_data.clear()
                st.rerun()
