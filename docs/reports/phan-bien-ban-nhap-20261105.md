# Phản biện bản nháp 05/11/2026

Phản biện trong dự án do một phiên AI (`thesis-critic`) làm, chỉ đọc; không phải phản biện ngoài. Lead đã tự kiểm lại mục C5 (nấc lan truyền).

## Phản biện bản nháp khóa luận và paper ViLexTime (đọc bản trên đĩa sau 3fb745e và 2c0e854)

**Kết luận chính.** Tôi đối chiếu hơn 40 số ở chương 4, 6, 7 và paper với file trong `runs/` và `data/`. Mọi số đều khớp. Accuracy test 2 trong các bảng đều lấy từ `rescore`, không lấy từ lần chấm sai (lần sai: `b1` 0,903, `b7` 0,885). Lỗi nằm ở chỗ khác:
- **Vòng tự chấm chưa có lối thoát.** TVER, Verifier và thông báo bãi bỏ của `proposed3` đều đọc cùng nguồn đồ thị với gold.
- **Đổi vai v1.0 và test 2 thành "vòng thử" sau khi đã thấy kết quả**, mà bản nháp không nói rõ.
- **Bảng lệch đề cương (§1.6) thiếu nhiều dòng.** Chính tài liệu định nghĩa đã yêu cầu đưa các dòng đó vào.
- **Hai "phần riêng" còn lại của paper chưa có bằng chứng:** nấc lan truyền và nhận diện bãi bỏ.

**Cách kiểm.** Chỉ đọc. Tôi chạy script Python chỉ đọc (`/tmp/claude-1000/-home-trica-UIT-Thesis-graphrag-legal-thesis/43cdcfcd-2e78-423b-8d88-80ef236bb0ff/scratchpad/chk1.py` và các lệnh tại chỗ). Tôi không chạy `pytest`. Mỗi mục ghi rõ [đã kiểm] (tự mở file hoặc tính lại) hoặc [suy đoán].

---

### A. CHẶN NỘP (5)

**C1. Gold tự chấm, và thiết kế cuối vẫn coi TVER là kiểm định xác nhận**
- **Ở đâu:** master-plan.md:217 (TVER `b7pp − b7` "kèm bản tính trên gold mù", Xác nhận); chuong-6:39; chuong-6:94 ("H0 được ủng hộ" trên v1.0); paper:334.
- **Sai gì:** TVER của `b7pp` bằng 0 là do cách dựng. Vì vậy nửa H0 (XN2) đúng trước khi chạy.
  - "TVER trên gold mù" không định nghĩa được. TVER chấm *mọi* trích dẫn, phần lớn không phải đơn vị gold, theo `effective_intervals` của đồ thị. Gold mù chỉ kiểm `version_id` của dòng.
- **Bằng chứng [đã kiểm]:**
  - Scorer: `score_vilextime.py:163-164, 216, 459` dùng `v["effective_intervals"]`.
  - `runs/x4_verifier_dev/report.json` tự ghi "Verifier và TVER dùng chung khoảng hiệu lực của đồ thị".
  - TVER `b7pp` = 0,000 [0,000; 0,000] ở cả hai bộ.
  - VBHN: chỉ 2 cặp so được, khớp 1 (`docs/reports/doi-chieu-vbhn.md`).
  - Phiếu gold: `gold_A`/`gold_B` có 0/37 và 0/38 ô điền.
- **Sửa:**
  - Amendment G3 đưa XN2 ra khỏi họ Holm, ghi là "kiểm nhất quán nội bộ". H0 quyết bằng XN1.
  - Thêm một phép kiểm độc lập: rút khoảng 100 đơn vị *được trích* từ `b2ctx`/`b7`/`b7pp`/`proposed*`. Người đọc văn bản gốc, không thấy cửa sổ đồ thị, rồi kết luận đơn vị đó còn hiệu lực tại `as_of` hay không. Báo TVER theo người, kèm Wilson.

**C2. `proposed3` tự cấp đáp án T6 từ cùng nguồn với gold**
- **Ở đâu:** chuong-6:291; master-plan.md:218, 361.
- **Sai gì:**
  - Thông báo bãi bỏ lấy từ sự kiện `repeal` đã phân giải của đồ thị. Gold "không có đáp án" của T6 cũng dẫn từ chính các sự kiện đó.
  - Bộ lọc LLM trước khi đưa người lại ưu tiên dòng có lệnh bãi bỏ rõ (xem N3).
  - Vì vậy mức tăng Accuracy ở dòng bãi bỏ phần lớn là do cách dựng, giống TVER.
