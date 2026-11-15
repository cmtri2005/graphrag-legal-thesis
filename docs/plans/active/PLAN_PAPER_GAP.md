# PLAN_PAPER_GAP: đưa khóa luận và paper ViLexTime lên mức mạnh nhất

Date: 2026-11-15

## Status

Đề xuất, chờ CMT duyệt. Chưa việc nào trong plan này được chạy.

Plan này nối `REFACTOR_PLAN.md` (các nhóm 1, 3, 5, 6 còn mở) và `docs/paper/PAPER_GAP.md` (mục 7–8).
`REFACTOR_PLAN.md` giữ làm sổ kết quả đã có. Tiến độ việc mới ghi ở đây. Không thay ADR nào.

Nhãn bằng chứng: **[XM]** đã kiểm trong repo hôm nay; **[SL]** suy luận; **[GT]** giả thuyết, phải đo.

## 1. Đọc trong 2 phút

- **Paper đã có câu chuyện đủ mạnh.** Chỉ số truy xuất quen dùng không thấy lỗi sai phiên bản: MRR 0,445 so với 0,456, trong khi đúng cả cặp (TCS) 7% so với 65% [XM]. Việc còn lại là làm cho người đọc **tin** câu chuyện đó.
- **Ba thứ quyết định paper có được nhận không**, theo thứ tự:
  1. Người độc lập kiểm thước đo (gold mù, nhãn, cờ sai phiên bản). Thiếu thì reviewer bác ngay.
  2. Kết luận giữ nguyên khi đổi generator (model mở) và khi retriever mạnh hơn.
  3. Trình bày: một hình, hai bảng, khung pháp lý, ẩn danh.
- **Điểm nghẽn là giờ người, không phải máy.** Cần khoảng 30 giờ người trong ba tuần tới. Phải bắt đầu tuần này, chạy song song với máy.
- **Không dựng bộ test mới trước 28/01.** Hiệu chính lớn (+0,3), KTC xa 0. Nhãn "thăm dò có khai trước" là đủ cho các phép kiểm độ bền.
- **Hai mốc cứng:** khóa luận 26/12/2026; ICAIL 28/01/2027.
- **Cần CMT chốt 7 việc** (mục 8). Gấp nhất: ai đọc gold mù, và có mở lại reranker không.

## 2. Outcome

Đo được, không phải cảm nhận.

**Khóa luận (26/12):**
- Mọi `[CHỜ]`, `[CẦN]` trong 7 chương được điền số hoặc ghi rõ "không làm, vì sao".
- RQ1 có cả hai vế. RQ2 có LightRAG thật. RQ3 có thêm hai phép kiểm độ bền.
- Ba câu hỏi hội đồng chắc chắn hỏi đều có **số mới** để trả lời, không chỉ lời giải trình (mục 6, WP-E).
- Demo trả lời một câu trong thời gian trình diễn được.

**Paper (28/01):**
- Bảy khẳng định ở mục 4 đều đạt cột "mức cần có".
- Bản ACM `sigconf` ẩn danh, tối đa 10 trang, qua `paper_check.py` và `evidence-gate`.
- Không còn lý do loại vì hình thức (mẫu, ẩn danh, preprint, model mở).

## 3. Hiện trạng ngày 15/11 [XM]

### 3.1. Số đã có trên bộ cuối (318 dòng, hai lần chạy)

| Hệ | Accuracy | Sai phiên bản | TCS | MRR |
|---|---|---|---|---|
| Lai ghép phẳng (`b4`) | 0,324 / 0,296 | 0,291 / 0,294 | 0,071 / 0,047 | 0,445 |
| Lọc theo ngày văn bản (`b7`) | 0,487 / 0,509 | 0,177 / 0,162 | 0,315 / 0,346 | 0,493 |
| Lọc theo khoảng phiên bản (`b7plus`) | 0,654 / 0,648 | 0,008 / 0,011 | 0,654 / 0,646 | 0,456 |
| Cấu hình đầy đủ (`proposed2`) | 0,667 / 0,664 | 0,008 / 0,008 | 0,661 / 0,646 | 0,453 |
| In ngày vào prompt (`bvdate`) | 0,409 / 0,418 | 0,064 / 0,060 | — | — |
| LightRAG | 0,346 / 0,355 | 0,355 / 0,351 | 0,055 / 0,055 | — |
| Oracle đúng mốc | 0,956 / 0,959 | 0 | 0,961 / 0,969 | 1 |
| Oracle bản hiện hành | 0,456 / 0,456 | 0,502 | 0 | 1 |

