# Master Plan — Khóa luận và paper Temporal-Aware KG-RAG

Date: 2026-11-05 · Viết lại toàn bộ. Bản cũ và mọi plan cũ đọc ở commit `51f36c7`.

## Status

Active. Đây là **plan duy nhất** của dự án. Lead: Claude. Thực thi: Codex. Duyệt và commit: CMT.
CMT đã trả lời Q1–Q3 và cho commit ngày 05/11. Còn Q4, Q7, Q8 ở mục "Cần chốt".

## Outcome

Đến 26/12/2026: nộp khóa luận khớp đề cương, có demo. Đến 01/2027: nộp một paper mà mỗi con số đều truy được về một lần chạy.

"Xong" nghĩa là đạt đủ cổng G0–G5. Không có cổng nào yêu cầu hệ đề xuất phải thắng. Đề cương hứa hai đóng góp (ViLexTime và kiến trúc) và ba câu hỏi nghiên cứu. Đề cương không hứa một mức điểm.

---

## 1. Đọc trong 2 phút

**Đang ở đâu.** Theo đề cương, hôm nay vẫn thuộc giai đoạn 4 (24/10–13/11). Hai giai đoạn hệ thống và thực nghiệm còn phía trước. Mốc 31/10 của GVHD đã lỡ, nhưng hạn đề cương thì chưa trễ. Còn 7 tuần, đủ để làm đúng một lần. CMT báo hai người gán được ngay trong cuối tuần 07–08/11, nên lịch dưới đây rút ngắn và giai đoạn 4 kịp hạn 13/11.

**Vấn đề thật không phải điểm thấp.** Vấn đề là chúng ta chưa tin được thước đo. Nhãn chưa đáng tin, đáp án chuẩn lấy từ chính đồ thị của hệ, và hệ đã chạy chưa phải hệ đề cương mô tả. Khi thước đo còn lỗi, điểm cao hay thấp đều chưa nói được gì.

**Hướng đi.** Sửa thước đo trước, rồi đo đúng một lần:

1. Dọn repo, chỉ còn một plan (G0).
2. Dựng **bộ test cuối** từ câu hệ chưa từng chạy, do người kiểm, đúng tinh thần đề cương (G1, G2).
3. Kiểm đáp án bằng nguồn độc lập với đồ thị (G2).
4. Hoàn thiện hệ đúng L4–L5 của đề cương, chỉ tinh chỉnh trên `dev` (G3).
5. Khai báo trước, chạy test một lần, báo cáo mọi kết quả kể cả kết quả xấu (G4).

v1.0 và test 2 không bị bỏ. Chúng trở thành hai vòng thử có khai báo, và phần lặp lại của paper.

---

## 2. Nguồn sự thật

Khi hai nơi mâu thuẫn, nơi đứng trên đúng.

| Thứ tự | Câu hỏi | Đọc ở đâu |
|---|---|---|
| 1 | Đã cam kết gì | `docs/DeCuongKLTN_23521635_23521643_UIT.docx` (không bao giờ sửa, xóa) |
| 2 | Quy tắc phân tích, cấu hình đã khóa | `docs/decisions/0005-ke-hoach-phan-tich.md` và các ADR khác |
| 3 | Thế nào là một câu hỏi đúng | `docs/vilextime-dinh-nghia.md`, `docs/vilextime-the-gan-nhan.md`, `docs/vilextime-annotation.md` |
| 4 | Đang làm gì, tiếp theo là gì | File này |
| 5 | Một con số đến từ đâu | `runs/README.md` trỏ tới file điểm trong `runs/` |
| 6 | Bộ dữ liệu là gì | `data/vilextime_dataset/manifest.json`, `docs/vilextime-datasheet.md` |
| 7 | Hệ làm gì thật | `src/vilexgraph/framework/`, `tests/` |

Số test 2: chỉ lấy Accuracy từ `runs/E3_test2/rescore/`. Lần chấm đầu đã sai vì thiếu đáp án ngắn.

---

## 3. Chẩn đoán

Xếp theo mức nguy hiểm cho kết luận. Mọi số đo lại ngày 05/11.

### D1. Nhãn chưa đáng tin

- Đồng thuận hai người trên 246 dòng: AC1 **0,377** [0,25; 0,50], ngưỡng 0,80. Theo nhóm: T1 0,88, T2 0,27, T3 0,38, T6 0,22.
- Người A ghi `dat` 900/971 dòng, người B 230/385. Theo hướng dẫn 3.0 có 101 dòng lệch: 97 dòng là A `dat`, B `khong_dat`. Luật sư đứng về phía B 87/101, nhưng lúc đó có phiếu Claude hỗ trợ.
- A gán khoảng 5 giây một dòng (đo 26/10), nên đây chưa phải phép đo đồng thuận thật. Phải nêu số này khi báo cáo.
- 90/211 dòng test của v1.0 chỉ có nhãn Codex (T1 75, T6 15). Luật sư kiểm mẫu đồng ý 43/50, dưới ngưỡng 45/50. T2, T3 của test v1.0 thì do người chốt.
- Test 2 (227 dòng) hoàn toàn là nhãn LLM, chưa từng so với người. Lời dặn v2 thử trên 68 câu chỉ đạt AC1 0,530.

**Lệch đề cương:** đề cương ghi "kiểm định thủ công; LLM chỉ hỗ trợ diễn đạt câu hỏi". Đây là chỗ lệch lớn nhất cần sửa.

### D2. Đáp án tự chấm chính nó

Phiên bản đúng được dẫn từ cùng đồ thị mà hệ dùng. Vì vậy TVER = 0 của `b7pp` phần lớn do cách dựng, chưa phải bằng chứng.
- Gold độc lập: `gold_A`, `gold_B` trống 0/75; phiếu `gold_sample.tsv` 0/120 và đã cũ.
- M2 (100 truy vấn đối chiếu tay) chưa đạt. Recall sự kiện sửa đổi mới 62,2% (5.007/8.046 cặp), dù precision 58/60.
- Reviewer sẽ hỏi điều này đầu tiên.

### D3. Hệ đã chạy chưa phải hệ trong đề cương

L4 hứa kết hợp từ vựng, ngữ nghĩa và đồ thị. `proposed` đã chạy test chỉ dùng từ vựng. `proposed2` (lai ghép và đồ thị đi lên cha) mới có trên dev, chưa sinh câu trả lời. Verifier (L5) chưa bác câu nào trên dev, vì bộ lọc đã loại hết trước đó.

### D4. Bộ test lệch và nhỏ

Test v1.0: T1 chiếm 58%, T3 chỉ 4 lineage, không có T5. Cả v1.0 lẫn test 2 đều đã chạy, nên không còn tinh chỉnh dựa trên chúng được. XN1 ủng hộ ở v1.0 (+0,051) nhưng chưa đủ bằng chứng ở test 2 (+0,028 [−0,014; +0,072]).

### D5. "Điểm thấp" thực ra là ba chuyện khác nhau

| Khâu | v1.0 (`b7pp`) | Test 2 (`b7pp`) | Đọc thế nào |
|---|---|---|---|
| Tìm: đáp án có trong top 20 | 0,839 (T2: 0,978) | **0,529** (T2: 0,583) | Test 2 khó tìm hơn hẳn. Một lý do có thể: lời hỏi ít trùng chữ với đáp án hơn (0,30 so với 0,48). Chưa kiểm nguyên nhân |
| Đọc: đúng khi đã có căn cứ | 0,757 | 0,583 | Generator 4B đọc chưa tốt. Trần ngữ cảnh đúng trên dev là 0,854 |
| Nhận ra đã bãi bỏ | 0/15 | 1/16 | Ngay cả ngữ cảnh đúng cũng chỉ 6/21 trên dev |

Ngoài ra, `b1` để trống 182/196 câu có đáp án. Vậy RQ1 ở vế "LLM không truy xuất" **chưa đo được**, dù XN9 ghi "ủng hộ". Vế RAG phẳng thì đã có số: TVER của `b2ctx` là 0,471 (v1.0) và 0,682 (test 2).

### D6. Thiếu kỷ luật

15 plan cùng "active", một hướng dẫn 2.394 dòng, nhiều lịch khác nhau. Việc đổi hướng theo từng phiên agent. Đây là lý do mọi thứ mơ hồ. Mục 8 và mục 9 xử lý chuyện này.

### Điều đã có và nói được ngay

Đây là phần tốt, không phải làm lại:
- Lọc thời gian giúp rõ: XN3 ủng hộ ở cả hai bộ (+0,138 và +0,047).
- RAG phẳng trích nhiều điều khoản hết hiệu lực (RQ1, vế RAG).
- Phần lớn lợi ích đến từ lọc, chưa thấy nhiều từ đồ thị trực tuyến: `proposed` − `b7pp` chỉ +0,019 [+0,005; +0,039] ở v1.0, và chứa 0 ở test 2. Đây chính là loại câu trả lời RQ3 cần.
- Đường ống, scorer, kế hoạch khai báo trước và 615 test đều chạy được. Kho văn bản và chuỗi phiên bản đã có.
- Kho ứng viên còn dư: T2 5.427, T6 2.828, T1 2.495, T3 475, T5 201 lineage. **Thiếu giờ người, không thiếu dữ liệu.** Không cần cào thêm.

---

## 4. Đối chiếu đề cương

| Đề cương cam kết | Hiện trạng | Việc còn lại | Cổng |
|---|---|---|---|
| RQ1: mức lỗi sai phiên bản của LLM và RAG | Có vế RAG; vế LLM chưa đo được | Bảng LLM không truy xuất, 2–3 model | G4 |
| RQ2: đồ thị theo phiên bản so với RAG phẳng, GraphRAG phi thời gian | Đã so bằng `proposed` chỉ từ vựng | Chạy `proposed2`; đủ `b4`, `b5`, `b6` | G4 |
| RQ3 và giả thuyết: đồ thị hay chỉ lọc | Thang 5 nấc đã có, kết quả chưa nhất quán | Chạy lại trên bộ cuối | G4 |
| ViLexTime 1.100–1.300 cặp, T1–T6 theo Bảng 1 | Xem mục 5 | Kiểm silver, thêm T6, T1 | G2 |
| Kiểm định thủ công, LLM chỉ diễn đạt | Lệch (D1) | Bộ cuối do người gán | G2 |
| L0–L3, kiểm chứng snapshot | Có; M2 chưa đạt | Đối chiếu VBHN, gold mù | G2 |
| L4 lai ghép có ràng buộc thời gian | Có trên dev | Khóa `proposed2` | G3 |
| L5 sinh, trích dẫn, Temporal Verifier | Có; Verifier chưa tác động | Đo Verifier khi không có bộ lọc; xử lý T6 | G3 |
| Baseline: LLM; BM25, dense, lai; GraphRAG; KG phân cấp; lọc siêu dữ liệu | Có cấu hình; `b2 b3 b4 b6` chưa chạy test | Chạy trên bộ cuối | G4 |
| Recall@k, MRR, TV-Recall, Accuracy, EM/F1, TVER, VCR, TCS | Có trong scorer | Giữ nguyên | G4 |
| LLM-as-judge | Có công cụ, chưa hiệu chuẩn | 100 mẫu người (C4) | G4 |
| Thí nghiệm chuyển miền | Chưa có | Phân rã theo miền (C5), ghi lệch | G4 |
| Giao diện minh họa | Chưa có | Demo một file (E3) | G5 |

**Bảng lệch phải giải trình trong khóa luận:**

| Lệch | Lý do | Xử lý |
|---|---|---|
| Nhãn LLM ở v1.0 và test 2 | Thiếu giờ người khi chạy theo mốc 31/10 | Coi là vòng thử; bộ cuối do người gán |
| "Chuyển miền" đổi thành phân rã theo miền | Hệ không huấn luyện lại, miền đa nhãn | Đã chốt C5 |
| GraphRAG là bản xấp xỉ trong cùng đường ống | So sánh chỉ đổi một yếu tố; dựng GraphRAG thật trên 1,48 triệu đơn vị quá đắt | Nêu rõ tên và giới hạn |
| T5 thiếu, T4 có thể dưới 150 | Điều kiện pháp lý hẹp | Báo số thật, không nới định nghĩa |
| Kho rộng hơn bốn miền | Cần đóng kín quan hệ sửa đổi | Đã có trong datasheet |

---

## 5. Bộ dữ liệu cuối

Đếm theo cặp (câu hỏi, mốc) ở chế độ ranh giới, đúng quyết định A2. T4 là lát của T2 và T3.

| Nhóm | Đề cương | v1.0 | Silver (chưa kiểm) | Test 2 (nhãn LLM) | Đang có | Dự báo sau kiểm* |
|---|---:|---:|---:|---:|---:|---:|
| T1 | 250 | 141 | 0 | 0 | 141 | 251 (thêm 110) |
| T2 | 400 | 118 | 274 | 120 | 512 | ~490 |
| T3 | 200 | 31 | 95 | 75 | 201 | ~200 |
| T4 (lát, gần giống ở T2) | 150 | 24 | 102 | 30 | 156 | ~130 |
| T5 | 50 | 0 | 20 | 0 | 20 | ~12 |
| T6 | 100 | 72 | 0 | 32 | 104 | ~155 |
| **Tổng, không tính trùng T4** | **1.150** | **362** | **389** | **227** | **978** | **~1.100** |

