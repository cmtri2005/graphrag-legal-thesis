# Điền G2 cho ADR 0006 (NHÁP, không sửa ADR; điền khi CMT duyệt)

## §1 Danh sách khóa
- Danh sách lineage: `data/vilextime_final/lineages_199.txt` (sha256 `d34a1ff2086b293152f24706006c25afcaf983b19326a64c014228e3156b4f1d`); gốc: `data/review/ai_research/2026-11-11_final_count/final_lineages.json` (156: T2 127, T3 6, T6 23) và `.../2026-11-11_t1_labels/cmt_confirmed_t1.json` (`t1_dat`, 43 T1).
- Release: `data/vilextime_final/vilextime.jsonl` sha256 `5766f9162939bd7c37471d8b995b56b6b5dae0c0da11e52ff13d8030587e534c`; meta `vilextime_meta.jsonl` `22142241f8eae7296b48ddad042a3552746070a89d1042663fd41c586acaaa49`.
- Manifest: `data/vilextime_final/manifest.json` sha256 `87093c3f78f4205e77b2c64a45b116cb3dd627465c47b7491a8f264d6675cbcd`.
- Đếm: 722 dòng; `all` 156 lineage / 318 dòng giua_khoang (295 có đáp án); `t6` 23; `t6_unanswerable` 23; `t6_ancestor` 9 lineage; `t2_near` 38; `qsource_silver` 75, `qsource_new` 70, `qsource_supp` 11; `t1_control` 43.
- `t6_ancestor` (12/11, phiên điều phối): chỉ dòng không đáp án, như `t6_ancestor_repealed` của ADR 0005; vẫn 9 lineage. Đã điền vào ADR 0006.

## §6 MDE (ước lượng trước khi chạy)
Cách tính (`data/vilextime_final/g2_mde.py`, kết quả `g2_mde_table.md`): SD của hiệu ghép cặp theo lineage trên dev (`runs/rebuild_20261110_dev/dev`, GPT-4o mini, 63 lineage T2/T3/T6) và test 2 (`runs/E3_test2/test`, `E1_test2/test`, 101 lineage); SE = SD/√N với N cuối (156; F7 23); MDE 80% power = (z + 0,84)·SE, z cho α 0,05 và cho Holm xấu nhất α/7. Xấp xỉ chuẩn trên trung bình theo lineage, không phải bootstrap; đây là ước lượng nháp.

| Mã | Đại lượng, lát | Nguồn SD | lineage nguồn | hiệu quan sát | SD ghép cặp | N cuối | SE | MDE (α 0,05) | MDE (Holm xấu nhất α/7) |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| F1 | accuracy, all | dev | 63 | +0.377 | 0.376 | 156 | 0.030 | 0.084 | 0.106 |
| F1 | accuracy, all | test2 | — | — | — | — | — | — | — (thiếu dự đoán) |
| F2 | accuracy, all | dev | 63 | +0.351 | 0.355 | 156 | 0.028 | 0.080 | 0.100 |
| F2 | accuracy, all | test2 | 101 | +0.186 | 0.304 | 156 | 0.024 | 0.068 | 0.086 |
| F3 | wrong_version, all | dev | 42 | -0.399 | 0.323 | 156 | 0.026 | 0.072 | 0.091 |
| F3 | wrong_version, all | test2 | — | — | — | — | — | — | — (thiếu dự đoán) |
| F4 | tv_recall@1, all_answerable | dev | 63 | +0.138 | 0.387 | 156 | 0.031 | 0.087 | 0.110 |
| F4 | tv_recall@1, all_answerable | test2 | 101 | +0.046 | 0.142 | 156 | 0.011 | 0.032 | 0.040 |
| F5 | tv_recall@1, all_answerable | dev | 63 | +0.085 | 0.259 | 156 | 0.021 | 0.058 | 0.073 |
| F5 | tv_recall@1, all_answerable | test2 | 101 | +0.028 | 0.211 | 156 | 0.017 | 0.047 | 0.060 |
| F6 | tv_recall@1, all_answerable | dev | 63 | +0.085 | 0.259 | 156 | 0.021 | 0.058 | 0.073 |
| F6 | tv_recall@1, all_answerable | test2 | 101 | +0.028 | 0.211 | 156 | 0.017 | 0.047 | 0.060 |
| F7 | accuracy, t6_unanswerable | dev | 21 | +0.000 | 0.316 | 23 | 0.066 | 0.185 | 0.233 |
| F7 | accuracy, t6_unanswerable | test2 | 16 | +0.000 | 0.000 | 23 | 0.000 | 0.000 | 0.000 |

Đọc bảng:
- F4–F6 trên test 2 chỉ có SD 0,14–0,21 (MDE 0,03–0,06); trên dev SD 0,26–0,39 (MDE 0,06–0,11). Hiệu quan sát F5/F6 là +0,03 (test 2) và +0,09 (dev), gần hoặc dưới MDE: "không đủ bằng chứng" là khả năng thật.
- F5 và F6 trùng số vì `b7plus` và `b7pp` cho truy xuất như nhau trên cả hai bộ (ADR 0006 Context).
- F1, F3 chỉ có SD từ dev (`b4` chưa chạy trên test 2). F7: dev 21 lineage, SD 0,32, hiệu quan sát 0, MDE 0,19–0,23 với N = 23; test 2 không có chênh lệch giữa `b7pp` và `proposed` nên SD = 0 vô nghĩa, bỏ qua.
- Dev dùng đồ thị đã sửa 10/11; test 2 dùng generator cũ (Qwen), nên SD test 2 cho F2 chỉ để tham khảo.
