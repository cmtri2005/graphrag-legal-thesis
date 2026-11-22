# Kiểm định độc lập bộ dữ liệu ViLexTime 5.1.1 (22/11/2026)

Đối tượng: repo phát hành `../vilextime_uit` (bản 5.1.1) và các file nguồn trong repo khóa luận.
Vai trò: người phản biện, không mặc định tin quy trình nào.

**Phạm vi đã kiểm:**
- Chạy `scripts/check_dataset.py`, kiểm sha256 và tự đo bằng script.
- Đọc nhãn thô, biên bản hòa giải, phiếu đọc mù, file duyệt của CMT, nhật ký sự kiện của kho.

**Chưa kiểm:**
- Tôi **không** tự tra lại nội dung pháp lý của dòng nào.
- Tôi chưa chạy `check_dataset.py --corpus`.
- Tôi chưa đọc hết corpus. Chỉ xem mẫu và manifest.

---

## 1. Đánh giá tổng quan

**Kết luận: ĐẠT CÓ ĐIỀU KIỆN.**

Phần cấu trúc dữ liệu sạch. Tài liệu đi kèm cũng tốt. Điểm yếu nằm ở chỗ khác:
- Lớp kiểm tra bằng AI và tác giả **không tự bắt được lỗi kho nào**. Cả 6 lỗi đã biết đều do người đọc mù hoặc phép rà sót sửa đổi tìm ra.
- Còn **94/199 lineage chưa có người đọc mù**, gồm cả 43/43 lineage control.

| | |
|---|---|
| Tin được ngay | Cấu trúc, schema, hash, bộ chấm, tách dev và test, việc ghi nguồn gốc |
| Chưa tin được | Tỷ lệ lỗi của kho trên cả bộ. Độ tin của "tác giả duyệt mọi dòng". Đồng thuận về nội dung |
| Rủi ro lớn nhất | (1) 94 lineage chưa đọc mù. (2) Gold lấy từ kho, mà kho cũng là nguồn của hệ đề xuất. (3) Kết quả G4 chấm trên bản 2.0.0 nội bộ, chưa chấm lại trên 5.x |
| Làm ngay | Đổi tên trường `high_risk_lawyer_check`. Chấm lại G4 trên 5.1.1. Hoàn tất đợt đọc ngẫu nhiên 30 dòng |

## 2. Bộ dữ liệu và quy trình (tóm tắt)

Bộ có 722 dòng (câu hỏi × ngày) trên 199 lineage và 173 văn bản. Chỉ có tập test. Mỗi lineage có một câu hỏi, hỏi ở nhiều ngày.
Quy trình chi tiết nằm ở [quy-trinh-xay-dung-vilextime.md](quy-trinh-xay-dung-vilextime.md).

| Bước | Ai làm | Cách kiểm | Lỗ hổng |
|---|---|---|---|
| 1. Cào vbpl, dựng kho phiên bản | Script | Hash, `verify_pipeline.py`, `check_dataset.py` | Kho sót sửa đổi. 34.732/56.624 sự kiện bị từ chối, không áp vào kho (`data/derived/event_log.jsonl`) |
| 2. Viết câu hỏi | LLM (5 model) | `validate()` tự động, Q1–Q3 của AI | Không có người kiểm câu hỏi có tự nhiên và rõ nghĩa không |
| 3. Chọn đáp án ngắn | LLM hoặc người gán | Phải là span của lời văn | 8 đáp án bị cắt "…" phải sửa ở 5.0.0 |
| 4. Gán Q1–Q4 | AI-A (Claude), AI-B (Codex) | So hai AI với nhau | Đo trên tập đã lọc, nên chỉ số vô nghĩa (§5) |
| 5. Hòa giải | AI phân xử (11 lineage), tác giả (4) | — | AI phân xử cùng họ với AI-A |
| 6. Tác giả duyệt | CMT, đã thấy nhãn AI | Không có | Không mù. Chỉ có câu xác nhận chung (§3.3) |
| 7. Kiểm lại sau duyệt | AI phân xử | — | AI tự kiểm AI |
| 8. Đọc mù | 4 người đọc, 105 lineage | Đối chiếu kho sau khi mở đáp án | Mẫu không ngẫu nhiên. Người đọc tự chấm mình có khớp không |

