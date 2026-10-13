# Hướng dẫn gán nhãn ViLexTime: bản thảo v2.0, phần T6 và chuyển chỗ nội dung

**Trạng thái: ĐÃ GỘP** vào `docs/vilextime-annotation.md` v2.0 ngày 12/10/2026, kèm đổi `GUIDELINE`
trong `scripts/review/crosscheck.py`. File này giữ lại làm hồ sơ: nguồn quyết định, ý kiến luật sư và
hai ví dụ đã đối chiếu với văn bản thô. Bản hướng dẫn mới là bản có hiệu lực khi hai file khác nhau.

## 1. Nguồn quyết định

Cố vấn luật (trao đổi ghi nhận 05/10/2026). Bốn điểm đã chốt, **luật sư xác nhận lại đúng cách
diễn đạt dưới đây ngày 12/10/2026**:

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

**Ngày hỏi và điều khoản chuyển tiếp** (luật sư 12/10/2026, áp cho mọi nhóm). Câu hỏi chỉ nêu ngày t,
không nói sự việc phát sinh khi nào: hiểu mặc định là **sự việc phát sinh tại ngày t**, và trả lời theo
bản có hiệu lực tại t. Điều khoản chuyển tiếp cho hồ sơ, việc *đang thực hiện* tiếp tục theo bản cũ
**không** làm câu hỏi mơ hồ: đáp án vẫn là bản mới. Chỉ khi điều khoản chuyển tiếp buộc chính sự việc
phát sinh tại t theo bản cũ thì đáp án là bản cũ; luật sư không tự chọn bản, mà đọc đúng điều khoản
chuyển tiếp.

## 2. Quy trình cho một dòng T6

Thay cho đoạn T6 của §3 trong v1.2.

1. **Khoản có thật bị bãi bỏ không?** Như v1.2: `provision_repealed` chỉ đúng khi điều khoản bị bãi
   bỏ trong khi văn bản vẫn còn hiệu lực.
2. **Tìm chỗ nội dung có thể còn.** Theo thứ tự: (a) cùng văn bản sửa đổi, cụm "Bổ sung … sau …"
   đi cùng "Bãi bỏ …"; (b) khoản cha hoặc khoản anh em của cùng điều; (c) văn bản khác có hiệu
   lực cùng ngày hoặc được dẫn tới (thông tư thay thế, thông tư hướng dẫn chung).
3. **So bảy yếu tố** giữa quy định cũ và quy định ở chỗ mới. `moved` cần **đạt cả bảy** (luật sư
   12/10/2026):

   | # | Yếu tố | Đạt khi |
   |---|---|---|
   | 1 | Hành vi | giữ nguyên về bản chất |
   | 2 | Đối tượng, chủ thể | giữ nguyên |
   | 3 | Điều kiện áp dụng | giữ nguyên |
   | 4 | Cấu trúc quy định | chỉ đổi vị trí, thời hạn |
   | 5 | Chế tài, hậu quả pháp lý | cùng loại chế tài; **mức** được đổi, không dùng ngưỡng. Đổi loại chế tài hay thêm hình thức phạt bổ sung: không đạt |
   | 6 | Thẩm quyền, hiệu lực pháp lý kế thừa | cùng cơ quan ban hành, hiệu lực pháp lý không thấp hơn. Chuyển sang văn bản thấp hơn hoặc của cơ quan khác: không đạt |
   | 7 | Dẫn chiếu, kỹ thuật chuyển tiếp | có dấu vết nối hai quy định: cùng đợt "Bãi bỏ … Bổ sung …", câu "thay thế", điều khoản chuyển tiếp. Không có dấu vết nào: `unclear`, không tự kết luận |
4. **Gán `norm_continuity`:**

   | Giá trị | Khi nào |
   |---|---|
   | `none` | Không tìm thấy quy phạm kế thừa, hoặc có yếu tố 1–6 không đạt rõ ràng |
   | `moved` | Đạt cả bảy yếu tố ở bước 3 |
   | `unclear` | Không chắc ở yếu tố nào, hoặc yếu tố 7 không có dấu vết. Không tự quyết; chuyển cố vấn |

5. **Ghi `successor`:** văn bản, vị trí và trích đoạn. **Được ghi bằng chữ** khi kho không có điều
   khoản đích (xem ví dụ 1).
6. **Quy tắc gold:**
   - `none`: giữ gold rỗng (`provision_repealed`).
   - `moved`: gold sau ngày bãi bỏ là quy định tại `successor`. Dòng **không còn** là phép thử từ chối.
   - **Khoảng trống** (luật sư 12/10/2026): khoản cũ hết hiệu lực từ ngày A, `successor` có hiệu lực từ
     ngày B > A. Hỏi tại ngày giữa A và B thì **không có quy định**: gold rỗng. Trước khi kết luận
     trống, kiểm bốn điểm: (1) điều khoản chuyển tiếp giữ khoản cũ cho giai đoạn A–B; (2) văn bản cấp
     trên hoặc văn bản khác quy định cùng vấn đề trong giai đoạn đó; (3) `successor` có điều khoản hồi
     tố về A; (4) A và B có thật khác nhau, vì cổng có thể ghi sai ngày hiệu lực. Gặp một trong bốn
     điểm thì không còn trống: ghi vào `note`.
   - `unclear`: tạm loại khỏi bảng chính, giữ ở tập phụ.
