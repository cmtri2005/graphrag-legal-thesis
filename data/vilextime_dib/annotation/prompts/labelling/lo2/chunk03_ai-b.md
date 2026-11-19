Lượt nhãn ViLexTime. labeler = `ai-b`. Phiên: `2026-11-08_lo2/chunk03.jsonl/ai-b`.
Gốc repo: /home/trica/UIT_Thesis/graphrag-legal-thesis

## Chỉ được đọc
1. `docs/vilextime-dinh-nghia.md` (sha256 bb506aa679888907f29f6af2480c6ee66ea451296137e1d78c57cb5245ca122e): định nghĩa, thắng khi mâu thuẫn.
2. `docs/vilextime-annotation.md` (sha256 b92275cdfeb8c194d9a1c8e275c7fbfa80c06d4bc6b75a1a22f69cd81e25a72a): thẻ 4.0, đọc §1–§4 và §7.
3. `data/review/ai_research/2026-11-08_lo2/input/chunk03.jsonl` (sha256 641fc285fcf92384012b39870ef04fda452612acae1cc4eb723f2939f0920d40), 15 dòng. Mỗi dòng có:
   `worksheet_sha256` (binding, chép nguyên), `record` (phiếu), `official` (đoạn toàn văn chính
   thức lấy sẵn từ CSDL quốc gia về pháp luật: điều được hỏi ở bản ban hành; điều hiệu lực,
   chuyển tiếp hoặc toàn văn của văn bản tác động), `official_missing` (đoạn không lấy được).
4. Nguồn ngoài, theo ngân sách bên dưới.
Không mở file nào khác trong repo (manifest, `raw/`, `a.jsonl`, `b.jsonl`, TSV, `runs/`, git…).

## Cách làm cho đỡ tốn
- Đọc hết input một lần bằng Read (đọc theo đoạn nếu file dài). Căn cứ chính là `record` và
  `official`; đoạn `official` có `source_tier` = `official`.
- Ngày hiệu lực lấy từ lời văn điều hiệu lực, không lấy từ trường ngày trong phiếu.
- Tra ngoài chỉ khi cần cho Q4 (quy phạm khác đè lên, chuyển chỗ, sắp xếp bộ máy) hoặc khi
  `official` thiếu thứ cần. Ngân sách cả phiên: tối đa 6 lượt WebSearch/WebFetch.
  Gộp nhiều lệnh tra vào cùng một lượt khi được. Toàn văn văn bản khác:
  WebFetch `https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/<ItemID>`.
  Không WebFetch trang vbpl.vn (chỉ trả khung trống). Lawgical không có trong runtime agent.
- Không đủ căn cứ thì vẫn chọn Q1–Q4 tốt nhất, ghi `[phân vân]` ở note và `evidence_status`
  = `insufficient`. Không bịa quote hay URL.

## Đầu ra (chỉ trả lời, không ghi file)
1. Một khối ```jsonl đúng 15 dòng theo schema skill `vilextime-ai-labeling`: `labeler`="ai-b",
   `label_origin`="ai", `verification_status`="not_verified", `guideline_version`="4.0".
   - `quote`: nguyên văn một câu từ văn bản tác động (bắt buộc).
   - `search_log`: bắt buộc khi T6 và q4=khong.
   - `note`: tối đa 2 câu, nêu lý do quyết định; dài hơn chỉ khi `[phân vân]`. Bắt buộc khi
     q1_reason=other hoặc q4_reason ∈ {relocated, relocation_unclear}.
   - `evidence`: 1–2 mục quyết định nhất, mỗi mục có `source_tier`
     (`official` | `worksheet` | `secondary` | `snippet`), quote ngắn.
   - Reason đúng bảng: q1 sai→gold_wrong|reference_only|other; q2 khong→group_mismatch|cosmetic_only|rename_only|auto_reference_update;
     q3 khong→question_ambiguous|unanswerable_as_asked|question_leaks; q4 co→superseded_by_other_norm|restructuring_2025|transitional_rule|relocated;
     q4 khong_chac→relocation_unclear. Đáp án đạt thì reason rỗng.
2. Một khối ```json provenance ngắn: phiên, model, input sha256, số lượt web, lỗi truy cập, độ mù
   (`blind` hoặc `blinding_compromised` kèm lý do).
Không viết tóm tắt văn xuôi ngoài hai khối trên.