Phễu chọn: 374 lineage ứng viên (silver 168, lo2 128, supp18 18, T1 60), giữ 199 (75 + 70 + 11 + 43).
Riêng nhóm repealed (T6) loại 133 lineage vì không rõ nội dung đã chuyển sang văn bản khác hay chưa (`docs/paper/nhap-paper-vilextime.md:132`).

## 3. Sáu phương diện

**3.1 Phương pháp luận.**
- Đơn vị phân tích rõ: một lineage. Định nghĩa vận hành có văn bản (`dataset_definition.md`).
- Gold được định nghĩa là "lời văn đúng theo kho", **không phải sự thật pháp lý đã kiểm độc lập**. Đây là đe dọa lớn nhất về giá trị cấu trúc.
- Kết quả theo nhóm chỉ đọc được ở control và two_versions. Nhóm multi_versions chỉ có 6 lineage. Nhóm repealed có 23 lineage, lại chỉ gồm những ca bãi bỏ rõ.

**3.2 Toàn vẹn cấu trúc.** Phần này tốt.
- 722 id đều duy nhất. Không có câu hỏi trùng, kể cả gần trùng (difflib, ngưỡng 0,8).
- Hash đạt. Không có `as_of` nào sau ngày chụp kho.
- Mọi span đáp án nằm trong context sau khi chuẩn hóa. 55 đáp án ghép nhiều span bằng "…", và bộ chấm xử lý đúng.
- 127/127 lineage two_versions có đáp án khác nhau giữa hai phiên bản.

**3.3 Gán nhãn.** Phần này yếu nhất.
- Không có ai gán nhãn người một cách độc lập trên toàn bộ.
- Duyệt silver và lo2 (296 dòng): câu "Đã xem và mình xác nhận", thời gian từng dòng không đo (`data/review/ai_research/2026-11-10_cmt_confirmed/cmt_confirmed.json`).
- Duyệt T1 (60 dòng): câu "ok bạn nhé" (`2026-11-11_t1_labels/cmt_confirmed_t1.json`).
- Lượt gán lại AI-B cho T1 đã nhìn thấy nhãn AI-B của lượt trước (`2026-11-11_t1_labels/README.txt`), nên không còn mù.

**3.4 LLM và agent.**
- Cùng họ model xuất hiện ở bốn khâu: viết câu hỏi, gán nhãn, phân xử, kiểm lại.
- Trong đợt gán lại high-risk, có ít nhất 3/23 dòng repealed mà *cả hai* AI cùng nói "Còn", trong khi đáp án đúng là đã hết hiệu lực (`annotation/high_risk_augmentation.jsonl`: L3B2610, L973721, LDF0DAA). Đây là bằng chứng có sai số tương quan giữa hai AI.
- Model không được ghi lại ở 288 câu hỏi (gpt-6.1-sol, chỉ do tác giả kể lại) và ở 70 lineage nhãn lo2.

**3.5 Sai lệch và rò rỉ.**
- Không rò rỉ giữa dev và test. Dev có 81 lineage và 73 văn bản; trùng với bộ phát hành 0 lineage, 0 văn bản.
- Câu hỏi không chứa năm hay số hiệu văn bản (0/199).
- Câu hỏi bám chữ của điều khoản: trung vị 36% token của đáp án nằm sẵn trong câu hỏi, p90 là 64%.
- Sai lệch do chọn mẫu: chỉ giữ những ca mà AI và tác giả xử lý được.

**3.6 Tái lập.**
- Có datasheet, schema, prompt nguyên văn, nhãn thô và changelog.
- Thiếu danh sách 175 lineage bị loại kèm mã lý do. Thiếu DOI.
- Một phần đầu vào nằm ngoài repo (`~/vilextime_loc/`). Chúng đã được sao vào `data/vilextime_final/inputs/` kèm sha256.

## 4. Danh sách phát hiện