- **Bằng chứng [đã kiểm]:** `graphx.py:54-71` (`_repeals`, "Typed resolved events"). Dòng prompt có dạng `BÃI BỎ | đích bị bãi bỏ | ngày hiệu lực`.
- **Sửa:**
  - Khai trước rằng Accuracy T6 của `proposed3` là cận trên khi đồ thị đúng.
  - Chỉ kết luận trên dòng T6 đã qua gold mù.
  - Báo kèm *precision* của khẳng định "đã bãi bỏ" trên dòng có đáp án (V5).

**C3. Đổi vai v1.0 và test 2 thành "vòng thử" sau khi thấy kết quả, chưa có luật gộp ba lần nhìn**
- **Ở đâu:** chuong-6:5 và 150; chuong-4:3; paper:12, 38, 206–209; master-plan.md:459.
- **Sai gì:**
  - ADR 0005 §1 khai v1.0 là bản final. Amendment 03/11 khai test 2 là "bản lặp lại".
  - Ngày 05/11, sau khi test 2 rơi vào nhánh "điểm quyết định B7" (XN1 không đủ bằng chứng), cả hai mới được gọi là "vòng thử có khai báo". Sau đó mở thêm lần nhìn thứ ba cho XN1.
  - Bản nháp viết như thể vai "vòng thử" đã có từ đầu. Đây là bậc tự do lớn nhất mà hội đồng sẽ hỏi.
- **Bằng chứng [đã kiểm]:**
  - ADR 0005:33–41, 211–232.
  - Ngày Accepted `a64a5bc` 29/10 07:10:17. Lần chạy E1 test đầu tiên bắt đầu 07:12:17.
  - confirm.log của test 2: "nhánh điểm quyết định B7".
- **Sửa:**
  - Viết đúng lịch sử: "xác nhận lần 1 và lần lặp lại, đổi vai ngày 05/11 sau khi thấy kết quả".
  - Amendment G3 khai trước: chỉ bộ cuối là xác nhận; báo cả ba phán quyết cạnh nhau, không gộp. Ghi sẵn kết luận cho từng tổ hợp (ví dụ bộ cuối không đủ bằng chứng thì H0 không được ủng hộ).

**C4. Bảng lệch §1.6 thiếu các dòng mà định nghĩa bắt buộc đưa vào**
- **Ở đâu:** chuong-1:77–84 (chỉ 5 dòng).
- **Bằng chứng [đã kiểm]:** `docs/vilextime-dinh-nghia.md:256-266` có mục "Chỗ lệch so với đề cương (đưa vào bảng lệch của khóa luận)". §1.6 không có các dòng sau của mục đó:
  - T1 250 → 150.
  - T3: sàn 120.
  - T5 đổi nghĩa (bỏ vế "có lợi").
  - T6 tách thành T6a sàn 100 và T6b sàn 200, với ghi chú "T6b là bậc lan truyền, phần đóng góp riêng của đề tài".
  - "LLM viết nháp, agent kiểm".
- **Lệch khác chưa khai [đã kiểm]:**
  - Đề cương ghi "1.100–1.300 **câu hỏi**", nay đếm theo cặp (câu hỏi, mốc). Số câu hỏi khác nhau (lineage) mọi tầng nhãn: 165 (test) + 81 (dev) + 101 (test 2) + 168 (silver) = 515, chưa tính T5.
  - T3 trong đề cương là "truy vết A→B→C, đo lợi ích của đồ thị". Thực tế T3 là "≥ 3 đáp án theo mốc", không đòi truy vết.
  - Claude chọn đáp án ngắn, tức chọn chính tiêu chí chấm.
  - Có bước LLM lọc trước khi đưa người.
  - Bốn miền đề cương chỉ chiếm khoảng 36% dòng: `khac` 136/211 dòng test v1.0 và 243/389 dòng silver; đất đai chỉ 5 dòng / 3 lineage (`runs/domain_e3/report.json`, meta `domain`).
  - TCS, VCR, MRR, EM/F1 và LLM-judge chưa báo.
  - L4 hứa "trước tiên lọc", nhưng `rel_up` lấy seed *trước* bộ lọc (chuong-5:117).
