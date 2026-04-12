import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os

# --- ページ設定 ---
st.set_page_config(page_title="カレンダーなど", layout="centered")

# パスワード設定
if "MY_PASSWORD" in st.secrets:
    correct_pw = st.secrets["MY_PASSWORD"]
else:
    st.error("管理画面でパスワードを設定してください")
    st.stop()

# ログイン画面の表示
pw = st.sidebar.text_input("パスワードを入力", type="password")

if pw != correct_pw:
    st.info("左のメニューからパスワードを入力してください。")
    st.stop()  # パスワードが違う間は、ここでプログラムを止める

# --- データ読み込み用関数 ---
def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# データの読み込み
# ※PC版と同じフォルダで動かせば、同じデータを読み書きできます
schedules_raw = load_json("schedules.json", {})
tasks = load_json("tasks.json", [])
# 時間割はPC版のDEFAULT_TIMETABLEをベースに設定
timetable = {
    "月": ["科技β", "数基α", "家庭", "地総", "科技α", "言語文化", "論表"],
    "火": ["科技α", "音楽", "歴総", "体育", "数基α", "言語文化"],
    "水": ["保健", "探求基礎", "論表", "数基β", "現国", "コミュ I"],
    "木": ["科技β", "コミュ I", "言語文化", "家庭", "音楽", "数基α", "LT"],
    "金": ["地総", "体育", "数基β", "現国", "SP I", "歴総"],
}

# --- アプリのデザイン ---
st.title("カレンダーなど")

# タブ機能で切り替え（スマホで操作しやすい）
tab1, tab2, tab3 = st.tabs(["予定", "時間割", "課題"])

# --- タブ1: カレンダー・予定 ---
with tab1:
    st.subheader("予定の確認・追加")
    selected_date = st.date_input("日付を選択", datetime.now())
    # 前回の修正通り、Windows対応の形式
    date_str = f"{selected_date.year}-{selected_date.month}-{selected_date.day}"
    
    # その日の予定を表示
    day_events = schedules_raw.get(date_str, [])
    
    if day_events:
        st.write(f"📅 {date_str} の予定:")
        # 予定を1つずつループして表示
        for idx, ev in enumerate(day_events):
            col1, col2 = st.columns([4, 1])
            col1.info(f"📌 {ev}")
            # 削除ボタン
            if col2.button("🗑️", key=f"del_ev_{date_str}_{idx}"):
                day_events.pop(idx) # リストから削除
                if not day_events:
                    schedules_raw.pop(date_str) # 予定が0になったら日付ごと消す
                else:
                    schedules_raw[date_str] = day_events
                
                save_json("schedules.json", schedules_raw) # 保存
                st.rerun() # 画面を更新
    else:
        st.write("予定はありません")

    # 予定の追加フォーム
    with st.expander("＋ 新しい予定を追加"):
        new_event = st.text_input("予定名", key="new_event_input")
        if st.button("予定を保存"):
            if new_event:
                if date_str not in schedules_raw:
                    schedules_raw[date_str] = []
                schedules_raw[date_str].append(new_event)
                save_json("schedules.json", schedules_raw)
                st.success("保存しました！")
                st.rerun()
                
# --- タブ2: 時間割 ---
with tab2:
    st.subheader("週間時間割")
    day_opt = st.selectbox("曜日を選択", ["月", "火", "水", "木", "金"])
    
    # リスト形式で表示（スマホで見やすい）
    day_subjects = timetable.get(day_opt, [])
    for i, sub in enumerate(day_subjects):
        with st.container():
            col1, col2 = st.columns([1, 4])
            col1.button(f"{i+1}", key=f"p_{day_opt}_{i}", disabled=True)
            col2.write(f"**{sub}**")

# --- タブ3: 課題管理 ---
with tab3:
    st.subheader("課題の管理")
    
    # --- 新規課題追加フォーム ---
    with st.expander("➕ 新しい課題を追加"):
        with st.form("add_task_form"):
            t_subject = st.selectbox("教科", ["科技β", "数基α", "英語", "現国", "地総", "その他"])
            t_name = st.text_input("課題の内容（例：ワークP.20まで）")
            t_date = st.date_input("期限", datetime.now())
            submit_task = st.form_submit_button("課題を登録")
            
            if submit_task and t_name:
                new_task = {
                    "subject": t_subject,
                    "name": t_name,
                    "date": t_date.strftime("%Y-%m-%d"),
                    "completed": False
                }
                tasks.append(new_task)
                save_json("tasks.json", tasks)
                st.success("課題を追加しました！")
                st.rerun()

    st.divider() # 区切り線

    # --- 課題一覧表示 ---
    st.write("未完了の課題一覧")
    if not tasks:
        st.info("現在、未完了の課題はありません。")
    else:
        # 期限が近い順に並び替え
        sorted_tasks = sorted(tasks, key=lambda x: x['date'])
        
        for i, task in enumerate(sorted_tasks):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**【{task['subject']}】**")
                st.write(f"{task['name']} (期限: {task['date']})")
            
            if col2.button("完了", key=f"done_{i}"):
                # 一致する課題を元のリストから削除
                tasks.remove(task)
                save_json("tasks.json", tasks)
                st.toast(f"{task['name']} を完了しました！")
                st.rerun()
