# REFACTOR_PLAN: việc còn lại của khóa luận sau G4

Date: 2026-11-13

## Status

Active. Lập theo yêu cầu của CMT ngày 13/11/2026, sau audit `docs/reports/research-audit-20261113.md`.
Plan này là phần nối của `master-plan.md` cho giai đoạn sau G4; không thay ADR nào.

## Outcome

Khóa luận có kết luận tin được và quy kết đúng: lợi ích đến từ đâu, thước đo độc lập với hệ đến đâu,
phần nào của đề cương đã đạt, phần nào lệch và vì sao.

## Context

- Kết quả G4: `runs/final_g4_20261112/` (F1–F6 ủng hộ, F7 không đủ bằng chứng, hai lần chạy giống nhau).
- Audit và phán quyết: `docs/reports/research-audit-20261113.md` (mục 1–8).
- Quy tắc phân tích: `docs/decisions/0006-ke-hoach-phan-tich-bo-test-cuoi.md`.
- Bộ test cuối đã xem. Mọi phân tích mới trên bộ này là **thăm dò hậu nghiệm**, trừ việc đã khai trong ADR 0006.

## Scope

In scope: sáu nhóm việc dưới đây.

Out of scope: đổi P, đổi prompt hay cấu hình hệ đã khóa; sửa nhãn, gold, scorer; viết lại ADR đã Accepted.

## Approach

Thứ tự: Nhóm 2 → Nhóm 1 (song song, cần người) → Nhóm 3 → Nhóm 6 → Nhóm 4, 5 (chỉ khi mở vòng đánh giá mới).

### Nhóm 1. Làm cho thước đo tin được (cần người)

| # | Việc | Xong khi |
|---|---|---|
| 1.1 | Gold mù do người đọc trên chính bộ test cuối: 60–80 dòng rút phân tầng từ 156 lineage, đủ 23 T6 | Có tỷ lệ khớp **thô trước phân xử** và sau phân xử, Wilson; F1–F6 tính lại trên phần này (ADR 0006 §7) |
| 1.2 | Nhãn có người độc lập: người thứ hai gán mù một mẫu; luật sư kiểm ngẫu nhiên 30 dòng `dat` (plan N1) | Có đồng thuận người–AI và tỷ lệ luật sư đồng ý |
| 1.3 | TVER theo người, khoảng 100 trích dẫn (ADR 0006 §4) | Có tỷ lệ kèm Wilson |
| 1.4 | M2: 100 truy vấn đối chiếu tay | Có số, hoặc ghi rõ không làm |
| 1.5 | Người chấm 100 câu trả lời (`b1`, `b4`, `proposed2`) | Có độ khớp scorer–người; đủ căn cứ để dùng hoặc bỏ LLM giám khảo |
| 1.6 | Mã hóa lỗi E7 bằng người | Phiếu `data/review/e7/` có nhãn người |
| 1.7 | Xem lại G002 và quy ước `dong_y` của gold mù đợt 1 | Có ghi chú lý do từng dòng lệch lời văn |

### Nhóm 2. Quy kết đúng lợi ích đến từ đâu

| # | Việc | Chi phí | Loại | Trạng thái |
|---|---|---|---|---|
| 2.1 | So trực tiếp `proposed2` với `b7plus` và `b7pp`, cả hai lần chạy | 0 | Thăm dò hậu nghiệm | xem Progress |
| 2.2 | Chạy `b7v` chỉ truy xuất trên bộ cuối; báo `b7v − b7`, `b7plus − b7v` | 0 | Đã khai ở ADR 0006 §2, chạy sau khi thấy kết quả | xem Progress |
| 2.3 | T6: precision, recall của khẳng định "hết hiệu lực"; lệnh bãi bỏ có vào prompt hay không | 0 | Precision/recall đã khai ở ADR 0006 §4 | xem Progress |
| 2.4 | Mọi hiệu ghép cặp của bảng mô tả báo ở cả hai lần; đánh dấu hiệu đổi dấu hoặc đổi kết luận | 0 | Thăm dò hậu nghiệm | xem Progress |
| 2.5 | Bảng hạng của căn cứ gold so với Accuracy; phân tầng theo người viết câu hỏi, miền; độ nhạy khi bootstrap theo văn bản | 0 | Thăm dò; lát theo miền và quy trình câu hỏi đã khai ở ADR 0006 §4 | xem Progress |
| 2.6 | Hai baseline mới: `bvnone` (lớp phiên bản, không lọc) và `bvdate` (như trên, in khoảng hiệu lực vào prompt) | khoảng 1–1,5 USD | **Cấu hình mới sau khi đã thấy test**: cần amendment ADR 0006, chọn trên dev, ghi thăm dò | xem Progress |

