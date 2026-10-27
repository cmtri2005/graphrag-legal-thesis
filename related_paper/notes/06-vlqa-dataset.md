# VLQA: The First Comprehensive, Large, and High-Quality Vietnamese Dataset for Legal Question Answering

> Ghi chú đọc chi tiết cho khóa luận ViLexTime. Nguồn: `related_paper/VLQA_ ... .pdf` (26 trang). Bảng số liệu lấy từ văn bản trích xuất PDF.

## 0. Thông tin chung

| Mục | Nội dung |
|---|---|
| Tác giả | Tan-Minh Nguyen (JAIST), Hoang-Trung Nguyen (VNU-UET), Trong-Khoi Dao (Khoa Luật ĐHQG Hà Nội), Xuan-Hieu Phan (VNU-UET), Ha-Thanh Nguyen (NII, Nhật), Thi-Hai-Yen Vuong\* (VNU-UET) |
| Nơi đăng | arXiv:2507.19995v1 [cs.CL], 26/07/2025; bản thảo gửi ACM ("Manuscript submitted to ACM", chưa rõ hội nghị) |
| Dữ liệu | Tác giả nêu "sẽ công bố sớm" dataset, mã nguồn, checkpoint (chưa thấy đường dẫn trong PDF) |
| Quy mô | **3.129** bộ ba {câu hỏi, điều luật liên quan, câu trả lời dài}; **59.636** điều luật; **2.162** văn bản; **27** lĩnh vực |
| Độ gần với ViLexTime | Trung bình: là dataset QA pháp lý tiếng Việt lớn, nguồn **câu hỏi thật của người dân**, có ví dụ minh họa trực tiếp vấn đề **đáp án lỗi thời do văn bản bị sửa** (lương cơ sở 1.490.000 → 1.800.000), nhưng **loại bỏ** các mẫu dính văn bản hết hiệu lực thay vì mô hình hóa thời gian |

## 1. WHY – Bài toán

- Các nghiên cứu LQA/LAR (legal QA / statutory article retrieval) hiện hẹp: tập trung một lĩnh vực nhỏ (thuế, quyền dân sự), đầu ra hạn chế (nhị phân yes/no hoặc span ngắn).
- Tiếng Việt là ngôn ngữ ít tài nguyên: thiếu kho có nhãn để huấn luyện có giám sát, kiểm định và fine-tune.
- Các bộ pháp lý hiện có thường lấy từ **đề thi** (COLIEE 1.206 câu từ kỳ thi luật sư Nhật, ALQAC 100 cặp), khác với câu hỏi thật của người không chuyên (rộng và đơn giản hơn).
- Mục tiêu: dataset lớn, đa lĩnh vực, **câu hỏi thật của công dân**, được **chuyên gia xác minh**, có cả **điều luật liên quan** (retrieval) lẫn **câu trả lời dạng dài** (QA).

### Bảng 1 – So sánh dataset LQA hiện có (theo bài)
| Dataset | Từ/câu hỏi | Từ/chứng cứ | Từ/đáp án | Số câu hỏi | Số chứng cứ | Dạng đáp án | Miền | Nguồn | Ngôn ngữ |
|---|---|---|---|---|---|---|---|---|---|
| COLIEE 2024 | 40,24 | 73,09 | 1 | 1.206 | 768 | Nhị phân | Luật dân sự | Đề thi | ja, en |
| JEC-QA | 47 | 58 | 15 | 26.365 | 3.382 | MCQ | Luật thành văn | Đề thi | zh |
| PrivacyQA | 8 | 3.237 | 140 | 1.750 | 335 | Đa span | Chính sách riêng tư | Luật gia | en |
| EQUALS | 32 | 252 | 69 | 6.914 | 3.081 | Dài | Luật thành văn | Diễn đàn web | zh |
| LLeQA | 15 | 1.857 | 264 | 1.868 | 27.942 | Dài | Luật thành văn | Luật gia | fr |
| ALQAC 2023 | 24,91 | 184,07 | 1,94 | 100 | 2.131 | Nhị phân, MCQ | Luật thành văn | Luật gia | vi |
| **VLQA** | 19,78 | 303,49 | 216,74 | **3.129** | **59.636** | **Dài** | Luật thành văn | Diễn đàn web | vi |

