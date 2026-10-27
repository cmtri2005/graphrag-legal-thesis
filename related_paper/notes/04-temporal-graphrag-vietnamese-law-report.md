# Temporal GraphRAG cho Pháp luật Việt Nam: Báo cáo Nghiên cứu Chuyên sâu (Feasibility, Gaps, and Thesis Roadmap)

> Ghi chú đọc chi tiết cho khóa luận ViLexTime. Nguồn: `related_paper/Temporal GraphRAG for Vietnamese Law_ Feasibility, Gaps, and Thesis Roadmap.pdf` (11 trang). Văn bản gốc bị lỗi dấu khi trích; các trích dẫn dưới đây đã được sửa chính tả tiếng Việt.

## 0. ĐỌC TRƯỚC: bản chất tài liệu

| Mục | Nhận định |
|---|---|
| Loại | **Không phải bài báo bình duyệt.** Là báo cáo tổng hợp kiểu "deep research" (cấu trúc TL;DR → Key Findings → Details → Recommendations → Caveats), **không có tác giả, ngày, đơn vị, danh mục tài liệu tham khảo chính thức**; trích dẫn dạng liên kết/nguồn rời trong văn bản. |
| Giá trị | Là **bản đồ tài nguyên và gợi ý lộ trình** rất sát đề tài ViLexTime; hữu ích để tìm nguồn, ý tưởng schema, danh sách baseline. |
| Cách dùng đúng | **Không trích làm nguồn học thuật.** Mỗi số liệu/khẳng định phải lần về nguồn gốc (bài báo, văn bản luật, trang vbpl.vn) và kiểm chứng lại. Chính tài liệu tự cảnh báo ở mục Caveats. |
| Rủi ro | Có thể chứa lỗi do mô hình tổng hợp (ngày tháng, số hiệu văn bản, tên công trình, nhãn năm 2026 chưa chắc đã công bố). Một số số liệu ghi "dẫn lại qua tổng hợp 2026". |

## 1. WHY – Luận điểm trung tâm (TL;DR)

- Temporal GraphRAG **khả thi và cấp thiết** cho pháp luật Việt Nam, nhưng đúng đắn nhất là **kiến trúc lai**: mô hình hóa cấu trúc phân cấp + quan hệ sửa đổi bằng đồ thị, kết hợp **lọc bi-temporal (valid time / transaction time) ở tầng metadata**, *không* phải một "temporal knowledge graph" ngữ nghĩa đầy đủ cho từng thực thể.
- Bằng chứng thực tiễn mạnh nhất cho nhu cầu **point-in-time correctness**: đợt sắp xếp đơn vị hành chính 2025 — 63 → 34 đơn vị cấp tỉnh; bỏ 696 đơn vị cấp huyện từ 01/7/2025; 5.026 văn bản QPPL cấp Trung ương chịu tác động trực tiếp.
- **Khoảng trống nghiên cứu**: chưa có bộ dữ liệu hay hệ thống GraphRAG tiếng Việt nào mô hình hóa thời gian hiệu lực ở cấp Điều/Khoản (point-in-time). Các công trình VN hiện có (SBV-LawGraph, "Applying Graph RAG" với Neo4j, hienlh/vn-legal-rag 76,3% hit rate) mới dừng ở quan hệ **tĩnh** (trích dẫn, sửa đổi), không truy vấn được "văn bản có hiệu lực vào ngày X".
- **Phạm vi khả thi cho luận văn**: một lĩnh vực hẹp (lao động hoặc thuế), bộ **~1.000–3.000 câu hỏi** có nhãn point-in-time + benchmark "temporal trap", pipeline lai trên nền **vbpl.vn** (146.766 văn bản), embedding BGE-M3/AITeamVN, Neo4j/Kùzu, chứng minh giá trị thành phần temporal bằng ablation. Ước tính đóng góp dataset + benchmark + system "vừa sức **6–12 tháng**".

## 2. Các phát hiện chính (Key Findings) và kiểm chứng

