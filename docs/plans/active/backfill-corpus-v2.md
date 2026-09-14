# Execution Plan: Backfill và chuẩn hóa dữ liệu — corpus v2

Date: 2026-09-14

## Status

Active. Chưa bắt đầu triển khai. Chốt sau buổi review bản nháp
`phuong-an-dien-khuyet-va-backfill-du-lieu.md`.

## Outcome

Trước mốc **M1 (05/10/2026)** có **snapshot v2** của corpus, trong đó:

1. Mọi file dẫn xuất (`edges.jsonl`, review queue, cờ eligibility) là hàm thuần
   của toàn bộ `data/`, không phụ thuộc lần chạy trước.
2. Mọi khoảng trống được phân loại: ngoài phạm vi, đã phục hồi, candidate chờ
   review, hoặc không cứu được kèm lý do.
3. Chuỗi expiry cấp Điều/Khoản/Điểm được định vị qua cây nguồn cộng Khoản/Điểm
   tách từ HTML của Điều.
4. Giá trị suy dẫn nằm ngoài dữ liệu nguồn và luôn mang provenance.
5. `verify_pipeline.py` cùng các gate mới đều pass; có báo cáo số liệu trước và
   sau cho khóa luận.

Nằm trong master plan: P2.7–P2.12.

## Context

- Vấn đề gốc: `docs/audit_dataset.md` §4–§7.
- Quyết định: [0001](../../decisions/0001-neo4j-milvus-la-kho-dan-xuat.md),
  [0002](../../decisions/0002-pham-vi-neo-thoi-gian-va-du-lieu-dan-xuat.md).
- Bản nháp đã review: `phuong-an-dien-khuyet-va-backfill-du-lieu.md`. Số đo trong
  bản nháp (60/60 diagram, 4.187 node, 395 candidate) **chưa được tái lập**;
  chúng được đo lại ở T0 và T1.

### Gốc rễ mà plan này xử lý

| # | Gốc rễ | Tầng xử lý |
|---|---|---|
| R1 | Không có thời điểm cấp điều khoản (79,7% văn bản có nhiều văn bản tác động) | T5 chuẩn bị target; phần trích xuất L2 thuộc master plan P3.10–P3.13 |
| R2 | Cây nguồn dừng ở cấp Điều → 7.620 expiry không định vị được | T5 |
| R3 | Tính lỗ hổng cho cả loại văn bản không có hiệu lực riêng | T2 |
| R4 | File dẫn xuất sinh từ trạng thái một lần chạy (`edges.jsonl`, review queue) | T1 |
| R5 | Snapshot chỉ có một `as_of`, backfill trộn nhiều mốc crawl | T0, T3 |

## Scope

In scope:

- Sửa gốc pipeline offline; quy tắc phạm vi; backfill diagram và closure.
- Candidate thời gian cấp văn bản; tách Khoản/Điểm; snapshot v2.
- Phục hồi thủ công văn bản thiếu body hoặc cây, **chỉ khi nằm trên đường găng**.

Out of scope:

- Pipeline PDF/OCR tổng quát.
- View "augmented" (chỉ dựng khi có thí nghiệm cần).
- Auto-accept candidate khi chưa review.
- Ghi đè dữ liệu nguồn.
- Trích xuất L2 từ văn bản sửa đổi (thuộc master plan P3.11).

## Approach

Thứ tự: **khóa → sửa gốc → định phạm vi → backfill → suy dẫn → đóng băng**.
T4 và T5 chạy song song được sau T3.

### T0 — Khóa baseline (15/09) · CMT

| ID | Việc | Tiêu chí xong |
|---|---|---|
| T0.1 | Xác minh snapshot v1 trên HF tải về được và khớp sha256 (master P2.7) | `scripts/pull_snapshot.sh` chạy ở thư mục khác và khớp |
| T0.2 | Ghi baseline vào mục Validation của file này | Số file raw/tree/history/diagram/provision; node text/tổng; số văn bản dưới 50%; cạnh theo loại; target phả hệ thiếu; văn bản/node không neo |

### T1 — Sửa gốc pipeline, offline (15/09 – 20/09)