| Mã | Vấn đề | Mức độ | Bằng chứng | Tác động | Tin cậy | Hành động |
|---|---|---|---|---|---|---|
| F01 | Lớp AI + tác giả không bắt được lỗi kho | **CRITICAL** | 6/6 lỗi đã biết do đọc mù (3) hoặc rà sót sửa đổi (3) tìm ra; cả 6 đã qua AI + tác giả trước đó | Không được coi bước gán AI là bằng chứng gold đúng. Độ đúng của 94 lineage chưa đọc là ẩn số | Cao | Đọc mù phần còn lại (P1-1) |
| F02 | 94 lineage chưa đọc mù, gồm 43/43 control | HIGH | `blind_gold` rỗng: control 0/43, two_versions 50/127, multi 1/6 | Chưa ước lượng được lỗi cả bộ. 105 lineage đã đọc là mẫu thiên về ca khó | Cao | random30 rồi đọc nốt 64 |
| F03 | Gold vòng lặp với kho | HIGH | `versions.jsonl.xz` mang `effective_intervals`, chính là khoảng định nghĩa gold. Bộ chấm với oracle đạt 1,0 | Hệ lọc theo khoảng của kho lấy được nửa thời gian của đáp án. Lợi thế của hệ đề xuất một phần do cách dựng | Cao | Baseline có và không có khoảng; viết rõ trong paper |
| F04 | G4 chưa chấm lại trên 5.x | HIGH | G4 chạy 12–13/11. Sau đó có sửa đáp án T1 (19/11), sửa kho 5 lineage và hoàn thiện 8 đáp án (21/11). Trong `runs/` tôi không thấy lần chấm lại nào | Số trong khóa luận và paper khác bộ đã công bố | Trung bình (chỉ xem danh sách thư mục) | Chấm lại dự đoán đã lưu, không sinh lại |
| F05 | Tên trường gây hiểu nhầm `review.high_risk_lawyer_check` | HIGH | Giá trị thật là `method: ai_proposed_cmt_verified`. Trường không có trong `SCHEMA.md` | Người đọc tưởng có luật sư kiểm | Cao | Đổi tên và ghi vào schema |
| F06 | `agrees_with_store` do người đọc tự chấm sau khi thấy kho; với luật sư chỉ xét hiệu lực | HIGH | `annotation/README.md`. Số 137/141 (97,2%) gộp hai cách đo | Thiên về "khớp". Đồng thuận *nội dung* chưa đo độc lập | Cao | Người thứ ba chấm nội dung theo luật viết trước |
| F07 | Tác giả duyệt không mù và không có vết từng dòng | HIGH | §3.3 | "Tác giả duyệt mọi lineage" không có giá trị như bằng chứng | Cao | Paper mô tả đúng sự thật |
| F08 | Đồng thuận AI–AI đo trên tập đã lọc | MEDIUM | AC1 0,92–0,995 nhưng κ ≈ 0; mọi verdict cuối đều là `dat` | AC1 vô nghĩa nếu trích | Cao | Đo trên 374 ứng viên, hoặc bỏ |
| F09 | Không công bố phễu loại | MEDIUM | 374 → 199; bản công khai chỉ giữ lineage đã nhận | Người ngoài không kiểm được sai lệch chọn mẫu | Cao | Công bố id bị loại kèm mã lý do |
| F10 | Nhóm repealed chỉ gồm ca bãi bỏ rõ | MEDIUM | 133 lineage loại vì nghi chuyển chỗ | Không khái quát cho bãi bỏ nói chung | Cao | Ghi giới hạn; chấm repealed theo kiểu thăm dò |
| F11 | Corpus giữ khoảng sai ở 6 version | MEDIUM | `corpus/README.md`; 18 dòng mang cờ `store_corrected` | Hệ dùng khoảng của corpus sai ở các dòng này dù làm đúng thiết kế | Cao | Phát hành file khoảng đã sửa đè lên corpus |
| F12 | Thiếu vết model | MEDIUM | 288 câu hỏi chỉ do tác giả kể lại; 70 lineage lo2 "model not recorded" | Giảm khả năng tái lập | Cao | Ghi là giới hạn |
| F13 | Câu hỏi do LLM viết, cùng họ với hệ được đo | MEDIUM | Datasheet | Hệ cùng họ có thể được lợi | Trung bình | Báo kết quả theo `question_source` |
| F14 | Cỡ mẫu nhỏ ở multi_versions và repealed | MEDIUM | 6 và 23 lineage | Khoảng tin cậy rất rộng | Cao | Chỉ báo mô tả |
| F15 | 9 lineage có toàn bộ span gold của một phiên bản nằm trong lời văn phiên bản khác | LOW | Tôi tự đo: 9/133 lineage có từ 2 phiên bản trở lên | `wrong_version` có thể đếm thiếu | Trung bình | Liệt kê trong tài liệu bộ chấm |
| F16 | Chưa có DOI, chưa ghi nhận đồng ý của luật sư | INFO | Datasheet | — | — | Làm khi nộp |