| # | Khẳng định của báo cáo | Nguồn báo cáo dẫn | Ghi chú cho người đọc |
|---|---|---|---|
| 1 | Vector RAG chuẩn "mù thời gian" — de Martim: "blind to the hierarchical, diachronic, and causal structure of law, leading to anachronistic and unreliable answers" | arXiv 2505.00039 | **Đúng với bài 2 (SAT-Graph RAG)**: câu này có trong abstract. |
| 2 | Công cụ AI pháp lý thương mại ảo giác: Lexis+ AI ~17%, Westlaw AI-Assisted Research ~33%, GPT-4 ~43% trên 202 truy vấn; "each hallucinate between 17% and 33% of the time"; "Providers' claims are overstated" | Magesh et al., "Hallucination-Free? ...", arXiv 2405.20362, JELS 2025 (Stanford RegLab/HAI) | Đo trên **hệ thống pháp lý Mỹ**, không phải VN; chỉ minh họa mức rủi ro (báo cáo tự thừa nhận). Cần kiểm gốc con số. |
| 3 | Tiền lệ quốc tế trưởng thành: UK legislation.gov.uk (Akoma Ntoso + point-in-time consolidation), EU EUR-Lex/ELI, Brazil LexML + LRMoo de Martim | — | Point-in-time là bài toán đã giải về chuẩn hóa, **chưa áp dụng cho tiếng Việt**. |
| 4 | vbpl.vn chứa **146.766 văn bản** (tính đến 1/3/2025), phơi bày metadata hiệu lực và quan hệ "văn bản liên quan"/"lược đồ" | — | Ảnh chụp tại một ngày; phải trích kèm ngày. Hai số con (44.649 TW + 102.084 địa phương = 146.733) lệch ~33 so với tổng (tài liệu tự ghi). |
| 5 | Chưa bộ NLP công khai nào (ALQAC, Zalo 2021, SoICT 2024 với 261.446 văn bản) có **nhãn thời gian** | — | Khớp với gap ViLexTime; cần xác minh lại khi viết related work. |
| 6 | Chi phí GraphRAG không còn là rào cản: Microsoft Research (2024) index bộ án lệ ~5GB bằng GraphRAG gốc có thể tới **~$33.000**; **LazyGraphRAG** (blog MSR 25/11/2024) có chi phí index "identical to vector RAG and 0.1% of the costs of full GraphRAG", query rẻ hơn "more than 700 times" | blog MSR | Số $33k là của bộ án lệ, không đo trên luật VN; chỉ để tham chiếu bậc độ lớn. |

## 3. Chi tiết nội dung (theo mục của báo cáo)

### 3.1 Tính khả thi và cần thiết
- **Failure mode do mù thời gian**: cùng câu hỏi ("mức lương tối thiểu vùng là bao nhiêu?") đáp án khác nhau theo thời điểm; vector RAG xếp hạng theo tương đồng nên có thể trả điều khoản đã sửa/bãi bỏ.
- **Phản biện trung thực**: với đa số truy vấn "as-of-today", **vector RAG + bộ lọc trường ngày_hiệu_lực/ngày_hết_hiệu_lực** đã đạt phần lớn lợi ích với chi phí thấp hơn nhiều. Temporal KG đầy đủ chỉ thực sự cần cho: (a) point-in-time quá khứ ("quy định vào 01/5/2018 là gì?"), (b) phân tích tác động phân cấp ("sửa Điều 6 ảnh hưởng những khoản nào?"), (c) truy vết lịch sử sửa đổi. Khuyến nghị: **lai** — đồ thị cho phân cấp + quan hệ sửa/bãi bỏ; versioning thời gian bằng khoảng bi-temporal ở tầng thuộc tính. Mô hình "aggregations, not compositions" của de Martim tránh bùng nổ tổ hợp.
- **Thị trường legal tech VN** (bằng chứng nhu cầu): AI Luật của LuatVietnam (v1.0.1, 38 lĩnh vực, huấn luyện trên "hàng trăm nghìn văn bản ... từ năm 1945 đến nay", tuyên bố tự cập nhật câu trả lời theo văn bản mới nhất), AI Pháp luật trên Cổng pháp luật quốc gia (ai.phapluat.gov.vn), aitracuuluat.vn, trolyluat.ai.vn, trợ lý ảo thuvienphapluat.vn. Họ quảng bá tính năng "hiệu lực" nhưng **không công bố phương pháp**; báo cáo cảnh báo đây là tuyên bố marketing chưa kiểm chứng độc lập.

### 3.2 Tổng quan tài liệu / state of the art
**de Martim (arXiv 2505.00039)**: tiến hóa qua các phiên bản — v1/v2 "Graph RAG for Legal Norms: A Hierarchical and Temporal Approach" (cảm hứng FRBRoo); v3+ thành SAT-Graph RAG (LRMoo); bản journal FAIA251598 (IOS Press). Khái niệm cốt lõi: Work vs Expression (+ Manifestation); Temporal Versions và Language Versions; Text Units (metadata được "textualize" cho multi-aspect retrieval); CTV và "aggregations, not compositions"; Action nodes; deterministic primitives với planner. Có bài kế tiếp "Deterministic Legal Retrieval: An Action API for Querying the SAT-Graph RAG" (arXiv 2510.06002). Đánh giá của de Martim là **định tính, trace-based** (xem ghi chú bài 02).