Nguồn: `runs/final_g4_20261112/{r1,r2}/test/all.score.json` (đọc lại hôm nay, khớp PAPER_GAP); `bvdate` và LightRAG chép từ `REFACTOR_PLAN.md`.

### 3.2. Việc trong PAPER_GAP: xong, đang làm, chưa làm

| Việc | Trạng thái | Ghi chú |
|---|---|---|
| P0-1 TCS, MRR vào paper | Xong trong paper | Số **chưa qua evidence-gate** |
| P0-2 Người chấm cờ sai phiên bản | Phiếu 33 câu đã dựng, **chưa chấm** | `data/review/human_score_g4/recheck_versions/phieu.xlsx` |
| P0-3 Generator mở | **Đang chạy dev trên Colab** | Qwen3.8-27B qua vLLM, 13 hệ, hai lần. Chưa có `runs/qwen_gen_20261115/`. Bộ cuối cần amendment |
| P0-4 Gold mù người trên bộ cuối | Chưa | Hiện phủ 24/156 lineage, 0 dòng T6 |
| P0-5 Người thứ hai kiểm nhãn | Chưa | |
| P0-6 Ẩn danh, preprint | Bản ACM ẩn danh có rồi. Repo công khai vẫn chứa bản thảo | `develop` đã push, trùng `origin` |
| P0-7 Mẫu ACM | Xong, 8/10 trang | Còn 2 trang cho nội dung mới |
| P1-1 Retriever mạnh | Code reranker nằm trong working tree, **chưa commit, chưa chạy** | 35 test qua. Kế hoạch chính ghi "reranker cắt 05/11" |
| P1-2 LightRAG | Xong, thăm dò | Số chưa qua evidence-gate; thiếu log và revision từ Colab |
| P1-3 Bãi bỏ | Chưa | 7/23 |
| P1-4 Câu hỏi thật | Chưa | |
| P1-5 Vế LLM của RQ1 | Chưa | |
| P2-6 Sửa đáp án ngắn T1 | Nháp amendment có, chờ duyệt | Oracle T1 2/43 lên 37/43 |
| W1–W6, W8 | Xong | |
| W7, W9–W12 | Chưa | |

Khóa luận: chương 6 còn 11 chỗ `[CHỜ]`, chương 2 còn 9 chỗ `[CẦN]`, chương 4 còn 6 + 2, chương 3 còn 1 + 2. Chương 6 mới nhắc LightRAG một lần, chưa có Qwen3.8 và reranker.

### 3.3. Sáu điều thấy thêm khi rà, PAPER_GAP chưa ghi

1. **Gói Qwen thiếu `bvnone` và `bvdate`.** `colab_upload/qwen_gen/dev/` có 13 hệ, không có hai hệ này. "Lọc cứng hơn in ngày 0,245" là một trong ba số chính của abstract. Reviewer sẽ hỏi: model lớn hơn có tự dùng được ngày không? Prompt đã có sẵn ở `runs/posthoc_g4_20261113/{dev,test}/prompts/`. Thêm vào gói là xong.
2. **CMT không còn mù.** CMT đã duyệt mọi dòng bộ cuối, có thấy đáp án của kho. Gold mù phải do người khác đọc [SL].
3. **Reranker đang chạy trên CPU.** `retrieve.py:355` ghi cứng `device="cpu"`. 512 truy vấn × 100 ứng viên × vài hệ thì quá chậm [SL]. Cần mở tham số thiết bị trước khi chạy Colab.
4. **Chế độ `ranh_gioi` có dữ liệu, chưa có dự đoán.** File release có đủ 722 dòng (361 × 2 chế độ); file điểm toàn số 0.
5. **Paper còn đúng 2 trang.** Mọi nội dung thêm phải vừa 2 trang (ngân sách ở WP-D).
6. **Lần Colab LightRAG thiếu log, phiên bản thư viện, revision model.** Lần Qwen này phải lưu đủ ngay từ đầu.

