# Research audit ViLexTime và Temporal-Aware KG-RAG, 13/11/2026

Phiên audit chỉ đọc, làm theo yêu cầu của CMT sau khi G4 chạy xong. Không sửa code, dữ liệu, nhãn, cấu hình, ADR, plan hay bản thảo. Không gọi API trả phí, không chạy lại test.

Đây là báo cáo của một phiên AI trong dự án, không phải phản biện ngoài. Các số [HN] đã được tính lại bằng `scripts/eval/posthoc_g4.py` (`runs/posthoc_g4_20261113/attribution.json`) và qua `evidence-gate` 13/11 (việc 6.6 của REFACTOR_PLAN; tái chạy trùng từng byte). Số trong báo cáo này đã thay bằng số của file đó.

## Cách đọc nhãn bằng chứng

| Nhãn | Nghĩa |
|---|---|
| **[XM]** | Đã xác minh từ artifact trong repo |
| **[HN]** | Phân tích hậu nghiệm: tự tính trong phiên này từ `runs/final_g4_20261112/{r1,r2}/test/*.jsonl` bằng hàm `correct`, `load_rows`, `distractors` của `scripts/eval/score_vilextime.py`; bootstrap theo lineage, B = 10.000. Bản lưu: `runs/posthoc_g4_20261113/attribution.json`, đã qua `evidence-gate` 13/11. Vẫn là thăm dò hậu nghiệm |
| **[SL]** | Suy luận từ bằng chứng |
| **[GT]** | Giả thuyết cần kiểm |

Mọi số [HN] là thăm dò, tính sau khi đã thấy kết quả test.

---

## 1. Chẩn đoán tổng thể

**Kết luận ngắn:** lợi ích đo được đến từ kho phiên bản dựng offline và bộ lọc theo khoảng hiệu lực. Phần đồ thị khai thác lúc trả lời chưa cho thấy tác dụng. Thước đo chưa độc lập với hệ trên chính bộ test cuối.

### Điểm mạnh [XM]

- Kỷ luật khai báo trước tốt: ADR 0006 Accepted trước khi chạy, P khóa trên dev, chạy hai lần, Holm, bootstrap theo lineage, hash đầy đủ (`docs/decisions/0006-ke-hoach-phan-tich-bo-test-cuoi.md`, `runs/final_g4_20261112/`).
- Mọi hệ dùng chung một đường ống, một prompt, một `k` (`src/vilexgraph/framework/systems.py`).
- Có đủ hai điều kiện cấp sẵn căn cứ: `oracle` 0,956 và `oracle_now` 0,456 (`runs/final_g4_20261112/r1/results.md`).
- Tài liệu tự khai giới hạn rất thẳng (ADR 0006 §3, §11).

### Ba rủi ro lớn nhất

**Rủi ro 1. Tên và claim "đồ thị" vượt quá cơ chế đã đo.**

- `proposed2 − b7plus` trên `all`: +0,013 [−0,009; +0,035] ở lần 1, +0,016 [−0,006; +0,038] ở lần 2 **[HN]**.
- `proposed2 − b7pp`: +0,006 [−0,016; +0,028] ở lần 1, 0,000 [−0,016; +0,016] ở lần 2 **[HN]**.
- F1–F3 "ủng hộ" (P − `b4` = +0,343) vì thế cũng sẽ đúng nếu thay P bằng `b7plus` **[SL]**.
- `b7plus` chỉ là một vị từ SQL trên bảng khoảng hiệu lực (`src/vilexgraph/framework/temporal.py`).
- "Đồ thị trực tuyến" của `proposed2` là một phép nối SQL một bước lên các nút cha (`graphx.py`, `rel_up`). Không dùng Neo4j lúc truy vấn, không đi nhiều bước.
- Verifier không tác động do cách dựng; chính lời chú đầu `verify.py` ghi như vậy.

**Rủi ro 2. Vòng tự chấm chưa bị phá trên bộ test cuối.**

- Gold, bộ lọc và TVER cùng lấy cửa sổ từ một đồ thị (ADR 0006 §3 tự ghi).
- Mẫu gold mù 120 dòng chỉ có **24 lineage** thuộc 199 lineage bộ cuối. Đợt 2 (30 dòng) trùng 0 và do AI gán **[HN, đếm từ `data/review/gold_sample.tsv`, `data/review/gold_dot2/gold_sample.tsv`, `data/vilextime_final/lineages_199.txt`]**.
- "119/120 khớp" là sau cột `dong_y` do AI đề xuất, CMT xác nhận **[XM, `data/review/gold_A.reveal.tsv`]**:
  - G011: người ghi "còn", đồ thị ghi "bãi bỏ", vẫn tính khớp. Ghi chú: "A ghi còn sai… Đồ thị đúng. AI-đề xuất, CMT xác nhận".
  - G002: người ghi "06 tháng đến 12 tháng", đồ thị ghi "03 tháng đến 12 tháng", `dong_y = co`, ô lý do trống. Cần xem lại.
  - Khớp thô trạng thái hiệu lực trước phân xử: 148/150 phiếu.
- Nhãn bộ cuối là AI gán, một tác giả duyệt, AC1 AI–AI 0,608, dưới ngưỡng 0,80 (ADR 0006 §1). 168 nhãn silver được chấp nhận hàng loạt (master plan, mục Validation 08/11).

**Rủi ro 3. Bước lớn nhất của thang chưa được tách, và baseline phẳng chưa có cùng thông tin.**

