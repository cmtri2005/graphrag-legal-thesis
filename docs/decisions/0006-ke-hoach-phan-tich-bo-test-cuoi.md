# 0006 Kế hoạch phân tích cho bộ test cuối

Date: 2026-11-05

## Status

**Proposed, bản nháp.** Phải được CMT và NMT duyệt, chuyển sang Accepted và commit **trước** lần chạy đầu tiên của bất kỳ hệ nào trên bộ test cuối (cổng G3 của `docs/plans/active/master-plan.md`). `scripts/eval/final_run.py` từ chối chạy split `test` khi chưa có commit đó.

Các chỗ ghi `[ĐIỀN Ở G2]`, `[ĐIỀN Ở G3]` được điền bằng số đo thật trước khi duyệt. Không chỗ nào được điền sau khi đã thấy kết quả của bộ test cuối.

ADR này không sửa ADR 0005. Kết luận đã báo của v1.0 và test 2 giữ nguyên theo ADR 0005 và các amendment của nó.

## Context

- ADR 0005 khai báo trước họ XN1–XN9 cho v1.0, rồi amendment 03/11 lặp lại trên test 2 (nhãn LLM). Kết quả: v1.0 có 6/6 kiểm định ủng hộ. Test 2 có XN2, XN3, XN8, XN9 ủng hộ, còn XN1, XN4 không đủ bằng chứng.
- Ngày 05/11, sau khi đã thấy các kết quả này, nhóm quyết định dựng một bộ test cuối do người gán, vì ba lý do đo được: nhãn chưa đáng tin (AC1 0,377; 90/211 dòng v1.0 chỉ có nhãn Codex; test 2 toàn nhãn LLM), đáp án dẫn từ chính đồ thị của hệ, và hệ đã chạy chưa có lai ghép như L4 của đề cương. Việc gọi v1.0 và test 2 là "vòng thử" có từ ngày đó. Không được viết như thể vai này có từ đầu.
- Phản biện ngày 05/11 (`docs/reports/phan-bien-ban-nhap-20261105.md`) chỉ ra:
  - TVER, Verifier và gold cùng dùng cửa sổ hiệu lực của đồ thị, nên TVER = 0 của `b7pp` là do cách dựng;
  - nấc lan truyền đo được bằng 0 ở tầng truy xuất (`b7pp` = `b7plus` mọi nhóm, cả hai bộ);
  - thông báo bãi bỏ của `proposed3` lấy từ cùng sự kiện với gold T6.
- Công trình gần nhất là LawInForce-eCFR và NitiBench+ (`related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md`). Phần còn riêng của đề tài: pháp luật Việt Nam, và phép tách có đối chứng trên cùng dữ liệu giữa lọc theo ngày văn bản và lọc theo khoảng hiệu lực phiên bản.

## Decision

### 1. Dữ liệu

- **Bộ test cuối** chỉ gồm lineage chưa từng có dự đoán của hệ nào trong `runs/`: silver T2, T3 (`data/review/the4/lo1_silver_worksheet.jsonl`) và lô mới T2, T3, T6 (`lo2_moi_worksheet.jsonl`).
- **Điều kiện vào bộ cuối:** A và B gán độc lập theo hướng dẫn 4.0, luật sư chốt dòng lệch, và nhãn cuối là `dat`.
- **Danh sách khóa:** danh sách lineage, sha256 của release và manifest được ghi ở đây trước khi duyệt: `[ĐIỀN Ở G2]`.
- **Dev:** giữ nguyên 151 dòng `dev`, `giua_khoang`, như ADR 0005.
- **Lát khai báo trước** trên `giua_khoang`:

  | Lát | Điều kiện |
  |---|---|
  | `all` | T2, T3, T6 |
  | `all_answerable` | `all`, có đáp án |
  | `t6` | T6 |
  | `t6_unanswerable` | T6, không có đáp án |
  | `t6_ancestor` | T6 bãi bỏ qua nút cha |
  | `t2_near` | T2 gần giống |
  | `qsource_silver`, `qsource_new` | theo quy trình viết câu hỏi |

- **Không gộp** dòng của v1.0 hay test 2 vào bộ cuối. Dòng T6 của hai bộ đó đã được xem, nên chỉ báo riêng với nhãn "đã thấy".

### 2. Hệ và cấu hình bị khóa