## 4. Chiến lược: bảy khẳng định và bằng chứng cần có

Paper mạnh khi mỗi khẳng định có bằng chứng độc lập với chính hệ của tác giả.

| # | Khẳng định | Bằng chứng hiện có | Mức cần có | Việc |
|---|---|---|---|---|
| C1 | RAG phẳng trích sai phiên bản 25–29%; MRR không thấy lỗi này | Theo scorer; một generator; retriever yếu | Người xác nhận cờ; giữ với model mở; giữ với retriever mạnh | A1, B1, B2 |
| C2 | Đọc bản hiện hành mất nửa điểm (0,956 xuống 0,456) | Một generator | Giữ với model mở | B1 |
| C3 | Thứ khử lỗi là lọc cứng theo khoảng trên kho phiên bản; in ngày không thay được | Xác nhận (F4, F5) và thăm dò (`b7v`, `bvdate`) | Giữ với model mở và retriever mạnh; giữ trên phần có gold người | B1, B2, A2 |
| C4 | GraphRAG thật không hơn RAG phẳng ở bài này | LightRAG, thăm dò | Số qua gate; khai ba chỗ không ngang hàng | D1 |
| C5 | Benchmark đo đúng luật | Gold mù 24/156; nhãn AI | Gold mù người khoảng 2/3 bộ cuối, đủ T6; đồng thuận người–người và người–AI | A2, A3 |
| C6 | Lọc không làm hại điều khoản không đổi | Cột T1 hỏng | Cột T1 chấm lại theo amendment | B4 |
| C7 | LLM không truy xuất không biết phiên bản nào áp dụng | Accuracy 0,006, thước không hợp | Phép chọn một trong hai, 2–3 model | B3 |

Bãi bỏ (T6) **không** nằm trong bảng. Viết thẳng là bài toán mở: oracle 22/23, hệ 7/23, tức lỗi ở khâu tìm và quyết định, không ở khâu đọc. Với paper benchmark, một lát chưa ai giải được là điểm cộng nếu chẩn đoán rõ.

## 5. Thứ tự ưu tiên

| Hạng | Việc | Vì sao đứng đây | Tốn |
|---|---|---|---|
| 1 | A2 Gold mù người, 80 lineage | Phá lập luận "tự chấm bài mình". Điều kiện chặn | 16–18 giờ người |
| 2 | B1 Qwen: xong dev, lên bộ cuối, thêm `bvdate` | ICAIL yêu cầu; hết câu hỏi "một model" | GPU, 0 đồng |
| 3 | A1 Chấm phiếu 33 câu | Số chính 25–29% có người xác nhận | 2–3 giờ người |
| 4 | B2 Bảng retriever × bộ lọc | Câu hỏi đầu tiên của reviewer IR | GPU, khoảng 2 USD |
| 5 | A3 Người thứ hai kiểm nhãn | Trả lời "nhãn do AI gán" | 5–7 giờ người |
| 6 | B4 Sửa T1, B3 chọn một trong hai | Gần như miễn phí; đóng C6, C7 | Dưới 1 USD |
| 7 | D Viết lại paper; E hoàn thiện khóa luận | Sau khi số đã khóa | 2–3 tuần |
| 8 | C1–C4 phân tích 0 đồng và lát câu hỏi do người viết | Tăng sức thuyết phục, không chặn | 4 giờ người |

## 6. Các gói việc

### WP-A. Người kiểm thước đo (bắt đầu ngay, không chờ máy)

**A1. Chấm cờ sai phiên bản.** CMT chấm phiếu 33 câu đã dựng. Xong khi có độ chính xác của cờ kèm khoảng Wilson. Ghi rõ người chấm là tác giả và đã thấy các câu này ở phiếu trước.