- `b7 → b7plus` đổi cùng lúc hai thứ: lớp văn bản (nguyên bản `asis` sang lời văn hợp nhất `version`) và bộ lọc (ngày văn bản sang khoảng phiên bản).
- Nấc tách là `b7v`. ADR 0006 §2 khai thang `b2ctx → b7 → b7v → b7plus → b7pp`, nhưng `b7v` **không chạy** trên bộ cuối: `runs/final_g4_20261112/retrieval/` chỉ có `b2ctx`, `b7`, `b7plus`, `b7pp` **[XM]**.
- Toàn bộ lợi ích của bước này nằm ở dòng mà đáp án là phiên bản thứ hai trở đi **[HN]**:

  | Dòng có đáp án | `b7` đúng (lần 1) | `b7plus` đúng (lần 1) | Hiệu lần 1 | Hiệu lần 2 |
  |---|---:|---:|---|---|
  | Gold là phiên bản 1 (156 dòng) | 100 | 102 | +0,013 [−0,013; +0,038] | −0,013 [−0,032; 0,000] |
  | Gold là phiên bản ≥ 2 (139 dòng) | 53 | 103 | +0,360 [+0,269; +0,450] | +0,324 [+0,235; +0,413] |

  Nguồn: `attribution.json`, `pairs` lát `gold_v1`, `gold_v2plus`. Ở gold bản 1, hiệu đổi dấu giữa hai lần, KTC chứa 0 cả hai lần.

- Lợi ích chủ yếu không đến từ việc tìm thấy nhiều hơn, mà từ việc ngữ cảnh sạch hơn **[HN]**:

  | Hệ | Gold trong top 20 (trên 295) | Đúng khi đã có gold |
  |---|---:|---:|
  | `b7` | 235 | 151 (64%) |
  | `b7plus` | 243 | 202 (83%) |

- Prompt không cho model thấy ngày hiệu lực từng đoạn; mỗi đoạn chỉ có tên văn bản và đường dẫn Điều/Khoản **[XM, `runs/final_g4_20261112/r1/prompts/b4.jsonl`]**. Chưa có baseline "siêu dữ liệu ngày trong prompt".

### Mâu thuẫn giữa các nguồn [XM]

| Chỗ | Nguồn cũ | Nguồn mới hơn, áp dụng |
|---|---|---|
| Ai gán nhãn bộ cuối | `docs/paper/nhap-paper-vilextime.md`, chương 4 và 6 (05/11): "bộ test cuối do người kiểm" | ADR 0006 §1 và quyết định 06/11: AI gán, CMT duyệt |
| Phạm vi gold mù đợt 1 | ADR 0006 §7: "người, T2/T3" | `data/review/gold_sample.tsv`: 6 tầng × 20, gồm T1 và T6. Cần đối soát |
| Sổ chạy | `runs/README.md` quy tắc 2: mỗi lần chạy test có một dòng | Chưa có dòng nào cho G4 |
| Trạng thái release | `data/vilextime_final/README.md`, `manifest.json`: "NHÁP, chưa hệ nào chạy" | G4 đã chạy 13/11 |
| Nhãn bảng | `r1/results.md`: "318 dòng (T1, T2, T3, T6)" | `all` không gồm T1 |
| Thang truy xuất | ADR 0006 §2: 5 nấc | Chạy 4 nấc |

---

## 2. Bảng claim–evidence

| Claim | Bằng chứng và đường dẫn | Giới hạn | Trạng thái | Còn thiếu |
|---|---|---|---|---|
| RAG phẳng trích nhiều điều khoản sai phiên bản (RQ1, vế RAG) | `b4`: TVER 0,544, sai phiên bản 0,291; `r1/results.md` | TVER dùng cửa sổ đồ thị | Có bằng chứng, mức "nhất quán với đồ thị" | TVER theo người (ADR 0006 §4, chưa làm) |
| LLM không truy xuất sai phiên bản ở mức nào (RQ1, vế LLM) | `b1` đúng 2/318; 70% câu đổi giữa hai lần (`compare_runs.json`) | Accuracy đòi chép đúng lời văn; LLM không truy xuất gần như không thể đạt | **Chưa đo được** | Người hoặc giám khảo hiệu chuẩn chấm mẫu `b1`; 2–3 model như plan §6 |
| Lọc theo ngày văn bản giúp (F4) | +0,078 [0,049; 0,110]; `r1/confirm.json`; lặp ở v1.0 và test 2 | Như trên | Có bằng chứng, ba bộ | — |
| Kho phiên bản + lọc khoảng giúp (F5 = F6) | +0,115 [0,076; 0,156]; Accuracy +0,167 | Gộp hai thay đổi; test 2 không đủ bằng chứng | Có bằng chứng cho gói gộp | `b7v` trên bộ cuối |
| Hệ đề xuất hơn RAG phẳng và "GraphRAG phi thời gian" (F1, F2) | +0,343; +0,355 | `b5` là mở rộng một bước tự xây, không phải GraphRAG (ADR 0006 §11) | Đúng về số, **sai về quy kết** nếu gán cho đồ thị | So P với `b7plus` có KTC |
| Lan truyền từ nút cha có tác dụng | `t6_ancestor` 9 dòng: `b7plus` 0, `b7pp` 2, `proposed2` 3 ở lần 1; 1, 3, 3 ở lần 2 **[HN]** | n = 9; hai lần khác nhau | Thăm dò, chưa đủ | Thêm dòng T6 nút cha |
| Hệ nhận ra điều khoản đã bãi bỏ (F7) | +0,087 [0; 0,217], p = 0,26 | 23 dòng | **Không đủ bằng chứng** | — |
| Đọc sai văn bản hiện hành có giá lớn | `oracle` 0,956 so với `oracle_now` 0,456 | Một generator | Có bằng chứng | — |
| Gold đúng với luật | Gold mù 119/120 (ADR 0006 §7) | Sau phân xử AI; phủ 24/199 lineage bộ cuối | **Cần thu hẹp** | Gold mù người trên bộ cuối |
| Hệ không làm hại câu không có yếu tố thời gian | `t1_no_harm` trong `r1/confirm.json` | Đáp án ngắn T1 hỏng: `oracle` T1 0,047 | **Không dùng được** | Amendment sửa đáp án ngắn T1 |
| Verifier (L5) giảm lỗi | — | Không tác động do cách dựng (`verify.py`); X4 trên dev: `b7` 0 cờ | Không có bằng chứng | Chỉ báo như lưới an toàn |