## 5. Định lượng

| Chỉ số | Kết quả | Mẫu số | Ghi chú |
|---|---|---|---|
| Lỗi kho trên lineage đã đọc mù | 3/105 = 2,9% (Wilson 95%: 1,0–8,1%) | Lineage, mẫu không ngẫu nhiên | Không suy cho cả bộ |
| Tổng lỗi kho đã biết | 6/199 lineage; 19 dòng bị ảnh hưởng (18 `store_corrected` + 1) | Lineage | Là cận dưới |
| Đọc mù khớp kho | 137/141 = 97,2% | Lượt đọc, 105 lineage | Tự chấm; với luật sư chỉ xét hiệu lực |
| Luật sư với người đọc đồng tác giả | 29/30, κ 0,932 | Chỉ hiệu lực | Prevalence cao, AC1 đáng tin hơn κ |
| Bộ chấm so với người chấm | 96/100, κ 0,910 | 100 câu G4 | Chưa đo được `wrong_version` |
| AI-A so với AI-B | AC1 0,92–0,995, κ −0,03–0 | 199 lineage đã lọc | Vô nghĩa vì đã lọc |
| Trùng câu hỏi | 0 trùng hẳn, 0 gần trùng | 199 câu | difflib 0,8 |
| Rò rỉ dev sang test | 0 lineage, 0 văn bản | Dev 81 lineage, 73 văn bản | — |
| Token đáp án có trong câu hỏi | Trung vị 36%, p90 64% | 199 lineage | Thiên về truy xuất theo từ |
| Sự kiện sửa đổi áp được vào kho | 21.892/56.624 = 38,7% | Câu lệnh đã trích | Phần còn lại bị từ chối có lý do, kho có thể sót |

## 6. Riêng phần LLM và agent

- **Lỗi có thể lan rộng:** kho sót sửa đổi mà vbpl không ghi. Hai AI đọc cùng phiếu và cùng đoạn trích nên cùng sót.
- **Tự xác nhận:** bước 7 dùng AI phân xử để kiểm những dòng tác giả đánh dấu không chắc.
- **Prompt:** lời dặn bản v2 cho bộ test 2 không qua cổng hiệu chuẩn (AC1 0,530, `nhap-paper-vilextime.md:156-159`). Guideline 4.0 chỉ có lô 0, và lô 0 so AI với AI cùng model, không có người (`2026-11-06_lo0/metrics.json`).
- **Cần bổ sung:** người đọc mù trên mẫu ngẫu nhiên, và người thứ ba chấm nội dung.

## 7. Nguyên nhân gốc

1. **Đã xác nhận.** QA được thiết kế để kiểm *nhãn*, không kiểm *kho*. Gold = kho, nên lỗi kho chỉ lộ ra khi có người đọc từ nguồn gốc mà không nhìn kho.
2. **Đã xác nhận.** Người duy nhất là con người trong vòng lặp (CMT) đã thấy mọi đáp án, nên không thể là kiểm độc lập.
3. **Giả thuyết.** Phễu lọc ưu tiên ca dễ (AI đồng thuận, bãi bỏ rõ). Vì vậy tỷ lệ lỗi trên bộ đã lọc có thể thấp hơn thực tế, và độ khó bị đánh giá thấp.

## 8. Kế hoạch khắc phục

