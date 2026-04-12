import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
import jpholiday
import calendar

# --- 1. ページ設定 ---
st.set_page_config(page_title="MyTool", layout="centered")

st.markdown("""
    <style>
    .main .block-container { padding: 0.5rem 0.5rem !important; }
    .calendar-wrapper { display: grid; grid-template-columns: repeat(7, 1fr); background: white; border: 1px solid #eee; }
    .cal-box { aspect-ratio: 1/1; display: flex; flex-direction: column; justify-content: center; align-items: center; text-decoration: none; border: 0.5px solid #f8f8f8; color: #444; }
    .head-box { font-size: 10px; font-weight: bold; background: #fafafa; height: 30px; border: none; }
    .date-box { font-size: 16px; position: relative; }
    .selected-box { background: #ff4b4b !important; color: white !important; border-radius: 8px; font-weight: bold; }
    .sun { color: #ff4b4b; } .sat { color: #007bff; }
    /* 予定がある日の印を強調 */
    .has-event-dot { width: 5px; height: 5px; background-color: #ff9f00; border-radius: 50%; margin-top: 2px; }
    div[data-testid="stExpander"] { border: none; background: #f0f2f6; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 持ち物データ ---
BELONGINGS = {
    "現国": ["教科書", "ノート", "電子辞書", "核心漢字", "論理エンジン", "ステップ1.5"],
    "言語文化": ["教科書", "ノート", "電子辞書", "文法ノート", "グランステップ", "漢文必携"],
    "地総": ["教科書", "地図帳"], "歴総": ["教科書", "ワークノート"],
    "数基α": ["教科書I", "ノート", "CONNECT", "Focus Gold"],
    "数基β": ["教科書A", "ノート", "CONNECT", "Focus Gold"],
    "科技α": ["物理基礎", "セミナー", "ノート"], "科技β": ["生物基礎", "リードα", "ノート"],
    "保健": ["教科書", "図説"], "体育": ["体操服", "ルール本"], "音楽": ["教科書", "ファイル"],
    "コミュ I": ["Heartening", "LEAP", "Cutting Edge", "Navi"],
    "論表": ["EARTHRISE", "総合英語", "Workbook", "Listening"],
    "SP I": ["Heartening"], "家庭": ["教科書", "生活学Navi", "ファイル"],
    "探求基礎": ["課題研究メソッド"], "LT": ["（特になし）"]
}

# --- 3. データ読み込み（登録後はキャッシュを飛ばす） ---
gas_url = st.secrets.get("GAS_URL")
sheet_url = st.secrets.get("connections", {}).get("gsheets", {}).get("spreadsheet")

# clear_cacheがTrueの時は最新を取得
def load_data(sheet_name, clear_cache=False):
    if clear_cache:
        st.cache_data.clear()
    try:
        base = sheet_url.split('/edit')[0]
        return pd.read_csv(f"{base}/gviz/tq?tqx=out:csv&sheet={sheet_name}")
    except: return pd.DataFrame()

df_s = load_data("schedules")
df_t = load_data("tasks")

# 時間設定
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST)

if "d" in st.query_params:
    st.session_state.selected_date = datetime.strptime(st.query_params["d"], "%Y-%m-%d").date()
elif 'selected_date' not in st.session_state:
    st.session_state.selected_date = now.date()

sel = st.session_state.selected_date

# --- 4. メインUI ---
st.title(f"🎓 {sel.month}/{sel.day}")

with st.expander("📅 別の月を表示"):
    y = st.selectbox("年", [2025, 2026], index=([2025, 2026].index(now.year)))
    m = st.selectbox("月", list(range(1, 13)), index=now.month - 1)
if 'y' not in locals():
    y, m = now.year, now.month

# カレンダー表示
html = '<div class="calendar-wrapper">'
for d, cls in [("日","sun"),("月",""),("火",""),("水",""),("木",""),("金",""),("土","sat")]:
    html += f'<div class="cal-box head-box {cls}">{d}</div>'

for week in calendar.Calendar(firstweekday=6).monthdayscalendar(y, m):
    for i, day in enumerate(week):
        if day == 0: html += '<div class="cal-box"></div>'
        else:
            d_obj = datetime(y, m, day).date()
            d_str = d_obj.strftime("%Y-%m-%d")
            is_sel = "selected-box" if d_obj == sel else ""
            c_cls = "sun" if (i == 0 or jpholiday.is_holiday(d_obj)) else ("sat" if i == 6 else "")
            
            # 予定があるかチェック
            has_ev = not df_s.empty and d_str in df_s.iloc[:, 0].astype(str).values
            dot = '<div class="has-event-dot"></div>' if has_ev else ""
            
            html += f'<a href="/?d={d_str}" target="_self" class="cal-box date-box {is_sel} {c_cls}">{day}{dot}</a>'
html += '</div>'
st.markdown(html, unsafe_allow_html=True)

st.divider()

# --- 5. タブ構成（予定一覧を追加） ---
tabs = st.tabs(["📌 予定", "🎒 持ち物", "📋 課題", "📝 全予定", "➕ 登録"])

with tabs[0]: # 選択日の予定
    evs = df_s[df_s.iloc[:, 0].astype(str).str.contains(sel.strftime("%Y-%m-%d"))] if not df_s.empty else []
    if len(evs) > 0:
        for v in evs.iloc[:, 1]: st.info(v)
    else: st.caption("この日の予定はありません")

with tabs[1]: # 持ち物
    day_name = ["月","火","水","木","金","土","日"][sel.weekday()]
    timetable = {"月":["科技β","数基α","家庭","地総","科技α","言語文化","論表"],"火":["科技α","音楽","歴総","体育","数基α","言語文化"],"水":["保健","探求基礎","論表","数基β","現国","コミュ I"],"木":["科技β","コミュ I","言語文化","家庭","音楽","数基α","LT"],"金":["地総","体育","数基β","現国","SP I","歴総"]}
    if day_name in timetable:
        for sub in timetable[day_name]:
            items = " / ".join(BELONGINGS.get(sub, []))
            st.write(f"**{sub}**: {items}")
    else: st.write("お休みです")

with tabs[2]: # 課題
    if not df_t.empty:
        uncompleted = df_t[df_t.iloc[:, 3].astype(str).str.upper() == "FALSE"]
        if not uncompleted.empty:
            for _, row in uncompleted.iterrows():
                st.warning(f"**{row[0]}**: {row[1]} (期限: {row[2]})")
        else: st.success("課題はすべて完了！")

with tabs[3]: # ★全予定一覧
    st.subheader("今後の予定一覧")
    if not df_s.empty:
        # 日付順に並び替え（今日以降を表示）
        df_s.iloc[:, 0] = pd.to_datetime(df_s.iloc[:, 0])
        future_evs = df_s[df_s.iloc[:, 0].dt.date >= now.date()].sort_values(df_s.columns[0])
        for _, row in future_evs.iterrows():
            st.write(f"📅 {row[0].strftime('%m/%d')}: {row[1]}")
    else: st.write("予定が登録されていません")

with tabs[4]: # 登録
    mode = st.radio("登録種別", ["予定", "課題"], horizontal=True)
    with st.form("add_form"):
        txt = st.text_input("内容")
        sub = st.selectbox("教科(課題のみ)", list(BELONGINGS.keys())) if mode == "課題" else ""
        if st.form_submit_button("保存"):
            if mode == "予定":
                requests.post(f"{gas_url}?sheet=schedules", json=[sel.strftime("%Y-%m-%d"), txt])
            else:
                requests.post(f"{gas_url}?sheet=tasks", json=[sub, txt, sel.strftime("%Y-%m-%d"), "FALSE"])
            st.success("追加しました！(一覧に反映されない場合は更新してください)")
            # 登録直後に最新データを読み込む
            load_data("schedules", clear_cache=True)
            st.rerun()
