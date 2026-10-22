# ViLexTime — schema phát hành (bản chốt)

Ngày: 2026-10-21. Trạng thái: **chốt theo yêu cầu của CMT ("chốt schema cuối cùng")**; CMT sửa điểm 3 (không
công bố dòng bị loại). Code: `scripts/pipeline/export_release.py` (test `tests/test_export_release.py`);
`score_vilextime.py --release` chấm thẳng trên file công bố.

Nguồn: `data/derived/vilextime/release.jsonl` (`schema_version` 1.4.0, 2.383 dòng, 49 khóa cấp một), điều
kiện dùng của `scripts/eval/score_vilextime.py`, và so sánh với ViHERMES (arXiv:2602.07361): họ phát
hành một file phẳng 9 cột.

## Nguyên tắc

1. Người dùng benchmark chỉ cần một file phẳng, ít cột. Mọi thứ khác ở file phụ nối bằng `id`.
2. File chính đủ cho `score_vilextime.py` chấm mà không cần file phụ. Đã đối chiếu 21/10: chấm trên file
   công bố và trên `release.jsonl` cho cùng một báo cáo, 2.383/2.383 dòng.
3. Mỗi `id` là duy nhất (ViHERMES bỏ sót điều này: 1.561 dòng chỉ có 3 giá trị `id`).

## Các file

| File | Nội dung |
|---|---|
| `vilextime.jsonl` | 13 cột; dòng đã được người kiểm và đạt |
| `vilextime_silver.jsonl` | 13 cột; dòng chưa ai kiểm (định nghĩa §8, mã `not_verified`), không chấm |
| `vilextime_meta.jsonl` | mọi trường còn lại của các dòng trên, nối bằng `id`, có mục `review` |
| `vilextime.csv`, `vilextime_silver.csv` | 13 cột như bản `.jsonl`, để mở bằng Excel: UTF-8 có BOM, `accepted_evidence` nối bằng `;`, ô rỗng là null |
| `manifest.json` | phiên bản, số dòng theo nhóm × chế độ × split, lineage bị loại theo mã lý do, đồng thuận, sha256 |

Thư mục ra: `data/vilextime_dataset/`, riêng khỏi đầu vào dựng dữ liệu ở `data/vilextime/` và bản nội bộ
`data/derived/vilextime/release.jsonl`. Là file dẫn xuất (gitignore như `release.jsonl`), dựng lại bằng lệnh ở mục Cách xuất.

## File chính `vilextime.jsonl` (13 cột)

Đọc như bộ ba (câu hỏi, đáp án, ngữ cảnh). Hai cột mang tên khác tên nội bộ.

| Cột | Kiểu | Vì sao có |
|---|---|---|
| `id` | chuỗi | khóa dòng, duy nhất |
| `split` | `dev` / `test` | scorer mặc định chỉ chấm `test` |
| `group` | `T1`–`T6` | báo kết quả theo nhóm |
| `as_of_strategy` | `ranh_gioi` / `giua_khoang` / `truoc_hieu_luc` | bảng kết quả chính là `giua_khoang`; scorer báo theo từng chế độ |
| `question` | chuỗi | không chứa ngày, một câu phục vụ mọi mốc |
| `as_of` | ngày | mốc thời gian, cột làm ViLexTime khác các bộ khác |
| `context` | chuỗi hoặc null | câu dẫn của điều khoản cha + nguyên văn điều khoản có hiệu lực tại mốc (nội bộ: `target.lead_in` + `answer`); câu dẫn thường chứa đáp án ("3. Phạt tiền từ … đối với một trong các hành vi sau:"); null với T6 sau bãi bỏ |
| `answer` | chuỗi hoặc null | **đáp án chính thức**, scorer chấm EM/F1/Accuracy trên cột này; các đoạn cách nhau " … " (nội bộ: `short_answer`) |
| `answerable` | bool | T6 sau bãi bỏ là `false` |
| `citation` | chuỗi | "Điểm s Khoản 3 Điều 16", để tra lại (nội bộ: `target.citation`) |
| `lineage_id` | chuỗi | scorer ghép các phiên bản của một điều khoản để chấm tương phản |
| `version_id` | chuỗi hoặc null | phiên bản đúng tại mốc; scorer dùng cho TV-Recall |
| `accepted_evidence` | mảng chuỗi | đơn vị corpus được coi là đúng; scorer dùng cho Recall@k |