| Mức | Việc | Công sức | Tiêu chí nghiệm thu |
|---|---|---|---|
| P0 | Đổi `high_risk_lawyer_check` thành `high_risk_ai_author_check`, thêm vào SCHEMA, bản 6.0.0 | 0,5 giờ | `grep lawyer_check` không còn trong data |
| P0 | Chấm lại dự đoán G4 trên 5.1.1 bằng `evaluate.py`, báo cả hai bản | 1–2 giờ | Có file chấm lại kèm hash; mọi số trích từ file đó |
| P1-1 | Hoàn tất random30 (2 người), rồi đọc nốt 64 lineage còn lại | 2 người × 1–2 ngày | Tỷ lệ lỗi kho trên toàn bộ 199. Mọi lệch phân xử bằng văn bản chính thức |
| P1-2 | Đồng thuận nội dung do người thứ ba chấm theo luật viết trước | 0,5 ngày | Báo raw, κ, AC1 riêng cho hiệu lực và nội dung |
| P1-3 | Công bố phễu 374 → 199 theo nhóm và mã lý do | 2 giờ | `excluded_lineages.jsonl` trong bản phát hành |
| P1-4 | Baseline có và không có khoảng hiệu lực; paper viết gold là "theo kho tại ngày chụp" | 0,5 ngày | Bảng ablation trong paper |
| P2 | File khoảng đã sửa đè lên corpus; báo theo `question_source`; người kiểm 40 câu hỏi về độ rõ nghĩa | 1 ngày | File trong repo; bảng theo nguồn |
| P3 | DOI, mở rộng multi_versions, luật sư kiểm mẫu lớn hơn | Dài hạn | — |

Lưu ý về đọc mù: nếu random30 không thấy lỗi nào, cận trên 95% là 11,4%. Suy cho cả bộ thì còn khoảng ≤ 5,4%. Con số này vẫn rộng. Đọc nốt 94 lineage rẻ hơn tranh luận thống kê.

## 9. Mức sẵn sàng khoa học

- **Tin được:** cấu trúc, bộ chấm, việc tách tập, 105 lineage đã đọc mù (lỗi đã sửa).
- **Chưa tin được:** 94 lineage còn lại, nhất là control. Mọi khẳng định kiểu "người đã kiểm" hay "luật sư kiểm".
- **Kết luận được phép:** hệ X khớp hay không khớp với lời văn hiệu lực theo kho tại ngày chụp, đo trên 199 lineage có chọn lọc.
- **Chưa đủ cơ sở:** độ đúng pháp lý của cả bộ; nhãn AI ngang nhãn người; kết luận cho multi_versions và cho bãi bỏ nói chung.
- **Điều kiện tối thiểu:** xong P0, P1-1, P1-3.

## 10. Mười câu reviewer sẽ hỏi

| # | Câu hỏi | Vì sao hỏi | Bằng chứng cần đưa |
|---|---|---|---|
| 1 | Gold do ai kiểm độc lập trên *toàn bộ*? | Gold = kho tự dựng | Đọc mù đủ 199, hoặc mẫu ngẫu nhiên kèm CI |
| 2 | Tỷ lệ lỗi kho là bao nhiêu, mẫu số là gì? | 105 lineage không ngẫu nhiên | Kết quả random30 kèm Wilson CI |
| 3 | AC1 0,99 có ý nghĩa gì khi κ ≈ 0? | Đo sau khi lọc | Đồng thuận trên 374 ứng viên |
| 4 | Hệ đề xuất thắng vì đọc được khoảng của chính kho tạo gold? | Vòng lặp | Ablation P1-4 |
| 5 | Lineage nào bị loại, vì sao? | Sai lệch chọn | Phễu P1-3 |
| 6 | Bao nhiêu ca bãi bỏ thật bị loại? | 133 loại so với 23 giữ | Số phễu T6 kèm giới hạn |
| 7 | Câu hỏi LLM viết có tự nhiên không? | Không có người kiểm | Người kiểm 40 câu |
| 8 | Hệ dùng Claude hay GPT có được lợi không? | Cùng họ viết câu hỏi | Bảng theo `question_source` |
| 9 | "Tác giả duyệt" gồm những gì? | Câu xác nhận chung | Mô tả đúng: không mù, không đo thời gian |
| 10 | Kết quả có giữ được khi kho đã sửa? | Gold đổi sau G4 | G4 chấm lại trên 5.1.1 |

## 11. Khuyến nghị cuối

- **Tiếp tục dùng bộ này, không cần dừng.** Không phải dựng lại.
- Sửa trước: F05 (đổi tên trường) và F04 (chấm lại G4).
- Làm lại một phần: đọc mù 94 lineage còn lại, và chấm nội dung bằng người thứ ba.
- **Lộ trình ngắn nhất:** P0 (nửa ngày), rồi random30, rồi 64 lineage còn lại, rồi công bố phễu, rồi viết lại phần QA trong paper cho đúng thực tế. Tổng khoảng 3–4 ngày công.
