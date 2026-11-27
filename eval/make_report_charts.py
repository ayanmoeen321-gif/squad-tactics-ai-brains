"""Report charts: hero win rate with 95% Wilson intervals (held-out seeds 0 to 49, 150 games per level).
Numbers are wins out of 150, copied from spec.md sections 9, 25, 26, 27. Run: python -m eval.make_report_charts"""
import math
import os

N = 150

# label -> wins out of 150 (hero wins; lower = stronger monsters)
L2 = {
    "random": 149, "always attack": 127, "scripted": 121, "lookahead2 (teacher)": 86,
    "Laya-B (old text)": 128, "Laya Run D": 89, "Laya Run E": 89,
    "Kev-4B no training": 145, "Kev-0.8B no training": 133,
    "Kev-0.8B 2 epochs": 125, "Kev-0.8B 4 epochs": 115, "Kev-0.8B 1 epoch 17k": 115,
}
L3 = {
    "random": 143, "always attack": 50, "scripted": 37, "lookahead2 (teacher)": 5,
    "Laya-B (old text)": 19, "Laya Run D": 20, "Laya Run E": 18,
    "Kev-4B no training": 51, "Kev-0.8B no training": 88,
    "Kev-0.8B 2 epochs": 15, "Kev-0.8B 4 epochs": 11, "Kev-0.8B 1 epoch 17k": 14,
}
L4 = {
    "random": 148, "always attack": 83, "scripted": 82,
    "lookahead2 (teacher)": 30, "Laya Run D": 48,
}


def wilson(wins, n=N, z=1.96):
    p = wins / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * (c - h), 100 * (c + h)


def rows(data):
    out = []
    for label, wins in data.items():
        lo, hi = wilson(wins)
        out.append((label, 100 * wins / N, lo, hi))
    return out


def plot(data, title, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    r = rows(data)
    labels = [x[0] for x in r][::-1]
    vals = [x[1] for x in r][::-1]
    lo = [x[1] - x[2] for x in r][::-1]
    hi = [x[3] - x[1] for x in r][::-1]
    fig, ax = plt.subplots(figsize=(8, 0.45 * len(r) + 1.5))
    ax.barh(labels, vals, xerr=[lo, hi], color="#4a78b5", capsize=3)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Hero win rate % (lower = stronger monsters), 95% interval")
    ax.set_title(title)
    fig.tight_layout()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    plot(L2, "Level 2 (150 games per brain)", "docs/images/chart_level2.png")
    plot(L3, "Level 3 (150 games per brain)", "docs/images/chart_level3.png")
    plot(L4, "Level 4, a new map (150 games per brain)", "docs/images/chart_level4.png")
    print("wrote docs/images/chart_level2.png, chart_level3.png, chart_level4.png")


if __name__ == "__main__":
    main()