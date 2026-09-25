# Hướng dẫn gán nhãn ViLexTime

Phiên bản hướng dẫn: **1.0** (khớp `review.guideline_version` trong bản ghi).
Áp dụng cho đợt kiểm chéo D4 (Cohen κ) và mọi lượt kiểm tay sau đó.

## 1. Bạn đang kiểm cái gì

Mỗi dòng là **một câu hỏi được hỏi ở một mốc thời gian** (`as_of`), kèm **đáp án
chuẩn**: nội dung điều khoản có hiệu lực tại mốc đó. Đáp án do máy dựng từ chuỗi
phiên bản, không do LLM viết. Câu hỏi do LLM viết và chưa ai đọc.

Bạn trả lời **một câu duy nhất cho mỗi dòng**:

> Một luật sư đọc câu hỏi, biết ngày `as_of`, và tra đúng văn bản — người đó có
> trả lời **đúng bằng nội dung trong cột đáp án** không, và có trả lời được **chỉ
> một cách** không?

Có → `dat`. Không → `khong_dat` và ghi lý do.

## 2. Nhãn (từ vựng đóng, không thêm mã mới trong đợt kiểm)

| Cột | Giá trị | Ghi chú |
|---|---|---|
| `verdict` | `dat` · `khong_dat` | Cohen κ tính trên cột này |
| `reasons` | một hoặc nhiều mã bên dưới, cách nhau bằng dấu phẩy | Chỉ điền khi `khong_dat` |
| `note` | tự do | Bắt buộc khi có `gold_wrong` hoặc `other` |

Mã lý do:

| Mã | Khi nào dùng |
|---|---|
| `question_ambiguous` | Câu hỏi khớp **nhiều điều khoản** hoặc nhiều mục trong danh sách; đáp án chuẩn chỉ là một trong số đó |
| `question_leaks` | Câu hỏi đã nói ra đáp án, nêu số hiệu/Điều/Khoản, ký hiệu mục ("c)"), hoặc để lộ phiên bản nào |
| `gold_wrong` | Nội dung ở cột đáp án **không đúng** là điều khoản có hiệu lực tại `as_of` (sai phiên bản, vế "trước sửa đổi" thực ra đã là bản sửa, text bị cắt mất phần được hỏi) |
| `group_mismatch` | Câu hỏi không làm được việc của nhóm: T2/T4 không chạm chỗ thay đổi (hai mốc trả lời như nhau); T3 chỉ chạm một lần sửa; T6 hỏi kiểu có/không; T5 hỏi vào phần không đổi |
| `unanswerable_as_asked` | Câu hỏi đúng chủ đề nhưng không thể trả lời bằng đáp án (hỏi "khi nào" mà đáp án không nói thời hạn, hỏi "ai" mà đáp án không nêu chủ thể...) |
| `other` | Lỗi khác — mô tả ở `note` |

## 3. Cách kiểm từng nhóm

Đọc **câu hỏi → mốc → đáp án**, rồi mở link văn bản (cột `source_url`, là văn bản
bị sửa) khi cần kiểm cột đáp án. Cột `note_for_annotator` ghi ngày ký và ngày hiệu
lực của văn bản sửa đổi ở dòng T5.

- **T1** (một phiên bản): kiểm chủ yếu `question_ambiguous` — với mục trong danh
  sách, câu hỏi phải ghim được đúng mục, không phải cả danh sách.
- **T2** (hai phiên bản khác rõ): hai dòng cùng câu hỏi, khác mốc. Câu hỏi phải
  chạm vào chỗ đã đổi; nếu đọc câu hỏi mà hai đáp án đều trả lời được như nhau →
  `group_mismatch`. Kiểm **vế trước** (mốc sớm) với văn bản gốc: nếu văn bản gốc
  trên cổng đã là lời văn sau sửa đổi → `gold_wrong`.
- **T3** (chuỗi ≥ 3 phiên bản): câu hỏi phải tách được mọi mốc, không chỉ mốc đầu
  và cuối.
