# Verifiable Reasoning Framework for Legal Question Answering via RAG and Symbolic Rules

> Ghi chú đọc chi tiết cho khóa luận ViLexTime. Nguồn: `related_paper/Verifiable_Reasoning_Framework_ICOCO2026_CameraReady (1).pdf` (6 trang, bản camera-ready ICOCO 2026). Bài ngắn: dưới đây ghi lại gần như toàn bộ nội dung kỹ thuật.

## 0. Thông tin chung

| Mục | Nội dung |
|---|---|
| Tác giả | Diem K. T. Pham, Dung V. Dang, Dung Dinh (UIT-VNU-HCM), Hung Q. Ngo (UCD Dublin), José Machado (Univ. of Minho), Tai Huynh\* (Kyanon Digital, MiiN Labs), Hien D. Nguyen (UIT-VNU-HCM) |
| Nơi đăng | ICOCO 2026 (camera-ready; tên hội nghị theo tên file, PDF không nêu rõ trên trang đầu) |
| Loại bài | Khung neuro-symbolic **tích hợp** (tác giả nói rõ: không đề xuất thuật toán suy luận tổng quát mới) |
| Quy mô đánh giá | **443** câu hỏi người dùng thật, 4 miền; **28** văn bản luật; **8.020 luật Horn** |
| Độ gần với ViLexTime | Trung bình: tiếng Việt, cùng nhóm UIT; mô hình luật thành quy tắc **Horn có nhãn nguồn gốc (provenance)**, có nhắc **ràng buộc thời gian** là thuộc tính của luật nhưng **chưa dùng/đánh giá** |

## 1. WHY – Bài toán

- Hỏi đáp pháp lý đòi hỏi câu trả lời không chỉ đúng sự kiện mà phải: (i) được **hỗ trợ bởi điều khoản phù hợp**, (ii) **thỏa mọi điều kiện áp dụng**, (iii) có **quá trình suy luận giải thích được**.
- Quy định thường **nằm rải rác nhiều văn bản**; câu hỏi của người dùng có thể thiếu thông tin hoặc liên quan **nhiều lĩnh vực cùng lúc**.
- RAG cải thiện truy cập văn bản nhưng chủ yếu **sinh trả lời từ đoạn truy hồi**; việc nhận diện và kiểm chứng **điều kiện pháp lý áp dụng** không được hệ thống hóa trước khi suy luận. Phần lớn hệ LQA hiện có để quá trình suy luận và kiểm chứng kết luận **ngầm**.
- Đối chiếu với công trình cùng nhóm: Dang et al. [8] (ACIIDS 2025) kết hợp Legal-Onto + KG + RAG + GPT-4o (bộ ba ngữ nghĩa để truy hồi văn bản rồi sinh đáp án; đánh giá trên **197** câu bằng độ chính xác truy hồi/đáp án). Khung này khác: biểu diễn điều khoản thành **luật Horn bảo toàn nguồn gốc**, truy hồi luật ứng viên, suy diễn tiến, dựng chứng minh tường minh, rồi kiểm chứng với điều khoản gốc. Tác giả nói rõ **không so sánh số liệu trực tiếp** (443 câu, 4 miền, IRAC vs 197 câu, độ chính xác truy hồi/đáp án).
- Nền tảng lý thuyết: lập luận neuro-symbolic (Markov Logic Networks, Logic Tensor Networks, DeepProbLog), RAG, REALM, Self-RAG; benchmark LexGLUE, LegalBench; LEGAL-BERT.

## 2. HOW – Khung đề xuất

### 2.1 Cơ sở tri thức pháp lý (Legal Knowledge Base, mục III)
- Văn bản luật được chuyển thành **luật pháp lý có cấu trúc**, giữ phân cấp **chương – điều – khoản – điểm** theo Luật Ban hành VBQPPL (trích dẫn: Luật số 64/2025/QH15).
- Nhận định: điều khoản Việt Nam thường kết hợp **điều kiện tiên quyết, ngoại lệ, ràng buộc thời gian, tham chiếu chéo**, nên truy hồi đoạn đơn lẻ là không đủ. Do đó KB: giữ phân cấp + provenance; biểu diễn điều kiện và hệ quả thành thân/đầu luật Horn; lưu **ngoại lệ và ràng buộc thời gian dưới dạng thuộc tính của luật**.
- **Biểu diễn Horn** (công thức 1): r_i : h_i ← b_i1, b_i2, …, b_im; h_i là kết luận/hiệu lực pháp lý, b_ij là các điều kiện cần. Ví dụ (công thức 2): "doanh nghiệp phải đăng ký thay đổi người đại diện theo pháp luật": `obligation(X, register) ← enterprise(X), changeRep(X)`.
- Thuộc tính cấu trúc bổ sung (khi áp dụng): **chủ thể áp dụng, hành vi pháp lý, ngoại lệ, ràng buộc thời gian**. Metadata mỗi luật: văn bản nguồn, chương, điều, khoản, điểm, lĩnh vực, **mã luật** → mọi luật dùng khi suy luận truy được về điều khoản gốc.

