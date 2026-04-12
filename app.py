import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
import jpholiday
import calendar

# --- 1. ページ設定 & デザイン ---
st.set_page_config(page_title="学生用マイ・ツール Pro Max", layout="centered")

# CSS: スマホで見やすく、カレンダーを綺麗に整列
st.markdown("""
    <style>
    .main .block-container { padding: 1rem 0.2rem !important; }
    .calendar-wrapper { 
        display: grid; grid-template-columns: repeat(7, 1fr); 
        width: 100%; border-top: 1px solid #ddd; border-left: 1px solid #ddd; background-color: white; 
    }
    .cal-box { 
        border-right: 1px solid #ddd; border-bottom: 1px solid #ddd; 
        text-align: center; text-decoration: none; display: flex; 
        flex-direction: column; justify-content: center; align-items: center; color: #333; 
    }
    .head-box { background-color: #f8f9fa; font-weight: bold; font-size: 11px; padding: 8px 0; }
    .date-box { aspect-ratio: 1 / 1; cursor: pointer; }
    .selected-box { background-color: #ff4b4b !important; color: white !important; font-weight: bold; }
    .sun { color: red !important; }
    .sat { color: blue !important; }
    .day-text { font-size: 14px; }
    .mark-text { font-size: 9px; margin-top: -2px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 持ち物データ (PC版から移植) ---
BELONGINGS = {
    "現国": ["教科書「現代の国語」", "ノート", "電子辞書", "核心漢字2500", "論理エンジン⑧-1", "現代文ステップ1.5"],
    "言語文化": ["教科書「言語文化」", "ノート", "電子辞書", "古典文法ノート", "グランステップ古典1.5", "漢文必携"],
    "地総": ["教科書「新地理総合」", "地図帳「新詳高等地図」"],
    "歴総": ["教科書「歴史総合」", "副教材「歴史総合ワークノート」"],
    "数基α": ["教科書「NEXT数学I」", "ノート", "CONNECT", "完成ノート", "Focus Gold", "短期完成ノート"],
    "数基β": ["教科書「NEXT数学A」", "ノート", "CONNECT", "完成ノート", "Focus Gold", "短期完成ノート"],
    "科技α": ["教科書「物理基礎」", "セミナー物理基礎", "ノート"],
    "科技β": ["教科書「生物基礎」", "リードα生物基礎", "コンセプトノート"],
    "保健": ["教科書「現代高等保健体育」", "図説現代高等保健"],
    "体育": ["体操服", "最新スポーツルール'26"],
    "音楽": ["教科書", "ファイル"],
    "コミュ I": ["Heartening教科書", "LEAP", "Cutting Edge Yellow", "Navi Book"],
    "論表": ["EARTHRISE", "GRAND EARTH 総合英語", "Workbook", "Listening Pre-Std", "Listening Std"],
    "SP I": ["Heartening教科書"],
    "家庭": ["教科書「新図説 家庭基礎」", "2026 生活学 Navi", "ファイル"],
    "探求基礎": ["テキスト「課題研究メソッド」"],
    "LT": ["（特になし）"]
}

# --- 3. ログイン管理 ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 ログイン")
    pw = st.text_input("パスワード", type="password")
    if st.button("ログイン"):
        if pw == st.secrets.get("MY_PASSWORD"):
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

# --- 4. データ読み込みと時間設定 ---
gas_url = st.secrets.get("GAS_URL")
sheet_url = st.secrets.get("connections", {}).get("gsheets", {}).get("spreadsheet")

def load_data(sheet_name):
    try:
        if not sheet_url: return pd.DataFrame(columns=['date', 'content'])
        base = sheet_url.split('/edit')[0]
        url = f"{base}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        return pd.read_csv(url)
    except:
        return pd.DataFrame(columns=['date', 'content'])

# 先にデータを読み込む
df_s = load_data("schedules")

# 日本時間を「デフォルトの今日」にする
JST = timezone(timedelta(hours=+9), 'JST')
now_jst = datetime.now(JST).date()

# 状態管理
if "d" in st.query_params:
    st.session_state.selected_date = datetime.strptime(st.query_params["d"], "%Y-%m-%d").date()
elif 'selected_date' not in st.session_state:
    st.session_state.selected_date = now_jst

# --- 5. メインUI ---
st.title("🎓 学生用ツール Pro")
tabs = st.tabs(["📅 カレンダー", "🎒 持ち物", "📝 登録"])

# 【タブ1: カレンダー】
with tabs[0]:
    c1, c2 = st.columns(2)
    y = c1.selectbox("年", [2025, 2026], index=([2025, 2026].index(now_jst.year)))
    m = c2.selectbox("月", list(range(1, 13)), index=now_jst.month - 1)
    
    html = '<div class="calendar-wrapper">'
    # 曜日のヘッダー
    for d, cls in [("日","sun"), ("月",""), ("火",""), ("水",""), ("木",""), ("金",""), ("土","sat")]:
        html += f'<div class="cal-box head-box {cls}">{d}</div>'

    # 日付の描画
    weeks = calendar.Calendar(firstweekday=6).monthdayscalendar(y, m)
    for week in weeks:
        for i, day in enumerate(week):
            if day == 0:
                html += '<div class="cal-box" style="background:#fcfcfc;"></div>'
            else:
                d_obj = datetime(y, m, day).date()
                d_str = d_obj.strftime("%Y-%m-%d")
                is_sel = "selected-box" if d_obj == st.session_state.selected_date else ""
                is_hol = jpholiday.is_holiday(d_obj)
                c_cls = "sun" if (i == 0 or is_hol) else ("sat" if i == 6 else "")
                
                # 予定の有無を確認
                has_ev = not df_s.empty and d_str in df_s.iloc[:, 0].astype(str).values
                mark = "🎌" if is_hol else ("📍" if has_ev else "")
                
                # Aタグを構築
                link = f'<a href="/?d={d_str}" target="_self" class="cal-box date-box {is_sel} {c_cls}">'
                html += f'{link}<span class="day-text">{day}</span><span class="mark-text">{mark}</span></a>'
    
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    sel = st.session_state.selected_date
    st.subheader(f"📅 {sel.strftime('%m/%d')} の予定")
    evs = df_s[df_s.iloc[:, 0].astype(str).str.contains(sel.strftime("%Y-%m-%d"))] if not df_s.empty else pd.DataFrame()
    if not evs.empty:
        for v in evs.iloc[:, 1]: st.info(f"📍 {v}")
    else: st.write("予定なし")

# 【タブ2: 持ち物/時間割】
with tabs[1]:
    days = ["月","火","水","木","金","土","日"]
    sel_day_name = days[st.session_state.selected_date.weekday()]
    st.subheader(f"🎒 {sel_day_name}曜日の持ち物")
    
    timetable = {
        "月":["科技β","数基α","家庭","地総","科技α","言語文化","論表"],
        "火":["科技α","音楽","歴総","体育","数基α","言語文化"],
        "水":["保健","探求基礎","論表","数基β","現国","コミュ I"],
        "木":["科技β","コミュ I","言語文化","家庭","音楽","数基α","LT"],
        "金":["地総","体育","数基β","現国","SP I","歴総"]
    }
    
    if sel_day_name in timetable:
        for i, sub in enumerate(timetable[sel_day_name]):
            with st.expander(f"{i+1}限: {sub}"):
                for item in BELONGINGS.get(sub, ["（データなし）"]):
                    st.write(f"✅ {item}")
    else:
        st.write("休みの日です。")

# 【タブ3: 登録】
with tabs[2]:
    st.subheader("📝 予定・課題の登録")
    sel = st.session_state.selected_date
    st.write(f"対象日: **{sel.strftime('%Y/%m/%d')}**")
    
    mode = st.radio("種類", ["📅 予定", "✍️ 課題"], horizontal=True)
    
    if mode == "📅 予定":
        with st.form("f1"):
            txt = st.text_input("内容")
            if st.form_submit_button("保存"):
                requests.post(f"{gas_url}?sheet=schedules", json=[sel.strftime("%Y-%m-%d"), txt])
                st.success("保存しました！")
    else:
        with st.form("f2"):
            sub = st.selectbox("教科", list(BELONGINGS.keys()))
            txt = st.text_input("課題内容")
            if st.form_submit_button("課題リストに追加"):
                requests.post(f"{gas_url}?sheet=tasks", json=[sub, txt, sel.strftime("%Y-%m-%d"), "FALSE"])
                st.success("追加しました！")