Các dataset khác nhắc: CJRC (50.000+ cặp từ 10.000 vụ, tiếng Trung), CAIL2018 (2,6 triệu vụ hình sự), ECtHR, CAIL2019-SCM, BSARD (Louis & Spanakis: 1.108 câu hỏi, 22.633 điều luật Bỉ, tiếng Pháp, từ tổ chức tư vấn pháp lý), ViRHE4QA (9.758 câu, 294 điều, quy chế đại học VN).

## 2. HOW – Xây dựng dataset

### 2.1 Bốn pha (Hình 1)
1. **Kho điều luật**: chọn **2.162 văn bản** thuộc **27 lĩnh vực** phổ biến; tách từng điều và giữ **cấu trúc phân cấp** (văn bản, phần, mục, chương). Loại các văn bản trùng tiêu đề nhưng khác chủ đề (tránh nhập nhằng); regex sửa lỗi chính tả và ký tự lạc; **loại các điều đã bị bãi bỏ bởi luật trước nhưng vẫn còn trong văn bản nguồn**. Kết quả: **59.636 điều**, tổ chức phân cấp; điều là đơn vị truy hồi cơ bản. Thống kê Bảng 5: 8.316 chương, 11.409 mục, 59.636 điều; lĩnh vực lớn nhất Hệ thống hành chính (8.566 điều, 1.381 chương), Thương mại (4.748), Kinh doanh (3.816), Giao thông vận tải (3.017), Tài nguyên môi trường (2.922); nhỏ: Sở hữu trí tuệ (737), Chứng khoán (799).
2. **Bộ ba câu hỏi–đáp–điều luật**: thu **~430.000** câu hỏi thô từ các website tư vấn pháp luật của VN (hôn nhân, thuế, lao động...). Làm sạch: loại câu hỏi viện dẫn **cả văn bản**, **điều bị bãi bỏ**, hoặc điều không có trong kho; gộp câu hỏi trùng nội dung khác nhãn phân loại. Câu trả lời của luật sư có nêu rõ điều luật ("Điều 5 Bộ luật Dân sự 2015", "Điều 2 của bộ luật này") → dùng **regex** trích tham chiếu rồi gióng vào kho; loại câu không trích được điều. Cấu trúc câu trả lời tư vấn (phân tích → viện dẫn điều → kết luận) được khai thác bằng regex để tách đoạn; lọc ngôn từ không trang trọng, từ không phải tiếng Việt, icon (regex và SpaCy fastlang). Quy mô qua các bước (Hình 3): **427.310 → 15.842 → 3.180 → 3.129** (thu thập → làm sạch → chú giải → xác minh).
3. **Xác minh chuyên gia**: **5 sinh viên luật năm cuối** (annotator) + **1 chuyên gia luật** (reviewer/giám sát). Đào tạo và hướng dẫn trước. Công cụ chú giải tự xây bằng **Streamlit** (Hình 2). **Mỗi cặp hỏi-đáp được hai annotator chú giải độc lập** để giảm thiên lệch cá nhân. Mỗi annotator ghi: *Verify answer* (True/False), *Modify answer* (kèm nói rõ thiếu/thừa...), *Verify relevant law* (True/False), *Modify relevant law*, *Feedback*.
4. **Rà soát chuyên gia** theo 3 tiêu chí: **Clearness** (câu hỏi đủ cụ thể để truy hồi), **Validity** (câu trả lời viện dẫn điều **còn hiệu lực**; **mẫu nào viện dẫn văn bản bị bãi bỏ hoặc lỗi thời thì loại**), **Fluency** (người không chuyên đọc được, đúng ngữ pháp). Không đạt thì sửa hoặc loại.
   Chia tập **7:1:2** (train/dev/test) — khoảng 2.190 / 313 / 626 (suy ra từ tỷ lệ, bài không ghi số chính xác; bài nhắc "2.1k mẫu in-domain" để huấn luyện).