**Quy trình xây KB 4 giai đoạn (Hình 1)**: (1) tiền xử lý văn bản (chuyển văn bản thuần, chuẩn hóa định dạng nhưng giữ phân cấp); (2) phân đoạn cấu trúc pháp lý (chương/điều/khoản/điểm → đơn vị văn bản pháp lý); (3) **trích luật theo quy tắc (rule-based)**: nhận diện điều khoản quy phạm và xác định hệ quả pháp lý cùng điều kiện tiên quyết (hệ quả = đầu, điều kiện = thân); (4) xây KB và gắn metadata.

### 2.2 Suy luận neuro-symbolic: 4 mô-đun tuần tự (Hình 2)
**A. Semantic Parsing (thần kinh)** — GPT-4o (truy cập tháng 6/2026), prompt không fine-tune, giải mã tất định (temperature 0,0, top-p 1,0). Đầu ra kiểm tra bằng **lược đồ Pydantic hai tầng**: *Layer 1* (ngôn ngữ và ngữ nghĩa pháp lý bề mặt): loại phát ngôn, chủ thể pháp lý, điều kiện, hành vi, tình thái (modality), **thông tin thời gian (temporal information)**, ngoại lệ, tiêu điểm câu hỏi, trạng thái khẳng định; *Layer 2* (chuẩn hóa): biểu diễn chủ thể, **nguyên tử điều kiện logic**, sự kiện của vụ việc, mục tiêu pháp lý dạng vị từ–đối số → tạo **Structured Legal Query**. Ba bước: (1) xác định chủ thể và hành vi pháp lý (loại thông tin mô tả không liên quan); (2) trích các **sự kiện** có liên quan pháp lý nêu tường minh (thuộc tính cá nhân, tình trạng pháp lý, **thông tin thời gian**, định lượng) — chỉ giữ cái có trong câu hỏi, loại giả định; (3) xác định mục tiêu pháp lý đích (hệ quả cần suy ra). Cảnh báo của tác giả: lỗi ở parsing lan truyền xuống dưới (nhầm chủ thể/hành vi → truy hồi sai luật; thiếu hay chuẩn hóa sai sự kiện → không thỏa tiền đề; sai mục tiêu → suy luận đi tới kết luận khác); **chứng minh hợp lệ hình thức không đảm bảo đúng ngữ nghĩa nếu truy vấn có cấu trúc đã biểu diễn sai câu hỏi**.

**B. Candidate Rule Retrieval (ký hiệu)** — truy hồi **luật có cấu trúc**, không phải đoạn văn. (1) Khớp luật: so khớp mục tiêu, chủ thể, hành vi và sự kiện với các **vị từ** của luật; dùng metadata (lĩnh vực, mã văn bản) để lọc và ưu tiên, giữ truy vết; tập ứng viên có thể gồm luật từ **nhiều văn bản/lĩnh vực** khi cần suy luận liên miền. (2) Xây tập luật ứng viên (giữ biểu diễn lô-gic và metadata) → thu hẹp không gian suy luận mà vẫn giữ các luật liên quan.

**C. Forward Reasoning (Hình 3)** — suy diễn tiến trên luật Horn (Russell & Norvig): từ sự kiện, lặp áp dụng luật đã thỏa và thêm kết luận, đến khi đạt mục tiêu hoặc điểm bất động; ghi lại luật áp dụng và kết luận trung gian thành chứng minh nhiều bước. Bốn bước: (1) khởi tạo tập sự kiện làm việc (từ sự kiện vụ việc), nạp tập luật ứng viên làm không gian suy luận, mục tiêu là điều kiện dừng; (2) mỗi vòng, xác định luật áp dụng được: mọi vị từ trong thân được hỗ trợ bởi sự kiện hoặc kết luận trước đó (luật chưa thỏa được giữ lại cho vòng sau); (3) suy ra đầu luật và thêm ngay vào tập sự kiện (hỗ trợ multi-hop xuyên luật, xuyên lĩnh vực khi cần); lặp đến khi đạt mục tiêu hoặc không suy ra thêm; (4) **dựng chứng minh**: với mỗi kết luận suy ra, ghi sự kiện hỗ trợ, luật áp dụng, kết luận trung gian và hệ quả.

