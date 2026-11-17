# Nguyên nhân của ba vấn đề còn mở (17/11/2026)

CMT yêu cầu ngày 17/11. Nhãn: **[XM]** đã đo trong repo; **[SL]** suy luận; **[GT]** giả thuyết, phải đo.
Mọi số là hậu nghiệm và mô tả, tính trên artifact G4 có sẵn, không chạy lại hệ nào.

## 1. Khoảng cách 0,667 (hệ đề xuất) so với 0,956 (oracle)

**Sửa một câu nói sai trước đó:** "khoảng cách nằm ở xếp hạng" chỉ đúng một phần.

Phễu lỗi của `proposed2`, lát `all`, 318 dòng, lần 1 [XM]. Script: `runs/gap_analysis_20261117/funnel.py`. Kết quả: `funnel_r1.json` và `funnel_r2.json`; lần 2 cho cùng hình dạng.

| Vị trí bản gold trong 20 đoạn đưa vào lời nhắc | Số dòng | Sai | Tỷ lệ đúng |
|---|---|---|---|
| Hạng 1 | 107 | 5 | 95% |
| Hạng 2–5 | 81 | 17 | 79% |
| Hạng 6–20 | 59 | 24 | 59% |
| Không có trong top 20 | 48 | 44 | 8% |
| Dòng không có đáp án (T6, đã bãi bỏ) | 23 | 16 | 30% |
| **Tổng** | **318** | **106** | **66,7%** |

`oracle` đúng mà hệ sai ở 96 dòng (ngược lại 4; hiệu ròng 92; lần 2: 98). Chia theo nguyên nhân (sửa theo evidence-gate 17/11):

1. **Truy xuất hụt hẳn (41 dòng).** Bản gold không nằm trong top 20, kể cả khi bộ lọc đã loại hết bản không hiệu lực. Chỉ 3/41 dòng có điều/khoản cha nằm trong top 20, nên phần lớn không phải lỗi chọn sai cấp (khoản thay vì điểm). Nguyên nhân [SL]:
   - Câu hỏi do LLM viết theo luật "không nhắc thời gian, diễn đạt lại thành tình huống" (`prompts/vilextime/base.md`). Từ ngữ của câu hỏi vì vậy xa lời văn điều khoản.
   - Kho có khoảng 1,48 triệu đơn vị, rất nhiều điều khoản cùng mẫu câu ("Hồ sơ gồm…", "Trong thời hạn … ngày làm việc").
   - Trên dev, gold nằm trong top 100 ở 96–100% dòng T2 (`runs/rerank_pool_dev_20261115/`). Vậy phần lớn gold có trong vùng ứng viên nhưng bị xếp dưới hạng 20. Đây vẫn là xếp hạng, nhưng ở bước truy xuất đầu, không phải chọn giữa các bản.
2. **Có gold nhưng trả lời sai (37 dòng có gold ở hạng 2–20 và oracle đúng: 34 nội dung khác, 2 sai phiên bản, 1 từ chối).** Tỷ lệ đúng giảm dần khi gold xuống hạng: 95% → 79% → 59%. Model lấy nhầm khoản anh em hoặc câu chung chung của cùng văn bản. Ví dụ: hỏi chủ thể lập báo cáo tháng về cung cấp điện, model trả lời công ty điện lực tỉnh thay vì đơn vị điều độ.
3. **Không nhận ra điều khoản đã bãi bỏ (15 dòng oracle đúng; 16 dòng hệ sai).** Đây không phải lỗi xếp hạng: hệ vẫn trả lời thay vì nói "đã hết hiệu lực". Kiểm F7 không đủ bằng chứng.
4. **Đưa đúng hạng 1 mà vẫn sai (3 dòng oracle đúng)**, cộng một phần có thể do scorer quá chặt. Ví dụ "07 ngày" và "7 ngày", "02 bộ" và "02 bộ hồ sơ". Chấm tay 14/11 có 4/100 dòng lệch (scorer chấm sai một câu người cho là đúng), nhưng phiếu 33 câu đảo một trong 4 dòng đó, và riêng `proposed2` chỉ lệch 1/33. Độ lệch riêng cho `proposed2` chưa đo [SL].

**Hướng xử lý (chưa làm):** reranker (đã bỏ 16/11 vì hết quota; trên dev MRR `b4` tăng từ 0,536 lên 0,696); đưa ít đoạn hơn khi điểm cao; bước kiểm bãi bỏ riêng cho T6. Nếu làm, phải khai là hậu nghiệm.

**Viết trong paper:** khoảng cách đến oracle chia gần đều giữa (a) bước truy xuất đầu không đưa được gold vào top 20 và (b) gold có trong ngữ cảnh nhưng bị đoạn khác lấn. Phần còn lại là dòng bãi bỏ. Lọc phiên bản đã xử lý gần hết lỗi *chọn bản* (sai phiên bản của `proposed2` khoảng 1%), nên phần còn lại là bài toán truy xuất văn bản thông thường.

## 2. Hệ giả định người dùng cho sẵn ngày

