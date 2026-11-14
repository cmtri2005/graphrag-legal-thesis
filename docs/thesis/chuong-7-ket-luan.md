# Chương 7. Kết luận và hướng phát triển

> Kết luận sau bộ test cuối (G4, chạy 12–13/11/2026 theo ADR 0006). Số kết quả lấy từ Chương 6; số về kho phiên bản và phiếu chấm lại lấy từ nguồn ghi ở chú thích. Mỗi khẳng định giữ đúng mức của nó ở Chương 6: **xác nhận** (họ F1–F7, Holm, khóa trước khi chạy), **thăm dò** (tính sau khi đã thấy kết quả) hoặc **mô tả**.
<!-- nguồn: docs/thesis/chuong-6-thuc-nghiem.md §6.6; docs/decisions/0006-ke-hoach-phan-tich-bo-test-cuoi.md -->

## 7.1. Đóng góp đã có

**Kho văn bản có phiên bản.** Khóa luận dựng được đường ống từ văn bản nguồn và quan hệ sửa đổi đến chuỗi lời văn có phiên bản, khoảng hiệu lực và corpus truy xuất. Biểu diễn tách danh tính điều khoản khỏi phiên bản, nên một câu hỏi được đặt thành cặp câu hỏi–mốc và căn cứ đã dùng truy ngược được. Các kiểm tra nội bộ chứng minh khả năng tái dựng và tính nhất quán. Chúng chưa chứng minh lịch sử pháp luật được dựng đầy đủ hoặc đúng độc lập với nguồn (§7.2).
<!-- nguồn: docs/thesis/chuong-3-kho-van-ban-va-do-thi.md -->

**ViLexTime bản cuối.** 199 lineage, 361 dòng có mốc ở giữa khoảng hiệu lực; lát `all` gồm T2, T3, T6 với 156 lineage và 318 dòng; T1 (43 lineage) là đối chứng. Phép chấm tương phản đòi câu trả lời chứa đáp án của bản tại mốc và không chứa đoạn chỉ bản khác có. Nhãn thuộc tầng "AI-A/AI-B gán mù, CMT duyệt" (`ai_cmt`), chưa có luật sư hay người độc lập kiểm. Vì vậy ViLexTime là tài nguyên có xuất xứ và hồ sơ sai sót, chưa phải chuẩn vàng pháp lý.
<!-- nguồn: docs/thesis/chuong-6-thuc-nghiem.md §6.6; docs/thesis/chuong-4-vilextime.md -->

**Thước đo đã được người kiểm một phần.** Accuracy của scorer khớp người chấm 96/100 câu, không có câu nào scorer chấm đúng mà người chấm sai. Bản chấm đầu là 95/100; sau khi thấy các dòng lệch, người chấm đổi một nhãn theo hướng khớp scorer. Mẫu gồm `b1`, `b4`, `proposed2`, lần 1, T2/T3/T6, không có T1; một người chấm, là tác giả. Trong phạm vi đó, không cần giám khảo LLM cho Accuracy (§6.6.5).
<!-- nguồn: runs/posthoc_g4_20261113/human_score/agreement.json -->

## 7.2. Trả lời câu hỏi nghiên cứu

### RQ1. LLM và RAG hiện có sai phiên bản đến mức nào (mô tả)

- **RAG phẳng sai phiên bản thường xuyên.** Trên bộ cuối, lần 1, câu trả lời của `b2ctx` và `b4` chứa đoạn chỉ phiên bản khác có ở 0,253 và 0,291 trong 265 dòng có đoạn phân biệt phiên bản. Accuracy chỉ 0,302 và 0,324. Đây là số theo scorer; phiếu người chưa xác nhận độ lớn của tỷ lệ sai phiên bản (§6.6.5).
- **Cỡ của bài toán thời gian.** Khi được cấp sẵn căn cứ, cùng generator đúng 0,956 với bản đúng mốc nhưng chỉ 0,456 với bản hiện hành.
- **LLM không truy xuất gần như không trả lời đúng.** `b1` (GPT-4o mini) có Accuracy 0,006; người chấm thấy 2/34 câu đúng, phần lớn sai nội dung. Tỷ lệ sai phiên bản của nó chưa đo được, và mới có một LLM.
<!-- nguồn: runs/final_g4_20261112/r1/results.md; runs/posthoc_g4_20261113/human_score/agreement.json -->

### RQ2. Hệ đề xuất so với đối chứng (xác nhận)

Hệ đề xuất `proposed2` hơn RAG phẳng lai ghép (`b4`) và hơn mở rộng đồ thị phi thời gian một bước (`b5`), ở cả hai lần chạy:

| F | So sánh | Lần 1 | Phán quyết |
|---|---|---|---|
| F1 | P − `b4`, Accuracy | +0,343 [+0,283; +0,401] | ủng hộ, ổn định |
| F2 | P − `b5`, Accuracy | +0,355 [+0,297; +0,414] | ủng hộ, ổn định |
| F3 | P − `b4`, `wrong_version` | −0,283 [−0,330; −0,237] | ủng hộ, ổn định |
<!-- nguồn: runs/final_g4_20261112/r1/confirm.json; runs/final_g4_20261112/compare_runs.json -->