**A2. Gold mù người trên bộ cuối. Việc quan trọng nhất của plan.**
- Mẫu: 80 lineage rút từ 132 lineage chưa có gold người: đủ 23 T6, 1 T3 còn lại, 56 T2 (phân tầng theo lát lời văn gần giống và theo miền). Cộng 24 lineage cũ thành **104/156, khoảng hai phần ba bộ cuối** [SL].
- Người đọc 1 làm cả 80. Người đọc 2 làm 30 dòng trùng (có 12 T6) để có đồng thuận người–người.
- Người đọc không phải CMT, chưa xem phiếu duyệt, không thấy phiên bản của kho. Đọc văn bản gốc hoặc văn bản hợp nhất.
- Công cụ có sẵn: `scripts/review/independent_gold.py build --only … --strata … --per-stratum …`.
- Báo: tỷ lệ khớp **thô trước phân xử** và sau phân xử, tách riêng, kèm Wilson. Phân xử do người làm, mỗi dòng lệch có lý do viết ra. AI không đề xuất `dong_y`.
- Tính lại F1–F6 trên 104 lineage (ADR 0006 §7). Xem lại G002 và quy ước `dong_y` của đợt 1 theo cùng quy tắc.
- Việc này cũng là M2 (đối chiếu tay) mà đề cương hứa. Ghi rõ như vậy, không làm M2 riêng.
- Ngưỡng: giữ B6 của kế hoạch chính (95% sau phân xử). Không hạ.

**A3. Người thứ hai kiểm nhãn.** Thiết kế "một mẫu, hai pha" để đỡ giờ đọc:
- Pha 1 là A2 (mù). Khóa kết quả.
- Pha 2: mở câu hỏi và đáp án của 50 dòng trong chính mẫu đó, người đọc trả lời Q1–Q4. Thêm 50 dòng đã bị loại ở vòng nhãn AI.
- Báo đồng thuận người–người và người–AI (AC1, kèm KTC). Luật sư kiểm 30 dòng `dat`.
- Chỉ gọi là alt-test nếu đủ ba người gán. Không đủ thì gọi đúng tên: đồng thuận.

**A4. Việc người còn nợ trong đề cương, làm nếu còn giờ:** TVER theo người (khoảng 100 trích dẫn), mã hóa lỗi E7. Không làm thì ghi "không làm" trong chương 6, không để `[CHỜ]`.

### WP-B. Độ bền (máy làm)

Mọi cấu hình mới chọn trên dev. Lên bộ cuối sau **một amendment gộp** của ADR 0006 (mục 7).

**B1. Generator mở (đang chạy).**
- Khi dev xong: tải `raw_dev/` về `runs/qwen_gen_20261115/dev/raw/`, nhập, chấm, so với cột GPT-4o mini trên dev. Lưu kèm log vLLM, `pip freeze`, revision model.
- Thêm `bvnone`, `bvdate` vào gói (mục 3.3 điểm 1).
- Kiểm trước khi lên bộ cuối: định dạng, cắt cụt, và oracle dev không sụp. Ngưỡng cụ thể CMT chốt trong amendment.
- Bộ cuối: 15 hệ × 2 lần. Báo F1–F5, cặp oracle, `b7plus − bvdate`, `proposed2 − lightrag`.
- Đo luôn tỷ lệ câu trả lời trùng nguyên văn giữa hai lần. Nếu gần 100% thì có cột không dao động, trả lời ca `b5 − b4` đổi dấu.
- Tùy chọn, 0 đồng: thêm Qwen3-4B (đường chạy có sẵn theo ADR 0004) để có ba cỡ model.