- **T4** (hai phiên bản gần giống): chỗ đổi thường chỉ là một cụm từ (tên cơ
  quan, số ngày). Câu hỏi phải hỏi đúng vào cụm đó; hỏi chung chung là
  `group_mismatch`. Vế trước kiểm như T2.
- **T5** (hồi tố): mốc sau nằm **trong khoảng hồi tố** — sau ngày có hiệu lực,
  trước ngày ký. Đáp án chuẩn ở mốc đó là **nội dung mới**. Chỉ đánh `gold_wrong`
  nếu văn bản sửa đổi không thật sự có hiệu lực từ ngày đó; việc văn bản có thuộc
  Điều 152 hay không là việc của luật sư (`data/review/t5_documents.tsv`), không
  phải của đợt gán nhãn.
- **T6** (hết hiệu lực một phần): mốc sau có đáp án rỗng và
  `no_answer_reason = provision_repealed`. Đúng khi điều khoản đã bị bãi bỏ trong
  khi văn bản vẫn còn hiệu lực. Câu hỏi không được giả định quy định đang tồn tại.

## 4. Ví dụ

| Câu hỏi | Nhãn | Vì sao |
|---|---|---|
| "Một doanh nghiệp tái xuất hàng hoá thì phải làm thủ tục hải quan tại đâu?" (đáp án: "tại cửa khẩu nhập hoặc cửa khẩu tái xuất") | `dat` | Một cách hiểu, đáp án trả lời trọn |
| "Trong lĩnh vực xử phạt chứng khoán, hình thức xử phạt chính loại c) được quy định như thế nào?" | `khong_dat`: `question_leaks` | Ký hiệu mục "c)" là vị trí, không phải nội dung |
| "Những hành vi nào bị phạt tiền từ 20.000.000 đồng đến 40.000.000 đồng?" (đáp án: một mục b) | `khong_dat`: `question_ambiguous` | Đáp án đúng là cả danh sách |
| T2 — "Chế độ bảo hiểm xã hội đối với dân quân thường trực được xác định ra sao?" với hai đáp án khác nhau về căn cứ áp dụng | `dat` | Chạm đúng khía cạnh đã đổi |
| T4 — câu hỏi về "cơ quan nào" khi chỗ đổi là "Bộ Tài nguyên và Môi trường" → "Bộ Nông nghiệp và Môi trường" | `dat` | Hỏi đúng cụm đã đổi |
| Hỏi "được xác định ra sao" khi đáp án chỉ là tiêu đề Điều ("Điều 12. Các chỉ số…") | `khong_dat`: `gold_wrong` | Nội dung nằm ở nút con; lẽ ra đã bị cờ `answer_in_children` |

## 5. Quy trình

1. Hai người gán nhãn **độc lập**, mỗi người một file (`data/review/crosscheck_A.tsv`,
   `crosscheck_B.tsv`), không trao đổi trong lúc làm. Tên thật không ghi vào
   file; dùng mã `A` / `B`.
2. Không sửa câu hỏi hay đáp án trong file — chỉ điền `verdict`, `reasons`, `note`.
3. Xong cả hai, chạy `python scripts/review/crosscheck.py kappa` để tính κ
   (mục tiêu ≥ 0,6). Nếu thấp hơn: viết lại hướng dẫn ở các điểm hay lệch, tăng
   phiên bản hướng dẫn, kiểm lại (plan, Gói D).
4. Dòng hai người lệch nhau được người thứ ba (hoặc hai người cùng ngồi) hoà giải;
   kết quả ghi ở cột `adjudicated` của file A. **Nhãn thô của từng người được
   giữ nguyên** và phát hành cùng bộ dữ liệu (ADR 0003 §9).
5. Dòng `khong_dat` sau hoà giải: câu hỏi viết lại hoặc dòng bị loại, không lặng lẽ
   sửa đáp án chuẩn — sửa gold là thay đổi MAJOR (ADR 0003 §8).
