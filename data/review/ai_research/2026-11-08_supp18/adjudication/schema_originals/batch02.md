# supp18 batch02 — AI adjudication

Official cache reads are distinguished from live requests. The result remains not_verified and requires human adjudication.

```json
{
  "agent": "Codex native legal-adjudicator /root/supp_adj02",
  "model": "inherited; exact model/revision unknown; not Claude",
  "guideline_version": "4.0",
  "skills": [
    "legal-adjudicator repository agent",
    "vilextime-ai-labeling (version field absent)",
    "vn-legal-research (version field absent)",
    "karpathy-guidelines (version field absent)"
  ],
  "input_file": "data/review/ai_research/2026-11-08_supp18/adjudication/input/batch02.jsonl",
  "input_sha256": "64f154996450c10463d01bf9de4c4e89d5605bbbb84647dc179f30049a6ea206",
  "source_cache_read_at": "2026-11-08T15:26:07Z",
  "cache_original_fetch_times": "unknown",
  "source_cache_sha256": {
    "32442": "dbee6d424fc23950d0e3b8facb74046ee73c648f232027ed087352da4511d7b1",
    "75724": "5189c5588f1cf0d671680d2aefa0e4fcd115070176726296e961138d166e6316",
    "36870": "2c5e2f225b6434a0a784b6746dca84ee75825fe864be1f1610f8f1b6b2dbe181"
  },
  "tools_available_used": [
    "functions.exec",
    "exec_command (cat/sed/rg/wc/python3)",
    "web.run search_query/open",
    "clock.curr_time"
  ],
  "lawgical_available": false,
  "lawgical_calls": 0,
  "live_external_calls": 2,
  "live_external_budget": 15,
  "live_external_remaining": 13,
  "errors": [
    "python command unavailable; reran with python3",
    "web.open official btllang.bqp.vn page returned 400 Timeout fetching"
  ],
  "source_access": [
    "packet official excerpts",
    "read-only official cache 32442 and 75724",
    "SQLite read-only exact-number metadata route 52/2014/QH13 -> 36870; no evidence from database",
    "official cache 36870"
  ],
  "blindness": "Only assigned input/batch02.jsonl with frozen A/B labels; no peer adjudication outputs or system predictions read. Frozen raw hash fields copied as supplied, not claimed recomputed from unavailable original raw files.",
  "validation": {
    "records_expected": 1,
    "records_written": 1,
    "worksheet_binding_matches": true,
    "copied_binding_fields_match": true,
    "side_match": "all four Q and four reasons exactly A; B differs at Q3",
    "schema_taxonomy_and_verdict": "validate_label passed",
    "quote_cache_matches": true
  },
  "counts": {
    "prefer_a": 1,
    "prefer_b": 0,
    "both_wrong": 0,
    "unresolved": 0,
    "sufficient": 1,
    "insufficient": 0,
    "unavailable": 0
  }
}
```

Bounded official sections read in full:

```json
{
  "32442_Điều48": "Điều 48. Hành vi vi phạm quy định về cấm kết hôn, vi phạm chế độ hôn nhân một vợ, một chồng; vi phạm quy định về ly hôn\n1. Phạt tiền từ 1.000.000 đồng đến 3.000.000 đồng đối với một trong các hành vi sau:\na) Đang có vợ hoặc đang có chồng mà kết hôn với người khác, chưa có vợ hoặc chưa có chồng mà kết hôn với người mà mình biết rõ là đang có chồng hoặc đang có vợ;\nb) Đang có vợ hoặc đang có chồng mà chung sống như vợ chồng với người khác;\nc) Chưa có vợ hoặc chưa có chồng mà chung sống như vợ chồng với người mà mình biết rõ là đang có chồng hoặc đang có vợ;\nd) Kết hôn giữa những người có họ trong phạm vi ba đời;\nđ) Kết hôn giữa cha mẹ nuôi với con nuôi;\ne) Kết hôn giữa người đã từng là cha mẹ nuôi với con nuôi, bố chồng với con dâu, mẹ vợ với con rể, bố dượng với con riêng của vợ, mẹ kế với con riêng của chồng.\n2. Phạt tiền từ 10.000.000 đồng đến 20.000.000 đồng đối với hành vi lợi dụng việc ly hôn để vi phạm chính sách, pháp luật về dân số hoặc để trốn tránh nghĩa vụ tài sản.",
  "32442_Điều74": "Điều 74. Hiệu lực thi hành\n1. Nghị định này có hiệu lực thi hành từ ngày 11 tháng 11 năm 2013 và thay thế Nghị định số 60/2009/NĐ-CP ngày 23 tháng 7 năm 2009 của Chính phủ quy định về xử phạt vi phạm hành chính trong lĩnh vực tư pháp; Nghị định số 87/2001/NĐ-CP ngày 21 tháng 11 năm 2001 của Chính phủ về xử phạt vi phạm hành chính trong lĩnh vực hôn nhân và gia đình; Nghị định số 10/2009/NĐ-CP ngày 06 tháng 02 năm 2009 của Chính phủ quy định xử phạt vi phạm hành chính trong quá trình tiến hành thủ tục phá sản.\n2. Đối với hành vi vi phạm hành chính trong lĩnh vực bổ trợ tư pháp, hành chính tư pháp, hôn nhân và gia đình, thi hành án dân sự, phá sản doanh nghiệp, hợp tác xã xảy ra trước thời điểm Nghị định này có hiệu lực mà sau đó mới bị phát hiện hoặc đang xem xét, giải quyết thì áp dụng Nghị định của Chính phủ về xử phạt vi phạm hành chính có hiệu lực tại thời điểm thực hiện hành vi vi phạm để xử lý. Trường hợp các quy định về xử phạt vi phạm hành chính trong Nghị định này có lợi cho cá nhân, tổ chức vi phạm hành chính thì áp dụng các quy định của Nghị định này để xử lý.\n3. Đối với quyết định xử phạt vi phạm hành chính đã được ban hành hoặc đã được thi hành xong trước thời điểm Nghị định này có hiệu lực thi hành, mà cá nhân, tổ chức bị xử phạt vi phạm hành chính còn khiếu nại thì áp dụng quy định của Pháp lệnh xử lý vi phạm hành chính, Nghị định số 60/2009/NĐ-CP ngày 23 tháng 7 năm 2009 của Chính phủ quy định về xử phạt vi phạm hành chính trong lĩnh vực tư pháp, Nghị định số 87/2001/NĐ-CP ngày 21 tháng 11 năm 2001 của Chính phủ về xử phạt vi phạm hành chính trong lĩnh vực hôn nhân và gia đình; Nghị định số 10/2009/NĐ-CP ngày 06 tháng 02 năm 2009 của Chính phủ quy định xử phạt vi phạm hành chính trong quá trình tiến hành thủ tục phá sản.",
  "75724_Điều1_khoản35": "35. Sửa đổi tên Điều 48, Điểm d, Điểm đ, Điểm e Khoản 1, Điểm a Khoản 2 và bổ sung Điểm b Khoản 2 Điều 48 như sau:\n“Điều 48. Hành vi vi phạm quy định về kết hôn, ly hôn và vi phạm chế độ hôn nhân một vợ, một chồng\n1. Phạt tiền từ 1.000.000 đồng đến 3.000.000 đồng đối với một trong các hành vi sau:\nd) Kết hôn hoặc chung sống như vợ chồng giữa những người có họ trong phạm vi ba đời;\nđ) Kết hôn hoặc chung sống như vợ chồng giữa cha mẹ nuôi với con nuôi;\ne) Kết hôn hoặc chung sống như vợ chồng giữa người đã từng là cha, mẹ nuôi với con nuôi, bố chồng với con dâu, mẹ vợ với con rể, bố dượng với con riêng của vợ, mẹ kế với con riêng của chồng;\n2. Phạt tiền từ 10.000.000 đồng đến 20.000.000 đồng đối với một trong các hành vi sau:\na) Lợi dụng việc ly hôn để trốn tránh nghĩa vụ tài sản, vi phạm chính sách, pháp luật về dân số hoặc để đạt được mục đích khác mà không nhằm mục đích chấm dứt hôn nhân;\nb) Kết hôn hoặc chung sống như vợ chồng với người có cùng dòng máu về trực hệ.”",
  "75724_Điều2": "Điều 2. Hiệu lực và trách nhiệm tổ chức thực hiện\n1. Nghị định này có hiệu lực thi hành kể từ ngày 01 tháng 10 năm 2015.\n2. Các Bộ trưởng, Thủ trưởng cơ quan ngang Bộ, Thủ trưởng cơ quan thuộc Chính phủ, Chủ tịch Ủy ban nhân dân các tỉnh, thành phố trực thuộc Trung ương chịu trách nhiệm tổ chức thực hiện Nghị định này./.",
  "36870_Điều5": "Điều 5. Bảo vệ chế độ hôn nhân và gia đình\n1. Quan hệ hôn nhân và gia đình được xác lập, thực hiện theo quy định của Luật này được tôn trọng và được pháp luật bảo vệ.\n2. Cấm các hành vi sau đây:\na) Kết hôn giả tạo, ly hôn giả tạo;\nb) Tảo hôn, cưỡng ép kết hôn, lừa dối kết hôn, cản trở kết hôn;\nc) Người đang có vợ, có chồng mà kết hôn hoặc chung sống như vợ chồng với người khác hoặc chưa có vợ, chưa có chồng mà kết hôn hoặc chung sống như vợ chồng với người đang có chồng, có vợ;\nd) Kết hôn hoặc chung sống như vợ chồng giữa những người cùng dòng máu về trực hệ; giữa những người có họ trong phạm vi ba đời; giữa cha, mẹ nuôi với con nuôi; giữa người đã từng là cha, mẹ nuôi với con nuôi, cha chồng với con dâu, mẹ vợ với con rể, cha dượng với con riêng của vợ, mẹ kế với con riêng của chồng;\nđ) Yêu sách của cải trong kết hôn;\ne) Cưỡng ép ly hôn, lừa dối ly hôn, cản trở ly hôn;\ng) Thực hiện sinh con bằng kỹ thuật hỗ trợ sinh sản vì mục đích thương mại, mang thai hộ vì mục đích thương mại, lựa chọn giới tính thai nhi, sinh sản vô tính;\nh) Bạo lực gia đình;\ni) Lợi dụng việc thực hiện quyền về hôn nhân và gia đình để mua bán người, bóc lột sức lao động, xâm phạm tình dục hoặc có hành vi khác nhằm mục đích trục lợi.\n3. Mọi hành vi vi phạm pháp luật về hôn nhân và gia đình phải được xử lý nghiêm minh, đúng pháp luật.\nCơ quan, tổ chức, cá nhân có quyền yêu cầu Tòa án, cơ quan khác có thẩm quyền áp dụng biện pháp kịp thời ngăn chặn và xử lý người có hành vi vi phạm pháp luật về hôn nhân và gia đình.\n4. Danh dự, nhân phẩm, uy tín, bí mật đời tư và các quyền riêng tư khác của các bên được tôn trọng, bảo vệ trong quá trình giải quyết vụ việc về hôn nhân và gia đình.",
  "36870_Điều131": "Điều 131. Điều khoản chuyển tiếp\n1. Quan hệ hôn nhân và gia đình được xác lập trước ngày Luật này có hiệu lực thì áp dụng pháp luật về hôn nhân và gia đình tại thời điểm xác lập để giải quyết.\n2. Đối với vụ việc về hôn nhân và gia đình do Tòa án thụ lý trước ngày Luật này có hiệu lực mà chưa giải quyết thì áp dụng thủ tục theo quy định của Luật này.\n3. Không áp dụng Luật này để kháng nghị theo thủ tục giám đốc thẩm, tái thẩm đối với vụ việc mà Tòa án đã giải quyết theo quy định của pháp luật về hôn nhân và gia đình trước ngày Luật này có hiệu lực.",
  "36870_Điều132": "Điều 132. Hiệu lực thi hành\nLuật này có hiệu lực thi hành từ ngày 01 tháng 01 năm 2015.\nLuật Hôn nhân và gia đình số 22/2000/QH10 hết hiệu lực kể từ ngày Luật này có hiệu lực."
}
```