**B2. Bảng retriever × bộ lọc.**
- Trước hết đo Recall@100 của vùng ứng viên hiện tại trên dev (miễn phí). Thấp thì reranker bị chặn trần; khi đó đổi embedding trước.
- Ứng viên reranker: ba model trong PAPER_GAP P1-1. **Chọn theo MRR của RAG phẳng trên dev, không theo độ lợi của bộ lọc.** Chọn retriever tốt nhất cho đối thủ thì kết quả mới công bằng.
- Sửa `device` ghi cứng (mục 3.3 điểm 3). Commit code reranker trước khi chạy, để run có commit sạch.
- Bảng: {retriever hiện tại, retriever mạnh} × {không lọc, lọc ngày văn bản, lọc khoảng phiên bản}, thêm `bvdate`.
- Truy xuất (TV-R@1, MRR) chạy cả thang, miễn phí và tất định. Sinh câu trả lời: Qwen (miễn phí) và GPT-4o mini hai lần cho 4 ô.
- Dự đoán [GT]: reranker tăng MRR của RAG phẳng, TCS gần như đứng yên. Nếu đúng, đây là bằng chứng mạnh nhất cho C1.

**B3. Vế LLM của RQ1: chọn một trong hai.**
- Mỗi dòng T2: câu hỏi, ngày, hai đoạn (bản đúng mốc, bản khác), thứ tự xáo theo seed, không in ngày. Hỏi đoạn nào áp dụng. Đoán mò 50%.
- Thêm biến thể có in khoảng hiệu lực làm mức trần.
- Model: GPT-4o mini, Qwen3.8-27B, tùy chọn Qwen3-4B. Không dùng họ Claude, DeepSeek (ADR 0004 §3).
- Thử trên dev trước.

**B4. Sửa đáp án ngắn T1.** Duyệt nháp amendment đã có trong `REFACTOR_PLAN.md`. Chấm lại dự đoán đã lưu, không gọi model. Báo cả bản trước và sau.

**B5. Mốc sát biên (`ranh_gioi`).** Chạy truy xuất cả thang (miễn phí); sinh bằng Qwen. Bảng phụ.

**B6. Không làm thêm lần chạy GPT-4o mini** chỉ để đo dao động, trừ khi B1 cho thấy Qwen cũng dao động.

### WP-C. Tính hợp lệ của dữ liệu (phần lớn 0 đồng)

**C1. Một bảng phễu duy nhất**, từ dữ liệu cổng đến dòng được giữ. Kèm so sánh phân bố giữa 40,2% sự kiện áp được và phần còn lại (loại văn bản, năm, loại thao tác). Trả lời "bộ này chỉ gồm thứ đường ống dựng được" bằng số.

**C2. Lát câu hỏi do người viết.** Một người (không phải LLM) viết lại câu hỏi cho 40 lineage T2, chỉ nhìn điều khoản. Chạy 4 hệ đã khóa. Báo riêng, thăm dò. Rẻ hơn và kiểm soát tốt hơn việc lấy bộ câu hỏi ngoài. Lấy câu hỏi thật từ bộ công khai (ViLegalExpert, VLQA) là việc thêm, nếu còn thời gian và giấy phép cho phép.

**C3. Bảng phân tầng theo người viết câu hỏi** vào paper (số đã có: 0,507 / 0,775 / 0,889), kèm ba nguồn về thiên lệch benchmark do LLM sinh.

**C4. Giá trị của đồ thị lúc dựng kho, đo trên toàn kho** [GT]: bao nhiêu đơn vị có từ hai phiên bản; bao nhiêu khoảng hiệu lực được chốt bởi lệnh ở văn bản khác; bao nhiêu do lan truyền từ nút cha. Đây là câu trả lời bằng số cho câu hỏi "đề tài tên đồ thị mà đồ thị làm gì". Kiểm trước xem kho có đủ trường để đếm không.

**C5. Đối chiếu nguồn độc lập** (P2-2): 40 phiên bản so với một nguồn khác cổng vbpl. Máy tải và so chuỗi; người phân xử chỗ lệch. Làm sau A2.

### WP-D. Viết lại paper (sau khi số khóa)

**Trục kể chuyện:** (1) chỉ số truy xuất mù với phiên bản; (2) thang phân rã chỉ ra đúng thứ khử lỗi; (3) kết luận giữ khi đổi generator và retriever; (4) benchmark có người độc lập kiểm.

**Ngân sách 2 trang còn lại:**

