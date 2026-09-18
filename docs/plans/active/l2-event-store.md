# Execution Plan: Event L2 áp được lên chuỗi phiên bản (P3.9–P3.11)

Date: 2026-09-18

## Status

Active.

## Outcome

`data/derived/provision_events.jsonl` chứa event có `id` tất định, `status`
theo ba mức, và với thao tác sửa lời văn thì có kèm lời văn mới. Nhờ vậy
`EventApplier` (`temporal/event_applier.py`) nhận được event mà không cần sửa
domain model. Loader Neo4j (P3.4) và P3.15 đọc thẳng file này.

## Context

- ADR 0001: event đã duyệt phải là file trong `data/`, vì Neo4j dựng lại được.
- `EventApplier` từ chối AMEND/REPLACE/CORRECT nếu không có `text_updates`, và
  từ chối SUPPLEMENT nếu không có update hoặc insertion. Bản L2 đầu (commit
  d9a43df) chỉ có thao tác + vị trí + ngày, nên chỉ 9.382/41.249 event (repeal)
  áp được.
- Text của mỗi nút chỉ là lời của chính nút đó (`data/provisions/*.json`): Điều
  chỉ có dòng tiêu đề, Khoản chỉ có đoạn của nó, các Điểm là nút con riêng.
- Đo trên các VB tác động (2026-09-18): sau "như sau:", 22.821 chỗ có lời văn
  trong ngoặc kép, 12.072 chỗ không có ngoặc. Nhóm không ngoặc gồm cả câu dẫn
  mở danh sách chỉ dẫn.

## Scope

In scope:

- Ba mức trạng thái, dùng lại `EventStatus`:
  - `verified`: có metadata của cổng xác nhận, tức một nút bị tác động nằm
    trong `expiry_targets` (resolve chính xác) và thao tác thuộc nhóm kết thúc.
  - `auto_accepted` (mức "EXTRACTED" đã thống nhất): resolve được, có ngày,
    có đủ payload, không thuộc lớp lỗi đã biết.
  - `needs_review`: phần còn lại, có `status_reason`
    (`WarningCode` trong `extraction/models.py`).
- Lời văn mới lấy từ khối trong ngoặc kép sau "… như sau:", cắt theo marker
  (`Điều N.`, `1.`, `a)`) rồi ghép vào cây con của nút đích theo nhãn.
- Thay cụm từ: `new_text = old_text.replace(A, B)` khi A có trong text cũ.

Out of scope (tới lượt thì làm, hoặc để `needs_review`):

- Lời văn mới không nằm trong ngoặc kép.
- Khối mới có cấu trúc con khác cây cũ (thêm hoặc bớt Khoản/Điểm).
- SUPPLEMENT tạo nút mới (`ProvisionInsertion`).
- Hàng đợi duyệt tay `data/review/provision_events.jsonl`: chỉ tạo khi có
  người duyệt thật.

## Approach

1. `Mention` mang chỉ số đoạn chứa câu chỉ dẫn; `_drop_quotes` giữ nguyên số
   dòng.
2. `wording_blocks(paragraphs)`: khối trong ngoặc sau đoạn i (trên cùng dòng
   hoặc các đoạn kế), cân ngoặc; không có ngoặc thì trả về None.
3. Ghép khối vào cây đích: gốc khối khớp nhãn nút đích, các con khớp đúng tập
   nhãn các con hiện có, khi đó mỗi nút nhận một `TextUpdate`. Lệch thì
   `needs_review`.
4. `extract_provision_events.py` ghi `id`, `status`, `status_reason`,
   `text_updates`. `measure_provision_events.py` báo tỷ lệ theo mức và mẫu
   kiểm tay cho lời văn mới.
5. P3.10: 456 cặp gold một-actor khớp thì thành `verified`; 8 ca lệch thì
   xem tay.

## Risks And Recovery

- Nút Khoản/Điểm tách từ thân văn bản (backfill T5) chưa có phiên bản trong
  index. Loader phải tạo phiên bản cho chúng, nếu không applier báo "no
  version".
- Ghép sai lời văn là một câu trả lời sai lặng lẽ. Chỉ nhận khi khớp nhãn
  hoàn toàn và đo precision trên mẫu mới.
