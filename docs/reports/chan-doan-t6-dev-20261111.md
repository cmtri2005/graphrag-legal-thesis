# Chẩn đoán lỗi T6 trên dev (11/11/2026)

**Nháp, chưa đối soát độc lập.** Chỉ đọc kết quả đã lưu. Không gọi API, không sửa code, dữ liệu, scorer hay gold, không chạm test. Mọi con số tính lại bằng `scripts/check/t6_diag.py`; Recall@10 tính lại khớp `all.score.json` cho cả 5 hệ (script có `assert`).

## 1. Kết luận ngắn

1. **R@10 T6 tụt 0,76 xuống 0,38 gần như hoàn toàn là hệ quả của cách đo, không phải bộ lọc làm mất căn cứ.** Trên 21 dòng có đáp án, cả 5 hệ đều tìm trúng đúng 16/21 và đúng cùng các dòng. Mọi chênh lệch nằm ở 21 dòng không đáp án: b7 16/21, b7plus 11/21, b7pp và proposed2 0/21.
2. Với dòng không đáp án, scorer coi "tìm trúng" là lấy được đơn vị bị bãi bỏ (bất kỳ phiên bản nào). Bộ lọc phiên bản có nhiệm vụ loại chính đơn vị đó. Lọc đúng thì R@10 bằng 0. Lệnh bãi bỏ (`accepted_evidence`) do đồ thị thêm vào luôn ở hạng 21, ngoài top 10.
3. **Accuracy 0,52 của proposed2 trên T6 là 18/21 (có đáp án) + 4/21 (không đáp án).** Lỗi nằm ở dòng không đáp án: 17/21 dòng mô hình ghi "HIỆU LỰC: còn". Trong 12 dòng, lệnh bãi bỏ đã nằm trong prompt mà mô hình vẫn trả lời từ đoạn khác cùng chủ đề (thường là văn bản thay thế). Oracle (chỉ đưa lệnh bãi bỏ, không có đoạn nhiễu) đúng 19/21 dòng không đáp án (0,95 chung T6), nên mô hình đọc được lệnh bãi bỏ khi không bị nhiễu.

## 2. Định nghĩa của scorer (`scripts/eval/score_vilextime.py`, hàm `row_scores`, dòng 187–199)

- `accepted` = `accepted_evidence` của dòng. `hit[i]` = đơn vị thứ i nằm trong `accepted` **hoặc** thuộc cùng lineage (`provision`) với gold, bất kỳ phiên bản. `Recall@k` = có `hit` trong k đơn vị đầu.
- `tv_hit[i]` = đơn vị thuộc `accepted` **hoặc** chính là `version_id` của dòng. `TV-Recall@k` tương tự.
- Dòng có đáp án (T6 "trước bãi bỏ"): gold = `version:<id>:1`, `accepted_evidence` = `asis:provision:<id>`. Đáp án đúng = câu trả lời chứa mọi span của `short_answer`.
- Dòng không đáp án (T6 "sau bãi bỏ"): `lineage_id` = điều khoản **bị bãi bỏ**; `version_id` = None; `accepted_evidence` = **lệnh bãi bỏ** `asis:event:...` (đơn vị lớp A, không có ở lớp B). Đúng khi `answerable == False` (tức mô hình ghi "HIỆU LỰC: không"; "không rõ" và mọi thứ khác đều là `answerable=True`, xem `generate.py` dòng 130–140).
- Hệ quả: với hệ lọc đến phiên bản mà đúng thì đơn vị bị bãi bỏ bị loại, nên `hit` chỉ còn có thể đến từ lệnh bãi bỏ. Lệnh này do mở rộng đồ thị thêm vào **sau** top-k=20, nên luôn ở hạng 21 (cột `p2_event_gold_hang` = 21 ở mọi dòng có). Vì vậy R@10 của dòng không đáp án = 0 với b7pp, proposed2, proposed3.
- b7 (lọc cấp văn bản) vẫn thấy điều khoản đã bị bãi bỏ vì văn bản chứa nó còn hiệu lực. Nó "trúng" 16/21 nhưng Accuracy 0/21: tìm thấy nội dung đã hết hiệu lực được tính là trúng.

## 3. Cơ chế R@10 tụt (code)