**D. Verification and Answer Generation** — (1) xác định các điều khoản pháp lý được tham chiếu trong chứng minh (lấy mã văn bản, mã luật, metadata); (2) **truy hồi văn bản gốc** (chương/điều/khoản/điểm) từ kho văn bản gốc làm bằng chứng thẩm quyền; (3) **LLM kiểm chứng**: luật áp dụng có được điều khoản trích dẫn hỗ trợ không, kết luận có nhất quán với văn bản không, có diễn giải không được hỗ trợ hay mâu thuẫn không; (4) sinh câu trả lời tự nhiên, **chỉ thị bảo toàn kết quả đã kiểm** và không thêm kết luận không có căn cứ hoặc sửa căn cứ pháp lý đã xác nhận.

## 3. Thực nghiệm (mục V)

### 3.1 Thiết lập
- **Cơ sở tri thức**: 28 văn bản pháp luật chính thức Việt Nam thuộc **bảo hiểm xã hội, doanh nghiệp, thuế, và liên lĩnh vực**. Sau tiền xử lý: **207 chương, 3.160 điều, 5.417 khoản, 7.167 điểm**; trích ra **8.020 luật Horn**, mỗi luật gắn văn bản–chương–điều–khoản–điểm.
- **Tập đánh giá**: **443 câu hỏi người dùng thật** từ các website tư vấn pháp luật công khai, kèm **đáp án và căn cứ pháp lý do luật sư cung cấp**.
- **Hệ so sánh**: Qwen2.5-7B-Instruct, GPT-4o, cùng prompt và giải mã tất định (temperature 0,0; top-p 1,0).
- **Chỉ số IRAC**: năm chiều **Issue (I), Rule (R), Analysis (A), Conclusion (C), Legal Grounding (L)** + điểm IRAC tổng; **một annotator** chấm thủ công từng câu trả lời so với đáp án và căn cứ của luật sư (chỉ làm tham chiếu, không phải đánh giá độc lập thứ hai).

### 3.2 Kết quả (Bảng I – điểm IRAC)
| Miền | Số câu | Qwen2.5-7B | GPT-4o | **Phương pháp đề xuất** |
|---|---|---|---|---|
| Bảo hiểm xã hội | 196 | 50,66 | 60,68 | **80,92** |
| Doanh nghiệp | 119 | 50,87 | 59,01 | **71,22** |
| Thuế | 69 | 49,64 | 61,90 | **68,88** |
| Liên lĩnh vực (cross-domain) | 59 | 38,01 | 47,43 | **77,82** |
| **Toàn bộ** | **443** | 48,87 | 58,66 | **76,03** |

- Vượt cả hai baseline ở mọi miền; **tăng lớn nhất ở câu liên miền** (77,82 vs 47,43 của GPT-4o, +30,4 điểm) → suy luận ký hiệu có lợi khi cần tích hợp nhiều điều khoản. Trong các miền đơn: Bảo hiểm xã hội cao nhất; Doanh nghiệp và Thuế khó hơn (điều kiện đa dạng, nhiều quy định).
- Định tính: GPT-4o trả lời trôi chảy, hợp lý; Qwen2.5 xử lý tốt câu đơn giản; **cả hai hay bỏ sót điều kiện pháp lý thiết yếu, trích căn cứ không đầy đủ hoặc kết luận vội**, rõ nhất ở câu liên miền. Phương pháp đề xuất tách bạch truy hồi luật – suy luận ký hiệu – kiểm chứng – sinh trả lời; kết luận chỉ được suy ra sau khi đủ điều kiện ở bước suy diễn tiến.
- Tác giả nhấn mạnh: đóng góp chính **không** nằm ở sinh ngôn ngữ mạnh hơn mà ở **bổ sung năng lực suy luận pháp lý tường minh và truy vết** cho mô hình ngôn ngữ.