---

## 3. Bổ sung ưu tiên

### P0: cần để kết luận đáng tin

**P0-1. Báo trực tiếp phần của đồ thị trực tuyến.**

- Khoảng trống: họ F không có phép so P với `b7plus` trên `all`. F1, F2 so với `b4`, `b5` nên không tách được.
- Củng cố: RQ3.
- Việc nhỏ nhất: một script đọc dự đoán có sẵn, tính `proposed2 − b7plus`, `proposed2 − b7pp`, `b7pp − b7plus` ở cả hai lần, có KTC theo lineage.
- Diễn giải:
  - KTC nằm trong ±0,035: viết "không thấy lợi ích lớn hơn 3,5 điểm"; không viết "bằng nhau".
  - KTC loại 0 về phía dương ở cả hai lần: mới được nói đồ thị trực tuyến có tác dụng.
- Chi phí: 0 API, 0 giờ người. Không đụng protocol; ghi nhãn thăm dò hậu nghiệm.

**P0-2. Chạy `b7v` trên bộ cuối.**

- Khoảng trống: ADR 0006 §2 khai thang 5 nấc, chỉ chạy 4.
- Củng cố: RQ3, tách "có lời văn hợp nhất" khỏi "lọc theo khoảng".
- Việc nhỏ nhất: chỉ truy xuất từ vựng, k = 20, tất định, không gọi model. Báo `b7v − b7` và `b7plus − b7v` trên TV-R@1.
- Diễn giải:
  - `b7v ≈ b7` và `b7plus − b7v` lớn: lợi ích là bộ lọc khoảng.
  - `b7v > b7`: lời văn hợp nhất tự nó đã giúp.
  - Tham chiếu v1.0: −0,019 và +0,066 (`runs/README.md`, 29/10).
- Chi phí: khoảng 30 phút máy. Đây là hoàn tất việc đã khai, nhưng chạy sau khi đã thấy kết quả, phải ghi rõ.

**P0-3. Phá vòng tự chấm trên chính bộ cuối.**

- Khoảng trống: gold mù phủ 24/199 lineage. ADR 0006 §7 hứa "báo song song F1–F6 trên phần gold mù", chưa thấy trong `confirm.json`.
- Củng cố: mọi claim dựa trên F3–F6.
- Việc nhỏ nhất: rút phân tầng 60–80 dòng từ 156 lineage, ưu tiên đủ 23 T6. Một người chưa thấy đáp án đồ thị đọc văn bản gốc.
- Báo tỷ lệ khớp **thô trước phân xử** và sau phân xử, tách riêng. Xem lại G002.
- Diễn giải:
  - Từ 95% trở lên: F3–F6 được nói là đúng với luật trong phạm vi mẫu.
  - Dưới 95%: F3–F6 chỉ được gọi là "nhất quán với đồ thị".
- Chi phí: khoảng 10–13 giờ người, cần người hiểu luật. Không đổi protocol.

**P0-4. Đưa dao động generator vào cách đọc số.**

- Bằng chứng **[HN]**:

  | So sánh, `all` | Lần 1 | Lần 2 |
  |---|---|---|
  | `b5 − b4` | −0,013 [−0,025; −0,003] | +0,016 [+0,003; +0,031] |
  | `b6 − b4` | +0,016 [−0,003; +0,037] | +0,028 [+0,009; +0,050] |
  | `b4` số câu đúng | 103 | 94 |

  Hai KTC của `b5 − b4` đều loại 0 và ngược dấu.
- Hệ quả: KTC bootstrap chỉ chứa sai số chọn mẫu câu hỏi. Mọi hiệu dưới khoảng 0,03 trong bảng mô tả chưa phân biệt được với nhiễu API.
- Việc nhỏ nhất: báo mọi hiệu ghép cặp ở cả hai lần; áp quy tắc §5b cho cả bảng mô tả, không chỉ F1–F7.
- Chi phí: 0.

### P1: tăng đáng kể sức thuyết phục

**P1-5. Baseline thời gian mạnh, không truy vấn đồ thị.**

- Nghi vấn cụ thể: nếu RAG phẳng được đọc cùng kho phiên bản và thấy ngày hiệu lực, nó có tự chọn đúng không?
- Hai cấu hình mới:
  - (a) lớp phiên bản, không lọc;
  - (b) như (a), mỗi đoạn in thêm "hiệu lực từ … đến …".
- Diễn giải:
  - (b) gần `b7plus`: đóng góp là kho phiên bản, không phải bộ lọc.
  - (b) kém rõ: "lọc cứng trước khi xếp hạng" có giá trị riêng.
- Chi phí: ít code, khoảng 1 USD. Đây là cấu hình mới: chọn trên dev, báo trên bộ cuối với nhãn thăm dò.

**P1-6. Đo RQ1 vế LLM và hiệu chuẩn thước Accuracy.**

- Khoảng trống: Accuracy là phép khớp chuỗi (`contains` trong `score_vilextime.py`). `b1` gần như luôn bằng 0 vì thước, không vì sai phiên bản.
- Việc nhỏ nhất: 100 câu rút từ đầu ra có sẵn của `b1`, `b4`, `proposed2`. Người chấm đúng, sai, hoặc sai phiên bản. So với scorer.
- Chi phí: khoảng 6–8 giờ người. Không gọi API.

**P1-7. Giải thích T6.**

