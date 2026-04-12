import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import jpholiday
import calendar

# --- 1. ページ設定 & デザイン ---
st.set_page_config(page_title="学生用マイ・ツール Pro Max", layout="centered")

st.markdown("""
    <style>
    .main .block-container { padding: 1rem 0.2rem !important; }
    .calendar-wrapper { display: grid; grid-template-columns: repeat(7, 1fr); width: 100%; border-top: 1px solid #ddd; border-left: 1px solid #ddd; background-color: white; }
    .cal-box { border-right: 1px solid #ddd; border-bottom: 1px solid #ddd; text-align: center; text-decoration: none; display: flex; flex-direction: column; justify-content: center; align-items: center; color: #333; }
    .head-box { background-color: #f8f9fa; font-weight: bold; font-size: 11px; padding: 8px 0; }
    .date-box { aspect-ratio: 1 / 1; cursor: pointer; }
    .selected-box { background-color: #ff4b4b !important; color: white !important; font-weight: bold; }
    .sun { color: red !important; }
    .sat { color: blue !important; }
    .day-text { font-size: 14px; }
    .mark-text { font-size: 9px; margin-top: -2px; }
    /* 持ち物リスト用のスタイル */
    .belonging-item { background: #f0f2f6; padding: 5px 10px; border-radius: 5px; margin-bottom: 5px; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. PC版から移植したデータ ---
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

# --- 4. 状態管理 & データ読み込み ---
params = st.query_params
if "d" in params:
    st.session_state.selected_date = datetime.strptime(params["d"], "%Y-%m-%d").date()
elif 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.now().date()

gas_url = st.secrets.get("GAS_URL")
sheet_url = st.secrets.get("connections", {}).get("gsheets", {}).get("spreadsheet")

def load_data(sheet_name):
    try:
        url = f"{sheet_url.split('/edit')[0]}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        return pd.read_csv(url)
    except: return pd.DataFrame()

df_s = load_data("schedules")

# --- 5. メイン画面 ---
st.title("🎓 学生用ツール Pro")
tabs = st.tabs(["📅 カレンダー", "🎒 持ち物/時間割", "📝 課題/予定追加"])

# 【タブ1: カレンダー】
with tabs[0]:
    c1, c2 = st.columns(2)
    y = c1.selectbox("年", [2025, 2026], index=1)
    m = c2.selectbox("月", list(range(1, 13)), index=datetime.now().month-1)

    html = '<div class="calendar-wrapper">'
    for d, cls in [("日","sun"), ("月",""), ("火",""), ("水",""), ("木",""), ("金",""), ("土","sat")]:
        html += f'<div class="cal-box head-box {cls}">{d}</div>'

    weeks = calendar.Calendar(firstweekday=6).monthdayscalendar(y, m)
    for week in weeks:
        for i, day in enumerate(week):
            if day == 0: html += '<div class="cal-box" style="background:#fcfcfc;"></div>'
            else:
                d_obj = datetime(y, m, day).date()
                d_str = d_obj.strftime("%Y-%m-%d")
                is_sel = "selected-box" if d_obj == st.session_state.selected_date else ""
                is_hol = jpholiday.is_holiday(d_obj)
                c_cls = "sun" if (i == 0 or is_hol) else ("sat" if i == 6 else "")
                mark = "🎌" if is_hol else ("📍" if not df_s.empty and d_str in df_s.iloc[:, 0].astype(str).values else "")
                html += f'<a href="/?d={d_str}" target="_self" class="cal-box date-box {is_sel} {c_cls}"><span class="day-text">{day}</span><span class="mark-text">{mark}</span></a>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    sel = st.session_state.selected_date
    st.subheader(f"📅 {sel.strftime('%m/%d')} の予定")
    if not df_s.empty:
        evs = df_s[df_s.iloc[:, 0].astype(str).str.contains(sel.strftime("%Y-%m-%d"))]
        if not evs.empty:
            for v in evs.iloc[:, 1]: st.info(f"📍 {v}")
        else: st.write("予定なし")

# 【タブ2: 持ち物/時間割】
with tabs[1]:
    sel_day_name = ["月","火","水","木","金","土","日"][st.session_state.selected_date.weekday()]
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
                items = BELONGINGS.get(sub, ["（持ち物データなし）"])
                for item in items:
                    st.write(f"✅ {item}")
    else:
        st.write("休みの日です。")
    
    st.divider()
    st.caption("💡 補足事項: 化学基礎・数A等は単元に合わせて持参すること。")

# 【タブ3: 登録】
with tabs[2]:
    st.subheader("📝 登録・予定管理")
    
    # 1. 登録先を選択
    mode = st.radio("何を登録しますか？", ["📅 予定（行事・メモ）", "✍️ 課題（提出物）"], horizontal=True)
    
    # 2. 日付の確認（現在選択中の日付を強調）
    sel = st.session_state.selected_date
    st.info(f"選択中の日付: **{sel.strftime('%Y/%m/%d')}**")
    st.caption("※日付を変えたい場合は「カレンダー」タブで日付をタップしてからここに戻ってください。")

    if mode == "📅 予定（行事・メモ）":
        with st.form("event_form"):
            content = st.text_input("予定の内容（例：英単語テスト、部活休み）")
            submitted = st.form_submit_button("この日に予定を保存")
            if submitted:
                if content:
                    requests.post(f"{gas_url}?sheet=schedules", json=[sel.strftime("%Y-%m-%d"), content])
                    st.success(f"{sel.month}/{sel.day} に「{content}」を登録しました！")
                else:
                    st.error("内容を入力してください")

    else:
        with st.form("task_form"):
            # 教科選択（PC版のリストを使用）
            sub = st.selectbox("教科を選択", list(BELONGINGS.keys()))
            msg = st.text_input("課題の内容（例：ワーク P10-15、プリント提出）")
            
            # 期限のヒント
            st.write(f"🚩 提出期限: **{sel.strftime('%m/%d')}**")
            
            submitted = st.form_submit_button("課題リストに追加")
            if submitted:
                if msg:
                    requests.post(f"{gas_url}?sheet=tasks", json=[sub, msg, sel.strftime("%Y-%m-%d"), "FALSE"])
                    st.success(f"{sub} の課題「{msg}」を登録しました！")
                else:
                    st.error("内容を入力してください")

    # 3. 予定のプレビュー（入力ミス防止）
    st.divider()
    st.write("📖 **この日の現在の状況:**")
    today_evs = df_s[df_s.iloc[:, 0].astype(str).str.contains(sel.strftime("%Y-%m-%d"))] if not df_s.empty else pd.DataFrame()
    if not today_evs.empty:
        for v in today_evs.iloc[:, 1]:
            st.caption(f"・ {v}")
    else:
        st.caption("予定はありません。")