### Nhóm 3. Lấp phần đề cương còn thiếu

| # | Đề cương hứa | Hiện có | Cần làm |
|---|---|---|---|
| 3.1 | RQ1, vế LLM không truy xuất | `b1` gần 0 vì thước đòi chép đúng lời văn | 2–3 LLM; chấm tỷ lệ sai phiên bản bằng người hoặc giám khảo đã hiệu chuẩn (phụ thuộc 1.5) |
| 3.2 | Bảng 1: T1 250, T2 400, T3 200, T4 150, T5 50, T6 100 | Bộ cuối: T2 127, T6 23, T3 6, T1 43 (đáp án ngắn hỏng), không có T5 | Amendment sửa đáp án ngắn T1 rồi chấm lại; bổ sung T3, T5, T6 có kiểm; báo số theo tầng chất lượng |
| 3.3 | So với GraphRAG phi thời gian | `b5` là mở rộng một bước tự xây | LightRAG/GraphRAG thật trên tập con, hoặc ghi vào bảng lệch đề cương |
| 3.4 | Thí nghiệm chuyển miền | Chưa có | Bảng theo miền (2.5 cung cấp số); ghi lệch |
| 3.5 | Kiểm chứng snapshot | M2 chưa đạt | Như 1.4 |
| 3.6 | Giao diện minh họa | `scripts/demo.py` | Chạy và kiểm trước khi bảo vệ |
| 3.7 | Độ bền | Một generator | Thêm một generator khác họ ở bảng phụ |

### Nhóm 4. Nâng chất kho phiên bản (cần vòng đánh giá mới)

| # | Việc | Căn cứ |
|---|---|---|
| 4.1 | Phân tích 2.846 cặp sự kiện bị sót theo ba nhóm nguyên nhân, nâng độ phủ áp dụng (hiện 3.238/8.046 = 40,2%) | `docs/reports/g2-recall-m2-20261109.md` |
| 4.2 | Mở rộng đối chiếu với văn bản hợp nhất (hiện khớp 80% trên 51 văn bản) | Chương 3 mục 3.5 |
| 4.3 | Một bảng phễu duy nhất từ dữ liệu cổng đến corpus | Chương 3 mục 3.2 ghi thiếu |
| 4.4 | Sau khi sửa đồ thị: dựng lại bộ dữ liệu, chạy lại mọi hệ trên bộ test mới | ADR 0006 §7 không cho sửa sau khi chạy test |

### Nhóm 5. Nâng hệ truy vấn (không bắt buộc, cần vòng đánh giá mới)

| # | Việc | Ghi chú |
|---|---|---|
| 5.1 | Reranker, vùng ứng viên sâu hơn, embedding tốt hơn, áp đều cho mọi hệ | Trần khoảng +0,10 (audit mục 8.2). Reranker đã cắt 05/11; mở lại là quyết định của CMT |
| 5.2 | Nhóm câu hỏi cần đi theo dẫn chiếu tại đúng mốc, rồi lan truyền trên đồ thị lúc truy vấn | Dữ liệu mới, vòng gán nhãn mới |
| 5.3 | Mọi hệ mới chỉnh trên dev, đo trên bộ test mới | Bộ cuối đã xem |

### Nhóm 6. Viết và sổ sách

| # | Việc |
|---|---|
| 6.1 | Cập nhật chương 4, 6, 7 và paper theo G4 và quy trình nhãn thật (chương 6 còn 34 chỗ `[CHỜ]`, chương 2 còn 9 chỗ `[CẦN]`) |
| 6.2 | Bảng lệch so với đề cương; phụ lục khai báo AI |
| 6.3 | Định vị: đồ thị đóng vai offline; không gọi `b5` là GraphRAG; không nói "đầu tiên" |
| 6.4 | Đọc bản gốc các nguồn mới xem tóm tắt; kiểm NitiBench+ và mục bib FiscalQA |
| 6.5 | Dòng G4 trong `runs/README.md`; sửa trạng thái "NHÁP" ở `data/vilextime_final/`; NMT xác nhận ADR 0004, 0006 |
| 6.6 | Số hậu nghiệm của audit tính lại bằng script và qua `evidence-gate` trước khi trích |

### Nháp amendment ADR 0006 cho việc 2.6 (CHƯA có hiệu lực, chờ CMT duyệt)

Chỉ khi CMT duyệt đoạn này mới chép vào cuối ADR 0006, commit, rồi mới chạy trên bộ cuối.

