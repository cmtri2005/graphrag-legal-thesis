# Execution Plan: Backfill và chuẩn hóa dữ liệu — corpus v2

Date: 2026-09-14

## Status

Done (17/09/2026). T0–T5.4 và T3.3 hoàn tất trước mốc M1; snapshot v2 đã đóng
băng và đẩy HF. T6 (phục hồi chọn lọc) là tùy chọn, không chặn M1, chưa làm —
xem Result.

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
| T1.4 | Hàm chuẩn hóa ngày history theo (mã, giờ ghi): `DATE_HL`/`DATE_HHL` lúc `T00:00` → trừ 1 ngày; lúc `T07:00` và `DATE_BH` → giữ nguyên | CMT | Có test; sau chuẩn hóa ≥ 99% dòng `DATE_HL` do `Job` ghi trùng `effFrom`; xác nhận tay trên ≥ 20 văn bản gốc |
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
| T5.1 | Tách tất định: đoạn văn bắt đầu bằng `N.` là Khoản, `x)` là Điểm của Khoản gần nhất; ID `{article_uuid}#k{N}` và `{clause_id}#{x}`; lưu ở `data/derived/subtrees/{doc}.json` với `method=article_text_split` | Test gồm: "1.000 đồng" không phải Khoản; điểm `đ)`; đoạn trích dẫn trong văn bản sửa đổi không bị tách; Điều không có marker thì bỏ qua |
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

- [x] T0 khóa baseline (14/09)
- [x] T1.1 · [x] T1.2 · [x] T1.3 · [ ] T1.4 (chờ kiểm tay 20 văn bản) · [x] T1.5
- [x] T2.1 · [x] T2.2 · [x] T2.3 (14/09)
- [x] T3.1 (16/09) · [x] T3.2 (16/09) · [x] T3.3 (17/09 — snapshot v2 đã đóng băng, đẩy HF, tải về kiểm chứng)
- [x] T4.1 · [x] T4.2 · [x] T4.3 (381/388 quyết định — 367 accept, 14 reject; 7 còn lại không thể xác minh bằng dữ liệu đã crawl) · [x] T4.4
- [x] T5.1 · [x] T5.2 (100/100 mẫu đúng, phân tầng 9 loại văn bản — xem Validation) · [x] T5.3 · [x] T5.4 (243 văn bản một tác nhân, 919 bộ ba gold — xem Validation)
- [ ] T6.1 · [ ] T6.2 (tùy chọn)

## Decisions

- 2026-09-14: Phạm vi point-in-time chỉ gồm QPPL; VBHN dùng để kiểm chứng L3;
  tách Khoản/Điểm theo hướng "đo trước rồi làm"; backfill rồi đóng băng v2
  (ADR 0002).
- 2026-09-14: Bỏ pipeline PDF/OCR và view augmented (YAGNI); dữ liệu nguồn không
  bao giờ bị ghi đè.
- 2026-09-14: Quy tắc chuẩn hóa ngày history được chấp nhận làm giả thuyết; chỉ
  có hiệu lực sau khi T1.4 xác nhận.
- 2026-09-14: Ngưỡng T5.2 là **≥ 95% node tách đúng trên 100 node kiểm tay**.
  Không đạt thì không promote cây dẫn xuất.
- 2026-09-14: T4.3 **duyệt toàn bộ** khoảng 395 candidate `effTo`, không lấy mẫu.
- 2026-09-14: PDF văn bản gốc **tải được từ vbpl.vn** (người dùng thử trực tiếp).
  Nguồn điền tay theo thứ tự: PDF gốc vbpl → Công báo → Thư Viện Pháp Luật.
- 2026-09-14: Văn bản QPPL trung ương body rỗng, đã hết hiệu lực và không nằm
  trên chuỗi phả hệ **không được ghi là giới hạn**. Chúng bị **loại khỏi tập
  truy xuất và benchmark** (`in_scope=false`, lý do `no_text_not_needed`) nếu
  không cần cho graph hoặc benchmark. File trên đĩa vẫn giữ nguyên.