- **Sửa:** gộp mục §11 của định nghĩa vào §1.6, thêm các dòng trên kèm số đo.

**C5. Hai "phần riêng" còn lại của paper chưa có bằng chứng**
- **Ở đâu:** paper:60, 66 và 77(b); chuong-1:20; chuong-2:211–215.
- **Nấc lan truyền [đã kiểm]:** `b7pp − b7plus` = +0,000 [0; 0] ở **mọi nhóm, cả hai bộ** (`runs/E1/test/ladder.score.json`, `runs/E1_test2/...`).
  - XN5 chưa từng chạy.
  - Thiết kế cuối (master-plan.md:212–219) không có kiểm định nào cho `b7pp − b7plus`.
  - Dòng "T6 lan truyền" thực ra so phần mở rộng trực tuyến (`proposed2 − b7pp`), không so lan truyền.
  - T6b: test v1.0 có 12 dòng, test 2 có 3 lineage "cấp trên" (ADR:224). Bộ cuối dự báo khoảng 14 lineage T6 *tổng* (master-plan.md:359–361). Sàn 200 của định nghĩa hụt hơn 10 lần.
- **"Nhận diện bãi bỏ" [đã kiểm trong ghi chú đọc]:** NitiBench+ đã có nhóm bãi bỏ (+0,79, `related_paper/notes/...:161, 182`). Ghi chú còn nêu "Sycophants" (EUR-Lex có quan hệ bãi bỏ, :283).
- **Sửa:**
  - Thu (b) về hai nấc đã đo (ngày văn bản và khoảng phiên bản); ghi rõ lan truyền là chưa kiểm được.
  - Hoặc rút có chủ đích ứng viên T6b, cho người gán, sinh câu trả lời cho `b7plus` và khai XN5 trong amendment.
  - Viết lại phần bãi bỏ thành phần đặc thù Việt Nam: lệnh bãi bỏ nằm ở văn bản khác, và bãi bỏ qua nút cha. Dẫn rõ NitiBench+.

---

### B. NẶNG (11)

**N1. Người gán là chính hai tác giả, bản nháp không nói**
- **Ở đâu:** master-plan.md:282 ("Gán nhãn, gold mù, kiểm mẫu, mã hóa lỗi | CMT, NMT, luật sư"); chuong-4:193; phụ lục:12 ("Không suy tên thật của người gán").
- **Sai gì:** người dựng hệ cũng gán test, gold mù và mã lỗi E7. Q4 đòi tìm quy định thay thế trên 17.333 văn bản, nên năng lực pháp lý của người gán là câu hỏi thật.
- **Sửa:** khai vai A/B = CMT/NMT trong chương 4 và paper. Lấy mẫu luật sư kiểm ngẫu nhiên các dòng `dat` của bộ cuối làm thước đo độ đúng chính.

**N2. A đã thấy đáp án đồ thị của silver, và gold mù của A đã dùng hết phần A chưa thấy**
- **Bằng chứng [đã kiểm]:**
  - A đã gán 131/168 lineage silver T2/T3, 283 dòng, 280 `dat`.
  - Phần silver A chưa thấy = **37 lineage = đúng cỡ `gold_A`**.
  - Phần cả A và B đều chưa thấy chỉ có 26 lineage. Gán đôi trong gold chỉ có 15 câu.
- **Sai gì:**
  - Master-plan.md:362 ghi "Nhãn mới của A vẫn độc lập với B". Câu này nói về B, không nói được A có mù với đồ thị hay không.
  - AC1 ở G2 sẽ trộn phần A đã thấy với phần chưa thấy.
  - Gold 120+30 không thể rút thêm từ silver cho A.
- **Sửa:** khai trước rằng AC1 báo riêng trên phần A chưa thấy. Tính lại gold sẽ lấy đủ từ đâu (T6, T3, T2 mới chỉ khoảng 50 lineage).