*Dự báo giả định 60% câu qua kiểm (v1.0: 246 lineage đạt, 185 không đạt), test 2 tính cả ở tầng LLM, và làm đủ T1, T2 mới. Đây là ước lượng. Số thật sẽ thay vào ở G2.

**Mỗi dòng phát hành có tầng chất lượng:** người gán đôi và luật sư; hoặc LLM, agent. Không gộp hai tầng trong bảng chính.

### Bộ test cuối, dùng để kết luận

Chỉ gồm lineage chưa hệ nào chạy. Đã kiểm 05/11: silver không có dự đoán nào trong `runs/`, không trùng lineage với main và test 2, không trùng văn bản với dev.

| Nguồn | Đưa cho người | Dự kiến qua kiểm |
|---|---:|---:|
| Silver T2 (51 lineage gần giống) | 137 | ~82 |
| Silver T3 | 31 | ~19 |
| Silver T5 (chỉ báo riêng) | 10 | ~6 |
| T6 mới từ kho, có lọc LLM trước | 60 | ~25 |
| T3 mới | 20 | ~12 |
| T2 mới, làm nếu còn giờ | 60 | ~45 |

Kết quả khoảng 180 lineage, hoặc 138 nếu không có T2 mới (chưa tính T5). Dựa trên sai số của test 2: 180 lineage cho khoảng tin cậy XN1 khoảng ±0,032, phát hiện được hiệu chừng 0,046 với power 80%; 138 lineage cho ±0,037 và 0,052. Đây là ước lượng. Hiệu +0,028 của test 2 vẫn khó phát hiện ở cả hai cỡ. Nếu vậy thì báo đúng như vậy.

T1 không vào bộ này vì không có gì để tương phản. T1 mới chỉ để đủ Bảng 1 và làm đối chứng. Có thể kiểm T1 nhẹ hơn: một người, luật sư kiểm mẫu.

### Quy tắc gán nhãn

Theo thẻ 4.0, gán theo câu hỏi, Q1–Q4.
- A và B gán độc lập. Dòng lệch do luật sư chốt, **không có phiếu AI**.
- Người gán không thấy gợi ý, nhãn hay ghi chú của LLM, và không thấy kết quả hệ.
- Bắt buộc dán một câu trích từ văn bản tác động. Trang gán ghi thời gian từng câu.

### Giờ người ước tính

| Việc | Công thức | Giờ công | Ưu tiên |
|---|---|---:|---|
| Lô thử G1 | 30 câu × 2 người × 5 phút | 5 | P0 |
| Silver | 178 × 2 × 4 | 24 | P0 |
| T6 mới | 60 × 2 × 5 | 10 | P0 |
| T3 mới | 20 × 2 × 4 | 3 | P0 |
| Gold mù 120 + 30 dòng (B6) | khoảng 10 phút một dòng | 25 | P0 |
| Kiểm nhãn test 2: lô thử đã gồm 30 câu, thêm 10 câu | 10 × 2 × 4 | 1 | P0 |
| T1: thêm 110, kiểm 30 nhãn Codex cũ | | 5 | P1 |
| T2 mới | 60 × 2 × 4 | 8 | P1 |
| Mã hóa lỗi E7, hiệu chuẩn giám khảo | | 12 | P1 |
| Kiểm hết phần còn lại của test 2 (61 câu) | 61 × 2 × 4 | 8 | P1 |
| **Tổng** | | **~96** | P0 = 68 |

P0 là khoảng 34 giờ cho mỗi người. Luật sư đã nhận: xem thẻ 4.0, chốt khoảng 30–50 dòng lệch.

**Thứ tự làm:** cuối tuần 07–08/11 là lô thử (G1) rồi silver T2, T3 (168 câu, khoảng 14 giờ mỗi người). T6 và T3 mới cần LLM lọc và viết câu hỏi trước, nên làm từ 09/11, cùng gold mù. **Nhanh không được đánh đổi chất lượng:** vòng trước A gán 5 giây một dòng nên đồng thuận không có giá trị. Trung vị dưới 90 giây/câu thì dừng và xem lại.

**Lô thử không lấy từ silver:** rút 30 câu từ 101 câu của test 2 (phiếu v3 có sẵn), để silver còn nguyên cho bộ cuối, và đo luôn nhãn LLM của test 2 so với người.

**Nếu không đủ giờ**, cắt theo thứ tự: T2 mới → T1 mới → T5 → giảm silver T2 còn 90 lineage (giữ đủ phần gần giống). Không cắt lô thử và gold mù.

---

## 6. Thiết kế thực nghiệm cuối

### Câu hỏi và cách trả lời

| Câu hỏi | Đại lượng | So sánh | Loại |
|---|---|---|---|
| RQ1, RAG | TVER, `wrong_version`, VCR | `b2ctx`, `b4` | Mô tả có khoảng tin cậy |
| RQ1, LLM | Tỷ lệ sai phiên bản trên câu **có trả lời** | 2–3 LLM không truy xuất | Mô tả, bảng phụ |
| RQ2 | Accuracy | `proposed2` − `b4`; `proposed2` − `b5` | Xác nhận |
| RQ3, lọc văn bản | TV-Recall@1 | `b7` − `b2ctx` | Xác nhận |
| RQ3 và giả thuyết, phiên bản | TV-Recall@1 | `b7plus` − `b7`; `b7pp` − `b7` | Xác nhận |
| Giả thuyết, câu trả lời | TVER, **kèm bản tính trên gold mù** | `b7pp` − `b7` | Xác nhận |
| T6 lan truyền | Accuracy, dòng bãi bỏ | `proposed2` − `b7pp` | Xác nhận nếu đủ ≥ 20 lineage; không thì thăm dò |
| Thành phần | Bỏ đồ thị, bỏ Verifier | `p2a2`, `p2a3` | Mô tả |

Danh sách chốt và Holm ghi vào amendment ADR 0005 tại G3. Kết quả v1.0 và test 2 được nêu trong amendment, nói rõ đã thấy.

### Việc trên dev (trước G3)

Mỗi việc có điều kiện dừng. Không đạt thì bỏ, ghi lại, không thử tiếp.

| Mã | Việc | Chi phí | Giữ lại khi |
|---|---|---|---|
| X1 | Sinh câu trả lời `b7pp --hybrid`, `proposed2`, `p2a2`, `p2a3`. Prompt trùng thì dùng lại, không chạy GPU lại | Colab ≤ 3 giờ | Luôn chạy, đây là cam kết L4–L5 |
| X2 | Đưa thông báo bãi bỏ có cấu trúc vào prompt, từ đồ thị | ít code, ≤ 1 giờ GPU | T6 không đáp án tăng rõ, KTC ghép cặp > 0, nhóm khác không giảm |
| X3 | **Đổi 09/11 (CMT):** cột chính dùng GPT-4o mini qua API, không qua cổng Accuracy cũ; Qwen3-4B ở bảng phụ RQ1. Xem amendment 09/11 của ADR 0004 (chờ duyệt) | khoảng $4 | Kiểm định dạng, cắt cụt và ba trạng thái hiệu lực trên dev trước khi chạy hết |
| X4 | Đo Verifier khi không có bộ lọc (`b4`, `b7`) | thấp | Báo đúng vai trò của Verifier |
| X5 | Lưu sổ chạy dev hôm 05/11. Dùng số chấm lại R@30 0,808 (không dùng 0,801 ghi nhầm trong plan cũ) | rất thấp | Luôn làm |
| X6 | Embedding tốt hơn (`AITeamVN`, đúng quyết định C1) trên GPU. Khâu tìm là nút thắt lớn nhất (top 20 của test 2 chỉ 0,529) | Colab ~1 phiên | Chạy. Chỉ giữ cho hệ khi R@10 dev tăng, KTC > 0 |
| X8 | Điều kiện cấp sẵn căn cứ: bản đúng mốc và bản hiện hành, theo nhóm T1 (đối chứng), T2, T3, T6. Đo cái giá của đọc sai văn bản, tách lỗi tìm khỏi lỗi đọc. Dev trước, rồi trên bộ test cuối | Colab ~1 giờ | Luôn chạy; so được với NitiBench+, LawInForce-eCFR |
| X7 | Colab đợt 2: `b7plus b7v` trên test 2; `b7plus b7v a4 b2 b6 oracle b3 b4 a1 a2 a3` trên v1.0. Hoàn tất các hệ ADR 0005 đã khai báo, điền chỗ chờ ở chương 6. Mỗi cấu hình một lần | Colab ~10 giờ | Chạy. Kết quả chỉ để mô tả; không dùng để chọn cấu hình |

**Đã cắt, không mở lại nếu không có lý do mới:** cào toàn bộ; reranker (CMT cắt 05/11).

**Giờ GPU không phải giới hạn (CMT 05/11):** việc nào cần và tốt cho khóa luận thì chạy. Điều kiện giữ lại ở bảng trên là để giữ kỷ luật khoa học, không phải để tiết kiệm. LightRAG thật (C3) vẫn giữ, làm sau G3 trên tập con, báo riêng vì không cùng corpus.

---

## 7. Lộ trình và cổng

Bám giai đoạn của đề cương. Không qua cổng thì không làm bước sau.

| Cổng | Hạn | Giai đoạn đề cương | Tiêu chí đo được | Làm gì nếu không đạt |
|---|---|---|---|---|
| **G0** Repo sạch | 07/11 | — | Một plan; `pytest` qua; hash dữ liệu không đổi; mục 8 đạt | Khôi phục từ bản sao lưu |
| **G1** Thước đo gán nhãn | 07/11 | 4 | Lô 30 câu: AC1 ≥ 0,80 và p_neg ≥ 0,60 trên từng Q1–Q4 có ít nhất 5 nhãn âm; Q khác báo KTC; trung vị ≥ 90 giây/câu; luật sư đã xem hướng dẫn 4.0 | Làm rõ hướng dẫn với luật sư một lần, thử lô 30 câu khác. Trượt lần nữa: vẫn gán đôi, ghi "đồng thuận không đạt", không hạ ngưỡng |
| **D0** Bản nháp | CN 08/11 | — | Đủ 7 chương và paper theo hướng mới; số khớp `runs/`; chỗ chưa có số ghi `[CHỜ]`; hai người đọc lại | Giao phần đã có, ghi rõ phần thiếu. Không chạy test để lấp chỗ trống |
| **G2** Khóa dữ liệu | 12/11 | 4 (kịp 13/11) | Bộ test cuối ≥ 130 lineage người kiểm (mục tiêu ~180); AC1, p_neg đo trên toàn bộ phần gán đôi; gold mù có số; đối chiếu VBHN có báo cáo; datasheet khớp manifest; không rò `dev` | Dưới 130: báo là chưa đủ cỡ mẫu, ghi power thật, không hạ tiêu chuẩn nhãn. Gold mù dưới ngưỡng: sửa lỗi đồ thị, người kiểm lại các dòng bị ảnh hưởng |
| **G3** Khóa hệ | 20/11 | 5 (sớm hơn 04/12) | X1–X5 có kết quả; demo chạy; amendment ADR 0005 đã commit trước khi chạy test | Không chạy test khi chưa có commit này |
| **G4** Chạy cuối | 30/11, muộn nhất 14/12 | 6 | Mỗi cấu hình chạy test một lần; `confirm.json`, bảng theo nhóm và miền, E7, giám khảo | Lỗi đường ống: amendment trước khi chấm lại, ghi cả lần sai |
| **G5** Nộp | 26/12 | 7 | Khóa luận đủ chương, số khớp `runs/`; demo; tài liệu đã đọc bản gốc | — |
| **G6** Paper | 01/2027 | Sau đề cương | Bản nộp qua `paper_check.py`; đã kiểm quy định ẩn danh (E2) | GVHD chọn nơi nộp |

**Gold mù:** rút phân tầng từ bộ test cuối. Người gán đọc văn bản gốc hoặc VBHN, không thấy phiên bản đồ thị. Đạt khi ≥ 114/120 khớp (B6). Lấy 100 dòng làm M2. VBHN chạy tự động trước để kiểm rộng; dòng lệch do người phân xử. VBHN **không** thay nhãn người.

**Nơi nộp, đề xuất cho GVHD:** ICAIL 2027, hạn báo là 28/01/2027, hợp đề tài pháp luật và AI. Phương án phụ: SIGIR 2027 (21/01/2027, chưa rõ track tài nguyên). Hai hạn này lấy từ trang tổng hợp, chưa kiểm trang chính thức.

**Paper chọn hướng A:** bộ đánh giá và phép đo có đối chứng, kèm hệ đầy đủ. Hướng này đứng vững với mọi kết quả ở G4. Bản nháp ở `docs/paper/` sửa qua `scripts/paper/paper_template.md`.

### Khóa luận

| Chương | Hiện trạng | Hoàn thiện sau |
|---|---|---|
| 1 Mở đầu | Chưa viết | G2 |
| 2 Cơ sở lý thuyết | Nháp; 14 nguồn mới có metadata | Đọc bản gốc trước G3 |
| 3 Kho văn bản, đồ thị | Nháp | G2 (thêm M2, VBHN) |
| 4 ViLexTime | Nháp theo v1.0 | G2 |
| 5 Phương pháp | Nháp theo `proposed`. Phải nói đúng: lúc truy xuất, đồ thị đọc từ SQLite, không dùng Neo4j hay Milvus | G3 |
| 6 Thực nghiệm | Nháp, 7 chỗ chờ | G4 (v1.0, test 2 thành vòng thử) |
| 7 Kết luận | Chưa viết | G4 |
| Phụ lục khai báo AI | Nháp | G5: gồm tốc độ gán của A, ghi chú Claude nháp, phiếu Claude ở vòng hòa giải, quy tắc A–agent, lần chấm sai, nhãn agent và LLM |

