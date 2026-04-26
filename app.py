import streamlit as st
import pandas as pd
from scorer import rank_horses, find_anaba
from advisor import advise
from scraper import fetch_race_data

st.set_page_config(page_title="競馬予想ツール", page_icon="🏇", layout="wide")

st.title("🏇 競馬予想ツール")
st.caption("G1レース専用 ｜ 前走成績はG1/G2/G3のみ参照")

# --- サイドバー：設定 ---
with st.sidebar:
    st.header("⚙️ 設定")
    num_horses = st.number_input("出走頭数", min_value=2, max_value=18, value=8, step=1)
    budget = st.number_input("予算（円）", min_value=500, max_value=100000, value=3000, step=500)
    st.markdown("---")
    st.markdown("**スコア基準（合計最大120点）**")
    st.markdown(
        "- オッズ：20点\n"
        "- 前走着順：15点\n"
        "- 直近3走平均：20点\n"
        "- 上がり3F：15点\n"
        "- 騎手勝率：15点\n"
        "- 距離・コース・馬場適性：10点\n"
        "- 調教評価：5点\n"
        "- 馬体重変動：10点\n"
        "- 枠番：10点"
    )

# --- netkeiba URL 自動取得 ---
st.header("① netkeiba出馬表から自動取得（任意）")
st.caption("netkeibaの出馬表URLを貼るとデータを自動入力します。例: https://race.netkeiba.com/race/shutuba.html?race_id=XXXXXXXXXX")

col_url, col_past, col_btn = st.columns([4, 2, 1])
race_url = col_url.text_input("出馬表URL", placeholder="https://race.netkeiba.com/race/shutuba.html?race_id=...", label_visibility="collapsed")
fetch_past = col_past.checkbox("詳細データ取得（+1〜2分）", value=True)

if col_btn.button("🔄 取得", use_container_width=True):
    if not race_url.strip():
        st.warning("URLを入力してください。")
    else:
        msg = "データ取得中...（上がり3F・騎手勝率・適性・調教を並行取得中）" if fetch_past else "データ取得中..."
        with st.spinner(msg):
            try:
                scraped = fetch_race_data(race_url.strip(), fetch_past_races=fetch_past)
                st.session_state["scraped_horses"] = scraped
                st.session_state["num_horses"] = len(scraped)
                for i, h in enumerate(scraped):
                    st.session_state[f"num_{i}"] = h["number"]
                    st.session_state[f"name_{i}"] = h["name"]
                    st.session_state[f"odds_{i}"] = float(h["odds"])
                    st.session_state[f"ninki_{i}"] = h.get("ninki", 0)
                    st.session_state[f"jockey_{i}"] = h["jockey"]
                    st.session_state[f"place_{i}"] = h["last_place"]
                    recent3 = h.get("recent3", [5, 5, 5])
                    st.session_state[f"place2_{i}"] = recent3[1] if len(recent3) > 1 else 5
                    st.session_state[f"place3_{i}"] = recent3[0] if len(recent3) > 0 else 5
                    st.session_state[f"weight_{i}"] = h["weight_change"]
                    st.session_state[f"gate_{i}"] = min(h["gate"], 8)
                    # 新規フィールド（フォームには表示しないがスコアに使用）
                    st.session_state[f"agari3f_{i}"] = h.get("agari3f_avg")
                    st.session_state[f"jockey_wr_{i}"] = h.get("jockey_win_rate", 0.10)
                    st.session_state[f"jockey_fr_{i}"] = h.get("jockey_fukusho_rate", 0.30)
                    st.session_state[f"dist_fit_{i}"] = h.get("distance_fit", 0.5)
                    st.session_state[f"training_{i}"] = h.get("training", "B")
                st.success(f"{len(scraped)}頭のデータを取得しました。")
            except Exception as e:
                st.error(f"取得失敗: {e}")

scraped = st.session_state.get("scraped_horses", [])

# --- 馬情報入力 ---
st.header("② 馬の情報を確認・修正")

n = len(scraped) if scraped else int(num_horses)

horses = []
cols_header = st.columns([1, 2, 1, 2, 2, 1, 1, 1, 2, 2])
cols_header[0].markdown("**馬番**")
cols_header[1].markdown("**馬名**")
cols_header[2].markdown("**人気**")
cols_header[3].markdown("**単勝オッズ**")
cols_header[4].markdown("**騎手名**")
cols_header[5].markdown("**前走**")
cols_header[6].markdown("**前々走**")
cols_header[7].markdown("**3走前**")
cols_header[8].markdown("**体重増減(kg)**")
cols_header[9].markdown("**枠番**")