**Công trình liên quan**
- **LegalBench-RAG** (Pipitone & Houir Alami, arXiv 2408.10343): "6,858 query-answer pairs over a corpus of over 79M characters, entirely human-annotated by legal experts"; bản mini 776 cặp (194/nguồn); nguồn CUAD, MAUD, ContractNLI, PrivacyQA; nhấn mạnh trích span tối thiểu, Precision@k/Recall@k.
- **Louis, van Dijck, Spanakis "Finding the Law"** (arXiv 2301.12847, EACL 2023): G-DSR (graph-augmented dense statute retriever, GNN); dataset **BSARD** (22.600+ điều luật Bỉ, ~1.100 câu hỏi tiếng Pháp); chứng minh cấu trúc đồ thị cải thiện dense retrieval. Cùng nhóm: "Interpretable long-form legal QA with RAG LLMs" (AAAI 2024).
- Cai et al. khảo sát temporal KG (arXiv 2403.04782); khảo sát Graph RAG (arXiv 2408.08921, mục 9.2.5 ứng dụng pháp lý); Hei et al.; Barron et al.
- **Chuẩn point-in-time**: Akoma Ntoso (OASIS LegalDocML), ELI, URN:LEX; legislation.gov.uk có API CLML + Akoma Ntoso (thêm `/data.akn`), hỗ trợ "point-in-time consolidation" → tiền lệ cho thiết kế định danh tiếng Việt.

**Kiến trúc GraphRAG và biến thể**
| Hệ | Đặc điểm theo báo cáo | Đánh giá cho temporal-pháp lý |
|---|---|---|
| Microsoft GraphRAG | index → trích thực thể/quan hệ → Leiden → tóm tắt cộng đồng → local/global/DRIFT; ~$33k/5GB | community detection thuật toán **không phù hợp**; nên dùng phân cấp nội tại (Phần/Chương/Điều) làm "community" |
| LazyGraphRAG | hoãn LLM đến lúc query; index = vector RAG (0,1% chi phí); query rẻ hơn tới 700 lần; chất lượng ngang GraphRAG Global Search | rẻ |
| LightRAG (HKUDS, EMNLP 2025) | trích thực thể 1 lần/chunk, cập nhật đồ thị tăng dần (~$0,50/1M token với gpt-4o-mini), giảm ~50% thời gian update, ~80ms latency | **phù hợp** vì luật thay đổi liên tục |
| FastGraphRAG (circlemind) | PageRank lúc truy hồi; rẻ ~6× ($0,08 vs $0,48 trên "Wizard of Oz") | — |
| RAPTOR, nano-graphrag | cây tóm tắt phân cấp; bản gọn nhẹ | — |

**Temporal KG bi-temporal**: **Graphiti** (open-source, Apache-2.0, 20.000+ sao) + **Zep** (arXiv 2501.13956): mỗi cạnh có `valid_at/invalid_at` (valid time) và `created_at/expired_at` (transaction time); nguyên tắc "**invalidate, don't delete**" (đóng cửa sổ hiệu lực thay vì xóa) → point-in-time query; chạy trên Neo4j/FalkorDB/Neptune; Zep CE self-hosted đã deprecated 4/2025. Phù hợp ý tưởng cho VN: valid time = hiệu lực thực tế; transaction time = lúc hệ thống ghi nhận (quan trọng cho **hiệu lực trở về trước/hồi tố**). Lưu ý: Graphiti thiết kế cho **agent memory** (nhiều đồ thị nhỏ) → coi là **tham chiếu thiết kế mô hình**, không phải thư viện dùng trực tiếp cho corpus lớn.

### 3.3 Đặc thù hệ thống pháp luật Việt Nam (mục then chốt)

**Luật Ban hành VBQPPL 2025 (Luật số 64/2025/QH15)**: Quốc hội khóa XV thông qua 19/02/2025 (kỳ họp bất thường lần 9), hiệu lực 01/4/2025; **9 chương, 72 điều** (so với Luật 2015: giảm 8 chương, 101 điều; −53% chương, −58,4% điều). Thay đổi quan trọng: còn 25 hình thức VBQPPL (giảm 1) do 14 chủ thể ban hành (giảm 2); đổi một hình thức từ Quyết định của Tổng Kiểm toán Nhà nước sang Thông tư; bỏ thẩm quyền ban hành VBQPPL của chính quyền cấp xã (ban đầu), sau đó **Luật sửa đổi số 87/2025/QH15** (thông qua 25/6/2025, hiệu lực 01/7/2025) điều chỉnh: bổ sung Nghị quyết HĐND cấp xã, Quyết định UBND cấp xã, Quyết định Chủ tịch UBND cấp tỉnh; bỏ thẩm quyền của HĐND/UBND cấp huyện. Quy định mới về hiệu lực khi thay đổi địa giới hành chính (khoản 2 Điều 54, sửa bởi khoản 20 Điều 1 Luật 87/2025) với 4 tình huống; văn bản cấp xã và Chủ tịch UBND cấp tỉnh không được quy định hiệu lực trở về trước (khoản 21 Điều 1 Luật 87/2025 sửa khoản 3 Điều 55).

