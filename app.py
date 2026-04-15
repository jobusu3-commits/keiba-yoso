import streamlit as st
import pandas as pd
from scorer import rank_horses
from advisor import advise

st.set_page_config(page_title="競馬予想ツール", page_icon="🏇", layout="wide")

st.title("🏇 競馬予想ツール")
st.caption("馬の情報を入力してスコアリング＆買い目を自動生成")

# --- サイドバー：設定 ---
with st.sidebar:
    st.header("⚙️ 設定")
    num_horses = st.number_input("出走頭数", min_value=2, max_value=18, value=8, step=1)
    budget = st.number_input("予算（円）", min_value=500, max_value=100000, value=3000, step=500)
    st.markdown("---")
    st.markdown("**スコア基準（合計100点）**")
    st.markdown("- オッズ：25点\n- 前走着順：20点\n- 直近3走平均：25点\n- 馬体重変動：15点\n- 枠番：15点")

# --- 馬情報入力 ---
st.header("① 馬の情報を入力")

horses = []
cols_header = st.columns([1, 2, 2, 2, 1, 1, 1, 2, 2])
cols_header[0].markdown("**馬番**")
cols_header[1].markdown("**馬名**")
cols_header[2].markdown("**単勝オッズ**")
cols_header[3].markdown("**騎手名**")
cols_header[4].markdown("**前走**")
cols_header[5].markdown("**前々走**")
cols_header[6].markdown("**3走前**")
cols_header[7].markdown("**体重増減(kg)**")
cols_header[8].markdown("**枠番**")

for i in range(int(num_horses)):
    cols = st.columns([1, 2, 2, 2, 1, 1, 1, 2, 2])
    number = cols[0].number_input("", min_value=1, max_value=18, value=i+1, key=f"num_{i}", label_visibility="collapsed")
    name = cols[1].text_input("", value=f"馬{i+1}", key=f"name_{i}", label_visibility="collapsed")
    odds = cols[2].number_input("", min_value=1.0, max_value=999.9, value=10.0, step=0.1, key=f"odds_{i}", label_visibility="collapsed")
    jockey = cols[3].text_input("", value="", key=f"jockey_{i}", label_visibility="collapsed")
    last_place = cols[4].number_input("", min_value=1, max_value=18, value=5, key=f"place_{i}", label_visibility="collapsed")
    place2 = cols[5].number_input("", min_value=1, max_value=18, value=5, key=f"place2_{i}", label_visibility="collapsed")
    place3 = cols[6].number_input("", min_value=1, max_value=18, value=5, key=f"place3_{i}", label_visibility="collapsed")
    weight_change = cols[7].number_input("", min_value=-20, max_value=20, value=0, key=f"weight_{i}", label_visibility="collapsed")
    gate = cols[8].number_input("", min_value=1, max_value=8, value=min(i+1, 8), key=f"gate_{i}", label_visibility="collapsed")

    horses.append({
        "number": number,
        "name": name,
        "odds": odds,
        "jockey": jockey,
        "last_place": last_place,
        "recent3": [place3, place2, last_place],
        "weight_change": weight_change,
        "gate": gate,
    })

# --- 予想実行 ---
if st.button("🔍 予想する", type="primary", use_container_width=True):
    ranked = rank_horses(horses)

    # スコア表示
    st.header("② スコアランキング")
    df = pd.DataFrame([
        {
            "順位": i+1,
            "馬番": h["number"],
            "馬名": h["name"],
            "騎手": h["jockey"],
            "オッズ": f"{h['odds']}倍",
            "前走": f"{h['last_place']}着",
            "体重増減": f"{h['weight_change']:+d}kg",
            "枠番": h["gate"],
            "スコア": h["score"],
        }
        for i, h in enumerate(ranked)
    ])

    def highlight_top3(row):
        colors = ["background-color: #FFD700", "background-color: #C0C0C0", "background-color: #CD7F32"]
        idx = row.name
        if idx < 3:
            return [colors[idx]] * len(row)
        return [""] * len(row)

    st.dataframe(df.style.apply(highlight_top3, axis=1), use_container_width=True, hide_index=True)

    # 馬券アドバイス
    st.header("③ 馬券の買い目")
    advice = advise(ranked, budget)

    if not advice:
        st.warning("スコアが低くて推奨できる馬券がありません。")
    else:
        total = 0
        for ticket_type, info in advice.items():
            with st.container():
                c1, c2, c3 = st.columns([2, 3, 4])
                c1.markdown(f"### {ticket_type}")
                c2.markdown(f"**{info['買い目']}**")
                c3.markdown(f"💰 {info['金額']:,}円｜{info['理由']}")
                total += info["金額"]
            st.divider()

        st.markdown(f"**合計投資額：{total:,}円 / 予算：{budget:,}円**")
        if total > budget:
            st.warning(f"⚠️ 合計が予算を{total - budget:,}円超えています。金額を調整してください。")

    # コピペ用テキスト
    st.header("④ コピペ用買い目まとめ")
    lines = [f"【{t}】{v['買い目']} {v['金額']:,}円" for t, v in advice.items()]
    st.code("\n".join(lines), language=None)
