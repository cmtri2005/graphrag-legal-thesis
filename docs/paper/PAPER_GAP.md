# PAPER_GAP: paper ViLexTime còn thiếu gì để được nhận

Ngày viết: 15/11/2026. Bản được đọc: `docs/paper/ieee/main.pdf` và `main.tex` (commit `835c032`, 7 trang).

Cập nhật cùng ngày: bổ sung kết quả LightRAG chạy trên Colab (mục 7, việc P1-2).

Người viết: một phiên AI trong dự án (Claude), đọc theo năm vai phản biện. Đây **không phải phản biện độc lập**: cùng họ model đã giúp viết paper, nên có thể cùng điểm mù. File này không sửa paper, không chạy lại thực nghiệm, không đổi số nào.

Nhãn bằng chứng dùng trong file:

| Nhãn | Nghĩa |
|---|---|
| **[XM]** | Lấy từ file trong repo (paper, `numbers.md`, audit 13/11, REFACTOR_PLAN, file điểm) |
| **[WEB]** | Tra web ngày 15/11/2026. Mới đọc tóm tắt hoặc trích đoạn, chưa đọc toàn văn |
| **[NHỚ]** | Kiến thức nền của tôi, hôm nay chưa tra lại. Phải kiểm trước khi dẫn |
| **[SL]** | Suy luận từ bằng chứng |
| **[GT]** | Giả thuyết. Phải đo mới biết |

---

## 1. Trả lời nhanh bốn câu hỏi

**Câu 1. Paper có thật sự giải quyết vấn đề đã nêu không?**
Được một nửa.
- Phần sửa đổi (T2): giải quyết tốt **trên kho của chính mình**. Lỗi trích sai phiên bản từ 29,1% xuống 0,8%, Accuracy từ 0,324 lên 0,667 [XM].
- Phần bãi bỏ (T6): chưa. Hệ đúng 7/23, trong khi cấp sẵn căn cứ thì đúng 22/23 [XM].
- Phần "đúng với luật thật": chưa chứng minh. Đáp án và bộ lọc lấy từ cùng một kho, kho mới áp được 40,2% sự kiện sửa đổi [XM].

**Câu 2. Bộ dữ liệu và phương pháp đủ mạnh chưa?**
- Thiết kế đo: mạnh, hơn mặt bằng chung (khai báo trước, thang đổi từng nấc, hai lần chạy, tự khai giới hạn).
- Bộ dữ liệu: ý tưởng tốt, nhưng **chưa có người độc lập kiểm**. Đây là điểm yếu nhất.
- Phương pháp: phần chạy được là một bộ lọc theo khoảng hiệu lực. Ý này đã có người công bố. Phần "đồ thị lúc truy vấn" của hệ đề xuất không tạo khác biệt đo được.

**Câu 3. Có bám đề cương không?**
- Bám: ba câu hỏi nghiên cứu và giả thuyết. Giả thuyết đề cương chính là F5, được ủng hộ (+0,115) [XM].
- Lệch lớn ở ba chỗ: cỡ dữ liệu (361 dòng so với 1.100–1.300), cách kiểm nhãn (AI gán thay vì kiểm thủ công), vai của đồ thị (chỉ có tác dụng lúc dựng kho).

**Câu 4. Sửa gì để ăn điểm nhanh nhất?** Bảy việc, xếp theo thứ tự nên làm:

| # | Việc | Tốn | Vì sao ăn điểm |
|---|---|---|---|
| 1 | Đưa TCS, MRR vào paper | 0 đồng, số đã có sẵn | Flat RAG đúng cả cặp chỉ 7,1%; có lọc 65,4%. Số này mạnh hơn mọi số đang có trong paper |
| 2 | Chấm phiếu 33 câu "sai phiên bản" đã dựng sẵn | 2–3 giờ người (ước lượng) | F3 hết cảnh "chỉ theo scorer" |
| 3 | Chạy thêm một generator mã nguồn mở trên prompt đã lưu | Vài giờ GPU | ICAIL yêu cầu; đồng thời dập câu hỏi "một model" |
| 4 | Gold mù do người đọc, 60–80 dòng, đủ 23 dòng T6 | 10–13 giờ người | Phá vòng tự chấm. Thiếu việc này reviewer bác ngay |
| 5 | Người thứ hai (hoặc luật sư) kiểm mẫu nhãn | 6–10 giờ người (ước lượng) | Trả lời "nhãn do AI gán" |
| 6 | Reranker, áp đều cho mọi nấc | GPU, cần amendment | Dập câu hỏi "baseline yếu" |
| 7 | Ẩn danh, đổi sang mẫu ACM, sửa trình bày (mục 8) | 1–2 ngày | Không làm thì bị loại vì hình thức |

Riêng đối chứng LightRAG: Colab đã dựng xong đồ thị và lấy xong ngữ cảnh cho 512 truy vấn. Còn thiếu bước sinh câu trả lời và chấm, nên **chưa có Accuracy**. Chi tiết ở việc P1-2.

**Về xác suất được nhận.** Tôi không đưa con số phần trăm, vì không có căn cứ để tính. Nói theo mức:
- Nộp bản hiện tại làm bài dài ở ICAIL 2027: nhiều khả năng bị từ chối.
- Xong việc 1–5 và 7: vào vùng cạnh tranh.
- Thêm việc 6 và đối chứng LightRAG: mức tốt nhất đạt được trước hạn 28/01/2027.

---

## 2. Paper có giải quyết vấn đề đã nêu không

Phần mở đầu của paper đặt hai câu hỏi: RAG trả lời sai phiên bản thường xuyên đến đâu, và mức thông tin thời gian nào khử được lỗi.