> **Amendment 2026-11-13: hai baseline thăm dò sau khi đã thấy kết quả bộ cuối.**
> - **Đã thấy gì:** toàn bộ kết quả G4 (hai lần chạy), phân tích hậu nghiệm ở `runs/posthoc_g4_20261113/attribution.json`, và kết quả dev của hai hệ dưới đây.
> - **Hệ thêm:** `bvnone` (lớp B, lai ghép, không lọc thời gian, không mở rộng, không Verifier) và `bvdate` (như `bvnone`, mỗi đoạn trong prompt có thêm một dòng khoảng hiệu lực đã lan truyền). Cùng generator, prompt hệ thống, `k`, seed và hai lần chạy như ADR 0006 §2, §5b. Định nghĩa ở `src/vilexgraph/framework/systems.py` (`POSTHOC`).
> - **Câu hỏi:** RAG phẳng được đọc cùng kho phiên bản thì còn kém bao nhiêu; cho model thấy ngày hiệu lực thì có thay được bộ lọc cứng không.
> - **Phép so, đều là thăm dò, ngoài Holm, không có phán quyết:** Accuracy và `wrong_version` trên `all` của `bvnone − b4`, `bvdate − bvnone`, `b7plus − bvdate`, `proposed2 − bvdate`; báo ở cả hai lần chạy.
> - **Không đổi:** P, F1–F7, phán quyết đã báo, scorer, gold, prompt của các hệ đã khóa.
> - **Cách đọc đã khai trước:** nếu KTC của `b7plus − bvdate` chứa 0 ở cả hai lần thì viết "không thấy khác biệt lớn hơn độ rộng KTC giữa lọc cứng và để model tự chọn theo ngày"; nếu loại 0 về phía dương ở cả hai lần thì viết "lọc cứng trước khi xếp hạng còn giá trị riêng".

### Kết quả Nhóm 2 (13/11, thăm dò hậu nghiệm)

Nguồn: `runs/posthoc_g4_20261113/attribution.json`, `attribution.txt`; 10.000 lần lấy mẫu theo lineage; Accuracy tính lại khớp `all.score.json` cả hai lần (assert trong script).

**2.1 Phần của đồ thị trực tuyến (Accuracy, `all`, 318 dòng):**

| So sánh | Lần 1 | Lần 2 |
|---|---|---|
| `proposed2 − b7plus` | +0,013 [−0,009; +0,035] | +0,016 [−0,006; +0,038] |
| `proposed2 − b7pp` | +0,006 [−0,016; +0,028] | 0,000 [−0,016; +0,016] |
| `b7pp − b7plus` | +0,006 [−0,013; +0,025] | +0,016 [−0,003; +0,035] |

Bootstrap theo văn bản (132 văn bản) cho cùng kết luận. Trên `t6_unanswerable` (23 dòng) `proposed2 − b7plus` = +0,174 [+0,043; +0,348] ở cả hai lần; `t6_ancestor` (9 dòng) KTC chạm 0.

**2.2 Thang truy xuất có `b7v` (TV-R@1, `all_answerable`, 295 dòng; truy xuất tất định, một lần):**

| Nấc | Hiệu |
|---|---|
| `b7 − b2ctx` (F4) | +0,078 [+0,049; +0,110] |
| `b7v − b7` | **−0,044 [−0,072; −0,019]** |
| `b7plus − b7v` | **+0,159 [+0,120; +0,199]** |
| `b7pp − b7plus` | 0 |

Đọc: lời văn hợp nhất mà không lọc theo khoảng còn **kém hơn** lớp gốc, vì mọi phiên bản cũ cùng vào ứng viên. Toàn bộ lợi ích của F5 đến từ bộ lọc khoảng phiên bản áp trên kho phiên bản; cần cả hai.

**2.3 Khẳng định "hết hiệu lực" (lần 1; lần 2 gần như trùng):** `proposed2` 11 lần, đúng 7, sai 4 (precision 0,64, recall 7/23); lệnh bãi bỏ vào prompt 12/23, đúng 5 trong 12. `b2ctx` 36 lần, sai 29. `oracle` 23 lần, đúng 22.

**2.4 Ổn định giữa hai lần:** `b5 − b4` **đổi dấu** (−0,013 [−0,025; −0,003] rồi +0,016 [+0,003; +0,031]); `b6 − b5`, `b6 − b4` không ổn định. Các hiệu ≥ 0,13 giữ chiều và kết luận.

**2.5 Hạng của căn cứ đúng (`proposed2`, lần 1, 295 dòng có đáp án):** hạng 1: 102/107; 2–5: 64/81; 6–10: 26/36; 11–20: 8/20; sau 20: 1/3; không có: 4/48. Theo người viết câu hỏi: Codex 0,507 (144 dòng), Claude 0,775 (138), DeepSeek 0,889 (36). Theo miền: `khac` 0,632 (220), doanh nghiệp–đầu tư 0,628 (43), giao thông 0,829 (41), thuế 0,857 (14).