- Số trên `t6_unanswerable`, 23 dòng, lần 1 **[HN]**:

  | Hệ | Đúng | Số lần nói "hết hiệu lực" | Trong đó sai (dòng có đáp án) |
  |---|---:|---:|---:|
  | `b2ctx` | 7 | 36 | 29 |
  | `b4` | 3 | 21 | 18 |
  | `b7` | 2 | 7 | 5 |
  | `b7plus` | 3 | 7 | 4 |
  | `b7pp` | 5 | 9 | 4 |
  | `proposed2` | 7 | 11 | 4 |
  | `oracle` | 22 | 23 | 1 |

- `b2ctx` đúng bằng `proposed2` nhưng nhờ nói "hết hiệu lực" bừa. Accuracy riêng trên lát này không đủ; phải kèm precision.
- Việc nhỏ nhất: báo precision và recall của khẳng định bãi bỏ (đã khai ở ADR 0006 §4), kèm cột "lệnh bãi bỏ có trong prompt hay không" như đã làm trên dev.
- Chi phí: 0.

### P2: nếu còn nguồn lực

**P2-8. Sửa T1 và báo phân tầng.**

- Amendment sửa đáp án ngắn T1 rồi chấm lại, ghi rõ đã thấy kết quả.
- Phân tầng theo người viết câu hỏi, lần 1 **[HN]**:

  | Người viết câu hỏi | Dòng | `b4` | `b7` | `b7plus` | `proposed2` | `oracle` |
  |---|---:|---:|---:|---:|---:|---:|
  | Codex | 144 | 0,250 | 0,375 | 0,479 | 0,507 | 0,910 |
  | Claude | 138 | 0,391 | 0,572 | 0,775 | 0,775 | 0,993 |
  | DeepSeek | 36 | 0,361 | 0,611 | 0,889 | 0,889 | 1,000 |

  Độ khó phụ thuộc mạnh vào quy trình viết. Chưa tách được khỏi cổng trùng chữ và tỷ lệ T6 của từng lô.
- Miền **[HN]**: 220/318 dòng thuộc `khac`, ngoài bốn miền đề cương nêu; doanh nghiệp–đầu tư 43, giao thông 41, thuế 14.
- Loại văn bản **[HN]**: Nghị định 95, Thông tư 57, Luật 3, Thông tư liên tịch 1 lineage.
- Bootstrap theo văn bản làm kiểm độ nhạy: 156 lineage nằm trong 132 văn bản, 41 lineage chung văn bản với lineage khác.

---

## 4. Gói thực nghiệm tối thiểu

| Thứ tự | Việc | Dùng gì | Xong khi |
|---|---|---|---|
| 1 | Bảng quy kết từ dự đoán có sẵn (P0-1, P0-4, P1-7, phân tầng) | `runs/final_g4_20261112/r1`, `r2` | Một script, một file JSON trong `runs/`, gate đối soát, dòng mới trong `runs/README.md` |
| 2 | `b7v` chỉ truy xuất (P0-2) | Bộ cuối, không API | Có TV-R@1 và hai hiệu kề nhau kèm KTC |
| 3 | Gold mù người trên bộ cuối (P0-3) | 60–80 dòng | Có tỷ lệ khớp thô, Wilson, F1–F6 trên phần này |
| 4 | Người chấm 100 câu (P1-6) | Đầu ra có sẵn | Có tỷ lệ sai phiên bản của `b1`, độ khớp scorer–người |
| 5 | Hai baseline mới (P1-5) | Dev trước, rồi bộ cuối | Có amendment ghi "thăm dò, sau khi đã thấy test" |
| 6 | Amendment T1 | Bộ cuối | `oracle` T1 trở về mức hợp lý, rồi mới đọc `t1_no_harm` |

Việc 1 và 2 không tốn tiền, không cần người, làm trong một ngày. Việc 3 quyết định mức tin được của mọi số còn lại.

**Master plan có đang khắc phục các rủi ro này không?**

| Rủi ro | Việc trong plan | Đánh giá |
|---|---|---|
| Đồ thị trực tuyến không có tác dụng | Hướng A, C5 (thu luận điểm về hai nấc) | Đúng hướng. Thiếu phép so P với `b7plus` |
| Vòng tự chấm | Gold mù B6, TVER theo người, H3 | H3 đang "Chặn"; TVER theo người chưa làm; gold mù chưa phủ bộ cuối |
| Nhãn | N1 (luật sư kiểm 30 dòng `dat`) | Chưa làm; quyết định 11/11 bỏ người kiểm mẫu |
| Gộp hai thay đổi ở `b7 → b7plus` | `b7v` trong thang | Bị rơi ở G4 |
| Dao động API | §5b chạy hai lần | Chỉ áp cho F1–F7, chưa áp cho bảng mô tả |
| RQ1 vế LLM | A13, bảng 2–3 model | Chưa có trên bộ cuối; thước hiện tại không đo được |

---

## 5. Định vị khóa luận và paper

### Bảo vệ được với bằng chứng hiện tại

- Một bộ đánh giá theo mốc cho pháp luật Việt Nam, có cặp tương phản và dòng bãi bỏ, kèm hồ sơ nguồn gốc đầy đủ.
- Một thang đối chứng trên cùng dữ liệu: ngày văn bản (+0,08 TV-R@1), rồi kho phiên bản và khoảng hiệu lực (+0,12).
- Cái giá của việc đọc bản hiện hành: Accuracy 0,956 xuống 0,456.
- Câu trả lời RQ3: lợi ích đến từ việc dùng đồ thị **để dựng** kho phiên bản; phần duyệt đồ thị lúc truy vấn chưa cho thấy lợi ích.

### Cần thu hẹp hoặc bỏ

- "GraphRAG", "suy luận trên đồ thị", "Verifier giảm lỗi": cơ chế không có hoặc không tác động.
- "Hơn GraphRAG phi thời gian": `b5` không phải GraphRAG.
- "Gold đã kiểm độc lập", "bộ cuối do người kiểm".
- "Nhận diện bãi bỏ" như một kết quả: hiện là 7/23.
- Khoảng trống "chưa có nghiên cứu trong nước mô hình hóa chiều thời gian": ViHERMES và VLegal-Bench đã chạm chuỗi sửa đổi. Câu an toàn là mẫu ở `related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md` §4.3.
- "Baseline sai" không đồng nghĩa "RAG phẳng không giải được": baseline hiện không có lời văn hợp nhất và không thấy ngày.

