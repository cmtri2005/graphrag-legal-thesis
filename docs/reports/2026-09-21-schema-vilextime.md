# Dựng schema ViLexTime quanh neo thời gian

Năm trong chín tên trường mà đề cương đang dự kiến dùng — `hop_level`, `reasoning`, `used_context_ids`, `source_tuple_id`, `context_block` — **không truy được về bất kỳ bộ dữ liệu, bài báo hay framework công bố nào**; chúng là một thiết kế nội bộ mạch lạc, không phải quy ước để trích dẫn. Bốn tên còn lại (`id`, `question`, `answer`, `evidence`) là quy ước thật, nhưng `evidence` mang ba nghĩa khác nhau ở ba bộ dữ liệu nên phải nói rõ mình dùng nghĩa nào. Nghiêm trọng hơn tên trường: bảng ứng viên hiện tại (`data/derived/vilextime_pool.jsonl`, 9.331 dòng, 2.949 văn bản, 16.513 cặp gold) **chưa có trường `question`**, nên về mặt kỹ thuật nó chưa phải một bộ QA; và mỗi dòng đang gộp nhiều mốc `as_of` vào một bản ghi, trong khi toàn bộ benchmark temporal QA đã kiểm chứng được đều chọn **một bản ghi cho mỗi cặp (câu hỏi, ngày)** ([TempLAMA](https://huggingface.co/datasets/Yova/templama), [TimeQA](https://datasets-server.huggingface.co/first-rows?dataset=diwank%2Ftime-sensitive-qa&config=default&split=train)). Đóng góp mới thật sự của ViLexTime rất hẹp và nên được phát biểu đúng như vậy: **không một benchmark ML nào được kiểm chứng trong ghi chú mang validity interval ở mức bản ghi** — BSARD, COLIEE và VLegal-Bench đều thừa nhận vấn đề luật cũ trong phần văn xuôi rồi đóng băng nó vào dữ liệu ([arXiv:2108.11792](https://arxiv.org/html/2108.11792), [COLIEE 2022](https://sites.ualberta.ca/~miyoung2/Papers/COLIEE2022_summary.pdf), [arXiv:2512.14554](https://arxiv.org/html/2512.14554v5)). Báo cáo này đưa ra một schema cụ thể, kèm cách nó xử lý neo `as_of`, đáp án đổi theo thời gian, T6, chuỗi sửa đổi T3, và loại item khỏi chấm điểm mà không làm hỏng metric.

## Năm trong chín tên trường không có nguồn công bố nào

Bảng dưới là phán quyết trực tiếp trên chín tên trường đã liệt kê. "Không tìm thấy nguồn" nghĩa là các truy vấn nhắm thẳng vào tên trường đó không trả về bộ dữ liệu, bài báo hay framework nào dùng nó — đây là kết quả âm tính có giới hạn (chưa kiểm DeepEval, TruLens, LlamaIndex, và chưa tìm ở các hội nghị tiếng Trung/tiếng Việt), nhưng đủ mạnh để **không được trích dẫn như quy ước trong luận văn**.

| Trường | Có nguồn công bố? | Quy ước thật gần nhất | ViLexTime nên làm |
|---|---|---|---|
| `id` | **Có, phổ quát** | HotpotQA `id`, 2Wiki `_id`, MuSiQue `id` (`2hop__…`), CRAG `interaction_id` ([hotpot_qa](https://huggingface.co/datasets/hotpotqa/hotpot_qa), [CRAG](https://raw.githubusercontent.com/facebookresearch/CRAG/main/docs/dataset.md)) | **Giữ**, nhưng đổi sang khóa hợp thành có chứa `as_of`, theo TempLAMA `Q169814_P54_2010` ([TempLAMA](https://huggingface.co/datasets/Yova/templama)) |
| `question` | **Có, phổ quát** | HotpotQA/BSARD `question`, ALQAC `text`, VLSP-LTER `statement`, CRAG `query` ([ALQAC 2021](https://arxiv.org/pdf/2204.10717), [VLSP LTER](https://vlsp.org.vn/vlsp2023/eval/lter)) | **Bổ sung** — đây là trường đang thiếu khiến pool chưa phải bộ QA |
| `answer` | **Có, phổ quát** | ALQAC 2025 `answer`, CRAG `answer` + `alt_ans`; ở temporal QA đáp án hầu như luôn là **list** | **Giữ**, thành scalar vì mỗi bản ghi chỉ có một `as_of`; thêm `answerable` |
| `hop_level` | **Không tìm thấy nguồn nào** | HotpotQA `level` = độ khó (easy/medium/hard), GrailQA `level` = mức tổng quát hóa, CRAG `question_type` có giá trị `multi-hop`, MuSiQue nhét số hop vào prefix `id` ([2wikimultihop](https://raw.githubusercontent.com/Alab-NII/2wikimultihop/main/README.md), [GrailQA](https://raw.githubusercontent.com/dki-lab/GrailQA/main/README.md)) | **Thay hẳn.** Câu hỏi ViLexTime là tra cứu một điều khoản tại một mốc — không có hop nào. Dùng `group` (T1–T6) đã có, cộng `num_versions`/`num_transitions` dạng số |
| `evidence` | **Có, nhưng mập mờ** | GraphRAG-Bench `evidence` = mệnh đề ngôn ngữ tự nhiên; 2Wiki `evidences` = triple; StrategyQA `evidence` = id đoạn văn lồng theo annotator ([GraphRAG-Bench](https://datasets-server.huggingface.co/first-rows?dataset=GraphRAG-Bench%2FGraphRAG-Bench&config=medical&split=train), [StrategyQA](https://ar5iv.labs.arxiv.org/html/2101.02235)) | **Giữ tên, đổi cấu trúc**: từ list phẳng thành object gắn với từng transition, và nói rõ trong README rằng đây là câu lệnh sửa đổi |
| `reasoning` | **Không phải tên trường có quy ước** | MuSiQue `question_decomposition` (có cấu trúc); StrategyQA `decomposition`+`facts` (người viết); RAGBench `*_explanation` (**máy viết**, kèm `annotating_model_name`) ([MuSiQue](https://datasets-server.huggingface.co/first-rows?dataset=dgslibisey%2FMuSiQue&config=default&split=validation), [RAGBench](https://datasets-server.huggingface.co/first-rows?dataset=galileo-ai%2Fragbench&config=hotpotqa&split=test)) | **Bỏ.** Gold của ViLexTime suy ra máy móc; một blob văn xuôi sẽ do model viết và lặng lẽ trở thành một phần của nhãn. Thay bằng `derivation` có cấu trúc, máy kiểm được |
| `used_context_ids` | **Không tìm thấy nguồn nào** | RAGBench `all_utilized_sentence_keys` / `all_relevant_sentence_keys`; MuSiQue `paragraph_support_idx` ([RAGBench](https://datasets-server.huggingface.co/first-rows?dataset=galileo-ai%2Fragbench&config=hotpotqa&split=test)) | **Đổi tên** thành cặp `relevant_version_ids` / `utilized_version_ids`, theo đúng phân biệt "có thể grounding" vs "thực sự dùng" của RAGBench |
| `source_tuple_id` | **Không tìm thấy nguồn nào** | Quy ước KGQA là **query-as-provenance**: GrailQA `graph_query`+`sparql_query`+`s_expression`, LC-QuAD `SPARQL Query`, CWQ `sparql`; 2Wiki là ngoại lệ ship thẳng triple ([GrailQA](https://datasets-server.huggingface.co/first-rows?dataset=Hieuman%2Fgrail_qa&config=default&split=validation), [LC-QuAD 2.0](https://datasets-server.huggingface.co/first-rows?dataset=s-nlp%2Flc_quad2&config=default&split=train)) | **Thay** bằng `event_id` + `version_id` ổn định *và* một truy vấn TKG tái chạy được. Không dataset nào làm cả hai; làm cả hai là đóng góp có thể bảo vệ |
| `context_block` | **Không tìm thấy nguồn nào** | HotpotQA/2Wiki `context` (`[title, sentences]`); RAGBench `documents`; Ragas `reference_contexts` ([Ragas](https://docs.ragas.io/en/stable/concepts/test_data_generation/rag/)) | **Bỏ khỏi bản ghi gold.** ViLexTime thuộc họ retrieval (Family B): corpus phát hành riêng, bản ghi chỉ trỏ vào nó |

Hai hệ quả đáng nói. Thứ nhất, `hop_level` đặc biệt nguy hiểm vì `level` đã mang hai nghĩa khác nhau ở hai bộ dữ liệu lớn (độ khó ở HotpotQA, mức tổng quát hóa ở GrailQA) — dùng lại chữ `level` để chỉ số hop sẽ gây hiểu sai cho bất kỳ ai quen hai bộ đó. Thứ hai, tên `evidence` mà ViLexTime đang dùng (câu lệnh *"Sửa đổi, bổ sung khoản 1 Điều 18 như sau"*) không trùng nghĩa với bất kỳ nghĩa nào trong ba nghĩa đã công bố; nó là *câu lệnh sửa đổi*, không phải mệnh đề chứng minh đáp án. README phải nói rõ điều này.

## Một bản ghi cho mỗi cặp (điều khoản, as_of), không phải mỗi điều khoản

Thay đổi kiến trúc lớn nhất: tách làm hai tầng. `vilextime_pool.jsonl` hiện nay ở lại làm **bảng ứng viên nội bộ** (một dòng cho mỗi lineage điều khoản, giữ nguyên `versions`, dùng để lấy mẫu và tách split); bộ dữ liệu phát hành là **bảng QA** với một dòng cho mỗi cặp (điều khoản, `as_of`) — 16.513 dòng từ 9.331 ứng viên. Đây là lựa chọn của mọi benchmark temporal QA đã kiểm chứng: TempLAMA phát ra cùng một `query` một lần cho mỗi năm kèm `id` hậu tố năm; TimeQA tạo bản ghi riêng với hậu tố `idx` khác cho mỗi ràng buộc thời gian trên cùng một trang ([TempLAMA](https://huggingface.co/datasets/Yova/templama), [TimeQA](https://datasets-server.huggingface.co/first-rows?dataset=diwank%2Ftime-sensitive-qa&config=default&split=train)). Giá phải trả là lặp chuỗi câu hỏi; lợi ích là mỗi dòng tự nó chấm điểm được.

Bản ghi dưới đây dùng dữ liệu thật: Khoản 1 Điều 18 Thông tư 16/2012/TT-NHNN, một chuỗi T3 bốn phiên bản với ba lần sửa đổi.

```jsonc
{
  // ── Định danh ────────────────────────────────────────────────────────────
  "schema_version": "1.0.0",              // [BẮT BUỘC][v1] xem cảnh báo ở mục versioning
  "id": "vilextime:T3:16-2012-TT-NHNN:art18_cl1:2021-11-21",
                                          // [BẮT BUỘC][v1] khóa hợp thành: group,
                                          //   law_id, đường dẫn điều khoản, as_of.
                                          //   Theo TempLAMA "Q169814_P54_2010".
  "lineage_id": "provision:3bf55646-e172-11f0-8230-79cf6a670840#k1",
                                          // [BẮT BUỘC][v1] gom 4 dòng cùng điều khoản
  "group": "T3",                          // [BẮT BUỘC][v1] T1..T6, thay cho hop_level
  "split": "test",                        // [BẮT BUỘC][v1] dev|test|test_contested|excluded
  "num_versions": 4,                      // [TÙY CHỌN][v1] thay phần "hop" của hop_level
  "num_transitions": 3,                   // [TÙY CHỌN][v1]

  // ── Câu hỏi ──────────────────────────────────────────────────────────────
  "question": "Tính đến ngày 21/11/2021, khoản 1 Điều 18 Thông tư 16/2012/TT-NHNN quy định như thế nào?",
                                          // [BẮT BUỘC][v1] TRƯỜNG ĐANG THIẾU
  "question_template_id": "as_of_provision_text.v1",
                                          // [BẮT BUỘC][v1] theo Test of Time, giữ tham
                                          //   số sinh làm trường hạng nhất; và theo cặp
                                          //   question/machine_question của CWQ
  "as_of": "2021-11-21",                  // [BẮT BUỘC][v1] neo thời gian, ISO 8601.
                                          //   Không benchmark nào dùng đúng tên "as_of";
                                          //   gần nhất là TempLAMA/TEMPREASON `date`
                                          //   và StreamingQA `question_ts`.

  // ── Đơn vị pháp lý được hỏi ──────────────────────────────────────────────
  "target": {                             // [BẮT BUỘC][v1]
    "law_id": "16/2012/TT-NHNN",          // số hiệu văn bản — quy ước ALQAC/VLSP/Zalo
    "doc_type": "Thông tư",               // theo `"type": "law"` của VLSP-LTER, mở rộng
                                          //   cho Luật/Nghị định/Thông tư
    "article_id": "18",                   // quy ước ALQAC `article_id`
    "clause_id": "1",                     // MỞ RỘNG THẬT: không bộ VN nào có Khoản
    "point_id": null,                     // MỞ RỘNG THẬT: không bộ VN nào có Điểm
    "provision_path": "Điều 18 › Khoản 1",// theo `description` của BSARD (chuỗi tiêu đề)
    "provision_id": "provision:3bf55646-e172-11f0-8230-79cf6a670840#k1",
    "akn_ref": "/akn/vn/act/2012-05-25/16-2012-TT-NHNN/vie:2021-11-21/!main~art_18__para_1"
                                          // [TÙY CHỌN][v1] MINH HỌA, không phải trích
                                          //   từ spec. Dấu ":" là "virtual expression"
                                          //   = phiên bản gần nhất trước ngày đó —
                                          //   đúng ngữ nghĩa tra cứu TKG.
  },

  // ── Đáp án ───────────────────────────────────────────────────────────────
  "answer": "1. Các văn bản, tài liệu trong hồ sơ quy định tại Mục 3 Thông tư này, trừ trường hợp hồ sơ cấp phép theo cơ chế một cửa quốc gia, phải là bản chính hoặc bản sao được cấp từ sổ gốc …",
                                          // [BẮT BUỘC][v1] null khi answerable=false
  "answerable": true,                     // [BẮT BUỘC][v1] boolean tường minh, vì bài
                                          //   học SQuAD 2.0: schema chỉ báo hiệu bằng
                                          //   list rỗng thì bị script tiền xử lý làm hỏng
  "no_answer_reason": null,               // [BẮT BUỘC][v1] từ vựng đóng:
                                          //   not_yet_in_force | provision_repealed |
                                          //   document_repealed | out_of_corpus
  "in_force": true,                       // [BẮT BUỘC][v1] cờ hiệu lực TÁCH RIÊNG —
                                          //   thay cho việc nhét "KHÔNG CÒN HIỆU LỰC"
                                          //   vào answer
  "version_id": "version:3bf55646-e172-11f0-8230-79cf6a670840#k1:3",
  "valid_from": "2021-11-20",             // [BẮT BUỘC][v1] tên theo ví dụ SQL:2011
  "valid_to":   "2023-02-15",             // [BẮT BUỘC][v1] nửa mở [from, to)

  // ── Dẫn xuất: thay cho `reasoning` ───────────────────────────────────────
  "derivation": {                         // [BẮT BUỘC][v1]
    "transitions": [                      // MỖI transition là MỘT object — actor, event,
                                          //   evidence, ngày nằm cùng chỗ, không bao giờ
                                          //   lệch nhau (đối chiếu MuSiQue
                                          //   question_decomposition: cấu trúc hóa lý do,
                                          //   đừng viết văn xuôi)
      { "on": "2016-02-15", "from_version": 1, "to_version": 2,
        "event_id": "event:96223:3d6c034aa9aa475d54ac2874",
        "actor": { "law_id": "38/2015/TT-NHNN", "document_id": "document:96223",
                   "effective_from": "2016-02-15" },
        "evidence": "Sửa đổi, bổ sung khoản 1 Điều 18 như sau",
        "evidence_kind": "amend_replace" },
      { "on": "2021-11-20", "from_version": 2, "to_version": 3,
        "event_id": "event:149987:9fc3f29d8b312b8192ba29c9",
        "actor": { "law_id": "15/2021/TT-NHNN", "document_id": "document:149987",
                   "effective_from": "2021-11-20" },
        "evidence": "Sửa đổi, bổ sung khoản 1 Điều 18 như sau",
        "evidence_kind": "amend_replace" },
      { "on": "2023-02-15", "from_version": 3, "to_version": 4,
        "event_id": "event:158757:371fafa93f8acf0fa1f030ac",
        "actor": { "law_id": "24/2022/TT-NHNN", "document_id": "document:158757",
                   "effective_from": "2023-02-15" },
        "evidence": "Sửa đổi, bổ sung khoản 1 Điều 18  như sau",
        "evidence_kind": "amend_replace" }
    ],
    "query": "as_of(provision:3bf55646-…#k1, 2021-11-21)"
                                          // [TÙY CHỌN][v1] truy vấn TKG tái chạy được —
                                          //   theo GrailQA/LC-QuAD/CWQ ship logical form
                                          //   để regrade sau khi rebuild graph
  },
  "relevant_version_ids": ["…:1", "…:2", "…:3", "…:4"],
                                          // [TÙY CHỌN][v1] mọi phiên bản của lineage
  "utilized_version_ids": ["…:3"],        // [TÙY CHỌN][v1] phiên bản gold thực dùng.
                                          //   Cặp này theo RAGBench all_relevant_* /
                                          //   all_utilized_*

  // ── Nguồn ────────────────────────────────────────────────────────────────
  "source_url": "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=27581",
  "retrieved_at": "2026-09-14",           // [BẮT BUỘC][v1] cặp url + timestamp của
                                          //   Pile of Law là tiền lệ duy nhất ở mức bản ghi
  "snapshot_sha256": null,                // [TÙY CHỌN][HOÃN] Croissant khuyến nghị sha256
                                          //   cho mỗi FileObject; cần lưu snapshot trước
  "jurisdiction": "VN", "language": "vi", // [TÙY CHỌN][v1]

  // ── Kiểm định thủ công ───────────────────────────────────────────────────
  "review": {                             // [BẮT BUỘC][v1] — KHÔNG có tiền lệ mức bản ghi
                                          //   ở bất kỳ bộ nào; đây là superset có chủ ý
    "status": "adjudicated",              // unchecked|agreed|disputed|adjudicated
    "labels": [ {"annotator": "A1", "correct": true},
                {"annotator": "A2", "correct": true} ],
                                          // ship nhãn thô để bên thứ ba tự tính kappa
    "adjudicator": "LGL1",                // mã giả danh, không phải tên thật (ARR B4)
    "guideline_version": "1.0",
    "note": ""
  },

  // ── Cờ mô tả ─────────────────────────────────────────────────────────────
  "flags": [],                            // [BẮT BUỘC][v1] list từ vựng có kiểm soát,
                                          //   theo BIG-bench `keywords` / HELM `tags`.
                                          //   Ví dụ: kg_unreproducible, text_ocr_suspect,
                                          //   retroactive_152, near_duplicate
  "similarity": null                      // [TÙY CHỌN][v1] chỉ T4; tham số sinh, giữ lại
                                          //   theo kiểu graph_gen_algorithm của Test of Time
}
```

Những gì cố tình **hoãn sang v2**: `snapshot_sha256` (cần hạ tầng lưu snapshot trước), `question_zh`/đa ngữ, `alt_ans` (đáp án ViLexTime là văn bản luật nguyên văn, không có alias), `pipeline_commit` ở mức bản ghi (chỉ đáng có nếu build tăng dần; bản freeze một lần thì để ở descriptor), và `canary` GUID (ở README + metadata file, không ở mỗi dòng).

## Chuỗi ba lần sửa đổi đang làm lệch actor, evidence và transition

Năm tình huống mà audit nêu, và cách schema trên xử lý từng cái:

**Neo `as_of`.** Hiện neo nằm trong `gold[n].as_of` — lồng bên trong, không truy vấn phẳng được. Đưa nó lên thành cột `as_of` ở mức bản ghi là chính xác điều mà khảo sát temporal QA chỉ trích các bộ khác vì thiếu: TimeQA *"lacks temporal metadata annotations"*, TEMPREASON *"covers 634–2023 but lacks temporal metadata, hindering focus-time estimation"* ([arXiv:2505.20243](https://arxiv.org/html/2505.20243v1)). Không bộ nào dùng đúng tên `as_of`; `date` (TempLAMA, TEMPREASON) và `question_ts` (StreamingQA) là gần nhất. `as_of` vẫn là lựa chọn tốt hơn vì nó khớp ngữ nghĩa `FOR SYSTEM_TIME AS OF` của SQL:2011 và không mơ hồ như `date`.

**Đáp án đổi theo thời gian.** Một dòng cho mỗi `as_of` giải quyết trọn: `answer` thành scalar, `valid_from`/`valid_to` nói khoảng nào đáp án đó đúng. Cần ghi rõ trong README rằng khoảng là **nửa mở `[from, to)`** — đây là ngữ nghĩa SQL:2011, và cũng đúng chỗ những lỗi lệch một ngày hay sống trong luật (nghị định "có hiệu lực từ 01/01" thay cái kết thúc "31/12"). Lưu ý tính bất định: nguồn duy nhất phát biểu thẳng closed-open là bài Wikipedia về SQL:2011 và một bài khảo sát, còn bài khảo sát đó **nói rõ là tài liệu không khẳng định tính bao/mở của biên** — cần đối chiếu văn bản chuẩn trước khi trích như chuẩn mực trong luận văn.

**"Điều khoản không còn tồn tại" (T6).** Hiện chuỗi `KHÔNG CÒN HIỆU LỰC` được ghép vào ô answer trong `scripts/check/sample_question_pool.py` (dòng 108). Trong pool thì `gold` đã đúng — `{"in_force": false, "version_id": null, "text": null}` — nên lỗi nằm ở worksheet, không ở dữ liệu; nhưng nếu schema phát hành không có cờ riêng thì lỗi đó sẽ lan vào bộ dữ liệu. Schema trên tách làm ba trường dư thừa có chủ ý: `answer: null`, `answerable: false`, `in_force: false`, cộng `no_answer_reason: "provision_repealed"`. Ba trường vì lịch sử SQuAD 2.0 là lập luận cho chính nó: bản HuggingFace **bỏ hẳn** boolean `is_impossible` và chỉ báo bằng list rỗng ([squad_v2](https://huggingface.co/datasets/rajpurkar/squad_v2)), còn TimeQA dùng chuỗi canh `"[unanswerable]"` ngay trong list đáp án ([ar5iv 2108.06314](https://ar5iv.labs.arxiv.org/html/2108.06314)) — cả hai đều gộp mọi lý do vào một rọ. Với benchmark này, **lý do chính là thứ đang được đo**: hệ thống trả "không có đáp án" vì không tìm thấy điều khoản không làm cùng việc với hệ thống truy được một lần bãi bỏ. `no_answer_reason` là trường không có tiền lệ nào trong QA và cũng là trường mang đóng góp thật.

**Chuỗi nhiều lần sửa đổi (T3).** Đây là lỗi nặng nhất và nó tái hiện được ngay trên dữ liệu hiện có. Với `vilextime:T3:provision:3bf55646-…#k1`:

| Đang có (list phẳng, chỉ mục i) | `event_ids[i]` | `evidence[i]` | `actor_numbers[i]` |
|---|---|---|---|
| i=0 | event:149987 (15/2021) | "Sửa đổi, bổ sung khoản 1 Điều 18 như sau" | 15/2021/TT-NHNN |
| i=1 | event:158757 (24/2022) | "Sửa đổi, bổ sung khoản 1 Điều 18  như sau" | 24/2022/TT-NHNN |
| i=2 | event:96223 (38/2015) | "Sửa đổi, bổ sung khoản 1 Điều 18 như sau" | 38/2015/TT-NHNN |

`event_ids` là `sorted(set(...))` — sắp theo **chuỗi**, nên event:96223 rơi xuống cuối dù nó là lần sửa **đầu tiên** (2016-02-15). `actor_numbers` là một `sorted(set)` **độc lập**, nên `actor_numbers[i]` không ánh xạ sang `event_ids[i]` theo thứ tự thời gian. Ba ngày chuyển tiếp thật là 2016-02-15 ← 38/2015, 2021-11-20 ← 15/2021, 2023-02-15 ← 24/2022 — tức thứ tự đúng là chỉ mục 2, 0, 1. Ngoài ra `transition_on` là **một** giá trị vô hướng ("2023-02-15") trong khi chuỗi có ba chuyển tiếp. Và worksheet ghép tất cả bằng `" | "` và `", "`, nên người kiểm nhìn thấy ba câu gần như giống hệt cạnh ba số hiệu văn bản xếp sai thứ tự — không cách nào đối chiếu. Cách sửa rẻ và máy móc: `derivation.transitions` là list object, mỗi object gói `on`, `from_version`, `to_version`, `event_id`, `actor`, `evidence` cùng một chỗ. Dữ liệu đã có sẵn — prefix của `event_id` chính là `document_id` của văn bản sửa đổi, và `effective_from` của văn bản đó bằng đúng ngày chuyển tiếp. Không phải thu thập thêm gì, chỉ là không làm phẳng nữa.

**Loại item khỏi chấm điểm.** Ghi chú rất dứt khoát ở đây: không benchmark nào chuẩn hóa ngữ nghĩa loại-trừ-lúc-chấm, và mẫu hình quan sát được là **loại trừ mang tính cấu trúc** — item có tranh chấp đi vào split/config/subset khác để metric mặc định không bao giờ nhìn thấy nó. Một cờ mà scorer được *tin* là sẽ tôn trọng thì một nửa người dùng downstream sẽ lặng lẽ bỏ qua. Vì vậy: `flags` để **giải thích**, `split` để **thi hành**. Một item mà TKG hiện tại không tái dựng được mang `flags: ["kg_unreproducible"]` *và* ship trong file `excluded`, không nằm trong `test`. Cần nói thẳng: không tìm thấy benchmark nào công bố cờ "hệ thống tham chiếu không tái dựng được" ở mức item — đây là một khoảng trống chưa ai phục vụ, không phải một quy ước để dẫn nguồn. Về kiểu trường, `flags` dạng list từ vựng có kiểm soát là cơ chế chất lượng mức item duy nhất có tiền lệ liên-benchmark thật, qua BIG-bench `keywords` và HELM `tags` ([BIG-bench](https://github.com/google/BIG-bench/blob/main/docs/doc.md), [HELM](https://crfm-helm.readthedocs.io/en/latest/code/)) — an toàn hơn là phát minh năm boolean.

Về `review`: không một bộ nào trong số đã kiểm mang metadata annotator ở mức item. ALQAC chỉ nói *"verified by legal experts"*; VLegal-Bench báo cáo IAA 92,39% (9.656/10.450), Cohen's κ = 0,89, 7,61% tranh chấp *"resolved through consensus or senior adjudication"* — tất cả **trong bài báo**, không trong schema ([arXiv:2204.10717](https://arxiv.org/pdf/2204.10717), [arXiv:2512.14554](https://arxiv.org/html/2512.14554v5)). Tiền lệ gần nhất về chính sách là CUAD: *"Each annotation was verified by three additional annotators"* ([arXiv:2103.06268](https://arxiv.org/abs/2103.06268)). Thiết kế an toàn là làm **superset**: giữ thống kê tổng hợp trong bài báo theo đúng chuẩn VLegal-Bench (đang là mức cao nhất của mảng tiếng Việt) và thêm trường mức item để ai bỏ qua vẫn parse được file. Ship **nhãn thô trước hòa giải**, không chỉ kappa — đó là thứ cho phép bên thứ ba tính lại độ đồng thuận. Dùng mã giả danh chứ không tên thật.

## Tách theo văn bản, đánh số phiên bản ở hai trục

Khóa gom nhóm để tách split phải là **văn bản nguồn**, không phải câu hỏi. Hai câu hỏi sinh từ cùng một Điều là gần-trùng lặp dưới mắt một mô hình truy hồi; tách chúng sang hai bên là rò rỉ. Với ViLexTime điều này còn mạnh hơn: cùng một `lineage_id` sinh ra 2–4 dòng QA chỉ khác `as_of` và khác nhau đúng một đoạn văn bản — nếu `as_of=2016-02-16` nằm ở train còn `as_of=2021-11-21` nằm ở test thì mô hình đã thấy 90% đáp án. Vậy nên **gom ở hai mức**: mọi dòng cùng `lineage_id` phải cùng split (bắt buộc), và mọi lineage cùng `document_id` nên cùng split (khuyến nghị, chống rò rỉ giữa các điều khoản của cùng văn bản). 2.949 văn bản cho 9.331 ứng viên là đủ hạt để làm điều này mà không làm lệch tỷ lệ T1–T6. Ghi chú cho biết tách theo nhóm là phòng thủ rò rỉ có tài liệu trong phương pháp luận nhưng **không spec nào bắt buộc**, và không tìm thấy benchmark NLP lớn nào công bố hẳn một trường "khóa gom nhóm dùng để tách" — nên `lineage_id` là lựa chọn cục bộ có thể bảo vệ, không phải chuẩn.

Cấu trúc split nên đi theo cả hai mẫu hình vì chúng không mâu thuẫn: **phân hoạch file là hợp đồng phát hành** (HuggingFace ánh xạ file→split trong YAML README; Croissant mô hình split thành RecordSet kiểu `cr:Split`), còn **trường `split` trong bản ghi là hợp đồng phân tích** (HELM đặt `split` thẳng lên `Instance`; CRAG đặt `split` là số nguyên trong record) ([HF](https://huggingface.co/docs/hub/datasets-manual-configuration), [Croissant](https://docs.mlcommons.org/croissant/docs/croissant-spec.html), [HELM](https://crfm-helm.readthedocs.io/en/latest/code/), [CRAG](https://raw.githubusercontent.com/facebookresearch/CRAG/main/docs/dataset.md)). File là thẩm quyền; trường là tiện lợi và là checksum chống trộn nhầm. Với ViLexTime, tập giá trị nên là `dev` / `test` / `test_contested` / `excluded`, trong đó `test` là thứ duy nhất metric mặc định nhìn thấy. Về tỷ lệ: T1 là nhóm đối chứng nên phải có mặt ở mọi split; GrailQA là tiền lệ đáng mượn cho slice zero-shot — giữ hẳn một số lĩnh vực/văn bản ra khỏi dev để đo tổng quát hóa ([GrailQA](https://ar5iv.labs.arxiv.org/html/2011.07743)).

Versioning cần **hai trường ở hai tầng, không phải một**. Croissant tách rõ "file này tuân theo spec nào" (`dct:conformsTo`) khỏi "đây là bản phát hành nào của dữ liệu" (`version`), và bắt buộc `version` + `datePublished` ([Croissant](https://docs.mlcommons.org/croissant/docs/croissant-spec.html)). Cảnh báo quan trọng: **không spec nào định nghĩa `schema_version` ở mức từng bản ghi** — cả Croissant lẫn Frictionless đều đặt version ở mức descriptor/package, và không tìm thấy thẩm quyền nào ủng hộ việc đóng dấu `schema_version` lên mỗi dòng. Nó là quy ước thực dụng phổ biến trong các bản phát hành JSONL, giữ được (rẻ, hữu ích khi trộn file), nhưng đừng trình bày nó như chuẩn.

Cái gì là thay đổi **breaking**? Hai spec bất đồng và cách đọc an toàn hơn cho một benchmark là của Frictionless: bất cứ thay đổi nào parser của người dùng có thể vấp đều là MAJOR.

| Thay đổi | Croissant | Frictionless | Kết luận cho ViLexTime |
|---|---|---|---|
| Đổi serialization (JSONL → Parquet) | PATCH | MAJOR nếu đổi `type`/`format` trường | **MAJOR** |
| Thêm trường mới, dữ liệu cũ vẫn lấy được | MINOR | MINOR (thêm resource/dữ liệu) | MINOR |
| Đổi tên hoặc sắp xếp lại trường | — | **MAJOR** | MAJOR |
| Sửa lỗi trong dữ liệu đã có | MAJOR (dữ liệu bị sửa) | PATCH | **MAJOR** — với benchmark, sửa gold là đổi nhãn |
| **Xáo lại item giữa các split** | **MAJOR** | — | **MAJOR**. Đây là luật nặng ký nhất: tư cách split là một phần của hợp đồng công khai, tách lại là breaking dù mọi item y nguyên từng byte |
| Thêm mã mới vào `no_answer_reason` | MINOR | MINOR | MINOR |
| Gán lại item giữa các mã `no_answer_reason` đã có | MAJOR | — | **MAJOR** |

Từ vựng `no_answer_reason` vì vậy phải được đánh số phiên bản cùng `guideline_version`. Ngoài ra, nếu đích đến là NeurIPS: metadata Croissant là **bắt buộc và có chế tài desk-reject**, và từ 2026 trường RAI trong file Croissant cũng trở thành bắt buộc ([NeurIPS 2025 D&B CFP](https://neurips.cc/Conferences/2025/CallForDatasetsBenchmarks), [NeurIPS blog 05/2026](https://blog.neurips.cc/2026/05/04/responsible-ai-metadata-requirements-for-the-evaluations-and-datasets-track-neurips-2026/)). Đường lười nhất là host trên HuggingFace Hub với khối `configs:` đúng chuẩn trong README — Croissant được sinh tự động ([NeurIPS blog 03/2025](https://blog.neurips.cc/2025/03/10/neurips-datasets-benchmarks-raising-the-bar-for-dataset-submissions/)). Và thêm chuỗi canary GUID kiểu BIG-bench vào README để chống rò vào corpus huấn luyện web-scraped ([BIG-bench](https://github.com/google/BIG-bench/blob/main/docs/doc.md)).

Một điểm cuối cùng về provenance: `retrieved_at` không phải trang trí. Nó là trục **transaction time** bên cạnh trục **valid time** của `valid_from`/`valid_to` — SQL:2011 gọi hai trục này là application-time period và system-time period, và bảng có cả hai là bitemporal ([SQL:2011](https://en.wikipedia.org/wiki/SQL:2011)). Valid time trả lời "Điều X có hiệu lực ngày D không" — câu hỏi benchmark đặt ra. Transaction time trả lời "bản crawl cổng luật của chúng tôi tin gì vào ngày dựng gold" — câu hỏi người phản biện đặt ra khi cổng đã được sửa từ đó. Thiếu trục thứ hai, một chỉnh sửa hồi tố ở thượng nguồn biến gold đúng thành gold sai mà không cách nào biết item nào bị ảnh hưởng. Với ViLexTime điều này sắc hơn bình thường vì T5 (hồi tố theo Điều 152) chính là lớp item mà hai trục lệch nhau theo thiết kế.

## Đóng góp mới nằm ở validity interval được công bố ở mức bản ghi

Phát biểu đóng góp phải hẹp và chính xác, nếu không nó sai. **Không** phải "chưa ai để ý luật cũ" — đến 2026 đã có nhiều bài. Bài về statutory QA tiếng Đức có 312 cặp QA nhạy thời gian được chuyên gia thẩm định, chia ba loại Post-Cutoff Amendment / Pre-Amendment / Multi-Provision Pre-Amendment, và giảm thiểu bằng "fact date extraction and version filtering" trong RAG ([arXiv:2605.23497](https://arxiv.org/abs/2605.23497)). **Cũng không** phải "chưa ai dựng KG sửa đổi cho luật Việt Nam" — VLegal-Bench có Knowledge Graph Database mã hóa hệ thống Điều/Khoản/Điểm và theo dõi "amendments, replacements" cùng "temporal relations among legal documents" ([arXiv:2512.14554](https://arxiv.org/html/2512.14554v5)).

Đóng góp còn lại, và nó vẫn đứng vững: trong toàn bộ các bộ dữ liệu đã kiểm chứng ở mức trường, **không bộ nào mang validity interval mức bản ghi, con trỏ "as amended by", hay cờ phân biệt bản gốc với bản hợp nhất**. Cách xử lý thời gian phổ biến là đóng băng rồi chú thích: BSARD nói thẳng văn bản thu thập tháng 5/2021 và *"both the questions and articles correspond to an outdated version of the Belgian law from May 2021"* — **cảnh báo nằm trong bài báo, `articles.csv` không có cột ngày nào** ([arXiv:2108.11792](https://arxiv.org/html/2108.11792)). COLIEE ghim Bộ luật Dân sự Nhật "(updated in 2020)" ở 768 điều, cũng bằng văn xuôi ([COLIEE 2022](https://sites.ualberta.ca/~miyoung2/Papers/COLIEE2022_summary.pdf)). VLegal-Bench có KG thời gian nhưng tự thừa nhận *"the benchmark itself is static"* — cấu trúc thời gian nằm trong KG, không trong bản ghi benchmark ([arXiv:2512.14554](https://arxiv.org/html/2512.14554v5)). Thêm vào đó, cấp độ Khoản/Điểm tự nó đã là mở rộng thật: mọi bộ dữ liệu pháp luật tiếng Việt đã công bố định danh điều khoản bằng đúng hai chuỗi — `law_id` (số hiệu văn bản) và `article_id` (số điều trần) — không version, không ngày, không đường dẫn con ([ALQAC 2021](https://arxiv.org/pdf/2204.10717), [VLSP LTER](https://vlsp.org.vn/vlsp2023/eval/lter), [Zalo LTR](https://github.com/hieudx149/ZaloAI2021_LTR/blob/main/README.md)).

Hai giới hạn phải nêu cùng lúc với phát biểu đó. Thứ nhất, khẳng định là về **benchmark ML**, không về cơ sở dữ liệu pháp luật: legislation.gov.uk, Lexis/Westlaw và chính vbpl.vn đều phục vụ văn bản point-in-time, nhưng không được khảo sát ở đây như *dataset*. Thứ hai, **tên trường của benchmark tiếng Đức chưa được xác minh** — abstract không in schema và bản full-text HTML chưa được tải; không được khẳng định bộ đó không có trường validity. Tương tự, bản phát hành chính thức của TimeQA (Google Drive) có thể mang nhiều trường hơn bản mirror trên HuggingFace, và ghi chú đánh dấu đây là **prior art liên quan nhất, cần kiểm trực tiếp repo TimeQA trước khi đóng băng v1**. LEXAM, CALRK-Bench, STaRK, FreshQA, MenatQA, SituatedQA, TIQ, TempTabQA và TRAM đều chưa xác minh được schema. Ví dụ Akoma Ntoso cho luật Việt Nam trong bản ghi trên là **minh họa do người viết dựng theo template `art_5__para_2` của spec** ([AKN-NC v1.0 §4.6](https://docs.oasis-open.org/legaldocml/akn-nc/v1.0/akn-nc-v1.0.html)), không phải trích dẫn; và mẫu URI template của ELI không tải được (irishstatutebook.ie trả HTTP 403) — chỉ tên thuộc tính trong `eli.owl` là đã xác minh.

## Kết luận

Đường ngắn nhất từ pool hiện tại đến một bộ QA phát hành được không phải là viết thêm trường, mà là **ngừng làm phẳng**. Ba defect nặng nhất — thiếu `question`, gộp nhiều `as_of` vào một dòng, và ba list song song `event_ids`/`evidence`/`actor_numbers` được sắp xếp độc lập — đều là lỗi hình dạng, không phải lỗi dữ liệu: mọi thông tin cần thiết đã nằm trong `data/temporal.sqlite` và trong pool, kể cả ánh xạ actor→transition (prefix của `event_id` chính là `document_id`, và `effective_from` của văn bản đó chính là ngày chuyển tiếp). Chi phí sửa là viết lại một hàm dựng bản ghi, không phải chú giải lại 9.331 ứng viên.

Điều đáng cân nhắc hơn là thứ tự công việc. `review` và `flags` chỉ có giá trị nếu được điền *trong lúc* hai người kiểm và cố vấn pháp lý làm việc — nhãn thô trước hòa giải là thứ không thể khôi phục sau khi đã hòa giải xong, và đó chính là thứ cho phép bên thứ ba tính lại kappa thay vì phải tin con số trong bài báo. Vì đợt hand-check chưa diễn ra, đây là cửa sổ duy nhất để làm đúng. Ngược lại, `no_answer_reason` và `flags` là hai từ vựng đóng mà việc gán lại item giữa các mã sau khi phát hành sẽ là thay đổi MAJOR — nên chúng phải được chốt *trước* đợt kiểm, không phải sau. Còn `snapshot_sha256`, `pipeline_commit` mức bản ghi và slice zero-shot theo lĩnh vực thì hoãn được mà không mất gì: chúng cộng vào một bản ghi đã đúng hình dạng, không sửa một bản ghi đã sai.