### Ai làm gì

| Việc | Người |
|---|---|
| Gán nhãn (từ 06/11): AI-A, AI-B gán độc lập; `legal-adjudicator` đề xuất cho dòng lệch; CMT duyệt **mọi dòng**, có xem nhãn AI, đồng ý hoặc sửa | Agent gán, CMT xác nhận. Xem Decisions 06/11 |
| Gold mù, kiểm mẫu, mã hóa lỗi | CMT, NMT, luật sư. AI không tham gia |
| Chạy Colab | CMT hoặc NMT, theo gói đã xuất sẵn |
| Quyết định, commit, gửi GVHD | CMT |
| Code, xuất gói, chấm, dựng bảng, soạn nháp | Codex làm, Claude kiểm |
| Lọc trước và viết câu hỏi cho ứng viên T6, T3, T2 mới. Công bố phễu lọc | Agent; đề cương cho LLM diễn đạt câu hỏi |
| Bổ sung đoạn văn gốc thiếu trong phiếu: chỉ trích nguyên văn, không kết luận | Agent |
| Kéo nhãn, đo đồng thuận và thời gian mỗi lô, dừng khi tụt. Hai người gán chỉ nghe đạt hay không, không biết câu nào lệch | Claude chạy script |
| Sau khi lô khóa: agent gán mù, người không thấy kết quả. Dùng để đo LLM so với người (thăm dò) và chọn câu nghi sai, trộn với câu ngẫu nhiên đưa luật sư | Agent chọn, luật sư đọc, không kèm lý do của AI |
| Kiểm phiên bản đồ thị với VBHN và nguồn ngoài. Lawgical chỉ 20 lượt/ngày, để dành cho dòng lệch | Codex, `vn-law-verifier` |
| Ghi chú đọc tài liệu có trích dẫn, phản biện bản nháp | `lit-scout`, `thesis-critic`; hai người vẫn phải đọc bản gốc |
| Đặt hướng, viết hợp đồng việc, kiểm lại độc lập | Claude |

---

## 8. Dọn repo (G0)

**Sao lưu xong trước khi dọn:** `/home/trica/UIT_Thesis/backup-pre-cleanup-20261105/` (diff chưa commit, 123 file chưa track, sha256). File đã track đọc lại ở commit `51f36c7`.

**Quy tắc:**
1. Không đụng: đề cương; file harness; ADR; định nghĩa và thẻ gán; `docs/thesis`, `docs/paper`; nhãn người, luật sư; dự đoán test; file có sha256 trong manifest; mọi dữ liệu gitignore tốn công dựng.
2. Xóa khi có bằng chứng: không còn nơi sống nào nhắc tới, hoặc có bản thay thế nêu tên, hoặc trùng byte.
3. Dữ liệu duy nhất nằm sai chỗ thì chuyển vào `runs/`, không xóa.
4. Không viết lại ADR đã Accepted, không sửa file harness. README gốc ghi: tài liệu cũ mà ADR hoặc comment code nhắc tới thì đọc ở `51f36c7`.
5. Không commit. CMT xem diff rồi commit.

**Cây đích:**

```text
README.md            một trang: đề tài, nguồn sự thật, cách chạy
AGENTS.md CLAUDE.md  harness, không đổi
docs/
  DeCuong...docx     bất biến
  plans/active/master-plan.md   plan duy nhất
  plans/completed/   việc đã xong
  decisions/         ADR
  vilextime-*.md     định nghĩa, thẻ gán, hướng dẫn, schema, datasheet
  reports/           kết quả E3, phân rã lỗi E7, biên bản D5, thử tải VBHN
  crawling-plan.md audit_dataset.md graph_justification.md gcs-source-snapshots.md   tài liệu kỹ thuật, nguồn cho chương 3
  thesis/ paper/
src/ scripts/ tests/ prompts/ notebooks/
data/                dữ liệu; nhãn ở data/review
runs/                README và các lượt còn được trích
related_paper/ references.bib
```

Hồ sơ đầy đủ về những gì đã xóa: `docs/plans/completed/2026-11-05-don-dep-repo.md`.

---

## 9. Quy tắc làm việc từ nay

1. **Một plan.** Việc mới vào file này. Việc đủ lớn mới tách plan riêng, xong thì chuyển `completed/`.
2. **Trạng thái cần bằng chứng.** Chỉ đánh dấu xong khi có lệnh, file hoặc số đo.
3. **Mọi số trong khóa luận và paper truy được** về một file trong `runs/`. Không chép số tay.
4. **Không chạm test ngoài G4.** Mọi tinh chỉnh ở `dev`. Mọi thay đổi sau khi khai báo đều là amendment, có ngày, có ghi đã thấy gì.
5. **Báo mọi kết quả đã khai báo,** kể cả xấu. Không có "chạy lại cho đẹp".
6. **Nhãn người là của người.** AI không gợi ý, không nháp ghi chú, không hòa giải.
7. **Quy trình với Codex:** Claude viết hợp đồng (phạm vi, cấm gì, bằng chứng gì) → Codex làm → Claude kiểm độc lập bằng lệnh riêng → chưa đạt thì trả lại, nói rõ sai ở đâu → Claude commit và push `develop` (CMT cho phép 05/11). Nhiều phiên Codex chạy cùng lúc thì mỗi phiên một vùng file không chồng nhau.
8. **Nói rõ độ tin cậy.** Mọi kết luận ghi rõ: xác nhận, thăm dò hay mô tả; nhãn người hay nhãn LLM.

---

## 10. Công trình gần nhất và hệ quả (đọc 05/11)

Hồ sơ: `related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md`. Lead đã tự mở tóm tắt hai bài đầu.
- **LawInForce-eCFR** (AACL 2026): 805 cặp có người kiểm, luật Mỹ, BM25 có/không lọc ngày, kết luận hai nút thắt. **NitiBench+** (arXiv 02–03/11/2026): luật Thái, đo cái giá khi đọc văn bản hiện hành thay vì văn bản đúng mốc.

Hệ quả cho paper:
1. Không nói "đầu tiên". Khoảng trống còn giữ được: pháp luật Việt Nam, và tách có đối chứng trên cùng dữ liệu ba nấc: ngày văn bản, khoảng hiệu lực phiên bản, lan truyền từ nút cha.
2. "Lọc thời gian đáng giá" và "hai nút thắt" không còn là phát hiện riêng. Phần riêng: nhận diện bãi bỏ, thang ba nấc.
3. **Bắt buộc có điều kiện cấp sẵn căn cứ** trên bộ test: đúng mốc và bản hiện hành (X8). Thiếu là reviewer hỏi ngay.
4. **Đồng thuận người gán là thế yếu nhất:** LawInForce báo thỏa thuận 95,28% (theo báo cáo đọc), ViLexTime 0,377. G1 và G2 quyết định paper có đứng được không.
5. Lĩnh vực đang đi nhanh, nên nộp sớm có giá trị thật.

### Đo được thêm ngày 05/11, đổi kỳ vọng

- **VBHN gần như không phủ được benchmark:** silver 21/168 lineage có cạnh VBHN, chỉ 2/819 mốc so được; cả ba bộ chỉ có 2 cặp so được, khớp xác nhận 1 (`docs/reports/doi-chieu-vbhn.md`). Vì vậy **gold mù do người là đường duy nhất để phá vòng tự chấm**. Không cắt gold mù trong mọi trường hợp.
- **T6 và T3 thiếu thật:** tỷ lệ giữ T6 cộng dồn chỉ 5,6%. Lọc hết kho còn lại dự báo khoảng 24 phiếu T6, T3 mới tối đa 8. T2 dư (khoảng 46–63 phiếu).
- **Dự báo bộ test cuối sau kiểm của người (60%):** silver T2 ~82, T3 ~19; T2 mới ~30, T6 mới ~14, T3 mới ~5: tổng khoảng 150 lineage. Chưa đo, thay bằng số thật ở G2.
- **F7 (T6) nhiều khả năng dưới 20 lineage, thành thăm dò.** Cách bù, khai báo trước trong amendment: chạy thêm `proposed2`, `proposed3` trên T6 của v1.0 và test 2, báo gộp có ghi rõ là thăm dò vì các dòng đó đã được xem.
- **A đã gán 131/168 lineage silver** ở vòng 25/10 và đã thấy đáp án đồ thị. Nhãn mới của A vẫn độc lập với B, nhưng phải khai trong khóa luận. Gold mù chia theo người.

### Phản biện 05/11 và cách xử lý

Hồ sơ: `docs/reports/phan-bien-ban-nhap-20261105.md` (do `thesis-critic` làm, chỉ đọc; đã đối chiếu hơn 40 số, khớp hết). Lead đã tự kiểm mục lan truyền. Các xử lý dưới đây chỉ siết thêm, không nới quy tắc nào, và sẽ vào amendment G3.

| Mã | Vấn đề | Xử lý |
|---|---|---|
| C1 | TVER, Verifier dùng chung cửa sổ đồ thị với gold, nên TVER = 0 của `b7pp` là do cách dựng | TVER bỏ khỏi họ xác nhận, gọi là kiểm nhất quán nội bộ. H0 chỉ quyết bằng TV-Recall. Thêm **TVER theo người**: rút khoảng 100 đơn vị được trích, người đọc văn bản gốc mà không thấy cửa sổ đồ thị |
| C2 | Thông báo bãi bỏ của `proposed3` lấy từ cùng sự kiện với gold T6 | Accuracy T6 của `proposed3` là cận trên khi đồ thị đúng. Chỉ kết luận trên dòng T6 đã qua gold mù. Báo precision của khẳng định "đã bãi bỏ" trên dòng có đáp án |
| C3 | Gọi v1.0, test 2 là "vòng thử" sau khi đã thấy kết quả | Viết đúng lịch sử: xác nhận lần 1 và lần lặp, đổi vai ngày 05/11 sau khi thấy. Amendment ghi sẵn kết luận cho từng tổ hợp ba phán quyết, không gộp |
| C4 | Bảng lệch §1.6 thiếu | Gộp mục 11 của định nghĩa, thêm: đếm câu hỏi theo lineage (515 hiện có), T3 không đòi truy vết, Claude viết đáp án ngắn, LLM lọc trước, bốn miền chỉ khoảng 36%, chỉ số chưa báo, `rel_up` lấy hạt giống trước bộ lọc |
| C5 | Nấc lan truyền đo được bằng 0 ở tầng truy xuất (`b7pp` = `b7plus` mọi nhóm, cả hai bộ); bãi bỏ đã có ở NitiBench+ | Thu luận điểm về hai nấc đã đo. Lan truyền chỉ được nói nếu XN5 (sinh câu trả lời, `b7pp` − `b7plus` trên T6 cấp trên) cho thấy. Đưa `b7plus` vào lần sinh cuối. Phần bãi bỏ viết thành đặc thù Việt Nam: lệnh nằm ở văn bản khác, bãi bỏ qua nút cha |
| N1 | Người gán là hai tác giả | Khai rõ. Luật sư kiểm ngẫu nhiên 30 dòng `dat` của bộ cuối |
| N2 | A đã thấy phần lớn silver | AC1 báo riêng trên phần A chưa thấy, khai trước |
| N3 | Bộ lọc LLM gây lệch chọn mẫu | Công bố phễu theo mã lý do. Người kiểm 20 câu T6 bị lọc loại, rút ngẫu nhiên, để ước tỷ lệ loại nhầm. Kết quả T6 ghi là có điều kiện theo bộ lọc |
| N4 | Gold mù đợt 1 chưa có T6, T1 | Đợt 2: ít nhất 30 T6 và T1 cũ. Dòng gold sai thì giữ với gold đã sửa, không loại. Sửa đồ thị thì chạy lại mọi hệ trước G3 |
| N6 | Paper bỏ XN6, XN7 | Thêm bảng XN5–XN7 và bảng đủ nhóm × hệ |
| N7, N10 | Hệ cuối chưa chọn; đại lượng chính đổi | G3 ghi đúng một tên hệ, một generator, một embedding. RQ2 lấy thêm `wrong_version`. Giữ nguyên văn RQ3 của đề cương. Amendment liệt kê từng thay đổi kèm "đã thấy gì" |
| N8 | Định gộp T6 đã thấy | Không gộp; báo riêng, gắn nhãn "đã thấy" |
| N9 | G1 khó đo, đường lui là hạ chuẩn | Cổng chỉ tính trên câu Q có ít nhất 5 nhãn âm, các câu khác báo KTC. Trượt thì ghi "đồng thuận không đạt", không chuyển sang một người gán |
| N11 | Colab đợt 2 chạy trên test trước G3 | **Niêm phong:** nhập raw, lưu hash, chỉ chấm sau khi amendment G3 commit |
| V, L | Số chưa đồng bộ, power, mẫu số, TCS, precision từ chối, p | Sửa trong bản nháp |

**Việc người thêm:** TVER theo người (khoảng 100 đơn vị, khoảng 8 giờ), kiểm 20 câu T6 bị lọc loại (khoảng 2 giờ), luật sư kiểm 30 dòng `dat`.

## 11. Hàng việc của agent

Mục tiêu (CMT 05/11): agent làm hết phần của agent, cuối cùng chỉ còn việc người ở mục 12. Mỗi việc do Codex hoặc agent làm, Claude kiểm độc lập, rồi commit và push `develop`.