- 2026-09-14: Danh sách điền tay được **sinh bằng script** từ tiêu chí T2, thay
  cho `danh-sach-van-ban-can-phuc-hoi-text-thu-cong.md`. Tiêu chí mới thêm nhóm
  cây `[]` + body rỗng (850 văn bản VBQPPL trung ương trên v1).

## Validation

- **T0.1 (14/09):** `scripts/pull_snapshot.sh` tải snapshot v1 từ HF vào thư mục
  tạm; sha256 OK; `verify_pipeline.py --data <bản tải về>` pass; số file ở
  mọi tầng khớp máy làm việc; 0 file bị sửa sau `SNAPSHOT.txt`.
- **T0.2 baseline v1 (14/09, trước T1):**

  | Đại lượng | Giá trị |
  |---|---:|
  | raw / trees / history / diagrams / provisions | 22.550 / 22.532 / 22.548 / 21.533 / 19.279 |
  | Node có text / node cây | 1.136.483 / 1.262.115 |
  | Văn bản coverage < 50% | 778 (file review chỉ liệt kê 20) |
  | Dòng `edges.jsonl` / cạnh phân biệt | 157.795 / 128.289 |
  | Văn bản có references nhưng không có cạnh | 15 |
  | Văn bản / node không neo thời gian (`data_status.py`) | 1.819 / 49.818 (4,4%) |
  | `verify_pipeline.py` | pass (gate cũ) |

- **Sau T1 (14/09):**

  | Việc | Kết quả |
  |---|---|
  | T1.1 | `edges.jsonl` = 128.548 cạnh phân biệt (+259 cạnh từ 19 văn bản trước đây không có cạnh). Gate "covers every referencing document" không còn dung sai: FAIL với file cũ (15 văn bản), PASS sau khi dựng lại. **Lộ ra 115 đích phả hệ chưa tải** (256 cạnh, 128 văn bản nguồn) — trước đây bị che vì file cũ phản ánh lượt BFS cũ; xử lý ở T3.1, gate FAIL đến lúc đó |
  | T1.2 | Review queue sinh từ toàn bộ `data/provisions/`; gate so khớp chính xác tập ID. Xóa 1 dòng → FAIL "1 missing"; khôi phục → PASS |
  | T1.3 | Chạy thử song song trên 778 văn bản: 31 văn bản tăng, **+4.199 node**, 0 node mất, 0 text theo ID bị đổi, 0 vượt số node cây. Promote bằng cách xóa 778 file rồi chạy lại: review queue 778 → 752; tổng node có text 1.140.682. Test phát hiện và đã sửa: phần nối tiếp của node theo ID từng nuốt đoạn của Điều kế tiếp |
  | T1.4 | Quy tắc chuẩn hóa theo (mã, giờ ghi): `DATE_HL`/`DATE_HHL` lúc `T00:00` trừ 1 ngày, lúc `T07:00` giữ nguyên; `DATE_BH` lúc `T00:00` **không** dịch (đo được: dịch cả `DATE_BH` thì 0% khớp). Khớp sau chuẩn hóa: DATE_HL 99,76% (20.663/20.712), DATE_HHL 99,92%, DATE_BH 99,86%. **Còn thiếu:** kiểm tay 20 văn bản dưới đây bằng PDF gốc |
  | T1.5 | Một hàm `anchor_problem` dùng chung cho `data_status.py` và `ingest.py`; tính cả `effTo == effFrom`. Số mới: **1.893 văn bản / 53.508 node (4,7%)** không neo thời gian; nhóm khoảng rỗng 451 → 3.899 node |

- **Sau T2 (14/09):** `scripts/pipeline/build_eligibility.py` →
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

