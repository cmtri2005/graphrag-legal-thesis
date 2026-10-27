# LegalGraphRAG: Multi-Agent Graph Retrieval-Augmented Generation for Reliable Legal Reasoning

> Ghi chú đọc chi tiết cho khóa luận ViLexTime. Nguồn: `related_paper/2026.acl-long.1738.pdf` (30 trang). File PDF bị lỗi luồng nén nhẹ ("Bad block header in flate stream"); phần chữ đọc được đầy đủ, nhưng **các hình biểu đồ (Hình 2, 5, 6, 9) không đọc được số liệu**, chỉ lấy được những số mà văn bản/bảng nêu. Bảng được dựng lại từ bản trích xuất theo cột; đã đối chiếu các cột với nhau.

## 0. Thông tin chung

| Mục | Nội dung |
|---|---|
| Tác giả | Zerui Chen, Qinggang Zhang†, Zhishang Xiang, Zhimin Wei, Linfeng Gao, Xiao Huang, Zhihong Zhang†, Jinsong Su† (Đại học Hạ Môn, Đại học Cát Lâm, PolyU) |
| Nơi đăng | Proceedings of the 64th Annual Meeting of the ACL (Long Papers), tr. 37455–37484, 2–7/07/2026 (ACL 2026) |
| Mã nguồn | https://github.com/XMUDeepLIT/LegalGraphRAG |
| Miền / ngôn ngữ | **Luật hình sự Trung Quốc**, tiếng Trung; tác vụ **dự đoán bản án (Legal Judgment Prediction, LJP)**: tội danh, điều luật, mức án |
| Độ gần với ViLexTime | **Thấp về nội dung và dữ liệu** (hình sự, không có thời gian); **trung bình về kiến trúc**: đồ thị phân tầng + hệ đa agent có bước **kiểm chứng bằng chứng**, tham chiếu được cho phần xác minh phiên bản |

## 1. WHY – Bài toán

Hai thách thức khi áp GraphRAG chuẩn vào pháp lý (Hình 1):
1. **Tri thức dị thể, đa mức chi tiết**: kho pháp lý gồm án lệ (chi tiết sự kiện), điều luật (quy tắc áp dụng) và giải thích tư pháp (nguyên tắc trừu tượng). Đồ thị phẳng không phân biệt được **sự kiện cụ thể – quy tắc áp dụng – nguyên tắc trừu tượng**, nên truy hồi bị lệch: ưu tiên chi tiết sự kiện có trùng lặp bề mặt, bỏ sót quy tắc then chốt ("**semantic similarity trap**": tương đồng ≠ hữu ích).
2. **Thiếu suy luận có kiểm chứng**: RAG "truy hồi rồi sinh" đưa ngữ cảnh thẳng vào LLM không xác minh, nhất là khi ngữ cảnh dài chứa nhiều thông tin không liên quan → suy luận mờ đục, dễ sai ("blind trust in context"). Ví dụ Hình 1: tham chiếu vụ án tương tự và Điều 382 (không liên quan) thay vì Điều 271 (liên quan) → kết án sai.

Fine-tuning (SFT) chuyên biệt (DISC-LawLLM v.v.) tốn chi phí tính toán và có rủi ro quên thảm họa; RAG là phương án thực tế hơn.