| Paper hỏi | Trả lời hiện có [XM] | Mức | Còn thiếu |
|---|---|---|---|
| RAG phẳng sai phiên bản bao nhiêu | 25,3% (BM25) và 29,1% (lai ghép) số dòng có đoạn phân biệt phiên bản | Có, mức mô tả | Cờ sai phiên bản chưa có người xác nhận. Một generator. Retriever yếu nên tỷ lệ có thể khác khi retriever mạnh |
| LLM không truy xuất sai bao nhiêu | Accuracy 0,006; người chấm 2/34 đúng | **Chưa đo được** | Thước đòi chép đúng lời văn. LLM không truy xuất gần như không thể đạt |
| Mức thông tin nào khử lỗi | Ngày văn bản +0,078; khoảng phiên bản +0,115 TV-R@1 (xác nhận). Kho phiên bản không lọc −0,044; in ngày vào prompt kém lọc cứng 0,245 (thăm dò) | **Có. Đây là phần chắc nhất** | Đo so với chính kho. Kho áp được 40,2% sự kiện |
| Đọc bản hiện hành tốn bao nhiêu | 0,956 xuống 0,456 | Có | Một generator |
| Bãi bỏ | Hệ 7/23, precision 0,64; cấp sẵn căn cứ 22/23 | **Chưa giải quyết** | 23 dòng, MDE khoảng 0,185 |
| Đồ thị lúc truy vấn có giúp không | +0,013 [−0,009; +0,035] | Không thấy tác dụng | — |
| Lan truyền từ nút cha có giúp không | F6 trùng F5; đổi căn cứ đứng đầu ở 1/295 dòng | Không thấy tác dụng | Thêm dòng T6 nút cha |
| Đáp án có đúng luật không | Gold mù người phủ 24/156 lineage, không có T6; phân xử do AI đề xuất | **Chưa chứng minh** | Gold mù người trên chính bộ cuối |

**Đọc bảng này thế nào.** Paper trả lời chắc một câu: *khi đã có kho phiên bản, lọc cứng theo khoảng hiệu lực trước khi xếp hạng là thứ khử lỗi sai phiên bản*. Mọi thứ khác hoặc là mô tả, hoặc chưa đủ bằng chứng. Paper đã tự viết đúng như vậy. Điểm trừ không nằm ở chỗ nói quá, mà ở chỗ bằng chứng nền (nhãn, gold) chưa đủ độc lập.

---

## 3. Bộ dữ liệu ViLexTime

### Điểm mạnh [XM]

- Đáp án gắn với **phiên bản điều khoản tại một ngày**, không chỉ gắn với điều luật.
- Chấm tương phản: phải chứa lời văn bản đúng mốc và không chứa lời văn chỉ bản khác có.
- Có nhóm bãi bỏ (T6), có mốc giữa khoảng để ngày hỏi không lộ đáp án.
- Chia dev và test theo văn bản. Bộ cuối chưa hệ nào chạy trước.
- Hồ sơ nguồn gốc từng nhãn, hash, datasheet, kế hoạch phân tích khóa trước.
- Cỡ không phải vấn đề chính: bộ của Prior và cộng sự (luật Đức, ICAIL 2026) có 312 cặp [XM, ghi chú repo]. Khác biệt là bộ đó có chuyên gia kiểm.

### Điểm yếu, xếp từ nặng đến nhẹ

| # | Điểm yếu | Bằng chứng [XM] | Reviewer sẽ nói gì |
|---|---|---|---|
| D1 | Không có người độc lập kiểm nhãn | AI-A, AI-B gán; một tác giả duyệt; ca khó do agent chốt; AC1 AI–AI 0,608, dưới ngưỡng 0,80; không luật sư | "Đây là bộ silver do model tự chấm bài của model" |
| D2 | Gold và bộ lọc chung một nguồn | Gold mù phủ 24/156 lineage, 0 dòng T6; "119/120" là sau phân xử do AI đề xuất; khớp thô 148/150 | "F3–F6 chỉ đo độ nhất quán với kho của tác giả" |
| D3 | Thiên lệch chọn mẫu | Kho áp được 3.238/8.046 = 40,2% sự kiện; bộ lọc LLM gắn `gold_wrong` cho 48/280 ứng viên T2 và 162/1.217 ứng viên T6 nút cha | "Bộ này chỉ gồm điều khoản mà đường ống dựng được. Lỗi bỏ sót sự kiện không bao giờ lộ ra" |
| D4 | Lệch nhóm | T3 6 lineage; T6 23; T5 0; T1 hỏng đáp án ngắn (41/43); 76/254 dòng T2 là lời văn gần giống | "Chỉ là bộ T2" |
| D5 | Lệch miền và loại văn bản | 220/318 dòng ngoài bốn miền mục tiêu; Nghị định 95, Thông tư 57, Luật 3, Thông tư liên tịch 1 lineage | "Không đại diện cho luật Việt Nam" |
| D6 | Câu hỏi do LLM viết | Accuracy hệ đề xuất theo người viết: Codex 0,507 (144 dòng), Claude 0,775 (138), DeepSeek 0,889 (36) | "Độ khó do model viết câu hỏi quyết định, không do luật" |
| D7 | Cùng họ model ở hai vai | Codex (OpenAI) viết 144 dòng và là AI-B; generator được chấm là GPT-4o mini (OpenAI) | "Có thiên vị cùng họ không?" Số liệu cho thấy dòng Codex viết lại khó nhất, nên không có dấu hiệu thổi điểm [SL], nhưng chưa tách được khỏi cơ cấu từng lô |
| D8 | Cờ sai phiên bản chưa có người kiểm | Phiếu 100 câu chỉ hiện bản đúng mốc; phiếu 33 câu đã dựng, chưa chấm | "Con số chính của paper (25–29%) chưa ai kiểm" |
| D9 | Một nguồn | Chỉ vbpl.vn; văn bản hợp nhất để đối chiếu cũng từ cổng đó | "Sai ở nguồn thì sai cả hai phía" |
| D10 | Chỉ báo mốc giữa khoảng | Trong file điểm bộ cuối, chế độ `ranh_gioi` toàn số 0, tức chưa chạy | "Sát ngày hiệu lực thì sao?" |

So với các bộ gần nhất: LawInForce-eCFR báo hai người gán đồng thuận 95,28% [XM, ghi chú repo]; Prior và cộng sự có chuyên gia nhận 312 trên 697 cặp LLM sinh [XM]; CALRK-Bench (luật Hàn) ghi có chuyên gia luật kiểm [WEB]. ViLexTime chưa có tầng này.

**Kết luận về bộ dữ liệu.** Khung và quy trình đủ chuẩn để công bố. Chất lượng nhãn và độ độc lập của gold thì chưa. Việc 2, 4, 5 ở mục 1 đóng đúng ba lỗ D1, D2, D8.

---

## 4. Phương pháp và thực nghiệm

### Điểm mạnh [XM]

- Thang đối chứng đổi một yếu tố mỗi nấc, cùng prompt, cùng generator, cùng `k`.
- Cặp oracle (bản đúng mốc so với bản hiện hành) tách lỗi tìm khỏi lỗi đọc.
- Kế hoạch phân tích khóa trước khi chạy; Holm; bootstrap theo lineage; chạy hai lần và chỉ nhận khi cả hai lần đồng ý.
- Phân tích sau khi thấy kết quả được dán nhãn rõ.
- Đối chứng "in ngày vào prompt" (`bvdate`) là ý hay và ít bài có.
- Người chấm lại 100 câu: scorer khớp 96/100, không có câu nào scorer cho đúng mà người cho sai.

