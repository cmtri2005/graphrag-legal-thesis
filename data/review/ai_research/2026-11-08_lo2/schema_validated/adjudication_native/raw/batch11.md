```jsonl
{"case_id": "lo2-049", "run_id": "lo2", "lineage_id": "provision:592f6e64-e171-11f0-88ed-ff9450fdb79b#k3", "worksheet_sha256": "d64c7f4c993ecd6514461c001b593c1014debfedfae82e7da3ef5c3fc232b371", "raw_a_sha256": "99009642da6e5c1bd4e5955f87e05690ecb67c633fc14557690fb1e38fd56ddf", "raw_b_sha256": "66feb4ebbba4ad7ba2c61316de79566688eaab3c32fbaf430660d5794f684752", "disputed_fields": ["q2", "q2_reason"], "disposition": "unresolved", "proposed_label": null, "reasoning": "Nguồn chính thức chốt được phần A và B cùng nhận định: khoản 2 Điều 18 TT11/2017 gắn hiệu lực nhiệm vụ của Tổng cục Phòng, chống thiên tai tại Điều 5 với Quyết định chức năng; Điều 5 QĐ26/2017 ghi 18/08/2017, nên đáp án thứ ba áp nhiệm vụ mới ở 18/07/2017 là sớm. Q3 cũng không ghim lĩnh vực: nhiều khoản Điều 3 cùng trả lời được. Riêng Q2, A theo dõi nội dung thủy sản: sau sửa đổi nội dung ấy chuyển từ khoản 3 sang khoản 4, nên không tính đổi số thành trạng thái thứ ba theo R1. B nhìn ba đoạn tại vị trí khoản 3 và chọn co. Với câu hỏi chung đã không đạt Q3, thẻ chưa chốt cách chọn đơn vị nội dung để đếm trạng thái T3 khi lineage giữ số khoản nhưng chủ đề bị chuyển chỗ. Không tự tạo quy tắc giải nghĩa Q2 để chọn A/B; giữ nhãn đầy đủ chưa chốt dù đã có lỗi Q1 và Q3 chắc chắn.", "evidence": [{"url": "https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/124607", "source_tier": "official", "document_number": "11/2017/TT-BNNPTNT", "provision": "Khoản 2 Điều 18; Điều 5 sửa Điều 3 TT16/2011", "as_of": "2017-07-18", "quote": "Những quy định về nhiệm vụ của Tổng cục Thủy lợi; Tổng cục Phòng, chống thiên tai được quy định tại Điều 2, Điều 5, Điều 6, Điều 9 của Thông tư này có hiệu lực thi hành cùng thời điểm với hiệu lực của Quyết định của Thủ tướng Chính phủ quy định chức năng, nhiệm vụ, quyền hạn và cơ cấu tổ chức của Tổng cục Thủy lợi; Tổng cục Phòng, chống thiên tai.", "accessed_at": "unknown", "access_method": "provided official excerpt; no new live fetch"}, {"url": "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=124736", "source_tier": "official", "document_number": "26/2017/QĐ-TTg", "provision": "Điều 5", "as_of": "2017-07-18", "quote": "Quyết định này có hiệu lực thi hành từ ngày 18 tháng 8 năm 2017.", "accessed_at": "unknown", "access_method": "cached official fulltext; no live request", "cache_path": "data/review/ai_research/2026-11-08_lo2/schema_validated/adjudication_native/full_sources/124736.txt"}], "open_questions": ["CMT/luật sư xác định cách chấm Q2 ở T3 khi câu hỏi không ghim lĩnh vực và lineage theo vị trí khoản bị thay chủ đề: đếm chuỗi nội dung thủy sản chuyển khoản hay ba đoạn khác nội dung tại cùng vị trí? R1 không tính đánh số thuần túy, nhưng cần xác định đơn vị nội dung của chính câu hỏi này trước khi áp."], "labeler": "ai-adjudicator", "label_origin": "ai", "verification_status": "not_verified", "human_adjudication_required": true}
```

```json
{
  "runtime": "Codex native, parent coordinator performing legal-adjudicator role",
  "model": "unknown",
  "shared_context_with_coordinator": true,
  "not_fresh_worker": true,
  "input": "input/batch11.jsonl",
  "input_sha256": "9193f515617a4d2ac7dd482a3a096e82657e02a6c951ee8d2bbb214da90f4099",
  "guideline_version": "4.0",
  "web_tool_calls": 1,
  "web_search_queries": 2,
  "live_scope": "Official-domain searches for QĐ26/2017 and TT16/2011 amendment history; search snippets not used as decisive legal evidence.",
  "decisive_access": "provided official TT11 excerpt and cached original QĐ26 body, with cache/live distinction explicit",
  "limitations": [
    "No fresh independent worker for this one-case packet; parent role execution disclosed.",
    "Q2 interpretation gap retained unresolved; definite failure on Q1/Q3 not used to claim full-label sufficiency."
  ],
  "date": "2026-11-08"
}
```