### 2.2 Chất lượng nhãn (Bảng 3) – số liệu minh bạch về mức sửa của chuyên gia
| Kết quả rà soát | Số lượng | % |
|---|---|---|
| Khớp hoàn toàn (đáp án và điều luật không đổi) | 2.321 | 74,18% |
| Sửa điều luật, giữ đáp án | 464 | 14,83% |
| Sửa đáp án, giữ điều luật | 119 | 3,80% |
| Sửa cả đáp án và điều luật | 225 | 7,19% |
| **Tổng** | **3.129** | 100% |

→ **25,82%** mẫu cần chuyên gia can thiệp. Ví dụ minh họa quan trọng (Bảng 4): câu "lương cơ sở" gốc "hiện nay lương cơ sở là **1.490.000 đồng/tháng**" (viện dẫn **Điều 2 Nghị định 38/2019/NĐ-CP**) → sau xác minh "Từ **ngày 01/7/2023**, lương cơ sở là **1.800.000 đồng/tháng**" (viện dẫn **Điều 3 Nghị định 24/2023/NĐ-CP**), vì Nghị định 38/2019 đã được Nghị định 24/2023 sửa đổi. Tác giả nói rõ: nhãn gốc do luật sư tư vấn trên diễn đàn có thể lỗi thời → chuyên gia cập nhật.
- Ví dụ giao diện: câu "Nếu người lao động không nghỉ việc khi nhận con nuôi thì trợ cấp một lần BHXH là bao nhiêu?" → "2 lần mức lương cơ sở tại tháng, tương đương 2.980.000 đồng" (dựa Điều 31, 38 Luật BHXH, Điều 11 Thông tư 59/2015/TT-BLĐTBXH, Điều 2 và 3 Nghị định 38/2019/NĐ-CP), cho thấy nhãn liên quan thường **nhiều văn bản xếp tầng**. Nhận xét của người đọc (bài không nói): 2.980.000 = 2 × 1.490.000, tức là con số trong ví dụ giao diện dùng mức lương cơ sở cũ; ví dụ này chưa được tác giả bàn về tính cập nhật.

### 2.3 Thống kê và đa dạng (mục 3.2)
- Độ dài trung bình (từ): câu hỏi **19,78**, điều **303,49**, đáp án **216,74**; phân bố lệch trái.
- **Số điều liên quan/câu hỏi**: trung bình **1,33**, tối đa **9**. Phân bố (Hình 4d, đọc từ nhãn cột của biểu đồ): 1 điều: **2.352** câu; 2 điều: **596**; 3: **123**; 4: **40**; 5: **10**; 6: 3; 7: 3; 8: 1; 9: 1. **94%** câu hỏi dẫn ≤ 2 điều; 6% dẫn 3–9 điều (thường cần lập luận phức tạp hay thông tin bổ sung về điều bị bãi bỏ/tham chiếu chéo).
- **Loại câu hỏi** (thủ công, 8 loại): **How 36%**, **What 27,1%**, binary, which, when, who, where, other. Which/when/who/where < 9% cộng lại. (Hình 5: How 1.128; What 849; Binary 676; Other 197; Which 102; When 88; Who 70; Where 19.)
- **Loại lập luận** (Bảng 7, một câu có thể có nhiều loại): **diễn giải ngữ nghĩa (semantic interpretation) 59%**; khớp từ vựng (lexical matching); **suy luận logic ~1/5** (có/không, điều kiện); **đọc nhiều điều (multi-article) ~25%** — "đòi hỏi tích hợp và dung hòa thông tin giữa nhiều điều, thường kèm tham chiếu chéo và **lập luận thời gian (temporal reasoning, tức điều bị bãi bỏ)**".
- **Chủ đề**: Hệ thống hành chính 14,67% (gấp đôi Kinh doanh); Sở hữu trí tuệ, Xuất nhập khẩu, Chứng khoán < 3% mỗi loại.