### Điểm yếu

| # | Điểm yếu | Bằng chứng [XM] | Hệ quả |
|---|---|---|---|
| M1 | Tính mới về phương pháp thấp | Phần có tác dụng là một điều kiện lọc theo khoảng. Prior 2026, LawInForce-eCFR, NitiBench+ đã cho thấy lọc theo mốc có lợi | Không bán được như "phương pháp mới". Phải bán như "tài nguyên + phép đo phân rã" |
| M2 | Hệ đề xuất không hơn nấc ngay dưới | TV-RAG − `+VersionFilter` = +0,013 [−0,009; +0,035]; F1–F3 vẫn đúng nếu thay bằng `+VersionFilter` [SL] | Tên "TV-RAG" gợi một hệ mới, nhưng chính paper cho thấy nó không thêm gì |
| M3 | Retriever yếu | Căn cứ đúng đứng hạng 1 ở 107/295 dòng; BM25 trên âm tiết rời nối bằng OR; dense PhoBERT-base cắt 256 token; chỉ trộn top 20 + top 20; không reranker | Reviewer hỏi: retriever mạnh thì flat RAG có tự hết lỗi không? Paper chưa trả lời |
| M4 | Một generator, lại là model đóng | GPT-4o mini; `b5 − b4` đổi dấu giữa hai lần chạy, cả hai KTC đều loại 0 | Hiệu nhỏ hơn khoảng 0,03 không đọc được. Trái yêu cầu của ICAIL (mục 6) |
| M5 | Đối chứng đồ thị không phải GraphRAG | `b5`, `b6` là mở rộng một bước tự xây. LightRAG đã dựng đồ thị và lấy ngữ cảnh trên Colab (15/11), chưa sinh câu trả lời, chưa có điểm | Đề cương hứa "GraphRAG phi thời gian" |
| M6 | Bãi bỏ yếu ở mọi hệ | 7/23; F7 không đủ lực (MDE khoảng 0,185) | Không có kết quả dương nào cho T6 |
| M7 | Verifier và lan truyền không tác động | Verifier không tác động do cách dựng; lan truyền đổi 1/295 dòng | Hai thành phần của kiến trúc đề cương không có bằng chứng lợi ích |
| M8 | Ngày hỏi được cấp sẵn | Đầu vào là cặp (câu hỏi, ngày) | Người dùng thật hiếm khi ghi ngày. Cần nêu là giới hạn |
| M9 | "Còn hiệu lực" chưa phải "được áp dụng" | Không có T5 (hồi tố, điều khoản chuyển tiếp) | Người đọc ngành luật ở ICAIL sẽ hỏi đầu tiên |
| M10 | Kho phiên bản chưa đầy đủ | 40,2% sự kiện áp được; khớp văn bản hợp nhất 80,0% trên 51 văn bản | Mọi kết luận chỉ đúng "trên phần kho đã dựng" |

**Kết luận về phương pháp.** Phép đo đáng tin trong phạm vi đã khai. Cái thiếu là độ bền (retriever mạnh, generator khác) và một đối chứng đồ thị thật. Không nên cố làm cho đồ thị lúc truy vấn "thắng": audit 13/11 đã chốt như vậy và tôi đồng ý.

---

## 5. So với đề cương

Nguồn: `docs/DeCuongKLTN_23521635_23521643_UIT.docx` [XM]. Bảng lệch chi tiết đã có ở Chương 1 mục 1.6; dưới đây là bản rút gọn kèm đánh giá.

| Đề cương hứa | Hiện có | Mức |
|---|---|---|
| Tên: Temporal-Aware KG-RAG | Paper đổi trọng tâm sang "benchmark + phép đo có đối chứng"; đồ thị có vai lúc dựng kho | Lệch có lý do. Khóa luận giữ tên và giải trình; paper đổi tên là đúng |
| RQ1: LLM và RAG sai phiên bản đến đâu | Vế RAG: có, theo scorer. Vế LLM: chưa đo được | Một nửa |
| RQ2: đồ thị theo phiên bản có giảm lỗi so với RAG phẳng và GraphRAG phi thời gian | Hơn RAG phẳng: có (F1–F3). So với GraphRAG thật: LightRAG đã có ngữ cảnh, chưa có điểm (P1-2) | Phần lớn |
| RQ3: lợi ích từ đồ thị hay từ lọc siêu dữ liệu | Trả lời rõ: từ lọc khoảng trên kho phiên bản; đồ thị lúc truy vấn không thêm | **Đạt. Đây là phần mạnh nhất** |
| Giả thuyết: mô hình hóa chuỗi phiên bản hơn lọc theo ngày văn bản | F5 +0,115 [+0,076; +0,156], ủng hộ ở cả hai lần | **Đạt** |
| 1.100–1.300 câu, kiểm định thủ công, LLM chỉ hỗ trợ diễn đạt | Bộ cuối 199 lineage, 361 dòng; AI gán nhãn, một tác giả duyệt; LLM còn chọn đoạn đáp án và lọc trước | **Lệch lớn** |
| Bảng 1: T1 250, T2 400, T3 200, T4 150, T5 50, T6 100 | T1 43 (hỏng), T2 254, T3 18, T4 thành lát 76 dòng của T2, T5 0, T6 46 | **Lệch lớn** |
| Bốn miền: giao thông, thuế, doanh nghiệp–đầu tư, đất đai | 220/318 dòng ngoài bốn miền | Lệch |
| L0–L3 dựng đồ thị và chuỗi phiên bản | Có, là đóng góp thật. Độ phủ 40,2% | Đạt một phần |
| L4: lọc hiệu lực trước, lai ghép, mở rộng đồ thị | Có đủ. Mở rộng đồ thị không có tác dụng; `rel_up` lấy seed trước khi lọc | Đạt về cài đặt |
| L5: Temporal Verifier | Có, không tác động | Chỉ là lưới an toàn |
| Đối chứng: LLM, BM25, dense, hybrid, GraphRAG phi thời gian, KG phân cấp, lọc siêu dữ liệu | Đủ, trừ GraphRAG thật (LightRAG đang ở giữa chừng, P1-2) | Thiếu một |
| Chỉ số: Recall@k, MRR, TV-Recall@k, Accuracy, EM/F1, LLM-judge, TVER, VCR, TCS | Paper chỉ có Accuracy, TV-R@1, TVER, sai phiên bản. MRR, EM/F1, VCR, TCS **đã tính sẵn** trong file điểm bộ cuối nhưng chưa vào paper. LLM-judge bỏ, có lý do | Dễ lấp |
| Thí nghiệm chuyển miền | Chỉ có phân rã theo miền | Lệch |
| Giao diện minh họa | Dòng lệnh, khoảng 5 phút một câu | Yếu |