**Hệ thống thứ bậc** (cần mã hóa thành DAG, cạnh `has_higher_authority`): Hiến pháp > Bộ luật/Luật, Nghị quyết QH > Pháp lệnh, Nghị quyết UBTVQH > Lệnh, Quyết định Chủ tịch nước > Nghị định CP, Nghị quyết CP > Quyết định Thủ tướng > Thông tư (Bộ trưởng), Thông tư liên tịch > văn bản cấp tỉnh (Nghị quyết HĐND, Quyết định UBND).

**Khái niệm thời gian/hiệu lực PHẢI mô hình hóa** (Điều 152–156 Luật 2015, kế thừa trong Luật 2025):
1. **Ngày ban hành ≠ ngày có hiệu lực ≠ ngày hết hiệu lực** (ba mốc riêng).
2. Hết hiệu lực **toàn bộ vs một phần** (Điều 154): hết thời hạn; bị sửa đổi/bổ sung/thay thế; bị bãi bỏ; văn bản quy định chi tiết hết hiệu lực khi văn bản gốc hết hiệu lực.
3. **Ngưng hiệu lực** (đình chỉ thi hành) và **hiệu lực trở về trước/hồi tố** (Điều 152): chỉ cơ quan trung ương, trong trường hợp thật cần thiết bảo đảm lợi ích chung; **cấm** hồi tố khi (a) quy định trách nhiệm pháp lý mới đối với hành vi mà thời điểm thực hiện pháp luật không quy định trách nhiệm, hoặc (b) quy định trách nhiệm pháp lý nặng hơn.
4. **Văn bản hợp nhất** (Pháp lệnh Hợp nhất VBQPPL số 01/2012/UBTVQH13, sửa bởi Pháp lệnh 01/2026/UBTVQH16 — mở rộng sang văn bản địa phương và văn bản bị bãi bỏ/hết hiệu lực một phần/ngưng hiệu lực một phần). Văn bản hợp nhất = "consolidated version", nguồn point-in-time quý giá, giảm nhu cầu tự consolidation.
5. **Văn bản hướng dẫn/quy định chi tiết**: Luật 2025 mềm dẻo hơn — văn bản hướng dẫn có thể tiếp tục áp dụng nếu không trái với văn bản thay thế/sửa đổi.
6. **"Một luật sửa nhiều luật"** (ví dụ Luật 87/2025 sửa nhiều điều của Luật 64/2025): quan hệ many-to-many → phải **reify** sự kiện sửa đổi thành nút Action (một Action trỏ nhiều Work/Expression đích), không dùng cạnh đơn.

**Đợt tái cấu trúc hành chính 2025** (động lực thực tiễn mạnh nhất):
- 63 tỉnh → **34** đơn vị cấp tỉnh (28 tỉnh + 6 thành phố TW) theo Nghị quyết 60-NQ/TW (BCH TW khóa XIII, Hội nghị 11, ban hành 12/4/2025) và Nghị quyết 76/2025/UBTVQH15, hiệu lực 01/7/2025.
- Kết thúc hoạt động đơn vị cấp huyện từ 01/7/2025: **696** đơn vị (49 quận, 508 huyện, 52 thị xã, 85 thành phố thuộc tỉnh, 2 thành phố thuộc TP TW); cấp xã còn 3.321 (2.621 xã, 687 phường, 13 đặc khu).
- **5.026 văn bản QPPL cấp TW chịu tác động trực tiếp** (theo Bộ Tư pháp): 160 luật/bộ luật, 8 NQ Quốc hội, 10 pháp lệnh, 2 NQ UBTVQH, 833 nghị định, 1 NQ Chính phủ, 287 quyết định TTg, 3 chỉ thị TTg, 3.722 văn bản cấp bộ; trong đó 3.887 chỉ đổi tên cơ quan, 326 cần xử lý theo lộ trình. ~1.700 văn bản HĐND/UBND địa phương rà soát riêng; **tập ưu tiên hẹp cho mô hình chính quyền 2 cấp: 129 văn bản (49 luật, 33 nghị định, 47 thông tư)**.
- **Nghị quyết 190/2025/QH15** (hiệu lực 19/2/2025): công cụ pháp lý trung tâm xử lý chuyển tiếp, tránh "khoảng trống pháp luật".
- Các câu hỏi point-in-time điển hình: "văn bản X còn hiệu lực không sau 1/7/2025?", "quy định của tỉnh cũ áp dụng cho địa bàn mới thế nào?", "văn bản cấp huyện còn hiệu lực đến khi nào?".
- **Lưu ý của báo cáo (Caveats)**: 5.026 là toàn bộ tái cấu trúc bộ máy nhà nước (gồm cả sáp nhập bộ), không chỉ sáp nhập tỉnh/bỏ huyện.

