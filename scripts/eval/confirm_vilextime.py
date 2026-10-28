#!/usr/bin/env python3
"""The confirmatory tests of ADR 0005 §4 (XN1–XN9) with Holm, read from the prediction files.

Each test is fixed here before any system runs on `test`: comparison, metric, slice,
predicted direction and kind of resampling (ADR 0005 §5). Rows are the main table
(`giua_khoang`) of the chosen split; the unit of resampling is the lineage.

  paired      two systems on the same rows, the same resamples (`score` with one seed)
  two_sample  one system on two slices, each slice resampled on its own seed
  did         the paired difference on one slice minus the paired difference on another

A test whose prediction files are missing is reported as not run, and Holm then covers
the tests that ran; the header says so. A dry run on `dev` is expected to be partial.
The run that the thesis reports must have all nine.

Usage:
    python scripts/eval/confirm_vilextime.py --retrieval runs/E1_ladder/test --generation runs/E3/test \\
        --split test --release data/vilextime_dataset/vilextime.jsonl --draws 10000 --out runs/confirm_test.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zlib
from pathlib import Path

from score_vilextime import distractors, interval, load_rows, score, units_of

ALPHA = 0.05
MAIN = ("T1", "T2", "T3", "T6")      # "all": T5 is diagnostic only (ADR 0005 §1)
SLICES = {
    "all": lambda r: r["group"] in MAIN,
    # retrieval-level tests: a repealed row accepts only the repeal instruction, a layer-A unit,
    # so a layer-B rung scores 0 there by construction (ADR 0005 §4)
    "all_answerable": lambda r: r["group"] in MAIN and r["answerable"],
    "t2_near": lambda r: r["group"] == "T2" and bool(r.get("near_identical")),
    "t2_regular": lambda r: r["group"] == "T2" and not r.get("near_identical"),
    "t6_ancestor_repealed": lambda r: (r["group"] == "T6" and r.get("repeal_mode") == "ancestor"
                                       and not r["answerable"]),
    "t6": lambda r: r["group"] == "T6",
    "t2_t3": lambda r: r["group"] in ("T2", "T3"),
}
# (id, hypothesis, kind, metric, slices, source, systems, predicted sign): ADR 0005 §4.
TESTS = (
    ("XN1", "H0, truy xuất", "paired", "tv_recall@1", ("all_answerable",), "retrieval", ("b7", "b7pp"), +1),
    ("XN2", "H0, câu trả lời", "paired", "tver", ("all",), "generation", ("b7", "b7pp"), -1),
    ("XN3", "RQ3: siêu dữ liệu cấp văn bản", "paired", "tv_recall@1", ("all_answerable",), "retrieval",
     ("b2ctx", "b7"), +1),
    ("XN4", "RQ3: chuỗi phiên bản", "paired", "tv_recall@1", ("all_answerable",), "retrieval", ("b7", "b7plus"), +1),
    ("XN5", "H3: lan truyền", "paired", "accuracy", ("t6_ancestor_repealed",), "generation", ("b7plus", "b7pp"), +1),
    ("XN6", "H1", "two_sample", "vcr", ("t2_near", "t2_regular"), "generation", ("b2ctx",), +1),
    ("XN7", "H2", "did", "accuracy", ("t6", "t2_t3"), "generation", ("b7", "proposed"), +1),
    ("XN8", "RQ2: đồ thị phi thời gian", "paired", "accuracy", ("all",), "generation", ("b5", "proposed"), +1),
    ("XN9", "RQ1: giá trị của truy xuất", "paired", "accuracy", ("all",), "generation", ("b1", "b2ctx"), +1),
)


def holm(p: dict[str, float]) -> dict[str, float]:
    """Holm-adjusted p: the i-th smallest times (m − i), kept monotone."""
    out, running = {}, 0.0
    for i, key in enumerate(sorted(p, key=p.get)):
        running = max(running, min(1.0, (len(p) - i) * p[key]))
        out[key] = running
    return out


def verdict(estimate: float, p_holm: float, sign: int) -> str:
    """ADR 0005 §6: supported, contradicted, or not enough evidence."""
    if p_holm >= ALPHA:
        return "không đủ bằng chứng"
    return "ủng hộ" if estimate * sign > 0 else "bác"


def _paired(rows, a, b, units, metric, draws, seed):
    """Per-resample difference b − a (None where a resample leaves the metric undefined)."""
    x, y = score(rows, a, units, draws=draws, seed=seed), score(rows, b, units, draws=draws, seed=seed)
    est = None if x[metric] is None or y[metric] is None else y[metric] - x[metric]
    return est, [None if u[metric] is None or v[metric] is None else v[metric] - u[metric]
                 for u, v in zip(x["_draws"], y["_draws"])]


def run(test: tuple, rows: list[dict], preds: dict[str, dict], units: dict, draws: int) -> dict:
    name, _, kind, metric, slices, _, systems, _ = test
    cut = {s: [r for r in rows if SLICES[s](r)] for s in slices}
    seed = lambda s: zlib.crc32(f"{name}/{s}".encode())  # noqa: E731
    if kind == "paired":
        est, d = _paired(cut[slices[0]], preds[systems[0]], preds[systems[1]], units, metric, draws, seed(slices[0]))
    elif kind == "two_sample":
        x, y = (score(cut[s], preds[systems[0]], units, draws=draws, seed=seed(s)) for s in slices)
        est = None if x[metric] is None or y[metric] is None else x[metric] - y[metric]
        d = [None if u[metric] is None or v[metric] is None else u[metric] - v[metric]
             for u, v in zip(x["_draws"], y["_draws"])]
    else:   # did
        (e1, d1), (e2, d2) = (_paired(cut[s], preds[systems[0]], preds[systems[1]], units, metric, draws, seed(s))
                              for s in slices)
        est = None if e1 is None or e2 is None else e1 - e2
        d = [None if u is None or v is None else u - v for u, v in zip(d1, d2)]
    d = [v for v in d if v is not None]
    p = min(1.0, 2 * min(sum(v <= 0 for v in d), sum(v >= 0 for v in d)) / len(d)) if est is not None and d else None
    return {"estimate": est, "ci95": interval(d) if est is not None else None, "p": p,
            "rows": {s: len(cut[s]) for s in slices},
            "lineages": {s: len({r["lineage_id"] for r in cut[s]}) for s in slices}}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--retrieval", type=Path, help="directory of retrieval-only runs (E1): <system>.jsonl")
    ap.add_argument("--generation", type=Path, help="directory of runs with answers (E2, E3): <system>.jsonl")
    ap.add_argument("--split", required=True, choices=("dev", "test"))
    ap.add_argument("--draws", type=int, default=10_000)
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--release", type=Path, help="a published vilextime.jsonl (export_release.py) "
                                                 "instead of <data>/derived/vilextime/release.jsonl")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    files, preds = {}, {}
    for test in TESTS:
        folder = {"retrieval": args.retrieval, "generation": args.generation}[test[5]]
        for system in test[6]:
            path = folder / f"{system}.jsonl" if folder else None
            if path and path.exists():
                files[(test[5], system)] = path
    for key, path in files.items():
        preds[key] = {p["id"]: p for p in map(json.loads, path.open(encoding="utf-8"))}

    release = load_rows(args.release or args.data / "derived/vilextime/release.jsonl")
    extra = distractors(release)
    rows = [{**r, "_distractors": extra.get(r["id"], [])} for r in release
            if r.get("split") == args.split and r["as_of_strategy"] == "giua_khoang"]
    units = units_of(args.data, {f"{s}/{n}": p for (s, n), p in preds.items()})[0]

    results = {}
    for test in TESTS:
        name, _, _, _, _, source, systems, _ = test
        if all((source, s) in preds for s in systems):
            results[name] = run(test, rows, {s: preds[(source, s)] for s in systems}, units, args.draws)
    ran = {k: v["p"] for k, v in results.items() if v["p"] is not None}
    adjusted = holm(ran)
    lines = [f"ADR 0005 · split {args.split} · {args.draws:,} lần lấy mẫu lại · "
             f"Holm trên {len(ran)}/{len(TESTS)} kiểm định" + ("" if len(ran) == len(TESTS) else " (CHƯA ĐỦ HỌ)")]
    for name, hypothesis, kind, metric, slices, source, systems, sign in TESTS:
        r = results.get(name)
        what = f"{name} {hypothesis}: {' − '.join(reversed(systems))} · {metric} · {'/'.join(slices)}"
        if r is None or r["p"] is None:
            lines.append(f"{what}: chưa chạy" + ("" if r is None else " (đại lượng không xác định)"))
            continue
        r.update(p_holm=adjusted[name], verdict=verdict(r["estimate"], adjusted[name], sign), predicted=sign)
        lines.append(f"{what}: {r['estimate']:+.3f} [{r['ci95'][0]:+.3f}; {r['ci95'][1]:+.3f}] "
                     f"p={r['p']:.4f} p_Holm={r['p_holm']:.4f} → {r['verdict']} "
                     f"({', '.join(f'{s} {r['rows'][s]} dòng/{r['lineages'][s]} lineage' for s in slices)})")
    h0 = [results.get(k, {}).get("verdict") for k in ("XN1", "XN2")]
    if all(h0):
        lines.append("H0: " + ("ủng hộ" if h0 == ["ủng hộ", "ủng hộ"] else
                               "nhánh điểm quyết định B7 (XN1 không được ủng hộ)" if h0[0] != "ủng hộ" else
                               "ủng hộ một phần (chỉ ở tầng truy xuất)"))
    print("\n".join(lines))
    if args.out:
        args.out.write_text(json.dumps({
            "split": args.split, "draws": args.draws, "tests_run": len(ran),
            "files": {f"{s}/{n}": {"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                      for (s, n), p in files.items()},
            "results": results}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"-> {args.out}")


if __name__ == "__main__":
    main()