**Hội đồng sẽ hỏi ba chỗ:** vì sao 361 dòng thay vì 1.150; vì sao AI gán nhãn; vì sao đề tài tên "đồ thị tri thức" mà đồ thị không giúp lúc truy vấn. Cả ba đã có lời giải trình trong Chương 1 mục 1.6. Chỗ còn lấp được trước 26/12 là chỉ số (TCS, MRR), đối chứng LightRAG và vế LLM của RQ1.

---

## 6. Nơi nộp và luật chơi

Kế hoạch chính ghi đề xuất ICAIL 2027, "chưa kiểm trang chính thức". Hôm nay tôi đã mở trang của hội nghị qua công cụ đọc web. Công cụ này tóm tắt trang và cắt bớt câu trích, nên **CMT cần mở trang gốc kiểm lại** trước khi quyết.

ICAIL 2027, Vienna, 5–9/7/2027 [WEB]:

| Mục | Quy định | Paper hiện tại |
|---|---|---|
| Hạn nộp | 28/01/2027; phản hồi 18–25/3; báo kết quả 19/4 | Còn khoảng 10 tuần, trùng hạn khóa luận 26/12 |
| Độ dài | Bài dài tối đa 10 trang, bài ngắn 5 trang, **gồm cả tài liệu tham khảo** | 7 trang IEEE |
| Mẫu | ACM `sigconf` | Đang là IEEEtran. **Phải đổi** |
| Ẩn danh | Phản biện kín hai chiều; không tên, không đơn vị, không lời cảm ơn; link code và dữ liệu cũng phải ẩn danh | Có tên, email, link GitHub có tên. **Phải sửa** |
| Preprint | Không được đăng preprint mở trước ngày báo kết quả | Repo GitHub công khai đang chứa `main.pdf` và `main.tex`. **Rủi ro**, xem việc P0-6 |
| Model đóng | Bài dùng LLM đóng nên so với ít nhất một model mở cỡ tương đương, cùng điều kiện | Chỉ có GPT-4o mini. **Thiếu** |
| Dữ liệu | Nên dùng dữ liệu thật, không chỉ dữ liệu tổng hợp hay bộ đã làm sạch quá mức | Câu hỏi do LLM viết. **Điểm trừ** |
| AI | Được dùng, phải khai đầy đủ | Đã có mục khai. Giữ |
| Chủ đề | Có "legal information retrieval", "legal benchmarking, hallucination management and verification" | Hợp |

Các phương án:

| Phương án | Cần gì | Nhận xét |
|---|---|---|
| A. ICAIL 2027, bài dài | P0 đủ, thêm P1-1 hoặc P1-2 | Giá trị cao nhất. Rủi ro về thời gian |
| B. ICAIL 2027, bài ngắn 5 trang | P0-1 đến P0-3, P0-6, P0-7 | Chỉ kể thang đo, cặp oracle, `bvdate`, TCS. Ít chỗ để bị bắt bẻ |
| C. Hội nghị IEEE trong khu vực | Bản IEEE gần sẵn | Tôi **chưa tra** hạn 2027 của hội nghị nào. Các hội nghị này thường giới hạn 6 trang [NHỚ]; bản hiện 7 trang |
| D. NLLP 2027 hoặc JURIX 2027 | P0 và P1 đầy đủ | Năm 2026 hai nơi này có hạn vào tháng 8 và tháng 9 [WEB]; chưa có thông báo 2027 |

Khuyến nghị của tôi: nhắm A, lấy mốc tự kiểm ngày 10/01/2027. Đến ngày đó chưa xong gold mù người và model mở thì chuyển sang B. GVHD là người chốt (cổng G6 của kế hoạch chính).

---

## 7. Việc cần làm, kèm cách làm theo chuẩn hiện nay

Bộ test cuối đã xem. Mọi cấu hình mới chạy trên bộ này phải có amendment ADR 0006 và ghi "thăm dò". Muốn có số "xác nhận" cho cấu hình mới thì cần bộ test mới.

### P0. Phải xong trước khi nộp

**P0-1. Đưa TCS và MRR vào paper.**
- Vì sao: đề cương hứa hai chỉ số này. Số đã nằm sẵn trong `runs/final_g4_20261112/r1/test/all.score.json`, lát `all`, chế độ `giua_khoang` [XM]:

  | Hệ | TCS (127 cặp T2) | MRR | VCR | EM | F1 |
  |---|---:|---:|---:|---:|---:|
  | Lai ghép phẳng (`b4`) | 0,071 | 0,445 | 0,255 | 0,071 | 0,508 |
  | +VersionFilter (`b7plus`) | 0,654 | 0,456 | 0,016 | 0,156 | 0,611 |
  | TV-RAG (`proposed2`) | 0,661 | 0,453 | 0,000 | 0,149 | 0,609 |
  | Oracle đúng mốc | 0,961 | 1,000 | 0,000 | 0,312 | 0,793 |
  | Oracle bản hiện hành | 0,000 | 1,000 | 0,516 | 0,173 | 0,679 |

  Lần 2 (`r2/test/all.score.json`) cho TCS cùng chiều: 0,047; 0,646; 0,646; 0,969; 0,000. Các số này tôi đọc thẳng từ hai file điểm, **chưa qua evidence-gate**.
- Thông điệp có thể viết [SL]: MRR thường gần như không đổi giữa flat RAG và hệ có lọc (0,445 và 0,456), trong khi tỷ lệ đúng cả cặp tăng từ 7% lên 65%. Nghĩa là chỉ số truy xuất quen dùng **không nhìn thấy** lỗi sai phiên bản. Đây là lý do tồn tại của benchmark, và nó gọn hơn mọi câu đang có trong abstract.
- Chi phí: 0. Xong khi: số qua gate, có KTC, báo cả hai lần chạy.