| Thêm | Khoảng |
|---|---|
| Bảng kiểm chứng: gold mù, đồng thuận nhãn, scorer–người, cờ sai phiên bản | 0,4 trang |
| Bảng độ bền: 2–3 generator × 2 retriever | 0,5 trang |
| Hình MRR so với TCS, mỗi hệ một điểm | 0,3 trang |
| Chọn một trong hai (C7), cột T1 (C6) | 0,25 trang |
| Khung pháp lý: "còn hiệu lực" khác "được áp dụng" (W9) | 0,15 trang |
| Tài liệu tham khảo từ 33 lên khoảng 45 | 0,4 trang |

Thiếu chỗ thì rút bảng hạng hậu nghiệm và Bảng I.

**Việc viết:**
- D1. `evidence-gate` cho số TCS/MRR và LightRAG đang nằm trong paper.
- D2. W7 (ô ✗ ở Bảng I), W9 (tra số điều bằng công cụ luật, không viết theo trí nhớ), W10 (giấy phép), W11, W12.
- D3. Hai tác giả đọc bản gốc các nguồn mới (P2-7). Chưa đọc thì không dẫn.
- D4. Dẫn GraphRAG-Bench và dòng GraphRAG có thời gian để đặt kết quả LightRAG vào đúng chỗ.
- D5. Một người ngoài nhóm đọc bản gần cuối (GVHD hoặc bạn cùng lab). Phản biện giả lập bằng AI cùng họ model không thay được việc này.

### WP-E. Khóa luận (26/12)

- E1. Chương 6: thêm LightRAG, TCS/MRR, Qwen, bảng retriever, chọn một trong hai, cột T1, kết quả người kiểm. Dọn 11 chỗ `[CHỜ]`: chỗ nào thuộc vòng thử cũ thì xóa hoặc ghi "không làm".
- E2. Chương 3: bảng phễu (C1), M2 (A2), một ví dụ chuỗi sửa đổi có nguồn, số của C4.
- E3. Chương 4: phễu T6, số người kiểm, datasheet khớp manifest.
- E4. Chương 2: hai tác giả đọc và xác minh 9 chỗ `[CẦN]`.
- E5. Chương 1 mục 1.6 và chương 7: cập nhật bảng lệch đề cương. Phụ lục khai báo AI; tra quy định của UIT về dùng AI.
- E6. Demo: đo xem 5 phút mỗi câu chậm ở đâu rồi mới sửa.
- E7. Ba câu hỏi hội đồng và số mới để trả lời:

| Hội đồng hỏi | Trả lời bằng |
|---|---|
| Vì sao 361 dòng thay vì 1.150? | Bảng MDE có sẵn; hai phần ba bộ cuối có người đọc mù (A2); phễu công khai (C1) |
| Vì sao AI gán nhãn? | Đồng thuận người–AI và luật sư (A3); scorer khớp người 96/100 |
| Đề tài tên đồ thị, đồ thị làm gì? | F5 +0,115 là phần của chuỗi phiên bản; số toàn kho ở C4; thẳng thắn: lúc truy vấn không thêm gì, LightRAG cũng không |

- E8. `thesis-critic` và `evidence-gate` rà toàn văn sau ngày khóa số.

### WP-F. Nộp bài

- F1. CMT mở trang gốc ICAIL kiểm lại quy định (hôm 15/11 mới đọc qua công cụ tóm tắt).
- F2. Xử lý repo công khai (mục 8, Q4). Link code và dữ liệu qua dịch vụ ẩn danh. Không đăng arXiv trước 19/04/2027.
- F3. Hỏi GVHD: khóa luận nộp 26/12 có bị coi là công bố trước không.
- F4. Chạy `paper_check.py`; điền CRediT, tài trợ; soát khai báo AI.

## 7. Amendment gộp cho ADR 0006

Viết **sau khi có số dev** của B1 và B2, duyệt **trước** khi chạm bộ cuối. Một amendment, khai đủ:

- Đã thấy gì: toàn bộ G4, hậu nghiệm, LightRAG, và số dev của các cấu hình mới.
- Hệ thêm: cột Qwen cho 15 hệ; các hệ có reranker; phép chọn một trong hai; `ranh_gioi`; lát câu hỏi do người viết.
- Tất cả là thăm dò, ngoài Holm, không đổi phán quyết F1–F7.
- Cách đọc khai trước:

| Thí nghiệm | Nếu | Thì viết |
|---|---|---|
| Qwen | F1–F5 cùng dấu, KTC loại 0 ở cả hai lần | "Kết luận không phụ thuộc generator" |
| Qwen | Có hiệu đổi dấu hoặc KTC chứa 0 | Nêu đúng hiệu đó; khẳng định tương ứng chỉ còn cho GPT-4o mini |
| Qwen, `bvdate` | `b7plus − bvdate` chứa 0 | Sửa số chính thứ ba: model lớn dùng được ngày; lọc cứng vẫn rẻ và chắc hơn |
| Reranker | `b7plus-rr − b4-rr` loại 0 ở cả hai lần | "Lợi ích của lọc còn với retriever mạnh", kèm tỷ lệ so với hiệu gốc |
| Reranker | Khoảng cách co hơn một nửa | Viết lại: xếp hạng sửa một phần, lọc sửa phần còn lại |
| Reranker | Khoảng cách mất | Viết lại thông điệp chính. Vẫn công bố |
| Gold mù | Dưới ngưỡng B6 | Báo tỷ lệ lỗi; chấm lại phần đó theo gold người; thu hẹp khẳng định. Không sửa kho trước hạn nộp |

## 8. Cần CMT chốt

| # | Quyết định | Đề xuất | Chặn |
|---|---|---|---|
| Q1 | Ai đọc gold mù (không phải CMT)? Ai là người thứ hai? | NMT làm 80; luật sư hoặc một sinh viên luật làm 30 | A2, A3. **Gấp nhất** |
| Q2 | Mở lại reranker (đã cắt 05/11)? | Có. Lý do mới: reviewer hỏi baseline yếu; code đã viết | B2 |
| Q3 | Duyệt amendment gộp (mục 7) khi có số dev | Có | B1–B5 trên bộ cuối |
| Q4 | Repo công khai đang chứa bản thảo có tên | Chuyển riêng tư đến 19/04/2027; hoặc ít nhất gỡ `docs/paper/` khỏi nhánh công khai. Hỏi GVHD | F2 |
| Q5 | Nơi nộp | ICAIL bài dài. Ngày 10/01 chưa có A2 và B1 thì chuyển bài ngắn. GVHD chốt | WP-D |
| Q6 | Dựng bộ test mới trước 28/01? | Không. Để sau khi nộp, cùng việc nâng độ phủ kho và bãi bỏ | — |
| Q7 | Ai viết 40 câu hỏi cho C2? | Người ngoài nhóm nếu có; không thì NMT | C2 |

## 9. Lịch

| Tuần | Máy | Người | Mốc |
|---|---|---|---|
| 16–22/11 | Qwen dev xong, nhập, chấm. Thêm `bvdate`. Reranker: Recall@100, chọn trên dev. Dựng phiếu A2, A3. Gate số TCS, LightRAG | CMT chấm 33 câu. Chốt Q1, Q2. Người đọc bắt đầu A2 | **M1 22/11:** amendment gộp được duyệt |
| 23–29/11 | Bộ cuối: Qwen 15 hệ; bảng retriever; B3; B4; B5 | A2 tiếp | |
| 30/11–06/12 | Chấm, bootstrap, gate. C1, C3, C4 | A2 xong, phân xử. A3 pha 2 | **M2 06/12:** có số người kiểm |
| 07–13/12 | Tính lại F1–F6 trên 104 lineage. Chương 6, 3, 4 | Đọc nguồn chương 2. C2 viết câu hỏi | **M3 10/12:** khóa số khóa luận |
| 14–20/12 | `thesis-critic`, `evidence-gate`. Demo | GVHD đọc | |
| 21–26/12 | Sửa theo góp ý | | **M4 26/12:** nộp khóa luận |
| 27/12–10/01 | Viết lại paper theo WP-D. C2 chạy. C5 | Đọc bản gốc nguồn mới | **M5 10/01:** chọn bài dài hay ngắn |
| 11–24/01 | Gate, `paper_check.py`, gói ẩn danh | Người ngoài đọc | **M6 21/01:** khóa bản thảo |
| 25–28/01 | Dự phòng | Nộp | **28/01** |

