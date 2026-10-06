# Hướng dẫn gán nhãn ViLexTime: bản thảo v2.0, phần T6 và chuyển chỗ nội dung

**Trạng thái: BẢN THẢO, ghi nhận 05/10/2026.** Chưa thay `docs/vilextime-annotation.md` (v1.2) và
chưa đổi `GUIDELINE` trong `scripts/review/crosscheck.py`. Mới có phần T6 và chuyển chỗ. Chưa có
tiêu chí `khong_dat` cho T2, T3, T4, và chưa có phần T5; các phần đó vẫn theo v1.2.

## 1. Nguồn quyết định

Cố vấn luật (trao đổi ghi nhận 05/10/2026). Bốn điểm đã chốt:

1. **Hai loại câu hỏi, hai loại đáp án.** Hỏi theo cấu trúc ("Khoản A còn hiệu lực không?") thì đáp
   án là "đã bị bãi bỏ". Hỏi theo nội dung ("Tại ngày t, quy định X là gì?") thì trả quy phạm đang
   điều chỉnh X, kể cả khi nó đã chuyển sang chỗ khác.
2. **Khoản bị bãi bỏ vẫn là đã bãi bỏ**, dù cơ chế tương tự còn ở khoản khác. Quy phạm tương tự ở
   chỗ khác không làm khoản đó "sống lại".
3. **Đổi mức phạt không tự thân biến thành quy phạm mới. Không đặt ngưỡng "tăng bao nhiêu".** Phải
   đối chiếu hành vi, đối tượng, điều kiện áp dụng và cấu trúc của quy định mới. Nếu hành vi giữ
   nguyên về bản chất, chỉ chuyển vị trí và sửa mức phạt, gán **chuyển chỗ + sửa mức phạt**.
4. **Chuyển sang văn bản khác vẫn là chuyển chỗ**, nếu quy định mới thực sự tiếp tục điều chỉnh
   chính nội dung cũ. Việc nằm ở văn bản khác không tự thân biến nó thành "không còn quy định".
   Sau ngày có hiệu lực, trả lời theo văn bản mới.

**Áp dụng cho ViLexTime.** Mọi câu hỏi của bộ dữ liệu là câu hỏi **nội dung** (`prompts/vilextime/base.md`,
điều cấm số 2: không dẫn Điều, Khoản). Vì vậy quy tắc ở điểm 1 áp cho cả bộ.

## 2. Quy trình cho một dòng T6

Thay cho đoạn T6 của §3 trong v1.2.

1. **Khoản có thật bị bãi bỏ không?** Như v1.2: `provision_repealed` chỉ đúng khi điều khoản bị bãi
   bỏ trong khi văn bản vẫn còn hiệu lực.
2. **Tìm chỗ nội dung có thể còn.** Theo thứ tự: (a) cùng văn bản sửa đổi, cụm "Bổ sung … sau …"
   đi cùng "Bãi bỏ …"; (b) khoản cha hoặc khoản anh em của cùng điều; (c) văn bản khác có hiệu
   lực cùng ngày hoặc được dẫn tới (thông tư thay thế, thông tư hướng dẫn chung).
3. **So bốn trục** giữa quy định cũ và quy định ở chỗ mới: hành vi · đối tượng/chủ thể · điều kiện
   áp dụng · cấu trúc của quy định mới (kể cả mức phạt, thời hạn). Không dùng ngưỡng mức phạt.
4. **Gán `norm_continuity`:**

   | Giá trị | Khi nào |
   |---|---|
   | `none` | Không tìm thấy quy phạm kế thừa: xoá hẳn |
   | `moved` | Hành vi, đối tượng, điều kiện giữ nguyên về bản chất; chỉ đổi vị trí (có thể kèm đổi mức phạt, thời hạn) |
   | `unclear` | Không chắc. Không tự quyết; chuyển cố vấn |

5. **Ghi `successor`:** văn bản, vị trí và trích đoạn. **Được ghi bằng chữ** khi kho không có điều
   khoản đích (xem ví dụ 1).
6. **Quy tắc gold:**
   - `none`: giữ gold rỗng (`provision_repealed`).
   - `moved`: gold sau ngày bãi bỏ là quy định tại `successor`. Dòng **không còn** là phép thử từ chối.
   - `unclear`: tạm loại khỏi bảng chính, giữ ở tập phụ.
