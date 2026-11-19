Lượt nhãn ViLexTime. labeler = `ai-b`. Phiên: `2026-11-11_t1_labels/chunk01.jsonl/ai-b`.
Gốc repo: /home/trica/UIT_Thesis/graphrag-legal-thesis

## Chỉ được đọc
1. `docs/vilextime-dinh-nghia.md` (sha256 bb506aa679888907f29f6af2480c6ee66ea451296137e1d78c57cb5245ca122e): định nghĩa, thắng khi mâu thuẫn.
2. `docs/vilextime-annotation.md` (sha256 e18ee6c7dd9f8a7ec2a9556310f9250dd8b83cb6931b5322e208b5c3f03866cf): thẻ 4.0, đọc §1–§4 và §7. Lô này toàn nhóm T1 (đối chứng không làm hại): BẮT BUỘC đọc kỹ mục "T1 đối chứng" ở §3. Q2 với T1 = điều khoản có thật sự không đổi/không bị sửa không (chỉ một phiên bản từ ngày hiệu lực đến mốc; không văn bản nào sửa, thay thế hay bãi bỏ nó hoặc điều khoản cấp trên trước mốc; văn bản còn hiệu lực tại mốc). Có lần sửa hay bãi bỏ mà phiếu không ghi → Q2 = khong, `group_mismatch`, ghi văn bản tác động ở `note`. Bãi bỏ đến mốc cũng làm Q2 = khong.
3. `data/review/ai_research/2026-11-11_t1_labels/input/chunk01.jsonl` (sha256 ed7fbed4b313d0cf90df48e1dfa4803832937bf3746d3ba94f1774a15173bbcb), 30 dòng. Mỗi dòng có:
   `worksheet_sha256` (binding, chép nguyên), `record` (phiếu), `official` (đoạn toàn văn chính
   thức lấy sẵn từ CSDL quốc gia về pháp luật: điều được hỏi ở bản ban hành; điều hiệu lực,
   chuyển tiếp hoặc toàn văn của văn bản tác động), `official_missing` (đoạn không lấy được).
4. Nguồn ngoài, theo ngân sách bên dưới.
Không mở file nào khác trong repo (manifest, `raw/`, `a.jsonl`, `b.jsonl`, TSV, `runs/`, git…).

## Cách làm cho đỡ tốn
- Đọc hết input một lần bằng Read (đọc theo đoạn nếu file dài). Căn cứ chính là `record` và
  `official`; đoạn `official` có `source_tier` = `official`.
- Với T1, `official` chỉ có điều được hỏi ở bản ban hành; hiệu lực/sửa đổi phải tra ngoài. Ngày hiệu lực lấy từ lời văn điều hiệu lực, không lấy từ trường ngày trong phiếu.
- Tra ngoài chỉ khi cần cho Q4 (quy phạm khác đè lên, chuyển chỗ, sắp xếp bộ máy) hoặc khi
  `official` thiếu thứ cần. Ngân sách cả phiên: tối đa 10 lượt (T1 cần tra xem có văn bản sửa/bãi bỏ điều khoản không; gộp nhiều điều vào một lượt) WebSearch/WebFetch.
  Gộp nhiều lệnh tra vào cùng một lượt khi được. Toàn văn văn bản khác:
  WebFetch `https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/<ItemID>`.
  Không WebFetch trang vbpl.vn (chỉ trả khung trống). Lawgical không có trong runtime agent.
- Không đủ căn cứ thì vẫn chọn Q1–Q4 tốt nhất, ghi `[phân vân]` ở note và `evidence_status`
  = `insufficient`. Không bịa quote hay URL.

## Đầu ra (chỉ trả lời, không ghi file)
1. Một khối ```jsonl đúng 30 dòng theo schema skill `vilextime-ai-labeling`: `labeler`="ai-b",
   `label_origin`="ai", `verification_status`="not_verified", `guideline_version`="4.0".
   - `quote`: nguyên văn một câu (bắt buộc). T1 không có văn bản tác động: trích câu từ điều được hỏi (đoạn `official` bản ban hành); nếu tìm thấy văn bản sửa/bãi bỏ thì trích câu từ văn bản đó.
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
