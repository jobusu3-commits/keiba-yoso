import re
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.netkeiba.com/",
}
DB_HEADERS = {**HEADERS, "Referer": "https://db.netkeiba.com/"}

# 主要騎手の実績勝率（スクレイピング失敗時のフォールバック）
JOCKEY_KNOWN_RATES = {
    "武豊":   (0.22, 0.45),
    "川田":   (0.23, 0.48),
    "ルメール": (0.28, 0.52),
    "デムーロ": (0.18, 0.42),
    "横山武":  (0.17, 0.40),
    "戸崎":   (0.16, 0.38),
    "坂井":   (0.18, 0.40),
    "松山":   (0.15, 0.38),
    "北村友":  (0.14, 0.35),
    "三浦":   (0.12, 0.32),
    "岩田康":  (0.13, 0.33),
    "岩田望":  (0.13, 0.33),
    "池添":   (0.12, 0.31),
    "田辺":   (0.11, 0.30),
    "西村淳":  (0.12, 0.31),
    "横山典":  (0.10, 0.28),
    "レーン":  (0.20, 0.43),
    "モレイラ": (0.25, 0.50),
    "北村宏":  (0.10, 0.28),
    "丹内":   (0.09, 0.26),
}


def _extract_race_id(url: str) -> str:
    m = re.search(r"race_id=(\d+)", url)
    if not m:
        raise ValueError("URLからrace_idが取得できません。")
    return m.group(1)


def _fetch_odds(race_id: str) -> tuple[dict, dict]:
    try:
        api_url = f"https://race.netkeiba.com/api/api_get_jra_odds.html?race_id={race_id}&type=1&action=update"
        resp = requests.get(api_url, headers=HEADERS, timeout=10)
        data = resp.json()
        odds_raw = data.get("data", {}).get("odds", {}).get("1", {})
        odds_map, ninki_map = {}, {}
        for k, v in odds_raw.items():
            num = str(int(k))
            if v and v[0] not in ("", "---.-"):
                try:
                    odds_map[num] = float(v[0])
                except ValueError:
                    pass
            if len(v) >= 3 and v[2] not in ("", "--", "**"):
                try:
                    ninki_map[num] = int(v[2])
                except ValueError:
                    pass
        return odds_map, ninki_map
    except Exception:
        return {}, {}


def _fetch_race_info(soup) -> dict:
    """現レースの距離・コース・馬場状態を取得"""
    info = {"distance": 0, "track": "芝", "condition": "良"}
    try:
        data_div = soup.find("div", class_="RaceData01")
        if data_div:
            text = data_div.get_text()
            m = re.search(r"(芝|ダ)\s*(\d+)m", text)
            if m:
                info["track"] = "芝" if m.group(1) == "芝" else "ダート"
                info["distance"] = int(m.group(2))
            for cond in ["稍重", "不良", "重", "良"]:
                if cond in text:
                    info["condition"] = cond
                    break
    except Exception:
        pass
    return info


def _fetch_past_results(race_id: str) -> dict:
    """
    shutuba_past.html から全馬の直近着順・上がり3F・距離・コース・馬場を取得。
    馬番(int) -> {recent3, agari3f, distances, tracks, conditions}
    """
    try:
        url = f"https://race.netkeiba.com/race/shutuba_past.html?race_id={race_id}&rf=shutuba_submenu"
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.encoding = "EUC-JP"
        soup = BeautifulSoup(resp.text, "html.parser")

        table = soup.find("table", class_="Shutuba_Past5_Table")
        if not table:
            return {}

        result = {}
        for row in table.find_all("tr", class_="HorseList"):
            waku_td = row.find("td", class_="Waku")
            if not waku_td:
                continue
            try:
                number = int(waku_td.get_text(strip=True))
            except ValueError:
                continue

            past_tds = row.find_all("td", class_=lambda c: c and "Past" in c)
            places, agari3f_list, distances, tracks, conditions = [], [], [], [], []

            for td in past_tds:
                td_text = td.get_text(separator=" ", strip=True)

                # GI/GII/GIII（G1/G2/G3）以外はスキップ
                if not re.search(r"GI{1,3}", td_text):
                    continue

                # 着順
                span_num = td.find("span", class_="Num")
                if span_num:
                    txt = span_num.get_text(strip=True)
                    m = re.match(r"^(\d+)$", txt)
                    places.append(int(m.group(1)) if m else 18)
                else:
                    places.append(5)

                # 距離・コース: "芝1600" "ダ1400" など
                m_dist = re.search(r"(芝|ダ)\s*(\d{3,4})", td_text)
                if m_dist:
                    tracks.append("芝" if m_dist.group(1) == "芝" else "ダート")
                    distances.append(int(m_dist.group(2)))
                else:
                    tracks.append(None)
                    distances.append(0)

                # 馬場状態
                cond = next((c for c in ["稍重", "不良", "重", "良"] if c in td_text), None)
                conditions.append(cond)

                # 上がり3F: "34.5" のような小数（30〜39秒台）
                m_agari = re.search(r"\b(3[0-9]\.\d)\b", td_text)
                agari3f_list.append(float(m_agari.group(1)) if m_agari else None)

                if len(places) >= 3:
                    break

            while len(places) < 3:
                places.append(5)
                agari3f_list.append(None)
                distances.append(0)
                tracks.append(None)
                conditions.append(None)

            result[number] = {
                "recent3": list(reversed(places[:3])),
                "agari3f": list(reversed(agari3f_list[:3])),
                "distances": list(reversed(distances[:3])),
                "tracks": list(reversed(tracks[:3])),
                "conditions": list(reversed(conditions[:3])),
            }

        return result
    except Exception:
        return {}