| ID | Việc | Phụ trách | Tiêu chí xong |
|---|---|---|---|
| T1.1 | `edges.jsonl` sinh từ **toàn bộ** `data/raw/*`, không từ kết quả BFS (R4) | CMT | Hai lần chạy `build_graph.py` với seed khác nhau cho cùng một file; 19 văn bản thiếu cạnh có cạnh; có test |
| T1.2 | Review queue tính từ toàn bộ `data/provisions/`; gate so khớp đúng tập ID | NMT | Thiếu hoặc thừa một ID thì `verify_pipeline.py` fail; chạy lại cho kết quả giống hệt |
| T1.3 | `align()`: chỉ nối theo ID khi `tree_ids ∩ paragraph_ids ≠ ∅`; marker bổ sung node còn thiếu, không ghi đè text lấy theo ID | NMT | Test HTML có ID lạ; chạy thử song song trên 778 văn bản vào thư mục tạm; không văn bản nào có số node text > số node cây; ≥ 4.187 node tăng hoặc giải trình được |
| T1.4 | Hàm chuẩn hóa ngày history (`T00:00` → trừ 1 ngày; `T07:00` → giữ nguyên) | CMT | Có test; sau chuẩn hóa ≥ 99% dòng `DATE_HL` do `Job` ghi trùng `effFrom`; xác nhận tay trên ≥ 20 văn bản gốc |
| T1.5 | Một hàm duy nhất phân loại lỗi khoảng hiệu lực, dùng chung cho `data_status.py`, `ingest.py`, `verify_pipeline.py` | CMT | Tính cả `effTo == effFrom` (74) cùng `effTo < effFrom` (29); ba nơi cho cùng một con số |

### T2 — Quy tắc phạm vi (21/09 – 23/09) · CMT, NMT

| ID | Việc | Tiêu chí xong |
|---|---|---|
| T2.1 | Chốt danh sách loại văn bản QPPL từ 23 `docType` hiện có; xem `docGroup` (1.016 văn bản) có giúp tách "Quyết định" cá biệt không | Danh sách ghi vào ADR 0002; mọi `docType` được xếp loại |
| T2.2 | Sinh `data/derived/eligibility.jsonl`: `in_scope`, `temporal_anchor` kèm lý do, `benchmark_eligible` | Hàm thuần của `data/`; đọc qua skip-list ở tầng đọc; không xóa file nào (master P2.8) |
| T2.3 | Đếm lại lỗ hổng thật chỉ trên tập trong phạm vi | Bảng thay thế `docs/audit_dataset.md` §4 |

### T3 — Backfill nguồn và đóng closure (23/09 – 30/09) · CMT

| ID | Việc | Tiêu chí xong |
|---|---|---|
| T3.1 | Tải 1.017 diagram thiếu → `expand_reverse.py` (hợp tập) → `build_graph.py` → tree, history, text cho văn bản mới; lặp tới khi hội tụ | Không chạm circuit breaker; `reverse_seeds.json` chỉ tăng; mọi target phả hệ mới được tải hoặc ghi nhận gone/failed (master P2.9) |
| T3.2 | Chạy lại toàn bộ gate T1 và T2 trên corpus sau backfill | `verify_pipeline.py` pass |
| T3.3 | Snapshot v2: `SNAPSHOT.txt` ghi khoảng `last_crawled_at` và commit của code không có thay đổi dở dang; đẩy lên HF; kéo về kiểm tra | Tải về ở thư mục khác và dựng lại được |

### T4 — Candidate thời gian cấp văn bản (24/09 – 04/10) · CMT, NMT

| ID | Việc | Tiêu chí xong |
|---|---|---|
| T4.1 | Candidate `effTo` cho văn bản trong phạm vi, hết hiệu lực toàn bộ, thiếu `effTo`, có đúng một văn bản bãi bỏ/thay thế có `effFrom` hợp lệ và muộn hơn `effFrom` của đích | `data/derived/temporal_candidates.jsonl` có method, bằng chứng, `status=needs_review` |
| T4.2 | `issueDate` làm `lower_bound` cho văn bản QPPL thiếu `effFrom` | Không dùng như ngày chính xác trong truy vấn strict (master P2.10) |
| T4.3 | Review thủ công candidate `effTo`, lưu quyết định | Quyết định người duyệt nằm ở `data/review/temporal_candidates.jsonl` (whitelist trong `.gitignore`); chỉ bản ghi được chấp nhận mới thành `derived_verified` |
| T4.4 | 103 văn bản có khoảng hiệu lực lỗi: đối chiếu history đã chuẩn hóa | Giữ `temporal_anchor=false` trừ khi có bằng chứng độc lập |

### T5 — Tách Khoản/Điểm từ HTML của Điều (24/09 – 04/10) · NMT