| Mã | Việc | Xong khi | Phụ thuộc |
|---|---|---|---|
| A1 | Gộp hướng dẫn 4.0, file Word cho luật sư, cổng Q4 đúng ADR, trang gán | Trang đã đăng, kiểm được ghi và đọc | — |
| A2 | Đối chiếu đáp án với VBHN | `docs/reports/doi-chieu-vbhn.md` có độ phủ và tỷ lệ khớp | — |
| A3 | Kiểm kê ứng viên đã lọc | Biết còn thiếu bao nhiêu câu mỗi tầng | — |
| A4 | Phiếu T6, T3, T2 mới: lọc, viết câu hỏi, đáp án ngắn | `data/review/the4/lo2_moi_worksheet.jsonl` đủ 60/20/60 hoặc nêu rõ thiếu | A3 |
| A5 | T1 mới 110 câu; gói T5 cho luật sư | Phiếu sẵn | A4 |
| A6 | **Gold mù:** rút mẫu 120 + 30 từ bộ test cuối, phiếu riêng từng người, đưa lên trang | Trang có phần gold không lộ đáp án đồ thị; mỗi người không thấy câu gold của mình ở lô gán cho đến khi điền xong | A1, A4 |
| A7 | `proposed3`, Verifier khi không lọc, phân rã theo miền, demo | Có gói Colab, báo cáo, `scripts/demo.py` chạy được | — |
| A8 | Bản nháp 7 chương và paper | Mốc D0 | — |
| A9 | Đọc 14 nguồn, khảo sát tính mới có log | Ghi chú trong `related_paper/notes/`, sửa mô tả sai | — |
| A10 | Tập dượt lần chạy cuối trên dev: từ phát hành, xuất, nhập, chấm, kiểm định, đến bảng | Một lệnh chạy hết trên dev, số khớp lần chấm cũ; có chặn thiếu đáp án ngắn | — |
| A11 | Phiếu luật sư tự sinh từ dòng lệch, không có ý kiến AI; xuất bản phát hành có tầng chất lượng | `adjudicate`, `export_release` chạy được trên dữ liệu thử | A1 |
| A12 | Agent gán mù sau khi lô khóa; chọn câu nghi sai trộn câu ngẫu nhiên cho luật sư | Script sẵn, khai báo trong amendment | A1 |
| A13 | Bảng LLM không truy xuất (RQ1), generator kiểm độ bền (X3) trên dev | Có so sánh chi phí và kết quả | A7 |
| A14 | Gói Colab embedding `AITeamVN` (X6): dữ liệu, notebook, lệnh nhập | CMT chỉ còn bấm chạy | — |
| A15 | Giám khảo LLM: công cụ và mẫu 100 câu; phiếu mã hóa lỗi E7 | Mẫu sẵn cho người | A7 |
| A16 | Hình và bảng tự sinh từ file kết quả cho khóa luận và paper | Một lệnh dựng lại | A10 |
| A17 | Nháp amendment ADR 0005 cho bộ test cuối; datasheet và tuyên bố dữ liệu | Nháp sẵn, chờ số G2 và người duyệt | A4 |
| A18 | Phản biện độc lập bản nháp (`thesis-critic`), sửa chỗ sai | Danh sách lỗi đã xử lý | A8 |
| A19 | Nhập và chấm Colab khi CMT tải về; điền chương 6 | Không còn `[CHỜ COLAB]` | CMT chạy Colab |
| A20 | X8: hệ `oracle` bản hiện hành, gói Colab dev | Gói sẵn, không có đáp án trong prompt | — |
| A21 | Sửa chương 2 và `references.bib` theo báo cáo đọc 05/11 mục 3; gỡ các `[CẦN XÁC MINH]` đã đóng | Hết lỗi mô tả đã biết | — |
| A22 | Đo lại X4: tier `document` cho lớp `asis`. Số `propagated` trên `asis` không dùng được vì lớp này không có cửa sổ | Báo cáo có ý nghĩa, sổ chạy đúng | — |

**Thứ tự thật sự quan trọng:** gold mù phải đi trước khi người gán thấy đáp án đồ thị của cùng câu đó (B6). Vì vậy câu gold của mỗi người được giữ lại khỏi các lô gán của chính người đó, cho đến khi họ điền xong phiếu gold.

**Giới hạn công cụ (05/11):** Codex chạm hạn mức tuần, mở lại 9/11 7:49. Claude có hạn mức 5 giờ dùng chung với phiên điều phối. Lọc một gói tốn khoảng 100 nghìn token. Hai bạn đã đủ việc đến 9/11 (lô thử, gold đợt 1, 108 câu silver), nên A4 làm tiếp sau 9/11 không chặn người. Nếu CMT mua thêm hạn mức Codex thì chạy ngay.

## 12. Việc chỉ người làm được

Khi hàng việc trên xong, chỉ còn:
1. Hai người gán: lô thử; silver; T6, T3, T2 mới; T1; gold mù; mã hóa lỗi E7; mẫu giám khảo.
2. Luật sư: xem hướng dẫn 4.0; chốt dòng lệch; T5.
3. Chạy Colab theo gói đã xuất.
4. CMT, NMT: duyệt amendment rồi cho chạy test cuối; đọc và sửa bản nháp bằng lời của mình; đọc bản gốc tài liệu chính.
5. GVHD: góp ý hướng; chọn nơi nộp. Gửi mẫu khóa luận UIT.
6. Chuẩn bị bảo vệ.

**Việc harness, chưa làm:** `docs/README.md` và `docs/product/README.md` là file mẫu của harness, nhắc tới file không có trong repo. Theo `AGENTS.md`, muốn sửa thì CMT phải yêu cầu `$improve-harness`. Không chặn việc gì.

## Risks And Recovery

| Rủi ro | Dấu hiệu | Phòng và xử lý |
|---|---|---|
| Không đủ giờ người | Hết 08/11 chưa xong nửa silver | Cắt theo mục 5. Báo power thật |
| Gán quá nhanh | Trung vị dưới 90 giây/câu, hoặc hai người cùng tài khoản | Dừng, xem lại. Không tính lô đó vào đồng thuận |
| Đồng thuận vẫn thấp | G1 trượt hai lần | Đổi quy trình như G1. Không hạ ngưỡng |
| Gold mù lộ lỗi đồ thị | < 95/100 | Tìm nguyên nhân, sửa, người kiểm lại phần ảnh hưởng. Đây là kết quả có ích, phải báo |
| Bộ cuối ra kết quả xấu | XN1, XN4 vẫn chưa đủ bằng chứng | Hướng A vẫn đứng được: báo đúng phần lợi ích đến từ đâu |
| Colab hết hạn mức | Không chạy được | Xuất gói sớm, ưu tiên hệ chính, dùng lại prompt trùng |
| Agent lại đổi hướng | Xuất hiện plan mới, cấu hình mới | Quy tắc 1 và 4; từ chối khi không có ghi vào file này |

Hoàn tác việc dọn: giải nén bản sao lưu; file đã track lấy từ `51f36c7`.

## Cần chốt

| Mã | Quyết định | Đề xuất | Chặn gì |
|---|---|---|---|
| Q1 | Làm bộ test cuối do người gán? | **Có.** CMT 05/11: cuối tuần xong | Đã chốt |
| Q2 | Luật sư còn làm được: xem thẻ 4.0, chốt 30–50 dòng lệch? | **Có** (CMT 05/11) | Đã chốt |
| Q3 | Dừng Colab đợt 2? | **Không dừng.** CMT 05/11: không có khái niệm để dành, cái nào cần và tốt cho khóa luận thì chạy | Đã chốt (X7) |
| Q4 | Paper hướng A (mốc M4)? | Có | Viết paper; không chặn thực nghiệm |
| Q5 | Gold mù 100 + 20 thay vì 120 + 30 (B6)? | Bỏ đề xuất này: đủ giờ nên giữ B6 | Đã đóng |
| Q6 | Bỏ LightRAG thật khỏi cam kết (C3)? | Bỏ đề xuất này: giữ C3, làm sau G3 | Đã đóng |
| Q7 | Thêm T6, T1, T3 mới, tức nới quyết định B1? | Có; B1 đã bị test 2 vượt qua. Làm theo đề xuất, trừ khi CMT phản đối | G2 |
| Q8 | GVHD đồng ý nơi nộp và lịch này? | CMT gửi | G6 |

## Hàng việc đóng G2 (10/11/2026)

Điều phối bởi `research-lead` (opus), vai và model theo bảng ở `.claude/agents/research-lead.md`.
Làm tuần tự theo cột Phụ thuộc; ghi kết quả vào mục Progress.

| # | Việc | Vai làm | Người chốt | Phụ thuộc | Trạng thái |
|---|---|---|---|---|---|
| H1 | Push `develop`, phiếu VBHN cho luật sư (`data/review/vbhn_phan_xu/`) | lead | | | Xong (`67a80b5`, `9bba732`) |
| H2 | Luật sư phân xử 9 ca + 2 tín hiệu bãi bỏ; `vn-law-verifier` tra trước để luật sư có căn cứ | verifier → luật sư | Luật sư | H1 | Xong 10/11: CMT xác nhận đề xuất AI, chưa qua luật sư |
| H3 | Gold mù đợt 2 (≥30 dòng T1/T6): cần người gán mới, độc lập với đồ thị và nhãn AI. Thêm `--per-stratum` cho `independent_gold.py`, dựng phiếu | `data-clerk` | CMT chọn người | Quyết định ai gán | Chặn |
| H4 | Xác nhận quy ước `dong_y` và G108 (gold đợt 1, 119/120) | verifier đã tra | CMT | | Xong 10/11 (CMT xác nhận) |
| H5 | Danh sách lỗi đồ thị gom từ gold mù, VBHN, G108 (đóng cả khoản khi bãi bỏ một phần), `document:31760` lệch trạng thái | `experiment-executor` điều tra, chưa sửa | CMT chốt sửa một lần | H2, H3 | Xong 10/11 (gate 2 lần FAIL câu chữ, đã sửa) |
| H6 | Dựng lại release, chạy lại mọi hệ trên dev, đối soát | executor → `evidence-gate` | CMT | H5 | Dựng lại xong; gate code không lỗi chặn; dev 15 hệ xong 11/11 (`16213bb`), P = `proposed2`; chờ gate số dev |
| H7 | Xem 24 dòng silver CMT ghi sửa + dòng `[phân vân]` (hợp 47 lineage) | `legal-adjudicator` (CMT 11/11 thay người) | CMT | | Đang làm 11/11 |
| H8 | ADR 0005 amendment G3 → Accepted; `thesis-critic` rà trước | critic → CMT | CMT | H6 | Chờ |
| H10 | T6: `legal-adjudicator` chốt 17 dòng dev + gói ca khó; rà R2 mọi dòng T6 bộ test cuối; chấm lại T6 dev | adjudicator → `data-clerk` | CMT | | Xong 11/11: dev loại 12 lineage (9 R2 + 3 Q1), chấm lại `runs/t6_dev_r2_20261111/`, P vẫn `proposed2`; test cuối loại 3 |
| H9 | `final_run` P = `proposed2`; gate kiểm số; viết paper | executor → gate | CMT | H8 | Chờ |

Ràng buộc: gold mù và nhãn người không giao cho AI; `dong_y` AI điền phải khai trong
paper; Lawgical dưới 20 lượt/ngày, thiếu thì dùng API vbpl và ghi nguồn thật.

## Progress