### 1.1 Hai nghiên cứu sơ bộ làm động lực (mục 3)
**(a) Granularity bias** (Hình 2): so sánh *Flat Strategy* (một kho phẳng) với *Hierarchical Strategy* ngây thơ (tách điều luật khỏi án lệ, xây trên Naive RAG). Chiến lược phẳng bộc lộ "granularity bias": ưu tiên chi tiết sự kiện tần suất cao, thiệt hại cho nguyên tắc trừu tượng. Phân tầng đơn giản **cải thiện truy hồi 25,3%**.
**(b) Chất lượng sinh dưới nhiễu truy hồi** (Bảng 1): thêm tài liệu "hợp lý về pháp lý nhưng không liên quan" vào ngữ cảnh:
| Điều kiện | Charge ACC | ∆ | Articles ACC | ∆ | Term of Penalty MAE (tháng) | ∆ |
|---|---|---|---|---|---|---|
| RAG (ngữ cảnh đúng) | 42,8 | – | 74,7 | – | 24,3 | – |
| + 2 tài liệu nhiễu | 34,9 | ↓7,9 | 57,2 | ↓17,5 | 27,7 | ↑3,4 |
| + 4 tài liệu nhiễu | 32,9 | ↓9,9 | 51,1 | ↓23,6 | 28,4 | ↑4,1 |
| + 6 tài liệu nhiễu | 29,8 | ↓13,0 | 46,8 | ↓27,9 | 31,7 | ↑7,4 |

→ RAG nhạy mạnh với "độ tinh khiết" ngữ cảnh; thiếu bước lọc/xác minh thì mô hình không phân biệt bằng chứng hợp lệ và gây hiểu lầm. Tài liệu nhiễu được tạo bằng cách lấy toàn bộ Bộ luật Hình sự làm kho, với mỗi điều đúng thì tìm top-k điều **giống nhất bằng vector** nhưng không thuộc tập đúng ("High-Similarity Distractors": trùng từ khóa như "trộm cắp", "lừa đảo" nhưng khác yếu tố cấu thành hay khung hình phạt). Ngữ cảnh gốc: các điều đúng theo CAIL.

## 2. HOW – Khung LegalGraphRAG

Bài toán (mục 2): cho mô tả sự kiện hình sự f và bị cáo d, dự đoán tội danh y qua ba bước: Tổ chức tri thức KG = Φ(D); Truy hồi C = R(f, d, KG); Sinh P(y | f, d, C) = G(f, d, C).

### 2.1 Giai đoạn 1: Hierarchical Legal Graph (HierarGraph) = 3 đồ thị con
- **Fact Graph (G_fac)** – kho án lệ đã xác minh, "cơ sở thực tế": nút **Cases (C)**, **Articles (A)**, **Offense (O)**; cạnh e_ca (án → điều được viện dẫn), e_co (án → tội danh bị kết án).
- **Ontology Graph (G_ont)** – trừu tượng hóa đặc trưng vụ án để thu hẹp khoảng cách ngữ nghĩa và giảm nhiễu: chắt lọc tường thuật chứa chi tiết riêng (ngày, nơi chốn) thành "bản chất pháp lý". Ontology theo lý thuyết pháp lý (Rüthers et al. 2013) gồm **bốn chiều**: *Defendant Attributes* (D), *Criminal Behaviors* (O), *Victim Characteristics* (V), *Subjective Mental States* (M). Từ khóa/thực thể được trích và gióng vào các thuộc tính để tạo embedding có cấu trúc, làm chỉ mục cho **Case Feature Nodes (F)**. Để lộ liên kết giữa các vụ: **k-NN** nối các nút giống ngữ nghĩa (top-3 case feature nodes theo cosine khi xây đồ thị), rồi **Leiden** gom thành **Community Nodes (K)** có tóm tắt → truy hồi từ rộng đến chi tiết.
- **Rule Graph (G_rul)** – giải quyết mơ hồ quy phạm bằng nối **Articles (A)** với **Judicial Interpretations (J)** (tham chiếu chéo tường minh). Mỗi điều gắn **Diagnostic Checklist D(a_i) = {d_1…d_|C|}**: phân rã quy tắc phức tạp thành các **câu hỏi boolean nguyên tử** sinh bằng cách phân tích văn bản luật. Ví dụ Điều 266 (lừa đảo): "Bị cáo có bịa đặt sự thật hoặc che giấu sự thật không?", "Nạn nhân có rơi vào nhầm lẫn do hành vi đó không?", "Nạn nhân có định đoạt tài sản dựa trên nhầm lẫn đó không?". Mục đích: buộc mô hình kiểm từng yếu tố cấu thành, tránh dựa vào trùng lặp ngữ nghĩa mơ hồ. Lý do: một khác biệt nhỏ (bị cáo thành niên hay vị thành niên) có thể dẫn tới phán quyết khác hẳn.