| Hệ | Lọc | Dòng không đáp án, R@10 | Theo kiểu bãi bỏ (ancestor 16 / direct 5) |
|---|---|---|---|
| b7 | tài liệu | 16/21 | 12 / 4 |
| b7plus | tài liệu + cửa sổ cục bộ `local_from/local_to` | 11/21 | 11 / 0 |
| b7pp, proposed2 | cửa sổ lan truyền `prop_iv` | 0/21 | 0 / 0 |

- `temporal.py` dòng 36–43 và `predicate()` (dòng 58–76): `version` thêm `_LOCAL`, `propagated` thêm `_PROPAGATED` (`EXISTS ... prop_iv`). Cửa sổ cục bộ chỉ kết thúc khi chính điều khoản bị bãi bỏ (`direct`). Khi lệnh nhắm vào Điều cha (`ancestor`, 16/21 dòng dev), chỉ cửa sổ lan truyền mới kết thúc, nên b7plus giữ lại 11/16 dòng ancestor và b7pp loại hết.
- `retrieve.py` dòng 358–403: sau khi lọc và gộp RRF lấy `spec.k = 20`, mới gọi `expand(...)`. `graphx.expand` (cuối file) trả `hits + extra`, nên đơn vị đồ thị luôn xếp sau hạng 20. `fuse_rrf` và `lexical` lọc trước khi xếp hạng (dòng 5–6, 205).
- 21 dòng có đáp án: tập dòng trúng của b7, b7plus, b7pp, proposed2 trùng nhau hoàn toàn (đã kiểm). Phân loại (a) bằng 0.
- TV-Recall@10 của b7 (0,429) cao hơn R@10 có đáp án vì 2 dòng không đáp án b7 lấy được đúng lệnh bãi bỏ ở top 10. Các hệ lớp B không bao giờ có.

## 4. Phân loại lỗi proposed2 trên 42 dòng T6 dev (giua_khoang)

Bảng từng dòng: `docs/reports/chan-doan-t6-dev-20261111.tsv` (32 cột: gold, top10 và đúng/sai của 5 hệ, prompt có gold hay lệnh bãi bỏ, câu trả lời proposed2/proposed3, nhãn lỗi). Quy tắc phân loại ở `classify()` trong script.

| Loại | Nghĩa | Có đáp án | Không đáp án | Tổng |
|---|---|---|---|---|
| ok | proposed2 đúng | 18 | 4 | 22 |
| (a) | bộ lọc loại gold ở dòng có đáp án | 0 | 0 | **0** |
| (b) | truy xuất/đồ thị không đưa căn cứ vào prompt | 3 | 3 | **6** |
| (c) | căn cứ có trong prompt, mô hình trả lời sai | 0 | 12 | **12** |
| (d) | gold nghi: câu trả lời chứa đúng lời văn của điều khoản "bị bãi bỏ" lấy từ văn bản khác | 0 | 2 | **2** |
| (e) | khác | 0 | 0 | 0 |

Chi tiết:

- **(b) có đáp án, 3 dòng**: đơn vị gold không vào top 20 của bất kỳ hệ nào (lỗi tìm, không liên quan lọc).
- **(b) không đáp án, 3 dòng**: lệnh bãi bỏ không vào prompt. Nguyên nhân: mở rộng `rel_up` chỉ đi từ 5 hạt giống là **top 5 từ vựng không lọc ngày** (`retrieve.py` dòng 376–381, `SEEDS = 5` ở `graphx.py`; hạt giống không dùng dense). Với 3 dòng này, không hạt giống nào nằm trong chuỗi tổ tiên của điều khoản bị bãi bỏ (chạy lại truy vấn từ vựng, chỉ đọc, ngoài script), dù lệnh bãi bỏ có trong chuỗi `rel`.
- **(c), 12 dòng**: lệnh bãi bỏ đúng nằm trong prompt (đoạn dạng "Bãi bỏ Điều 11, Điều 12... Thông tư số 10/2025..."), cùng 19–20 đoạn khác. Mô hình ghi "còn" (tất cả 17 dòng sai đều là "còn"; không dòng nào "không rõ") và trích một đoạn cùng chủ đề của văn bản khác, ví dụ Thông tư 88/2025 thay vì Điều 12 Thông tư 10/2025.
- **(d), 2 dòng** (`...06-18` Nghị quyết 136/2024/QH15 và `...2025-05-18` TT 06/2023/TT-BGTVT): câu trả lời chứa đúng span gold của dòng đối ứng có đáp án, lấy từ đoạn khác có cùng lời văn. Dòng 2025-05-18 còn có điểm lạ: trong đồ thị, chuỗi tổ tiên của điều khoản này không có đơn vị lệnh bãi bỏ (`rel_units = 0`), nhưng lệnh gold vẫn là `accepted_evidence`. **Chưa kết luận gold sai**; cần CMT hoặc luật sư xem. Không sửa gold.
- Cũng nên xem nhóm (c): trích dẫn cho thấy nhiều dòng được trả lời từ văn bản thay thế (ví dụ TT 88/2025, NĐ 207/2026, NĐ 154/2013, NĐ 59/2017), tức là có thể là "chuyển chỗ". Quy tắc 4 của prompt (`generate.py`) và phán quyết cố vấn ngày 05/10 cho phép trả theo quy phạm đang điều chỉnh, nên với những dòng này gold "không đáp án" có thể xung đột với chính luật chơi. Chưa kiểm từng dòng, ghi là câu hỏi mở.