for i in range(n):
    d = scraped[i] if i < len(scraped) else {}
    cols = st.columns([1, 2, 1, 2, 2, 1, 1, 1, 2, 2])

    number = cols[0].number_input("", min_value=1, max_value=18, value=d.get("number", i+1), key=f"num_{i}", label_visibility="collapsed")
    name = cols[1].text_input("", value=d.get("name", f"馬{i+1}"), key=f"name_{i}", label_visibility="collapsed")
    ninki = cols[2].number_input("", min_value=0, max_value=18, value=d.get("ninki", 0), key=f"ninki_{i}", label_visibility="collapsed")
    odds = cols[3].number_input("", min_value=1.0, max_value=999.9, value=float(d.get("odds", 10.0)), step=0.1, key=f"odds_{i}", label_visibility="collapsed")
    jockey = cols[4].text_input("", value=d.get("jockey", ""), key=f"jockey_{i}", label_visibility="collapsed")
    last_place = cols[5].number_input("", min_value=1, max_value=18, value=d.get("last_place", 5), key=f"place_{i}", label_visibility="collapsed")
    recent3 = d.get("recent3", [5, 5, 5])
    place2 = cols[6].number_input("", min_value=1, max_value=18, value=recent3[1] if len(recent3) > 1 else 5, key=f"place2_{i}", label_visibility="collapsed")
    place3 = cols[7].number_input("", min_value=1, max_value=18, value=recent3[0] if len(recent3) > 0 else 5, key=f"place3_{i}", label_visibility="collapsed")
    weight_change = cols[8].number_input("", min_value=-20, max_value=20, value=d.get("weight_change", 0), key=f"weight_{i}", label_visibility="collapsed")
    gate = cols[9].number_input("", min_value=1, max_value=8, value=min(d.get("gate", i+1), 8), key=f"gate_{i}", label_visibility="collapsed")

    horses.append({
        "number": number,
        "name": name,
        "ninki": ninki,
        "odds": odds,
        "jockey": jockey,
        "last_place": last_place,
        "recent3": [place3, place2, last_place],
        "weight_change": weight_change,
        "gate": gate,
        # 詳細スコアデータ（スクレイプ時のみ有効）
        "agari3f_avg": st.session_state.get(f"agari3f_{i}"),
        "jockey_win_rate": st.session_state.get(f"jockey_wr_{i}", 0.10),
        "jockey_fukusho_rate": st.session_state.get(f"jockey_fr_{i}", 0.30),
        "distance_fit": st.session_state.get(f"dist_fit_{i}", 0.5),
        "training": st.session_state.get(f"training_{i}", "B"),
    })

# --- 予想実行 ---
if st.button("🔍 予想する", type="primary", use_container_width=True):
    ranked = rank_horses(horses)
    anaba = find_anaba(ranked)

    st.header("③ スコアランキング")
    df = pd.DataFrame([
        {
            "順位\n(地力)": i+1,
            "馬番": h["number"],
            "馬名": h["name"],
            "人気": f"{h['ninki']}番人気" if h.get("ninki") else "-",
            "騎手": h["jockey"],
            "オッズ": f"{h['odds']}倍",
            "前走": f"{h['last_place']}着",
            "上がり3F": f"{h['agari3f_avg']:.1f}" if h.get("agari3f_avg") is not None else "-",
            "騎手勝率": f"{h['jockey_win_rate']:.0%}" if h.get("jockey_win_rate") else "-",
            "適性": f"{h['distance_fit']:.0%}" if h.get("distance_fit") is not None else "-",
            "調教": h.get("training", "-"),
            "体重増減": f"{h['weight_change']:+d}kg",
            "枠番": h["gate"],
            "地力スコア": h["score"],
            "期待値指数": h.get("ev", "-"),
        }
        for i, h in enumerate(ranked)
    ])

    def highlight_top3(row):
        colors = [
            "background-color: #FFD700; color: #000000; font-weight: bold",
            "background-color: #A8A8A8; color: #000000; font-weight: bold",
            "background-color: #8B4513; color: #FFFFFF; font-weight: bold",
        ]
        idx = row.name
        if idx < 3:
            return [colors[idx]] * len(row)
        return [""] * len(row)

    st.dataframe(df.style.apply(highlight_top3, axis=1), use_container_width=True, hide_index=True)

    # 期待値ランキング
    st.header("③-A 期待値ランキング（地力 × オッズ）")
    st.caption("地力スコアが高いのにオッズが高い馬＝市場が見落としている馬")
    ev_sorted = sorted(ranked, key=lambda h: h.get("ev", 0), reverse=True)[:5]
    df_ev = pd.DataFrame([
        {
            "馬番": h["number"],
            "馬名": h["name"],
            "人気": f"{h.get('ninki', '?')}番人気",
            "オッズ": f"{h['odds']}倍",
            "地力スコア": h["score"],
            "期待値指数": h.get("ev", "-"),
        }
        for h in ev_sorted
    ])
    st.dataframe(df_ev, use_container_width=True, hide_index=True)
    st.caption("💡 期待値指数が高い馬は「実力の割に買われていない馬」。穴馬候補と重なれば特に注目。")

    # 穴馬候補
    if anaba:
        st.header("③-B 穴馬候補")
        st.caption("4〜9人気の中で前走成績・上がり・騎手実績から選出")
        df_anaba = pd.DataFrame([
            {
                "馬番": h["number"],
                "馬名": h["name"],
                "人気": f"{h.get('ninki', '?')}番人気",
                "オッズ": f"{h['odds']}倍",
                "騎手": h["jockey"],
                "前走": f"{h['last_place']}着",
                "上がり3F": f"{h['agari3f_avg']:.1f}" if h.get("agari3f_avg") else "-",
                "スコア": h["score"],
            }
            for h in anaba
        ])
        st.dataframe(df_anaba, use_container_width=True, hide_index=True)

    st.header("④ 馬券の買い目")
    advice = advise(ranked, budget, anaba)

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

    st.header("⑤ コピペ用買い目まとめ")
    lines = [f"【{t}】{v['買い目']} {v['金額']:,}円" for t, v in advice.items()]
    st.code("\n".join(lines), language=None)