### Chia việc

- **Cho khóa luận:** việc 1, 2, 6; bảng lệch đề cương; cập nhật chương 4–7 theo quy trình nhãn thật. Giữ tên đề tài; nói rõ đồ thị đóng vai offline (L0–L3).
- **Thêm cho paper:** việc 3, 4, 5. Thiếu việc 3 thì reviewer bác ngay ở tính độc lập của gold.

### Nếu lợi ích chủ yếu từ lọc thời gian

Đây đã là hiện trạng. Định vị thành "bộ đánh giá và phép đo phân rã", đúng hướng A của master plan.

Thông điệp: với luật Việt Nam, phần khó và có giá trị là hợp nhất phiên bản từ lệnh sửa đổi nằm ở văn bản khác. Một khi có kho đó, một bộ lọc khoảng là đủ cho T2. T6 vẫn mở: cấp sẵn căn cứ đạt 22/23, hệ đạt 7/23.

---

## 6. Năm phản biện khó nhất

**1. "Đây là bảng khoảng hiệu lực, không phải GraphRAG."**
- Có: thang đối chứng; `b7pp ≡ b7plus` ở truy xuất; ADR tự ghi.
- Chưa trả lời: P so với `b7plus`.
- Hành động: P0-1 và đổi cách gọi tên.

**2. "Gold lấy từ chính đồ thị của hệ."**
- Có: gold mù 120 dòng; đối chiếu VBHN (chỉ 2 cặp so được, `docs/reports/doi-chieu-vbhn.md`).
- Chưa trả lời: bộ cuối chỉ phủ 24 lineage; phân xử có AI.
- Hành động: P0-3.

**3. "Nhãn do AI gán, tác giả duyệt, không có luật sư."**
- Có: AC1 0,608 khai thẳng; hồ sơ hòa giải ở `data/review/ai_research/`.
- Chưa trả lời: độ đúng pháp lý của dòng `dat`.
- Hành động: luật sư hoặc NMT kiểm ngẫu nhiên 30 dòng `dat`; đã có trong plan (N1), chưa làm.

**4. "Baseline phẳng bị thiệt."**
- Có: cùng đường ống, cùng prompt, cùng `k`.
- Chưa trả lời: baseline không có lời văn hợp nhất và không thấy ngày.
- Hành động: P0-2 và P1-5.

**5. "Số phụ thuộc một generator dao động và một thước khớp chuỗi; truy xuất còn yếu."**
- Có: chạy hai lần; `oracle` 0,956 cho thấy thước ít phạt oan khi căn cứ đúng.
- Chưa trả lời: `b5 − b4` đổi dấu; TV-R@1 chỉ 0,336; trong 90 câu có đáp án mà `proposed2` sai, 46 câu không có gold trong top 20 **[HN]**.
- Hành động: P0-4 và P1-6.

---

## 7. Cần tác giả và GVHD chốt

1. **Tên gọi:** giữ "Temporal-Aware KG-RAG" theo đề cương và nói rõ đồ thị ở tầng offline, hay đổi cách gọi trong paper?
2. **Giờ người độc lập:** NMT hoặc luật sư có 10–20 giờ cho gold mù và mẫu chấm tay không? Thiếu thì paper phải tự hạ xuống "nhất quán với đồ thị".
3. **Phân tích sau khi đã thấy test:** chấp nhận amendment T1 và hai baseline mới ở dạng thăm dò, hay dựng một vòng đánh giá nhỏ mới cho chúng?
4. **LightRAG thật (C3):** còn là cam kết không? Đề cương ghi "GraphRAG phi thời gian", hiện chỉ có `b5`.
5. **NMT xác nhận ADR 0004 và 0006:** repo ghi chưa có.
6. **Nơi nộp và hạn:** plan ghi ICAIL 28/01/2027, chưa kiểm trang chính thức.

**Giả định khi xếp ưu tiên:** hạn 26/12 còn hiệu lực; ngân sách API thấp (đã hết credit hai lần); giờ người là thứ khan hiếm nhất.

| Nguồn lực | Làm |
|---|---|
| 1 ngày, 0 đồng | Việc 1 và 2 |
| 1 tuần, khoảng 15 giờ người | Thêm việc 3 và 4 |
| Thêm khoảng 2 USD và 1 amendment | Thêm việc 5 và 6 |

---

## Phụ lục A. Số G4 dùng trong báo cáo [XM]

Nguồn: `runs/final_g4_20261112/r1/results.md`, `r1/confirm.json`, `compare_runs.json`. Chế độ `giua_khoang`, 318 dòng T2/T3/T6, 156 lineage.

| Hệ | Acc | TV-R@1 | R@10 | TVER | Sai phiên bản |
|---|---:|---:|---:|---:|---:|
| `b1` | 0,006 | 0,000 | 0,000 | — | 0,008 |
| `b2ctx` | 0,302 | 0,151 | 0,613 | 0,535 | 0,253 |
| `b4` | 0,324 | 0,164 | 0,670 | 0,544 | 0,291 |
| `b5` | 0,311 | 0,164 | 0,670 | 0,566 | 0,294 |
| `b6` | 0,340 | 0,164 | 0,670 | 0,553 | 0,283 |
| `b7` | 0,487 | 0,242 | 0,758 | 0,248 | 0,177 |
| `b7plus` | 0,654 | 0,336 | 0,720 | 0,022 | 0,008 |
| `b7pp` | 0,660 | 0,336 | 0,704 | 0,000 | 0,008 |
| `proposed2` | 0,667 | 0,336 | 0,704 | 0,013 | 0,008 |
| `oracle` | 0,956 | 1,000 | 1,000 | 0,000 | 0,000 |
| `oracle_now` | 0,456 | 0,484 | 1,000 | 0,516 | 0,502 |