| ID | Việc | Tiêu chí xong |
|---|---|---|
| T5.1 | Tách tất định: đoạn văn bắt đầu bằng `N.` là Khoản, `x)` là Điểm của Khoản gần nhất; ID `{article_uuid}#k{N}` và `#k{N}.{x}`; lưu ở `data/derived/subtrees/{doc}.json` với `method=RULE` | Test gồm: "1.000 đồng" không phải Khoản; điểm `đ)`; đoạn trích dẫn trong văn bản sửa đổi không bị tách; Điều không có marker thì bỏ qua |
| T5.2 | Đo độ chính xác trên 100 node tách được, phân tầng theo loại văn bản | Ngưỡng chấp nhận chốt trước khi đo (xem Decisions); ghi kết quả vào file này |
| T5.3 | `target_resolver` đọc cây nguồn ∪ cây dẫn xuất; chạy lại `resolve_expiry_targets.py` | Resolve ≥ 29.000/31.175 hoặc giải trình được; số `ambiguous_locator` không tăng |
| T5.4 | Tính lại tập văn bản chỉ có một văn bản tác động và tập bộ ba gold (843 trên v1) | Số mới được cập nhật vào master plan P3.10 |

### T6 — Phục hồi chọn lọc (tùy chọn, không chặn M1)

| ID | Việc | Tiêu chí xong |
|---|---|---|
| T6.1 | Sinh danh sách điền tay: VBQPPL trung ương (`docType.parentCode=VBQPPL`, `organization.orgType=0`) có body rỗng, kể cả cây `[]`. Thứ tự: còn hiệu lực hoặc hết hiệu lực một phần → P0/P1 cũ → hết hiệu lực trên chuỗi phả hệ. Còn lại loại khỏi tập truy xuất | Danh sách tái lập được bằng script; mỗi văn bản điền tay có `method=MANUAL`, `details.source_kind`, sha256 của PDF gốc và người thực hiện |
| T6.2 | Lập bảng VBHN → (ngày hợp nhất, văn bản thành phần) để dùng cho kiểm chứng L3 | Bảng sẵn cho master P3.18 |

## Risks And Recovery

| Rủi ro | Giảm thiểu / khôi phục |
|---|---|
| Backfill ghi raw mới, cập nhật manifest và seeds | T0 xác minh snapshot v1 trước; phục hồi bằng `pull_snapshot.sh` |
| Tách Khoản/Điểm nhầm trong đoạn trích dẫn của văn bản sửa đổi | Test riêng; T5.2 đo phân tầng theo loại văn bản; file dẫn xuất xóa đi dựng lại được |
| "Quyết định" lẫn QPPL và văn bản cá biệt | T2.1 xem `docGroup` và mẫu tay; ghi rõ giới hạn nếu không tách được |
| T1.3 làm đổi text đang đúng | Chạy thử song song, so sánh text lấy theo ID trước và sau khi promote |
| Trễ M1 | T6 không chặn M1; T4 và T5 song song |

## Progress

- [x] T0 khóa baseline (15/09)
- [x] T1.1 · [x] T1.2 · [x] T1.3 · [ ] T1.4 (chờ kiểm tay 20 văn bản) · [x] T1.5
- [x] T2.1 · [x] T2.2 · [x] T2.3 (15/09)
- [ ] T3.1 · [ ] T3.2 · [ ] T3.3 (snapshot v2)
- [ ] T4.1 · [ ] T4.2 · [ ] T4.3 · [ ] T4.4
- [ ] T5.1 · [ ] T5.2 · [ ] T5.3 · [ ] T5.4
- [ ] T6.1 · [ ] T6.2 (tùy chọn)

## Decisions

- 2026-09-14: Phạm vi point-in-time chỉ gồm QPPL; VBHN dùng để kiểm chứng L3;
  tách Khoản/Điểm theo hướng "đo trước rồi làm"; backfill rồi đóng băng v2
  (ADR 0002).
- 2026-09-14: Bỏ pipeline PDF/OCR và view augmented (YAGNI); dữ liệu nguồn không
  bao giờ bị ghi đè.
- 2026-09-14: Quy tắc chuẩn hóa ngày history được chấp nhận làm giả thuyết; chỉ
  có hiệu lực sau khi T1.4 xác nhận.
- 2026-09-15: Ngưỡng T5.2 là **≥ 95% node tách đúng trên 100 node kiểm tay**.
  Không đạt thì không promote cây dẫn xuất.
- 2026-09-15: T4.3 **duyệt toàn bộ** khoảng 395 candidate `effTo`, không lấy mẫu.
- 2026-09-15: PDF văn bản gốc **tải được từ vbpl.vn** (người dùng thử trực tiếp).
  Nguồn điền tay theo thứ tự: PDF gốc vbpl → Công báo → Thư Viện Pháp Luật.