## 3. Mô hình cơ sở (baselines)

### 3.1 Truy hồi điều luật
- **Thưa**: BM25 (k1 = 1,2; b = 0,75), fastText (Doc2Vec-style).
- **Zero-shot dày**: bi-encoder SBERT tiếng Việt (`keepitreal/vietnamese-sbert`), **BGE-m3**.
- **Có giám sát (2 giai đoạn)**: BM25 xếp hạng sơ bộ → cross-encoder fine-tune (mBERT, BGE-reranker-v2-m3), mất mát BCE, 5 epoch, Adam lr 2e-5, batch 32, **5 mẫu âm** từ top-k BM25; độ dài tối đa 512 (mBERT)/1024 (BGE-rerank); **bể ứng viên giảm xuống top-200 BM25**.
- Chỉ số: Recall@k (k = 1,2,5,10,20,50,100,200,500,1000), Precision@2, F2@2 (β=2, ưu tiên recall), MAP, MRR, NDCG ở k=2.

### 3.2 Hỏi đáp (đầu vào là câu hỏi + top-k điều)
- **Trích xuất (extractive)**: mBERT, LegalBERT, XLM-RoBERTa, PhoBERT, ViDeBERTa. Do đáp án vàng do con người viết không khớp nguyên văn điều luật, nhóm dựng **nhãn bạc (silver label)**: tách điều thành câu, gióng với đáp án vàng để chọn câu là đáp án, gộp lại thành đáp án bạc; mô hình dự đoán xác suất một câu thuộc đáp án (softmax trên [CLS]).
- **Sinh (generative)**: ViT5, BARTpho (đầu vào tối đa 1024 token; BARTpho dùng VnCoreNLP tách từ trước; giải mã tham lam).
- **In-context learning**: Qwen2.5-7B/14B-Instruct, Llama3-8B, Llama3.1-8B, **GPT-4o, GPT-4o-mini, DeepSeek-V3**; zero-shot và two-shot (ví dụ lấy từ dev); open-weight chạy cục bộ bằng vLLM, giải mã tham lam.
- Chỉ số QA: ROUGE-1/2/L và BERTScore; **đánh giá người** bởi chuyên gia pháp lý (lỗi thật, thiếu sót, hiểu sai) trên 100 mẫu ngẫu nhiên của test.

## 4. WHAT – Kết quả

### 4.1 Truy hồi
**Bảng 8 – Recall zero-shot**
| Mô hình | R@1 | R@2 | R@5 | R@10 | R@20 | R@50 | R@100 | R@200 | R@500 | R@1000 |
|---|---|---|---|---|---|---|---|---|---|---|
| fastText | 0,1380 | 0,2281 | 0,3310 | 0,4044 | 0,4781 | 0,5446 | 0,6006 | 0,6713 | 0,7475 | 0,7986 |
| SBERT | 0,1274 | 0,1733 | 0,2841 | 0,3579 | 0,4476 | 0,5695 | 0,6518 | 0,7325 | 0,8100 | 0,8522 |
| BM25 | 0,2670 | 0,3835 | 0,5221 | 0,6139 | 0,6928 | 0,7678 | 0,8232 | 0,8651 | 0,9113 | 0,9318 |
| **BGE-m3** | **0,4323** | **0,5442** | **0,6928** | **0,7814** | **0,8449** | **0,9099** | **0,9348** | **0,9610** | **0,9691** | **0,9800** |

**Bảng 9 – Kết quả ở k = 2**
| Mô hình | P@2 | R@2 | F2@2 | MAP@2 | MRR@2 | NDCG@2 |
|---|---|---|---|---|---|---|
| SBERT | 0,1045 | 0,1733 | 0,1531 | 0,1808 | 0,1794 | 0,1883 |
| fastText | 0,1348 | 0,2281 | 0,2003 | 0,2139 | 0,2153 | 0,2313 |
| BM25 | 0,2265 | 0,3835 | 0,3368 | 0,3278 | 0,3780 | 0,4017 |
| BGE-m3 | 0,3222 | 0,5442 | 0,4783 | 0,4921 | 0,5654 | 0,5925 |
| BGE-rerank (2 giai đoạn) | 0,3437 | 0,5845 | 0,5127 | 0,5504 | 0,6467 | 0,5869 |
| **mBERT-ft** (2 giai đoạn) | **0,3740** | **0,6257** | **0,5515** | **0,5757** | **0,6675** | **0,6179** |