| F | So sánh | Ước lượng [KTC 95%] | Kết luận (hai lần giống nhau) |
|---|---|---|---|
| F1 | `proposed2 − b4`, Accuracy | +0,343 [+0,283; +0,401] | ủng hộ |
| F2 | `proposed2 − b5`, Accuracy | +0,355 [+0,297; +0,414] | ủng hộ |
| F3 | `proposed2 − b4`, sai phiên bản | −0,283 [−0,330; −0,237] | ủng hộ |
| F4 | `b7 − b2ctx`, TV-R@1 | +0,078 [+0,049; +0,110] | ủng hộ |
| F5 | `b7plus − b7`, TV-R@1 | +0,115 [+0,076; +0,156] | ủng hộ |
| F6 | `b7pp − b7`, TV-R@1 | +0,115 [+0,076; +0,156] | ủng hộ |
| F7 | `proposed2 − b7pp`, Accuracy, T6 không đáp án | +0,087 [0,000; +0,217] | không đủ bằng chứng |

## Phụ lục B. Số câu đúng theo lát [HN]

Lần 1 / lần 2. Tính lại từ dự đoán; tổng `all` của lần 1 khớp Accuracy trong `results.md`.

| Hệ | `all` (318) | Có đáp án (295) | T6 không đáp án (23) | T6 nút cha (9) | Gold bản 1 (156) | Gold bản ≥ 2 (139) |
|---|---|---|---|---|---|---|
| `b2ctx` | 96 / 102 | 89 / 95 | 7 / 7 | 4 / 3 | 48 / 51 | 41 / 44 |
| `b4` | 103 / 94 | 100 / 92 | 3 / 2 | 1 / 1 | 58 / 53 | 42 / 39 |
| `b5` | 99 / 99 | 98 / 97 | 1 / 2 | 0 / 1 | 56 / 53 | 42 / 44 |
| `b6` | 108 / 103 | 105 / 100 | 3 / 3 | 1 / 1 | 60 / 58 | 45 / 42 |
| `b7` | 155 / 162 | 153 / 160 | 2 / 2 | 1 / 1 | 100 / 103 | 53 / 57 |
| `b7plus` | 208 / 206 | 205 / 203 | 3 / 3 | 0 / 1 | 102 / 101 | 103 / 102 |
| `b7pp` | 210 / 211 | 205 / 205 | 5 / 6 | 2 / 3 | 103 / 103 | 102 / 102 |
| `proposed2` | 212 / 211 | 205 / 204 | 7 / 7 | 3 / 3 | 100 / 101 | 105 / 103 |
| `oracle` | 304 / 305 | 282 / 283 | 22 / 22 | 9 / 9 | 148 / 148 | 134 / 135 |
| `oracle_now` | 145 / 145 | 144 / 144 | 1 / 1 | 0 / 0 | 18 / 18 | 126 / 126 |

## Phụ lục C. Tra cứu ngoài (13/11/2026)

Phạm vi: 3 truy vấn tìm web chung, không gửi nội dung repo ra ngoài. Semantic Scholar, ACM DL, Google Scholar không được tra ở lượt này.

- LawInForce-eCFR: xác nhận có ở ACL Anthology. <https://aclanthology.org/2026.aacl-long.42/>
- NitiBench+: một lượt tìm không thấy. **Chưa xác minh hôm nay**; repo ghi arXiv ngày 3/11/2026. Bản NitiBench gốc: <https://arxiv.org/abs/2502.10868v2>
- "Asking For An Old Friend" (luật Đức): <https://arxiv.org/html/2605.23497>
- "Temporal Misgrounding in Legal RAG" (luật thuế Pháp) có trang ICML 2026; nên kiểm lại mục bib đang ghi arXiv. <https://icml.cc/virtual/2026/80578>
- CALRK-Bench (luật Hàn, chọn quy phạm còn hiệu lực theo thời điểm): thấy qua kết quả tìm, chưa đọc, chưa có trong ghi chú repo.
- VLegal-Bench có chiều "legislative evolution tracking": <https://arxiv.org/html/2512.14554v4>
- ViHERMES nêu việc lần theo chuỗi sửa đổi và xác định điều khoản đang hiệu lực: <https://arxiv.org/html/2602.07361>
- VLQA: <https://arxiv.org/html/2507.19995v1>

Khảo sát đầy đủ hơn của dự án nằm ở `related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md`; lượt này chỉ kiểm lại vài mục.

## Phụ lục D. Đã đọc gì

- `AGENTS.md`, `docs/WORKFLOW.md`, đề cương (trích chữ từ docx, không sửa).
- `docs/plans/active/master-plan.md` (toàn bộ).
- ADR 0004, 0006 (toàn bộ); ADR 0005 chỉ qua phần ADR 0006 dẫn lại.
- `runs/README.md` (toàn bộ); `runs/final_g4_20261112/` (`results.md`, `confirm.json`, `compare_runs.json`, `all.score.json`, dự đoán, prompt mẫu).
- `src/vilexgraph/framework/`: `systems.py`, `temporal.py`, `graphx.py`, `verify.py`; `scripts/eval/score_vilextime.py`, `compare_runs.py`, một phần `confirm_vilextime.py`.
- `data/vilextime_final/` (README, manifest, meta); `data/review/gold_*.reveal.tsv`, `gold_sample.tsv`.
- `docs/vilextime-dinh-nghia.md` §6; `docs/reports/phan-bien-adr-0006-20261111.md`, `doi-chieu-vbhn.md`.
- `docs/paper/nhap-paper-vilextime.md` (phần đầu và các chỗ `[CHỜ]`); chương 1, 4, 5, 6, 7 qua tìm từ khóa.
- `related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md` §1, §2 (một phần), §4.

