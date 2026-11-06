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
| X3 | So một generator mạnh hơn (không thuộc họ Claude, DeepSeek), trên ngữ cảnh đúng | vài USD | Làm cột kiểm độ bền (B7). Chỉ đổi cột chính nếu Accuracy tăng ≥ 0,05, KTC > 0 |
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
- [ ] X2: thiết kế thông báo bãi bỏ trong prompt, sau khi có X1.
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
- [ ] D0: bản nháp 7 chương và paper. Đã có nháp đủ, 0/437 số thiếu nguồn, chờ phản biện và Colab.

## Decisions

- 2026-11-05: Coi v1.0 và test 2 là vòng thử có khai báo. Kết luận chính dựa trên bộ test cuối mới.
- 2026-11-05: Không yêu cầu hệ đề xuất phải thắng. Mục tiêu là đo đúng.
- 2026-11-05 (CMT): giờ GPU không phải giới hạn; gán nhãn trong cuối tuần 07–08/11; luật sư tham gia; cho commit.
- 2026-11-05 (CMT): repo GitHub đang công khai, CMT biết và vẫn cho push lên `develop`. Claude tự commit và push `develop` sau mỗi việc đã kiểm. Quyết định E2 (giữ riêng tư đến khi kiểm quy định ẩn danh) coi như đổi; phải xem lại trước khi nộp hội nghị.
- 2026-11-05 (CMT): cân nhắc giao agent gán toàn bộ rồi chọn **người gán**. Agent chỉ hỗ trợ ở các khâu ghi trong mục "Ai làm gì", không tính vào nhãn chính. CMT muốn có bản nháp Chủ nhật 08/11 (D0).
- 2026-11-06 (CMT): **đổi quy trình gán nhãn.** Agent làm phần gán: AI-A, AI-B gán mù độc lập theo thẻ 4.0, đo AC1/p_neg AI–AI, `legal-adjudicator` đề xuất cho dòng lệch. CMT duyệt mọi dòng, có xem nhãn và lý do AI, rồi đồng ý hoặc sửa; nhãn CMT là nhãn cuối. Bỏ lịch hai người gán mù lô 0 và silver ngày 07–08/11. Thay quyết định 05/11 "chọn người gán" và các dòng "A và B gán độc lập", "người gán không thấy gợi ý AI" ở mục Quy tắc gán nhãn. Hệ quả phải ghi trong paper: không còn đồng thuận người–người cho bộ cuối; chỉ báo AI–AI và tỷ lệ CMT sửa nhãn AI; dòng vào test có tầng "AI gán, người xác nhận" (định nghĩa §6, sửa 06/11). Mặc định (CMT đổi được): luật sư chốt các dòng CMT ghi `[phân vân]`; gold mù giữ nguyên, phải xong trước khi CMT duyệt câu gold của mình (B6).
- Quyết định cũ còn hiệu lực: A2, A3, B2, B6, B7, B9, C2, C3, C4, C5, E1–E5 (MASTER_RESEARCH_GUIDE §13.3 tại `51f36c7`), và reranker cắt 05/11.

## Validation

### Tiếp quản gán nhãn silver đợt 2, 06/11/2026

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