- Mọi đầu ra là file dẫn xuất: xóa rồi chạy lại script.

## Progress

- [x] Chỉ số đoạn cho `Mention`; khối lời văn mới (cả ngoặc thẳng) bị che
  khỏi bộ đọc chỉ dẫn, nhờ vậy sửa luôn lớp lỗi dòng 7 và 17 của vòng 4
- [x] `extraction/wording.py`: `wording_blocks`, `parse_items`, `fit`; test
  trong `tests/test_wording.py`
- [x] Ghi `id`/`status`/`status_reason`/`text_updates`, chạy lại toàn corpus
- [x] Đo: số event theo mức, precision trên mẫu kiểm tay, áp thử bằng
  `EventApplier`
- [x] P3.10: xem 8 ca lệch với gold một-actor; không tạo event chỉ từ
  metadata (xem Decisions)
- [ ] Lời văn không ngoặc kép, thay đổi cấu trúc (thêm/bớt Khoản/Điểm),
  SUPPLEMENT tạo nút mới, thay cụm từ: để phiên sau

## Decisions

- 2026-09-18: Ba mức trạng thái như trên (CMT đồng ý). Tên mức giữa dùng
  `auto_accepted` có sẵn thay vì thêm `extracted`.
- 2026-09-18: Trích lời văn mới từ VB tác động, không sửa domain model để
  cho phép phiên bản không có text (CMT chọn).

- 2026-09-18: Câu chỉ dẫn có "Phụ lục" hoặc "mẫu" chen giữa thao tác và trích
  dẫn thì bỏ qua: phụ lục không nằm trong cây, resolve sẽ rơi vào Điều cùng số
  ở thân văn bản (mẫu 20260922: 3/60 lỗi thuộc lớp này, 2 trong số đó đã áp được).
- 2026-09-18: P3.10 không sinh event chỉ từ metadata. Các cặp gold một-actor
  mà L2 bỏ sót gồm 57 bãi bỏ (thao tác suy từ hậu tố HHL1P1 chỉ đúng 81%) và
  376 sửa đổi (không có lời văn). Mức `verified` đã là event được cổng xác
  nhận. 8 ca "lệch actor" đều là VB tác động ghi rõ trong text mà cổng thiếu
  cạnh genealogy, không phải lỗi L2.
- 2026-09-18: Từ seed 20260923, mẫu kiểm tay chỉ lấy event áp được.

## Validation

- Focused proof: `tests/test_provision_ops.py`, test mới cho `new_wording` và
  phần ghép cây.
- Integration: dựng `TemporalState` từ index cho vài VB tác động có thật và
  `EventApplier.apply` chạy không lỗi với event `auto_accepted`/`verified`.
- Repository-required checks: `python -m pytest -q`.

## Result

Đo 2026-09-18 (chưa đóng plan, còn các mục ở Progress):

- 50.700 dòng event: 2.819 `verified`, 13.985 `auto_accepted`, còn lại
  `needs_review`. Tính trên các event đã resolve: bãi bỏ áp được 99,9%, sửa đổi
  41,9% (có lời văn khớp cây), thay thế 10,8%, bổ sung 0%.
- `scripts/check/apply_provision_events.py`: 16.254/16.804 (96,7%) event áp được
  chạy qua `EventApplier` không lỗi. Lỗi còn lại: 269 ngày của actor không sau
  ngày bắt đầu phiên bản hiện tại, 170 nút đích không có text, 111 nút đã bị
  đóng trước đó.
- Kiểm tay 60 event áp được (seed 20260923): 58/60 = 96,7% (Wilson 95%:
  88,6–99,1%). Cả 2 lỗi là câu có hai thao tác ("Bãi bỏ Điều 6 và sửa đổi
  Điều 15"), trong đó thao tác thứ hai bị nhận là bãi bỏ.
- Kiểm tay 30 lời văn mới: 30/30 cắt đúng biên nút.
- Recall theo expiryProvisions giảm từ 64,9% xuống 62,2%, vì bỏ các câu có
  phụ lục và che khối lời văn mới. Cùng actor với gold một-actor: 98,2%.