**N3. Bộ lọc LLM trước khi đưa người gây lệch chọn mẫu (T6 chỉ giữ lại khoảng 5,6%)**
- **Ở đâu:** master-plan.md:359; chuong-4:175 ("LLM lọc trước", không bàn hệ quả).
- **Bằng chứng:**
  - [đã kiểm] Gói lọc là gói cho Claude, kèm chuỗi phiên bản và gợi ý chỗ chuyển của đồ thị. Lúc hiệu chuẩn chấp nhận tỷ lệ loại nhầm tới 30% (`scripts/review/test2_packs.py:2, 13-17, 55`).
  - [đã kiểm] Lời dặn LLM bản 2 loại nhầm 12/39 câu người gán là tốt (`calib_score.json`).
  - [chưa kiểm được] Số 5,6% chỉ có trong master plan. File gốc ở `~/vilextime_loc`, ngoài repo.
  - [suy đoán] T6 còn lại là tập "LLM chấp nhận và đồ thị có lệnh bãi bỏ đã phân giải". Đây đúng là tập mà `proposed3` thắng do cách dựng (C2).
- **Sửa:**
  - Công bố phễu lọc theo mã lý do, lưu trong repo.
  - Người kiểm khoảng 20 câu T6 bị LLM loại, rút ngẫu nhiên, để ước lượng tỷ lệ loại nhầm.
  - Ghi kết quả T6 là có điều kiện theo bộ lọc.
  - Đưa bước lọc vào §1.6.

**N4. Gold mù đợt 1 bỏ qua đúng nhóm mà đồ thị yếu nhất**
- **Bằng chứng [đã kiểm]:**
  - `gold_sample.tsv` có 3 tầng: T3 20, T2-near 20, T2-regular 20. Không có T6, không có T1.
  - Dấu bãi bỏ trong VBHN lệch trạng thái kho 10/24 (`thu-tai-vbhn-20261105.md`) và 0/2 khớp (`doi-chieu-vbhn.md`).
  - Ngưỡng 114/120 có cận dưới Wilson khoảng 0,89 [tự tính].
  - Chưa có quy tắc cho dòng gold sai: bỏ khỏi test hay sửa gold.
- **Sửa:**
  - Đợt 2 có ít nhất 30 dòng T6 trước G2, và có T1 cũ (xem V7).
  - Khai trước: dòng sai giữ lại với gold đã sửa, không loại. Sửa đồ thị thì chạy lại mọi hệ trước G3.

**N5. Bản nháp bỏ qua bằng chứng VBHN bất lợi đã có**
- **Ở đâu:** chuong-3:123 ghi "Chưa có `docs/reports/doi-chieu-vbhn.md` tại lúc soạn", nhưng file đã có và đã commit ở 3fb745e. Paper:89 ghi "chưa có báo cáo đối chiếu hoàn chỉnh".
- **Bằng chứng [đã kiểm]:**
  - Độ phủ: 2/819 mốc silver, 0/492 test 2, 2/487 v1.0. Khớp xác nhận 1/2.
  - Dấu bãi bỏ lệch 10/24 và 2/2.
  - Thử căn: 344 đơn vị có độ giống dưới 0,90.
- **Sửa:** đưa vào chương 3 §3.5 và paper §3.1. Kết luận rõ: VBHN không dùng được làm gold.

**N6. Paper báo chọn lọc: bỏ XN6, XN7 nhưng giữ một phân tích nhóm con thuận lợi**
- **Bằng chứng [đã kiểm]:**
  - Grep: paper không có số XN6/XN7.
  - XN7 v1.0 = −0,154 [−0,274; −0,051], p 0,0042: ngược chiều H2. ADR §4 bắt báo ước lượng, KTC, p. Chương 6 có báo.
  - Paper:430 báo hiệu `proposed − b7pp` ở T2 (+0,087 [+0,022; +0,174]; +0,067 [+0,017; +0,117], khớp file). Tự ghi "chọn sau khi thấy số".
- **Sửa:** thêm bảng XN5–XN7 vào paper. Đặt phân tích T2 trong một bảng đủ nhóm × hệ, có cả chiều xấu.

**N7. Hệ đề xuất cuối chưa được chọn, và so sánh RQ2 bị lẫn nhiều yếu tố**
- **Ở đâu:** master-plan.md:214, 218, 361; chuong-6:291.
- **Sai gì:**
  - RQ2 so `proposed2` − `b5`, nhưng `b5` chỉ dùng từ vựng ở lớp A. Hiệu này trộn lai ghép, lớp B, `rel_up` và Verifier.
  - Dòng T6 dùng `proposed2`, trong khi thông báo bãi bỏ nằm ở `proposed3`.
  - X3 (đổi generator) và X6 (đổi embedding) còn có thể thay cấu hình.