Scorer không chấm dễ dãi (§6.6.5). Trên mẫu người chấm, `proposed2` vẫn hơn `b4` rõ (23/33 so với 10/33 câu đúng), cùng chiều F1; đây là mô tả, không phải phép so ghép cặp. Độ lớn của F3 là theo scorer. `b5` là mở rộng một bước tự xây, không phải GraphRAG đầy đủ; so với một GraphRAG thật (LightRAG) chưa có kết quả.

### RQ3 và giả thuyết đề cương: lợi ích đến từ đâu

**Xác nhận.** Lọc theo ngày văn bản (F4, +0,078) và lọc theo khoảng phiên bản (F5, +0,115) đều tăng TV-Recall@1. F6 (`b7pp` − `b7`, +0,115) ủng hộ, nên theo quy tắc đã khóa, giả thuyết đề cương được **ủng hộ**, kèm ghi chú lần lặp test 2 trước đó không đủ bằng chứng.

**Nhưng F6 bằng đúng F5 (mô tả).** `b7pp` chỉ khác `b7plus` ở chỗ lan truyền khoảng hiệu lực. Lan truyền này không đổi kết quả TV-R@1 ở dòng nào có đáp án; căn cứ đứng đầu chỉ đổi ở 1/295 dòng, và cả hai đều sai. F6 được ủng hộ hoàn toàn nhờ bước lọc khoảng phiên bản. Không được đọc F6 là bằng chứng cho lan truyền hay cho việc duyệt đồ thị lúc truy vấn.

**Thăm dò, sau khi đã thấy kết quả:**
- Accuracy trên `all`, lần 1: `proposed2` − `b7pp` +0,006 [−0,016; +0,028]; `proposed2` − `b7plus` +0,013 [−0,009; +0,035]. KTC chứa 0 ở cả hai lần: không thấy lợi ích lớn hơn khoảng 4 điểm từ phần đồ thị lúc truy vấn.
- TV-R@1: kho phiên bản không có bộ lọc còn kém lớp lời văn gốc (`b7v` − `b7` −0,044), và cần bộ lọc mới có lợi (`b7plus` − `b7v` +0,159).
- Lọc cứng trước khi xếp hạng còn giá trị riêng so với chỉ in khoảng hiệu lực vào prompt (Accuracy `b7plus` − `bvdate` +0,245 [+0,18; +0,31] lần 1, +0,230 [+0,17; +0,29] lần 2).
<!-- nguồn: runs/final_g4_20261112/r1/confirm.json; runs/posthoc_g4_20261113/attribution.json; runs/posthoc_g4_20261113/test/ -->

**Kết luận cho RQ3 (xác nhận).** Lợi ích đo được đến từ hai nấc lọc: lọc theo ngày văn bản (F4) và **kho phiên bản kèm lọc khoảng hiệu lực** (F5). Đồ thị đóng vai **ngoại tuyến**: dựng lịch sử sửa đổi và tính khoảng hiệu lực. **(Thăm dò)** Trên `all`, phần đồ thị lúc truy vấn không cho thấy lợi ích Accuracy lớn hơn khoảng 4 điểm; ngoại lệ thăm dò là T6 không đáp án (+0,174 so với `b7plus`, mục dưới). Đề cương đặt giả thuyết vào biểu diễn đồ thị; kết quả ủng hộ ở mức biểu diễn phiên bản dựng từ đồ thị, không ở mức duyệt đồ thị khi trả lời.

### Bãi bỏ (T6)

- **Xác nhận:** F7 (P − `b7pp`, T6 không đáp án) **không đủ bằng chứng** ở cả hai lần: +0,087 [0,000; +0,217] và +0,043 [0,000; +0,130]. Chỉ có 23 lineage, MDE khoảng 0,185, nên đây không phải bằng chứng hiệu ứng bằng không.
- **Thăm dò:** `proposed2` − `b7plus` trên T6 không đáp án là +0,174 [+0,043; +0,348] ở cả hai lần. `proposed2` khẳng định "hết hiệu lực" 11 lần, đúng 7 (precision 0,64; recall 7/23).
- Nhận diện bãi bỏ vẫn yếu, kể cả với hệ tốt nhất (recall 7/23).
<!-- nguồn: runs/final_g4_20261112/r1/confirm.json; runs/posthoc_g4_20261113/attribution.json -->

### Độ bền của kết luận