7. **`substantive_change`** (đổi mức phạt, phạm vi, điều kiện hay không) **không gán tay**: suy ra từ
   so sánh văn bản khi phân tích.

## 3. Hệ quả cho nhãn người gán

- Dòng T6 có gold rỗng nhưng nội dung đã chuyển chỗ: `khong_dat` với mã **`gold_wrong`**, ghi
  `successor` ở `note`. Không đánh `group_mismatch`.
- Dòng T6 mà người gán B gắn `gold_wrong` vì lý do này (ít nhất 25 dòng trong hàng audit) **không phải**
  gán nhãn sai: chúng là các dòng guideline v1.2 chưa phân biệt được.
- `repeal_mode = ancestor`: quy tắc trên áp dụng khi nút cha bị bãi bỏ nhưng nội dung được đặt lại
  ở chỗ khác. Chưa có ví dụ đã kiểm.

## 4. Hai ví dụ đã đối chiếu với văn bản thô (05/10/2026)

Đối chiếu bằng `data/raw/<doc>.json` và bằng kho. Đây là kiểm của nhóm; cố vấn có thể xác nhận.

**Ví dụ 1. Nghị định 100/2019/NĐ-CP, điểm b khoản 1 Điều 17 → điểm d khoản 2 Điều 17.**
- Nghị định 123/2021/NĐ-CP (ký 28/12/2021, hiệu lực 01/01/2022): mục "Bãi bỏ điểm b khoản 1 Điều 17"
  và mục 10 "Bổ sung điểm d vào sau điểm c khoản 2 Điều 17".
- Nội dung **giống từng chữ**: "Điều khiển xe gắn biển số không đúng quy định; gắn biển số không rõ
  chữ, số; gắn biển số bị bẻ cong, bị che lấp, bị hỏng; sơn, dán thêm làm thay đổi chữ, số hoặc
  thay đổi màu sắc của chữ, số, nền biển".
- Mức phạt: 100.000–200.000 đồng (khoản 1) → 800.000–1.000.000 đồng (khoản 2 sau sửa).
- Kết luận: `moved`, mức phạt đổi.
- **Lưu ý dữ liệu:** kho có khoản 2 Điều 17 chỉ gồm điểm a, b, c. **Điểm d không có nút trong kho**
  (sự kiện chèn điểm mới chưa được áp). Nên `successor` ghi bằng chữ.

**Ví dụ 2. Thông tư 225/2016/TT-BTC, khoản 2 Điều 5 → Thông tư 74/2022/TT-BTC, Điều 3.**
- Khoản cũ: tổ chức thu phí kê khai, nộp phí theo tháng, quyết toán năm. Hết hiệu lực 22/12/2022 khi
  Thông tư 74/2022/TT-BTC có hiệu lực cùng ngày. Thông tư 225/2016 vẫn còn hiệu lực ở các phần khác.
- **Ghi chú của người gán B trỏ tới khoản 2 Điều 3, nhưng nội dung "kê khai, nộp theo tháng, quyết
  toán năm" nằm ở khoản 3 Điều 3.** Khoản 2 Điều 3 quy định nộp tiền phí vào tài khoản phí chờ nộp
  ngân sách.
- Kết luận: `moved`, `successor` = Thông tư 74/2022/TT-BTC Điều 3 khoản 3 (và khoản 2 một phần).
- **Bài học:** con trỏ của người gán cần được kiểm với văn bản đích; con trỏ đúng một nửa vẫn có thể
  dẫn tới đúng quy phạm.

## 5. Còn mở

- Tiêu chí `khong_dat` cho T2, T3, T4. Hướng lệch giữa hai người đổi chiều theo nhóm nên mỗi nhóm cần
  tiêu chí riêng.
- Phát hiện tự động: bộ dò cùng đợt sửa vừa bãi bỏ đoạn A vừa bổ sung đoạn trùng nhiều từ với A bắt
  được kiểu 1; chuyển sang văn bản khác (ví dụ 2) cần so khớp nội dung giữa văn bản, vì **kho không
  có cạnh quan hệ** giữa hai văn bản.
- Phần trích xuất: các câu "Bổ sung điểm … vào sau điểm …" chưa luôn tạo nút mới, nên `successor` có
  thể phải ghi bằng chữ cho nhiều dòng.
- Cách chấm khi gold là điều khoản kế thừa: `accepted_evidence` cần đơn vị của `successor`.
