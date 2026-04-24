import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import pandas as pd

df = pd.read_csv("results_log.csv")

print("=== 全体サマリー ===")
print(f"記録レース数: {df['race_name'].nunique()}")
print(f"記録馬数: {len(df)}")

# ツール1位の単勝的中率
top1 = df[df["tool_rank"] == 1]
top1_hit = (top1["actual_place"] == 1).sum()
print(f"\n【単勝】ツール1位が1着: {top1_hit}/{len(top1)} ({top1_hit/len(top1)*100:.0f}%)")

# ツール上位3頭のうち1頭以上が3着以内
results_by_race = []
for race, group in df.groupby("race_name"):
    top3_tool = group[group["tool_rank"] <= 3]
    hit = (top3_tool["actual_place"] <= 3).any()
    results_by_race.append({"race": race, "hit": hit})

hit_df = pd.DataFrame(results_by_race)
hit_count = hit_df["hit"].sum()
print(f"【複勝圏】上位3頭に3着以内が1頭以上: {hit_count}/{len(hit_df)} ({hit_count/len(hit_df)*100:.0f}%)")

# 馬連的中（1位×2位が1・2着）
umaren_hit = 0
for race, group in df.groupby("race_name"):
    top2 = group[group["tool_rank"] <= 2]["actual_place"].tolist()
    if set(top2) == {1, 2} or (1 in top2 and 2 in top2):
        umaren_hit += 1
print(f"【馬連】1位×2位が1・2着: {umaren_hit}/{df['race_name'].nunique()} ({umaren_hit/df['race_name'].nunique()*100:.0f}%)")

print("\n=== レース別詳細 ===")
for race, group in df.groupby(["race_name", "date"]):
    print(f"\n{race[0]} ({race[1]})")
    for _, row in group.sort_values("tool_rank").iterrows():
        mark = "o" if row["actual_place"] <= 3 else "-"
        print(f"  [{mark}] ツール{row['tool_rank']}位 {row['horse_name']} → {row['actual_place']}着")
