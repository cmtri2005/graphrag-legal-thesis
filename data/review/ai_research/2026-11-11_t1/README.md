# Phiếu T1 mới (đối chứng "không làm hại"), 11/11/2026 — NHÁP, chưa người kiểm

Đối chiếu độc lập chưa làm. CMT duyệt trong hội thoại 11/11. Phiếu: `data/review/the4/t1_moi_worksheet.jsonl` (+ `.manifest.json`),
60 lineage, batch 12 (30) và 13 (30), 60 dòng mốc `ranh_gioi`. Chưa gán nhãn, chưa chạy hệ.

## Phễu

| Bước | Số | Model |
|---|---:|---|
| Rút seed `vilextime-t1-1111`: 90 đầu, thêm 120 tiếp (hạng 91–210, cùng thứ tự đã xáo) vì 90 đầu chỉ có 31 câu đạt | 210 | không |
| Câu hỏi đạt qcheck (tối đa 3 lượt; 90 đầu 31, 120 sau 47) | 78 | `claude-code` / `claude-haiku-5-5` (yêu cầu `haiku`, `modelUsage` trả đúng ID này) |
| Có đáp án ngắn trích nguyên văn | 78 | `claude-haiku-5-5`, 0 null |
| Qua contrast (T1: 1 phiên bản, cần 1 đáp án ngắn trích đúng) | 77 | máy |
| Có đoạn + link văn bản gốc | 76 | máy (`evidence.py`, 1 lineage thiếu đoạn gốc bị loại) |
| Vào phiếu: 60 đầu theo thứ tự rút (dùng đến hạng 153) | 60 | |

Nhóm lỗi qcheck (lượt cuối, 210 mục): copy_share 122, insufficient_context 8, copies_the_answer 2. T1 có một phiên bản ngắn nên
khó viết câu không chép chữ; cổng 0,40 giữ nguyên, không nới.

## Loại trừ và kiểm

Loại cứng: lineage có `flags` (như `sample_vilextime.py`), R6 blocked, v1.0 (246 lineage), văn bản dev (`published_scope` 73 + hash split dev 376 văn bản),
và mọi lineage có nhắc `provision:<uuid>` trong `runs/`, `data/review/**` (kể cả xlsx), `data/vilextime/`, `vilextime_dataset*`, `derived/vilextime_test2`, `derived/vilextime/selected.jsonl`
(1.276.078 token). Quét `runs/` nhắc cả đoạn truy xuất, rộng hơn "dự đoán", nên loại 1.799/2.497 T1: bảo thủ có chủ ý, kho còn 462. Tối đa 2 lineage mỗi văn bản.
`verify.json`: mọi số trùng = 0 (v1.0, dev, hash dev, token, lo0, lo1 silver, lo2, silver, test2 release/questions, jsonl ai_research); 58 văn bản, tối đa 2/văn bản;
60/60 qua `judge_question` hiện hành; 0 câu có số hiệu/Điều/Khoản/năm; schema bằng lo2; không có khóa review/nhãn/provenance trong phiếu.

Phân bố 60 (`distribution_60.json`): Nghị định 31, Thông tư 18, Quyết định 4, Luật 3, Thông tư liên tịch 2, Pháp lệnh 1, Nghị quyết 1; Điểm 39, Khoản 21;
miền: giao_thong 15, doanh_nghiep_dau_tu 4, thue 4, dat_dai 3, khac 35.

## Mốc

Phiếu chỉ có dòng `ranh_gioi` (như lo2). Dòng `giua_khoang` của 60 lineage dựng bằng đúng `twin_of` của `enrich_vilextime.py`
(cùng caps, document_end, SNAPSHOT): `t1_moi_twins_giua_khoang.jsonl`, 60/60 có twin. Twin thừa nhãn của dòng ranh giới lúc phát hành (như v1.0).

## Thay đổi mã

- `scripts/review/test2_packs.py`: `lineage_rows` đọc thêm T1 (nếu có file); `qpack` chỉ T1 thì HUONG_DAN = base + T1 + test2_cau_hoi (T2/T3/T6 không đổi byte).
- `scripts/review/test2_prepare.py`: `contrast_problems` thêm T1 (cần 1 đáp án ngắn, đáp án giống nhau ở mọi mốc là đúng).
- Test mới: `test_t1_pack_uses_only_base_t1_...` (packs), `test_t1_single_version_...` (prepare).
- Hồ sơ này: `draw.py`, `draw_ext.py`, `scan.sh`, `twins.py`, `claude_task.py` (phiên `claude -p --tools ''` cô lập, cờ như `filter_session.py`), `publish_t1.py`, `verify.py`, `rounds_ext.sh`.

## Còn hở

- `test2_labels.load_worksheet` chỉ nhận T2/T3/T6 và thẻ 4.0 có Q2 "có thay đổi" (T1 không có). Trang gán nhãn chưa nạp được phiếu T1; chưa sửa, cần quyết định thẻ cho T1.
- T1 không qua lọc LLM; `result_t1_nofilter.tsv` là file ống dẫn qpack, không phải quyết định giữ thật.
- Câu hỏi và đáp án ngắn do `claude-haiku-5-5`, chưa người đọc. Hồ sơ đầy đủ ở `/home/trica/vilextime_loc/gan_t1/` (log từng phiên trong `logs/`).