## File phụ `vilextime_meta.jsonl` (nối bằng `id`)

Mọi khóa của `release.jsonl` trừ các cột đã ở file chính; `schema_version` là `2.0.0`.

- **Nhóm và mốc:** `schema_version`, `subgroup`, `twin_of`, `changed_span`.
- **Điều khoản đích:** `target` (`document_id`, `law_id`, `doc_type`, `document_title`, `provision_id`,
  `parent_id`, `provision_path`, `level`, `lead_in`, `article_id`, `clause_id`, `point_id`, `citation`),
  `source_url`, `retrieved_at`, `jurisdiction`, `language`, `domain`, `domain_source`.
- **Chuỗi thời gian:** `valid_from`, `valid_to`, `in_force`, `num_versions`, `num_transitions`,
  `substantive_transitions`, `relevant_version_ids`, `utilized_version_ids`, `derivation`,
  `evidence_set`, `retroactive` (T5), `repeal_mode`, `repealed_by`, `norm_continuity` (T6),
  `pending`, `legal_markers`, `no_answer_reason`.
- **Độ khó:** `near_identical`, `similarity`, `similarities`, `chance_accuracy`, `min_repr`.
- **Xuất xứ:** `question_source` (loại, model, `prompt_sha`), `flags` (cờ máy).
- **Kiểm định của người:** `review`.

### Mục `review`

| Trường | Nội dung |
|---|---|
| `status` | `checked` / `not_verified` |
| `why` | (chỉ `not_verified`) chưa gán; A và B lệch, chưa hòa giải; nhãn theo hướng dẫn cũ |
| `verdict` | nhãn cuối `dat` / `khong_dat` |
| `reasons` | mã lý do (danh sách đóng, mục 7 của định nghĩa) |
| `double_labelled` | `true` nếu dòng nằm trong phần gán đôi (25% và lô 0) |
| `adjudicated` | `true` nếu luật sư chốt |
| `raw` | nhãn thô của A và B (chỉ với dòng gán đôi), để tái tính AC1 |
| `guideline_version` | `3.0` |
| `label_of` | (chỉ dòng anh em `giua_khoang`, `truoc_hieu_luc`) id dòng ranh giới mà nhãn được lấy |

## Quy tắc lấy nhãn cuối

1. **Một dòng ranh giới:** nhãn luật sư chốt nếu có (`hoa_giai_kiem.tsv`); không thì nhãn của người đã gán theo 3.0,
   **một người là đủ** (CMT 21/10: gán chéo làm sau). A và B cùng gán mà lệch nhau, chưa hòa giải: `not_verified`.
2. **Nhãn mang sang từ D4 (hướng dẫn 1.2, 2.0) chỉ tính khi người kiểm xác nhận lại theo 3.0.** Lý do: định nghĩa
   §8 chỉ nhận dòng đã kiểm có dẫn chứng; nhãn D4 không có bốn ô dẫn chứng và ra đời trước các mã 3.0
   (`restructuring_2025`…). Ví dụ có thật: dòng T2 mốc 14/01/2026, đáp án nêu "cấp huyện", máy gắn cờ
   `cap_huyen`, nhãn D4 1.2 là `dat`. Có 139 nhãn như vậy (A 70, B 69). Trang gán nhãn hiện lại các dòng này.
