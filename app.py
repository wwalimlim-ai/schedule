import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import jpholiday
import calendar

# --- 1. ページ設定（一番最初に書く） ---
st.set_page_config(page_title="学生用ツール", layout="centered")

# 【CSS】（前回までの神レイアウトを維持）
st.markdown("""
    <style>
    .main .block-container { padding: 1rem 0.2rem !important; }
    .cal-wrapper { display: grid; grid-template-columns: repeat(7, 1fr); gap: 3px; width: 100%; margin-bottom: 10px; }
    .cal-item { text-align: center; text-decoration: none; color: #31333F; display: flex; flex-direction: column; 
                justify-content: center; align-items: center; border-radius: 4px; font-size: 12px; min-height: 50px; }
    .header-item { font-weight: bold; font-size: 11px; min-height: 30px; }
    .date-item { background-color: #f0f2f6; border: 1px solid transparent; }
    .date-selected { background-color: #ff4b4b !important; color: white !important; font-weight: bold; }
    .marker { font-size: 10px; margin-top: -2px; }
    .stTable td { white-space: nowrap !important; font-size: 11px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ログイン状態の管理 ---
# これが「ログイン維持」のキモです
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# パスワードチェック用の関数
def check_password():
    if st.session_state.authenticated:
        return True
    
    st.title("🔒 ログイン")
    pw = st.text_input("パスワードを入力してください", type="password")
    if st.button("ログイン"):
        if pw == st.secrets.get("MY_PASSWORD"):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("パスワードが違います")
    return False

# --- 3. メインロジック ---
if check_password():
    # ログイン成功後の処理
    
    # 状態管理（日付）
    params = st.query_params
    if "date" in params and 'date_init' not in st.session_state:
        st.session_state.selected_date = datetime.strptime(params["date"], "%Y-%m-%d").date()
        st.session_state.date_init = True
    elif 'selected_date' not in st.session_state:
        st.session_state.selected_date = datetime.now().date()

    # データ読み込み用
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

    with tab_cal:
        # --- カレンダー表示（HTMLグリッド） ---
        now = datetime.now()
        c1, c2 = st.columns(2)
        sel_year = c1.selectbox("年", [2025, 2026], index=1, label_visibility="collapsed")
        sel_month = c2.selectbox("月", list(range(1, 13)), index=now.month-1, label_visibility="collapsed")
        
        html_code = '<div class="cal-wrapper">'
        days = [("日","red"), ("月",""), ("火",""), ("水",""), ("木",""), ("金",""), ("土","blue")]
        for d, color in days:
            html_code += f'<div class="cal-item header-item" style="color:{color};">{d}</div>'

        cal_obj = calendar.Calendar(firstweekday=6)
        weeks = cal_obj.monthdayscalendar(sel_year, sel_month)

        for week in weeks:
            for i, day in enumerate(week):
                if day != 0:
                    d_obj = datetime(sel_year, sel_month, day).date()
                    d_str = d_obj.strftime("%Y-%m-%d")
                    has_ev = not df_s.empty and d_str in df_s.iloc[:, 0].astype(str).values
                    is_hol = jpholiday.is_holiday(d_obj)
                    
                    color = "inherit"
                    if i == 0 or is_hol: color = "red"
                    elif i == 6: color = "blue"
                    
                    active_class = "date-selected" if d_obj == st.session_state.selected_date else "date-item"
                    marker = ""
                    if is_hol: marker = '<span class="marker">🎌</span>'
                    elif has_ev: marker = '<span class="marker">📍</span>'
                    
                    # hrefに現在のURLを維持しつつ日付を渡す
                    html_code += f'<a href="/?date={d_str}" target="_self" class="cal-item {active_class}" style="color:{color};">{day}{marker}</a>'
                else:
                    html_code += '<div class="cal-item"></div>'
        html_code += '</div>'
        st.markdown(html_code, unsafe_allow_html=True)

        st.divider()
        sel = st.session_state.selected_date
        st.subheader(f"🔍 {sel.strftime('%m/%d')} の情報")
        # （以下、予定表示などの処理）
        if not df_s.empty:
            day_evs = df_s[df_s.iloc[:, 0].astype(str).str.contains(sel.strftime("%Y-%m-%d"))]
            if not day_evs.empty:
                for v in day_evs.iloc[:, 1]: st.info(f"📍 {v}")
            else: st.write("予定なし")

    # --- 2. 予定追加 ---
    with tab_ev:
        st.subheader("予定の登録")
        st.write(f"選択日: **{st.session_state.selected_date}**")
        ev_text = st.text_input("予定を入力")
        if st.button("保存", key="save_ev"):
            if ev_text:
                requests.post(f"{gas_url}?sheet=schedules", json=[st.session_state.selected_date.strftime("%Y-%m-%d"), ev_text])
                st.success("完了！")
                st.rerun()

    # --- 3. 課題追加 ---
    with tab_task:
        st.subheader("課題の登録")
        st.write(f"期限: **{st.session_state.selected_date}**")
        with st.form("task_f"):
            t_sub = st.selectbox("教科", SUBJECTS)
            t_msg = st.text_input("内容")
            if st.form_submit_button("課題保存"):
                if t_msg:
                    requests.post(f"{gas_url}?sheet=tasks", json=[t_sub, t_msg, st.session_state.selected_date.strftime("%Y-%m-%d"), "FALSE"])
                    st.success("完了")
                    st.rerun()

    # --- 4. 時間割 ---
    with tab_time:
        st.subheader("週間時間割")
        timetable = {"月":["科技β","数基α","家庭","地総","科技α","言語文化","論表"],"火":["科技α","音楽","歴総","体育","数基α","言語文化","-"],"水":["保健","探求","論表","数基β","現国","コミュ I","-"],"木":["科技β","コミュ I","言語文化","家庭","音楽","数基α","LT"],"金":["地総","体育","数基β","現国","SP I","歴総","-"]}
        st.table(pd.DataFrame(timetable, index=[f"{i+1}限" for i in range(7)]))
