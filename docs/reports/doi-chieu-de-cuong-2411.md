# Đối chiếu hiện trạng với đề cương, 24/11/2026

Đề cương: `docs/DeCuongKLTN_23521635_23521643_UIT.docx`. Chỉ đọc, không sửa nghiên cứu.

## 1. Khớp đề cương
- Bài toán (x, t) → (a, E ⊆ 𝒰ₜ): giữ nguyên.
- Kiến trúc L0–L5: có đủ. `proposed2` = từ vựng + dense + lọc phiên bản lan truyền + mở rộng 1 bước + Verifier.
- Baseline: `b1`…`b7`, LightRAG, KG phân cấp `b6`, chỉ lọc siêu dữ liệu `b7`.
- Chỉ số: Recall@k, MRR, TV-Recall, Accuracy, F1, TVER, VCR, TCS. LLM-judge có script, chưa hiệu chuẩn.
- RQ1–RQ3 có câu trả lời (G4, `runs/final_g4_20261112/r1/test/all.score.json`, 318 dòng):
  - RQ1: `b1` Acc 0,006; RAG phẳng 0,30–0,34, TVER 0,54.
  - RQ2: `proposed2` 0,667 so với `b4` 0,324, `b5`/`b6` 0,31–0,34.
  - RQ3: lợi ích đến từ kho phiên bản + lọc: `b7plus − b7` +0,167; `proposed2 − b7plus` +0,013 [−0,009; +0,035].
- Giả thuyết đề cương (lọc cấp phiên bản > lọc cấp văn bản) được ủng hộ.

## 2. Lệch

| # | Mục | Đề cương | Hiện trạng | CMT 24/11 |
|---|---|---|---|---|
| 1 | Cỡ bộ dữ liệu | ~1.150 câu; T3 200, T5 50 | 722 dòng / 199 lineage; T3 36 dòng (6 lineage), T5 0 | Kiểm từ kho; được dựng lại nếu chắc chắn tốt hơn |
| 2 | Kiểm định | thủ công, LLM chỉ diễn đạt câu hỏi | nhãn Q1–Q4 do AI, tác giả duyệt; đáp án ngắn do LLM | Giữ LLM sinh câu hỏi; thay AI gán nhãn bằng người |
| 3 | Kết quả | — | G4 chạy trên bản 2.0.0 nội bộ, chưa chấm lại trên bản cuối | Chờ quyết định ở mục 1, 2 |
| 4 | Miền | 4 miền | trải nhiều bộ ngành (13/11: 220/318 dòng miền "khác") | Không quan trọng |
| 5 | Hợp nhất | "có thể sai sót" | kho áp 38,7% lệnh, bổ sung 0/5.653 (`kiem-tra-kho-2411.md`) | Ghi ở giới hạn |
| 6 | Đồ thị lúc truy vấn | mở rộng theo quan hệ | 1 bước, không bao đóng bắc cầu, không Neo4j | Viết theo khung biên dịch offline |
| 7 | Bìa | MSSV 23621643 | đúng là 23521643 | — |

## 3. Nguyên nhân cỡ mẫu nhỏ (mục 1)
Không phải do kho thiếu ứng viên. Kho ứng viên `data/derived/vilextime_pool.jsonl` có 11.408 ứng viên:
T2 5.428, T6 2.806, T1 2.497, T3 476, T5 201. Phễu thật:
- Chỉ rút 374 lineage để gán, vì giới hạn công gán nhãn.
- Loại 175/374 (47%), mọi quyết định do AI (`annotation/excluded_lineages.jsonl`, `decided_by` đều là `ai_*`):
  - lỗi câu hỏi 122: `question_ambiguous` 57, `group_mismatch` 36, `unanswerable_as_asked` 19, `question_leaks` 10;
  - lỗi pháp lý / kho 89 mã: `superseded_by_other_norm` 23, `restructuring_2025` 16, `gold_wrong` 15, `reference_only` 14,
    `relocation_unclear` 12, `rename_only` 7, khác;
  - `other` 29.
- T3 (`multi_versions`): rút 33 lineage, loại 27, còn 6.

Kho ảnh hưởng tới **độ đúng** (sót sửa đổi làm T1 không thuần, đáp án có thể sai) và tới **hình dạng kho ứng
viên** (lệnh bổ sung không áp được, nên thiếu chuỗi T3 do bổ sung), nhưng điểm nghẽn về **cỡ** là công gán
nhãn và chất lượng câu hỏi.
