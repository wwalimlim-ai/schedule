import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import jpholiday
import calendar

# --- 1. ページ設定 ---
st.set_page_config(page_title="学生用ツール", layout="centered")

# 【最終防衛CSS】
# Streamlitがスマホで「縦」にしようとする計算を、CSSの力で物理的に上書きします。
st.markdown("""
    <style>
    /* 画面端の余白を削る */
    .main .block-container { padding: 1rem 0.2rem !important; }
    
    /* [重要] カラムを包むコンテナを「絶対に横並び・折り返し禁止」に固定 */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: stretch !important;
        gap: 2px !important;
    }
    
    /* [重要] 各カラムを画面幅の1/7に強制固定 */
    div[data-testid="column"] {
        width: 14.28% !important;
        flex: 1 1 0% !important;
        min-width: 0 !important;
    }

    /* ボタンのデザイン調整 */
    .stButton > button {
        width: 100% !important;
        aspect-ratio: 1 / 1.1 !important;
        padding: 0 !important;
        font-size: 11px !important;
        border-radius: 4px !important;
        margin: 0 !important;
        line-height: 1.2 !important;
    }
    
    /* 曜日ヘッダー */
    .day-header-grid {
        display: flex;
        flex-direction: row;
        margin-bottom: 5px;
    }
    .day-header-item {
        width: 14.28%;
        text-align: center;
        font-size: 11px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ログイン管理（URLを変えないのでこれで安定します） ---
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

# --- 3. ログイン後の処理（URL操作なし） ---
if 'selected_date' not in st.session_state:
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

st.title("🎓 学生用ツール")
tab_cal, tab_ev, tab_task, tab_time = st.tabs(["📅 カレンダー", "📌 予定追加", "📝 課題追加", "⏰ 時間割"])

with tab_cal:
    now = datetime.now()
    c1, c2 = st.columns(2)
    sel_year = c1.selectbox("年", [2025, 2026], index=1, label_visibility="collapsed")
    sel_month = c2.selectbox("月", list(range(1, 13)), index=now.month-1, label_visibility="collapsed")
    
    st.markdown("""
        <div class="day-header-grid">
            <div class="day-header-item" style="color:red;">日</div><div class="day-header-item">月</div>
            <div class="day-header-item">火</div><div class="day-header-item">水</div>
            <div class="day-header-item">木</div><div class="day-header-item">金</div>
            <div class="day-header-item" style="color:blue;">土</div>
        </div>
    """, unsafe_allow_html=True)

    cal_obj = calendar.Calendar(firstweekday=6)
    weeks = cal_obj.monthdayscalendar(sel_year, sel_month)

    for week in weeks:
        # この columns(7) がスマホで縦にならないように、CSSで強制しています
        cols = st.columns(7) 
        for i, day in enumerate(week):
            if day != 0:
                d_obj = datetime(sel_year, sel_month, day).date()
                d_str = d_obj.strftime("%Y-%m-%d")
                has_ev = not df_s.empty and d_str in df_s.iloc[:, 0].astype(str).values
                is_hol = jpholiday.is_holiday(d_obj)
                
                label = f"{day}"
                if is_hol: label += "\n🎌"
                elif has_ev: label += "\n📍"
                
                # ログイン維持の鍵：リンクではなく「本物のボタン」
                btn_type = "primary" if d_obj == st.session_state.selected_date else "secondary"
                
                if cols[i].button(label, key=f"btn_{d_str}", type=btn_type):
                    st.session_state.selected_date = d_obj
                    st.rerun() # URLを変えずに中身だけ書き換える
            else:
                cols[i].empty()

    st.divider()
    sel = st.session_state.selected_date
    st.subheader(f"🔍 {sel.strftime('%m/%d')} の情報")
    if not df_s.empty:
        day_evs = df_s[df_s.iloc[:, 0].astype(str).str.contains(sel.strftime("%Y-%m-%d"))]
        if not day_evs.empty:
            for v in day_evs.iloc[:, 1]: st.info(f"📍 {v}")
        else: st.write("予定なし")

# --- 他のタブは維持 ---
with tab_ev:
    st.subheader("予定の登録")
    st.write(f"選択日: **{st.session_state.selected_date}**")
    ev_text = st.text_input("予定を入力", key="ev_input")
    if st.button("保存", key="save_ev"):
        if ev_text:
            requests.post(f"{gas_url}?sheet=schedules", json=[st.session_state.selected_date.strftime("%Y-%m-%d"), ev_text])
            st.success("完了！")
            st.rerun()

# (以下、課題登録・時間割は前回と同じ)
