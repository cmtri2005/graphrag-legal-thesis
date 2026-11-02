# Viết câu hỏi ViLexTime bộ test 2 — phần riêng

Phần trên là quy tắc chung và quy tắc từng nhóm của bộ dữ liệu; đọc phần ứng với `nhom` của mục (T2 → NHÓM T2, T2 gần
giống → NHÓM T2 và NHÓM T4, T3 → NHÓM T3, T6 → NHÓM T6). Khác với phần trên, ở đây bạn làm theo gói:

- Mỗi dòng của `packs/pack_*.jsonl` là một mục: `item`, `nhom`, `dau_vao` (đúng phần "đầu vào" mà quy tắc nhắc tới).
- Ghi `answers.jsonl` ở thư mục này, mỗi mục một dòng JSON: `{"item": "...", "question": "..."}`. Không viết được thì
  `question` là `KHONG_DU_NGU_CANH`.
- Có thêm file `viet_lai.jsonl` thì chỉ làm các mục trong đó, ghi đè kết quả vào file mà lệnh giao. Mỗi dòng có câu đã
  viết (`da_viet`) và lý do bị loại (`ly_do`).

## Câu hỏi không chép lời văn, nhưng vẫn là tiếng Việt chuẩn (kiểm tự động)

Không quá **40%** số tiếng có nghĩa của câu hỏi được nằm trong các phiên bản của điều khoản; vượt thì bị loại. Đây là
trần để câu hỏi không chép lời văn, không phải đích để hạ càng thấp càng tốt: 30–40% là bình thường.

- **Giữ nguyên thuật ngữ pháp lý và tên gọi chuẩn**: ngân hàng, thuế giá trị gia tăng, hóa đơn, thẩm định giá, giấy phép,
  hợp đồng, Bộ Tư pháp. Không đổi thành khẩu ngữ hay từ tự chế ("nhà băng", "biên lai", "đồ mang theo", "người đứng
  đầu ngành tư pháp" đều sai).
- Chỉ đổi cách diễn đạt phần còn lại, bằng văn viết tự nhiên của người đi tra cứu, và rút bớt chi tiết không cần để ghim
  đúng nội dung. Không chép nguyên mệnh đề của điều khoản.
- Đọc lại câu: một luật sư hoặc người dân có viết như vậy không? Không thì viết lại.
- Không đổi nghĩa để né: câu hỏi vẫn phải chạm đúng chỗ thay đổi, chỉ một điều khoản trả lời được, có một đáp án ở mỗi
  mốc. Không viết được trong trần này thì chọn `KHONG_DU_NGU_CANH`.

Chỉ đọc file trong thư mục này. Không mở thư mục cha hay thư mục nào khác trên máy.