def _fetch_jockey_stats(jockey_id: str, jockey_name: str = "") -> dict:
    """直近成績から騎手の勝率・複勝率を計算"""
    # 既知騎手は固定値を優先
    for known, (wr, fr) in JOCKEY_KNOWN_RATES.items():
        if known in jockey_name:
            return {"win_rate": wr, "fukusho_rate": fr}

    default = {"win_rate": 0.10, "fukusho_rate": 0.30}
    try:
        url = f"https://db.netkeiba.com/jockey/result/recent/{jockey_id}/"
        resp = requests.get(url, headers=DB_HEADERS, timeout=10)
        resp.encoding = "EUC-JP"
        soup = BeautifulSoup(resp.text, "html.parser")

        positions = []
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                tds = row.find_all("td")
                if len(tds) < 9:
                    continue
                try:
                    pos = int(tds[8].get_text(strip=True))
                    positions.append(pos)
                except ValueError:
                    continue

        if not positions:
            return default

        win_rate = round(sum(1 for p in positions if p == 1) / len(positions), 3)
        fukusho_rate = round(sum(1 for p in positions if p <= 3) / len(positions), 3)
        return {"win_rate": win_rate, "fukusho_rate": fukusho_rate}
    except Exception:
        return default


def _fetch_training(race_id: str) -> dict:
    """調教評価を取得。馬番(int) -> 評価文字列"""
    try:
        url = f"https://race.netkeiba.com/race/choukyou.html?race_id={race_id}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = "EUC-JP"
        soup = BeautifulSoup(resp.text, "html.parser")

        result = {}
        for row in soup.find_all("tr", class_="HorseList"):
            umaban_td = row.find("td", class_=lambda c: c and "Umaban" in str(c))
            if not umaban_td:
                continue
            try:
                number = int(umaban_td.get_text(strip=True))
            except ValueError:
                continue

            eval_td = row.find("td", class_=lambda c: c and any(
                k in str(c) for k in ["Hyoka", "Comment", "Rank", "Choukyou"]
            ))
            result[number] = eval_td.get_text(strip=True) if eval_td else "B"

        return result
    except Exception:
        return {}