- **Sửa:** amendment G3 ghi một tên hệ, một generator, một embedding. Baseline so RQ2 dùng cùng chế độ truy xuất, hoặc báo theo thiết kế nhân tố.

**N8. "Cách bù" của plan gộp dòng T6 đã thấy**
- **Ở đâu:** master-plan.md:361 ("chạy thêm `proposed2`, `proposed3` trên T6 của v1.0 và test 2, báo gộp").
- **Sai gì:** `proposed3` được thiết kế sau khi thấy 0/15 và 1/16 trên chính các dòng này.
- **Sửa:** không gộp. Báo riêng với nhãn "đã thấy". Thay vào đó, rút thêm ứng viên T6 mới cho người gán.

**N9. Cổng G1 gần như không đo được, và đường lui là hạ chuẩn**
- **Ở đâu:** master-plan.md:251 so với 413.
- **Sai gì:**
  - 30 câu, đòi p_neg ≥ 0,60 cho *từng* câu kiểm Q1–Q4. Mỗi câu kiểm có thể chỉ có vài nhãn âm.
  - Trượt thì thử lô khác (dừng tùy ý). Trượt lần hai thì chuyển sang "một người gán", tức bỏ gán đôi. Điều này mâu thuẫn với dòng "Không hạ ngưỡng".
  - Lô thử lấy từ test 2, vốn viết theo quy trình khác silver (giới hạn trùng chữ 40%, `test2_packs.py:55`).
- **Sửa:** khai trước số nhãn âm tối thiểu để cổng được tính, kèm KTC. Nếu trượt, báo là đồng thuận không đạt, không gọi là G2 đạt.

**N10. Đại lượng chính đổi sau khi thấy test**
- **Bằng chứng [đã kiểm]:**
  - ADR §3: RQ1 dùng Accuracy và `wrong_version`; RQ2 dùng TV-R@1 và Accuracy.
  - Plan (master-plan.md:212–214): RQ1 dùng TVER, `wrong_version`, VCR; RQ2 chỉ dùng Accuracy.
  - Đề cương hỏi RQ2 có "giảm tỷ lệ lỗi này" (sai phiên bản) không. Accuracy không đo đúng điều đó.
  - XN8 và XN9 lặng lẽ rơi khỏi thiết kế cuối.
  - Paper:53 đổi RQ3 từ "biểu diễn đồ thị" thành "biểu diễn phiên bản".
- **Sửa:** amendment liệt kê từng thay đổi kèm "đã thấy gì". RQ2 lấy `wrong_version` (hoặc TVER theo người) làm đại lượng chính cùng Accuracy. Giữ nguyên văn RQ3 của đề cương.

**N11. Colab đợt 2 chạy trên test v1.0 trước khi khóa hệ (G3)**
- **Ở đâu:** master-plan.md:236.
- **Sai gì:** `b3`, `b4`, `oracle` và ablation sẽ có kết quả test *trước* khi chọn lai ghép, embedding (X6) và biến thể `proposed`. Plan ghi "không dùng để chọn cấu hình" nhưng không có cơ chế ngăn.
- **Sửa:** chạy X7 sau commit G3, hoặc chỉ lưu hash và niêm phong file điểm đến G3.

---

### C. VỪA (12)

**V1. Số bộ cuối trong chương 4 đã cũ so với plan mới**
- chuong-4:170–180 vẫn ghi T6 mới 60 → khoảng 25, T3 mới 20 → khoảng 12, mục tiêu khoảng 180.
- Master-plan.md:359–360 nay ghi T6 khoảng 14, T3 khoảng 5, tổng khoảng 150.
- Plan tự mâu thuẫn: §3:104 nói "không thiếu dữ liệu"; §5:169 còn số 180.
- **Sửa:** đồng bộ cả hai nơi.

**V2. Phép tính power bỏ qua Holm và sự lệch giữa hai bộ** [tự tính, xấp xỉ chuẩn]
- SE của test 2 là 0,022. Ở 150 lineage, SE khoảng 0,018. Với hiệu +0,028, power khoảng 0,34; qua Holm khoảng 0,25.
- XN1 trên các dòng không phải T1 của v1.0 là 10/73 = +0,137, gấp khoảng 5 lần test 2.
- Silver được viết theo quy trình của v1.0, nên bộ cuối có thể giống v1.0 hơn test 2. Khi đó "lặp lại" không độc lập với cách sinh câu hỏi.
- **Sửa:** ghi power thật; báo kết quả theo quy trình sinh câu hỏi.

