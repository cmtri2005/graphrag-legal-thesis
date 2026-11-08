# Hòa giải xung đột AI — 07/11/2026

Đã rà 62 trường hợp theo lượt chạy, tương ứng 59 lineage riêng biệt. Có 56 đề
xuất Q1–Q4 đầy đủ (54 lineage); còn 6 trường hợp thuộc 5 lineage chưa chốt đủ
nhãn. Đây là đề xuất AI, `not_verified`; số xác nhận CMT là 0.

Mở [phiếu tổng hợp](reviews/all_conflicts.xlsx), sheet `Xung đột` để xem cả
62 trường hợp; sheet `Cần chốt` chứa 6 trường hợp còn mở. Các workbook riêng
trong `reviews/` dùng định dạng duyệt native của từng lượt. Phiếu tổng hợp
không dùng để nhập trực tiếp bằng CLI phiếu native.

| Kết quả | Trường hợp |
|---|---:|
| Chọn bộ Q1–Q4 của A | 19 |
| Chọn bộ Q1–Q4 của B | 24 |
| Cả hai sai, đề xuất bộ Q mới | 13 |
| Chưa chốt đầy đủ | 6 |

Phạm vi gồm lô thử Opus, silver chunk01, hai lượt chunk02–04, lượt chéo model
chunk05–11, các bất đồng chỉ xuất hiện khi đối chiếu chéo model, và 3 bất đồng
trong 14 câu Sonnet đã có đủ nhãn đôi. Không gán tiếp 16 câu Sonnet chưa có nhãn.
Các lượt và số đo đồng thuận trước hòa giải giữ riêng, không cộng thành mẫu độc lập.

## Năm câu còn mở

- `de0f8ef2`: “bán” → “buôn bán” có đổi phạm vi pháp lý thực chất không (Q2).
- `7d01ec54`: “chưa qua sử dụng” → “mới chưa qua sử dụng” có tạo trạng thái
  thứ ba không (Q2); xuất hiện ở cả lượt Codex và Claude.
- `5400b11e`: câu sửa cụm từ tạo lời văn lặp; thiếu VBHN/đính chính để chốt Q1.
  Q4 đã có căn cứ bị quy phạm cấp cao hơn đè lên, nhưng không lấp Q1 bằng verdict.
- `1089c3ac`: thiếu kỳ tài chính để ánh xạ quy định “kỳ tính thuế từ năm 2012”
  vào mốc 29/02/2012. Đã hỏi CMT; chưa nhận quyết định dùng mặc định năm dương lịch.
- `f8d931e0`: thiếu nguồn chính thức xác nhận riêng thời điểm Chi cục Hàng hải
  và Đường thủy nhận đúng thủ tục trước 14/01/2026. Trang thủ tục hiện tại không
  chứng minh được lịch sử; QĐ2530 đã đọc đủ 14 trang nhưng nói về thủ tục khác.

Chi tiết nguồn, lập luận của A/B và câu hỏi còn thiếu nằm trong
`report.jsonl`, `summary.json` và các receipt dưới `evidence/`. Bản đề xuất đã
được sửa sau khi đọc thêm nguồn được giữ trong `revisions/` kèm correction metadata.

## Runtime và kiểm chứng

Đã thử đúng Claude CLI `--agent legal-adjudicator`; hết hạn mức tuần trước khi
trả nhãn hoàn chỉnh. Sau đó dùng agent Codex native theo cùng spec
`.claude/agents/legal-adjudicator.md` và hai skill mà spec chỉ định. Model kế
thừa phiên, không suy đoán revision. Điều chỉnh công cụ native và lỗi truy cập
được ghi trong `provenance.json` cùng metadata từng lô.

94 tệp gốc và 38 snapshot được kiểm SHA256; nhãn A/B, metric và workbook cũ giữ
nguyên. Các đề xuất đầy đủ cho cùng worksheet có cùng Q1–Q4/reason. Fixture tạm
chứng minh validator từ chối verdict/binding sai và hai đề xuất mâu thuẫn cho
cùng worksheet; fixture không nằm trong dữ liệu nghiên cứu.

```sh
.venv/bin/python data/review/ai_research/2026-11-07_adjudication_all/package_review.py --validate-only
```

Kiểm `SHA256SUMS` từ thư mục này. Script đóng gói từ chối ghi đè phiếu đã xuất.
Không chỉnh hướng dẫn, chọn thêm quy ước pháp lý hoặc ký xác nhận thay CMT.

Friction đã ghi nhận: DNS trong sandbox; Claude hết quota; API có thể chứa
toàn văn văn bản liên quan dài hơn chính văn, nên chỉ dùng
`data.documentContent.content` và kiểm header/số hiệu. Một thay đổi hai dòng
trống không rõ nguồn ở skill được giữ cả hai bản rồi khôi phục đúng hash ban
đầu (`revisions/authority_whitespace/`); không tạo ngoại lệ bỏ kiểm hash.