**P0-2. Người chấm cờ "sai phiên bản".**
- Vì sao: F3 và con số 25–29% hiện chỉ theo scorer (D8).
- Việc nhỏ nhất: chấm phiếu `data/review/human_score_g4/recheck_versions/phieu.xlsx` (33 câu, hiện mọi phiên bản) đã dựng ngày 14/11 [XM].
- Xong khi: có độ chính xác của cờ kèm khoảng Wilson. Nếu người chấm là tác giả thì ghi rõ.

**P0-3. Thêm generator mã nguồn mở.**
- Vì sao: yêu cầu của ICAIL (mục 6); M4.
- Cách làm: prompt của mọi hệ đã lưu ở `runs/final_g4_20261112/r1/prompts/` [XM], nên chỉ cần sinh lại và chấm. Repo đã có đường chạy Qwen3-4B (ADR 0004) [XM]. Nên thêm một model mở lớn hơn, chọn trên dev. Không dùng họ Claude hay DeepSeek (ADR 0004 §3). Tên model cụ thể tôi chỉ biết đến giữa 2026 [NHỚ]; tra bảng xếp hạng hiện tại trước khi chọn.
- Lợi thêm: model chạy tại chỗ với seed cố định thì hết dao động API (ca `b5 − b4` đổi dấu).
- Báo gì: F1–F5 có giữ chiều và cỡ không; cặp oracle có giữ khoảng cách không. Ghi "thăm dò, độ bền".
- Chi phí: vài giờ GPU. GPU không phải giới hạn của dự án.

**P0-4. Gold mù do người đọc trên chính bộ cuối.**
- Vì sao: D2. Đây là việc quyết định mức tin của mọi số còn lại.
- Chuẩn hiện nay: các bộ gần nhất đều có người kiểm (mục 3). Danh mục BetterBench (NeurIPS 2024, 46 tiêu chí cho benchmark) [WEB] là bảng tự soát nên dùng; dự án đã có checklist 12 mục tương tự.
- Việc nhỏ nhất: 60–80 dòng rút phân tầng từ 156 lineage, đủ 23 dòng T6. Người đọc chưa thấy đáp án của kho, đọc văn bản gốc. Báo tỷ lệ khớp **thô trước phân xử** và sau phân xử, tách riêng. Tính lại F1–F6 trên phần này. Xem lại dòng G002.
- Chi phí: 10–13 giờ người (ước lượng của audit 13/11). Việc 1.1 trong REFACTOR_PLAN.

**P0-5. Người thứ hai kiểm nhãn.**
- Vì sao: D1.
- Chuẩn hiện nay: phép thử alt-test (Calderon, Reichart, Dror; ACL 2025) [WEB] là cách chứng minh "nhãn của AI không kém nhãn của một người". Nó cần ít nhất ba người gán và 50–100 mẫu.
- Việc nhỏ nhất nếu không đủ ba người: hai người gán mù 100 dòng (50 `dat`, 50 `khong_dat`), báo đồng thuận người–người và người–AI. Thêm luật sư kiểm 30 dòng `dat` (việc N1 trong kế hoạch). Không gọi là alt-test nếu chưa đủ điều kiện.
- Chi phí: 6–10 giờ người (ước lượng của tôi).

**P0-6. Ẩn danh và preprint.** *Cần CMT quyết.*
- Vấn đề: repo công khai có tên tác giả và chứa bản thảo trùng tiêu đề. Reviewer tìm tiêu đề là ra.
- Việc: trước khi nộp, đưa bản thảo ra khỏi repo công khai hoặc chuyển repo sang riêng tư (lịch sử git vẫn giữ file cũ); dùng dịch vụ ẩn danh cho link code và dữ liệu; bỏ tên, email, link GitHub trong bản nộp; không đăng arXiv trước 19/04/2027.
- Kế hoạch chính (quyết định 05/11) đã ghi "phải xem lại trước khi nộp hội nghị". Đây là lúc xem lại.

**P0-7. Đổi sang mẫu ACM `sigconf` và sửa trình bày** (mục 8).

### P1. Tăng mạnh sức thuyết phục

**P1-1. Retriever mạnh, áp đều cho mọi nấc.**
- Vì sao: M3. Câu hỏi của reviewer: "retriever mạnh thì lợi ích của bộ lọc còn không?"
- Cách làm chuẩn: lấy 100 ứng viên, xếp lại bằng cross-encoder, giữ 20.
  - Reranker: `BAAI/bge-reranker-v2-m3` (đội dự thi truy xuất pháp luật VLSP 2025 dùng) [WEB]; `AITeamVN/Vietnamese_Reranker` (tinh chỉnh từ model trên, khoảng 1,1 triệu bộ ba) [WEB]; ViRanker (arXiv 2509.09131) [WEB].
  - Embedding: BGE-M3; multilingual-e5-large; `AITeamVN/Vietnamese_Embedding`. Trên VN-MTEB (Findings EACL 2026), các model e5 đa ngữ và BGE-M3 dẫn ở nhiều tập truy xuất [WEB].
  - BM25: tách từ tiếng Việt thay cho âm tiết rời nối OR [NHỚ].
  - Cảnh báo: số trên thẻ model là tự báo, có thẻ đo ngay trên tập huấn luyện [WEB]. Tôi không tìm thấy bảng so sánh độc lập trên văn bản luật Việt Nam. Phải tự đo trên dev.
- Thiết kế: bảng 2×2 {retriever hiện tại, retriever mạnh} × {không lọc, lọc khoảng}, thêm `bvdate`.
- Dự đoán [GT]: lợi ích của bộ lọc vẫn còn, vì reranker không thấy ngày và hai phiên bản thường gần giống lời văn. Nếu đúng, đây là kết quả độ bền rất đáng giá. Nếu sai, phải viết lại thông điệp chính. Cả hai đều đáng biết trước reviewer.
- Trần ước tính nếu mọi căn cứ đúng lên hạng 1: khoảng +0,11 Accuracy [SL của audit, không phải số đo].
- Cần: amendment; chỉnh trên dev; báo "thăm dò" hoặc dựng test mới. Quyết định mở lại reranker là của CMT.

**P1-2. Đối chứng GraphRAG thật (LightRAG): đã dựng xong trên Colab, chưa có điểm.**
- Trạng thái ngày 15/11 [XM, `runs/lightrag_20261113/intake.json`]:
  - Xong: dựng đồ thị từ 608 văn bản (5.069 đoạn, 101.330 nút, 35.460 cạnh; khoảng 10,8 giờ; `Qwen/Qwen2.5-14B-Instruct`) và lấy ngữ cảnh cho 512 truy vấn (151 dev, 361 bộ cuối). Kiểm toàn vẹn đạt: đủ 512 mã, không ngữ cảnh rỗng. Hai văn bản bị LightRAG bỏ vì trùng nguyên nội dung với văn bản khác, không mất nội dung.
  - Chưa: sinh câu trả lời và chấm. Colab chỉ làm phần truy xuất. Câu trả lời phải sinh bằng GPT-4o mini với prompt chung, như mọi hệ khác. Vì vậy **chưa có Accuracy của LightRAG**.
