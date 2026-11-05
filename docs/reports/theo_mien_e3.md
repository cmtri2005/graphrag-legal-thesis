# E3 theo miền

**Thăm dò, không vào họ kiểm định** (C5). Chỉ chấm lại dự đoán có sẵn; không sinh hay chạy hệ mới.

Chế độ `giua_khoang`, split `test`, nhóm T1/T2/T3/T6. Mỗi dòng được đếm đầy đủ một lần ở mỗi miền của nó (đa nhãn; không chia trọng số). Lineage đếm riêng trong từng miền; tổng các miền có thể vượt tổng bộ.

Dùng nguyên `score_vilextime.load_rows`, `distractors`, `units_of`, `score`; distractor tính trên toàn release trước khi chia miền. Accuracy và TV-R@1 lấy mẫu số là mọi dòng; TVER lấy mẫu số `cited_rows` của scorer. Không có trích dẫn thì TVER = —. TVER dựa trên khoảng hiệu lực của đồ thị, không phải kiểm tra pháp lý độc lập. Miền dưới 10 lineage đánh dấu **ít lineage**.

## v1.0

211 dòng / 165 lineage; release `data/vilextime_dataset/vilextime.jsonl`; SHA-256 `7cf51ee66c7e242b0d3a7b03e62f1ed9bede6527082d9b2f8483ec75d278b366`.

v1.0 dùng metadata đồng hành; test 2 dùng bản v2 có đáp án ngắn đã sửa. Nhãn test 2 là nhãn LLM. Nguồn, hash dự đoán/metadata và số tổng kiểm lại: `runs/domain_e3/report.json`.

| Miền | Dòng | Lineage | Hệ | Accuracy | TV-R@1 | TVER | Dòng có trích dẫn |
|---|---:|---:|---|---:|---:|---:|---:|
| dat_dai **ít lineage** | 5 | 3 | b1 | 0.000 | 0.000 | — | 0 |
| dat_dai **ít lineage** | 5 | 3 | b2ctx | 0.600 | 0.200 | 0.600 | 5 |
| dat_dai **ít lineage** | 5 | 3 | b5 | 0.600 | 0.200 | 0.600 | 5 |
| dat_dai **ít lineage** | 5 | 3 | b7 | 1.000 | 0.200 | 0.200 | 5 |
| dat_dai **ít lineage** | 5 | 3 | b7pp | 1.000 | 0.400 | 0.000 | 5 |
| dat_dai **ít lineage** | 5 | 3 | proposed | 1.000 | 0.400 | 0.000 | 5 |
| doanh_nghiep_dau_tu | 23 | 21 | b1 | 0.000 | 0.000 | — | 0 |
| doanh_nghiep_dau_tu | 23 | 21 | b2ctx | 0.609 | 0.348 | 0.522 | 23 |
| doanh_nghiep_dau_tu | 23 | 21 | b5 | 0.609 | 0.348 | 0.522 | 23 |
| doanh_nghiep_dau_tu | 23 | 21 | b7 | 0.783 | 0.565 | 0.043 | 23 |
| doanh_nghiep_dau_tu | 23 | 21 | b7pp | 0.739 | 0.609 | 0.000 | 23 |
| doanh_nghiep_dau_tu | 23 | 21 | proposed | 0.739 | 0.609 | 0.000 | 23 |
| giao_thong | 32 | 25 | b1 | 0.000 | 0.000 | — | 0 |
| giao_thong | 32 | 25 | b2ctx | 0.562 | 0.312 | 0.531 | 32 |
| giao_thong | 32 | 25 | b5 | 0.562 | 0.312 | 0.531 | 32 |
| giao_thong | 32 | 25 | b7 | 0.719 | 0.406 | 0.188 | 32 |
| giao_thong | 32 | 25 | b7pp | 0.719 | 0.438 | 0.000 | 32 |
| giao_thong | 32 | 25 | proposed | 0.719 | 0.438 | 0.000 | 32 |
| khac | 136 | 103 | b1 | 0.000 | 0.000 | — | 0 |
| khac | 136 | 103 | b2ctx | 0.434 | 0.301 | 0.452 | 135 |
| khac | 136 | 103 | b5 | 0.441 | 0.301 | 0.452 | 135 |
| khac | 136 | 103 | b7 | 0.588 | 0.404 | 0.148 | 135 |
| khac | 136 | 103 | b7pp | 0.588 | 0.456 | 0.000 | 135 |
| khac | 136 | 103 | proposed | 0.618 | 0.456 | 0.007 | 134 |
| thue | 16 | 14 | b1 | 0.000 | 0.000 | — | 0 |
| thue | 16 | 14 | b2ctx | 0.438 | 0.125 | 0.438 | 16 |
| thue | 16 | 14 | b5 | 0.438 | 0.125 | 0.438 | 16 |
| thue | 16 | 14 | b7 | 0.625 | 0.438 | 0.000 | 16 |
| thue | 16 | 14 | b7pp | 0.625 | 0.438 | 0.000 | 16 |
| thue | 16 | 14 | proposed | 0.625 | 0.438 | 0.000 | 16 |

