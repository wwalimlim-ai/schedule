import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
import jpholiday
import calendar

# --- 1. ページ設定 (最上部への固定と余白削除) ---
st.set_page_config(page_title="MyTool", layout="centered")

st.markdown("""
    <style>
    .stAppHeader { display: none; }
    .main .block-container { padding-top: 0rem !important; padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 2px; position: sticky; top: 0; z-index: 1000; background-color: white; }
    .calendar-wrapper { display: grid; grid-template-columns: repeat(7, 1fr); background: white; border: 1px solid #eee; }
    .cal-box { aspect-ratio: 1/1; display: flex; flex-direction: column; justify-content: center; align-items: center; text-decoration: none; border: 0.5px solid #f8f8f8; color: #444; }
    .head-box { font-size: 10px; font-weight: bold; background: #fafafa; height: 30px; border: none; }
    .date-box { font-size: 16px; position: relative; }
    .selected-box { background: #ff4b4b !important; color: white !important; border-radius: 8px; font-weight: bold; }
    .sun { color: #ff4b4b; } .sat { color: #007bff; }
    .has-event-dot { width: 5px; height: 5px; background-color: #ff9f00; border-radius: 50%; margin-top: 2px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. データ定義 (TIMETABLE等は以前と同じ) ---
BELONGINGS = {"現国": ["教科書", "ノート", "電子辞書", "核心漢字", "論理エンジン", "ステップ1.5"],"言語文化": ["教科書", "ノート", "電子辞書", "文法ノート", "グランステップ", "漢文必携"],"地総": ["教科書", "地図帳"], "歴総": ["教科書", "ワークノート"],"数基α": ["教科書I", "ノート", "CONNECT", "Focus Gold"],"数基β": ["教科書A", "ノート", "CONNECT", "Focus Gold"],"科技α": ["物理基礎", "セミナー", "ノート"], "科技β": ["生物基礎", "リードα", "ノート"],"保健": ["教科書", "図説"], "体育": ["体操服", "ルール本"], "音楽": ["教科書", "ファイル"],"コミュ I": ["Heartening", "LEAP", "Cutting Edge", "Navi"],"論表": ["EARTHRISE", "総合英語", "Workbook", "Listening"],"SP I": ["Heartening"], "家庭": ["教科書", "生活学Navi", "ファイル"],"探求基礎": ["テキスト「課題研究メソッド」"], "LT": ["（特になし）"]}
TIMETABLE = {"月":["科技β","数基α","家庭","地総","科技α","言語文化","論表"],"火":["科技α","音楽","歴総","体育","数基α","言語文化"],"水":["保健","探求基礎","論表","数基β","現国","コミュ I"],"木":["科技β","コミュ I","言語文化","家庭","音楽","数基α","LT"],"金":["地総","体育","数基β","現国","SP I","歴総"]}

# --- 3. データ読み込み（キャッシュクリア機能を強化） ---
gas_url = st.secrets.get("GAS_URL")
sheet_url = st.secrets.get("connections", {}).get("gsheets", {}).get("spreadsheet")

# キャッシュの寿命を短く(ttl=10)し、手動クリアも可能にする
@st.cache_data(ttl=10)
def fetch_csv(url):
    return pd.read_csv(url)

def load_data(sheet_name):
    try:
        base = sheet_url.split('/edit')[0]
        url = f"{base}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        return fetch_csv(url)
    except: return pd.DataFrame()

# 保存処理後にキャッシュを強制破棄する関数
def clear_all_cache():
    st.cache_data.clear()

df_s = load_data("schedules")
df_t = load_data("tasks")

# 時間設定
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST)

if "d" in st.query_params:
    st.session_state.selected_date = datetime.strptime(st.query_params["d"], "%Y-%m-%d").date()
else:
    if 'selected_date' not in st.session_state:
        st.session_state.selected_date = now.date()

sel = st.session_state.selected_date

# --- 4. メインUI ---
tabs = st.tabs(["📅 カレンダー", "🎒 持ち物", "📋 課題", "📝 予定一覧", "➕ 登録"])

with tabs[0]: # カレンダー
    st.write(f"### 📅 {sel.month}/{sel.day}")
    html = '<div class="calendar-wrapper">'
    for d, cls in [("日","sun"),("月",""),("火",""),("水",""),("木",""),("金",""),("土","sat")]:
        html += f'<div class="cal-box head-box {cls}">{d}</div>'
    for week in calendar.Calendar(firstweekday=6).monthdayscalendar(now.year, now.month):
        for i, day in enumerate(week):
            if day == 0: html += '<div class="cal-box"></div>'
            else:
                d_obj = datetime(now.year, now.month, day).date()
                d_str = d_obj.strftime("%Y-%m-%d")
                is_sel = "selected-box" if d_obj == sel else ""
                c_cls = "sun" if (i == 0 or jpholiday.is_holiday(d_obj)) else ("sat" if i == 6 else "")
                has_ev = not df_s.empty and d_str in df_s.iloc[:, 0].astype(str).values
                dot = '<div class="has-event-dot"></div>' if has_ev else ""
                html += f'<a href="/?d={d_str}" target="_self" class="cal-box date-box {is_sel} {c_cls}">{day}{dot}</a>'
    st.markdown(html + '</div>', unsafe_allow_html=True)
    evs = df_s[df_s.iloc[:, 0].astype(str).str.contains(sel.strftime("%Y-%m-%d"))] if not df_s.empty else []
    if len(evs) > 0:
        for v in evs.iloc[:, 1]: st.info(v)

with tabs[1]: # 持ち物
    day_name = ["月","火","水","木","金","土","日"][sel.weekday()]
    st.write(f"### 🎒 {day_name}曜日のセット")
    if day_name in TIMETABLE:
        for sub in TIMETABLE[day_name]:
            items = " / ".join(BELONGINGS.get(sub, []))
            st.write(f"**{sub}**: {items}"); st.divider()
    else: st.write("お休みです")

with tabs[2]: # 課題
    st.write("### 📋 未完了の課題")
    if not df_t.empty:
        uncompleted = df_t[df_t.iloc[:, 3].astype(str).str.upper() == "FALSE"]
        if not uncompleted.empty:
            for _, row in uncompleted.iterrows(): st.warning(f"**{row[0]}**: {row[1]} (期限: {row[2]})")
        else: st.success("課題はすべて完了！")

with tabs[3]: # 予定一覧
    st.write("### 📝 今後の予定")
    if not df_s.empty:
        temp_df = df_s.copy()
        temp_df.iloc[:, 0] = pd.to_datetime(temp_df.iloc[:, 0])
        future = temp_df[temp_df.iloc[:, 0].dt.date >= now.date()].sort_values(temp_df.columns[0])
        for _, row in future.iterrows(): st.write(f"📅 {row[0].strftime('%m/%d')}: {row[1]}")

with tabs[4]: # 登録
    st.write(f"### ➕ {sel.month}/{sel.day} に追加")
    mode = st.radio("種類", ["予定", "課題"], horizontal=True)
    with st.form("add_form", clear_on_submit=True):
        txt = st.text_input("内容を入力")
        sub = st.selectbox("教科", list(BELONGINGS.keys())) if mode == "課題" else ""
        submit = st.form_submit_button("保存して更新")
        
        if submit:
            if not txt:
                st.error("内容を入力してください")
            else:
                # GASへ送信
                data = [sel.strftime("%Y-%m-%d"), txt] if mode == "予定" else [sub, txt, sel.strftime("%Y-%m-%d"), "FALSE"]
                sheet_name = "schedules" if mode == "予定" else "tasks"
                res = requests.post(f"{gas_url}?sheet={sheet_name}", json=data)
                
                if res.status_code == 200:
                    # 🚀 ここが重要：キャッシュを消してからリロード
                    clear_all_cache()
                    st.success("スプレッドシートに保存しました！一覧を更新します...")
                    st.rerun()
                else:
                    st.error("通信エラーが発生しました")
