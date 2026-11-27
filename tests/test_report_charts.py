from eval.make_report_charts import L2, L3, L4, N, wilson, rows


def test_wilson_matches_spec():
    lo, hi = wilson(89)  # Run D Level 2: 59.3 [51.3, 66.9]
    assert round(lo, 1) == 51.3 and round(hi, 1) == 66.9
    lo, hi = wilson(37)  # scripted Level 3: 24.7 [18.5, 32.1]
    assert round(lo, 1) == 18.5 and round(hi, 1) == 32.1


def test_percentages_match_spec():
    assert round(100 * L2["Laya Run D"] / N, 1) == 59.3
    assert round(100 * L3["Laya Run D"] / N, 1) == 13.3
    assert round(100 * L4["Laya Run D"] / N, 1) == 32.0
    assert round(100 * L4["scripted"] / N, 1) == 54.7


def test_rows_ordered_and_bounded():
    for data in (L2, L3, L4):
        for _, p, lo, hi in rows(data):
            assert 0 <= lo <= p <= hi <= 100