### 3.4 Nguồn dữ liệu corpus
| Nguồn | Mô tả | Lưu ý |
|---|---|---|
| **vbpl.vn** (CSDL quốc gia, Bộ Tư pháp) | 146.766 văn bản (1/3/2025): 44.649 TW + 102.084 địa phương; mỗi văn bản có PDF, "VB liên quan", "Thuộc tính", **"Lược đồ"** (sơ đồ quan hệ sửa đổi/thay thế/hướng dẫn), "Tải về"; phiên bản mới tái cấu trúc tới cấp Điều/Khoản/Điểm, tích hợp AI | `robots.txt` cho phép crawl (chặn `/api/`); nguồn **tốt nhất và an toàn pháp lý nhất** |
| datafiles.chinhphu.vn, congbao.chinhphu.vn, quochoi.vn | nguồn chính thức uy tín | — |
| thuvienphapluat.vn, luatvietnam.vn | đầy đủ, chất lượng cao | thương mại → **rủi ro ToS** khi crawl |
| **SoICT Hackathon 2024** Legal Document Retrieval | 261.446 văn bản (Kaggle); top-3 (arXiv 2507.14619): Exist@90 97%, MRR@10 77,54% | — |
| **ALQAC 2021–2025** (KSE/ISAILD) | retrieval + QA trên luật nổi tiếng; ALQAC 2024: retrieval ~87% F2, QA ~98% accuracy | — |
| **Zalo AI Challenge 2021** | Legal Text Retrieval | dùng fine-tune embedding |
| **TVPL** (arXiv 2412.00657) | 165.334 query train + 10.000 test + 224.006 passages; 507.152 query tổng hợp bằng Llama3-70B | — |
| VLQA, ViBidLQA, ViLQA (KSE 2024), VLSP 2025 MLQA-TSR (biển báo, luật 36/2024/QH15) | — | — |
| HuggingFace | `tmquan/vbpl-vn` (document→section→paragraph→sentence, CC-BY-4.0), `YuITC/Vietnamese-Legal-Documents`, các Vietnamese-Legal-Doc-Retrieval | giấy phép CC-BY-4.0 cần **xác minh** vì dữ liệu gốc là văn bản nhà nước |

**Khoảng trống xác nhận**: không dataset công khai nào có nhãn point-in-time/temporal.

### 3.5 Đề xuất cấu trúc bộ dữ liệu
**Schema property-graph (LRMoo + bi-temporal)**
- *Node*: `LegalWork` {work_id, loại, cơ_quan_ban_hành, số_hiệu_gốc}; `Expression` {expr_id, valid_from, valid_to, transaction_from, transaction_to, trạng_thái}; `StructuralUnit` (Phần/Chương/Mục/Tiểu mục/Điều/Khoản/Điểm) {unit_id, loại, số, tiêu_đề, path}; `TextUnit` (nội dung + metadata textualized); `Action` {action_id, loại (ban hành/sửa đổi/bãi bỏ/thay thế/ngưng hiệu lực), ngày, văn_bản_nguồn}; `Concept/Term`.
- *Edge*: `has_part` (phân cấp), `has_expression`, `amends/repeals/replaces/suspends` (qua Action), `cites`, `guides/detailed_by`, `consolidated_into`, `has_higher_authority`.
- Ví dụ JSON (Điều 54 Bộ luật Lao động 45/2019/QH14): work_id `vn:boluat:45/2019/QH14`; unit_id `...:dieu_54`; expression `...:dieu_54@2021-01-01` với `valid_from: 2021-01-01`, `valid_to: null`, `transaction_from: 2021-01-01`; action `type: sửa_đổi`, `source: vn:luat:XX/2024/QH15` (ví dụ minh họa với giá trị giữ chỗ).

**Granularity**: nên versioning ở **cấp Điều (Article)** — cân bằng chi phí/độ chính xác; cấp Khoản chính xác hơn nhưng tốn kém; cấp văn bản quá thô (không xử lý "hết hiệu lực một phần"). Louis et al. và de Martim đều ủng hộ Điều là đơn vị truy hồi tự nhiên.

**Định danh (tương tự ELI/URN:LEX)**: `vn:{loại}:{số}/{năm}/{cơ_quan}:{đơn_vị}@{ngày}`, ví dụ `vn:boluat:45/2019/QH14:dieu_54@2021-01-01` → trích dẫn ổn định một điều tại một mốc thời gian.

