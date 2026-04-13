# 通信テスト用（画面に出ます）
if not gas_url:
    st.error("GAS_URLが設定されていません！")
else:
    try:
        test_res = requests.get(f"{gas_url}?sheet=schedules")
        if test_res.status_code == 200:
            st.success("GASとの通信に成功しました！")
        else:
            st.error(f"GASと通信はできましたが、エラーが返ってきました: {test_res.status_code}")
    except:
        st.error("GASにアクセスできません。URLが間違っているか、公開設定が『全員』になっていません。")