- **Gold mù do người đọc nguồn** phủ 24/156 lineage (53 dòng, không có T6 và T1). Trên phần này, chấm vẫn bằng gold đồ thị (gold mù khớp 119/120 sau phân xử do AI đề xuất, CMT xác nhận), F1–F6 cùng chiều với toàn bộ cuối ở cả hai lần. Đây là mô tả trên tập con nhỏ, không thay gold độc lập.
- **Người chấm câu trả lời** khớp scorer 96/100 (bản đầu 95/100; một người chấm, mẫu không có T1).
- **(Thăm dò) Xếp hạng là nút thắt lớn:** khi căn cứ đúng đứng hạng 1, `proposed2` đúng 102/107 (95%); nhưng căn cứ đúng chỉ đứng hạng 1 ở 107/295 dòng có đáp án. Trong 247 dòng có căn cứ đúng trong prompt, `proposed2` vẫn sai 46 (5 khi căn cứ đúng ở hạng 1, 41/140 khi ở hạng 2 trở xuống).
<!-- nguồn: runs/posthoc_g4_20261113/gold_subset/; runs/posthoc_g4_20261113/human_score/agreement.json; runs/posthoc_g4_20261113/attribution.json -->

## 7.3. Điều chưa thể kết luận

- **Tỷ lệ sai phiên bản theo người.** Phiếu người chấm 100 câu (§6.6.5) không hiện phiên bản khác. Phiếu chấm lại 33 câu có hiện mọi phiên bản đang chờ người chấm.
- **Vế LLM của RQ1:** mới có một LLM không truy xuất.
- **Cơ cấu dữ liệu lệch đề cương:** T2 127 lineage, T6 23, T3 6, không có T5; cột T1 chờ amendment sửa đáp án ngắn.
- **Thước đo chưa độc lập hoàn toàn.** Gold phiên bản lấy từ cùng đồ thị mà bộ lọc dùng; gold mù chỉ phủ 24/156 lineage; TVER theo người chưa làm; M2 chưa làm được (0/100 truy vấn có gold người).
- **Nhãn bộ cuối** là silver-AI có CMT duyệt, chưa có người độc lập kiểm. Đồng thuận AI–AI trước hòa giải AC1 0,608, dưới ngưỡng 0,80. Ca khó do agent `legal-adjudicator` chốt, CMT ủy quyền, chưa qua luật sư.
- **Phạm vi:** một generator (GPT-4o mini); một nguồn dữ liệu (vbpl); chưa so với GraphRAG phi thời gian thật.
- Lan truyền chưa có bằng chứng lợi ích, còn nhóm bãi bỏ đã có ở NitiBench+; đặc thù cần kiểm là lệnh ở văn bản khác và bãi bỏ qua nút cha của nguồn Việt Nam. Các tiền lệ gần về lợi ích lọc theo mốc gồm Prior, LawInForce-eCFR và NitiBench+ [@prior2026oldfriend] [@yao2026lawinforce] [@akarajaradwong2026nitibenchplus]. Khóa luận chỉ giữ luận điểm hẹp: phép đo trên pháp luật Việt Nam, hai nấc lọc ngày văn bản và khoảng phiên bản. Chưa có bằng chứng cho thứ tự công bố hoặc ưu thế chung; các nguồn bị chặn và phần chưa đọc vẫn có thể đổi cách định vị. [CẦN: đọc đủ các phần và phiên bản còn thiếu đã nêu trong chương tổng quan].
<!-- nguồn: docs/plans/active/REFACTOR_PLAN.md; related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md -->

## 7.4. Hướng phát triển

- **Thước đo:** người độc lập kiểm nhãn bộ cuối; gold mù phủ T6 và các lineage còn lại; TVER theo người; luật sư kiểm ngẫu nhiên.
- **Kho phiên bản:** nâng độ phủ áp dụng sự kiện (hiện 3.238/8.046 = 40,2%) và đối chiếu rộng hơn với văn bản hợp nhất. Sửa đồ thị thì phải dựng lại bộ dữ liệu và chạy mọi hệ trên một bộ test mới, vì bộ cuối đã xem.
- **Hệ truy vấn:** phân tích thăm dò cho thấy xếp hạng là nút thắt lớn (căn cứ đúng chỉ đứng hạng 1 ở 107/295 dòng), nhưng vẫn có 46 câu sai dù căn cứ đúng đã nằm trong prompt. Hướng có triển vọng là xếp hạng tốt hơn, áp đều cho mọi hệ, và nhóm câu hỏi thật sự cần đi theo dẫn chiếu tại đúng mốc, nơi đồ thị lúc truy vấn có thể có ích.
- **Độ bền:** thêm generator khác họ và vài LLM không truy xuất.
- **Phạm vi dài hạn:** ngoại lệ theo đối tượng, không gian và xung đột quy phạm cần thiết kế và bằng chứng riêng, ngoài đề cương hiện tại.

[CẦN: tác giả và GVHD rà cách trình bày đóng góp, phạm vi và các phần chưa hoàn tất trước khi nộp].
<!-- nguồn: docs/plans/active/REFACTOR_PLAN.md, Nhóm 4 và 5; docs/DeCuongKLTN_23521635_23521643_UIT.docx -->
