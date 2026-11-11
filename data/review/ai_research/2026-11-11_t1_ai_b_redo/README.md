# AI-B T1 — gán lại theo yêu cầu CMT, 11/11/2026

Đầu ra mới: `b.jsonl` và `raw/b_chunk01.md`, `raw/b_chunk02.md`.
Không ghi đè nhãn, số đo đồng thuận hoặc phiếu CMT của lượt trước.

- 60/60 nhãn hợp lệ: 44 `dat`, 16 `khong_dat`.
- 49 `sufficient`: 36 `dat`, 13 `khong_dat`.
- 11 `insufficient`: 8 `dat`, 3 `khong_dat`. Xem `pending_evidence.tsv`.
- Tất cả là `label_origin=ai`, `verification_status=not_verified`.
  `dat` không có nghĩa là đủ nguồn hoặc được người xác nhận.

58 toàn văn chính thức được tải trực tiếp qua API CSDL quốc gia; bản JSON,
bản đọc và hash nằm trong `evidence/` và `source_receipts.json`.
Đã đọc điều hiệu lực, đối chiếu nguyên văn đáp án và kiểm các câu hỏi;
20 lượt tra web được giữ nguyên trong `web_receipts.json`.
Đã đọc riêng Quyết định 1317/QĐ-BTC: chỉ đính chính các Điều 11, 13, 17 của
Thông tư 58/2012/TT-BTC, không tác động khoản 7 Điều 7 trong phiếu.

11 ca chưa xác minh được ngày đăng Công báo bằng bản gốc/thuộc tính gốc;
không dùng `effFrom`, `effTo` hay ngày trong worksheet để giả chứng minh.
Các câu Q1–Q4 ở đó vẫn là lựa chọn tốt nhất kèm `[phân vân]`.
Tra tác động có giới hạn, chưa phải rà soát pháp lý toàn diện.

**Độ mù:** phiên này không đọc nhãn AI-A. Tuy nhiên đã thấy một phần nhãn
AI-B lượt trước trong lịch sử hội thoại; đây là gán lại cùng phiên, không phải
một lượt gán mù mới. Quyền truy cập nguồn cũng khác lượt đầu (tải qua shell
được cấp quyền thay cho WebFetch bị lỗi). Khi so sánh phải giữ hai giới hạn này.
Model là Codex trong phiên hiện tại, không xác định được revision chính xác.

`decisions.json` chứa từng quyết định do annotator đưa ra; `export_labels.py`
chỉ chuyển định dạng và kiểm tra. Chạy lại kiểm tra, không gọi model/network:

```sh
.venv/bin/python data/review/ai_research/2026-11-11_t1_ai_b_redo/export_labels.py
```

`validation.json` chứng minh đủ ID/binding/schema và quote có trong nguồn đã
tải, không chứng minh độ đúng pháp lý. `temporal_checks.jsonl` lưu lời văn
hiệu lực và ngày tính từ lời văn. `draft_attempts/serialization_v1` giữ lần
xuất nháp có lỗi bắt ngày văn bản dẫn chiếu khi điều hiệu lực dùng ngày tương
đối; đã sửa trước bàn giao, không đổi Q1–Q4. Xem đầy đủ `provenance.json`.

Chưa ghép AI-A, đo lại AC1, dựng phiếu CMT hoặc thay nhãn người. Các số đo và
phiếu trong thư mục lượt trước không đại diện cho file B mới này.