**Bộ đánh giá QA temporal – các loại "temporal trap"**: (1) hỏi as-of quá khứ; (2) điều đã bị bãi bỏ; (3) điều bị sửa một phần; (4) hiệu lực trở về trước; (5) văn bản của tỉnh cũ sau sáp nhập. Giao thức chú giải: **≥2 annotator có nền luật**, đo Cohen's Kappa (mục tiêu **>0,8**). Kích thước: **~1.000–3.000 câu**, trong đó **≥300–500 câu temporal trap**.

### 3.6 Đề xuất pipeline
Crawl (vbpl.vn) → parse/cấu trúc hóa → trích thực thể & quan hệ → suy luận/hợp nhất thời gian → dựng đồ thị → indexing → retrieval → generation → evaluation.
- **Parsing**: lai rule-based + LLM. Regex: `Điều \d+`, `^\d+.` (Khoản), `^[a-đ])` (Điểm), `Chương [IVX]+`, `Mục \d+`. Bẫy: phụ lục, biểu mẫu, bảng, đánh số không nhất quán qua các thời kỳ, văn bản OCR cũ; LLM xử lý bảng/ngoại lệ.
- **Giải quyết tham chiếu chéo**: tương đối ("khoản 2 Điều 5 của Luật này" → resolve nội văn bản); tuyệt đối ("điểm a khoản 1 Điều 10 Luật Doanh nghiệp số 59/2020/QH14" → work_id + unit_id); parser **hai tầng** (nhận diện pattern rồi ánh xạ về identifier).
- **Áp dụng sửa đổi (tự động consolidation) là phần khó nhất**: parse chỉ dẫn "sửa đổi, bổ sung khoản X Điều Y" rồi áp dụng để sinh phiên bản point-in-time. UK và Brazil làm bán tự động; tỷ lệ lỗi không nhỏ, cần người kiểm. **Khuyến nghị: ưu tiên dùng văn bản hợp nhất có sẵn trên vbpl.vn thay vì tự consolidation.**
- **Embedding tiếng Việt** (benchmark VN-MTEB, arXiv 2507.21500): `bge-m3` (568M, 1024 chiều) điểm trung bình **64,90**; `AITeamVN/Vietnamese_Embedding` (tinh chỉnh từ bge-m3, ~300k triplet, max 2048 token); `gte-multilingual-base` (305M) **65,22**; `halong-embedding` (278M, fine-tune từ m-e5-base, Matryoshka, đánh giá trên Zalo legal) 61,60; Vietnamese-bi-encoder 54,89; sup-SimCSE-VietNamese-phobert-base 50,59; mô hình instruct RoPE (e5-Mistral-7B, e5-Qwen2-7B) vượt trội nhưng nặng. Khuyến nghị: **BGE-M3 hoặc AITeamVN** (dense+sparse, ngữ cảnh dài).
- **Chiến lược truy hồi**: hybrid dense + BM25 (tách từ pyvi/VnCoreNLP/underthesea) → duyệt đồ thị có **lọc temporal** → rerank cross-encoder (PhoRanker/BGE-reranker-v2-m3) → trích "as-of date" từ query (không có thì mặc định hôm nay).
- **CSDL đồ thị**: Neo4j (phổ biến, hỗ trợ Graphiti), Memgraph, Kùzu (embedded, nhẹ, hợp nghiên cứu), TigerGraph, ArangoDB, hoặc **Postgres + pgvector + recursive CTE** (đơn giản, đủ cho luận văn). Khuyến nghị: Neo4j (cần trực quan/Graphiti) hoặc Kùzu/Postgres (gọn nhẹ).
- **LLM sinh tiếng Việt**: GPT-4o/5, Claude, Gemini (đóng, mạnh nhất); mở: SeaLLM 3, Sailor 2, SEA-LION v3.5, PhoGPT-4B (3,7B; 482GB/~102B token), VinaLLaMA-7B, Qwen, URA-LLaMa.

### 3.7 Phương pháp đánh giá đề xuất
- **Retrieval**: Recall@k, MRR, nDCG, Exist@m (SoICT).
- **Temporal correctness**: chỉ số đề xuất **point-in-time accuracy** = tỷ lệ câu trả lời trả về đúng *phiên bản điều luật có hiệu lực tại as-of date*.
- **Generation**: faithfulness, citation accuracy, hallucination rate.
- **Baseline**: BM25, dense-only RAG, Microsoft GraphRAG (non-temporal), LightRAG, SBV-LawGraph, hienlh/vn-legal-rag (76,3% hit rate).
- **Ablation**: có/không temporal filtering trên tập temporal-trap; kỳ vọng temporal cải thiện mạnh point-in-time accuracy trong khi retrieval as-of-today gần như không đổi (tránh confound).