def fetch_race_data(url: str, fetch_past_races: bool = True) -> list[dict]:
    race_id = _extract_race_id(url)

    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.encoding = "EUC-JP"
    soup = BeautifulSoup(resp.text, "html.parser")

    table = soup.find("table", class_="Shutuba_Table")
    if table is None:
        raise ValueError(
            "出馬表テーブルが見つかりません。URLが出馬表ページか確認してください。\n"
            "例: https://race.netkeiba.com/race/shutuba.html?race_id=XXXXXXXXXX"
        )

    rows = table.find_all("tr", class_="HorseList")
    if not rows:
        raise ValueError("出走馬データが取得できませんでした。")

    race_info = _fetch_race_info(soup)

    # 騎手IDを事前収集
    jockey_ids = {}
    raw_rows = []
    for row in rows:
        tds = row.find_all("td")
        gate = 1
        if tds:
            try:
                gate = int(tds[0].get_text(strip=True))
            except ValueError:
                pass

        umaban_td = row.find("td", class_=lambda c: c and any("Umaban" in x for x in c))
        number = int(umaban_td.get_text(strip=True)) if umaban_td else len(raw_rows) + 1

        horse_info = row.find("td", class_="HorseInfo")
        name = f"馬{number}"
        if horse_info:
            span = horse_info.find("span", class_="HorseName")
            if span:
                a = span.find("a")
                if a:
                    name = a.get("title") or a.get_text(strip=True)
                    name = re.sub(r"\s+", "", name)

        jockey_td = row.find("td", class_="Jockey")
        jockey = ""
        if jockey_td:
            a = jockey_td.find("a")
            if a:
                jockey = a.get("title") or a.get_text(strip=True)
                href = a.get("href", "")
                m = re.search(r"/jockey/(?:result/recent/)?(\d+)/?", href)
                if m:
                    jockey_ids[jockey] = m.group(1)

        weight_change = 0
        weight_td = row.find("td", class_="Weight")
        if weight_td:
            m = re.search(r"\(([+-]?\d+)\)", weight_td.get_text())
            if m:
                weight_change = int(m.group(1))

        raw_rows.append({
            "number": number,
            "name": name,
            "jockey": jockey,
            "weight_change": weight_change,
            "gate": gate,
        })

    # 並行取得
    odds_map, ninki_map = {}, {}
    past_map, training_map, jockey_stats = {}, {}, {}

    with ThreadPoolExecutor(max_workers=10) as ex:
        future_odds = ex.submit(_fetch_odds, race_id)

        future_past = ex.submit(_fetch_past_results, race_id) if fetch_past_races else None
        future_training = ex.submit(_fetch_training, race_id) if fetch_past_races else None
        jockey_futures = {}
        if fetch_past_races:
            for name, jid in jockey_ids.items():
                jockey_futures[ex.submit(_fetch_jockey_stats, jid, name)] = name

        odds_map, ninki_map = future_odds.result()
        if future_past:
            past_map = future_past.result()
        if future_training:
            training_map = future_training.result()
        for f in as_completed(jockey_futures):
            jockey_stats[jockey_futures[f]] = f.result()

    # 最終データ組み立て
    horses = []
    for raw in raw_rows:
        number = raw["number"]
        jockey = raw["jockey"]

        odds = odds_map.get(str(number), 10.0)
        ninki = ninki_map.get(str(number), 0)

        past_data = past_map.get(number, {})
        recent3 = past_data.get("recent3", [5, 5, 5])
        last_place = recent3[-1] if recent3 else 5

        # 上がり3F平均
        agari3f_vals = [x for x in past_data.get("agari3f", []) if x is not None]
        agari3f_avg = round(sum(agari3f_vals) / len(agari3f_vals), 1) if agari3f_vals else None

        # 距離適性
        race_dist = race_info["distance"]
        past_dists = [d for d in past_data.get("distances", []) if d > 0]
        if past_dists and race_dist > 0:
            min_diff = min(abs(d - race_dist) for d in past_dists)
            distance_fit = max(0.0, 1.0 - min_diff / 800)
        else:
            distance_fit = 0.5

        # コース適性（芝/ダート）
        race_track = race_info["track"]
        past_tracks = [t for t in past_data.get("tracks", []) if t is not None]
        course_fit = (sum(1 for t in past_tracks if t == race_track) / len(past_tracks)) if past_tracks else 0.5

        # 馬場適性
        race_cond = race_info["condition"]
        past_conds = [c for c in past_data.get("conditions", []) if c is not None]
        cond_fit = (sum(1 for c in past_conds if c == race_cond) / len(past_conds)) if past_conds else 0.5

        combined_fit = round((distance_fit + course_fit + cond_fit) / 3, 2)

        # 騎手成績
        jstats = jockey_stats.get(jockey, {"win_rate": 0.10, "fukusho_rate": 0.30})

        # 調教評価
        training = training_map.get(number, "B")

        horses.append({
            "number": number,
            "name": raw["name"],
            "odds": odds,
            "ninki": ninki,
            "jockey": jockey,
            "last_place": last_place,
            "recent3": recent3,
            "weight_change": raw["weight_change"],
            "gate": raw["gate"],
            "agari3f_avg": agari3f_avg,
            "jockey_win_rate": jstats["win_rate"],
            "jockey_fukusho_rate": jstats["fukusho_rate"],
            "distance_fit": combined_fit,
            "training": training,
        })

    return horses
