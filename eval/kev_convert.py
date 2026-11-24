import json
import sys


def to_kev_row(row):
    """Laya row (expected) -> Kev row (label on each question)."""
    if "expected" not in row:
        raise ValueError("row has no 'expected' answers")
    questions = {}
    for qid, q in row["questions"].items():
        q2 = dict(q)
        q2["label"] = row["expected"][qid]
        questions[qid] = q2
    return {"state": row["state"], "questions": questions}


def convert(src, dst):
    n = 0
    with open(src, encoding="utf-8") as f, open(dst, "w", encoding="utf-8") as g:
        for line in f:
            if not line.strip():
                continue
            g.write(json.dumps(to_kev_row(json.loads(line))) + "\n")
            n += 1
    return n


if __name__ == "__main__":
    print(convert(sys.argv[1], sys.argv[2]), "rows written")