### 2.2 Giai đoạn 2: suy luận dựa bằng chứng – 3 agent (Thuật toán 1)
- **Researcher** — gióng mô tả vụ án vào các chiều ontology rồi truy hồi bằng **hợp ba toán tử** R(q) = R_sem ∪ R_com ∪ R_chg:
  1. *Semantic Match Retrieval*: top-k theo tương đồng của embedding căn chỉnh ontology φ(·) trên các nút vụ án.
  2. *Community Expansion Retrieval*: chọn cộng đồng chủ đề gần truy vấn nhất K* = argmax sim(φ(q), φ(K)) rồi top-k vụ án giống nhất **trong cộng đồng đó**.
  3. *Charge-Anchored Retrieval*: lấy các vụ án liên kết với các tội danh được suy ra O(q), tức hợp các láng giềng N_Gfac(o).
  Tập ứng viên S_cand = hợp ba nguồn.
- **Auditor** — "verify-and-prune": với mỗi điều ứng viên v_a: (i) *Diagnostic Retrieval* lấy checklist D(v_a) và các Judicial Interpretations J từ Rule Graph; (ii) *Item-wise Verification*: vòng lặp xác minh từng mục d_k bằng CheckCondition(q, d_k, v_a, J) → tập kết quả boolean V_results; (iii) *Decision and Pruning*: tổng hợp quyết định IsApplicable; nếu không đạt thì **cắt tỉa (Prune)** nút điều luật đó **cùng các nút án lệ và tội danh phụ thuộc**, ra đồ thị con S_verified chỉ gồm bằng chứng hợp lệ về lô-gic.
- **Adjudicator** — tổng hợp phán quyết J = Adjudicator(q ⊕ A_f ⊕ C_f ⊕ O_f) trên các điều đã xác nhận, các án lệ và thông tin tội danh; đầu ra **kèm trích dẫn tường minh** tới điều luật và giải thích tư pháp, mọi kết luận truy được tới nút trong HierarGraph.

Ví dụ định tính (Hình 3–4): bị cáo Trương làm bếp trưởng ở ban dự án thủy điện, phụ trách thanh toán chi phí căng-tin, chiếm dụng ~98.160 NDT: Naive RAG thiếu điều then chốt; phương pháp tam đoạn luận gặp mơ hồ ("công chức nhà nước" nghĩa là gì?) và trả "Biển thủ, Điều 382, 36 tháng"; LegalGraphRAG nhờ Auditor loại Điều 382 (bếp trưởng không phải công chức nhà nước), kết luận đúng **"tội chiếm đoạt tài sản trong lĩnh vực nghề nghiệp, Điều 271, 18 tháng"**. Các ví dụ phụ lục: lái xe nguy hiểm (nồng độ cồn 242,5 mg/100 ml) với checklist "Có điều khiển xe cơ giới trên đường không?", "Có lái xe khi say rượu không?".