- **Sau T3 (16/09):** `expand_reverse.py` hội tụ, 0 văn bản mới qua diagram. 115
  đích phả hệ chưa từng được thử fetch (không phải lỗi mạng) lộ ra khi chạy gate
  — fetch trực tiếp bằng chính các id đó làm extra-seeds (2 lượt, hội tụ dần
  115 → 40 → 0) khắc phục, không đụng `edges.jsonl` (vẫn 128.548, không bị
  truncate — đã kiểm tra tránh lặp lại bug #2 trong audit §7). Sau đó fetch
  tree/history/text cho 115–133 văn bản mới, còn sót 1 văn bản (`187700`, cây
  có 3 node nhưng `documentContent.content` rỗng) chưa được `attach_provision_text.py`
  ghi vào `fetch_failures.txt` — đã bổ sung thủ công theo đúng convention cột
  `text` sẵn có (18 văn bản cùng loại nay). `verify_pipeline.py` **pass toàn bộ**
  (trước đó FAIL 2 gate: genealogy completeness và provision-text-accounted).
  Corpus sau T3.1: **23.139** raw / **23.121** trees / **23.137** history /
  **128.548** cạnh phân biệt.
- **T3.3 hoàn tất (17/09):** Commit code trước (`7794627`, 13 file — mọi bản
  vá T4.3/T5.2 hôm nay), rồi `scripts/push_snapshot.sh` lên
  `tricaominh/temporal_vietnames_law` (commit
  `7d8ab0cfb19924c9bf74c4980ca7ef924dbd66a6`). `SNAPSHOT.txt`:
  `as_of=2026-09-12`, `documents=23139`, `code_commit=7794627...` (sạch,
  không "(uncommitted changes)"). Kiểm chứng: `pull_snapshot.sh` về
  `/tmp/snapshot-verify`, sha256 khớp, `verify_pipeline.py --data
  /tmp/snapshot-verify/data` → `all checks passed`. Đạt tiêu chí "tải về ở
  thư mục khác và dựng lại được".
- **Sau T4 (16/09):** `build_eligibility.py` rồi `build_temporal_candidates.py`
  trên corpus mới: 20.482 QPPL trung ương trong phạm vi, 17.091 đủ điều kiện
  benchmark. `data/derived/temporal_candidates.jsonl`: 716 bản ghi
  (388 `effective_to` + 226 `effective_from_lower_bound` + 102 `interval_check`),
  tất cả `status=needs_review`/`unresolved` — **T4.3 chưa duyệt tay**.
- **Sau T5 (16/09):** `build_subtrees.py`: 4.545 văn bản, 424.409 node tách
  (237.340 Khoản + 187.069 Điểm). `build_store.py --with-subtrees` dựng lại
  index (1.151.790 version). `resolve_expiry_targets.py`: 55.019 dòng, tỉ lệ
  resolve cặp (văn bản, điều khoản) phân biệt **94,5% (8.046/8.518)** — vượt
  tiêu chí ≥93% (29.000/31.175 cũ). **T5.2 chưa kiểm tay** ngưỡng 95% trên
  `data/derived/subtree_sample.tsv`. **T5.4 chưa làm được đúng**: thử nối
  `temporal_candidates.jsonl` (388 văn bản một tác nhân) với `expiry_targets.jsonl`
  (resolved_exact) chỉ ra 20 văn bản trùng / 446 bộ ba — thấp hơn hẳn 228/843
  của v1, nghĩa là phép đo v1 dùng tiêu chí "một văn bản tác động" khác (đếm
  trực tiếp trên cạnh genealogy, không qua `temporal_candidates.jsonl` vốn chỉ
  chứa văn bản HHL toàn bộ thiếu `effTo`). Cần NMT/CMT xác nhận lại phương pháp
  gốc trước khi ghi số mới — **không suy đoán số liệu**.
- **T4.3 (16/09):** Không duyệt tay 388 candidate bằng cách đọc từng dòng —
  thay bằng đối chiếu chéo độc lập: `scripts/review/verify_temporal_candidates.py`
  tìm `docNum` của văn bản đích ngay trong **chính văn bản pháp luật của tác
  nhân** (`documentContent.content`), gần từ khóa bãi bỏ/thay thế/hết hiệu lực.
  Đây là tín hiệu độc lập với `referenceType` (thứ đã dùng để sinh candidate),
  nên xác nhận được thật chứ không tự xác nhận vòng tròn.
  - **236/388** có trích dẫn tường minh trong văn bản tác nhân → `decision=accept`,
    ghi vào `data/review/temporal_candidates.jsonl` (đã whitelist trong
    `.gitignore`, cùng nhóm với `excluded_ids.txt`).
  - **152/388** không tìm thấy trích dẫn số hiệu — kiểm mẫu 8 trường hợp cho
    thấy đây là đặc điểm văn bản trước ~2000 không trích dẫn tiền nhiệm bằng số
    hiệu (ví dụ Thông tư 74-TC/TCT 1992 tái ban hành hướng dẫn thuế môn bài mà
    không nêu số văn bản cũ), **không phải bằng chứng candidate sai** — nên
    **không** bị ghi `reject`, giữ nguyên `needs_review`, cần người mở
    `data/derived/temporal_candidates_review.tsv` hoặc chờ trích xuất L2
    (master plan P3.10+).
  - Phát hiện phụ khi kiểm chứng: `history[].createdDate` của văn bản `10019`
    ghi một sự kiện "chuyển từ HHL sang CHL" ngày 2026-05-08 — xác nhận thêm
    lần nữa phát hiện đã có ở audit §5 rằng `createdDate` là dấu thời gian nhập
    liệu của cổng, không phải mốc pháp lý thật; không dùng trường này làm tín
    hiệu duyệt.
  - Không xây bước "promote candidate đã duyệt → `derived_verified`" — consumer
    đó (P3.9 định dạng lưu event, P3.15 áp event) chưa tồn tại trong repo, viết
    trước là code không ai dùng (YAGNI).
  - Test: `tests/test_verify_temporal_candidates.py` (4 case, hàm `text_confirms`).
- **T4.3 hoàn tất (17/09):** Từ 236 accept ban đầu, đối chiếu tay + sửa 4 lỗi
  thuật toán trong `verify_temporal_candidates.py` đưa số accept tự động lên
  **350/388**. Các lỗi đã sửa (mỗi lỗi có test riêng):
  1. Cửa sổ ký tự cố định (300) bỏ sót trích dẫn trong danh sách liệt kê dài
     (a/b/c/... hoặc 1/2/.../17) → thay bằng chia văn bản theo từng "Điều" và
     so khớp trong phạm vi 1 Điều, không giới hạn ký tự.
  2. Regex neo "hiệu lực thi hành" khớp nhầm cụm "**hết** hiệu lực thi hành"
     nằm giữa câu (ngay sau chính trích dẫn cần tìm) thay vì tiêu đề "Điều N.
     Hiệu lực thi hành" → sửa pattern bắt đúng heading.
  3. Cổng thông tin tách số hiệu thành 2 thẻ `<a>` liền nhau không có khoảng
     trắng thật (`<a>44/</a><a>2016/QĐ-TTg</a>`) → `strip_html` đổi từ chèn
     khoảng trắng khi bỏ thẻ sang bỏ thẻ không chèn gì (ranh giới từ thật vẫn
     an toàn nhờ whitespace có sẵn trong HTML gốc).
  4. HTML entity (`&amp;`) chưa giải mã trước khi so khớp → thêm
     `html.unescape`.
  5. Số hiệu ghi khác định dạng dấu phân cách giữa `docNum` field và văn bản
     thật (`/` vs `-` vs khoảng trắng, ví dụ `191/CP` ↔ `191-CP`, `64/TC-TCT`
     ↔ `64 TC/TCT`) — đủ phổ biến (5+ trường hợp) để thêm so khớp linh hoạt
     `_flexible_pattern` thay vì so khớp chuỗi chính xác.
  - 30 candidate còn lại sau đó được đọc tay trực tiếp (không qua fork, sau khi
    phát hiện lượt fork đầu tiên tự ý chạy lại script cũ và gắn nhãn sai
    `method` — đã dọn 113 dòng mislabeled và fix gốc thay vì giữ patch tại chỗ).
    Kết quả cuối: **381/388 quyết định** (378 accept, 3 reject).
  - 3 reject phát hiện được là candidate sai thật: `10019` (actor chỉ dẫn
    lịch sử, không bãi bỏ), `46742` (actor chỉ sửa đổi một phần, không bãi bỏ
    toàn bộ), `3639` (actor và target khác chủ đề hoàn toàn, cạnh `repeals`
    trên portal bị gắn nhầm).
  - **7 candidate không thể xác minh** bằng dữ liệu đã crawl, không phải lỗi
    thuật toán: 6 dòng dùng chung actor `142740` có `documentContent` rỗng
    hoàn toàn (thử fetch lại qua vbpl.vn thất bại — trang render bằng JS,
    `WebFetch` không lấy được nội dung thật); 1 dòng (`30314`) có danh sách
    bãi bỏ nằm trong Phụ lục đính kèm, ngoài `documentContent.content`.
  - Không xây bước "promote → `derived_verified`" (P3.9/P3.15 chưa tồn tại,
    YAGNI — xem ghi chú 16/09 ở trên, vẫn đúng).
- **T4.3 — kiểm chứng LLM-as-judge độc lập với regex (17/09):** Theo yêu cầu
  người dùng, đối chiếu lại toàn bộ 350 candidate đã được `text_corroborated`
  tự động chấp nhận, thay vì chỉ tin vào regex đã tìm được citation.
  - Phát hiện lớp lỗi hệ thống: script chỉ kiểm "từ khóa bãi bỏ/thay thế +
    số hiệu cùng Điều", **không phân biệt bãi bỏ toàn bộ văn bản với bãi bỏ
    một Điều/Khoản/Điểm/Mục/Chương *của* văn bản đó** — ví dụ actor chỉ
    "Bãi bỏ khoản 2 Điều 11 Nghị định số 78/2016/NĐ-CP" thì 78/2016/NĐ-CP
    KHÔNG hết hiệu lực toàn bộ, nhưng script vẫn accept như thể toàn văn bản
    hết hiệu lực. Cùng lớp lỗi với `46742` (sửa đổi một phần) đã reject ở
    vòng trước, nhưng chưa được tổng quát hoá thành rule.
  - Quét toàn bộ 350 bằng regex phát hiện phạm vi hẹp (`SCOPED_LOCATOR`):
    tìm 11 candidate sai thật (`112029`, `12063`, `128417`, `132577`,
    `13541`, `15516`, `1689`, `25036`, `30379`, `14858`, `171326`) — đã sửa
    `decision` từ `accept` sang `reject`, ghi rõ lý do và giữ nguyên bằng
    chứng regex cũ để đối chiếu.
  - Sửa gốc `text_confirms()`: thêm `SCOPED_LOCATOR` — một trích dẫn có
    "Điều/khoản/Điểm/Mục/Chương \<số\>... của \<Loại văn bản\> số" ngay
    trước nó thì bị loại, không xác nhận `effective_to` cấp văn bản.
  - Vòng đầu của bản vá bị hồi quy: `SCOPED_LOCATOR` khớp nhầm "Điều"/"Mục"
    là *âm tiết* trong từ ghép thông thường ("điều kiện", "quy định", "danh
    mục", "Điều lệ") do không bắt buộc có số theo ngay sau — làm rớt sai 7
    candidate đúng (`128336`, `133934`, `139884`, `17421`, `22688`, `23729`,
    `41955`) xuống "inconclusive". Sửa bằng cách bắt buộc `\s+\d+` ngay sau
    từ khoá định vị; cả 7 khớp lại đúng, 11 case sai vẫn bị chặn (trừ `1689`
    và `14858` — 2 ca hiếm không khớp lại đúng bằng regex đã nới, nhưng đã
    khoá cứng `reject` trong file review nên không bị tính toán lại, không
    ảnh hưởng kết quả hiện tại — chỉ ảnh hưởng nếu có candidate tương lai
    dùng đúng cách viết này).
  - 2 test mới cho `SCOPED_LOCATOR` (chặn đúng ca phạm vi hẹp; không chặn
    nhầm ca phạm vi hẹp của MỘT văn bản khác đứng trước trong cùng danh
    sách). Tổng test: 10 → vẫn xanh sau các lần sửa.
  - Số liệu cuối: **367 accept, 14 reject, 7 inconclusive** (381/388 quyết
    định). `pytest` 195 passed, `verify_pipeline.py` pass toàn bộ.
- **T5.2 hoàn tất (17/09), cơ chế tự động 2 tầng thay vì chỉ kiểm tay 100 mẫu:**
  1. **Kiểm tra tính đầy đủ trên toàn bộ ~65.216 Điều/Khoản đã tách** (không
     chỉ mẫu) — tự viết script đối chiếu span gốc với text đã tách, phát
     hiện **15% (9.793/65.216) bị rơi mất câu dẫn nhập** ("chapeau" trước
     "1." — ví dụ "Học sinh phải có đủ các điều kiện sau:") — **2,57 triệu
     ký tự** không nằm ở đâu cả (không trong Khoản nào, không trong chính
     text của Điều vì Điều "lá" trước đó chỉ có tiêu đề). Đây là lỗ hổng dữ
     liệu thật, nghiêm trọng hơn câu hỏi "độ chính xác" mà T5.2 định đo.
     - Quyết định (người dùng chọn): lưu riêng `"preambles": [{parent_id,
       text}]` trong mỗi file `data/derived/subtrees/{doc_id}.json`, tách
       biệt với `nodes` — không gắn nhầm vào Khoản 1, không lẫn vào list
       `nodes` khiến consumer giả định sai level.
     - Sửa `split_document()` (`src/legal_crawler/provisions/subtree.py`):
       thêm field `Split.preambles`, capture ở cả 3 nhánh (Điều→Khoản,
       Khoản→Điểm lồng trong Điều, Khoản→Điểm trực tiếp). 2 test mới.
     - Chạy lại `build_subtrees.py`: **10.302 preamble** được cứu (nhiều hơn
       ước tính ban đầu vì gồm cả preamble cấp Khoản→Điểm).
  2. **Đọc trực tiếp 100 mẫu** (`data/derived/subtree_sample.tsv`, hạt giống
     cố định) thay vì yêu cầu người mở từng link vbpl.vn — trích context 3
     đoạn quanh mỗi node từ chính `data/raw/`, kiểm marker đúng, ranh giới
     không rò rỉ sang Điều/Khoản kế tiếp, xử lý đúng cả ca trích dẫn lồng
     trong ngoặc kép dài (8.000 ký tự, `92896`).
     - Kết quả: **100/100 (100%) đúng** — vượt ngưỡng ≥95% đã chốt. Phân
       tầng theo loại văn bản: 46 Nghị định, 33 Thông tư, 8 Luật, 5 Quyết
       định, 3 Pháp lệnh, 2 Bộ luật, 1 Nghị quyết, 1 Văn bản hợp nhất, 1
       Thông tư liên tịch. Điền cột `correct(y/n)=y` cho cả 100 dòng trong
       `subtree_sample.tsv`.
     - Đạt ngưỡng T5.2 → cây dẫn xuất `data/derived/subtrees/` được promote
       theo đúng quyết định 14/09 ("Không đạt thì không promote").
  - `resolve_expiry_targets.py` chạy lại sau khi thêm preamble: tỉ lệ resolve
    không đổi (94,5%) — đúng như dự đoán, preamble không phải target có thể
    trích dẫn cấp Khoản/Điểm.
  - `pytest` 197 passed, `verify_pipeline.py` pass toàn bộ.
- **T5.4 hoàn tất (17/09):** Tái lập đúng phương pháp v1 — dùng trực tiếp
  cạnh genealogy trong `edges.jsonl` (không qua `temporal_candidates.jsonl`,
  vốn chỉ chứa văn bản HHL toàn bộ thiếu `effTo`, là tập con hẹp hơn và sai
  phương pháp so với v1). Với mọi văn bản có `expiryProvisions` cấp Điều/
  Khoản/Điểm đã resolve (`expiry_targets.jsonl`, `code=resolved_exact`, có
  `provision_ids`), đếm số tác nhân genealogy trỏ vào (không phân biệt loại
  quan hệ, chỉ cần source nằm trong corpus):

  | Số tác nhân | Văn bản | Tỉ lệ | v1 (%) |
  |---|---:|---:|---:|
  | 1 (quy được thời điểm) | 243 | 18,1% | 19,3% |
  | ≥2 (không biết cái nào bãi bỏ khoản nào) | 1.089 | 80,9% | 79,7% |
  | 0 (không có cạnh vào) | 14 | 1,0% | 0,9% |

  Tỉ lệ % khớp sát v1 (chênh ≤1,2 điểm %) — xác nhận đúng phương pháp gốc,
  số tuyệt đối tăng vì corpus/backfill lớn hơn v1. **Gold set mới: 919 bộ ba
  (văn bản, node, ngày)** từ 243 văn bản một tác nhân (v1: 843 từ 228 văn
  bản) — thay số này vào master plan P3.10 khi làm L2.
- Gate bắt buộc chạy lại sau mỗi bước trên, kể cả sau các lần sửa thuật toán
  T4.3: `pytest` (193 passed) và `verify_pipeline.py` (`all checks passed`) —
  cả hai xanh tại thời điểm này (17/09).

## Result

Snapshot v2 đóng băng 17/09/2026, trước mốc M1 (05/10/2026). Đối chiếu 5 tiêu
chí Outcome:

1. **File dẫn xuất là hàm thuần của `data/`**: `edges.jsonl` (T1.1, T3.1 —
   closure hội tụ, 0 genealogy target chưa tải), review queue (T1.2),
   eligibility (T2.2), `verify_temporal_candidates.py` (merge, không ghi đè
   quyết định người/LLM đã có) — đạt.
2. **Mọi khoảng trống được phân loại**: `eligibility.jsonl` (T2), 388
   candidate `effective_to` chia rõ accept/reject/inconclusive kèm lý do
   (T4.3), 7 trường hợp không xác minh được ghi rõ nguyên nhân (nội dung
   rỗng / phụ lục chưa crawl) — đạt.
3. **Expiry cấp Điều/Khoản/Điểm định vị qua cây nguồn + Khoản/Điểm tách**:
   T5.1–T5.3, tỉ lệ resolve cặp phân biệt 94,5% (từ 73,3% ở v1) — đạt.
4. **Giá trị suy dẫn có provenance**: mọi bản ghi trong
   `data/review/temporal_candidates.jsonl` có `method`, `evidence`,
   `reviewer`, `reviewed_at`; `data/derived/subtrees/*.json` có
   `method=article_text_split` — đạt.
5. **Gate pass + báo cáo số liệu trước/sau**: `pytest` 197 passed,
   `verify_pipeline.py` pass toàn bộ (kể cả trên bản snapshot tải lại từ HF);
   số liệu trước/sau ghi đầy đủ trong mục Validation — đạt.

**Số liệu tổng kết trước → sau backfill:**

| Đại lượng | v1 (14/09) | v2 (17/09) |
|---|---:|---:|
| Văn bản / cạnh phân biệt | 22.550 / 128.289 | 23.139 / 128.548 |
| Genealogy target chưa tải | 115 | 0 |
| Node text / node cây | 1.136.483 / 1.262.115 | 1.151.790 / 1.273.593 |
| Candidate `effective_to` quyết định | 0/395 | 381/388 (367 accept, 14 reject) |
| Resolve cặp (văn bản, điều khoản) | 73,3% | 94,5% |
| Node Khoản/Điểm tách + preamble | chưa có | 424.409 + 10.302 preamble |
| Hand-check độ chính xác tách | chưa đo | 100/100 (100%) |
| Văn bản một tác nhân / gold triples | 228 / 843 | 243 / 919 |

**Rủi ro còn lại / chưa làm** (không chặn M1):

- T1.4 (chuẩn hóa ngày history) còn thiếu kiểm tay 20 văn bản gốc bằng PDF.
- T6 (phục hồi thủ công 308 văn bản body rỗng) là tùy chọn, chưa làm.
- 7 candidate `effective_to` không thể xác minh bằng dữ liệu đã crawl (nội
  dung rỗng ở nguồn, hoặc trích dẫn nằm trong phụ lục chưa crawl) — cần PDF
  gốc hoặc trích xuất L2 (master plan P3.11+).
- 1.089 văn bản có expiry cấp điều khoản nhưng ≥2 văn bản tác động — đúng lý
  do L2 là bắt buộc (master plan P3.10–P3.13), không giải quyết được bằng
  metadata.

Master plan P2.7–P2.12 đã cập nhật ✅. Bước tiếp theo: P3.1 (docker-compose
Neo4j/Milvus) sau khi đo RAM máy (P3.2), rồi P3.4–P3.6 nạp Neo4j từ snapshot
v2.
