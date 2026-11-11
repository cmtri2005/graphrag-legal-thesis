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

## 8. Bảng T6 tách (Việc 1, nháp chưa đối soát)

Dev, `giua_khoang`, 21 dòng có đáp án + 21 dòng không đáp án, release `data/vilextime_dataset_h6/vilextime.jsonl`. Điểm gọi thẳng `score_vilextime.score` trên từng vế; có assert Accuracy và R@10 T6 gộp khớp `all.score.json` cho cả 15 hệ. "Lệnh bãi bỏ trong prompt" = `accepted_evidence` của dòng có trong `retrieved` của file prompt; "hạng" = vị trí 1-based trong đó. R@10 dòng không đáp án theo định nghĩa của scorer (xem mục 2), nên không so được với R@10 dòng có đáp án. Phân tích khám phá, không đổi điểm nào.

| Hệ | T6 có đáp án: n | Accuracy | R@10 | T6 không đáp án: n | Accuracy (nói không) | R@10 | lệnh bãi bỏ trong prompt | hạng |
|---|---|---|---|---|---|---|---|---|
| b1 | 21 | 0.000 (0/21) | 0.000 | 21 | 0.000 (0/21) | 0.000 | 0/21 | - |
| b2ctx | 21 | 0.762 (16/21) | 0.619 | 21 | 0.048 (1/21) | 0.667 | 2/21 | 7,9 |
| b3 | 21 | 0.571 (12/21) | 0.571 | 21 | 0.143 (3/21) | 0.571 | 0/21 | - |
| b4 | 21 | 0.714 (15/21) | 0.667 | 21 | 0.000 (0/21) | 0.667 | 2/21 | 13,17 |
| b5 | 21 | 0.714 (15/21) | 0.667 | 21 | 0.000 (0/21) | 0.667 | 7/21 | 13,17,21 |
| b6 | 21 | 0.762 (16/21) | 0.667 | 21 | 0.000 (0/21) | 0.667 | 2/21 | 13,17 |
| b7 | 21 | 0.857 (18/21) | 0.762 | 21 | 0.000 (0/21) | 0.762 | 2/21 | 6,10 |
| b7plus | 21 | 0.857 (18/21) | 0.762 | 21 | 0.095 (2/21) | 0.524 | 0/21 | - |
| b7pp | 21 | 0.857 (18/21) | 0.762 | 21 | 0.190 (4/21) | 0.000 | 0/21 | - |
| oracle | 21 | 1.000 (21/21) | 1.000 | 21 | 0.905 (19/21) | 1.000 | 21/21 | 1 |
| oracle_now | 21 | 1.000 (21/21) | 1.000 | 21 | 0.048 (1/21) | 1.000 | 0/21 | - |
| p2a2 | 21 | 0.857 (18/21) | 0.762 | 21 | 0.143 (3/21) | 0.000 | 0/21 | - |
| p2a3 | 21 | 0.857 (18/21) | 0.762 | 21 | 0.190 (4/21) | 0.000 | 15/21 | 21 |
| proposed2 | 21 | 0.857 (18/21) | 0.762 | 21 | 0.190 (4/21) | 0.000 | 15/21 | 21 |
| proposed3 | 21 | 0.857 (18/21) | 0.762 | 21 | 0.238 (5/21) | 0.000 | 15/21 | 21 |

Đọc nhanh: ở mọi hệ có lọc phiên bản (b7pp, p2a2, p2a3, proposed2, proposed3), R@10 vế có đáp án là 0,762 (16/21) và vế không đáp án là 0,000; R@10 gộp 0,381 là trung bình hai vế. Hệ b2ctx–b6 có R@10 vế không đáp án 0,667 vì không lọc ngày (lấy lại điều khoản đã bị bãi bỏ) nhưng Accuracy vế đó gần 0. `oracle_now` có R@10 1,0 ở vế không đáp án vì được đưa phiên bản cuối của điều khoản bị bãi bỏ, và nói "không" 1/21. Hạng "21" của `proposed2` trùng mục 5 (đoạn thứ 21 hoặc 22 của prompt).

