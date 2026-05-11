ELITE_JOCKEYS = {
    "武豊":   8,
    "川田":   7,
    "ルメール": 7,
    "デムーロ": 6,
    "横山武":  5,
    "戸崎":   5,
    "坂井":   5,
    "松山":   4,
    "北村友":  4,
    "三浦":   4,
    "岩田康":  4,
    "池添":   3,
    "福永":   5,
    "田辺":   3,
    "レーン":  6,
    "モレイラ": 7,
    "シュタル": 5,
}


def score_ninki(ninki: int) -> int:
    if ninki == 0:
        return 2
    if ninki == 1:
        return 8
    elif ninki == 2:
        return 6
    elif ninki == 3:
        return 4
    elif ninki <= 5:
        return 3
    else:
        return 1


def score_odds(odds: float) -> int:
    if odds <= 2.9:
        return 20
    elif odds <= 3.9:
        return 17
    elif odds <= 5:
        return 14
    elif odds <= 10:
        return 15
    elif odds <= 20:
        return 8
    else:
        return 3


def score_last_place(place: int) -> int:
    if place == 1:
        return 6
    elif place == 2:
        return 5
    elif place == 3:
        return 4
    elif place <= 5:
        return 3
    elif place <= 8:
        return 2
    else:
        return 1  # 9着以下も1点（大差をつけない）


def score_recent3(places: list[int]) -> int:
    if not places:
        return 0
    avg = sum(places) / len(places)
    if avg <= 2:
        return 12
    elif avg <= 4:
        return 10
    elif avg <= 6:
        return 7
    elif avg <= 9:
        return 4
    else:
        return 1


def score_trend(recent3: list[int]) -> int:
    """着順のトレンド（改善傾向＝プラス、悪化傾向＝マイナス）"""
    if len(recent3) < 2:
        return 0
    # recent3 = [3走前, 2走前, 前走]
    first = recent3[0]
    last = recent3[-1]
    if last < first - 2:   # 明確に改善
        return 4
    elif last < first:     # やや改善
        return 2
    elif last > first + 2: # 明確に悪化
        return -2
    return 0


def score_weight_change(change: int) -> int:
    abs_change = abs(change)
    if abs_change <= 2:
        return 10
    elif abs_change <= 4:
        return 6
    else:
        return 2


def score_gate(gate: int) -> int:
    if 3 <= gate <= 6:
        return 10
    elif gate in (2, 7):
        return 7
    else:
        return 3


def score_agari3f(agari3f_avg) -> int:
    if agari3f_avg is None:
        return 8
    if agari3f_avg <= 33.0:
        return 15
    elif agari3f_avg <= 33.9:
        return 12
    elif agari3f_avg <= 34.9:
        return 8
    elif agari3f_avg <= 36.0:
        return 4
    else:
        return 1


def score_jockey(win_rate: float, jockey_name: str = "") -> int:
    base = 0
    if win_rate >= 0.20:
        base = 15
    elif win_rate >= 0.15:
        base = 12
    elif win_rate >= 0.10:
        base = 8
    elif win_rate >= 0.06:
        base = 4
    else:
        base = 1

    # 大舞台補正
    for name, bonus in ELITE_JOCKEYS.items():
        if name in jockey_name:
            base += bonus
            break

    return base


def score_distance_fit(fit: float) -> int:
    if fit >= 0.80:
        return 10
    elif fit >= 0.60:
        return 7
    elif fit >= 0.40:
        return 4
    else:
        return 1


def score_training(training: str) -> int:
    t = training.upper()
    if any(k in t for k in ["A", "◎", "素晴", "抜群", "絶好"]):
        return 5
    elif any(k in t for k in ["B", "○", "良好", "好調"]):
        return 3
    else:
        return 1


def calc_score(horse: dict) -> int:
    """地力スコア（人気を軽く加味した総合評価）"""
    recent3 = horse.get("recent3", [])
    return (
        score_last_place(horse["last_place"])
        + score_recent3(recent3)
        + score_trend(recent3)
        + score_weight_change(horse["weight_change"])
        + score_gate(horse["gate"])
        + score_agari3f(horse.get("agari3f_avg"))
        + score_jockey(horse.get("jockey_win_rate", 0.10), horse.get("jockey", ""))
        + score_distance_fit(horse.get("distance_fit", 0.5))
        + score_training(horse.get("training", "B"))
        + score_ninki(horse.get("ninki", 0))
    )


def calc_ev(horse: dict) -> float:
    """期待値指数 = 地力スコア × オッズ ÷ 10（高いほど市場が見落としている）"""
    return round(horse["score"] * horse["odds"] / 10, 1)


def find_anaba(horses: list[dict]) -> list[dict]:
    """4〜9人気で前走成績・上がりが良い穴馬候補を返す"""
    candidates = []
    for h in horses:
        ninki = h.get("ninki", 0)
        if ninki == 0 or not (4 <= ninki <= 9):
            continue
        recent3 = h.get("recent3", [5, 5, 5])
        avg = sum(recent3) / len(recent3) if recent3 else 5
        agari = h.get("agari3f_avg")
        jockey = h.get("jockey", "")
        is_elite = any(name in jockey for name in ELITE_JOCKEYS)

        # 条件：直近3走平均5着以内 or 上がり34.5以下 or エリート騎手
        if avg <= 5 or (agari is not None and agari <= 34.5) or is_elite:
            candidates.append(h)

    return sorted(candidates, key=lambda h: h.get("score", 0), reverse=True)[:3]


def rank_horses(horses: list[dict]) -> list[dict]:
    for h in horses:
        h["score"] = calc_score(h)
        h["ev"] = calc_ev(h)
    return sorted(horses, key=lambda h: h["score"], reverse=True)
