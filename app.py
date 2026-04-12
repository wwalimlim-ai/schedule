import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import jpholiday
import calendar

# --- ページ設定 ---
st.set_page_config(page_title="学生用ツール", layout="centered")

# CSS: ボタンの幅を揃え、表の改行を防止
st.markdown("""
    <style>
    div.stButton > button { width: 100%; padding: 0.5rem 0; }
    .stTable td { white-space: nowrap !important; }
    </style>
    """, unsafe_allow_html=True)

# Secrets & Data Loading
correct_pw = st.secrets.get("MY_PASSWORD")
gas_url = st.secrets.get("GAS_URL")
sheet_url = st.secrets.get("connections", {}).get("gsheets", {}).get("spreadsheet")

pw = st.sidebar.text_input("パスワード", type="password")
if pw != correct_pw:
    st.info("ログインしてください。")
    st.stop()

def load_data(sheet_name):
    if not sheet_url: return pd.DataFrame()
    try:
        base_url = sheet_url.split('/edit')[0]
        csv_url = f"{base_url}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        return pd.read_csv(csv_url)
    except: return pd.DataFrame()

df_s = load_data("schedules")
df_t = load_data("tasks")

SUBJECTS = ["教科なし", "現国", "言語文化", "地総", "歴総", "数基α", "数基β", "科技α", "科技β", "コミュ I", "論表", "SP I", "保健", "体育", "音楽", "家庭", "探求基礎", "LT"]

# --- メイン画面 ---
st.title("🎓 学生用ツール")

# 状態保持用の変数を初期化（選択した日付を記憶）
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.now().date()

tab_cal, tab_ev, tab_task, tab_time = st.tabs(["📅 カレンダー", "📌 予定追加", "📝 課題追加", "⏰ 時間割"])

# --- 1. カレンダータブ（選択のみ） ---
with tab_cal:
    col_y, col_m = st.columns(2)
    y = col_y.selectbox("年", [2025, 2026], index=1)
    m = col_m.selectbox("月", list(range(1, 13)), index=datetime.now().month-1)
    
    # カレンダーを自作ボタンで表示
    cal = calendar.monthcalendar(y, m)
    days_labels = ["月", "火", "水", "木", "金", "土", "日"]
    cols = st.columns(7)
    for i, label in enumerate(days_labels): cols[i].write(f"**{label}**")

    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day != 0:
                d_str = f"{y}-{m:02d}-{day:02d}"
                # 予定があるか確認
                has_ev = not df_s.empty and d_str in df_s.iloc[:, 0].astype(str).values
                # 祝日か確認
                is_hol = jpholiday.is_holiday(datetime(y, m, day))
                
                label = f"{day}\n📍" if has_ev else f"{day}"
                if is_hol: label = f"{day}\n🎌"
                
                if cols[i].button(label, key=f"btn_{d_str}"):
                    st.session_state.selected_date = datetime(y, m, day).date()
            else:
                cols[i].write("")

    st.divider()
    # 選択された日の詳細表示
    sel = st.session_state.selected_date
    st.subheader(f"🔍 {sel.strftime('%m月%d日')} の詳細")
    hol_n = jpholiday.is_holiday_name(sel)
    if hol_n: st.error(f"🎌 祝日: {hol_n}")
    
    if not df_s.empty:
        evs = df_s[df_s.iloc[:, 0].astype(str) == sel.strftime("%Y-%m-%d")]
        if not evs.empty:
            for v in evs.iloc[:, 1]: st.info(f"📍 {v}")
        else: st.write("予定なし")

# --- 2. 予定追加（キーボード排除） ---
with tab_ev:
    st.subheader("予定の追加")
    st.write(f"選択中の日: **{st.session_state.selected_date}**")
    ev_type = st.selectbox("内容", ["部活", "塾", "検定", "休み", "提出物期限", "テスト", "その他"])
    ev_memo = ""
    if ev_type == "その他":
        ev_memo = st.text_input("メモ（入力が必要な場合のみ）")
    
    if st.button("この日で保存"):
        final_text = ev_memo if ev_type == "その他" else ev_type
        requests.post(f"{gas_url}?sheet=schedules", json=[st.session_state.selected_date.strftime("%Y-%m-%d"), final_text])
        st.success("保存しました")
        st.rerun()

# --- 3. 課題追加 ---
with tab_task:
    st.subheader("課題の登録")
    st.write(f"期限日: **{st.session_state.selected_date}**")
    t_sub = st.selectbox("教科", SUBJECTS)
    t_msg = st.text_input("課題内容（ここだけは入力が必要）")
    
    if st.button("課題を保存"):
        requests.post(f"{gas_url}?sheet=tasks", json=[t_sub, t_msg, st.session_state.selected_date.strftime("%Y-%m-%d"), "FALSE"])
        st.success("保存完了")
        st.rerun()

# --- 4. 時間割（一括表） ---
with tab_time:
    st.subheader("週間時間割")
    timetable = {
        "月": ["科技β", "数基α", "家庭", "地総", "科技α", "言語文化", "論表"],
        "火": ["科技α", "音楽", "歴総", "体育", "数基α", "言語文化", "-"],
        "水": ["保健", "探求", "論表", "数基β", "現国", "コミュI", "-"],
        "木": ["科技β", "コミュI", "言語文化", "家庭", "音楽", "数基α", "LT"],
        "金": ["地総", "体育", "数基β", "現国", "SP I", "歴総", "-"]
    }
    st.table(pd.DataFrame(timetable, index=[f"{i+1}限" for i in range(7)]))