Lệnh: `.venv/bin/python scripts/eval/t6_breakdown.py` (cwd repo, exit 0, ~30 giây, đọc versions.jsonl theo luồng). Test: `tests/test_t6_breakdown.py`.

## 9. X8 mở rộng (Việc 2): đặt lệnh bãi bỏ gold lên vị trí 1 (nháp chưa đối soát)

**Đây là chẩn đoán dùng gold (lệnh bãi bỏ đúng được đưa vào prompt), không phải một hệ, không dùng để chọn P hay đổi prompt hệ.** Chỉ dev, đúng 21 dòng T6 không đáp án `giua_khoang`. Không chạm test.

Thiết kế: C0 = prompt `proposed2` giữ nguyên từng byte (script dựng lại từ `ids` và assert trùng `user`/`system` cũ ở 21/21 dòng), gọi API lại. C1 = như C0 nhưng đoạn lệnh bãi bỏ gold ở vị trí [1], đánh số lại, phần còn lại giữ thứ tự cũ, system không đổi (chuyển 15 dòng từ hạng 21, chèn 6 dòng chưa có trong prompt; `c1_changes.json`). Model `gpt-4o-mini-2024-07-18`, nhiệt độ 0, `max_tokens` 1024, seed 20261109; cùng `system_fingerprint` `fp_3a3c79652c` cho cả 42 lượt. Đúng = `score_vilextime.correct` (nói "HIỆU LỰC: không"). Định dạng 21/21 ở cả hai, cắt cụt 0.

```
| dòng | thao tác C1 | cũ | C0 | C1 |
|---|---|---|---|---|
| 41522558…2026-05-18 | chuyển (hạng 21) | sai | sai | sai |
| 8ac0e590…2026-08-08 | chèn | sai | sai | sai |
| 6cab03a0…2021-10-21 | chuyển (hạng 21) | sai | sai | sai |
| 6e3d884a…2025-09-06 | chuyển (hạng 21) | sai | sai | sai |
| 6e30cd9c…2026-06-18 | chèn | sai | sai | sai |
| 2cb2c1fa…2020-11-11 | chuyển (hạng 21) | sai | sai | sai |
| ecff2318…2018-06-10 | chuyển (hạng 21) | sai | sai | sai |
| 7dd23e64…2026-08-06 | chèn | sai | sai | sai |
| c203f3d0…2019-11-05 | chuyển (hạng 21) | sai | sai | sai |
| fe9e225a…2025-11-08 | chuyển (hạng 21) | sai | sai | sai |
| fe9e707a…2022-02-03 | chuyển (hạng 21) | đúng | đúng | đúng |
| 7dc9e82a…2025-05-18 | chèn | sai | sai | sai |
| 92d51460…2026-03-05 | chuyển (hạng 21) | sai | sai | sai |
| 20ee7b9c…2025-12-04 | chuyển (hạng 21) | sai | sai | sai |
| 1a267400…2017-06-07 | chuyển (hạng 21) | đúng | sai | đúng |
| 6caa8e70…2021-09-03 | chuyển (hạng 21) | sai | sai | sai |
| 982d3ea0…2026-03-18 | chèn | đúng | sai | sai |
| 890e6428…2021-05-28 | chèn | sai | sai | sai |
| 939488a2…2025-05-26 | chuyển (hạng 21) | đúng | đúng | đúng |
| 1634ac90…2025-01-31 | chuyển (hạng 21) | sai | sai | sai |
| f1fc5a86…2026-08-17 | chuyển (hạng 21) | sai | sai | đúng |
tổng đúng: {'cu': '4/21', 'C0': '2/21', 'C1': '4/21'}
C0 khác cũ (đúng/sai): 2 | câu trả lời khác chữ: 6
C1 - C0: +2 -0, hiệu +0.095 [+0.000; +0.238], McNemar chính xác p=0.500
C0 - cu: +0 -2, hiệu -0.095 [-0.238; +0.000], McNemar chính xác p=0.500
C1 - cu: +1 -1, hiệu +0.000 [-0.143; +0.143], McNemar chính xác p=1.000
chuyen 15 {'cu': 3, 'C0': 2, 'C1': 4}
chen 6 {'cu': 1, 'C0': 0, 'C1': 0}
```