## 3. Thiết lập thực nghiệm
- **Dữ liệu kiểm thử**: **CAIL2018** (2,6 triệu vụ hình sự; 183 điều luật, 202 tội danh) và **CMDL** (393.945 vụ, ~1,2 triệu bị cáo, 321 tội danh, 275 điều; nhiều bị cáo) — dùng **tập con** để kiểm soát chi phí: chỉ giữ mô tả sự kiện <1.024 ký tự; ưu tiên tội danh tần suất thấp và vụ nhiều tội để cân bằng phân bố và tăng độ khó (nên điểm thấp hơn so với dữ liệu tự nhiên). Thống kê tập test (Bảng 8): **CAIL 568 vụ, 168 tội danh, TB 1,25 tội/vụ, 1,72 bị cáo/vụ, độ dài TB 654,79**; **CMDL 572 vụ, 239 tội danh, 2,40 tội/vụ, 1,14 bị cáo/vụ, độ dài 517,13**. Bốn nhóm tội: Public Safety, Economic, Social Order, Person Rights.
- **Kho tri thức**: tổng hợp từ **JuDGE, CAIL2018, CMDL, LeCaRDv2** (cùng quy trình lọc dưới 1.024 ký tự, cân bằng tội danh) cộng **toàn văn Bộ luật Hình sự CHND Trung Hoa và giải thích tư pháp**. Bảng 9: **14.049 vụ**, 818 "tội danh" (số lớn do mô tả tội khác nhau giữa các dataset), 3,39 bị cáo/vụ, độ dài TB 399,73. Bảng 10: **452 điều luật** (độ dài TB 128,54) và **656 giải thích tư pháp** (243,95). Đã kiểm tra **không trùng** giữa kho và tập test (chống rò rỉ dữ liệu).
- **Baseline** (4 nhóm): (i) mã nguồn mở Qwen-2.5-7B, Qwen-3-8B, InternLM3-8B, GLM-4-9B; (ii) tiên tiến GPT-4o-mini, DeepSeek-V3.1; (iii) chuyên biệt pháp lý: DISC-LawLLM-7B (fine-tune từ Qwen2.5-7B; tam đoạn luận), **Legal Δ** (học tăng cường, độ lợi thông tin có dẫn CoT, 7B), **ADAPT** (suy luận phân biệt cho LJP, fine-tune Qwen2-7B); (iv) RAG: Naive RAG, G-Retriever, LightRAG, RAPTOR, HippoRAG2.
- **Cấu hình**: GPT-4o-mini để xây đồ thị; **BGE-m3** để nhúng; backbone suy luận mặc định **Qwen3-8B**; k = 5 (số khái niệm ngữ nghĩa truy hồi từ ontology graph và phạm vi mở rộng cộng đồng); `max_token_global_context: 2000` cho baseline; siêu tham số baseline theo giá trị tối ưu của bài gốc.
- **Chỉ số**: Accuracy (khớp chính xác tập nhãn: tập dự đoán phải trùng hệt tập vàng) và Micro-F1 cho tội danh và điều luật; **MAE** (tháng) cho mức án; **Retrieval Effectiveness** (độ phủ bằng chứng vàng, thực chất như recall) và **Error Rate** (tỷ lệ mệnh đề tham chiếu không được ngữ cảnh truy hồi hỗ trợ).

## 4. WHAT – Kết quả