- 2026-09-15: Văn bản QPPL trung ương body rỗng, đã hết hiệu lực và không nằm
  trên chuỗi phả hệ **không được ghi là giới hạn**. Chúng bị **loại khỏi tập
  truy xuất và benchmark** (`in_scope=false`, lý do `no_text_not_needed`) nếu
  không cần cho graph hoặc benchmark. File trên đĩa vẫn giữ nguyên.
- 2026-09-15: Danh sách điền tay được **sinh bằng script** từ tiêu chí T2, thay
  cho `danh-sach-van-ban-can-phuc-hoi-text-thu-cong.md`. Tiêu chí mới thêm nhóm
  cây `[]` + body rỗng (850 văn bản VBQPPL trung ương trên v1).

## Validation

- **T0.1 (15/09):** `scripts/pull_snapshot.sh` tải snapshot v1 từ HF vào thư mục
  tạm; sha256 OK; `verify_pipeline.py --data <bản tải về>` pass; số file ở
  mọi tầng khớp máy làm việc; 0 file bị sửa sau `SNAPSHOT.txt`.
- **T0.2 baseline v1 (15/09, trước T1):**

  | Đại lượng | Giá trị |
  |---|---:|
  | raw / trees / history / diagrams / provisions | 22.550 / 22.532 / 22.548 / 21.533 / 19.279 |
  | Node có text / node cây | 1.136.483 / 1.262.115 |
  | Văn bản coverage < 50% | 778 (file review chỉ liệt kê 20) |
  | Dòng `edges.jsonl` / cạnh phân biệt | 157.795 / 128.289 |
  | Văn bản có references nhưng không có cạnh | 15 |
  | Văn bản / node không neo thời gian (`data_status.py`) | 1.819 / 49.818 (4,4%) |
  | `verify_pipeline.py` | pass (gate cũ) |

- **Sau T1 (15/09):**

  | Việc | Kết quả |
  |---|---|
  | T1.1 | `edges.jsonl` = 128.548 cạnh phân biệt (+259 cạnh từ 19 văn bản trước đây không có cạnh). Gate "covers every referencing document" không còn dung sai: FAIL với file cũ (15 văn bản), PASS sau khi dựng lại. **Lộ ra 115 đích phả hệ chưa tải** (256 cạnh, 128 văn bản nguồn) — trước đây bị che vì file cũ phản ánh lượt BFS cũ; xử lý ở T3.1, gate FAIL đến lúc đó |
  | T1.2 | Review queue sinh từ toàn bộ `data/provisions/`; gate so khớp chính xác tập ID. Xóa 1 dòng → FAIL "1 missing"; khôi phục → PASS |
  | T1.3 | Chạy thử song song trên 778 văn bản: 31 văn bản tăng, **+4.199 node**, 0 node mất, 0 text theo ID bị đổi, 0 vượt số node cây. Promote bằng cách xóa 778 file rồi chạy lại: review queue 778 → 752; tổng node có text 1.140.682. Test phát hiện và đã sửa: phần nối tiếp của node theo ID từng nuốt đoạn của Điều kế tiếp |
  | T1.4 | Quy tắc chuẩn hóa theo (mã, giờ ghi): `DATE_HL`/`DATE_HHL` lúc `T00:00` trừ 1 ngày, lúc `T07:00` giữ nguyên; `DATE_BH` lúc `T00:00` **không** dịch (đo được: dịch cả `DATE_BH` thì 0% khớp). Khớp sau chuẩn hóa: DATE_HL 99,76% (20.663/20.712), DATE_HHL 99,92%, DATE_BH 99,86%. **Còn thiếu:** kiểm tay 20 văn bản dưới đây bằng PDF gốc |
  | T1.5 | Một hàm `anchor_problem` dùng chung cho `data_status.py` và `ingest.py`; tính cả `effTo == effFrom`. Số mới: **1.893 văn bản / 53.508 node (4,7%)** không neo thời gian; nhóm khoảng rỗng 451 → 3.899 node |