Tóm tắt: cũ 4/21, C0 2/21, C1 4/21. Nhiễu API (C0 so với cũ): 2 dòng đổi đúng/sai (cả hai đúng sang sai), 6/21 dòng đổi câu trả lời. C1 − C0 = +2/21 (+0,095, KTC bootstrap 95% [0,000; 0,238], 2.000 lần, seed 20261111; McNemar chính xác p = 0,50). C1 − cũ = +1 −1. Ở C1, mô hình trích lệnh bãi bỏ ở 4/21 dòng (C0: 1/21) và vẫn nói "còn" ở 17/21. Nhóm chuyển (15): cũ 3, C0 2, C1 4; nhóm chèn (6): cũ 1, C0 0, C1 0.

Diễn giải thận trọng (n = 21, một lượt mỗi điều kiện, không phải thử nghiệm xác nhận):
- Đưa lệnh bãi bỏ lên đầu không làm đúng nhiều lên: C1 4/21, ngang lượt cũ, cách xa oracle 19/21. Cải thiện so với C0 (+2) nằm trong cỡ nhiễu của chính API (C0 so với cũ lệch 2 dòng ngược chiều), KTC chạm 0. Dữ liệu này không ủng hộ giả thuyết lỗi (c) chủ yếu do vị trí cuối prompt.
- Khớp hơn với giả thuyết nhiễu nội dung: 19–20 đoạn cùng chủ đề (văn bản thay thế) vẫn có trong prompt, và quy tắc 4 (trả theo quy phạm đang điều chỉnh) cho phép mô hình trả lời từ chúng. Thí nghiệm này không tách được hai yếu tố đó; chưa có điều kiện bớt đoạn nhiễu.
- 6 dòng chèn: 0/6 đúng ở C1 dù lệnh bãi bỏ đứng đầu; trong đó có thể có dòng gold nghi (nhóm (d), mục 4). Không kết luận về gold.
- Không dùng kết quả này để chọn P hay đổi hệ. Quy tắc chọn P không đổi.

Chi phí: 217.470 token vào + 5.175 ra, ước tính khoảng 0,04 USD theo giá công bố (ngân sách 0,5 USD).

Tái lập (cwd repo, dev, cần `.env` nạp khóa, không in):
```
.venv/bin/python scripts/eval/x8_t6_variant.py
set -a; . ./.env; set +a
for c in C0 C1; do .venv/bin/python scripts/eval/api_generate.py --prompts runs/x8_t6_dev_20261111/prompts_$c.jsonl --provider openai --model gpt-4o-mini-2024-07-18 --out-dir runs/x8_t6_dev_20261111/raw; done
# import: colab_b1.py import --prompts prompts_$c.jsonl --raw raw/proposed2__gpt-4o-mini-2024-07-18__<sha12>.jsonl --out dev_$c.jsonl
.venv/bin/python scripts/eval/x8_t6_report.py
```
SHA256 (16 ký tự đầu): prompts_C0 480b9779e00adeec; prompts_C1 9d63ed11a4e87c7f; raw C0 0cf03d97dfacde88; raw C1 0348bd4087d59fb0; dev_C0 c98e9c46048bc292; dev_C1 83a61b6ebb17c3e8; nguồn `prompts/proposed2.jsonl` 3275bb291c34e472, `dev/proposed2.jsonl` 35b20daee0c1a83a, release 7aada39a82f5ec66. Code khi gọi API: HEAD 0b0cce8 (3 script mới chưa commit lúc chạy, nội dung nằm trong commit của lượt này). Log API (`api_C*.log`) bị gitignore, chỉ có ở máy chạy. Import dùng kiểm hash prompt của `colab_b1.py`; `.export.json` của C0/C1 là bản sao record proposed2 với `rows`/hash file đã cập nhật.
Giới hạn: một lượt mỗi điều kiện, nhiễu API đo được chỉ từ một cặp (cũ, C0); n = 21; dùng gold; chưa đối soát độc lập; không kết luận cho test.
