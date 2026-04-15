def score_odds(odds: float) -> int:
    if odds <= 5:
        return 25
    elif odds <= 10:
        return 18
    elif odds <= 20:
        return 10
    else:
        return 4


def score_last_place(place: int) -> int:
    if place == 1:
        return 20
    elif place == 2:
        return 16
    elif place == 3:
        return 12
    elif place <= 5:
        return 7
    else:
        return 2


def score_recent3(places: list[int]) -> int:
    """直近3走の着順リスト（古い順）からスコアを算出"""
    if not places:
        return 0
    avg = sum(places) / len(places)
    if avg <= 2:
        return 25
    elif avg <= 4:
        return 20
    elif avg <= 6:
        return 13
    elif avg <= 9:
        return 7
    else:
        return 2


def score_weight_change(change: int) -> int:
    abs_change = abs(change)
    if abs_change <= 2:
        return 15
    elif abs_change <= 4:
        return 9
    else:
        return 3


def score_gate(gate: int) -> int:
    if 3 <= gate <= 6:
        return 15
    elif gate in (2, 7):
        return 10
    else:
        return 5


def calc_score(horse: dict) -> int:
    return (
        score_odds(horse["odds"])
        + score_last_place(horse["last_place"])
        + score_recent3(horse.get("recent3", []))
        + score_weight_change(horse["weight_change"])
        + score_gate(horse["gate"])
    )


def rank_horses(horses: list[dict]) -> list[dict]:
    for h in horses:
        h["score"] = calc_score(h)
    return sorted(horses, key=lambda h: h["score"], reverse=True)