## 4. Hạn chế (do tác giả nêu) và nhận xét phê phán
- **Tác giả nêu**: chấm **một annotator**, không có độ tin cậy giữa người chấm; chưa chú giải riêng mức độ đầy đủ hay mơ hồ của câu hỏi; lỗi semantic parsing có thể lan xuống phía sau; hướng tương lai: mở rộng KB, cải thiện multi-step reasoning, **tự động hóa cập nhật pháp luật** ("automate legal updates").
- **Người đọc bổ sung**:
  - Baseline yếu: chỉ Qwen2.5-7B và GPT-4o **không truy hồi**; **không so với RAG chuẩn** (BM25/dense/hybrid) hay GraphRAG, nên không tách được lợi ích của "suy luận Horn" khỏi lợi ích của "có tri thức pháp lý bên ngoài". Mức so sánh với "cùng prompt" nhưng không rõ baseline có được cấp văn bản luật hay không.
  - **Chỉ số IRAC tự động hay thủ công?** Là thủ công bởi một người chấm; điểm 76,03 và chênh lệch lớn chưa được kiểm nghiệm thống kê, không có CI.
  - **Tập đánh giá tự thu từ diễn đàn tư vấn**, đáp án vàng của luật sư (không có bước xác minh thứ hai như VLQA).
  - **Không dùng thời gian**: dù KB lưu "ràng buộc thời gian" làm thuộc tính và parsing Layer 1 có "temporal information", bài **không mô tả** cách ràng buộc này được dùng khi suy diễn, không có thí nghiệm theo thời điểm, và KB gồm **28 văn bản** hiện hành (không có phiên bản). Đây là chỗ ViLexTime có thể mở rộng.
  - Trích luật Horn bằng **quy tắc** (rule-based) chưa báo độ chính xác/độ phủ; 8.020 luật từ 3.160 điều (khoảng 2,5 luật/điều, hoặc ~0,6 luật/đơn vị khoản–điểm) — bài không cho biết tỷ lệ điều nào được/không được chuyển thành luật; chưa có phân tích xử lý phủ định, ngoại lệ lồng nhau, quy định "trừ trường hợp".
  - Kiểm chứng cuối là **LLM-based verifier** (không tất định); phụ thuộc GPT-4o (truy cập tháng 6/2026, khó tái lập).
  - Bài rất ngắn (6 trang) nên thiếu chi tiết triển khai (thuật toán khớp luật, cách chuẩn hóa vị từ, ngưỡng).

## 5. Dùng gì cho khóa luận ViLexTime
1. **Biểu diễn luật dạng Horn có provenance** (metadata: văn bản, chương, điều, khoản, điểm, lĩnh vực, mã luật) là một lựa chọn lớp "quy tắc" bên cạnh lớp đồ thị; thuộc tính **ràng buộc thời gian** của luật có thể mở rộng thành `valid_from/valid_to` và điều kiện chuyển tiếp, cho phép suy luận "luật nào áp dụng tại ngày t" bằng chứng minh tường minh, có thể chấm tất định (so luật áp dụng với luật vàng).
2. **Lược đồ semantic parsing hai tầng (Pydantic)** có trường *temporal information* và *exceptions*: dùng làm khuôn trích **ngày tham chiếu** (as-of date) từ câu hỏi người dùng trước khi truy hồi (liên hệ báo cáo Temporal GraphRAG: "trích as-of date từ query, mặc định hôm nay" và chính sách mặc định ở SAT-Graph RAG).
3. **Kiến trúc tách 4 tầng** (parse → truy hồi luật → suy diễn → kiểm chứng/sinh) giống các agent trong ViHERMES (Interpreter/Pathfinder/Auditor/Conductor) và LegalGraphRAG (Researcher/Auditor/Adjudicator): khóa luận có thể trình bày một mô hình "bốn vai" nhất quán và so sánh ba công trình.
4. **Kiểm chứng với văn bản gốc** (truy hồi lại đoạn gốc theo mã provenance rồi kiểm) là cách giảm ảo giác; ở ViLexTime nên kiểm bằng **so khớp tất định phiên bản và nugget** trước, LLM verifier chỉ là lớp phụ.
5. **Chỉ số IRAC** (Issue–Rule–Analysis–Conclusion–Legal grounding) có thể làm thước đánh giá phụ cho câu trả lời dài; nhưng cần ≥2 người chấm và κ (bài này chỉ một người).
6. **Điểm nhấn thực nghiệm**: tăng mạnh nhất ở câu **liên miền** (nhiều điều khoản) → hỗ trợ lập luận rằng câu hỏi cần ghép nhiều văn bản/phiên bản mới là nơi cấu trúc tường minh thắng.
7. **Cẩn trọng**: baseline chưa có RAG; đánh giá một người; quy mô nhỏ (28 văn bản, 443 câu); không dùng thời gian thực sự. Dùng để định vị: *"neuro-symbolic cho luật VN có provenance nhưng chưa temporal"*, cùng nhóm tác giả với Legal-Onto (`infor617`) và Intelligent search (`peerj-cs-1786`).
