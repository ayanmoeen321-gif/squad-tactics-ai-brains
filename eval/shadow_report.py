import json
import sys
from collections import defaultdict

DECISIVE = 300  # about one of the teacher's 3 simulated games flips between a win and a loss (those count 1000)


def kind_of(option_id):
    return option_id.split("_")[0]


def load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def _stats(rs):
    n = len(rs)
    agree = sum(r["student"] == r["teacher"] for r in rs)
    reg = sum(r["regret"] for r in rs)
    return {"n": n, "agree_pct": round(100 * agree / n, 1), "mean_regret": round(reg / n, 3),
            "regret_sum": round(reg, 1), "decisive": sum(r["regret"] >= DECISIVE for r in rs)}


def _group(rs, keyfn):
    g = defaultdict(list)
    for r in rs:
        g[keyfn(r)].append(r)
    return {k: _stats(v) for k, v in sorted(g.items(), key=lambda kv: str(kv[0]))}


def summarize(rows):
    ds = [r for r in rows if r.get("teacher") is not None and r.get("regret") is not None]
    if not ds:
        return {"decisions": 0}
    out = {"decisions": len(ds), "all": _stats(ds)}
    out["by_level"] = _group(ds, lambda r: r.get("level"))
    out["by_kind"] = _group(ds, lambda r: r.get("kind"))
    out["by_round"] = _group(ds, lambda r: "1-5" if r["round"] <= 5 else "6-10" if r["round"] <= 10 else "11+")
    out["pairs"] = _group([r for r in ds if r["student"] != r["teacher"]],
                          lambda r: (kind_of(r["student"]), kind_of(r["teacher"])))
    return out


def print_report(s):
    if not s.get("decisions"):
        print("no decisions")
        return
    a = s["all"]
    print(f"decisions with 2+ options: {a['n']}   agree with the teacher: {a['agree_pct']}%   "
          f"mean regret: {a['mean_regret']}   decisive (regret >= {DECISIVE}): {a['decisive']}")
    for title, key in (("by level", "by_level"), ("by monster kind", "by_kind"), ("by round", "by_round")):
        print("\n" + title)
        for k, v in s[key].items():
            print(f"  {str(k):10} n={v['n']:6} agree={v['agree_pct']:5}%  mean regret={v['mean_regret']:9}  decisive={v['decisive']}")
    print("\ndisagreements, Laya option -> teacher option (by total regret)")
    for k, v in sorted(s["pairs"].items(), key=lambda kv: -kv[1]["regret_sum"])[:12]:
        print(f"  {k[0]:>8} -> {k[1]:<8} n={v['n']:6} regret sum={v['regret_sum']:10} decisive={v['decisive']}")


if __name__ == "__main__":
    rows = []
    for p in sys.argv[1:]:
        rows += load(p)
    print_report(summarize(rows))