3. **Một lineage đạt khi mọi dòng ranh giới của nó đạt**, bị loại khi một dòng không đạt (như `adjudicate.py drop`
   với D4: cặp T2 thiếu một dòng thì không còn là cặp).
4. **Dòng anh em** (`giua_khoang`, `truoc_hieu_luc`: cùng câu hỏi, cùng phiên bản đáp án với dòng ranh giới)
   đi theo lineage của mình.

Dòng của lineage bị loại **không có trong file phát hành**; `manifest.json` chỉ đếm số lineage theo mã lý do và
số dòng theo nhóm, để làm bảng trong paper.

## Không công bố (giữ nội bộ để tái kiểm)

- Bốn ô của hướng dẫn 3.0: `da_xem_van_ban_tac_dong`, `cham_lan_sua`, `noi_dung_con_o_dau`, `phut`.
- Tên người gán nhãn; chỉ ghi vai trò (A, B, luật sư).
- Ghi chú tự do (`note`, `suggestion`) của người gán nhãn.
- `dropped.jsonl` và các dòng bị loại.

## Quyết định đã chốt

1. **Số phiên bản `2.0.0`.** ADR 0003 §8: đổi gold hay chuyển dòng giữa split là MAJOR, bản dựng lại làm cả hai.
2. **Dòng `dev` được kiểm như `test`.** Phiếu `kiem` chứa mọi dòng ranh giới của cả hai split (test 934, dev 186),
   nên dev cũng có nhãn người. Dòng chưa kiểm (của split nào cũng vậy) ra file silver.
3. **Không công bố dòng bị loại** (CMT 21/10). Paper chỉ báo số lượng theo mã lý do.
4. **Đáp án chính thức là `answer`** (nội bộ `short_answer`); `context` là phần đối chiếu.
5. **Khóa tiếng Anh, nội dung tiếng Việt.**

Không đưa vào schema: trường `reasoning` sinh bằng máy (CMT chưa chọn làm; thêm sau là MINOR).

## Sửa câu chữ

Người kiểm sửa câu hỏi và đáp án ngắn ngay trên `label_ui.py`. Bản sửa ghi vào `data/vilextime/questions.jsonl` và
`short_answers.jsonl` (bản model giữ ở `model_question`, `model_short_answer`; `edited_by`, `edited_at`), nên
`question_source` của dòng phát hành nói rõ câu nào người đã sửa. Lời văn luật (`context`), `as_of`, `version_id`
không sửa tay: sai thì dòng là `khong_dat`.

## Cách xuất

```
# sau khi sửa câu chữ: dựng lại (~1 phút; không sửa gì thì kết quả trùng từng byte)
python scripts/pipeline/build_vilextime.py && python scripts/pipeline/sample_vilextime.py --select \
  && python scripts/pipeline/enrich_vilextime.py && python scripts/check/check_release.py
python scripts/pipeline/export_release.py --draft    # đủ mọi dòng (trừ lineage bị loại) để đọc
python scripts/pipeline/export_release.py            # bản ứng viên: dòng chưa kiểm vào silver
python scripts/pipeline/export_release.py --final    # từ chối, không ghi gì, khi còn dòng ranh giới chưa có nhãn cuối
python scripts/eval/score_vilextime.py pred.jsonl --release data/vilextime_dataset/vilextime.jsonl
```

## Còn mở

- **Corpus truy xuất.** Người dùng cần corpus (đơn vị `asis:…`, `version:…` mà `accepted_evidence`, `version_id`
  trỏ tới) để chạy benchmark: `data/derived/corpus/asis.jsonl` 771 MB, `versions.jsonl` 834 MB, chưa tính chỉ mục.
  Datasheet §7 cho phép phân phối lời văn pháp luật (luật sư 12/10); cách đóng gói và nơi đăng chưa chốt.
- Datasheet mục 2, 7, 8 cập nhật khi đóng băng (bước 8), theo `manifest.json` của bản `--final`.