Nhận xét tác giả: BGE-m3 vượt trội; BM25 vẫn là baseline mạnh, hiệu quả; fastText/SBERT yếu khi không tinh chỉnh. mBERT fine-tune trên **2,1k** mẫu VLQA vượt hẳn các baseline zero-shot → **thích nghi miền rất quan trọng**. **Mọi mô hình có Precision@2 < 0,40** → dưới một nửa điều trả về là liên quan; còn nhiều dư địa.

### 4.2 Hỏi đáp
**Bảng 10 – Trích xuất và sinh**
| Mô hình | ROUGE-1 | ROUGE-2 | ROUGE-L | BERTScore |
|---|---|---|---|---|
| LegalBERT | 0,4528 | 0,4235 | 0,2271 | 0,6549 |
| ViDeBERTa | 0,5065 | 0,4754 | 0,2530 | 0,7104 |
| mBERT | 0,5114 | 0,4786 | 0,2561 | 0,7090 |
| XLM-RoBERTa | 0,5187 | 0,4872 | 0,2617 | 0,7314 |
| PhoBERT | 0,5423 | 0,5088 | 0,2683 | 0,7304 |
| ViT5 | 0,4332 | 0,3198 | 0,3210 | 0,7666 |
| BARTpho | 0,4695 | 0,3827 | 0,3318 | 0,7872 |

Trích xuất tốt hơn sinh ở ROUGE-1/2; sinh tốt hơn ở BERTScore. **LegalBERT** (tiền huấn luyện miền luật, dù fine-tune trên VLQA) **tệ nhất** ở mọi chỉ số — tác giả diễn giải: hiểu ngôn ngữ (tiếng Việt) quan trọng hơn miền (vì LegalBERT là tiếng Anh).

**Bảng 11 – LLM (zero-shot / two-shot)**
| Mô hình | R-1 (0/2) | R-2 (0/2) | R-L (0/2) | BERTScore (0/2) |
|---|---|---|---|---|
| Llama3.1-8B | 0,4384 / 0,4313 | 0,3709 / 0,3681 | 0,3807 / 0,3779 | 0,7431 / 0,7414 |
| Qwen2.5-7B | 0,4988 / 0,4854 | 0,4190 / 0,4102 | 0,4250 / 0,4153 | 0,7263 / 0,7231 |
| Llama3-8B | 0,5720 / 0,5698 | 0,4967 / 0,4966 | 0,5007 / 0,5005 | 0,7745 / 0,7739 |
| Qwen2.5-14B | 0,6017 / 0,5995 | 0,5138 / 0,5118 | 0,5197 / 0,5179 | 0,7614 / 0,7613 |
| DeepSeek-V3 | 0,6704 / 0,6809 | 0,5307 / 0,5631 | 0,5165 / 0,5567 | 0,7769 / 0,8022 |
| GPT-4o | 0,6824 / 0,7040 | 0,5917 / 0,5993 | 0,5979 / 0,5912 | 0,8296 / 0,8233 |
| **GPT-4o-mini** | **0,6975 / 0,7137** | **0,6011 / 0,6219** | **0,6001 / 0,6192** | **0,8314 / 0,8339** |

GPT-4o-mini cao nhất mọi chỉ số, mọi thiết lập. Qwen2.5-14B tốt nhất trong nhóm open-weight. Hai ví dụ (two-shot) cải thiện ở mô hình lớn (GPT-4o, DeepSeek-V3) nhưng có thể **làm giảm** ở mô hình <14B (giới hạn độ dài đầu vào, trí nhớ nội tại). BARTpho fine-tune (nhỏ) ≈ Llama3.1-8B. Lưu ý: LLM được **cấp sẵn điều luật liên quan** (đầu vào "top-k điều"), nên điểm không đo năng lực truy hồi.