- [x] 05/11 Đo lại hiện trạng, viết plan này. Sao lưu trước khi dọn.
- [x] 05/11 G0: dọn repo. Chuyển 32 file, xóa 216 file (205 MB). Claude kiểm lại: 735 hash giữ nguyên trừ 1 file chỉ đổi comment nguồn; 611 test qua; nhập lại `b1` trùng 211/211; chấm lại `b7pp` ra đúng số cũ ở hai bộ; `paper_check` 0 sai lệch. Hồ sơ: `docs/plans/completed/2026-11-05-don-dep-repo.md`. **Chưa commit.**
- [x] 05/11 X5: sổ chạy dev đã cập nhật, số tính lại từ file (`runs/README.md`).
- [x] 05/11 CMT cho commit: tách ba commit (việc dở từ trước; dọn repo; master plan).
- [x] 05/11 CMT trả lời Q1–Q3.
- [ ] Trang gán nhãn thẻ 4.0 và lô thử G1 (30 câu từ test 2). Luật sư xem thẻ 4.0.
- [ ] Phiếu silver T2, T3 cho cuối tuần.
- [x] 05/11 X1, X7: gói Colab đã kiểm (dev 4 file × 151 dòng, không có đáp án, `p2a2` ≡ `b7pp`, `p2a3` ≡ `proposed2`; đợt 2 13/13 file khớp hash). Ở `colab_upload/` (gitignore).
- [ ] CMT chạy Colab: dev rồi đợt 2. Claude nhập và chấm.
- [x] 09/11 X2: `proposed3` chạy trên dev với GPT-4o mini; không đạt quy tắc chọn P (+2/21, cận dưới KTC bằng 0), P = `proposed2` (`runs/gpt4omini_dev/select_p.json`).
- [x] 05/11 A1: hướng dẫn 4.0 gộp xong; trang gán https://claude.ai/artifact/MMptLRDAjna7AeZakF2cxC (lô thử và 108 câu silver); file Word cho luật sư.
- [x] 05/11 A6 đợt 1: gold mù 60 câu T2, T3, phiếu Excel, 0 dòng người được giao đã thấy. Đợt 2 (T6, T1) chờ A4, A5.
- [x] 05/11 A2: đối chiếu VBHN xong, độ phủ rất thấp.
- [x] 05/11 A9: đọc nguồn và khảo sát tính mới; `related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md`.
- [x] 05/11 A21, A22, A20: chương 2 đã sửa; X4 đo lại (b7 0/151); gói X8 sẵn ở `colab_upload/dev_x8/`.
- [x] 05/11 A4 bước lọc: 51/51 gói; đạt cổng hiệu chuẩn sát ngưỡng (loại đúng 28/28, loại nhầm 11/40). Giữ T2 157, T2 gần giống 63, T6 cấp trên 48, T6 đích danh 50; T3 0. Phễu: `docs/reports/pheu-loc-lo-moi.md`.
- [ ] A4 bước viết câu hỏi: 275/318 mục đã viết; kiểm máy: 149 đạt (T2 79, T2 gần giống 31, T6 cấp trên 21, T6 đích danh 18), 36 viết lại, 90 không đủ ngữ cảnh (dừng theo quy tắc). Còn 2 gói và lượt viết lại, tự chạy khi Codex mở lại (6/11 04:05). Sau đó: đáp án ngắn, phiếu lô 7+, gold mù đợt 2 có T6.
- [x] 05/11 A10: tập dượt trên dev, 151/151 hash khớp mỗi hệ, 17/17 hệ trùng điểm và KTC (`runs/final_rehearsal_dev/`).
- [x] 05/11 A18: phản biện xong (`docs/reports/phan-bien-ban-nhap-20261105.md`); bản nháp đã sửa theo, 0 số thiếu nguồn, mẫu 30 số khớp 30.
- [ ] CMT gửi file Word cho luật sư, mời NMT vào trang, chạy Colab (dev_x1, dev_x2, dev_x8, round2).
- [x] 10/11 H2 tra trước (AI-đề xuất): 9 ca VBHN đồ thị chọn đúng phiên bản ở mọi ngày hỏi; 2 tín hiệu bãi bỏ là giả (căn sang điểm bên cạnh); 1 câu thiếu ở NĐ 209/2013 Đ3 k11 v1 vào H5. H021 (gold đợt 2): đề xuất loại khỏi T1 theo R3. Lawgical 7/20 lượt; còn lại qua API vbpl. Chờ luật sư.
- [x] 11/11 H6: dựng lại một lần (L1, L2, L4, L6, L7/Q1), vector phần thiếu trên Colab; 15 hệ dev chạy lại với GPT-4o mini, P vẫn `proposed2` (`runs/README.md`). Báo cáo GVHD: `docs/reports/bao-cao-tien-do-gvhd-20261111.html`.
- [x] 11/11 H7 xong: `legal-adjudicator` (opus, 2 phiên) chốt 47 lineage (`data/review/ai_research/2026-11-11_h7/`, kiểm `scripts/review/check_ai_verdicts.py`): silver đạt 80 → 75 (5 dòng dat → khong_dat). H10 phần 1: 17 dòng T6 dev → 8 giữ, 9 loại (`2026-11-11_t6_package/adjudication.md`); VBHN, H021 giữ; hai dòng thuế 2012 `question_ambiguous`. 13 quy tắc mở gom ở `docs/reports/quy-tac-mo-20261111.md`, chờ CMT. H8: phản biện `docs/reports/phan-bien-adr-0006-20261111.md` (7 điểm chặn). Đang rà R2 cho 27 lineage T6 bộ test cuối + 4 dòng dev còn lại.
- [x] 11/11 H10 phần 2: `legal-adjudicator` (opus, 2 phiên) rà R2 cho 27 lineage T6 bộ test cuối (`data/review/ai_research/2026-11-11_t6_r2/`): 24 `giu`, 3 `relocation_unclear` (0ba67328, 0ba67346: Phụ lục II NĐ 01/2019 chỉ đọc được qua nguồn phụ; d88e3c54: Luật sư 2012, chuyển tiếp hai năm), 0 ca Q1. Hai quy tắc mở mới N1, N2 ghi ở `docs/reports/quy-tac-mo-20261111.md`. Kiểm máy: đủ 27/27, mã hợp lệ. Chưa áp loại vào bộ test cuối.
- [x] 11/11 Đếm lại bộ test cuối (`data/review/ai_research/2026-11-11_final_count/count_final.py`): **157 lineage** (silver 75 sau H7, lo2 70, bổ sung 12) = T2 127, T6 24 (sau N2: 156, T6 23), T3 6, T1 0; đã trừ 3 lineage R2. Hai dòng lo2 dafc3b40 không nằm trong tập đạt nên không đổi số. Còn mở: N2 (có thể −1), N3 (có thể +2). Đạt ngưỡng G2 ≥ 130. Chưa dựng file phát hành.
- [x] 11/11 H10 xong: chấm lại dev sau khi loại 12 lineage T6 (9 R2 + 3 Q1; 151 → 127 dòng), không gọi API mới (`runs/t6_dev_r2_20261111/rescore.py`). T6 không đáp án còn 9: `proposed2` 3/9, `proposed3` 3/9, `b7pp` 2/9, `oracle` 9/9. Quy tắc chọn P chạy lại: hiệu 0 [−0,33; 0,33], **P vẫn `proposed2`**. Accuracy dev `proposed2` 0,722 → 0,764.
- [x] 11/11 T1 đối chứng: AI-A (Claude Sonnet) + AI-B (Codex, bản gán lại `2026-11-11_t1_ai_b_redo/`, chốt trước khi đo) trên 60 lineage: verdict AC1 0,919, κ 0,870, p_neg 0,903 (gate pass); 6 dòng lệch Q (3 lệch verdict). AI-B chunk02 lượt đầu hỏng 3 lần (transport, định dạng, rỗng), lưu `failed_attempts/`. Giới hạn: phiên gán lại đã thấy nhãn AI-B lượt trước, không thấy AI-A. `legal-adjudicator` đề xuất 6 dòng lệch: cả 6 `khong_dat` (`adjudication.jsonl`, kiểm miền giá trị qua). Đề xuất T1 đạt: 43/60. Phiếu `duyet_CMT.xlsx` chờ CMT.
- [x] 12/11 **G2 xong:** release bộ test cuối `data/vilextime_final/` (199 lineage, 722 dòng; sha256 `5766f916…`), điền ADR 0006 §1, §6 (MDE). Phiên điều phối kiểm độc lập: hash, đếm, 0 trùng dev, 676/676 đáp án khớp đồ thị dựng lại, 748 test qua. `t6_ancestor` sửa thành chỉ dòng không đáp án. **Trước G3 còn:** cách chạy `final_run.py --data` với bản nội bộ của release mới (không sửa guard); CMT + NMT duyệt ADR 0006.
- [ ] D0: bản nháp 7 chương và paper. Đã có nháp đủ, 0/437 số thiếu nguồn, chờ phản biện và Colab.

## Decisions

- 2026-11-05: Coi v1.0 và test 2 là vòng thử có khai báo. Kết luận chính dựa trên bộ test cuối mới.
- 2026-11-05: Không yêu cầu hệ đề xuất phải thắng. Mục tiêu là đo đúng.
- 2026-11-05 (CMT): giờ GPU không phải giới hạn; gán nhãn trong cuối tuần 07–08/11; luật sư tham gia; cho commit.
- 2026-11-05 (CMT): repo GitHub đang công khai, CMT biết và vẫn cho push lên `develop`. Claude tự commit và push `develop` sau mỗi việc đã kiểm. Quyết định E2 (giữ riêng tư đến khi kiểm quy định ẩn danh) coi như đổi; phải xem lại trước khi nộp hội nghị.
- 2026-11-05 (CMT): cân nhắc giao agent gán toàn bộ rồi chọn **người gán**. Agent chỉ hỗ trợ ở các khâu ghi trong mục "Ai làm gì", không tính vào nhãn chính. CMT muốn có bản nháp Chủ nhật 08/11 (D0).
- 2026-11-06 (CMT): **đổi quy trình gán nhãn.** Agent làm phần gán: AI-A, AI-B gán mù độc lập theo thẻ 4.0, đo AC1/p_neg AI–AI, `legal-adjudicator` đề xuất cho dòng lệch. CMT duyệt mọi dòng, có xem nhãn và lý do AI, rồi đồng ý hoặc sửa; nhãn CMT là nhãn cuối. Bỏ lịch hai người gán mù lô 0 và silver ngày 07–08/11. Thay quyết định 05/11 "chọn người gán" và các dòng "A và B gán độc lập", "người gán không thấy gợi ý AI" ở mục Quy tắc gán nhãn. Hệ quả phải ghi trong paper: không còn đồng thuận người–người cho bộ cuối; chỉ báo AI–AI và tỷ lệ CMT sửa nhãn AI; dòng vào test có tầng "AI gán, người xác nhận" (định nghĩa §6, sửa 06/11). Mặc định (CMT đổi được): luật sư chốt các dòng CMT ghi `[phân vân]`; gold mù giữ nguyên, phải xong trước khi CMT duyệt câu gold của mình (B6).
- 2026-11-06 (CMT): **từ silver phần 5, AI-A chạy bằng Claude, AI-B bằng Codex.** Lý do: trên cùng 44 câu silver phần 2–4, hai bên cùng model khớp cao hơn hẳn khác model (verdict AC1: Claude–Claude 0,867, Codex–Codex 0,728, chéo model 0,64–0,78; `round2_claude/cross_model.json`). Hai bên cùng input, lời giao việc, taxonomy, ngân sách và khả năng tra (API vbpl, tìm web). Số đo báo là đồng thuận chéo model. Phần 1 (Claude–Claude) và phần 2–4 (hai lượt cùng model) báo riêng, không gộp.
- 2026-11-10 (CMT): **chốt theo đề xuất AI, không chờ luật sư** cho H2 (9 ca VBHN, 2 tín hiệu bãi bỏ: đồ thị đúng), H021 (loại khỏi đối chứng T1, R3 `superseded_by_other_norm`) và H4 (G108 `kg_wrong_repeal`, quy ước `dong_y`). Ghi "AI-đề xuất, CMT xác nhận, chưa qua luật sư"; phải khai trong paper. Ca 1 VBHN (NĐ 122/2011 "kỳ tính thuế từ năm 2012") chốt theo ngày hiệu lực; hai dòng silver 2012-01-31, 2012-02-29 có thể thuộc `question_ambiguous` theo phán quyết luật sư 10/11 mục 4, để mở.
- 2026-11-10 (CMT): **H5/H6 theo đề xuất** (`docs/reports/h5-loi-do-thi-20261110.md` mục 5): Q1 bãi bỏ một phần khoản → đánh dấu `partial_repeal`, loại khỏi chấm; Q2 lấy mẫu ~30 văn bản lớp L2 rồi đặt luật chung (tối thiểu ghi đè 31760, NĐ 161/2004); Q3 sửa `align_by_marker` trong lần dựng lại này; Q4 loại theo dòng cho H021; Q5/Q6 `vn-law-verifier` tra 14 sự kiện bãi bỏ một phần và 4 lineage L4 trước khi dựng. Dựng lại một lần, rồi **chạy lại toàn bộ** truy xuất và generator GPT-4o mini cho mọi hệ trên dev (không phát lại câu trả lời cũ), so với dev 09/11 và kiểm lại quy tắc chọn P. Bắt đầu sau khi `evidence-gate` kiểm H5.
- 2026-11-11 (CMT): **loại 2 dòng lo2** `vilextime:T6:provision:dafc3b40-2d46-11f1-a24f-2977df249dcf:2024-06-30` và `…:2024-07-01` khỏi bộ test cuối: sự kiện `event:168125:91e09140c1ccddd85dcbaf0b` (Luật 15/2023/QH15) trỏ nhầm văn bản đích 21/2017/QH14 (document:131014) thay vì Luật 40/2009/QH12; không sửa đồ thị thêm lần nữa (ADR 0006 mục 7). Áp bằng cơ chế loại theo dòng khi dựng bộ test cuối. Các sự kiện "Luật/Pháp lệnh <tên>" khác (111) và 2.633 sự kiện danh sách điều/khoản vẫn chưa đo, phải khai là giới hạn.
- 2026-11-11 (CMT): theo chẩn đoán T6 dev (`docs/reports/chan-doan-t6-dev-20261111.md`): (1) báo T6 tách dòng có/không đáp án, thêm cột "lệnh bãi bỏ có trong prompt", không đổi scorer hay điểm; (2) mở rộng X8, **chỉ chẩn đoán, chỉ dev**: 21 dòng T6 không đáp án, C0 = prompt `proposed2` giữ nguyên gọi lại (đo nhiễu API), C1 = cùng prompt nhưng lệnh bãi bỏ gold đặt lên đầu (chèn nếu thiếu); dùng gold nên không dùng để chọn P hay báo như kết quả hệ. Hướng 3 (đổi P) quyết sau khi có kết quả (2). Quy tắc 4 của prompt (chuyển chỗ) và nhãn T6 không đáp án: hỏi luật sư.
- 2026-11-11 (CMT): **agent thay luật sư ở khâu chốt ca khó.** (1) Tầng nhãn bộ test cuối giữ "AI gán, CMT duyệt", không thêm người kiểm mẫu; generator chính GPT-4o mini; phần chưa đo ghi là giới hạn. (2) `legal-adjudicator` (opus, phiên mới) **chốt** thay luật sư: 17 dòng T6 dev, 9 ca VBHN + 2 tín hiệu bãi bỏ, H021, hai dòng thuế 2012, và H7 (24 dòng silver CMT ghi sửa + dòng `[phân vân]`). Quyết định này thay mặc định 06/11 "luật sư chốt dòng `[phân vân]`" và cột "Người chốt: luật sư" ở hàng H2, H7. Ghi "AI-chốt (`legal-adjudicator`), CMT ủy quyền, chưa qua luật sư"; paper phải khai không có luật sư hay người độc lập kiểm các ca này. Gold mù (B6) không đổi. (3) T6 chuyển chỗ áp **quy tắc đã có** (R2, §6 điều 7 định nghĩa): loại với mã `relocated` hoặc `relocation_unclear`, không đổi đáp án; báo cáo `t6-chuyen-cho-tra-cuu-20261111.md` nêu lựa chọn (a)/(b) là sai, R2 đã chốt. Sau đó rà R2 cho mọi dòng T6 của bộ test cuối, chấm lại T6 dev, rồi mới quyết hướng 3.
- 2026-11-11 (CMT): **N2 loại.** Dòng T6 có đáp án mà nửa đáp án chỉ là dẫn chiếu, câu hỏi hỏi đúng phần dẫn chiếu: loại cả lineage, mã `reference_only`. Áp cho e9ffd3da; bộ test cuối 157 → 156.
- 2026-11-11 (CMT): **thêm ~60 lineage T1 mới vào bộ test cuối** làm phép kiểm không làm hại, ngoài Holm (thay dòng "T1 không vào bộ này" ở mục bộ test cuối). Nháp ADR 0006 §1, §4 (δ = 0,05). Quy trình: rút mẫu, viết câu hỏi và đáp án ngắn bằng model rẻ (haiku), AI-A/AI-B gán, CMT duyệt. G2 có thể trễ 1–2 ngày.
- 2026-11-11 (CMT): **Q1 loại.** Dòng T6 không đáp án mà quy phạm cấp thấp hơn hoặc có từ trước vẫn điều chỉnh đúng nội dung được hỏi: loại lineage, mã `relocation_unclear`. Áp cho dev 6cab03a0, 6caa8e70, 1a267400; bộ test cuối không có ca nào.
- 2026-11-11 (CMT): **duyệt phiếu T1 theo đề xuất** ("ok bạn nhé"): 43/60 T1 đạt (`2026-11-11_t1_labels/cmt_confirmed_t1.json`). Bộ test cuối: 156 lineage chính (T2 127, T6 23, T3 6) + 43 T1 đối chứng = 199 lineage, 361 cặp (câu hỏi, mốc) ở ranh giới. Xác nhận qua hội thoại, thời gian từng dòng không đo.
- 2026-11-12 (CMT): **chạy mỗi hệ sinh hai lần trên bộ cuối** (ADR 0006 §5b: lần 1 chính, chỉ "ủng hộ" khi hai lần cùng phán quyết). **ADR 0004 amendment 09/11 (GPT-4o mini) Accepted.** NMT chưa có xác nhận riêng trong repo.
- Quyết định cũ còn hiệu lực: A2, A3, B2, B6, B7, B9, C2, C3, C4, C5, E1–E5 (MASTER_RESEARCH_GUIDE §13.3 tại `51f36c7`), và reranker cắt 05/11.

