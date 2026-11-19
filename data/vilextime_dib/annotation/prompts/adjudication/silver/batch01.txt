Thực hiện vai trò .claude/agents/legal-adjudicator.md cho đúng 5 ca.
Đọc đúng file agent, hai skill .claude/skills/vn-legal-research/SKILL.md và
.claude/skills/vilextime-ai-labeling/SKILL.md (đọc trực tiếp, không dựa vào preload),
docs/vilextime-dinh-nghia.md và docs/vilextime-annotation.md.
Chỉ đọc thêm packet data/review/ai_research/2026-11-07_adjudication_all/input/batch01.jsonl; không đọc nhãn/lô/kết quả hệ khác.
Packet có nhãn thô đã đóng băng, binding và hash. Trọng tài được xem cả A/B.
Đây là phạm vi Q1–Q4 VÀ mã reason khác nhau, hoặc unresolved cũ cần tra lại.
Không mặc định phiếu dài hơn hoặc đa số là đúng. Tự đối chiếu đủ bốn Q,
giải thích rõ lập luận A/B nào được nguồn chứng minh/bác bỏ, từng mốc.
Mở lại nguồn thật bằng WebFetch/WebSearch; API vbpl có thể lấy với ItemID
từ sources của record. official trong packet là excerpt đã lấy từ nguồn gốc,
không phải kiểm chứng độc lập mới; ghi rõ khi chỉ đọc excerpt. Pilot có thể thiếu
official, cần mở URL gốc. Kiểm nội dung điều hiệu lực, không dùng metadata ngày.
Lawgical không có trong runtime này: ghi rõ, dùng web/API nguồn chính thức.
Ngân sách mềm khoảng 15 lượt web/lô; ưu tiên gộp nguồn chung, nhưng cần thì tra đủ.
Nếu công cụ không mở nguồn hoặc chính sách gán còn thiếu, ghi unresolved thật,
không tự tạo quy tắc và không chọn A/B cho đủ số. Nếu một lỗi độc lập đã chắc
để loại dòng nhưng Q khác còn thiếu nguồn, vẫn ghi thiếu nguồn của nhãn đầy đủ;
không gọi cả phiếu sufficient chỉ vì verdict chắc chắn.

Chỉ trả MỘT khối ```jsonl gồm đúng 5 object theo thứ tự packet,
không viết file. Mỗi object gồm:
case_id,run_id,lineage_id,worksheet_sha256,raw_a_sha256,raw_b_sha256 (chép từ packet),
disputed_fields (chép từ packet), disposition prefer_a|prefer_b|both_wrong|unresolved,
proposed_label null nếu chưa đủ căn cứ, nếu đề xuất đầy đủ thì gồm
q1,q1_reason,q2,q2_reason,q3,q3_reason,q4,q4_reason,verdict,quote,search_log,note,
evidence_status và evidence. Giữ nguyên taxonomy thẻ 4.0 (không sáng tác reason).
verdict dat CHỈ khi dung/co/co/khong. Các câu thuận lợi reason rỗng.
Mỗi evidence có url thực đã mở, source_tier official|worksheet|secondary|snippet,
document_number,provision,as_of,quote nguyên văn ngắn,accessed_at (unknown nếu không biết).
Nếu đã đủ để giải quyết, evidence_status=sufficient; nếu không unresolved,
proposed_label có thể null hoặc phiếu tentative insufficient được đánh dấu rõ.
reasoning: tiếng Việt ngắn gọn nhưng nêu từng điểm tranh chấp, đối chiếu A và B.
evidence: các nguồn quyết định đã mở (không bịa URL), open_questions: danh sách còn thiếu.
labeler=ai-adjudicator,label_origin=ai,verification_status=not_verified,
human_adjudication_required=true. Không giả luật sư hoặc xác nhận CMT.
Sau đó MỘT khối ```json provenance: agent/model thực, input file, web calls,
nguồn lỗi, giới hạn, mốc truy cập; nếu không biết thì unknown. Không chép placeholder.