- Số đo được ngay, không gọi model, **chỉ trên dev** (130 dòng có đáp án; 85 dòng có đoạn phân biệt phiên bản) [XM, `runs/lightrag_20261113/dev/coverage.json`]:

  | Hệ | Đáp án đúng mốc có trong căn cứ | Lời văn chỉ phiên bản khác có, nằm trong căn cứ | Độ dài căn cứ (trung vị, ký tự) |
  |---|---:|---:|---:|
  | LightRAG | 123/130 | 81/85 | 98.955 |
  | Lai ghép phẳng (`b4`) | 115/130 | 78/85 | 13.235 |
  | Mở rộng một bước (`b5`) | 117/130 | 80/85 | 13.235 |
  | +DocDate (`b7`) | 122/130 | 42/85 | 11.971 |
  | +VersionFilter (`b7plus`) | 125/130 | 4/85 | 11.887 |
  | TV-RAG (`proposed2`) | 125/130 | 8/85 | 12.098 |

  Cách đọc: LightRAG kéo về lượng chữ gấp khoảng 7,5 lần, nên đáp án đúng có mặt nhiều hơn flat RAG. Nhưng lời văn của phiên bản sai cũng có mặt ở gần như mọi dòng, giống flat RAG. Chỉ bộ lọc theo khoảng mới gạt được nó ra. Đây là độ phủ của ngữ cảnh, **không phải Accuracy**: model còn phải tìm và chọn đúng đoạn trong 99.000 ký tự. Dự đoán [GT]: Accuracy của LightRAG gần flat RAG và thấp hơn hệ có lọc. Phải sinh câu trả lời mới biết.
- Ba chỗ không ngang hàng, phải khai khi viết: kho của LightRAG chỉ có 608 văn bản (các hệ khác tìm trên toàn kho); ngữ cảnh dài gấp khoảng 7,5 lần; kho không có ngày hiệu lực. Hai chỗ đầu có lợi cho LightRAG. Nếu LightRAG vẫn thua hệ có lọc thì kết luận càng chắc.
- Việc còn lại:
  1. Dev: gọi API hai lần, ước lượng 0,73 USD mỗi lần. Script đã soạn ở `runs/lightrag_20261113/run_dev_api.sh`, đường nhập và chấm đã thử khô. Chờ CMT đồng ý chi.
  2. Bộ cuối: cần CMT duyệt nháp amendment ADR 0006 (đã soạn trong REFACTOR_PLAN). Ước lượng 1,7 USD mỗi lần, hai lần. Kết quả ghi "thăm dò".
  3. Lấy thêm từ Colab nếu còn: `vllm.log`, phiên bản thư viện, revision model. Gói tải về không có ba thứ này.
- Khi có số: đóng được M5 và dòng lệch "GraphRAG phi thời gian" của đề cương; paper thêm một dòng LightRAG vào bảng mô tả.
- Dẫn GraphRAG-Bench ("When to use Graphs in RAG", Xiang và cộng sự, ICLR 2026) [WEB]: RAG thường ngang hoặc hơn GraphRAG ở câu tra cứu sự kiện đơn. Kết quả của mình khớp với nhận định đó. Viết như vậy thì kết quả "không thấy tác dụng" thành một điểm xác nhận, không phải một thất bại.
- Dẫn dòng GraphRAG có thời gian: T-GRAG (arXiv 2508.01680), TG-RAG (2510.13590), STAR-RAG (2510.16715), DyG-RAG [WEB]. Nêu khác biệt: các hệ đó dựng đồ thị thực thể bằng LLM trên tin tức hoặc báo cáo; ở đây đồ thị là tất định, dựng từ lệnh sửa đổi, và dùng trước lúc truy vấn. Không cần chạy các hệ này.

**P1-3. Bãi bỏ: thêm dữ liệu và một bước quyết định tất định.**
- Hiện trạng: 7/23; đã thử hai lần đưa thông báo bãi bỏ vào prompt, không ăn thua (audit mục 8.1) [XM].
- Cơ sở: AbstentionBench (NeurIPS 2025) cho thấy LLM tự từ chối trả lời kém, và prompt tốt chỉ giúp một phần [WEB]. Vậy không nên để LLM tự quyết "đã hết hiệu lực".
- Hướng làm [GT]: tìm danh tính trước, tra trạng thái sau.
  1. Truy xuất không lọc để tìm điều khoản mà câu hỏi nhắm tới.
  2. Tra bảng khoảng hiệu lực tại ngày hỏi.
  3. Nếu điều khoản đó không còn bản hiệu lực **và** không ứng viên còn hiệu lực nào vượt ngưỡng điểm, trả "hết hiệu lực" kèm lệnh bãi bỏ làm căn cứ.
- Rủi ro: quy tắc của cố vấn là câu hỏi về nội dung thì trả theo quy phạm đang điều chỉnh. Bước 3 có thể khẳng định bãi bỏ sai khi có quy phạm khác thay thế. Vì vậy phải chỉnh ngưỡng trên dev và báo đường precision–recall, không chỉ Accuracy.
- Dữ liệu: MDE giảm theo căn bậc hai của số lineage, nên gấp bốn số dòng thì MDE còn khoảng một nửa [SL, ước lượng thô]. Tính lại bằng script cỡ mẫu của dự án.
- Cần bộ test mới.

**P1-4. Một lát câu hỏi thật.**
- Vì sao: D6 và yêu cầu dữ liệu thật của ICAIL.
- Hướng rẻ [GT]: lấy câu hỏi tư vấn thật từ bộ công khai (ViLegalExpert của UIT, VLQA) mà điều khoản đáp án có từ hai phiên bản trong kho; gắn ngày hỏi; thu 30–50 dòng. Phải kiểm giấy phép và xem bộ đó có ngày hỏi không. Báo riêng, không trộn vào bộ cuối.
- Việc 0 đồng làm ngay: đưa bảng phân tầng theo người viết câu hỏi vào paper và dẫn nghiên cứu về thiên lệch của benchmark do LLM sinh: Silencer (NeurIPS 2025); "What Has Been Lost with Synthetic Evaluation?" (arXiv 2505.22830); "Can we Evaluate RAGs with Synthetic Data?" (arXiv 2508.11758) [WEB].