### 4.1 Bảng 2: dự đoán tội danh, backbone Qwen3-8B (ACC / F1; cột cuối là trung bình ACC "All" và chênh lệch của LegalGraphRAG ∆)
| Phương pháp | Cỡ | CAIL Pub.Safety | CAIL Econ. | CAIL Social | CAIL Person | CMDL Pub.Safety | CMDL Econ. | CMDL Social | CMDL Person | All ACC | ∆ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen-2.5-7B | 7B | 24,0/45,8 | 23,1/42,5 | 22,9/36,7 | 27,4/46,0 | 25,8/32,4 | 28,7/35,8 | 27,2/42,1 | 32,8/49,6 | 26,7 | ↑22,8 |
| Qwen-3-8B | 8B | 31,7/49,2 | 25,8/42,7 | 26,3/39,8 | 27,6/47,8 | 44,0/52,3 | 44,7/53,1 | 42,7/51,9 | 53,0/57,7 | 35,2 | ↑19,9 |
| InternLM3-8B | 8B | 29,8/49,1 | 26,7/42,0 | 25,2/34,3 | 28,1/47,3 | 25,4/32,1 | 35,7/37,0 | 27,5/36,2 | 34,1/53,6 | 26,6 | ↑22,9 |
| GLM-4-9B | 9B | 18,4/33,7 | 19,7/36,1 | 15,8/32,1 | 26,0/44,5 | 23,5/34,2 | 23,6/40,8 | 19,1/37,0 | 41,5/47,0 | 21,2 | ↑28,2 |
| GPT-4o-mini | ~8B | 19,7/35,5 | 19,6/33,3 | 15,5/35,2 | 29,0/46,3 | 18,0/28,0 | 22,7/31,9 | 21,9/32,0 | 35,9/50,3 | 28,4 | ↑21,1 |
| DeepSeek-V3.1 | ~200B | 31,0/51,3 | 29,0/48,4 | 29,8/50,2 | 35,2/54,8 | 35,0/64,0 | 54,7/62,7 | 58,2/61,9 | 62,5/71,6 | 42,8 | ↑6,7 |
| DISC-LawLLM-7B | 7B | 40,1/50,9 | 31,0/51,5 | 34,8/47,7 | 34,5/56,0 | 49,7/53,6 | 39,6/52,1 | 30,3/49,5 | 48,4/63,3 | 30,3 | ↑19,1 |
| ADAPT | 7B | 38,7/43,7 | 32,7/43,4 | 27,6/41,7 | 35,2/50,7 | 54,5/58,8 | 57,1/59,4 | 40,9/43,4 | 61,5/62,1 | 42,8 | ↑6,7 |
| Legal Δ | 7B | 40,8/50,6 | 25,1/37,4 | 32,1/43,7 | 34,1/53,6 | 58,3/61,5 | 51,8/55,8 | 50,2/54,8 | 65,8/64,4 | 42,4 | ↑7,1 |
| Naive RAG | 8B | 31,0/45,7 | 24,4/38,7 | 28,1/38,4 | 34,5/46,8 | 45,8/57,3 | 44,8/55,2 | 46,8/58,5 | 49,6/57,8 | 33,3 | ↑16,1 |
| G-Retriever | 8B | 33,8/48,0 | 26,0/39,8 | 23,8/39,3 | 32,6/50,1 | 36,8/40,0 | 42,5/48,8 | 45,3/50,7 | 46,2/52,4 | 34,4 | ↑13,2 |
| LightRAG | 8B | 20,4/43,6 | 21,7/42,5 | 19,0/42,5 | 26,9/50,6 | 37,9/50,1 | 43,2/45,1 | 44,2/51,3 | 43,7/46,9 | 30,5 | ↑19,0 |
| RAPTOR | 8B | 34,6/50,4 | 31,6/43,9 | 32,1/45,6 | 32,4/45,7 | 53,8/62,6 | 53,6/60,1 | 52,5/62,8 | 52,1/66,9 | 43,1 | ↑6,3 |
| HippoRAG2 | 8B | 34,5/38,2 | 24,0/33,5 | 28,8/35,0 | 31,0/36,3 | 53,5/56,5 | 50,6/52,7 | 53,5/55,0 | 62,4/62,8 | 43,1 | ↑6,3 |
| **LegalGraphRAG** | 8B | **42,9/54,3** | **38,5/53,6** | **37,6/51,1** | **37,2/58,3** | **65,5/66,5** | **59,8/65,1** | **58,5/63,7** | **70,1/72,7** | **49,5** | – |

(Cột "All" là số bài ghi ở cuối hàng. **Lưu ý**: nó không phải trung bình đơn giản của tám ô ACC — ví dụ DISC-LawLLM-7B có các ô 30,3–49,7 nhưng All = 30,3; GPT-4o-mini các ô 18,0–35,9 nhưng All = 28,4. Có thể tính theo trọng số số vụ hoặc là sai sót của bài; cần kiểm lại nếu trích. Bài tuyên bố cải thiện **6,3% đến 19,1%** so với các baseline; ∆ trong bảng dao động 6,3–28,2.)