7. **`substantive_change`** (đổi mức phạt, phạm vi, điều kiện hay không) **không gán tay**: suy ra từ
   so sánh văn bản khi phân tích.

## 3. Hệ quả cho nhãn người gán

- Dòng T6 có gold rỗng nhưng nội dung đã chuyển chỗ: `khong_dat` với mã **`gold_wrong`**, ghi
  `successor` ở `note`. Không đánh `group_mismatch`.
- Dòng T6 mà người gán B gắn `gold_wrong` vì lý do này (ít nhất 25 dòng trong hàng audit) **không phải**
  gán nhãn sai: chúng là các dòng guideline v1.2 chưa phân biệt được.
- `repeal_mode = ancestor`: quy tắc trên áp dụng khi nút cha bị bãi bỏ nhưng nội dung được đặt lại
  ở chỗ khác (luật sư xác nhận 12/10). Chưa có ví dụ đã kiểm.

## 4. Hai ví dụ đã đối chiếu với văn bản thô (05/10/2026)

Đối chiếu bằng `data/raw/<doc>.json` và bằng kho. Luật sư xác nhận cả hai kết luận ngày 12/10/2026.

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

## 5. Tiêu chí `khong_dat` cho T2 và cặp gần giống (CMT xác nhận 11/10)

Cặp gần giống (`near_identical`, T4 cũ) kiểm như T2. T3 và T5 giữ như v1.2. Mỗi **dòng** (mỗi ngày
hỏi) được gán nhãn riêng; một cặp có thể có một dòng `dat` và một dòng `khong_dat`.

1. **Câu hỏi phải chạm đúng chỗ đã đổi.** Nếu một luật sư trả lời giống nhau ở cả hai ngày thì
   `khong_dat` với `group_mismatch`.
   - Không đạt: "Điều 42 *Nghị định này*" đổi thành "Điều 42 *Nghị định số 27/2019/NĐ-CP*" (27/2019/NĐ-CP):
     cùng một điều của cùng một văn bản, chỉ khác cách viết.
   - Đạt: đổi tên cơ quan ("Tổng cục" thành "Ủy ban"); câu trả lời khác thật.
2. **Câu hỏi chứa sẵn vế trước của đáp án**: dòng ngày trước `khong_dat` với `question_leaks`
   (120/2021/NĐ-CP: đề đã nêu "xã, phường, thị trấn"). Dòng ngày sau vẫn có thể `dat`, vì chữ
   cũ trong đề là cái bẫy kéo về bản cũ.
3. **Đổi chủ thể giữa hai mốc** (25/2010/TT-BNNPTNT Điều 21: từ 18/07/2017 điều này nói về Cục Thú y,
   không còn là Cục được hỏi): đáp án ngày sau không trả lời câu hỏi, đánh `gold_wrong` kèm
   `note`. Ca này hiếm (khoảng 1 trong 290 lineage T2 và T3), nên chỉ cần ví dụ trong mục `gold_wrong`.

Xử lý sau gán nhãn: dòng `khong_dat` sau hoà giải thì viết lại câu hỏi hoặc loại lineage, không sửa
gold âm thầm (v1.2 §5.5). Hai ca đầu viết lại được nếu còn chạm được chỗ đổi; ca 1 kiểu cùng văn bản
đổi cách viết và ca 3 phải loại.

## 6. Còn mở

- Phần pháp lý đã đủ ý kiến luật sư (12/10/2026): §1 bốn điểm, ngày hỏi và điều khoản chuyển tiếp;
  §2 bảy yếu tố và khoảng trống; §3 ca `ancestor`; §4 hai ví dụ. Còn chờ: 19 dòng T5
  (`data/review/t5_luat_su.xlsx`).
- Phát hiện tự động: bộ dò cùng đợt sửa vừa bãi bỏ đoạn A vừa bổ sung đoạn trùng nhiều từ với A bắt
  được kiểu 1; chuyển sang văn bản khác (ví dụ 2) cần so khớp nội dung giữa văn bản, vì **kho không
  có cạnh quan hệ** giữa hai văn bản.
- Phần trích xuất: các câu "Bổ sung điểm … vào sau điểm …" chưa luôn tạo nút mới, nên `successor` có
  thể phải ghi bằng chữ cho nhiều dòng.
- Cách chấm khi gold là điều khoản kế thừa: `accepted_evidence` cần đơn vị của `successor`.