## Validation

### A4 lô mới T2/T6/T3, 08/11/2026

- Codex hết hạn mức đến 9/11, nên phần viết câu hỏi còn dở chạy bằng Claude
  subagent Sonnet, effort thấp; đáp án ngắn dùng Haiku. Hồ sơ biên soạn ở
  `~/vilextime_loc/gan5/` (ngoài repo): `chot_r*_claude.jsonl`, `chot_r2_redo36.jsonl`,
  `backlog/conflict_choices_0811.json`, `excluded_*_0811.json`.
- Một lượt viết lại bị loại trước qcheck, không tính lượt: agent ghi
  KHONG_DU_NGU_CANH vì khó qua cổng, và chèn cụm đệm để lách copy_share.
  Lượt chạy lại có công cụ tự chấm dùng đúng hàm qcheck.
- [x] 181 câu qua qcheck → contrast loại 51 T2 (đáp án bản cũ nằm trong bản mới)
  → 2 câu thiếu nguồn bị loại → **`data/review/the4/lo2_moi_worksheet.jsonl`:
  128 lineage** (T2 54, T2 gần giống 31, T6 cấp trên 22, T6 đích danh 19, T3 2),
  258 mốc, batch 7–11.
- [x] AI-A (Claude Opus, `2026-11-08_lo2/run_a.py`): đủ 12/12 chunk, 128 câu,
  sau lượt chạy ngoài sandbox 08:23–08:33 UTC. Raw và metadata giữ nguyên;
  lỗi hạn mức trước ở `claude_logs/failed_0811/`. Còn kiểm schema đầy đủ trước
  khi khóa cặp nhãn, đo, hòa giải, CMT.
- [x] AI-B (Codex native): hoàn tất 12 worker mù riêng, 128/128 câu;
  `2026-11-08_lo2/validate_b.py` kiểm native validator, đúng tập ID từng chunk,
  binding, verdict, evidence và provenance: không thiếu/trùng/lỗi. Có 93 nhãn
  báo đủ nguồn, 35 báo thiếu nguồn; đây không phải số câu đạt. Hash raw/input/
  prompt và kết quả ở `b_raw_validation.json`; chưa đo đồng thuận khi A còn thiếu.
- [x] Lượt 3 viết lại đủ 60 câu (29 redo36, 30 Claude, 1 backlog), giữ đủ hai
  lượt trước khi chạy qcheck gốc: 12 qua qcheck, 48 bị loại terminal vì
  copy_share, không còn lượt viết lại (`round3_validation.json`). Hai worker
  dừng vì hạn mức sau khi lưu đủ answers/provenance; điều phối kiểm tệp rồi
  chạy qcheck, không tính lỗi transport thành câu trả lời mới. T3 vẫn chỉ có 2.
- Tiếp tục phiên Codex 08/11, trước giờ Claude mở lại 05:50 UTC: đã kiểm
  hash manifest/worksheet/12 chunk và binding đủ 128 lineage, đều khớp.
  AI-B bắt đầu bằng các worker Codex mù riêng, không đọc nhãn AI-A; không
  cần chờ mốc dự kiến mở lại Codex vì runtime phiên này đã hoạt động.
- Hồ sơ lượt viết cuối được sao chép có chọn lọc vào
  `data/review/ai_research/2026-11-08_rewrite_final/`: 29 + 30 + 1 mục,
  mỗi mục giữ đủ hai lượt trả lời trước; bản ngoài repo giữ nguyên.
- [x] Trích 11 đáp án ngắn cho 7 câu redo36 vào
  `2026-11-08_rewrite_final/seven_shorts/answers.jsonl`; cả 11 đoạn khớp
  nguyên văn nguồn. Native `test2_prepare.py contrast`: 7/7 không phát hiện
  vấn đề, `needs_review=0` (`seven_contrast.json`). Chưa bổ sung vào worksheet
  128 câu đã đóng băng cho lượt nhãn đang chạy; chưa phải nhãn người hay G2.
- Kiểm tra nhãn Claude chunk01–04 phát hiện lệch schema (thiếu verdict,
  thiếu lineage_id, hoặc Q nằm trong từng mốc). `2026-11-08_lo2/normalize_a.py`
  tạo bản dẫn xuất trong `normalized_a/`, giữ nguyên raw và evidence_status.
  Binding xác định lineage; Q1 sai ở một mốc làm câu không đạt Q1 theo thẻ;
  các Q còn lại theo mốc phải đồng nhất, không thì dừng. Cả 48 nhãn dẫn xuất
  qua `ai_labels.read_labels`; hash và từng trường suy ra nằm trong receipt.
- `locate_a_evidence.py` tạo `canonical_a/`: gắn URL khi quote khớp nguồn có
  sẵn, gồm đối sánh các đoạn nguyên văn có dấu lược; nếu chỉ khớp worksheet
  thì ghi tầng worksheet. 48/48 nhãn có 1–2 evidence có locator; 6 evidence
  gốc chưa định vị được giữ trong original_evidence/receipt để rà khi hòa giải.
  Không đổi Q, reason, note, quote hay evidence_status; không có lượt tra mới.
- Phiếu riêng cho 7 câu bổ sung: `2026-11-08_rewrite_final/seven_worksheet.jsonl`
  (4 T2, 3 T6, 14 mốc), đủ nguồn và URL văn bản tác động, chưa có nhãn A/B.
- Tiếp tục 08/11 08:17 UTC (đã qua 05:50): chạy lại `run_a.py` đúng lệnh gốc,
  bỏ qua chunk01–04, xử lý chunk05–12; chờ kết quả, chưa tuyên bố A hoàn tất.
- Lượt 08:17 lỗi mạng/DNS `EAI_AGAIN` ở chunk05–08; dừng runner trước khi
  thử tiếp trong sandbox, lưu lỗi tại `claude_logs/failed_network_0817/`.
  Được cấp quyền chạy ngoài sandbox và khởi động lại đúng script lúc 08:23 UTC.
- A chunk07 bỏ sót Q4 ở `52444e30…` và `ae8436dc…` (không suy ra được từ
  verdict vì Q3 đã không đạt). `complete_a_schema.py` giao chính Claude hoàn
  tất riêng các trường thiếu, chỉ đọc packet gốc/nhãn A của mình, không xem B,
  không thêm lượt web. Patch gắn hash raw/binding, lưu riêng `schema_completion/`.
  Trường Q đã có giữ nguyên; nếu Q mới thiếu căn cứ, Claude phải hạ trạng thái
  nguồn và ghi phân vân. `finish_lo2.py` tái dùng lock/measure/review và runner/
  validator legal-adjudicator gốc; chưa tự ghi xác nhận CMT.
- [x] Claude đã hoàn tất hai Q4 riêng, không thêm web: đều Q4=khong có phân
  vân, hạ evidence_status xuống insufficient. Patch, raw trả lời và metadata
  được giữ; không có quyết định Q nào do Codex tự bổ sung cho AI-A.
- [x] Khóa đủ 128/128 cặp, không thiếu/trùng/lỗi native validator. `a.jsonl`,
  `b.jsonl`, `metrics.json` và phiếu `duyet_CMT.xlsx` là kết quả trước hòa giải.
  AC1/p_neg: Q1 0,932/0,759; Q2 0,967/0,333; Q3 0,849/0,755;
  Q4 0,753/0,465; verdict 0,503/0,680. **Cổng đồng thuận chưa đạt** (Q2,
  Q4, verdict); không lọc ca thiếu nguồn hoặc thay số đo bằng nhãn hòa giải.
- [ ] `legal-adjudicator` (Claude CLI đúng agent, đọc trực tiếp skills):
  49 ca lệch cả Q/reason, 11 packet, chạy tối đa 3 worker từ 08:38 UTC.
  Snapshot/hash tại `2026-11-08_lo2/adjudication/`; validator gốc
  `2026-11-07_adjudication_all/package_review.py:load_validate` kiểm cuối.
  Phiếu sau hòa giải dự kiến `duyet_CMT_after_adjudication.xlsx`, CMT chưa duyệt.
- Lượt hòa giải Claude 08:38 chạm hạn mức 5 giờ, mở lại **13:20 UTC**;
  không có đề xuất hoàn chỉnh, toàn bộ metadata lỗi được giữ ở `adjudication/`.
  Chuyển sang worker Codex native theo tiền lệ đã chấp thuận ngày 07/11,
  giữ nguyên spec `legal-adjudicator`, skills và packet; ghi runtime thực tế,
  không giả Claude. Hồ sơ làm việc: `schema_validated/adjudication_native/`.
- Validator nhãn gốc không chặn enum evidence_status của A: phát hiện 5 dòng
  `partial`. Bản khóa đầu và snapshot hòa giải Claude vẫn nguyên. Snapshot
  **`schema_validated/`** ánh xạ metadata partial→insufficient, giữ giá trị gốc,
  không thay Q/reason/verdict hay loại dòng; mọi số đo toàn lô và theo nhóm
  khớp chính xác bản đầu. A: 92 sufficient, 36 insufficient; B: 93/35.
  Binding, 128 cặp và enum nguồn của snapshot mới đều hợp lệ. Hash và 5 ID nằm
  trong `schema_validated/metadata_normalization.json`.
- Kiểm cuối Codex native: `.venv/bin/python data/review/ai_research/2026-11-08_lo2/finalize_native.py`.
  Tái dùng validator hòa giải gốc, đối chiếu raw/provenance với JSONL và xuất
  phiếu CMT từ snapshot schema_validated; không ký hoặc chấp nhận thay CMT.
- Đã trích thêm 20 đáp án ngắn nguyên văn cho 12 câu qua qcheck. Contrast gốc
  loại 1 T2 (`eaad300c…`: đáp án bản mới vẫn nằm trong bản cũ); không dùng ký
  hiệu mục để tạo tương phản giả. 11 câu còn lại + 7 câu bổ sung tạo
  `2026-11-08_rewrite_final/supplemental_worksheet.jsonl`: **18 ứng viên**, 36
  mốc (11 T2, 7 T6). Không thay worksheet 128 câu đang gán; chưa tính vào G2.