- **Sau T2 (15/09):** `scripts/pipeline/build_eligibility.py` →
  `data/derived/eligibility.jsonl` và `data/derived/manual_text_queue.tsv`.

  | Tập trong phạm vi (20.318 QPPL trung ương) | Số văn bản |
  |---|---:|
  | Đủ điều kiện benchmark (neo thời gian, có text) | 16.993 |
  | Body rỗng | 874 |
  | · vào hàng đợi điền tay: ưu tiên 1 (CHL 95, HHL1P 10, không status 1) | 106 |
  | · vào hàng đợi điền tay: ưu tiên 2 (HHL, seed, trên chuỗi phả hệ) | 202 |
  | · loại khỏi truy xuất và benchmark | 566 |
  | **Có body nhưng không có provision (chưa có cấu trúc)** | **1.626** |
  | Không neo thời gian: hết hiệu lực toàn bộ thiếu `effTo` / thiếu `effFrom` / khoảng rỗng / thiếu status | 669 / 223 / 102 / 16 |

  Đối chiếu với danh sách tay 152 văn bản: 128 Công văn và 1 văn bản HĐND nằm
  ngoài phạm vi; 17 vào hàng đợi; 6 QPPL hết hiệu lực toàn bộ không phải seed
  trên chuỗi phả hệ nên bị loại. 140/308 văn bản trong hàng đợi chỉ có tên PDF
  chung chung `Template.pdf`, nên chưa chắc có PDF gốc thật.

  **Phát hiện mới cần quyết định:** 1.626 văn bản QPPL trong phạm vi có chữ
  nhưng không có cây Điều/Khoản, nên hiện không truy xuất được. Chúng cần được
  dựng cấu trúc (mở rộng T5) hoặc dùng cả văn bản làm một đơn vị.

  Mẫu kiểm tay T1.4 — so "có hiệu lực từ ngày" trong PDF gốc với cột `effFrom`:

  | ID | Số hiệu | `effFrom` | history `DATE_HL` |
  |---|---|---|---|
  | `6252` | 11/2000/TTLT/BLĐTBXH-BTC | 2000-01-01 | `2000-01-02T00:00:00` |
  | `38260` | 14/2014/TT-BVHTTDL | 2015-01-01 | `2015-01-02T00:00:00` |
  | `7806` | 28/1998/NĐ-CP | 1999-01-01 | `1999-01-02T00:00:00` |
  | `113297` | 123/2016/NĐ-CP | 2016-10-15 | `2016-10-16T00:00:00` |
  | `8395` | 263/QĐ-NH21 | 1997-08-19 | `1997-08-20T00:00:00` |
  | `15440` | 18/2006/NQ-CP | 2006-09-26 | `2006-09-27T00:00:00` |
  | `113100` | 106/2015/NĐ-CP | 2015-12-10 | `2015-12-11T00:00:00` |
  | `21604` | 37/2003/NĐ-CP | 2003-05-20 | `2003-05-21T00:00:00` |
  | `8159` | 403/1997/QĐ-NHNN2 | 1997-12-20 | `1997-12-21T00:00:00` |
  | `105707` | 59/2007/QĐ-BNN | 2007-08-29 | `2007-08-30T00:00:00` |
  | `157077` | 05/2022/TT-BTP | 2022-10-20 | `2022-10-20T07:00:00` |
  | `144240` | 05/2020/TT-BLĐTBXH | 2020-10-01 | `2020-10-01T07:00:00` |
  | `127853` | 04/2018/TT-BGTVT | 2018-04-15 | `2018-04-15T07:00:00` |
  | `176315` | 18/2025/TT-BCT | 2025-05-02 | `2025-05-02T07:00:00` |
  | `163008` | 13/2023/TT-NHNN | 2023-12-14 | `2023-12-14T07:00:00` |
  | `47456` | 41/2014/TT-BGDĐT | 2015-01-20 | `2015-01-20T07:00:00` |
  | `12996` | 32/2007/TTLT-BCA-BGTVT | 2008-01-25 | `2008-01-25T07:00:00` |
  | `118526` | 219/2016/TT-BTC | 2017-01-01 | `2017-01-01T07:00:00` |
  | `11925` | 14/2009/TT-BGDĐT | 2009-07-10 | `2009-07-10T07:00:00` |
  | `125904` | 45/2017/QĐ-TTg | 2018-01-01 | `2018-01-01T07:00:00` |
- Số đo đã có (14/09, v1):
  - 7.620 chuỗi `locator_not_found`, trong đó 6.815 (89,4%) có marker Khoản/Điểm
    trong HTML (411/446 văn bản).
  - 22.992/31.175 chuỗi expiry cấp điều khoản đã resolve.
- Gate bắt buộc sau mỗi tầng: `python3 -m pytest`, `python3 scripts/check/verify_pipeline.py`.
- Gate mới do plan thêm vào:
  - Review queue khớp đúng tập ID (T1.2).
  - `edges.jsonl` không phụ thuộc tập seed (T1.1).
  - Không có text lấy theo ID nào bị ghi đè (T1.3).
  - Mọi bản ghi dẫn xuất có provenance (T2, T4, T5).
  - Candidate chưa duyệt không xuất hiện trong truy vấn strict (T4).

## Result

_Điền sau khi snapshot v2 được đóng băng._