### 3.8 Công trình VN để định vị
- **"Applying Graph RAG: Enhancing Retrieval and Synthesis of Vietnamese Legal Text Information"** (Huynh et al., ICCIES 2025, Springer, 10.1007/978-3-031-98164-7_25): 6 bộ luật VN, Neo4j + GPT-4o Mini; GraphRAG vượt RAG thường **+14,05% NDCG, +4,34% accuracy**; không có temporal.
- **SBV-LawGraph** (Khoa Phan et al., ACIIDS 2026): dual-retrieval (sparse-dense + Relationship Retrieval trên Legal KG), corpus ngân hàng SBV + ALQAC2025; LKG có amendments/citations/definitions, traversal giới hạn 1-hop hai chiều; quan hệ tĩnh.
- **hienlh/vn-legal-rag** (GitHub, MIT): kiến trúc 3 tầng (tree traversal + semantic + KG expansion), **76,3% hit rate**, vượt LightRAG (33,85% Hit@10).
- **"Optimizing Legal Document Retrieval in Vietnamese with Semi-Hard Negative Mining"** (arXiv 2507.14619, team 4Huiter, top-3 SoICT 2024): Bi-Encoder + Cross-Encoder, Exist@m, MRR@10 77,54%.
- "Can Small Language Models Handle Vietnamese Legal Reasoning?" (VLSP 2025, 2025.vlsp-1.23); chatbot pháp lý NAGphormer + Graph RAG; Dang et al. KG thuật ngữ pháp lý VN; "Graph Retrieval-Augmented Language Model for QA of Vietnamese Law"; VNLegalEase; "Integrating Knowledge Graph with RAG for Vietnamese Legal QA" (KG phân cấp Document→Chapter→Section→Article→Clause→Point).
- **Kết luận định vị**: tất cả công trình VN mô hình hóa quan hệ tĩnh; chưa có công trình nào truy vấn point-in-time/bi-temporal ở cấp Điều/Khoản.

### 3.9 Định vị đóng góp
Ba khoảng trống novelty: (1) chưa có bộ dữ liệu GraphRAG pháp luật VN có nhãn bi-temporal point-in-time; (2) chưa có benchmark "temporal trap" tiếng Việt; (3) chưa có hệ thống VN áp dụng LRMoo Work/Expression + Action nodes cho consolidation. De Martim cũng thừa nhận gap thiếu benchmark kết hợp truy hồi pháp lý với yêu cầu thời gian/phân cấp.
- Khung A (dataset + benchmark, an toàn nhất; hợp NeurIPS Datasets & Benchmarks, ALQAC); khung B (system; hợp JURIX, ICAIL); **khung C (lai; khuyến nghị cho luận văn)**.
- Venue gợi ý: ALQAC/ISAILD (gắn KSE), VLSP, JURIX (thường tháng 12), ICAIL (2 năm/lần), PACLIC, RIVF, COLIEE, NeurIPS D&B.

### 3.10 Rủi ro và thách thức
- Pháp lý/licensing: tránh crawl trang thương mại; dùng vbpl.vn (công khai; robots.txt cho phép) và bản CC-BY-4.0 trên HuggingFace.
- Chất lượng dữ liệu: OCR cũ (trước 1984, chính tả khác), định dạng không nhất quán, thiếu văn bản hợp nhất cho một số văn bản, "hết hiệu lực một phần" thường không chú giải rõ.
- Chi phí LLM indexing: full GraphRAG cho 100k–260k văn bản rất đắt; LightRAG/LazyGraphRAG hoặc parsing rule-based + LLM chọn lọc → vài trăm USD cho lĩnh vực hẹp.
- Đánh giá khó khi chưa có gold-standard temporal: phải tự xây, tốn annotator có nền luật.

### 3.11 Khuyến nghị lộ trình (Recommendations)
| Giai đoạn | Việc | Ngưỡng |
|---|---|---|
| 1 (tháng 1–2) | Chọn lĩnh vực hẹp (khuyến nghị **lao động**; hoặc thuế); crawl vbpl.vn ~50–200 văn bản gốc + bản hợp nhất + lược đồ; xác nhận metadata hiệu lực | nếu <80% văn bản có bản hợp nhất → thu hẹp phạm vi |
| 2 (tháng 3–5) | Schema LRMoo + bi-temporal (Neo4j hoặc Kùzu/Postgres); parser lai; cross-reference resolver; định danh VN; ưu tiên văn bản hợp nhất; BGE-M3/AITeamVN + BM25 (VnCoreNLP) + reranker | — |
| 3 (tháng 6–8) | ~1.000–3.000 câu (≥300–500 temporal-trap), ≥2 annotator luật, Kappa >0,8; Recall@k, MRR, nDCG, point-in-time accuracy, citation accuracy, hallucination; ablation temporal | — |
| 4 (tháng 9–12) | Baseline (BM25, dense RAG, MS GraphRAG, LightRAG, SBV-LawGraph, vn-legal-rag); nộp ALQAC/ISAILD/JURIX; cân nhắc NeurIPS D&B cho dataset | — |