### Tiếp quản sau Claude hết hạn mức 18:20 UTC, 08/11/2026

- [x] Đối chiếu hồ sơ Claude đã tiếp tục: `2026-11-08_supp18/` đủ 18/18 cặp
  khóa, 12 cùng verdict đạt; verdict AC1 0,538, cổng chưa đạt. Sáu ca lệch dùng
  run_id/case_id supp18 riêng, không lẫn ID lo2. Bản nhãn/metric/snapshot giữ nguyên.
- [x] Lô 128: Claude đã để lại gói 07–09, gói 10 còn thiếu. Codex native hoàn
  tất gói 10 (5 ca) và hai gói supp18 (6 ca), theo spec legal-adjudicator, ghi
  đúng runtime và nguồn cached/live. Không có worker còn chạy khi đóng phiên.
- [x] Validator gốc `2026-11-07_adjudication_all/package_review.py:load_validate`
  qua đủ **49/49 ca lo2** và **6/6 ca supp18**: hash nguồn/nhãn, binding,
  schema, verdict và prefer_a/b khớp đúng Q/reason của bên được chọn.
  Đối chiếu raw/results và provenance cũng qua. Lỗi đóng gói được sửa có giữ
  nguyên bản tại schema_originals: reasoning object→text, gắn nguyên evidence
  ngoài vào proposed_label; không sửa Q/reason/verdict. Hai ca lo2-032/043
  tự báo insufficient nhưng ghi resolved được trả về unresolved, giữ tentative
  label và câu hỏi mở; không nâng sufficient để vượt validator.
- Kết quả lo2: **69 đề xuất đạt, 39 không đạt, 20 chưa chốt**; 49 ca hòa giải
  gồm 11 prefer_a, 16 prefer_b, 2 both_wrong, 20 unresolved. Có runtime hỗn hợp
  Claude/Codex; raw/provenance từng packet là nguồn ghi nhận, không gọi cả lô
  trọng tài là một model duy nhất.
- Kết quả supp18: **12 đề xuất đạt, 3 không đạt, 3 chưa chốt**. Sáu ca hòa giải
  gồm 1 prefer_a, 2 both_wrong, 3 unresolved; hai both_wrong có lỗi mốc hiệu
  lực khiến hai mốc có cùng đáp án thực tế, nên Q2=group_mismatch.
- [x] Xuất phiếu CMT (sheet Duyệt và Hòa giải, không có xác nhận người):
  `2026-11-08_lo2/duyet_CMT_after_adjudication.xlsx` (128 câu) và
  `2026-11-08_supp18/duyet_CMT_after_adjudication.xlsx` (18 câu).
  Nguồn quá dài trong một ô được ghi rõ là preview, toàn bộ giữ tại JSONL,
  không cắt ngầm bằng giới hạn Excel. Hai script kiểm/xuất có thể chạy lại:
  `.venv/bin/python data/review/ai_research/2026-11-08_lo2/finalize_native.py`
  và `.venv/bin/python data/review/ai_research/2026-11-08_supp18/package_review.py`.
- **Trước xác nhận CMT 15:35 UTC**, G2 chưa đạt số lượng: silver được CMT chấp nhận 81, mới chấp nhận 0.
  Hai lô mới có tổng 81 đề xuất đạt, 42 không đạt, 23 chưa chốt. Nếu CMT nhận
  cả 81 đề xuất đạt thì số lượng là 162≥130; đây là điều kiện, không phải nhãn
  đã duyệt hay tuyên bố cổng đồng thuận đạt. AC1/p_neg trước hòa giải giữ nguyên.
- Còn lại trước xác nhận: CMT xem hai phiếu, luật sư/CMT chốt 23 ca nguồn/quy tắc còn thiếu;
  không tự diễn giải thêm chính sách khi authority chưa rõ. Danh sách từng ca
  và câu hỏi mở ở `2026-11-08_lo2/open_cases_for_CMT.jsonl`; tổng hợp ở
  `2026-11-08_lo2/combined_review_summary.json`. Không phát hành dữ liệu test.

### CMT duyệt hai lô mới qua hội thoại, 08/11/2026 15:35 UTC

- Hồ sơ tiếp tục ngày 09/11: [Nguyên nhân và checklist xử lý 23 ca mở, đồng
  thuận AI–AI](../../reports/resolve-nhan-va-dong-thuan-20261108.md).
  Đây là phân tích/đề xuất; chưa đổi thẻ, nhãn, ngưỡng hay miễn cổng.

- CMT xác nhận trực tiếp: “MÌnh (CMT) đã đọc xong rồi và mình duyệt nhé”.
  Ghi nhận việc CMT tự báo đã đọc và duyệt các kết luận hiện có, không suy ra
  lịch sử đọc từng dòng, không ký thay CMT hoặc sửa nhãn AI thô/metric.
- [x] Hai tệp `cmt_acceptance.json` tại `2026-11-08_lo2/` và
  `2026-11-08_supp18/` ghi câu xác nhận, hash hai phiếu/nhãn/metric/kết quả
  hòa giải và phạm vi. `cmt_accepted_labels.jsonl` mỗi lô giữ nhãn nguồn cùng
  quyết định CMT riêng: 108 + 15 = **123 kết luận được duyệt**, gồm **81 đạt,
  42 không đạt**. Không biến 23 ca unresolved thành nhãn cuối vì chưa có
  quyết định Q/reason cuối để duyệt; chúng vẫn cần nguồn/quyết định cụ thể.
- **Đạt ngưỡng số lượng G2: 162 câu đạt được chấp nhận**, gồm 81 silver +
  69 lo2 + 12 supp18. Cổng đồng thuận vẫn chưa đạt, không được miễn qua lời
  duyệt nhãn. Chưa phát hành dataset; 23 ca chưa chốt giữ ngoài nhãn cuối.
- Tổng hợp hiện tại ở `2026-11-08_lo2/combined_review_summary.json`; bản trước
  CMT giữ tại `combined_review_summary_before_CMT.json`. Hai summary validator
  hòa giải vẫn là bằng chứng trước phê duyệt; đọc kèm cmt_acceptance.json,
  không ghi đè bằng chứng kiểm hay thay nhãn thô thành nhãn người.

### Chốt 6 ca hòa giải còn mở, nhãn AI cuối silver, 08/11/2026

- Yêu cầu người dùng: dùng `legal-adjudicator` giải nốt các ca cần CMT. Đã chạy
  5 subagent (Claude Code, claude-opus-5-5), mỗi lineage một agent. Kết quả ở
  `data/review/ai_research/2026-11-08_adjudication_final/`; thư mục 07/11 giữ
  nguyên, hash khớp.
- [x] 62/62 ca có đề xuất (21 A, 25 B, 16 cả hai sai), 0 unresolved. Validator
  gốc chạy trên kết quả đã ghép: hợp lệ. Năm lineage đều không đạt, ở mọi cách
  đọc câu hỏi phụ còn mở.
- [x] `silver_ai_final.jsonl` + `duyet_CMT_final.xlsx`: một phiếu cho 168
  lineage. Có **81 đạt** (T2 71, T3 10) và 87 không đạt. Xác nhận người: 0.
- 08/11 (CMT): **chấp nhận hàng loạt cả 168 nhãn AI silver**, không duyệt từng dòng
  (`cmt_acceptance.json`). Tầng chất lượng: AI gán, người chấp nhận hàng loạt;
  paper phải khai, không gọi là người kiểm từng dòng.
- Còn lại cho G2: luật sư chốt 5 khoảng trống quy tắc
  (README thư mục); silver tối đa ~81 lineage, chưa đủ ngưỡng 130. Cần thêm
  T2/T6/T3 mới mới đạt G2.

### Hòa giải toàn bộ xung đột AI, 07/11/2026

- Yêu cầu trực tiếp CMT: dùng `.claude/agents/legal-adjudicator.md` xử lý hết
  xung đột. Phạm vi: cả lô thử 0, silver chunk01, hai lượt chunk02–04 và lượt
  chéo model chunk05–11. So cả Q1–Q4 và reason; thêm ca unresolved trước đây.
- Phạm vi cuối: 62 trường hợp theo lượt, 59 lineage riêng biệt; gồm thêm
  bất đồng chéo model bị che bởi đồng thuận nội bộ, và phần Sonnet đã có nhãn
  đôi (14/30 câu). Không gán tiếp 16 câu Sonnet chưa hoàn thành. 94 tệp gốc và
  38 snapshot được đóng băng bằng hash; không gộp IAA các lượt.
- Claude CLI chạy đúng `--agent legal-adjudicator`, nhưng hết hạn mức tuần,
  reset 11/11 02:00 UTC. Không có nhãn hoàn chỉnh từ CLI; lưu metadata lỗi.
  Đã thông báo CMT và chuyển runtime sang Codex native, giữ spec/skills,
  model kế thừa; ghi rõ điều chỉnh công cụ trong provenance, không giả Claude.
- [x] Đóng băng đầu vào/nhãn/metric/phiếu cũ; chạy Claude CLI với đúng agent
  legal-adjudicator theo từng lô; không đưa kết quả hệ vào ngữ cảnh.
- [x] Kiểm đủ mọi case, hash/binding/schema/taxonomy và nguồn; unresolved giữ
  nguyên nếu chưa đủ căn cứ, không ép chọn A/B. Xuất phiếu mới, không ký thay CMT.
- [x] Báo số giải quyết được, số còn mở, kiểm hash cũ không đổi. Kết quả tại
  `data/review/ai_research/2026-11-07_adjudication_all/`.
- Kết quả: 56/62 đề xuất đầy đủ (19 chọn A, 24 chọn B, 13 cả hai sai),
  tương ứng 54/59 lineage. 6 trường hợp thuộc 5 lineage còn mở: nghĩa thay đổi
  bán/buôn bán; mới/chưa qua sử dụng (hai lượt); lời văn thay cụm bị lặp;
  kỳ tính thuế không nêu năm tài chính; thiếu mốc chuyển đúng thẩm quyền hàng hải.
  Không ép đủ Q để tuyên bố đã giải quyết toàn bộ. CMT vẫn phải duyệt mọi nhãn.
- Đã hỏi CMT về quy ước năm dương lịch của ca thuế, chưa có trả lời cụ thể;
  "tiếp tục" không được coi là chấp nhận quy ước mới. Các ca còn lại ghi rõ
  nguồn đã thử, điều đã chứng minh và thông tin cần CMT/luật sư chốt.
- Xuất `reviews/all_conflicts.xlsx` (62 dòng; sheet `Cần chốt`: 6 dòng),
  cùng 8 workbook native theo lượt, report/summary/provenance và hash nguồn.
  Toàn bộ ô xác nhận CMT trống. Giữ các đề xuất cũ trong revisions khi sửa.
- Native validator: 62/62 hợp lệ; đề xuất cho cùng binding nhất quán. Fixture
  sai verdict/binding và đề xuất mâu thuẫn cùng worksheet đều bị từ chối;
  fixture nằm trong thư mục tạm, không trộn với kết quả nghiên cứu.

### Hoàn tất nhãn AI silver còn dở, 07/11/2026

- [x] Đợt 3 `round3_mixed/`: khóa 106 cặp chunk05–11 (A Claude, B Codex),
  212 nhãn hợp lệ; không thiếu, trùng hoặc bị loại. Chạy `reproduce.py` bằng
  `.venv/bin/python`, dùng validator và công thức native; không gộp IAA với đợt cũ.
- Chunk11 A thiếu `verdict` và URL evidence. `normalize_a11.py` suy verdict
  theo thẻ 4.0, giữ nguyên Q1–Q4/reason/note/quote/evidence_status. Bản Claude
  nguyên gốc ở `claude_logs/a_chunk11.original.md`; receipt
  `schema_normalization.json` giữ mọi evidence gốc, ghi nguồn thiếu URL.
  Evidence cấu trúc chỉ dùng quote khớp input; URL worksheet là vị trí input,
  không phải tra cứu pháp luật độc lập. Không gọi thêm model cho phần cơ học.
- Đồng thuận trước hòa giải: Q1/Q3 AC1 0,871, p_neg 0,706; Q2 0,933/0,667;
  Q4 0,977/0,909. Verdict AC1 **0,682**, p_neg 0,825, κ 0,678: **chưa đạt**
  ngưỡng 0,80. Có 25 câu lệch Q1–Q4, 17 câu lệch verdict. Không sửa nhãn để
  tăng đồng thuận. A thiếu căn cứ 10/106, B 18/106, vẫn giữ trong phép đo.
- [x] Xuất `round3_mixed/duyet_CMT.xlsx`: đủ 106 câu, chưa có xác nhận người.
  Nhãn, raw, input, provenance, receipt, script và workbook có SHA256SUMS.
- [x] Đóng gói phần tra cứu đợt 2 tại `round2_codex/duyet_CMT_bo_sung.xlsx`
  và `adjudication_report.jsonl`: đủ 26 câu, 17 đề xuất giải quyết được,
  9 unresolved; giữ nguyên hash nhãn, metric, provenance và workbook gốc.
- Còn lại: hòa giải 25 bất đồng đợt 3; bổ sung căn cứ còn thiếu; CMT duyệt
  mọi dòng. Hoàn tất lượt gán AI không đồng nghĩa hoàn tất xác nhận người hoặc G2.

### Tiếp quản gán nhãn silver đợt 2, 06/11/2026