**P1-5. Đo vế LLM của RQ1 bằng phép chọn một trong hai.**
- Vì sao: thước khớp chuỗi không đo được LLM không truy xuất.
- Hướng làm [GT]: đưa câu hỏi, ngày, và hai đoạn (bản đúng mốc, bản khác); hỏi bản nào áp dụng. Đoán mò được 50%. Không đòi chép lời văn. Chạy 2–3 LLM, có ít nhất một model mở.
- Cách khác, theo Prior 2026: tiêu chí "áp đúng phiên bản" với giám khảo LLM đã so với chuyên gia (κ 0,751) [XM, ghi chú repo]. Dự án đã bỏ giám khảo LLM một lần vì không qua hiệu chuẩn, nên phép chọn một trong hai đỡ rủi ro hơn.

### P2. Nên có

| # | Việc | Cách làm | Ghi chú |
|---|---|---|---|
| P2-1 | Nâng độ phủ kho (40,2%) | Prior 2025: để LLM tự viết lời văn hợp nhất chỉ khớp tuyệt đối 50,3% một bước [XM]. Vậy LLM chỉ nên **phân tích lệnh thành thao tác có cấu trúc**; việc áp dụng giữ tất định và kiểm bất biến như hiện nay [SL] | Sửa kho thì phải dựng bộ test mới |
| P2-2 | Nguồn đối chiếu độc lập | Văn bản hợp nhất cùng cổng nên không độc lập. Lấy mẫu kiểm từ nguồn khác: Công báo, Bộ pháp điển điện tử, cơ sở dữ liệu thương mại [GT] | Kiểm giấy phép trước |
| P2-3 | Một bảng phễu duy nhất | Từ dữ liệu cổng đến ứng viên, đến dòng được giữ | Trả lời D3; REFACTOR_PLAN 4.3 |
| P2-4 | Dao động giữa các lần chạy | Từ 5 lần chạy, hoặc dùng model tại chỗ có seed; báo độ lệch giữa các lần; thêm bootstrap theo văn bản (132 văn bản, đã có số) | Đóng M4 |
| P2-5 | Mốc sát biên | Chạy chế độ `ranh_gioi` làm bảng phụ | Đóng D10 |
| P2-6 | T1 | Duyệt amendment sửa đáp án ngắn (oracle T1 từ 2/43 lên 37/43) [XM] | Có lại cột đối chứng "không làm hại" |
| P2-7 | Tài liệu tham khảo | Paper có 25 nguồn, mỏng cho một bài benchmark. Bổ sung: CALRK-Bench (arXiv 2603.26332), LexKairos (2608.09106), "Can LLMs Time Travel?" (2605.25920), TimelyRAG (2609.11572), FourCorners, GraphRAG-Bench, các bài ở P1-1 đến P1-4 | Đọc bản gốc trước khi dẫn. Hôm nay tôi mới đọc tóm tắt |

---

## 8. Sửa ngay trong bản thảo, không cần thực nghiệm

| # | Chỗ | Vấn đề | Sửa |
|---|---|---|---|
| W1 | Abstract | 280 từ, nhồi cả giới hạn lẫn sáu con số | Rút còn khoảng 180 từ: vấn đề; tài nguyên; ba số chính (cặp oracle, TCS, lọc cứng so với in ngày); một câu giới hạn |
| W2 | Tên "TV-RAG" | Gợi một hệ mới, nhưng paper cho thấy nó không hơn `+VersionFilter` | Gọi là "cấu hình đầy đủ đã khai trước". Đóng góp là kho, benchmark và thang đo |
| W3 | Hình 1 | Dòng flat RAG ghi là "illustrative" | Thay bằng đầu ra thật của một hệ trên một dòng thật. Reviewer không tin ví dụ minh họa |
| W4 | Bảng IV | Cột ghi "hybrid" kèm dấu †, chú thích lại nói phép kiểm dùng lexical | Tách hai cột: truy xuất khi sinh, truy xuất khi kiểm F4–F6 |
| W5 | TV-R@1 | 0,336 ở Bảng V, 0,356 ở Hình 4 cho cùng một nấc | Dùng một mẫu số (295 dòng có đáp án) ở cả hai nơi, hoặc đổi tên cột |
| W6 | Mã nội bộ | `b7plus`, `proposed2`, `b2ctx` xuất hiện trong thân bài | Chỉ giữ tên mô tả; mã để ở phụ lục hoặc repo |
| W7 | Bảng I | Các ô ✗ của bài người khác dựa trên "phần đã đọc" | Đọc hết phụ lục của NitiBench+ và LawInForce-eCFR. Chưa đọc thì ghi "không báo cáo", đừng ghi ✗ |
| W8 | Thiếu ví dụ lỗi | Không có ca cụ thể nào | Thêm 2–3 ca: lời văn gần giống; bãi bỏ qua nút cha; sai dù căn cứ đúng nằm trong prompt |
| W9 | Thiếu khung pháp lý | Không phân biệt "còn hiệu lực" với "được áp dụng" | Thêm một đoạn ngắn, dẫn quy định về hiệu lực và áp dụng văn bản. **Tra số điều bằng công cụ luật trước khi viết, không viết theo trí nhớ** |
| W10 | Giấy phép dữ liệu | Chưa nêu giấy phép phát hành và căn cứ được phát hành lại văn bản luật | Thêm một câu, kèm căn cứ đã tra |
| W11 | Chỗ đỏ | CRediT, tài trợ, email GVHD | Điền |
| W12 | Nguồn arXiv | Nhiều mục còn ghi arXiv | Kiểm bản đã đăng: bài luật thuế Pháp có ghi nhận ở workshop AI4Law của ICML 2026 [WEB]; VN-MTEB ở Findings EACL 2026 [WEB] |

---

## 9. Phản biện giả lập và phán quyết

Năm vai dưới đây do một model đóng trong cùng một phiên. Chúng không độc lập với nhau.

**Vai xét độ hợp nơi nộp (ICAIL).** Đề tài hợp chủ đề. Ba điểm trừ theo đúng lời kêu gọi: chỉ có model đóng; câu hỏi tổng hợp; bản thảo lộ danh tính. Sửa được cả ba.