**Bảng 12 – Theo loại lập luận (two-shot)**
| Loại lập luận | Qwen2.5-14B (R-1/R-2/R-L/BERTScore) | GPT-4o-mini (R-1/R-2/R-L/BERTScore) |
|---|---|---|
| Lexical Matching | 0,6520/0,5796/0,5811/0,7826 | 0,7709/0,7007/0,6983/0,8592 |
| Multi-Article Reading | 0,6211/0,5210/0,5165/0,7754 | 0,6857/0,5744/0,5650/0,8154 |
| Semantic Interpretation | 0,5579/0,4581/0,4679/0,7445 | 0,6684/0,5595/0,5566/0,8138 |
| Logical Inference | 0,4835/0,3605/0,3772/0,7242 | 0,5619/0,4389/0,4460/0,7882 |
| Tất cả | 0,5995/0,5118/0,5179/0,7613 | 0,7137/0,6219/0,6192/0,8339 |

Điểm giảm dần từ khớp từ vựng → diễn giải ngữ nghĩa → suy luận logic: hạn chế ở lập luận phức tạp.

### 4.3 Phân tích lỗi thủ công (Bảng 13; 100 mẫu test)
| Loại lỗi | PhoBERT | Qwen2.5-14B | GPT-4o-mini |
|---|---|---|---|
| Lỗi cú pháp (định dạng, ngôn ngữ, ký tự không Unicode) | 12 | 40 | 0 |
| Dư thừa | 11 | 2 | 2 |
| Thiếu ý (incomplete) | 22 | 8 | 6 |
| Sai logic | 0 | 2 | 5 |
| **Tổng lỗi** | 45 | 52 | 13 |

- Câu trả lời LLM ngắn hơn vàng (Qwen2.5 trung bình **159** từ, GPT-4o-mini **172**, vàng **198**) → phần lớn lỗi ngữ nghĩa là trả lời thiếu.
- GPT-4o-mini mạch lạc nhưng phần lớn đầu ra chưa đầy đủ hoặc sai logic (đặc biệt câu suy luận logic); hay **chép nguyên văn cả điều thay vì trả lời câu hỏi**.
- Qwen2.5-14B điểm tự động cao nhưng **chính xác thấp hơn PhoBERT** theo đánh giá người; **77%** lỗi sai của nó là lỗi cú pháp (câu vô nghĩa, ký tự không Unicode).
- **Điểm quan trọng**: điểm tự động (ROUGE/BERTScore) cao đi cùng hoạt động thực tế còn sai; "khoảng cách giữa sinh văn bản trôi chảy và lập luận pháp lý vững".

### 4.4 Ví dụ hallucination (Phụ lục B)
- Bảng 14: câu "Phạt bao nhiêu khi đi xe máy ngược chiều?" – đáp án vàng 400.000–600.000 đồng; GPT-4o-mini nêu 1.000.000–2.000.000 đồng (Điều 6 NĐ 100/2019/NĐ-CP); Qwen-2.5-14B nêu 2.000.000–3.000.000 đồng (Điều 5 khoản 5) – cả hai trích **nhầm đoạn** trong ngữ cảnh được cung cấp.
- Bảng 15: câu về nguyên tắc xác định học phí mầm non – vàng viện **Khoản 1 Điều 8 Nghị định 81/2021/NĐ-CP**; GPT-4o-mini viện "Điều 8 **Luật Giáo dục 2019**" (bịa tên văn bản); Qwen viện "văn bản pháp lý được cung cấp".
- **Liên quan trực tiếp ViLexTime**: ví dụ mức phạt giao thông tại Bảng 14 là loại thông tin thay đổi theo từng Nghị định xử phạt (NĐ 100/2019 sau này bị thay thế); đây là dạng "mức phạt" mà các nghiên cứu khác cho là nhạy cảm với thời điểm, nhưng bài VLQA không phân tích khía cạnh đó.

