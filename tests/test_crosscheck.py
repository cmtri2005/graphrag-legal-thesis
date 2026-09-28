"""Cohen κ on the D4 cross-check."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "review"))
from crosscheck import cohen_kappa, gwet_ac1  # noqa: E402


def test_kappa_matches_a_hand_computed_case():
    # 10 items, 7 agree -> po = 0.7; A has 6 dat, B has 7 -> pe = 0.6*0.7 + 0.4*0.3 = 0.54
    a = ["dat"] * 5 + ["khong_dat"] * 2 + ["dat", "khong_dat", "khong_dat"]
    b = ["dat"] * 5 + ["khong_dat"] * 2 + ["khong_dat", "dat", "dat"]
    assert abs(cohen_kappa(a, b) - (0.7 - 0.54) / (1 - 0.54)) < 1e-9


def test_kappa_edges():
    assert cohen_kappa(["dat", "khong_dat"], ["dat", "khong_dat"]) == 1.0
    assert cohen_kappa(["dat", "dat"], ["dat", "dat"]) is None       # all chance: undefined
    assert cohen_kappa([], []) is None


def test_ac1_stays_high_when_both_raters_say_dat_almost_always():
    # 20 items, both say dat on 18, disagree on 2: raw agreement 0.9, κ collapses, AC1 does not.
    a = ["dat"] * 19 + ["khong_dat"]
    b = ["dat"] * 18 + ["khong_dat", "dat"]
    assert cohen_kappa(a, b) < 0                       # the κ paradox on a skewed sample
    assert gwet_ac1(a, b) > 0.85
    assert gwet_ac1(["dat", "khong_dat"], ["dat", "khong_dat"]) == 1.0
