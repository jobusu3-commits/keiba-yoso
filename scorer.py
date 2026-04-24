def score_ninki(ninki: int) -> int:
    """人気順位（1が最高）"""
    if ninki == 0:
        return 3
    if ninki == 1:
        return 10
    elif ninki == 2:
        return 5
    elif ninki == 3:
        return 6
    elif ninki <= 5:
        return 4
    else:
        return 2


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
        return 10
    elif place == 2:
        return 8
    elif place == 3:
        return 6
    elif place <= 5:
        return 3
    else:
        return 1


def score_recent3(places: list[int]) -> int:
    if not places:
        return 0
    avg = sum(places) / len(places)
    if avg <= 2:
        return 20
    elif avg <= 4:
        return 16
    elif avg <= 6:
        return 10
    elif avg <= 9:
        return 5
    else:
        return 1


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
    """上がり3F平均（秒）。低いほど速い"""
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


def score_jockey(win_rate: float) -> int:
    """騎手勝率（0〜1）"""
    if win_rate >= 0.20:
        return 15
    elif win_rate >= 0.15:
        return 12
    elif win_rate >= 0.10:
        return 8
    elif win_rate >= 0.06:
        return 4
    else:
        return 1


def score_distance_fit(fit: float) -> int:
    """距離・コース・馬場の総合適性（0〜1）"""
    if fit >= 0.80:
        return 10
    elif fit >= 0.60:
        return 7
    elif fit >= 0.40:
        return 4
    else:
        return 1


def score_training(training: str) -> int:
    """調教評価文字列からスコア"""
    t = training.upper()
    if any(k in t for k in ["A", "◎", "素晴", "抜群", "絶好"]):
        return 5
    elif any(k in t for k in ["B", "○", "良好", "好調"]):
        return 3
    else:
        return 1


def calc_score(horse: dict) -> int:
    return (
        score_ninki(horse.get("ninki", 0))
        + score_odds(horse["odds"])
        + score_last_place(horse["last_place"])
        + score_recent3(horse.get("recent3", []))
        + score_weight_change(horse["weight_change"])
        + score_gate(horse["gate"])
        + score_agari3f(horse.get("agari3f_avg"))
        + score_jockey(horse.get("jockey_win_rate", 0.10))
        + score_distance_fit(horse.get("distance_fit", 0.5))
        + score_training(horse.get("training", "B"))
    )


def rank_horses(horses: list[dict]) -> list[dict]:
    for h in horses:
        h["score"] = calc_score(h)
    return sorted(horses, key=lambda h: h["score"], reverse=True)