## test 2

227 dòng / 101 lineage; release `data/vilextime/test2_release_v2.jsonl`; SHA-256 `b299408327e3bb5c0e520d4457b27225d866afe3c7976e1c3b0aff2b8093855c`.

v1.0 dùng metadata đồng hành; test 2 dùng bản v2 có đáp án ngắn đã sửa. Nhãn test 2 là nhãn LLM. Nguồn, hash dự đoán/metadata và số tổng kiểm lại: `runs/domain_e3/report.json`.

| Miền | Dòng | Lineage | Hệ | Accuracy | TV-R@1 | TVER | Dòng có trích dẫn |
|---|---:|---:|---|---:|---:|---:|---:|
| dat_dai **ít lineage** | 2 | 1 | b1 | 0.000 | 0.000 | — | 0 |
| dat_dai **ít lineage** | 2 | 1 | b2ctx | 0.500 | 0.000 | 0.500 | 2 |
| dat_dai **ít lineage** | 2 | 1 | b5 | 0.500 | 0.000 | 0.500 | 2 |
| dat_dai **ít lineage** | 2 | 1 | b7 | 0.500 | 0.000 | 0.500 | 2 |
| dat_dai **ít lineage** | 2 | 1 | b7pp | 0.500 | 0.000 | 0.000 | 2 |
| dat_dai **ít lineage** | 2 | 1 | proposed | 0.500 | 0.000 | 0.000 | 2 |
| doanh_nghiep_dau_tu | 23 | 11 | b1 | 0.000 | 0.000 | — | 0 |
| doanh_nghiep_dau_tu | 23 | 11 | b2ctx | 0.043 | 0.000 | 0.826 | 23 |
| doanh_nghiep_dau_tu | 23 | 11 | b5 | 0.043 | 0.000 | 0.826 | 23 |
| doanh_nghiep_dau_tu | 23 | 11 | b7 | 0.174 | 0.043 | 0.304 | 23 |
| doanh_nghiep_dau_tu | 23 | 11 | b7pp | 0.130 | 0.130 | 0.000 | 23 |
| doanh_nghiep_dau_tu | 23 | 11 | proposed | 0.130 | 0.130 | 0.000 | 23 |
| giao_thong | 61 | 25 | b1 | 0.000 | 0.000 | — | 0 |
| giao_thong | 61 | 25 | b2ctx | 0.131 | 0.082 | 0.738 | 61 |
| giao_thong | 61 | 25 | b5 | 0.131 | 0.082 | 0.803 | 61 |
| giao_thong | 61 | 25 | b7 | 0.361 | 0.148 | 0.197 | 61 |
| giao_thong | 61 | 25 | b7pp | 0.377 | 0.164 | 0.000 | 61 |
| giao_thong | 61 | 25 | proposed | 0.377 | 0.164 | 0.016 | 61 |
| khac | 137 | 62 | b1 | 0.000 | 0.000 | — | 0 |
| khac | 137 | 62 | b2ctx | 0.168 | 0.080 | 0.647 | 133 |
| khac | 137 | 62 | b5 | 0.168 | 0.080 | 0.662 | 133 |
| khac | 137 | 62 | b7 | 0.299 | 0.117 | 0.216 | 134 |
| khac | 137 | 62 | b7pp | 0.314 | 0.139 | 0.000 | 134 |
| khac | 137 | 62 | proposed | 0.343 | 0.139 | 0.015 | 134 |
| thue **ít lineage** | 4 | 2 | b1 | 0.000 | 0.000 | — | 0 |
| thue **ít lineage** | 4 | 2 | b2ctx | 0.250 | 0.000 | 0.250 | 4 |
| thue **ít lineage** | 4 | 2 | b5 | 0.250 | 0.000 | 0.250 | 4 |
| thue **ít lineage** | 4 | 2 | b7 | 0.500 | 0.000 | 0.000 | 4 |
| thue **ít lineage** | 4 | 2 | b7pp | 0.500 | 0.000 | 0.000 | 4 |
| thue **ít lineage** | 4 | 2 | proposed | 0.500 | 0.000 | 0.000 | 4 |