- [x] Theo yêu cầu tiếp theo của người dùng: tra cứu bổ sung và đề xuất hòa giải
  cho đợt 2. Phạm vi là hợp 23 câu thiếu nguồn và 11 câu bất đồng: **26 câu**,
  chia chunk02: 7, chunk03: 10, chunk04: 9. Đề xuất là nhãn AI chờ CMT duyệt,
  không sửa a.jsonl/b.jsonl/metrics.json hoặc workbook gốc; xuất workbook mới.
  Nguồn đã mở, hash, giới hạn và câu hỏi còn thiếu được lưu cùng đề xuất.

- Cập nhật theo yêu cầu trực tiếp của người dùng: **Codex làm thay Claude Code**
  cho sáu lượt chunk02–04 × AI-A/AI-B. Giữ nguyên input, hướng dẫn và taxonomy;
  không tiếp tục chờ hạn mức Claude. Runtime mới là Codex native subagents,
  model kế thừa phiên chính (không suy đoán revision). Hai bên dùng context mới,
  không thấy nhãn nhau. Chạy tối đa ba worker đồng thời theo giới hạn runtime;
  cả sáu lượt vẫn là sáu phiên riêng. Không trộn provenance với chunk01 Claude.
- [x] Codex đã hoàn tất cả sáu lượt: 14 + 15 + 15 câu mỗi bên, 88 nhãn, 44 cặp;
  schema/ID/binding/dẫn chứng hợp lệ, không có nhãn bị loại ở bước kiểm máy.
  Nhãn thô ở `data/review/ai_research/2026-11-06_silver/raw/{a,b}_chunk02–04.md`.
- [x] Khóa và đo riêng tại `data/review/ai_research/2026-11-06_silver/round2_codex/`;
  `reproduce.py` dùng đúng công thức native, kiểm hash nguồn và input trước đo.
  Chạy lại sau khóa không đổi nhãn. SHA256SUMS lưu hash nhãn thô, input, aggregate,
  metric, provenance và phiếu duyệt. Hai file chunk01 Claude giữ nguyên byte.
- Kết quả trước hòa giải: Q1/Q2 AC1 0,876, p_neg 0,714; Q3 0,913/0,727;
  Q4 0,941/0,833. Nhãn suy ra: AC1 **0,728**, p_neg 0,857, κ 0,727 — **chưa đạt**
  ngưỡng AC1 0,80. Có 11 câu lệch ít nhất một Q, 6 câu lệch verdict. Không đổi
  nhãn thô để đạt ngưỡng. Chỉ áp dụng cho 44 câu silver của lượt Codex này.
- Thiếu căn cứ: A 17/44, B 16/44 phiếu `insufficient`, không âm thầm loại khỏi
  phép đo. Toàn bộ nhãn AI vẫn `not_verified`; đồng thuận không chứng minh đúng luật.
- [x] Xuất `round2_codex/duyet_CMT.xlsx`: 44 câu, chưa có xác nhận người nào.
  Chưa hòa giải hoặc duyệt thay CMT; chunk05–11 ngoài đợt này chưa chạy.
- Các mục về hết hạn mức Claude bên dưới là lịch sử trước khi người dùng cho
  Codex làm thay, không còn là lý do chặn đợt 2 này.

- Phần trước đã commit: `eb3d8d7` (framework), `3dfc95d` (silver phần 1,
  official text và prompts v2); working tree sạch khi tiếp quản.
- Sáu subagent Claude của phiên `aad8dda3-63f9-4858-b90a-0ae91504b00f` cho
  chunk02/chunk03/chunk04 × AI-A/AI-B đã kết thúc do hết hạn mức, không có
  khối JSONL cuối. Không tính `finished=true` trong metadata là gán xong.
- Đã kiểm lại SHA256 ba input với manifest trong
  `data/review/ai_research/2026-11-06_silver/`: khớp; số câu 14 + 15 + 15.
- Kiểm tra khả dụng trực tiếp bằng Claude CLI (không đọc dữ liệu): HTTP 429,
  `usage_limit_reached`, reset **06/11/2026 18:10 UTC**. Chưa có nhãn đợt 2;
  không chạy lại hàng loạt, không đổi model/nhà cung cấp hoặc suy nhãn thay.
- Tiếp tục sau reset: dùng đúng prompts `chunk02_ai-{a,b}.md` đến
  `chunk04_ai-{a,b}.md`, hai bên ngữ cảnh riêng, model `claude-opus-5-5` như
  lượt trước; chỉ lưu raw khi có đầu ra hoàn chỉnh, không ghi đè chunk01.
  Các file lời giao việc đã được chuẩn bị trong thư mục `prompts/` của run.

### Sửa framework theo yêu cầu CMT, 06/11/2026

- Phạm vi: cách ly cache fast/full và cấu hình sinh; lọc ngày trước fanout quan hệ;
  tái dùng điểm dense theo câu hỏi, chọn ứng viên chính xác theo lô; dùng chung
  seed giữa mở rộng đồ thị và thông báo bãi bỏ ở runner, export Colab và demo.
- Authority: yêu cầu sửa code của CMT ngày 06/11; ràng buộc tập căn cứ ở công thức
  (4) của `docs/graph_justification.md`; chỉ tinh chỉnh trên dev theo ADR 0003 §7.
  Giữ nguyên k, FANOUT, RRF và mô hình; không tự chọn siêu tham số hoặc chạy test.
- [x] Viết test hồi quy trước bản sửa: xác nhận cache lẫn fast/full, lẫn tham số
  sinh/model từ môi trường và bỏ sót instruction hợp lệ sau ba hàng chưa hiệu lực.
- [x] Sửa code và nối lại các caller; 92 test tập trung pass ở lượt đầu.
- [x] Suite đầy đủ: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q
  -p no:cacheprovider` → 715 passed (52,50 giây). Bao gồm đối chiếu dense với
  stable sort trên tie ở ranh giới, nhiều kích thước lô, NaN/inf, thay ngày/tier.
- [x] `git diff --check` sạch; `scripts/paper/paper_check.py`: 0 sai lệch,
  3/3 lỗi cấy bị bắt. Không thêm hook hoặc CI gate.
- Đã kiểm một phép chọn top-500 trên 1,5 triệu điểm float32 tổng hợp khớp stable
  sort; đây chỉ là kiểm thuật toán, không phải benchmark pipeline/corpus thật.
  Chưa sinh dự đoán mới hoặc chạy lại dev/test nghiên cứu; chưa có kết luận về
  thay đổi Accuracy/Recall hoặc tốc độ toàn pipeline.
- Tương thích: namespace cache mới không tái dùng mục cũ; không xóa cache, log,
  release hay kết quả nghiên cứu đã lưu. Kết quả graph mới có thể khác do sửa
  fanout; trước thực nghiệm tiếp theo phải xuất lại prompt và ghi hash/code mới.
- Khôi phục: hoàn tác đúng diff framework/caller/test của việc này; không đụng
  các thay đổi nhãn đang có của người dùng. Cache cũ giữ nguyên để đối chiếu.

- Plan không tự chứng minh điều gì. Mỗi cổng có tiêu chí đo được ở mục 7.
- Lệnh nền: `.venv/bin/python -m pytest -q`, `git diff --check`, `scripts/paper/paper_check.py`.

## Result

Chưa hoàn tất.

### AI-B cho 60 T1 mới, 11/11/2026

- Theo yêu cầu CMT: chỉ thực hiện AI-B bằng Codex, không thay bằng Claude khi
  hết hạn mức. Chưa đọc nhãn AI-A để đưa vào các phiên AI-B.
- Đầu vào và lời giao việc: `data/review/ai_research/2026-11-11_t1_labels/`,
  hai chunk × 30 chuỗi. Đã kiểm SHA256 hai chunk, định nghĩa và thẻ 4.0 khớp
  prompt AI-B. Q2 theo mục T1 đối chứng đã được CMT chấp thuận.
- Đã chạy `run_b.sh` (Codex `gpt-6-luna`, hai phiên ephemeral, read-only).
  Lượt trong sandbox lỗi khởi tạo do hệ thống tệp chỉ đọc; lượt được cấp quyền
  đã xuất hai gói. Gói 02 có 30/30 nhãn qua `ai_labels.read_labels`, không
  nhãn bị loại; worker báo thiếu căn cứ do API nguồn luật không truy cập được.
  Gói 01 lần đầu bị cắt giữa dòng, thiếu khối provenance; điều phối đã lưu
  lần lỗi ở `failed_attempts/` và hoàn tất lượt chạy lại, không chạy trùng.
- Hoàn tất phần AI-B: `.venv/bin/python .../validate_b.py` qua, **60/60 hợp
  lệ**, 0 thiếu/trùng/bị loại; kiểm hash input và binding. Bằng chứng:
  `data/review/ai_research/2026-11-11_t1_labels/b_raw_validation.json`;
  nhãn ở `raw/b_chunk01.md`, `raw/b_chunk02.md`, bản gốc và receipt chuẩn hóa
  ở `raw_original/`, log ở `codex_logs/`. `git diff --check` qua.
- Hạn chế: **60/60 evidence_status=insufficient**, tất cả `not_verified`.
  Validator chứng minh cấu trúc/độ phủ, không chứng minh đúng pháp lý hoặc
  người chấp nhận. Chưa có xác nhận người; phần AI-B không đo AC1 hoặc dựng
  phiếu duyệt thay cho tiến trình điều phối đang chạy.

### Gán lại AI-B T1 theo yêu cầu CMT, 11/11/2026

- Đầu ra riêng: `data/review/ai_research/2026-11-11_t1_ai_b_redo/b.jsonl`;
  giữ nguyên kết quả lượt trước. Tải đủ 58 toàn văn API nguồn chính thức sau
  khi được cấp quyền mạng; 20 lượt tra web và toàn văn 1317/QĐ-BTC đã lưu.
- Đối chiếu lại đủ 60 câu Q1–Q4: 44 `dat`, 16 `khong_dat`; 49 `sufficient`,
  11 `insufficient` do chưa xác minh ngày đăng Công báo bằng nguồn gốc.
  Danh sách mở ở `pending_evidence.tsv`; không đổi nhãn thành đã kiểm.
- `.venv/bin/python .../export_labels.py` qua: 60/60 hợp lệ, 0 thiếu/trùng/
  bị loại; hash/binding và mọi quote đối chiếu được với nguồn đã tải.
  `validation.json`, `source_receipts.json`, `temporal_checks.jsonl` và
  `provenance.json` là bằng chứng/hạn chế của lượt này.
- Gán lại trực tiếp bằng Codex trong cùng phiên, không đọc AI-A, nhưng đã
  thấy một phần B cũ trong lịch sử; không gọi là lượt mù mới. Khả năng truy
  cập nguồn khác lượt đầu, phải khai khi so sánh. Chưa đo lại AC1 hoặc dựng
  phiếu CMT từ B mới. Chưa commit hoặc push.

### Kiểm G2 theo yêu cầu CMT, 09/11/2026

Phạm vi: VBHN → chẩn đoán recall/M2 → datasheet → cỡ mẫu và đồng thuận.
Không thay split, ADR 0005, manifest, đề cương, nhãn người hoặc ngưỡng; không commit.
Dùng các báo cáo G2 trong `docs/reports/` và lệnh tái lập trong `scripts/check/`.
VBHN đã chạy lại: 96 cặp; 0 ca chọn sai được chứng minh, 1/2 khớp;
9 ca cần phân xử, 2 tín hiệu bãi bỏ cần người xem. 8 test VBHN qua; hash OK.
- Recall chạy lại hiện tại: 5.200/8.046 (64,6284%), không phải số lịch sử
  5.007. Sửa phép đo để báo thêm applicable 3.238/8.046 (40,2436%),
  thêm chế độ không ghi đè phiếu mẫu và kiểm độ sẵn sàng M2. Không sửa
  extractor theo suy đoán. M2 vẫn không chấm được: gold người hoàn tất 0.
  [Bằng chứng và phần dừng](../../reports/g2-recall-m2-20261109.md).
- Datasheet schema 2.0.0 đã khớp manifest: 769 main/246 lineage,
  859 silver/178 lineage (168 T2/T3 + 10 T5). Không sửa manifest.
- [Cỡ mẫu, power, toàn bộ đồng thuận](../../reports/g2-co-mau-dong-thuan-20261109.md):
  314 lineage AI sản xuất (168 + 128 + 18); verdict AC1 0,607519,
  p_neg 0,764045. 162 đạt được chấp nhận gồm 81 silver nhận hàng loạt
  và 81 mới có lời CMT tự báo đọc/duyệt. Không gọi 162 là người kiểm từng
  dòng; nếu áp yêu cầu 130 người xác nhận sau đọc thì mới chứng minh 81,
  thiếu 49. Giữ cả hai cách đếm, chờ CMT xử lý chênh lệch authority.
- Power có điều kiện với hiệu/phương sai test2: N=162 là 0,369007
  tại α=0,05; N=81 là 0,209652. Không phải power thực nghiệm bộ cuối.
- Kiểm: suite 721 passed (34,71 giây); paper_check 0 sai lệch, 3/3 đối
  chứng lỗi bị bắt; diff check sạch; thống kê chạy hai lần giống nhau.
  Sáu file bảo vệ và 79 đầu vào thống kê nguyên hash. Không commit.
- Còn dừng: gold mù/M2 cần người, ca VBHN và các ca nhãn mở cần
  người có thẩm quyền; chưa tuyên bố hoàn tất G2 hoặc tăng recall extractor.