**2.6 Hai baseline mới, chỉ dev (151 dòng `giua_khoang`, gồm T1; hai lần gọi API):**

| Hệ / so sánh | Accuracy lần 1 | Accuracy lần 2 | Ghi chú |
|---|---|---|---|
| `b4` | 0,358 | 0,371 | lớp gốc, không lọc (số tập dượt G3) |
| `bvnone` | 0,384 | 0,397 | lớp phiên bản, không lọc |
| `bvdate` | 0,424 | 0,450 | như trên, in khoảng hiệu lực; nói "hết hiệu lực" 43 và 37 lần (`bvnone` 4–5, `b7plus` 3) |
| `b7plus` | 0,695 | 0,695 | lọc cứng theo khoảng phiên bản |
| `bvnone − b4` | +0,026 [−0,02; +0,08] | +0,026 [−0,01; +0,07] | |
| `bvdate − bvnone` | +0,040 [−0,02; +0,10] | +0,053 [−0,01; +0,12] | sai phiên bản giảm 0,424 → 0,094 |
| `b7plus − bvdate` | **+0,272 [+0,19; +0,36]** | **+0,245 [+0,16; +0,33]** | |

Nguồn: `runs/posthoc_g4_20261113/dev/{r1,r2}/baselines.{txt,score.json}`; `b4`, `b7plus`, `proposed2` lấy từ `runs/final_rehearsal_g3_20261112/{r1,r2}/dev/`. Định dạng 151/151, cắt cụt 0.

Đọc (theo cách đọc đã viết trong nháp amendment, **trên dev**): KTC của `b7plus − bvdate` loại 0 về phía dương ở cả hai lần, nên lọc cứng trước khi xếp hạng có giá trị riêng; cho model thấy ngày hiệu lực chỉ giảm trích sai phiên bản, nhưng model lại khẳng định "hết hiệu lực" bừa nhiều hơn. Chưa có số trên bộ cuối; muốn có phải duyệt amendment.

## Risks And Recovery

- **Phân tích hậu nghiệm bị đọc như xác nhận.** Mọi file kết quả của Nhóm 2 ghi rõ "thăm dò, sau khi đã thấy test"; không đổi phán quyết F1–F7.
- **Cấu hình mới chạm test.** 2.6 chỉ chạy trên bộ cuối sau khi amendment ADR 0006 được CMT duyệt và commit.
- **Lẫn artifact.** Kết quả mới nằm ở `runs/posthoc_g4_20261113/`; không ghi vào `runs/final_g4_20261112/`.
- Hoàn tác: xóa thư mục run mới và revert commit của plan này; không có dữ liệu gốc nào bị sửa.

## Progress

- [x] 13/11 Lập plan.
- [x] 13/11 2.1–2.5: script `scripts/eval/posthoc_g4.py` (dùng lại `confirm_vilextime.run`, `t6_breakdown.event_rank`), test `tests/test_posthoc_g4.py`. Tự kiểm trong script: Accuracy tính lại khớp `all.score.json` của hai lần; F4, F5 dùng cùng seed với `confirm.json`.
- [x] 13/11 2.1–2.5 chạy xong (`run_after_b7v.sh` bước attribution); 2.2 `b7v` truy xuất xong 361/361, exit 0. Kết quả ở mục "Kết quả Nhóm 2".
- [x] 13/11 2.6 trên dev: xuất prompt, gọi API hai lần, chấm (`run_after_b7v.sh`, xong 07:45:56 UTC, exit 0). Phần bộ cuối chờ CMT duyệt amendment.
- [x] 13/11 2.6 (phần code): thêm `bvnone`, `bvdate` vào `systems.py` (`POSTHOC`, ngoài `FINAL_GENERATION`), dòng khoảng hiệu lực trong `generate.build_prompt` (mặc định tắt, prompt các hệ đã khóa không đổi), nối ở `colab_b1.export_prompts`; chặn đường sinh trực tiếp của `run_vilextime.py` cho `bvdate`. Test: `tests/test_rag_generate.py`, `tests/test_rag_systems.py`. Bộ test: 777 passed.

## Decisions

- 2026-11-13 (CMT): gom sáu nhóm việc vào file này và làm Nhóm 2 ngay.

## Validation

- Mỗi số của Nhóm 2 truy được về một file trong `runs/posthoc_g4_20261113/` kèm hash đầu vào.
- Lệnh nền: `.venv/bin/python -m pytest -q`, `git diff --check`.

## Result

Chưa hoàn tất.
