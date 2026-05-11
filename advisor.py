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

    # 穴馬三連複（複数パターン）
    if anaba and top and second:
        amount = int(budget * 0.05 / 100) * 100
        bought = set()
        count = 0
        for ana in anaba[:2]:
            for base_a, base_b in [(top, second), (top, third), (second, third)]:
                if base_a is None or base_b is None:
                    continue
                nums_set = tuple(sorted({base_a["number"], base_b["number"], ana["number"]}))
                if len(nums_set) == 3 and nums_set not in bought:
                    bought.add(nums_set)
                    nums_str = "-".join(str(n) for n in nums_set)
                    key = "三連複（穴馬込み）" if count == 0 else f"三連複（穴馬込み）{count + 1}"
                    result[key] = {
                        "買い目": f"{nums_str}（穴：{ana['number']}番 {ana['name']}）",
                        "金額": amount,
                        "理由": f"{ana['name']}（{ana.get('ninki', '?')}人気）を穴馬として組み込んだ高配当狙い",
                    }
                    count += 1
                    if count >= 3:
                        break
            if count >= 3:
                break

    return result