**V3. XN1 v1.0 chỉ dựa vào 10 dòng** [đã kiểm, ladder.score.json]
- T2 đóng góp +6 dòng (23 lineage), T3 +4 dòng (4 lineage). T1 (123 lineage) đóng góp 0.
- Nhãn "196/165" vì vậy làm người đọc tưởng lượng thông tin lớn hơn thật.
- **Sửa:** báo đóng góp theo nhóm. Không so độ lớn với bộ cuối (bộ cuối không có T1).

**V4. TCS, VCR, MRR, EM/F1 có trong file điểm nhưng không báo** [đã kiểm]
- TCS v1.0: `b2ctx` 0,000 → `b7` 0,435 → `b7pp` 0,609 → `proposed` 0,652 (23 cặp).
- TCS test 2: 0 → 0,167 → 0,233 → 0,233 (60 cặp).
- Đề cương gọi T2 là nhóm cốt lõi và liệt kê TCS là chỉ số chính.
- **Sửa:** thêm bảng mô tả.

**V5. Chưa báo precision của khẳng định "đã bãi bỏ"** [đã kiểm]
- Test 2: `b2ctx` nói "không còn hiệu lực" sai ở 12 dòng có đáp án, trong khi chỉ đúng 1/16 dòng bãi bỏ. `b7pp` sai 5, đúng 1. `proposed` sai 4, đúng 1.
- Định nghĩa (dinh-nghia:116) yêu cầu đo "Recall, precision của việc từ chối".
- **Sửa:** báo cả hai, nhất là cho `proposed3`.

**V6. Bộ dữ liệu thiên về truy xuất từ vựng**
- [đã kiểm] Dense R@1 0,253 so với BM25 0,409 trên dev (`runs/README.md`, W2-12).
- [đã kiểm] Top-20 ở T2 v1.0 là 0,978 (master plan D5). Số trùng chữ 0,48/0,30 chưa lưu thành file (paper:155).
- [suy đoán] Câu hỏi viết từ phần lời văn thay đổi, nên lai ghép (L4) khó cho thấy lợi ích trên bộ này.
- **Sửa:** lưu mức trùng chữ từng dòng của bộ cuối; báo kết quả theo tầng trùng chữ.

**V7. T1 chưa chắc là nhóm đối chứng hợp lệ**
- [đã kiểm] Recall sự kiện sửa đổi chỉ 62,2%. Văn bản T1 trải từ 1981 đến 2026.
- [đã kiểm] `b7pp − b7` trên T1 = −0,024 [−0,057; 0,000], chưa giải thích.
- [đã kiểm] 75/123 dòng T1 chỉ có nhãn agent.
- [suy đoán] Một phần T1 có thể là điều khoản đã sửa mà đồ thị bỏ sót.
- **Sửa:** đưa T1 cũ vào gold mù đợt 2.

**V8. Verifier (L5) không có tác dụng do cách dựng**
- [đã kiểm] Master-plan.md:443 ghi `p2a3 ≡ proposed2`.
- [đã kiểm] Cờ của X4 dùng cùng khoảng hiệu lực với TVER. Bật Verifier trên `b2ctx` sẽ kéo TVER xuống một cách máy móc.
- **Sửa:** chương 5 nói thẳng L5 hiện là phép kiểm nhất quán, tác dụng đo được bằng 0.

**V9. "Nhận diện bãi bỏ yếu" có thể chỉ là giới hạn của Qwen 4B**
- [đã kiểm] Ngữ cảnh đúng trên dev chỉ đạt 6/21 và 3/21 ở dòng bãi bỏ. X3 (generator khác) chưa chạy.
- **Sửa:** chạy X3 tối thiểu trên ngữ cảnh đúng của T6. Ghi kết luận là kết quả của Qwen3-4B.

**V10. Ước lượng giờ người và việc của luật sư quá lạc quan**
- Plan ghi luật sư chốt 30–50 dòng lệch. Lịch sử: 101/246 dòng lệch (41%) [đã kiểm D1, manifest]. Với khoảng 250 câu, nên dự trù khoảng 100 dòng.
- G1 và D0 rơi cùng cuối tuần với khoảng 14 giờ gán mỗi người.
- **Sửa:** khai trước quy tắc xử lý khi luật sư không chốt kịp hết.