Giờ người: A1 3; A2 16–18; A3 5–7; phân xử 2; C2 4. Tổng khoảng 30 giờ, chia cho CMT, NMT, luật sư.
Tiền API: bảng retriever khoảng 2 USD, B3 và C2 dưới 1 USD mỗi việc [SL, tính từ 5,3 USD cho 24 lượt hệ ở G4].

## 10. Không làm

- Không cố làm đồ thị lúc truy vấn "thắng". Đã chốt ở audit 13/11.
- Không dựng bộ test mới, không nâng độ phủ kho, không làm bước quyết định bãi bỏ trước 28/01. Ba việc này đi cùng nhau, để sau.
- Không LLM giám khảo. Không chạy T-GRAG, TG-RAG và các hệ tương tự; chỉ dẫn.
- Không thêm biến thể LightRAG.
- Không đổi P, F1–F7, scorer, gold, prompt của hệ đã khóa.

## Risks And Recovery

| Rủi ro | Xử lý |
|---|---|
| Không tìm được người đọc mù kịp | Giảm xuống 23 T6 + 37 T2 (60 lineage). Dưới mức đó thì nộp bài ngắn (Q5) |
| Gold mù lộ lỗi kho | Báo đúng số; chấm lại theo gold người; không sửa kho trước hạn |
| Model mở hoặc reranker đảo một kết luận | Viết theo bảng mục 7. Biết trước reviewer vẫn hơn |
| Trùng hạn khóa luận | Khóa số 10/12. Sau ngày đó số mới chỉ vào paper |
| Colab ngắt | `vllm_generate.py` chạy tiếp được từ dòng dở |
| Lẫn artifact | Mỗi việc một thư mục `runs/<tên>_<ngày>/`; không ghi vào `runs/final_g4_20261112/` |
| Lộ danh tính khi phản biện kín | Q4, F2 |

Hoàn tác: plan này chỉ thêm file và thư mục run mới. Xóa thư mục run và revert commit là về trạng thái 15/11.

## Progress

- [x] 15/11 Rà hiện trạng, lập plan.
- [ ] Q1–Q7: CMT chốt.
- [ ] A1 Chấm phiếu 33 câu.
- [ ] A2 Gold mù 80 lineage: dựng phiếu / đọc / phân xử / tính lại F1–F6.
- [ ] A3 Kiểm nhãn pha 2; luật sư 30 dòng.
- [ ] B1 Qwen: dev / thêm `bvdate` / bộ cuối.
- [ ] B2 Reranker: Recall@100 / chọn trên dev / bộ cuối.
- [ ] B3 Chọn một trong hai.
- [ ] B4 Sửa T1, chấm lại.
- [ ] B5 `ranh_gioi`.
- [ ] Amendment gộp ADR 0006.
- [ ] C1 Bảng phễu. C3 Bảng theo người viết. C4 Số toàn kho. C2 Lát câu hỏi người viết. C5 Nguồn độc lập.
- [ ] D1–D5 Paper.
- [ ] E1–E8 Khóa luận.
- [ ] F1–F4 Nộp.

## Decisions

- 2026-11-15: đề xuất không dựng bộ test mới trước 28/01; dồn giờ người cho gold mù. Chờ CMT.

## Validation

- Mỗi số mới truy được về một file trong `runs/` kèm hash đầu vào, và qua `evidence-gate` trước khi vào khóa luận hay paper.
- Mỗi cấu hình mới có dòng trong `runs/README.md` và nằm trong amendment đã duyệt trước khi chạy bộ cuối.
- Số người kiểm báo cả thô và sau phân xử.
- Lệnh nền: `.venv/bin/python -m pytest -q`, `git diff --check`, `latexmk -xelatex` ở `docs/paper/acm/`.

## Result

Chưa có.