**Ngưỡng đổi quyết định**: (a) tự consolidation lỗi >10% → chuyển hẳn sang văn bản hợp nhất; (b) temporal ablation không cải thiện point-in-time accuracy đáng kể → xem lại chất lượng nhãn thời gian; (c) chi phí LLM indexing vượt ngân sách → LightRAG/rule-based; (d) lĩnh vực chọn có quá ít câu hỏi temporal thực tế → đổi sang lĩnh vực chịu tác động mạnh của sáp nhập 2025 (đất đai, tổ chức chính quyền, hộ tịch).

### 3.12 Caveats do báo cáo tự nêu
Tuyên bố sản phẩm thương mại là marketing chưa kiểm chứng; số vbpl.vn là ảnh chụp 1/3/2025 và có lệch ~33; 5.026 là toàn bộ tái cấu trúc bộ máy; $33k là số cho án lệ 5GB (dẫn lại qua tổng hợp 2026); ảo giác 17%/33%/43% đo trên hệ pháp lý Mỹ; nhiều công trình mang nhãn 2026 (SBV-LawGraph ACIIDS 2026, "Applying Graph RAG" ICCIES 2025, LegalGraphRAG) cần kiểm tra trạng thái xuất bản chính thức; de Martim chỉ đánh giá định tính.

## 4. Đối chiếu với các bài đã đọc kỹ (để tránh lệch)
- **Với bài 02 (SAT-Graph RAG)**: báo cáo mô tả đúng cốt lõi (Work/Expression, CTV aggregation, Action, planner tất định). Cần phân biệt: bản FAIA/JURIX 2025 có thể khác chi tiết so với arXiv v5 đã đọc.
- **Với bài 01 (FiscalQA Pro, ra 08/2026)**: báo cáo này **chưa** biết bài đó; kết quả của bài 01 (98,3% chỉ với chỉ mục phiên bản + lọc ngày, không đồ thị) **củng cố phản biện "lọc metadata đơn giản có đủ không?"** ở mục 3.1 và đòi hỏi khóa luận phải chứng minh đồ thị thắng ở loại câu hỏi vượt single-anchor (impact, provenance, so sánh nhiều phiên bản, chuỗi văn bản sửa nhau).
- **Với bài 03 (ViHERMES)**: báo cáo không nhắc ViHERMES; đó là benchmark multihop tiếng Việt về quy định, có quan hệ Amends/Replaces nhưng chưa temporal.
- Mục tiêu "Kappa >0,8", "1.000–3.000 câu" trong báo cáo là gợi ý chưa có nguồn thực nghiệm; **tình trạng dữ liệu thực tế của ViLexTime** (các ghi chú hiện có về chất lượng nhãn/quy mô) cần được đối chiếu riêng với `docs/` của repo, không suy ra từ báo cáo này.

## 5. Dùng gì cho khóa luận ViLexTime
1. **Danh sách khái niệm hiệu lực VN cần mô hình hóa** (mục 3.3): ba mốc ngày; hết hiệu lực toàn bộ/một phần; ngưng hiệu lực; hồi tố và điều kiện cấm; văn bản hợp nhất; văn bản hướng dẫn còn áp dụng; "một luật sửa nhiều luật". Lần về **Luật 64/2025/QH15, Luật 87/2025/QH15, Luật 80/2015** (các Điều 152–156) để trích nguồn chính xác (nên tra bằng công cụ tra cứu pháp luật, không dựa vào báo cáo).
2. **Taxonomy "temporal trap"** 5 loại làm điểm xuất phát cho phân loại câu hỏi benchmark.
3. **Nguồn dữ liệu**: ưu tiên vbpl.vn (có "Lược đồ" quan hệ + văn bản hợp nhất), xác minh giấy phép/robots/ToS; đối chiếu SoICT/ALQAC/TVPL cho phần related work.
4. **Chỉ số `point-in-time accuracy`** và thiết kế ablation temporal (cần bổ sung chấm tất định theo tinh thần bài 01).
5. **Danh sách baseline VN** (vn-legal-rag, SBV-LawGraph, "Applying Graph RAG") và **bảng embedding** (VN-MTEB) để chọn mô hình.
6. **Định danh `vn:{loại}:{số}/{năm}/{cơ_quan}:{đơn_vị}@{ngày}`** làm bản nháp, cần chuẩn hóa với quy ước số hiệu văn bản thực tế.
7. **Cẩn trọng**: không trích báo cáo này trong luận văn như một tài liệu học thuật; chỉ dùng như bản đồ để tìm và kiểm chứng nguồn gốc.
