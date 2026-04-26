def advise(ranked: list[dict], budget: int, anaba: list[dict] = None) -> dict:
    result = {}
    top = ranked[0] if len(ranked) >= 1 else None
    second = ranked[1] if len(ranked) >= 2 else None
    third = ranked[2] if len(ranked) >= 3 else None

    # 単勝
    if top and top["score"] >= 85:
        amount = int(budget * 0.4 / 100) * 100
        result["単勝"] = {
            "買い目": f"{top['number']}番 {top['name']}",
            "金額": amount,
            "理由": f"スコア{top['score']}点（最高）。オッズ{top['odds']}倍",
        }

    # 複勝
    fukusho = [h for h in ranked[:2] if h["score"] >= 65]
    if fukusho:
        amount = int(budget * 0.3 / 100) * 100
        targets = "・".join([f"{h['number']}番 {h['name']}" for h in fukusho])
        result["複勝"] = {
            "買い目": targets,
            "金額": amount,
            "理由": f"スコア上位{len(fukusho)}頭。安定的な回収を狙う",
        }

    # 馬連・馬単
    if top and second:
        amount = int(budget * 0.1 / 100) * 100
        result["馬連"] = {
            "買い目": f"{top['number']}番-{second['number']}番",
            "金額": amount,
            "理由": "スコア1位×2位の組み合わせ",
        }
        result["馬単"] = {
            "買い目": f"{top['number']}番→{second['number']}番",
            "金額": amount,
            "理由": f"{top['name']}が1着、{second['name']}が2着を予想",
        }

    # 三連複（通常）
    if top and second and third:
        amount = int(budget * 0.05 / 100) * 100
        nums = f"{top['number']}-{second['number']}-{third['number']}"
        result["三連複"] = {
            "買い目": nums,
            "金額": amount,
            "理由": "スコア上位3頭のボックス",
        }
        result["三連単"] = {
            "買い目": f"{top['number']}→{second['number']}→{third['number']}",
            "金額": amount,
            "理由": "スコア順に1・2・3着を予想（高配当狙い）",
        }

    # 穴馬三連複（穴馬がいる場合）
    if anaba and top and second:
        for ana in anaba[:1]:
            nums_set = sorted({top["number"], second["number"], ana["number"]})
            if len(nums_set) == 3:
                amount = int(budget * 0.05 / 100) * 100
                nums_str = "-".join(str(n) for n in nums_set)
                result["三連複（穴馬込み）"] = {
                    "買い目": f"{nums_str}（穴：{ana['number']}番 {ana['name']}）",
                    "金額": amount,
                    "理由": f"{ana['name']}（{ana.get('ninki', '?')}人気）を穴馬として組み込んだ高配当狙い",
                }

    return result