**Đọc bổ sung ở lượt 2 (cùng ngày):** `retrieve.py`, `generate.py`, `corpus.py`; `docs/reports/chan-doan-t6-dev-20261111.md`, `e7_phan_ra_loi.md`, `t6-chuyen-cho-tra-cuu-20261111.md`, `g2-recall-m2-20261109.md`, `h5-loi-do-thi-20261110.md` (mục 0–1), `pheu-loc-lo-moi.md`, `quy-tac-mo-20261111.md`; `docs/vilextime-datasheet.md`; `docs/graph_justification.md` (mục 1–4.1); chương 3, 5, 7 và mục 6.7–6.8.

**Vẫn chỉ xem lướt:** ADR 0005 (chỉ khung và bảng XN), hướng dẫn gán nhãn (chỉ khung Q1–Q4), chương 1, 2, 4, phần còn lại của `h5-loi-do-thi`, `resolve-nhan-va-dong-thuan`, `theo_mien_e3`, `audit_dataset.md`, `crawling-plan.md`.

---

## 8. Bổ sung sau khi đọc hết code và báo cáo: phán quyết cuối

Mục này sửa hai nhận định ở lượt trao đổi về "cải thiện framework" và chốt việc cần làm.

### 8.1. Hai chỗ tôi nói chưa đúng, đã kiểm lại

1. **"Chia đơn vị cha–con là nút thắt": sai.** 294/295 đơn vị gold trong chỉ mục đã chứa đủ đáp án ngắn **[HN, `data/derived/corpus/index.sqlite`]**. Không cần đổi cách chia đơn vị.
2. **"Thẻ trạng thái từ đồ thị cho T6": đã thử gần như vậy và không ăn thua.** `proposed3` đưa thông báo bãi bỏ có cấu trúc vào prompt: +1/21 trên dev. X8 đặt lệnh bãi bỏ gold lên vị trí 1: 4/21, ngang lượt cũ. `oracle` chỉ đưa lệnh bãi bỏ: 19/21 **[XM, `docs/reports/chan-doan-t6-dev-20261111.md` mục 5; mục 9 là nháp chưa đối soát]**. Nguyên nhân theo chẩn đoán đó: 19–20 đoạn cùng chủ đề còn hiệu lực trong prompt, cộng quy tắc 4 của prompt cho phép trả theo quy phạm khác.

### 8.2. Phát hiện mới: điểm yếu thật là xếp hạng

Accuracy theo hạng của căn cứ gold, 295 dòng có đáp án, lần 1 **[HN]**:

| Hạng của gold | `b7` | `b7plus` | `proposed2` |
|---|---|---|---|
| 1 | 67/77 | 103/107 | 102/107 |
| 2–5 | 56/95 | 64/81 | 64/81 |
| 6–10 | 20/34 | 26/36 | 26/36 |
| 11–20 | 8/29 | 9/19 | 8/20 |
| Sau 20 (do mở rộng) | — | — | 1/3 |
| Không có | 2/60 | 3/52 | 4/48 |

- Gold đứng hạng 1 thì đúng 96%. Hạng 11–20 thì đúng dưới 50%.
- Gold chỉ đứng hạng 1 ở 107/295 dòng (36%).
- `proposed2` có 46 câu sai dù gold nằm trong prompt; 40 câu trong đó không trích căn cứ gold; 39 nếu không tính 1 câu trả "hết hiệu lực".
- Trần nếu mọi gold đang có trong prompt lên hạng 1: khoảng +34 câu (247 × 0,953 − 201), tức khoảng +0,11 trên `all` **[SL]**, không phải số đo.

Vì sao xếp hạng yếu **[XM, `src/vilexgraph/framework/retrieve.py`]**:
- BM25 chạy trên âm tiết rời, nối bằng OR, gồm cả âm tiết rất phổ biến.
- Lai ghép chỉ trộn top 20 của từ vựng với top 20 của dense, rồi cắt còn 20. Không có vùng ứng viên sâu hơn.
- Reranker chưa được cài (`NotImplementedError`).
- Dense là PhoBERT-base, cắt 256 token.

Các điểm yếu của phần mở rộng đồ thị **[XM, `graphx.py`]**:
- Lệnh lấy theo `ORDER BY unit_id LIMIT 3` cho mỗi đích: thứ tự tùy ý, không ưu tiên lệnh bãi bỏ hay ngày gần mốc.
- Không lọc theo loại thao tác, nên lệnh sửa đổi cũng vào prompt.
- Lệnh luôn đứng sau hạng 20.
- Trên bộ cuối, lệnh bãi bỏ gold vào prompt ở 12/23 dòng T6 không đáp án; model đúng 5 trong 12 **[HN]**.

### 8.3. Điều audit lượt 1 chưa nêu đủ: kho phiên bản chưa đầy đủ

- Độ phủ sự kiện sửa đổi so với `expiryProvisions` của cổng: trích được 5.200/8.046 (64,6%); **áp được 3.238/8.046 (40,2%)** **[XM, `docs/reports/g2-recall-m2-20261109.md`]**.
- Đối chiếu tự động với văn bản hợp nhất: 5.762/7.201 cặp lời văn khớp chính xác (80,0%) trên 51 văn bản; kiểm tay 58/60 sự kiện đã áp là đúng **[XM, chương 3 mục 3.5, số lịch sử]**.
- Bộ lọc LLM trước khi gán gắn mã `gold_wrong` cho 48/280 ứng viên T2 và 162/1.217 ứng viên T6 nút cha; tỷ lệ giữ T6 nút cha 3,9% **[XM, `docs/reports/pheu-loc-lo-moi.md`]**.