## 5. Dòng không đáp án: prompt có căn cứ bãi bỏ không, vì sao proposed3 chỉ +1/21

- proposed2: lệnh bãi bỏ gold có trong prompt ở 15/21 dòng (12/16 ancestor, 3/5 direct), luôn là đoạn thứ 21 hoặc 22 (cuối prompt). 6 dòng không có (3 (b), 2 (d), 1 ok do mô hình vẫn ghi "không").
- proposed3 (`repeal_note`): ghi chú có `đích bị bãi bỏ` đúng (khớp tổ tiên hoặc điều khoản gold) ở 15/21 dòng, trùng đúng 15 dòng trên. Trong 15 dòng đó: proposed2 đúng 3, proposed3 đúng 4. Còn 11 dòng cả hai cùng sai. Chênh +1 chung (p3 5/21, p2 4/21) gồm 1 dòng tăng trong nhóm có ghi chú, và 1 dòng tăng, 1 dòng giảm ở nhóm không có ghi chú (prompt nhóm này chỉ khác system prompt; đây là nhiễu lấy mẫu của mô hình).
- Vì sao ghi chú không đủ: dòng ghi chú gắn với **hạt giống** (một điều khoản anh em/ cùng Điều bị bãi bỏ, ví dụ "Điều 12 › Khoản 2 › Điểm a") chứ không gắn với điều khoản mà câu hỏi hỏi (nó đã bị lọc nên văn bản không có trong prompt). Mô hình phải tự suy "câu hỏi thuộc Điều 12", trong khi prompt còn có đoạn văn bản thay thế trả lời đúng chủ đề. Mô hình chọn đoạn trả lời được. Đây là kết luận từ đọc prompt và đối chiếu oracle, **chưa thí nghiệm**.
- Oracle chỉ gồm lệnh bãi bỏ: prompt rất ngắn, câu hỏi nêu tên văn bản, mô hình ghi "không" 19/21. Khác biệt chính giữa oracle và proposed2 là sự có mặt của 19–20 đoạn nhiễu cùng chủ đề (và một quy tắc 4 cho phép trả theo quy phạm thay thế).

## 6. Hướng sửa đề xuất (không chạy thử)

Quy tắc giữ nguyên: X2 (proposed3) không đạt, không thử lại; không đổi scorer, gold, split, ngưỡng.

**Hướng 1. Báo cáo T6 tách có/không đáp án; không dùng R@10 chung cho dòng không đáp án.** Thay đổi: chỉ ở chương kết quả và `report_results`, thêm bảng phụ "lệnh bãi bỏ có vào prompt" (15/21) và R@10 chia đôi, không sửa scorer. Tác động: không đổi điểm nào; sửa việc đọc sai "bộ lọc làm giảm R@10". Rủi ro: thấp, chỉ là trình bày, phải ghi là phân tích khám phá. Thuộc: **không có mục riêng trong "Việc trên dev"**; gần nhất là X5 (sổ chạy) và X8 (tách lỗi tìm khỏi lỗi đọc). Cần CMT đồng ý phạm vi trình bày.

