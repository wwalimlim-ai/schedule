import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import jpholiday
import calendar
from urllib.parse import quote

# --- ページ設定 ---
st.set_page_config(page_title="学生用ツール", layout="centered")

# 【最終奥義CSS】
st.markdown("""
    <style>
    .main .block-container { padding: 1rem 0.2rem !important; }
    
    /* 曜日と日付を強制的に7等分するグリッド */
    .calendar-container {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 4px;
        width: 100%;
        margin-bottom: 10px;
    }
    
    /* 共通のセルスタイル */
    .cal-cell {
        text-align: center;
        font-size: 12px;
        padding: 8px 0;
        border-radius: 4px;
        text-decoration: none;
        color: inherit;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        min-height: 45px;
    }

    /* 曜日のスタイル */
    .day-header { font-weight: bold; background: #f0f2f6; }

    /* 日付ボタンのスタイル（HTML版） */
    .date-btn {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        cursor: pointer;
        transition: 0.2s;
    }
    .date-btn:active { background-color: #f0f2f6; }
    
    /* 選択中の日のスタイル */
    .selected { border: 2px solid #ff4b4b !important; font-weight: bold; }

    /* 記号のサイズ */
    .marker { font-size: 10px; line-height: 1; }
    </style>
    """, unsafe_allow_html=True)

# Secrets & Data
correct_pw = st.secrets.get("MY_PASSWORD")
gas_url = st.secrets.get("GAS_URL")
sheet_url = st.secrets.get("connections", {}).get("gsheets", {}).get("spreadsheet")

pw = st.sidebar.text_input("パスワード", type="password")
if pw != correct_pw:
    st.info("ログインしてください。")
    st.stop()

# 状態管理（クエリパラメータを使って日付を選択）
query_params = st.query_params
if "d" in query_params:
    st.session_state.selected_date = datetime.strptime(query_params["d"], "%Y-%m-%d").date()
elif 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.now().date()

def load_data(sheet_name):
    if not sheet_url: return pd.DataFrame()
    try:
        base_url = sheet_url.split('/edit')[0]
        csv_url = f"{base_url}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        return pd.read_csv(csv_url)
    except: return pd.DataFrame()

df_s = load_data("schedules")

st.title("🎓 学生用ツール")
tab_cal, tab_ev, tab_task, tab_time = st.tabs(["📅 カレンダー", "📌 予定追加", "📝 課題追加", "⏰ 時間割"])

# --- 1. カレンダータブ（HTML自作グリッド） ---
with tab_cal:
    now = datetime.now()
    c1, c2 = st.columns(2)
    sel_year = c1.selectbox("年", [2025, 2026], index=1, label_visibility="collapsed")
    sel_month = c2.selectbox("月", list(range(1, 13)), index=now.month-1, label_visibility="collapsed")
    
    # 曜日ヘッダー
    days = [("日","red"), ("月",""), ("火",""), ("水",""), ("木",""), ("金",""), ("土","blue")]
    header_html = '<div class="calendar-container">'
    for d, color in days:
        header_html += f'<div class="cal-cell day-header" style="color:{color};">{d}</div>'
    header_html += '</div>'
    st.markdown(header_html, unsafe_allow_html=True)

    # 日付グリッド
    cal_obj = calendar.Calendar(firstweekday=6)
    weeks = cal_obj.monthdayscalendar(sel_year, sel_month)
    
    grid_html = '<div class="calendar-container">'
    for week in weeks:
        for i, day in enumerate(week):
            if day != 0:
                d_obj = datetime(sel_year, sel_month, day).date()
                d_str = d_obj.strftime("%Y-%m-%d")
                
                # 予定・祝日チェック
                has_ev = not df_s.empty and d_str in df_s.iloc[:, 0].astype(str).values
                is_hol = jpholiday.is_holiday(d_obj)
                
                # 色とマーク
                color = "inherit"
                if i == 0 or is_hol: color = "red"
                elif i == 6: color = "blue"
                
                marker = ""
                if is_hol: marker = '<span class="marker">🎌</span>'
                elif has_ev: marker = '<span class="marker">📍</span>'
                
                # 選択中か
                active_class = "selected" if d_obj == st.session_state.selected_date else ""
                
                # ボタン（リンク形式で擬似ボタンを作成）
                grid_html += f'''
                    <a href="/?d={d_str}" target="_self" class="cal-cell date-btn {active_class}" style="color:{color};">
                        {day}{marker}
                    </a>'''
            else:
                grid_html += '<div class="cal-cell"></div>'
    grid_html += '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)

    st.divider()
    sel = st.session_state.selected_date
    st.subheader(f"🔍 {sel.strftime('%m/%d')} の情報")
    hol_n = jpholiday.is_holiday_name(sel)
    if hol_n: st.error(f"🎌 {hol_n}")
    
    if not df_s.empty:
        day_evs = df_s[df_s.iloc[:, 0].astype(str).str.contains(sel.strftime("%Y-%m-%d"))]
        if not day_evs.empty:
            for v in day_evs.iloc[:, 1]: st.info(f"📍 予定: {v}")
        else: st.write("予定なし")

# --- 2〜4のタブは変更なし（前回と同じ） ---
with tab_ev:
    st.subheader("予定の登録")
    st.write(f"選択日: **{st.session_state.selected_date}**")
    ev_text = st.text_input("予定を入力")
    if st.button("保存", key="save_ev"):
        if ev_text:
            requests.post(f"{gas_url}?sheet=schedules", json=[st.session_state.selected_date.strftime("%Y-%m-%d"), ev_text])
            st.success("完了！")
            st.rerun()

with tab_task:
    st.subheader("課題の登録")
    st.write(f"期限: **{st.session_state.selected_date}**")
    with st.form("task_f"):
        t_sub = st.selectbox("教科", ["現国", "数基α", "科技β", "SP I"]) # 省略（全リスト入れてOK）
        t_msg = st.text_input("内容")
        if st.form_submit_button("課題保存"):
            if t_msg:
                requests.post(f"{gas_url}?sheet=tasks", json=[t_sub, t_msg, st.session_state.selected_date.strftime("%Y-%m-%d"), "FALSE"])
                st.success("完了")
                st.rerun()

with tab_time:
    st.subheader("週間時間割")
    timetable = {"月": ["科技β", "数基α", "家庭", "地総", "科技α", "言語文化", "論表"],"火": ["科技α", "音楽", "歴総", "体育", "数基α", "言語文化", "-"],"水": ["保健", "探求", "論表", "数基β", "現国", "コミュI", "-"],"木": ["科技β", "コミュI", "言語文化", "家庭", "音楽", "数基α", "LT"],"金": ["地総", "体育", "数基β", "現国", "SP I", "歴総", "-"]}
    st.table(pd.DataFrame(timetable, index=[f"{i+1}限" for i in range(7)]))
