import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import jpholiday
import calendar

# --- 1. ページ設定 ---
st.set_page_config(page_title="学生用ツール", layout="centered")

# 【スマホ特化型：鉄壁の7分割デザイン】
st.markdown("""
    <style>
    /* 1. 画面端の余白を削り、カレンダーを横いっぱいに広げる */
    .main .block-container { padding: 1rem 0.2rem !important; }
    
    /* 2. 7分割を絶対死守するグリッド */
    .calendar-wrapper {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        width: 100%;
        border-top: 1px solid #ddd;
        border-left: 1px solid #ddd;
        background-color: white;
    }

    /* 3. 各セルの見た目（曜日も日付も共通） */
    .cal-box {
        border-right: 1px solid #ddd;
        border-bottom: 1px solid #ddd;
        text-align: center;
        text-decoration: none;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        color: #333;
    }

    /* 曜日（上段） */
    .head-box {
        background-color: #f8f9fa;
        font-weight: bold;
        font-size: 11px;
        padding: 8px 0;
    }

    /* 日付（下段以降） */
    .date-box {
        aspect-ratio: 1 / 1;
        cursor: pointer;
    }
    
    /* 選択中の日の色（赤背景に白文字） */
    .selected-box {
        background-color: #ff4b4b !important;
        color: white !important;
        font-weight: bold;
    }

    /* 土日の色 */
    .sun { color: red !important; }
    .sat { color: blue !important; }
    
    .day-text { font-size: 14px; }
    .mark-text { font-size: 9px; margin-top: -2px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ログイン管理（セッション維持） ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 ログイン")
    with st.form("login"):
        pw = st.text_input("パスワード", type="password")
        if st.form_submit_button("ログイン"):
            if pw == st.secrets.get("MY_PASSWORD"):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("パスワードが違います")
    st.stop()

# --- 3. 状態管理（URLパラメータを利用してログインを維持） ---
params = st.query_params
if "d" in params:
    st.session_state.selected_date = datetime.strptime(params["d"], "%Y-%m-%d").date()
elif 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.now().date()

# GAS連携用
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

# --- 4. メインコンテンツ ---
st.title("🎓 学生用ツール")
tabs = st.tabs(["📅 カレンダー", "📌 予定追加", "📝 課題追加", "⏰ 時間割"])

# カレンダータブ
with tabs[0]:
    # 年月選択
    c1, c2 = st.columns(2)
    y = c1.selectbox("年", [2025, 2026], index=1, key="y")
    m = c2.selectbox("月", list(range(1, 13)), index=datetime.now().month-1, key="m")

    # グリッド描画
    html = '<div class="calendar-wrapper">'
    
    # 曜日ヘッダー
    days = [("日","sun"), ("月",""), ("火",""), ("水",""), ("木",""), ("金",""), ("土","sat")]
    for d, cls in days:
        html += f'<div class="cal-box head-box {cls}">{d}</div>'

    # 日付
    cal = calendar.Calendar(firstweekday=6)
    weeks = cal.monthdayscalendar(y, m)
    for week in weeks:
        for i, day in enumerate(week):
            if day == 0:
                html += '<div class="cal-box" style="background:#fcfcfc;"></div>'
            else:
                d_obj = datetime(y, m, day).date()
                d_str = d_obj.strftime("%Y-%m-%d")
                is_sel = "selected-box" if d_obj == st.session_state.selected_date else ""
                is_hol = jpholiday.is_holiday(d_obj)
                
                # 色分け
                c_cls = "sun" if (i == 0 or is_hol) else ("sat" if i == 6 else "")
                mark = "🎌" if is_hol else ("📍" if not df_s.empty and d_str in df_s.iloc[:, 0].astype(str).values else "")
                
                # ★aタグでURLを更新しつつ、ブラウザに「同じページ」と認識させてログイン維持
                html += f'''
                    <a href="/?d={d_str}" target="_self" class="cal-box date-box {is_sel} {c_cls}">
                        <span class="day-text">{day}</span>
                        <span class="mark-text">{mark}</span>
                    </a>
                '''
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    st.divider()
    # 選択日の予定表示
    sel = st.session_state.selected_date
    st.subheader(f"🔍 {sel.strftime('%m/%d')} の予定")
    if not df_s.empty:
        evs = df_s[df_s.iloc[:, 0].astype(str).str.contains(sel.strftime("%Y-%m-%d"))]
        if not evs.empty:
            for v in evs.iloc[:, 1]: st.info(f"📍 {v}")
        else: st.write("予定なし")

# 予定追加タブ
with tabs[1]:
    st.subheader("予定の登録")
    st.write(f"日付: {st.session_state.selected_date}")
    new_ev = st.text_input("内容を入力")
    if st.button("GASへ送信", key="ev_btn"):
        if new_ev:
            requests.post(f"{gas_url}?sheet=schedules", json=[st.session_state.selected_date.strftime("%Y-%m-%d"), new_ev])
            st.success("保存完了")
            st.rerun()

# 課題追加タブ
with tabs[2]:
    st.subheader("課題の登録")
    with st.form("task"):
        sub = st.selectbox("教科", SUBJECTS)
        msg = st.text_input("内容")
        if st.form_submit_button("保存"):
            requests.post(f"{gas_url}?sheet=tasks", json=[sub, msg, st.session_state.selected_date.strftime("%Y-%m-%d"), "FALSE"])
            st.success("完了")

# 時間割タブ
with tabs[3]:
    st.subheader("週間時間割")
    timetable = {"月":["科技β","数基α","家庭","地総","科技α","言語文化","論表"],"火":["科技α","音楽","歴総","体育","数基α","言語文化","-"],"水":["保健","探求","論表","数基β","現国","コミュ I","-"],"木":["科技β","コミュ I","言語文化","家庭","音楽","数基α","LT"],"金":["地総","体育","数基β","現国","SP I","歴総","-"]}
    st.table(pd.DataFrame(timetable, index=[f"{i+1}限" for i in range(7)]))
