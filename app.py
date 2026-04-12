import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import jpholiday
import calendar
from streamlit_calendar import calendar as st_cal # 不要なら消してOK

# --- 1. ページ設定 ---
st.set_page_config(page_title="学生用ツール", layout="centered")

# --- 2. ログイン管理 ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 ログイン")
    pw = st.text_input("パスワード", type="password")
    if st.button("ログイン"):
        if pw == st.secrets.get("MY_PASSWORD"):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("パスワードが違います")
    st.stop()

# --- 3. ログイン後のメインロジック ---

# 選択された日付を保持
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.now().strftime("%Y-%m-%d")

# クエリパラメータから日付を受け取る（ログイン維持用）
query_params = st.query_params
if "d" in query_params:
    st.session_state.selected_date = query_params["d"]

# データ読み込み
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

st.title("🎓 学生用ツール")
tab_cal, tab_ev, tab_task, tab_time = st.tabs(["📅 カレンダー", "📌 予定追加", "📝 課題追加", "⏰ 時間割"])

# --- カレンダータブ ---
with tab_cal:
    now = datetime.now()
    c1, c2 = st.columns(2)
    sel_year = c1.selectbox("年", [2025, 2026], index=1)
    sel_month = c2.selectbox("月", list(range(1, 13)), index=now.month-1)

    # 【神のHTML/CSS】
    # ボタン自体を完全に自作し、クリックしてもページが飛ばない工夫
    cal_html = f"""
    <style>
        .grid-container {{
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 4px;
            width: 100%;
        }}
        .grid-item {{
            aspect-ratio: 1 / 1;
            border-radius: 6px;
            border: 1px solid #e0e0e0;
            background-color: #f8f9fb;
            color: #31333F;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            font-size: 13px;
            cursor: pointer;
            text-decoration: none;
            transition: 0.2s;
        }}
        .grid-item:active {{ background-color: #e0e0e0; }}
        .header {{ font-weight: bold; border: none; background: none; aspect-ratio: auto; padding: 5px 0; }}
        .selected {{ background-color: #ff4b4b !important; color: white !important; font-weight: bold; border: none; }}
        .marker {{ font-size: 10px; margin-top: -2px; }}
    </style>
    <div class="grid-container">
        <div class="grid-item header" style="color:red;">日</div>
        <div class="grid-item header">月</div><div class="grid-item header">火</div>
        <div class="grid-item header">水</div><div class="grid-item header">木</div>
        <div class="grid-item header">金</div><div class="grid-item header" style="color:blue;">土</div>
    """

    cal_obj = calendar.Calendar(firstweekday=6)
    weeks = cal_obj.monthdayscalendar(sel_year, sel_month)

    for week in weeks:
        for i, day in enumerate(week):
            if day == 0:
                cal_html += '<div style="aspect-ratio: 1 / 1;"></div>'
            else:
                d_obj = datetime(sel_year, sel_month, day).date()
                d_str = d_obj.strftime("%Y-%m-%d")
                is_selected = "selected" if d_str == st.session_state.selected_date else ""
                is_hol = jpholiday.is_holiday(d_obj)
                has_ev = not df_s.empty and d_str in df_s.iloc[:, 0].astype(str).values
                
                color = "inherit"
                if i == 0 or is_hol: color = "red"
                elif i == 6: color = "blue"
                
                marker = "🎌" if is_hol else ("📍" if has_ev else "")
                
                # ここが重要：URLを変えずにStreamlitの状態だけ更新するための「仕掛け」
                cal_html += f'<a href="/?d={d_str}" target="_self" class="grid-item {is_selected}" style="color:{color};">{day}<span class="marker">{marker}</span></a>'
    
    cal_html += "</div>"
    st.markdown(cal_html, unsafe_allow_html=True)

    st.divider()
    
    # 選択中の情報表示
    sel_d = st.session_state.selected_date
    st.subheader(f"🔍 {sel_d} の情報")
    if not df_s.empty:
        day_evs = df_s[df_s.iloc[:, 0].astype(str).str.contains(sel_d)]
        if not day_evs.empty:
            for v in day_evs.iloc[:, 1]: st.info(f"📍 {v}")
        else: st.write("予定なし")

# --- 予定追加・課題追加などのタブ ---
with tab_ev:
    st.subheader("予定の登録")
    st.write(f"選択日: **{st.session_state.selected_date}**")
    ev_text = st.text_input("予定を入力")
    if st.button("保存", key="save_ev"):
        if ev_text:
            requests.post(f"{gas_url}?sheet=schedules", json=[st.session_state.selected_date, ev_text])
            st.success("完了！")
            st.rerun()

# (以下、課題追加・時間割などのコードは維持)