Quan sát: **Obs.1** vượt mọi baseline ở hầu hết chỉ số, cả hai dataset; GraphRAG tiêu chuẩn (LightRAG, G-Retriever, HippoRAG2) không mạnh ở pháp lý, có khi **thấp hơn** mô hình nền không truy hồi (ví dụ LightRAG 30,5 < Qwen-3-8B 35,2). **Obs.2** vượt các LLM pháp lý chuyên biệt: hơn Legal Δ trung bình 7,1% và ADAPT 6,7%; ghép backbone mạnh đạt tới **78,7% trên CMDL**.

### 4.2 Bảng 4: backbone khác (ACC/F1 theo nhóm; All ACC)
| Backbone | Dataset | Naive RAG | G-Retriever | LightRAG | RAPTOR | HippoRAG2 | **LegalGraphRAG** |
|---|---|---|---|---|---|---|---|
| GPT-4o-mini (~8B) | CAIL | 22,2 | 21,4 | 23,1 | 30,5 | 31,9 | **40,9** |
| DeepSeek-V3.1 (~200B) | CAIL | 37,8 | 37,2 | 45,4 | 44,4 | 41,2 | **49,9** |
| GPT-4o-mini | CMDL | 32,9 | 28,3 | 34,2 | 48,7 | 46,0 | **60,0** |
| DeepSeek-V3.1 | CMDL | 62,9 | 55,2 | 52,4 | 56,4 | 74,0 | **78,7** |

**Obs.7**: nhất quán vượt mọi baseline bất kể backbone.

### 4.3 Bảng 5: dự đoán điều luật (All ACC, CAIL)
Qwen-2.5-7B 30,1; Qwen-3-8B 35,9; InternLM3-8B 29,9; GLM-4-9B 30,8; GPT-4o-mini 30,9; DeepSeek-V3.1 **44,9**; DISC-LawLLM 38,2; ADAPT 41,3; Legal Δ 37,9; Naive RAG 34,8; RAPTOR 37,2; HippoRAG2 39,8; **LegalGraphRAG 47,9** (43,0/64,9; 37,8/61,0; 44,6/69,4; 54,5/70,6 theo nhóm). **Obs.8**: mô hình 8B vượt cả DeepSeek-V3.1 (44,9%) và baseline mạnh nhất ADAPT; kết luận truy hồi theo bằng chứng hiệu quả hơn tăng quy mô tham số.

### 4.4 Bảng 6: dự đoán mức án (MAE tháng, càng thấp càng tốt; CAIL)
MAE trung bình All: Qwen-2.5-7B 29,5; Qwen-3-8B 27,5; InternLM3 33,7; GLM-4 33,1; GPT-4o-mini 33,6; DeepSeek-V3.1 29,1; DISC-LawLLM 31,6; ADAPT 20,4; Legal Δ 26,3; Naive RAG 26,5; RAPTOR 24,3; HippoRAG2 23,8; **LegalGraphRAG 20,1** (Public Safety 14,0 ACC / 20,9 MAE so với RAPTOR 21,7 và HippoRAG2 23,0). **Obs.9**: sai số nhỏ nhất ở hầu hết nhóm so với các RAG; khớp chính xác mức án vẫn khó với mọi mô hình.

### 4.5 Ablation (Bảng 3, ACC CAIL)
| Cấu hình | ACC | ∆ |
|---|---|---|
| LegalGraphRAG đầy đủ | 40,9 | – |
| w/o HierarGraph | 33,7 | ↓7,2 |
| w/o Researcher | 36,9 | ↓4,0 |
| w/o Auditor | 37,5 | ↓3,4 |
| w/o Semantic Match | 39,1 | ↓1,8 |
| w/o Community Expansion | 38,5 | ↓2,4 |
| w/o Charge-Anchored | 39,3 | ↓1,6 |

(Con số 40,9 là ACC nền GPT-4o-mini trên CAIL — khớp Bảng 4, trong khi Bảng 2 dùng Qwen3-8B; bài không ghi rõ backbone ở Bảng 3.) **Obs.5**: cấu trúc phân tầng là tảng đá (giảm mạnh nhất 7,2); **Obs.6**: Researcher và Auditor bổ trợ nhau.