Adjudication:

```json
{
  "case_id": "supp18-006",
  "run_id": "supp18",
  "lineage_id": "provision:c45fe1a8-df43-11f0-9a1c-277c000beaf7#k1#e",
  "worksheet_sha256": "160a564adb8fe848a21c47b1681a3e776e9e7c4a1f101afd2187d9b94b6d07a0",
  "raw_a_sha256": "bb72ca86c9194d502d8886b6dc17b969c7925523f7a2dbca7cc98b55152d7a74",
  "raw_b_sha256": "a36dcb71264d004307e3fc7b648c916baab8725b391e193d416530443e28d3b2",
  "disputed_fields": [
    "q3",
    "q3_reason"
  ],
  "disposition": "prefer_a",
  "proposed_label": {
    "q1": "dung",
    "q1_reason": "",
    "q2": "co",
    "q2_reason": "",
    "q3": "khong",
    "q3_reason": "question_ambiguous",
    "q4": "khong",
    "q4_reason": "",
    "verdict": "khong_dat",
    "quote": "e) Kết hôn hoặc chung sống như vợ chồng giữa người đã từng là cha, mẹ nuôi với con nuôi, bố chồng với con dâu, mẹ vợ với con rể, bố dượng với con riêng của vợ, mẹ kế với con riêng của chồng;",
    "search_log": "Đã mở cache chính thức 32442: toàn Điều 48 và Điều 74; 75724: toàn khoản 35 Điều 1 và Điều 2; kiểm Luật cấp cao hơn 52/2014/QH13 tại cache 36870: Điều 5, 131, 132. SQLite chỉ định tuyến đúng số hiệu 52/2014/QH13 sang ItemID 36870, không dùng nội dung kho làm chứng cứ. Live web search site:vbpl.vn \"52/2014/QH13\" \"Điều 5\" \"Điều 133\" trả locator; mở cổng btllang.bqp.vn bị timeout, không dùng snippet làm bằng chứng. Hai mốc 2015 không thuộc sắp xếp 2025. T2 nên bước chuyển chỗ T6 không áp dụng.",
    "note": "Câu hỏi không giới hạn cha mẹ nuôi ở người đã từng là cha mẹ nuôi; mức phạt 1–3 triệu chung cho cả điểm đ và e, nên đáp án chỉ điểm e không duy nhất. Điều 5 Luật 52/2014 quy định cấm, không đặt mức phạt hành chính đang hỏi. Điều 131 của Luật giữ luật cũ cho quan hệ xác lập trước 01/01/2015; đề bài coi sự việc phát sinh tại hai mốc 2015 nên không kích hoạt chuyển tiếp.",
    "evidence_status": "sufficient",
    "evidence": [
      {
        "url": "https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/32442",
        "source_tier": "official",
        "document_number": "110/2013/NĐ-CP",
        "provision": "Điều 48 khoản 1 điểm đ, e",
        "as_of": "2015-09-30",
        "quote": "đ) Kết hôn giữa cha mẹ nuôi với con nuôi;\ne) Kết hôn giữa người đã từng là cha mẹ nuôi với con nuôi, bố chồng với con dâu, mẹ vợ với con rể, bố dượng với con riêng của vợ, mẹ kế với con riêng của chồng.",
        "accessed_at": "2026-11-08T15:26:07Z",
        "access_method": "official cached source data/raw/32442.json through official_text.text_of; no live fetch of this URL",
        "source_cached_at": "unknown"
      },
      {
        "url": "https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/32442",
        "source_tier": "official",
        "document_number": "110/2013/NĐ-CP",
        "provision": "Điều 74 khoản 1",
        "as_of": "2015-09-30",
        "quote": "Nghị định này có hiệu lực thi hành từ ngày 11 tháng 11 năm 2013",
        "accessed_at": "2026-11-08T15:26:07Z",
        "access_method": "official cached source data/raw/32442.json through official_text.text_of; no live fetch of this URL",
        "source_cached_at": "unknown"
      },
      {
        "url": "https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/75724",
        "source_tier": "official",
        "document_number": "67/2015/NĐ-CP",
        "provision": "Điều 1 khoản 35 sửa điểm đ, e khoản 1 Điều 48",
        "as_of": "2015-10-01",
        "quote": "đ) Kết hôn hoặc chung sống như vợ chồng giữa cha mẹ nuôi với con nuôi;\ne) Kết hôn hoặc chung sống như vợ chồng giữa người đã từng là cha, mẹ nuôi với con nuôi, bố chồng với con dâu, mẹ vợ với con rể, bố dượng với con riêng của vợ, mẹ kế với con riêng của chồng;",
        "accessed_at": "2026-11-08T15:26:07Z",
        "access_method": "official cached source data/raw/75724.json through official_text.text_of; no live fetch of this URL",
        "source_cached_at": "unknown"
      },
      {
        "url": "https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/75724",
        "source_tier": "official",
        "document_number": "67/2015/NĐ-CP",
        "provision": "Điều 2 khoản 1",
        "as_of": "2015-10-01",
        "quote": "Nghị định này có hiệu lực thi hành kể từ ngày 01 tháng 10 năm 2015.",
        "accessed_at": "2026-11-08T15:26:07Z",
        "access_method": "official cached source data/raw/75724.json through official_text.text_of; no live fetch of this URL",
        "source_cached_at": "unknown"
      },
      {
        "url": "https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/36870",
        "source_tier": "official",
        "document_number": "52/2014/QH13",
        "provision": "Điều 5 khoản 2 điểm d",
        "as_of": "2015-09-30;2015-10-01",
        "quote": "d) Kết hôn hoặc chung sống như vợ chồng giữa những người cùng dòng máu về trực hệ; giữa những người có họ trong phạm vi ba đời; giữa cha, mẹ nuôi với con nuôi; giữa người đã từng là cha, mẹ nuôi với con nuôi, cha chồng với con dâu, mẹ vợ với con rể, cha dượng với con riêng của vợ, mẹ kế với con riêng của chồng;",
        "accessed_at": "2026-11-08T15:26:07Z",
        "access_method": "official cached source data/raw/36870.json through official_text.text_of; no live fetch of this URL",
        "source_cached_at": "unknown"
      },
      {
        "url": "https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/36870",
        "source_tier": "official",
        "document_number": "52/2014/QH13",
        "provision": "Điều 132",
        "as_of": "2015-09-30;2015-10-01",
        "quote": "Luật này có hiệu lực thi hành từ ngày 01 tháng 01 năm 2015.",
        "accessed_at": "2026-11-08T15:26:07Z",
        "access_method": "official cached source data/raw/36870.json through official_text.text_of; no live fetch of this URL",
        "source_cached_at": "unknown"
      }
    ]
  },
  "reasoning": "Q1: cả hai đáp án đầy đủ và đoạn ngắn trùng điểm e bản ban hành và bản sửa theo khoản 35 Điều 1 NĐ 67/2015; Điều 74 NĐ 110 và Điều 2 NĐ 67 xác nhận các mốc. Q2: thêm hành vi chung sống như vợ chồng vào đúng các quan hệ câu hỏi nêu là thay đổi thực chất; hai mốc cho nội dung khác nhau. Q3: A được chứng minh: câu hỏi nêu cha mẹ nuôi với con nuôi nhưng không nói đã từng, nên điểm đ khoản 1 Điều 48 cũng trả lời được; mức tiền chung không phân biệt điểm đ với điểm e. B đánh giá Q3 co không được chứng minh. Cụm bố mẹ vợ chồng chỉ thu hẹp một phần, không loại nhánh cha mẹ nuôi hiện tại. Theo bước 3 phải chọn question_ambiguous, không chọn lỗi đáp án ngắn. Q4: đã đọc Luật HNGĐ 52/2014 có hiệu lực 01/01/2015; Điều 5 cấm cả kết hôn và chung sống, nhưng câu hỏi ghim chế tài tiền hành chính 1–3 triệu nên điều cấm không thay phạm vi chế tài trước khi NĐ 67 có hiệu lực. Điều 131 không buộc chính sự việc mới tại hai as_of theo luật cũ. Không có yếu tố cơ quan/địa danh cũ hay chuyển chỗ T6. Đánh giá cả Q/reason khớp A, nên prefer_a; đây là đề xuất AI chưa được người xác nhận.",
  "evidence": [
    {
      "url": "https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/32442",
      "source_tier": "official",
      "document_number": "110/2013/NĐ-CP",
      "provision": "Điều 48 khoản 1 điểm đ, e",
      "as_of": "2015-09-30",
      "quote": "đ) Kết hôn giữa cha mẹ nuôi với con nuôi;\ne) Kết hôn giữa người đã từng là cha mẹ nuôi với con nuôi, bố chồng với con dâu, mẹ vợ với con rể, bố dượng với con riêng của vợ, mẹ kế với con riêng của chồng.",
      "accessed_at": "2026-11-08T15:26:07Z",
      "access_method": "official cached source data/raw/32442.json through official_text.text_of; no live fetch of this URL",
      "source_cached_at": "unknown"
    },
    {
      "url": "https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/32442",
      "source_tier": "official",
      "document_number": "110/2013/NĐ-CP",
      "provision": "Điều 74 khoản 1",
      "as_of": "2015-09-30",
      "quote": "Nghị định này có hiệu lực thi hành từ ngày 11 tháng 11 năm 2013",
      "accessed_at": "2026-11-08T15:26:07Z",
      "access_method": "official cached source data/raw/32442.json through official_text.text_of; no live fetch of this URL",
      "source_cached_at": "unknown"
    },
    {
      "url": "https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/75724",
      "source_tier": "official",
      "document_number": "67/2015/NĐ-CP",
      "provision": "Điều 1 khoản 35 sửa điểm đ, e khoản 1 Điều 48",
      "as_of": "2015-10-01",
      "quote": "đ) Kết hôn hoặc chung sống như vợ chồng giữa cha mẹ nuôi với con nuôi;\ne) Kết hôn hoặc chung sống như vợ chồng giữa người đã từng là cha, mẹ nuôi với con nuôi, bố chồng với con dâu, mẹ vợ với con rể, bố dượng với con riêng của vợ, mẹ kế với con riêng của chồng;",
      "accessed_at": "2026-11-08T15:26:07Z",
      "access_method": "official cached source data/raw/75724.json through official_text.text_of; no live fetch of this URL",
      "source_cached_at": "unknown"
    },
    {
      "url": "https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/75724",
      "source_tier": "official",
      "document_number": "67/2015/NĐ-CP",
      "provision": "Điều 2 khoản 1",
      "as_of": "2015-10-01",
      "quote": "Nghị định này có hiệu lực thi hành kể từ ngày 01 tháng 10 năm 2015.",
      "accessed_at": "2026-11-08T15:26:07Z",
      "access_method": "official cached source data/raw/75724.json through official_text.text_of; no live fetch of this URL",
      "source_cached_at": "unknown"
    },
    {
      "url": "https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/36870",
      "source_tier": "official",
      "document_number": "52/2014/QH13",
      "provision": "Điều 5 khoản 2 điểm d",
      "as_of": "2015-09-30;2015-10-01",
      "quote": "d) Kết hôn hoặc chung sống như vợ chồng giữa những người cùng dòng máu về trực hệ; giữa những người có họ trong phạm vi ba đời; giữa cha, mẹ nuôi với con nuôi; giữa người đã từng là cha, mẹ nuôi với con nuôi, cha chồng với con dâu, mẹ vợ với con rể, cha dượng với con riêng của vợ, mẹ kế với con riêng của chồng;",
      "accessed_at": "2026-11-08T15:26:07Z",
      "access_method": "official cached source data/raw/36870.json through official_text.text_of; no live fetch of this URL",
      "source_cached_at": "unknown"
    },
    {
      "url": "https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/36870",
      "source_tier": "official",
      "document_number": "52/2014/QH13",
      "provision": "Điều 132",
      "as_of": "2015-09-30;2015-10-01",
      "quote": "Luật này có hiệu lực thi hành từ ngày 01 tháng 01 năm 2015.",
      "accessed_at": "2026-11-08T15:26:07Z",
      "access_method": "official cached source data/raw/36870.json through official_text.text_of; no live fetch of this URL",
      "source_cached_at": "unknown"
    }
  ],
  "open_questions": [],
  "labeler": "ai-adjudicator",
  "label_origin": "ai",
  "verification_status": "not_verified",
  "human_adjudication_required": true,
  "guideline_version": "4.0"
}
```