Hệ quả **[SL]**:
- ViLexTime chỉ gồm điều khoản mà đường ống dựng được và bộ lọc giữ lại. Lỗi bỏ sót sự kiện của đồ thị không thể hiện ra trên bộ này.
- Vì vậy không thể nói hệ "trả lời đúng phiên bản" trên pháp luật Việt Nam nói chung; chỉ nói được trên phần kho đã dựng.

### 8.4. Phán quyết

**Về paper:** viết theo hướng bộ đánh giá và phép đo phân rã (hướng A). **Không viết paper "framework GraphRAG đạt SOTA".** Ba lý do:

1. Phần đồ thị lúc truy vấn không tạo khác biệt đo được trên `all` (318 dòng, thăm dò hậu nghiệm): `proposed2 − b7pp` +0,006 [−0,016; +0,028] / 0,000 [−0,016; +0,016]; `proposed2 − b7plus` +0,013 [−0,009; +0,035] / +0,016 [−0,006; +0,038]. KTC chứa 0 ở cả hai lần. Ngoại lệ: trên T6 không đáp án (23 dòng), `proposed2 − b7plus` +0,174 [+0,043; +0,348] ở cả hai lần, còn `proposed2 − b7pp` có KTC chạm 0.
2. Với khoảng hiệu lực lan truyền đã tính sẵn offline, bài toán này không còn việc gì buộc phải duyệt đồ thị lúc truy vấn. Kể cả nhận diện bãi bỏ cũng chỉ cần bảng khoảng và con trỏ tới lệnh. Đây là hệ quả của chính thiết kế "phương án A" ở ADR 0001, không phải lỗi cài đặt.
3. Gold và hệ dùng chung một kho, kho mới áp được 40% sự kiện. Mọi claim về phương pháp đều vướng điểm này.

**Về framework:** dừng việc tìm cách cho thành phần đồ thị trực tuyến "thắng". Đóng góp phương pháp bảo vệ được là **đồ thị dùng để dựng kho phiên bản** (L0–L3) và thang đo cho thấy kho đó đáng giá bao nhiêu.

Nếu muốn điểm tuyệt đối cao hơn cho khóa luận và demo, chỉ một việc đáng làm:

- **Reranker cộng vùng ứng viên sâu hơn** (lấy 100, xếp lại, giữ 20). Phải áp như nhau cho `b4`, `b7`, `b7plus` và P. Việc này nâng mọi hệ có căn cứ đúng trong vùng ứng viên; nó không làm đồ thị thắng và không được viết thành đóng góp đồ thị. Reranker đã bị cắt ngày 05/11, mở lại là quyết định của CMT.

Không làm: thêm multi-hop, cộng đồng, agent; đổi generator lớn hơn; sửa tiếp `rel_up` hay thông báo bãi bỏ để cứu T6 (đã thử hai lần, n quá nhỏ để thấy khác biệt).

**T6:** báo đúng như đang có. Hệ 7/23, cấp sẵn căn cứ 22/23, kèm precision của khẳng định bãi bỏ. Kết luận: bài toán còn mở, nút thắt là nhiễu từ quy phạm cùng chủ đề, không phải thiếu thông tin đồ thị.

### 8.5. Danh sách thực nghiệm chốt

| # | Việc | Chi phí | Bắt buộc cho |
|---|---|---|---|
| 1 | Script quy kết từ dự đoán có sẵn: P so với `b7plus`; bảng hạng–Accuracy ở 8.2; precision/recall bãi bỏ; mọi hiệu ở cả hai lần; phân tầng theo người viết câu hỏi và miền | 0 | Khóa luận, paper |
| 2 | `b7v` chỉ truy xuất trên bộ cuối | 0 | Khóa luận, paper |
| 3 | Gold mù người 60–80 dòng rút từ 156 lineage bộ cuối; báo khớp thô trước phân xử | 10–13 giờ người | Paper; nên có cho khóa luận |
| 4 | Người chấm 100 câu (`b1`, `b4`, `proposed2`) | 6–8 giờ người | Paper (RQ1 vế LLM, độ tin của thước) |
| 5 | Hai baseline: lớp phiên bản không lọc; lớp phiên bản không lọc có in ngày hiệu lực | khoảng 1 USD, dev trước | Paper |
| 6 | Amendment sửa đáp án ngắn T1, chấm lại | ít | Khóa luận (Bảng 1, đối chứng) |
| 7 | Tùy chọn: reranker cho `b4`, `b7`, `b7plus`, P | GPU, dev trước, cần bộ đo mới hoặc ghi thăm dò | Chỉ khi muốn điểm cao hơn |

Việc 5 và 7 là cấu hình mới sau khi đã thấy test: phải có amendment, chọn trên dev, và ghi "thăm dò".

LightRAG thật (C3): không khuyên làm. Nó tốn tiền trích thực thể và không trả lời RQ3. Ghi vào bảng lệch đề cương, trừ khi GVHD yêu cầu.

### 8.6. Ba câu paper được phép nói, và cách nói

1. "Trên phần kho đã dựng được, lọc theo ngày văn bản tăng TV-R@1 +0,08; thêm kho phiên bản và lọc theo khoảng tăng tiếp +0,12." Kèm kết quả `b7v` để tách hai thành phần của bước thứ hai.
2. "Đọc bản hiện hành thay cho bản đúng mốc làm Accuracy rơi từ 0,956 xuống 0,456." Một generator.
3. "Mở rộng theo quan hệ lúc truy vấn so với `b7plus` (cùng kho, không lan truyền) không tạo khác biệt lớn hơn khoảng 4 điểm trên `all`; nhận diện bãi bỏ còn mở (7/23 so với 22/23 khi cấp sẵn căn cứ)."

Mỗi câu phải đi kèm: nhãn là AI gán, một tác giả duyệt; gold lấy từ cùng kho; kho áp được 40% sự kiện theo phép đo của dự án; kết quả gold mù ở việc 3.
