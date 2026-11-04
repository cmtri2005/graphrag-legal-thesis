# Kết quả ViLexTime — test 2

> **Nhãn LLM, không phải nhãn người hay luật sư.** Đã có một lần chấm E3 sai do thiếu đáp án ngắn; báo cáo này chỉ dùng kết quả chấm lại tại `runs/E3_test2/rescore/`. Xem [Amendment 2026-11-04 của ADR 0005](../decisions/0005-ke-hoach-phan-tich.md#amendment-2026-11-04-sửa-đáp-án-ngắn-của-test-2-sau-lần-chấm-e3-đầu).

## `runs/E3_test2/rescore/all.score.json`

Chế độ `giua_khoang`, 227 dòng (T2, T3, T6). KTC 95% bootstrap theo lineage.

| Hệ | Acc | Acc lỏng | TV-R@1 | R@1 | TVER | Sai phiên bản | Phủ trích dẫn |
|---|---|---|---|---|---|---|---|
| `b1` | 0,000 [0,000; 0,000] | 0,000 | 0,000 | 0,000 | — | 0,000 | 0,000 |
| `b2ctx` | 0,150 [0,108; 0,195] | 0,154 | 0,070 | 0,154 | 0,682 | 0,210 | 0,982 |
| `b5` | 0,150 [0,110; 0,193] | 0,159 | 0,070 | 0,154 | 0,709 | 0,215 | 0,982 |
| `b7` | 0,308 [0,242; 0,379] | 0,308 | 0,115 | 0,176 | 0,219 | 0,077 | 0,987 |
| `b7pp` | 0,317 [0,241; 0,396] | 0,317 | 0,141 | 0,141 | 0,000 | 0,010 | 0,987 |
| `proposed` | 0,335 [0,262; 0,411] | 0,335 | 0,141 | 0,141 | 0,013 | 0,005 | 0,987 |

Acc theo nhóm (số dòng trong ngoặc):

| Hệ | T2 (120) | T3 (75) | T6 (32) |
|---|---|---|---|
| `b1` | 0,000 | 0,000 | 0,000 |
| `b2ctx` | 0,167 | 0,093 | 0,219 |
| `b5` | 0,175 | 0,093 | 0,188 |
| `b7` | 0,350 | 0,253 | 0,281 |
| `b7pp` | 0,325 | 0,320 | 0,281 |
| `proposed` | 0,392 | 0,267 | 0,281 |

Hiệu ghép cặp với hệ đứng trước trong file (KTC 95%):

| So sánh | accuracy | tv_recall@1 | tver |
|---|---|---|---|
| b2ctx − b1 | +0,150 [+0,108; +0,195] | +0,070 [+0,040; +0,104] | — |
| b5 − b2ctx | +0,000 [-0,013; +0,013] | +0,000 [+0,000; +0,000] | +0,027 [+0,005; +0,054] |
| b7 − b5 | +0,159 [+0,107; +0,212] | +0,044 [+0,021; +0,072] | -0,490 [-0,563; -0,417] |
| b7pp − b7 | +0,009 [-0,036; +0,055] | +0,026 [-0,013; +0,068] | -0,219 [-0,273; -0,166] |
| proposed − b7pp | +0,018 [-0,026; +0,058] | +0,000 [+0,000; +0,000] | +0,013 [+0,000; +0,031] |

## XN1–XN9 (`runs/E3_test2/rescore/confirm.json`)

10.000 lần lấy mẫu lại, Holm trên 6/6 kiểm định; XN5–XN7 là thăm dò, ngoài Holm (ADR 0005 §1).

| XN | Giả thuyết | So sánh · thước đo · lát | Ước lượng [KTC 95%] | p | p Holm | Kết luận | Dòng/lineage |
|---|---|---|---|---|---|---|---|
| XN1 | H0, truy xuất | `b7pp` − `b7` · tv_recall@1 · all_answerable | +0,028 [-0,014; +0,072] | 0,230 | 0,460 | không đủ bằng chứng | 211/101 |
| XN2 | H0, câu trả lời | `b7pp` − `b7` · tver · all | -0,219 [-0,273; -0,165] | 0,000 | 0,000 | ủng hộ | 227/101 |
| XN3 | RQ3: siêu dữ liệu cấp văn bản | `b7` − `b2ctx` · tv_recall@1 · all_answerable | +0,047 [+0,023; +0,078] | 0,000 | 0,000 | ủng hộ | 211/101 |
| XN4 | RQ3: chuỗi phiên bản | `b7plus` − `b7` · tv_recall@1 · all_answerable | +0,028 [-0,014; +0,072] | 0,235 | 0,460 | không đủ bằng chứng | 211/101 |
| XN5 | H3: lan truyền | `b7pp` − `b7plus` · accuracy · t6_ancestor_repealed | chưa chạy | | | | |
| XN6 | H1 | `b2ctx` · vcr · t2_near/t2_regular | +0,100 [-0,067; +0,278] | 0,271 | — | thăm dò | 30/15, 90/45 |
| XN7 | H2 | `proposed` − `b7` · accuracy · t6/t2_t3 | -0,031 [-0,078; +0,015] | 0,231 | — | thăm dò | 32/16, 195/85 |
| XN8 | RQ2: đồ thị phi thời gian | `proposed` − `b5` · accuracy · all | +0,185 [+0,127; +0,246] | 0,000 | 0,000 | ủng hộ | 227/101 |
| XN9 | RQ1: giá trị của truy xuất | `b2ctx` − `b1` · accuracy · all | +0,150 [+0,109; +0,195] | 0,000 | 0,000 | ủng hộ | 227/101 |