## 5. Hạn chế và nhận xét phê phán
- **Tác giả không có mục hạn chế riêng**; mục kết luận chỉ nêu hướng tương lai (end-to-end framework cho văn bản dài, truy vấn phức tạp).
- Câu hỏi và đáp án gốc do **luật sư tư vấn trên diễn đàn** trả lời, rồi sinh viên luật xác minh (không phải luật sư hành nghề); **chỉ 1 chuyên gia luật** rà cuối. Không báo **hệ số đồng thuận giữa hai annotator** (chỉ báo mức sửa của reviewer 74,18% khớp hoàn toàn).
- Nhãn "điều luật liên quan" trích bằng **regex từ câu trả lời của luật sư**: có thể thiếu điều liên quan mà luật sư không nêu (rủi ro recall nhãn thấp), điều này làm Precision@k bị đánh giá thấp một cách hệ thống (tác giả đã thấy P@2<0,40).
- Kho gồm **văn bản còn hiệu lực tại thời điểm xây** (đã loại điều bị bãi bỏ); mẫu dính văn bản hết hiệu lực bị loại. Không có kho phiên bản lịch sử, không có tác vụ "bản có hiệu lực tại ngày X". Dataset sẽ lỗi thời khi luật đổi.
- Phần lớn đánh giá QA dựa **ROUGE/BERTScore** – tự bài nói là kém tin cậy với QA pháp lý; đánh giá người chỉ 100 mẫu và 3 hệ.
- Đã cấp sẵn điều luật cho mô hình QA; không đo hiệu quả pipeline truy hồi→trả lời end-to-end.
- Bản thảo chưa gắn hội nghị; dataset "sẽ công bố"; cần kiểm lại trạng thái phát hành trước khi trích.

## 6. Dùng gì cho khóa luận ViLexTime
1. **Bằng chứng có sẵn cho động lực thời gian**: Bảng 4 (lương cơ sở 1.490.000 → 1.800.000, Nghị định 38/2019 → Nghị định 24/2023, hiệu lực 01/7/2023) và thống kê **7,19%** mẫu cần sửa cả đáp án và điều vì văn bản đổi → dẫn chứng cụ thể rằng dữ liệu QA pháp lý VN **lỗi thời theo thời gian** và các tác giả phải xử lý thủ công. Số 25,82% mẫu cần chuyên gia can thiệp cho thấy chi phí thủ công.
2. **Mẫu quy trình**: crawl diễn đàn tư vấn → regex gióng điều luật → lọc → hai annotator độc lập → reviewer với ba tiêu chí (Clearness, Validity, Fluency) → chia 7:1:2. Phần "Validity = chỉ giữ mẫu viện dẫn văn bản còn hiệu lực" là nơi ViLexTime có thể thay "loại bỏ" bằng "gắn nhãn thời điểm".
3. **Baseline truy hồi tiếng Việt**: BM25 mạnh, BGE-m3 zero-shot vượt, hai giai đoạn BM25→cross-encoder fine-tune tốt nhất; số liệu R@k để so sánh; **bể ứng viên 200 từ BM25** là cấu hình tham khảo cho rerank.
4. **Phân loại câu hỏi** theo loại câu (How/What/Binary/...) và theo kiểu lập luận (khớp từ vựng/diễn giải/logic/nhiều điều) có thể bổ sung chiều "thời gian" làm trục thứ ba cho ViLexTime.
5. **Kho điều luật cấp Điều** (59.636 điều/27 lĩnh vực) là nguồn tham khảo cho cấu trúc phân cấp và có thể là nguồn mẫu câu hỏi người dân thật; cần kiểm tra giấy phép khi dùng.
6. **Cẩn trọng**: điểm ROUGE/BERTScore không phản ánh đúng đắn pháp lý; nếu trích kết quả LLM của VLQA nên kèm cảnh báo của chính tác giả. Dataset chưa chắc đã phát hành đầy đủ.