**V11. Paper chưa dẫn các công trình gần mà khảo sát đã thấy**
- Ghi chú đọc (`related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md`) nêu: "Retrieving What Is Still True" (so chỉ mục có và không cập nhật), arXiv 2604.14220 (CFR, cạnh SUPERSEDES), Version-Aware KG for Multi-Version Legal QA, FourCorners, Temporal Legal-RAG.
- Grep paper không thấy bài nào. Khẳng định (b) "không thấy công trình nào" vì vậy chưa tính đến chúng.
- **Sửa:** đọc các bài này và đưa vào mục công trình liên quan.

**V12. Mẫu số "căn cứ đúng trong top 20" có số 0 do cấu trúc** [đã kiểm]
- Ở dòng không có đáp án, TV-Recall của lớp B luôn bằng 0 do cấu trúc (ADR:113–115). Các con số 0,839 và 0,529 vẫn tính cả các dòng đó.
- Bảng còn lẫn hai định nghĩa: `proposed` test 2 có 120 ở top 20 nhưng 121 "trong prompt".
- Báo cáo `e7_phan_ra_loi.md` đã có cột "Chỉ dòng có đáp án".
- **Sửa:** dùng cột đó (chuong-6:227–253, paper Bảng 14–15).

---

### D. NHẸ (7)

- **L1. Ghi p sai độ phân giải.** "p Holm < 0,0001" không đúng (chuong-6:23 và các bảng). Với B = 10.000, p nhỏ nhất khác 0 là 2/B = 0,0002 (`confirm_vilextime.py:122`); qua Holm có thể tới 0,0012. Nên ghi "p < 0,0002 (Holm ≤ 0,0012)".
- **L2. Số "A gán khoảng 5 giây/dòng" lấy từ plan, không từ file đo.** Cột `phut` trong `kiem_A.tsv` điền 971/971 dòng, trung vị 1,0 phút, tổng 990 phút [đã kiểm]. Cần trỏ tới log thời gian thật và giải thích cột `phut`.
- **L3. Paper:77 viết "truy vấn ghi ở phụ lục", nhưng paper không có phụ lục đó.**
- **L4. Paper:19 đặt "AC1 người 0,377" cạnh "LLM v2 0,530".** Một số là người với người, số kia là LLM so với người; không cùng loại.
- **L5. "769 dòng chính" (paper:58) gồm cả dev và cả ba chế độ mốc.** Nên báo theo lineage và tầng nhãn: test ranh giới có 121/211 dòng nhãn người.
- **L6. VBHN không độc lập về nguồn.** VBHN tải từ cùng cổng vbpl (`vbpl-bientap-gateway.moj.gov.vn`), nên không phải nguồn độc lập. Cần nói rõ dự án phụ thuộc một nguồn.
- **L7. Biên thời gian khai báo trước rất sát (khớp quy tắc, nên nêu).**
  - E1 test 2 bắt đầu 15:37:15, cùng giây với commit `463d2eb`.
  - Quy tắc "A lệch agent thì lấy agent" commit lúc 07:06 (`3e487c4`), sau khi đã có kết quả dev, 4 phút trước Accepted.

---

### Số đã đối chiếu: khớp hết [đã kiểm]

- **E3 v1.0** (`runs/E3_v1/test/all.score.json`, `confirm.json`): Accuracy, TV-R@1, TVER, độ phủ trích dẫn, `tver_strict` của 6 hệ; Accuracy theo T1, T2, T3, T6; XN1–XN9 đủ ước lượng, KTC, p Holm.
- **E3 test 2** (`runs/E3_test2/rescore/`): như trên.
- **Phân rã:** `b7 − b5` (+0,161 / +0,159); `proposed − b7pp` (+0,019 [+0,005; +0,039] / +0,018 [−0,026; +0,058]); Bảng 12–13 của paper.
- **E1:** TV-R@1 và R@1 của 5 nấc ở hai bộ; `b7v − b7`, `b7plus − b7v`, `b7pp − b7plus`.
- **Bãi bỏ và `b1`:** 0/15 dòng bãi bỏ; 1/16 cho `b2ctx`, `b7`, `b7pp`, `proposed` (0 cho `b1`, `b5`); `b1` để trống 182/196 và 208/211.
- **Dev:** ngữ cảnh đúng 129/151.
- **Nhãn v1.0:** 88 / 33 / 90 (T1 75, T6 15); câu hỏi 145 do Opus, 20 do DeepSeek; AC1 0,377 [0,250; 0,496], κ 0,235, p_neg 0,395; theo nhóm 0,878 / 0,269 / 0,378 / 0,216.
- **Agent và luật sư:** agent 0,721 / 0,610; luật sư 43/50.
- **Test 2:** lời dặn v2 0,530 / 0,758.
- **Loại lineage:** 108 `relocation_unclear` / 25 `relocated`.
- **Silver và gold:** A 131 / 283 / 280; gold 60 = 22 + 23 + 15, 37 / 38 phiếu, trống.
- **E7:** cộng các tầng ra đúng tổng sai và khớp Accuracy.