**Hướng 2. Mở rộng X8 bằng điều kiện "căn cứ gold + đoạn nhiễu của P" (dev, T6).** Thay đổi: một điều kiện cấp sẵn mới: lệnh bãi bỏ gold nhét vào đúng prompt proposed2 (20 đoạn của P) thay vì đứng một mình. Tác động: cho biết lỗi (c) do nhiễu hay do prompt; chỉ chẩn đoán, không đổi hệ P. Chi phí: khoảng 42 lượt GPT-4o mini, vài xu. Rủi ro: dễ bị đọc nhầm như tuning P. Thuộc: **X8 mở rộng**, điều kiện mới nên cần CMT duyệt trước khi chạy.

**Hướng 3 (đổi hệ P, việc mới).** Hai phần có thể tách:
- 3a. Nới hạt giống của `rel_up` (SEEDS 5 lên 10, hoặc dùng hạt giống từ hợp nhất từ vựng + dense). `graphx.py` docstring ghi tham số này "may be tuned on dev only (ADR 0003 §7)". Kỳ vọng: tối đa +3 dòng vào prompt (các (b) không đáp án), nhưng mỗi dòng chỉ ~25% khả năng đúng (4/15 hiện tại), nên T6 không đáp án khoảng +1/21. Rủi ro: thêm đoạn nhiễu cho nhóm khác.
- 3b. Gắn trạng thái vào đoạn thay vì thêm ghi chú: giữ điều khoản bị bãi bỏ trong prompt kèm nhãn "ĐÃ BỊ BÃI BỎ từ <ngày> theo <lệnh>", hoặc đặt quy tắc ưu tiên "lệnh bãi bỏ nhắm đúng điều khoản được hỏi thì trả 'không' dù có văn bản khác cùng chủ đề". Kỳ vọng: nếu giả thuyết nhiễu ở Hướng 2 đúng, trần là 15–18/21 (số dòng có lệnh bãi bỏ trong prompt); so với oracle 19/21. Rủi ro lớn: xung đột với quy tắc 4 (chuyển chỗ) làm tụt dòng T2/T3 nơi cần trả theo quy phạm thay thế; thêm đoạn hết hiệu lực làm tăng `wrong_version`; có thể hợp thức hóa nhầm gold nghi sai (nhóm (d)). Thuộc: **việc mới, không nằm trong X1–X8; cần CMT duyệt và chạy dev toàn nhóm, KTC ghép cặp, trước G3 (20/11)**. Dừng ngay nếu T6 không đáp án không tăng rõ hoặc nhóm khác giảm. Vì gần với X2, nên ghi rõ đây là cơ chế khác (trạng thái/quy tắc) nếu được duyệt.

Khuyến nghị: làm Hướng 1 ngay (không rủi ro), xin duyệt Hướng 2 để biết có đáng làm Hướng 3 không. Chưa nên đổi P chỉ vì T6.

## 7. Tái lập và truy vết

- Lệnh: `.venv/bin/python scripts/check/t6_diag.py` (cwd repo; exit 0). Phần chạy lại truy vấn từ vựng cho hạt giống chỉ làm ngoài script (đọc `data/derived/corpus/index.sqlite` ở chế độ chỉ đọc, 1 lần, exit 0); kết quả ghi ở mục 4 là đếm phụ chưa nằm trong script.
- HEAD: 3de9b05 (cây làm việc có file untracked sẵn của lượt chạy cũ; các file đầu vào không bị sửa).
- SHA256 (16 ký tự đầu): `all.score.json` b10526d682706ac0; dev/b7 bba8d06290c4f974; b7plus 486d61729ccdcb6f; b7pp cf87c69d05c1f04f; proposed2 35b20daee0c1a83a; proposed3 220fd74fd843a095; prompts/proposed2 3275bb291c34e472; prompts/proposed3 8124ad253cf5dc0e; `data/vilextime_dataset_h6/vilextime.jsonl` 7aada39a82f5ec66; `vilextime_meta.jsonl` e0d4c2693bfd85c7.
- Mô hình sinh: `gpt-4o-mini-2024-07-18` (API, không checkpoint); các lượt đã chạy sẵn, không sinh mới.
- Giới hạn: n = 21 lineage mỗi vế, dev; không kết luận cho test. Nhãn (c) và (d) dựa trên quy tắc cơ học và đọc tay các câu trả lời; chưa có luật sư xem.