- **Generator:** `gpt-4o-mini-2024-07-18` (OpenAI), nhiệt độ 0, `max_tokens` 1024, `seed` 20261109, theo amendment 09/11 của ADR 0004 (Proposed). Qwen3-4B rev `cdbee75` chỉ ở bảng phụ RQ1 và các vòng thử lịch sử, không đặt số cạnh cột chính.
- **Embedding:** `dangvantuan/vietnamese-embedding`, trừ khi X6 trên dev cho R@10 tăng với KTC ghép cặp > 0: `[ĐIỀN Ở G3]`.
- **Thang truy xuất** (F4–F6): `b2ctx → b7 → b7v → b7plus → b7pp`, từ vựng, `k = 20`, như ADR 0005, để so được với v1.0 và test 2.
- **Hệ có sinh câu trả lời:** `b1`, `b2ctx`, `b3`, `b4`, `b5`, `b6`, `b7`, `b7plus`, `b7pp`, `oracle`, `oracle_now` và **P**. Danh sách gốc là `FINAL_GENERATION` trong `src/vilexgraph/framework/systems.py`; bảng cấu hình in bằng `python -m vilexgraph.framework.systems`. Mọi hệ có truy xuất dense chạy ở chế độ lai ghép (`--hybrid`), không reranker.
- **Chỉ chạy trên dev:** `proposed2`, `proposed3` để chọn P; `p2a2`, `p2a3` để mô tả thành phần.
- **Trình bày:** mọi hệ đều chạy. Paper giữ 7 hệ lõi cộng `b1` ở bảng chính và `oracle`, `oracle_now` ở bảng chẩn đoán; khóa luận báo đầy đủ.
- **P** là đúng một hệ, chọn trên dev theo quy tắc khai trước:
  - P là `proposed3` nếu trên dev, `proposed3` − `proposed2` ở `t6_unanswerable` có KTC ghép cặp > 0, **và** trên các dòng có đáp án, cận dưới KTC của hiệu Accuracy ≥ −0,02.
  - Ngược lại, P là `proposed2`.
  - Kết quả áp quy tắc trên dev: `[ĐIỀN Ở G3]`.

### 3. Họ kiểm định xác nhận (Holm, α = 0,05)

| Mã | Câu hỏi | So sánh | Đại lượng | Lát | Dự đoán |
|---|---|---|---|---|---|
| F1 | RQ2, so với RAG phẳng lai ghép | P − `b4` | Accuracy | all | > 0 |
| F2 | RQ2, so với mở rộng đồ thị phi thời gian (`b5` không phải GraphRAG thật; LightRAG báo riêng) | P − `b5` | Accuracy | all | > 0 |
| F3 | RQ2, lỗi sai phiên bản | P − `b4` | `wrong_version` | all | < 0 |
| F4 | RQ3, lọc ngày văn bản | `b7` − `b2ctx` | TV-Recall@1 | all_answerable | > 0 |
| F5 | RQ3, lọc khoảng phiên bản | `b7plus` − `b7` | TV-Recall@1 | all_answerable | > 0 |
| F6 | Giả thuyết đề cương (H0) | `b7pp` − `b7` | TV-Recall@1 | all_answerable | > 0 |
| F7 | T6 | P − `b7pp` | Accuracy | t6_unanswerable | > 0 |

- **F7** chỉ vào họ khi lát có ít nhất 20 lineage. Không đủ thì tự chuyển sang thăm dò; công cụ ghi rõ.
- **H0 chỉ quyết bằng F6.**
- **TVER không còn là kiểm định xác nhận**, vì nó dùng chung cửa sổ của đồ thị với gold. Công cụ vẫn tính nó dưới mã F8, luôn ngoài Holm, như một phép kiểm nhất quán nội bộ.

### 4. Thăm dò và mô tả (ngoài Holm)

- `b7pp` − `b7plus`, Accuracy trên `t6_ancestor`: phép đo duy nhất cho nấc lan truyền. Chỉ được nói lan truyền có tác dụng khi khoảng tin cậy loại trừ 0.
- **TVER theo người:** rút có seed khoảng 100 đơn vị được trích bởi `b2ctx`, `b7`, `b7pp`, P. Người đọc văn bản gốc, không thấy cửa sổ đồ thị, rồi xác định đơn vị đó còn hiệu lực tại mốc hay không. Báo tỷ lệ kèm Wilson.
- **Hai điều kiện cấp sẵn căn cứ:** `oracle` (bản đúng mốc) và `oracle_now` (bản hiện hành), theo nhóm, có T1 của v1.0 làm đối chứng.
- **Khẳng định "đã bãi bỏ":** precision trên dòng có đáp án và recall trên dòng không đáp án, mọi hệ.
- **Các chỉ số khác:** TCS, VCR, MRR, EM/F1.
- **Các lát:** theo miền, theo quy trình câu hỏi, theo mức trùng chữ giữa câu hỏi và đáp án.
- **Về nhãn:** AC1 riêng trên phần A chưa từng thấy (A đã gán 131/168 lineage silver ở vòng 25/10). So nhãn LLM của test 2 với nhãn người trên lô thử.
- **Accuracy T6 của `proposed3`** là cận trên khi đồ thị đúng. Chỉ kết luận trên dòng T6 đã qua gold mù.

### 5. Thống kê

Như ADR 0005 §5: bootstrap theo cụm lineage, B = 10.000, khoảng phân vị 95%, ghép cặp dùng chung lần lấy mẫu lại. Với B = 10.000, p nhỏ nhất khác 0 là 0,0002; p bằng 0 trong file được ghi là "p < 0,0002".

### 6. Quy tắc kết luận