Hiện trạng [XM]:
- Ngày được đưa vào hệ như một trường riêng (`as_of`). 0/722 câu hỏi của tập test có ngày hay năm trong chữ, vì đây là luật viết câu hỏi (`base.md` mục 1).
- `as_of` được định nghĩa là ngày tính hiệu lực pháp lý, coi sự việc phát sinh tại ngày đó. Điều khoản chuyển tiếp không làm đổi đáp án (`prompts/vilextime/agent_kiem.md` mục 1).
- T5 (hồi tố, văn bản đã ký nhưng chưa có hiệu lực) không có trong test.

Nguyên nhân là **quyết định thiết kế để cô lập biến**, không phải lỗi. Muốn đo hệ có chọn đúng bản hay không thì phải cố định ngày. Nhưng bài toán thật còn hai bước chưa ai đo:

1. **Lấy ngày từ câu hỏi.** Người dùng nói "năm 2019 tôi bị phạt…", "hiện nay", "trước khi luật mới có hiệu lực", hoặc không nói gì.
2. **Ngày nào mới là ngày áp dụng: đây là câu hỏi pháp lý, không phải trích xuất.** Ngày xảy ra hành vi khác ngày xử lý. Có quy định chuyển tiếp. Có nguyên tắc áp dụng văn bản có lợi cho người vi phạm trong xử lý vi phạm hành chính. Có văn bản hồi tố. [SL; phải tra điều luật cụ thể trước khi viết vào khóa luận.]

**Hệ quả:** số 0,667 là cận trên của hệ trong thực tế, ở điều kiện ngày đúng. Lọc cứng còn khuếch đại sai ngày: ngày sai thì bộ lọc loại luôn bản đúng.

**Viết trong paper:** nêu rõ là giả định của bài toán (task assumption) ở phần định nghĩa nhiệm vụ, không chỉ ở Limitations. Hướng sau: lát câu hỏi có ngày trong chữ, và đo độ nhạy khi ngày lệch ±k ngày quanh mốc chuyển [GT].

## 3. Kho chỉ đúng tới đâu việc dựng từ lệnh sửa đổi đúng tới đó

Số đã có [XM]:
- Bảng corpus trong paper: lệnh được áp dụng đúng 58/60 (mẫu cũ). Khớp nguyên văn với văn bản hợp nhất 80,0%. **Chỉ 40,2% cặp hết hiệu lực mà cổng vbpl ghi ở mức văn bản có lệnh áp dụng được ở mức khoản.** 1.109/8.046 cặp không có lệnh nào nhắm vào văn bản.
- Gold mù 105 lineage: 3 lineage kho sai (2 bỏ sót sửa đổi, 1 bỏ sót bãi bỏ: TT 36/2026/TT-BXD).

Nguyên nhân:
1. **Độ chính xác cao, độ phủ thấp.** Lệnh nào bắt được thì gần như đúng, nhưng nhiều thay đổi không bắt được. Các dạng khó [SL]:
   - "thay thế cụm từ X bằng Y" rải nhiều điều;
   - bãi bỏ cả văn bản bằng một câu ở văn bản khác;
   - văn bản sửa đổi không có trên vbpl hoặc chưa cào;
   - định vị cấu trúc mơ hồ (sự kiện bị xếp hàng chờ duyệt, không đoán).
2. **Một nguồn duy nhất.** Văn bản hợp nhất dùng để đối chiếu cũng lấy từ vbpl, nên không phải kiểm độc lập.
3. **Thiên lệch chọn mẫu, điểm quan trọng nhất [SL].** Dòng benchmark được sinh từ *các lần chuyển phiên bản mà kho đã thấy*. Một sửa đổi kho bỏ sót thì không bao giờ thành câu hỏi. Vì vậy:
   - Benchmark không đo được lỗi bỏ sót của kho. Tỷ lệ 3/105 chỉ đo trên các điều khoản kho đã biết là có thay đổi.
   - Ngoài benchmark, với một điều khoản bị bỏ sót sửa đổi, hệ sẽ lọc rất "tự tin" và trả về bản cũ như thể đang có hiệu lực. Lọc cứng biến lỗi kho thành lỗi im lặng.

**Viết trong paper:** tách hai câu. (a) Trong phạm vi các thay đổi kho đã ghi, lọc theo khoảng hiệu lực sửa gần hết lỗi sai phiên bản. (b) Độ phủ sự kiện là giới hạn chính khi dùng thực tế: 40,2% cặp hết hiệu lực có lệnh áp dụng được. Hướng sau: đo độ phủ bằng mẫu ngẫu nhiên điều khoản (không lấy từ lần chuyển đã thấy), đối chiếu một nguồn thứ hai [GT].

## Ba vấn đề chung một gốc

Hệ đúng khi ba điều cùng đúng: **ngày đúng**, **kho biết thay đổi**, **truy xuất đưa đúng điều khoản lên đầu**. Benchmark và thí nghiệm hiện tại kiểm kỹ điều thứ tư: *chọn đúng bản khi đã có ba điều kia*. Đó là đóng góp thật. Ba điều kia là phạm vi chưa giải và cần nói rõ, không giấu.