### 4.6 Truy hồi và độ tin cậy
- **Obs.3** (Hình 5, số liệu trong hình không đọc được): LegalGraphRAG truy hồi bằng chứng liên quan, đầy đủ hơn và **tỷ lệ lỗi thấp hơn nhiều** so với đồ thị phẳng (HippoRAG2 hay bỏ sót điều luật cốt yếu).
- **Obs.4** (Hình 6): "**unsupported correctness**" — dự đoán đúng tội danh nhưng **không truy hồi được bằng chứng hỗ trợ**. Định nghĩa: *Traceable Correct* = dự đoán đúng tội danh **và** truy hồi được điều luật vàng; *Untraceable Correct* = đúng tội danh dù không truy hồi được điều luật cần thiết. LegalGraphRAG tăng tỷ lệ Traceable Correct và giảm Untraceable Correct (số liệu nằm trong biểu đồ Hình 6, không đọc được chắc chắn từ PDF nên không chép ở đây) → mọi điều trích dẫn đều có trong ngữ cảnh truy hồi.
- **Độ nhạy k** (Hình 9; Obs.10): hiệu năng đạt đỉnh ở **k = 5 (ACC 40,9; F1 52,8)**; biến thiên trong {3,4,5,6} nhỏ; chặn trên k = 6 vì lớn hơn gây nhiễu ngữ cảnh.
- **Chi phí (Bảng 7; Obs.11)**:
  | Phương pháp | Thời gian lập chỉ mục (s) | Token prompt (×10⁶) | Token completion (×10⁶) | Thời gian TB/truy vấn (s) | Token TB/truy vấn |
  |---|---|---|---|---|---|
  | RAPTOR | 13.696,90 | 5,64 | 0,72 | 5,86 | 3.589 |
  | HippoRAG2 | 4.581,60 | 10,58 | 2,79 | 11,2 | 5.199 |
  | **LegalGraphRAG** | **3.687,49** | **3,97** | **0,78** | 46,1 | 10.664 |
  → lập chỉ mục rẻ nhất, nhưng **truy vấn chậm hơn nhiều (46,1 s)** và tốn token hơn do xác minh nhiều bước; tác giả coi là đánh đổi cần thiết để có chuỗi suy luận đáng tin.

## 5. Hạn chế và đạo đức (do tác giả nêu)
- Chỉ nhập **văn bản đơn phương thức**; chứng cứ phi văn bản (ảnh hiện trường, camera, chữ viết tay quét, ghi âm phiên tòa) phải được chép lời trước, có thể mất sắc thái (ví dụ phân biệt "cố ý" và "vô ý" đôi khi dựa vào video). Hướng tương lai: nút đa phương thức trong Fact Graph ("Smart Court").
- Đạo đức: dữ liệu công khai đã ẩn danh; nhận thức rủi ro thiên lệch (khu vực, giới) từ dữ liệu lịch sử; công cụ **hỗ trợ**, không thay thế thẩm phán hay luật sư; dự đoán "mức án" chỉ là xác suất tham khảo, không phải bản án có hiệu lực thi hành.

## 6. Nhận xét phê phán (người đọc)
- **Không có yếu tố thời gian/phiên bản luật**: kho là Bộ luật Hình sự "hiện hành" cộng án lệ; không bàn việc điều luật thay đổi theo ngày xét xử. Đây chính là điều kiện thiếu mà ViLexTime cần.
- Tập test là **tập con đã được chọn lọc khó hơn** (tội ít gặp, nhiều tội/vụ), ~570 vụ mỗi dataset, một lần chạy; không có khoảng tin cậy hay kiểm định thống kê; chênh lệch với baseline mạnh nhất (RAPTOR/HippoRAG2) khoảng 6 điểm.
- **Điểm tuyệt đối thấp** (ACC tội danh 49,5% ở Qwen3-8B; CAIL ~41–50% với backbone khác) cho thấy bài toán chưa gần giải quyết; ACC đòi hỏi trùng khớp **tập** nhãn.
- Ablation chỉ trên CAIL và không nêu backbone; checklists do LLM sinh từ văn bản luật (chất lượng phụ thuộc LLM xây đồ thị, không đánh giá riêng).
- Auditor và checklists tăng độ trễ gấp 4–8 lần RAPTOR/HippoRAG2; chưa phân tích hiệu ứng lỗi lan truyền (Auditor loại nhầm điều đúng sẽ làm mất bằng chứng).
- Dữ liệu hình sự Trung Quốc: kết quả không chuyển nguyên sang luật dân sự/hành chính Việt Nam (nhiều quy phạm cấp dưới luật, hiệu lực chồng lấn).