- **Ủng hộ, bác, không đủ bằng chứng:** như ADR 0005 §6.
- **Kết luận chính chỉ lấy từ bộ test cuối.** v1.0 (xác nhận lần 1) và test 2 (lần lặp, nhãn LLM) được báo cạnh nhau, không gộp, không dùng để đổi phán quyết của bộ cuối.
- **Kết luận cho H0 theo F6 của bộ cuối:**

  | F6 bộ cuối | Kết luận cho H0 |
  |---|---|
  | Ủng hộ | Ủng hộ, kèm ghi chú là lần lặp test 2 không đủ bằng chứng |
  | Không đủ bằng chứng | **Không được ủng hộ.** Đề tài theo nhánh tài nguyên và phân tích, dù v1.0 ủng hộ |
  | Bác | Bác |

- **Cỡ mẫu và power:** ghi cạnh mọi phán quyết. Ước lượng với khoảng 150 lineage là MDE khoảng 0,05: `[ĐIỀN Ở G2]`.

### 7. Gold mù và sửa gold

- Gold mù theo B6 (120 + 30 dòng), mù theo từng người (`independent_gold.py` với `--only`). Đạt khi ≥ 114/120 khớp.
- **Dòng mà gold mù cho thấy gold sai:** giữ trong bộ cuối với gold đã sửa, có luật sư chốt, không loại.
- **Lỗi đồ thị phải sửa:** dựng lại release và chạy lại mọi hệ trên dev trước G3. Không sửa sau khi đã chạy test.
- **Báo song song** F1–F6 trên phần gold mù.

### 8. Kết quả đã thấy trước khi viết ADR này

- **Đã thấy:**
  - kết quả test của v1.0 (E1, E3) và test 2 (E1, E3, lần chấm sai và lần chấm lại);
  - mọi kết quả dev (B2, lai ghép, `proposed2`, `proposed3` chưa sinh, X4, tập dượt);
  - phân rã lỗi E7 do máy; hiệu chuẩn lời dặn v2; phản biện 05/11; đối chiếu VBHN.
- **Chưa thấy:** mọi dự đoán trên bộ test cuối; kết quả Colab đợt 2 (niêm phong, xem mục 9).

### 9. Niêm phong Colab đợt 2

Kết quả đợt 2 (các hệ còn thiếu trên v1.0 và test 2) được nhập, lưu sha256 vào `runs/README.md`, nhưng **chỉ chấm sau khi ADR này được commit**. Mục đích: không để kết quả test của `b3`, `b4`, `oracle` và ablation ảnh hưởng đến việc chọn embedding, lai ghép hay P.

### 10. Thay đổi so với ADR 0005

| Thay đổi | Lý do | Đã thấy gì lúc đổi |
|---|---|---|
| Bỏ TVER (XN2) khỏi họ xác nhận | Dùng chung cửa sổ đồ thị với gold | TVER `b7pp` = 0 ở cả hai bộ |
| Thêm `wrong_version` cho RQ2 | Đề cương hỏi việc giảm lỗi sai phiên bản | Kết quả hai vòng thử |
| P thay `proposed` | `proposed` chưa có lai ghép như L4 | Lai ghép và `rel_up` trên dev |
| RQ2 so với `b4` | `b4` là RAG phẳng lai ghép, cùng chế độ truy xuất với P | Không có số test của `b4` |
| Bỏ XN8, XN9 dạng cũ | XN9 với `b1` để trống gần hết là phép so tầm thường; XN8 trộn nhiều yếu tố | Kết quả hai vòng thử |
| T5 ngoài họ | Quá ít dòng | Như ADR 0005 |

RQ1–RQ3 giữ nguyên văn đề cương.

## Alternatives Considered

1. **Giữ v1.0 làm bộ xác nhận chính.** Bị loại: 43% dòng test chỉ có nhãn Codex, AC1 0,377, T3 chỉ 4 lineage.
2. **Gộp ba bộ thành một phân tích tổng hợp.** Bị loại: khác cách gán nhãn và quy trình câu hỏi, và vai các bộ đổi sau khi thấy kết quả.
3. **Giữ TVER trong họ.** Bị loại vì là phép đo do cách dựng.
4. **Chọn P sau khi chạy test.** Bị loại: chọn trên dev theo quy tắc ở mục 2.

## Consequences

Positive:

- Có một lần xác nhận trên nhãn người, với cấu hình đúng L4–L5 của đề cương.
- Mọi bậc tự do đã dùng được ghi ra.

Tradeoffs:

- Bộ cuối nhỏ (dự báo khoảng 150 lineage), nên power cho hiệu cỡ +0,03 thấp. Kết quả "không đủ bằng chứng" là khả năng thật.
- F7 có thể không vào họ vì T6 thiếu. Nấc lan truyền có thể chỉ có bằng chứng thăm dò.
- Kết luận về bãi bỏ chỉ đúng với Qwen3-4B và với đồ thị hiện tại.

## Follow-Up

- G2: điền danh sách lineage, sha256, cỡ mẫu, power.
- G3: điền kết quả áp quy tắc chọn P, generator, embedding; CMT, NMT duyệt; commit; rồi mới chạy test.
- `confirm_vilextime.py --family final` đã khớp mục 3 (05/11): F1–F7, F8 là TVER luôn ngoài Holm.