---

### Reviewer sẽ phản bác thế nào khi so với LawInForce-eCFR và NitiBench+

**Reviewer sẽ nói:**
- "Lọc theo mốc có lợi" và "hai nút thắt tìm–đọc" đã có. Bản nháp đã tự nhận điều này.
- Nấc "ngày văn bản" là baseline yếu. Nấc "lan truyền" đo được đúng 0.
- Nhóm bãi bỏ đã có ở NitiBench+.
- Về nhãn: LawInForce có 805 cặp người kiểm, đồng thuận 95,28%. ViLexTime có AC1 0,377 và nhãn LLM; bộ cuối dự báo khoảng 150 lineage.
- Gold ViLexTime tự dẫn xuất (recall 62%), không lấy từ kho phiên bản chính thức.
- [suy đoán] eCFR có bản theo thời điểm chính thức; tôi chưa kiểm điều này trong repo.

**Phần còn đứng được:**
1. Bộ theo mốc tiếng Việt, trong đó phiên bản được *dựng lại từ lệnh sửa đổi nằm ở văn bản khác*. Đây vừa là đóng góp, vừa là rủi ro; chỉ có giá trị nếu gold mù đạt.
2. Phép đối chứng hai nấc trên cùng dữ liệu, cùng chiều ở cả hai bộ:
   - `b7plus − b7v`: +0,066 [+0,034; +0,101] và +0,070 [+0,036; +0,109].
   - `b7v − b7` âm: −0,019 và −0,044 [−0,074; −0,017]. Đưa lời văn hợp nhất vào mà không lọc theo phiên bản còn làm hại.
3. Kết quả âm có kiểm soát về việc dùng LLM gán nhãn luật: lời dặn v2 không đạt cổng đã khai trước.
4. Nơi nộp hợp hơn là track tài nguyên hoặc NLLP/ICAIL, không phải track hệ thống.

---

### 10 câu hội đồng dễ hỏi nhất mà bản nháp chưa trả lời được

1. Lúc trả lời, đồ thị làm được gì mà một bảng khoảng hiệu lực trong SQLite không làm được? Phần trực tuyến chỉ +0,019 và +0,018 (khoảng chứa 0); `b7pp − b7plus` = 0.
2. Đề cương hứa 1.100–1.300 câu hỏi kiểm định thủ công. Hiện có bao nhiêu *câu hỏi* đạt chuẩn do người kiểm?
3. A và B là ai? Có phải hai em không? Ai đủ năng lực trả lời Q4?
4. Gold, TVER, Verifier và thông báo bãi bỏ cùng lấy từ một đồ thị. Có số nào đo độc lập tỷ lệ sai của đồ thị không?
5. Vì sao v1.0 và test 2 thành "vòng thử" sau khi đã chạy? Nếu bộ cuối "không đủ bằng chứng", em kết luận gì về giả thuyết?
6. Hệ của em cuối cùng là `proposed2` hay `proposed3`? Đã có Accuracy chưa? Vì sao lai ghép làm R@1 trên dev giảm?
7. Lan truyền hiệu lực là "đóng góp riêng". Con số nào chứng minh?
8. So với NitiBench+ và LawInForce-eCFR, ViLexTime có gì mà họ chưa có?
9. Oracle chỉ 6/21 ở dòng bãi bỏ. Đây là giới hạn của bài toán hay của Qwen 4B?
10. Bốn miền trong đề cương chiếm bao nhiêu phần bộ test? Vì sao 64% là "khác" và đất đai chỉ có 3 lineage?
