---
name: vilextime-ai-labeling
description: Gán và đối soát nhãn AI ViLexTime theo Q1–Q4; giữ nhãn thô độc lập, đo AC1/p_neg/kappa trước hòa giải, không giả nhãn người.
---

## Authority và phạm vi

Đọc `docs/vilextime-dinh-nghia.md` (định nghĩa thắng khi mâu thuẫn),
`docs/vilextime-annotation.md` §1–§5 và §6, và phần liên quan của ADR 0003/0005.
Hiện hành là thẻ 4.0; kiểm lại phiên bản trên đĩa mỗi lượt. Mã/miền giá trị nằm ở
`scripts/review/test2_labels.py`: `GOOD`, `OPTIONS`, `REASONS`, `validate_label`,
`worksheet_sha256`. Không nhập CLI phiếu người để giả chữ ký hoặc thời gian.

Quy trình chính thức hiện tại cấm người gán xem gợi ý AI cho câu đang gán và yêu
cầu luật sư hòa giải. Skill này chỉ tạo nhãn nghiên cứu AI riêng, luôn
`label_origin=ai`, `verification_status=not_verified`; không đủ điều kiện đưa vào
test do người kiểm. Chỉ làm trên lô đã được giao, không tự mở nhãn đối phương.

## Đầu vào và nhãn

Nhận cùng worksheet cho hai agent: `lineage_id`, `question`, `group`, tất cả
`rows`/`as_of`/đáp án/câu dẫn và `sources`. Điều phối cung cấp SHA256 toàn file
và binding từng record bằng hàm `worksheet_sha256`; không bịa digest. Thiếu
binding thì yêu cầu điều phối bổ sung, không tuyên bố nhãn đã được khóa.

- Q1: đáp án đúng nguồn/phiên bản (`dung`, `sai`).
- Q2: hỏi đúng phần thay đổi (`co`, `khong`).
- Q3: câu hỏi rõ, trả lời duy nhất, không lộ đáp án/vị trí (`co`, `khong`).
- Q4: quy phạm khác thay đáp án (`khong`, `co`, `khong_chac`).
- `verdict=dat` chỉ khi Q1=`dung`, Q2=`co`, Q3=`co`, Q4=`khong`; còn lại
  `khong_dat`. Reason chính xác theo bảng `REASONS` cho từng đáp án bất lợi;
  đáp án thuận lợi có reason rỗng. Không chọn reason ngoài taxonomy.

Theo hướng dẫn §5, phân vân vẫn chọn Q1–Q4 tốt nhất, ghi `[phân vân]` ở `note`.
Phân biệt `evidence_status` (`sufficient`, `insufficient`, `unavailable`) với
nhãn đánh giá; có nhãn không chứng minh đã đủ nguồn. Không bịa quote để hoàn
thành phiếu. Q4=`khong_chac` là mức có sẵn, không tự thêm mức cho các Q khác.

Trả một JSON object trên mỗi dòng, đủ các trường:

```json
{"lineage_id":"<id>","labeler":"ai-a hoặc ai-b","label_origin":"ai","verification_status":"not_verified","guideline_version":"4.0","worksheet_sha256":"<binding record do điều phối cung cấp>","q1":"dung","q1_reason":"","q2":"co","q2_reason":"","q3":"co","q3_reason":"","q4":"khong","q4_reason":"","verdict":"dat","quote":"<trích đoạn đã đọc>","search_log":"<đã tìm ở đâu; bắt buộc cho T6 Q4=khong>","note":"","evidence_status":"sufficient","evidence":[{"url":"<URL đã mở>","source_tier":"official|worksheet|secondary|snippet","document_number":"<số hiệu>","provision":"<điều khoản>","as_of":"<ngày>","quote":"<đoạn chứng minh>","accessed_at":"<thời gian truy cập>"}]}
```

Sau JSONL trả provenance riêng: agent/phiên/model thực tế, phiên bản skill và
guideline, input hash, thời gian, công cụ khả dụng/đã dùng, lỗi truy cập, quota,
độ mù. Nếu không biết model revision hay timestamp thì ghi unknown; không suy
đoán. Ví dụ trên chỉ mô tả schema, không được điền nguyên placeholder như dữ liệu.

## Đồng thuận do điều phối tính sau khi khóa cả hai file

- Dùng code để tính, không ước lượng từ lời văn. Tái dùng `gwet_ac1`,
  `cohen_kappa`, `specific_agreement` trong `scripts/review/crosscheck.py` và
  hằng số/nguyên tắc hiện hành của `test2_labels.py`; không đổi identity thành
  A/B để vượt validator phiếu người. Đo trên cùng ID và binding, cùng guideline.
- Báo số yêu cầu, số mỗi bên, số cặp, số thiếu/trùng/nhãn lỗi, nguồn chưa đủ và
  các ID bị loại khỏi phép tính kèm lý do. Tính trên các cặp nhãn hợp lệ, công bố
  độ phủ của cả tập được giao. Nhãn lỗi hoặc thiếu không phải đồng thuận.
- Tính riêng Q1, Q2, Q3, Q4 và verdict: AC1, p_neg, κ, ma trận nhầm lẫn, n;
  thêm theo nhóm và phiên bản hướng dẫn. Q4 giữ ba mức khi tính AC1/κ; p_neg
  gộp `co` và `khong_chac` thành bất lợi. Các Q khác: bất lợi là ngược `GOOD`;
  verdict bất lợi=`khong_dat`.
- Hướng dẫn §5.7: AC1 ≥ 0,80 và p_neg ≥ 0,60; κ báo kèm. Tôn trọng điều kiện
  đánh giá đủ nhãn bất lợi trong master plan G1 và `MIN_NEGATIVES` của code.
  Không có mẫu âm hoặc chỉ số undefined thì `not_evaluable`, không PASS.
  Nếu chỉ kiểm lô thử, không tuyên bố cổng toàn bộ dữ liệu đã đạt.
- Loại lô hiệu chuẩn 0 khỏi số đo chính theo hướng dẫn. Đo **trước hòa giải**;
  hiệu chuẩn lại dùng câu mới, giữ kết quả thất bại và mọi nhãn gốc. Không lọc
  các ca lệch/thiếu nguồn để đạt ngưỡng. Không cam kết trước rằng AI sẽ đạt.
- Báo rõ đây là đồng thuận AI–AI, cùng model có sai số tương quan; không thay
  cho người–người, AI–người hoặc độ đúng pháp lý. Thước đo chọn sau pilot phải
  được mô tả đúng lịch sử, không gọi là preregistered.