**Vai phương pháp.** Kỷ luật khai báo trước là điểm cộng hiếm. Điểm trừ: gold chung nguồn với bộ lọc; nhãn AI; phần lớn nội dung hay nhất (`b7v`, `bvdate`, phân tích theo hạng) là hậu nghiệm; hai lần chạy là ít; F6 trùng F5 nên họ kiểm định thực chất là sáu.

**Vai chuyên ngành.** Tính mới so với Prior 2026, LawInForce-eCFR, NitiBench+ là ở ngôn ngữ, ở thang phân rã và ở nhóm bãi bỏ. Thông điệp "lọc theo mốc có lợi" không còn mới. Thiếu phân biệt hiệu lực với áp dụng. Danh mục tham khảo mỏng.

**Vai ứng dụng.** Cặp số 0,956 và 0,456 là thông điệp mạnh cho mọi chatbot luật chỉ đọc bản hiện hành. Điểm trừ: ngày hỏi phải cấp sẵn; kho mới phủ 40% sự kiện; demo chậm.

**Vai phản biện gay gắt nhất.** Lập luận mạnh nhất chống lại paper:

> Paper đo mức các hệ khớp với cái kho do chính tác giả dựng. Đáp án, bộ lọc và chỉ số TVER cùng đọc một bảng. Bộ câu hỏi chỉ gồm điều khoản mà đường ống dựng được. Nhãn do AI gán. Vì vậy F3–F6 sẽ đúng với bất kỳ hệ nào đọc cùng bảng đó, và không nói gì về việc trả lời có đúng luật không. Hệ được đặt tên thì không hơn một điều kiện lọc. Kết quả: chưa phải benchmark đã kiểm chứng, cũng chưa phải phương pháp mới.

Xử lý lập luận này:
- Nửa "chưa phải benchmark đã kiểm chứng": **có cơ sở, chưa giải quyết**. Chỉ P0-4 và P0-5 đóng được. Đây là điều kiện chặn.
- Nửa "chưa phải phương pháp mới": **chấp nhận**. Paper đã tự định vị là tài nguyên và phép đo. Cần làm triệt để hơn (W2).

**Phán quyết giả lập cho bài dài ở ICAIL:** sửa lớn (Major Revision). Lý do chặn: D1, D2, M4 và các lỗi hình thức ở mục 6. Phán quyết này không được hiệu chuẩn với bài thật nào; coi như ý kiến của một người đọc kỹ.

---

## 10. Giới hạn của bản đánh giá này

- Một model, một phiên, cùng họ với model đã giúp viết paper. Không chạy năm agent riêng và không chạy các script kiểm của bộ skill phản biện. Bước kiểm từ viết tắt không chạy được trên file `.tex`.
- Không chạy lại thực nghiệm. Số chép từ paper, `numbers.md`, audit 13/11, REFACTOR_PLAN. Riêng bảng ở P0-1 tôi đọc trực tiếp từ hai file điểm (lần 1 và lần 2) và chưa qua evidence-gate.
- Chưa đọc hết: Chương 2–5 của khóa luận, ADR 0005 và 0006, datasheet, hướng dẫn gán nhãn.
- Phần web: chỉ đọc tóm tắt và trích đoạn do công cụ trả về. Chưa mở toàn văn bài nào hôm nay. Quy định của ICAIL đọc qua công cụ tóm tắt, câu trích bị cắt.
- Tên model ở P0-3 và P1-1 lấy từ thẻ model và kết quả tìm kiếm. Chưa có phép đo độc lập nào trên văn bản luật Việt Nam.
- Chưa tra hạn 2027 của các hội nghị IEEE trong khu vực.
- Số LightRAG ở P1-2 là độ phủ ngữ cảnh trên dev, đo bằng phép khớp đoạn của scorer. Chưa qua evidence-gate. Chưa có số nào của LightRAG trên bộ test cuối.
- Các mục gắn [GT] là đề xuất chưa thử. Không viết chúng vào paper như kết quả.

---

## 11. Nguồn

Trong repo:
- `docs/paper/ieee/main.tex`, `main.pdf`, `numbers.md`
- `docs/DeCuongKLTN_23521635_23521643_UIT.docx`
- `docs/reports/research-audit-20261113.md`
- `docs/plans/active/REFACTOR_PLAN.md`, `docs/plans/active/master-plan.md`
- `docs/thesis/chuong-1-mo-dau.md` mục 1.6, `chuong-7-ket-luan.md`
- `related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md`
- `runs/final_g4_20261112/r1/results.md`, `r1/test/all.score.json`
- `runs/lightrag_20261113/intake.json`, `dev/coverage.json`, `run_intake.sh` (file log chỉ nằm ở máy, không vào git)

Web, tra ngày 15/11/2026:
- ICAIL 2027: <https://icail-vienna-2027.org>, <https://icail-vienna-2027.org/call-for-papers/>
- JURIX 2026, lời kêu gọi: <https://jurix.nl/>
- Alt-test (ACL 2025): <https://arxiv.org/abs/2501.10970>
- BetterBench (NeurIPS 2024): <https://arxiv.org/abs/2411.12990>, <https://betterbench.stanford.edu/>
- AbstentionBench (NeurIPS 2025): <https://arxiv.org/abs/2506.09038>
- GraphRAG-Bench, "When to use Graphs in RAG": <https://arxiv.org/abs/2506.05690>
- TG-RAG: <https://arxiv.org/abs/2510.13590>; STAR-RAG: <https://arxiv.org/abs/2510.16715>; T-GRAG: arXiv 2508.01680
- Silencer (NeurIPS 2025): <https://arxiv.org/abs/2505.20738>; "What Has Been Lost with Synthetic Evaluation?": <https://arxiv.org/abs/2505.22830>; "Can we Evaluate RAGs with Synthetic Data?": <https://arxiv.org/abs/2508.11758>
- ViRanker: <https://arxiv.org/abs/2509.09131>; Vietnamese_Reranker: <https://huggingface.co/AITeamVN/Vietnamese_Reranker>; Vietnamese_Embedding: <https://huggingface.co/AITeamVN/Vietnamese_Embedding>
- VN-MTEB: <https://arxiv.org/abs/2507.21500>
- CALRK-Bench: <https://arxiv.org/abs/2603.26332>; LexKairos: <https://arxiv.org/abs/2608.09106>; "Can LLMs Time Travel?": <https://arxiv.org/abs/2605.25920>; TimelyRAG: arXiv 2609.11572
- "Temporal Misgrounding in Legal RAG": <https://arxiv.org/abs/2608.09393>; "Asking For An Old Friend": <https://arxiv.org/abs/2605.23497>