## 7. Dùng gì cho khóa luận ViLexTime
1. **Ý tưởng "Auditor / verify-and-prune"**: bước kiểm chứng trước khi sinh, loại bằng chứng không áp dụng được, rồi cắt luôn các nút phụ thuộc. Trong ViLexTime có thể chuyển thành **bộ kiểm chứng hiệu lực**: với mỗi điều luật ứng viên, kiểm `valid_from ≤ t < valid_to`, kiểm điều đã bị sửa/bãi bỏ ở ngày t (checklist tất định thay vì LLM), rồi loại phiên bản không áp dụng. Kết hợp với chấm tất định ở bài 01.
2. **Diagnostic Checklist** (phân rã điều luật thành câu hỏi boolean): có thể dùng cho **điều kiện áp dụng** của quy định chuyển tiếp (ví dụ "hành vi xảy ra trước hay sau ngày hiệu lực?", "có thuộc trường hợp được áp dụng quy định cũ?"). Cần thận trọng vì checklist sinh bằng LLM.
3. **Thiết kế thí nghiệm "chèn nhiễu có tương đồng cao"** (Bảng 1): thêm 2/4/6 tài liệu "giống nhưng không áp dụng" làm giảm ACC; trong ViLexTime, tài liệu nhiễu tự nhiên chính là **các phiên bản khác của cùng điều** (đồng thời là nhiễu mà bài 01 gọi là near-identical) → có thể làm thí nghiệm "tăng số phiên bản nhiễu" để chứng minh nhạy cảm với phiên bản.
4. **Chỉ số Traceable Correct / Untraceable Correct**: tách "đúng và có căn cứ" khỏi "đúng nhưng không truy hồi được bằng chứng" — rất hợp với đánh giá **provenance** của bài 01; ViLexTime nên báo "đúng đáp án nhưng trích sai phiên bản".
5. **Phân tầng tri thức** (sự kiện / quy tắc / nguyên tắc; Fact–Ontology–Rule): tương tự phân tầng trong khung của ViLexTime (văn bản gốc, văn bản sửa đổi, hướng dẫn). "Granularity bias" gợi ý rằng việc tách kho theo loại nội dung (điều luật / văn bản sửa đổi / án lệ) có thể cải thiện truy hồi 25,3% (số từ bài, ở hình không đọc được chi tiết).
6. **Ablation theo module** (HierarGraph, Researcher, Auditor, từng toán tử truy hồi) là mẫu trình bày ablation; thêm "w/o temporal filter" cho ViLexTime.
7. **Bài học về baseline**: GraphRAG chuẩn (LightRAG, G-Retriever) có thể kém hơn LLM không truy hồi trong pháp lý nếu đồ thị không nhận biết cấu trúc → hỗ trợ lập luận "đồ thị phải theo cấu trúc pháp lý, không phải đồ thị thực thể chung".
8. **Chi phí/độ trễ**: khai báo chi phí lập chỉ mục và truy vấn như Bảng 7 (thời gian, token prompt/completion, token/truy vấn).
9. **Cẩn trọng**: miền hình sự Trung Quốc, không có thời gian; tránh trích như bằng chứng cho hiệu quả temporal. Có thể dùng làm related work cho "GraphRAG pháp lý nhiều agent với xác minh".
