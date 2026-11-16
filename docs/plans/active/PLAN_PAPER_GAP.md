# PLAN_PAPER_GAP: đưa khóa luận và paper ViLexTime lên mức mạnh nhất

Date: 2026-11-15

## Status

Đang chạy từ 15/11. CMT đã chốt Q1 (người đọc chính) và Q2. Q3–Q7 và người đọc thứ hai còn chờ.

Plan này nối `REFACTOR_PLAN.md` (các nhóm 1, 3, 5, 6 còn mở) và `docs/paper/PAPER_GAP.md` (mục 7–8).
`REFACTOR_PLAN.md` giữ làm sổ kết quả đã có. Tiến độ việc mới ghi ở đây. Không thay ADR nào.

Nhãn bằng chứng: **[XM]** đã kiểm trong repo hôm nay; **[SL]** suy luận; **[GT]** giả thuyết, phải đo.

## 1. Đọc trong 2 phút

- **Paper đã có câu chuyện đủ mạnh.** Chỉ số truy xuất quen dùng không thấy lỗi sai phiên bản: MRR 0,445 so với 0,456, trong khi đúng cả cặp (TCS) 7% so với 65% [XM]. Việc còn lại là làm cho người đọc **tin** câu chuyện đó.
- **Ba thứ quyết định paper có được nhận không**, theo thứ tự:
  1. Người độc lập kiểm thước đo (gold mù, nhãn, cờ sai phiên bản). Thiếu thì reviewer bác ngay.
  2. Kết luận giữ nguyên khi đổi generator (model mở) và khi retriever mạnh hơn.
  3. Trình bày: một hình, hai bảng, khung pháp lý, ẩn danh.
- **Điểm nghẽn là giờ người, không phải máy.** Cần khoảng 30 giờ người trong ba tuần tới. Phải bắt đầu tuần này, chạy song song với máy.
- **Không dựng bộ test mới trước 28/01.** Hiệu chính lớn (+0,3), KTC xa 0. Nhãn "thăm dò có khai trước" là đủ cho các phép kiểm độ bền.
- **Hai mốc cứng:** khóa luận 26/12/2026; ICAIL 28/01/2027.
- **Cần CMT chốt** (mục 8): còn Q3–Q7 và người đọc thứ hai của gold mù. Q1, Q2 đã chốt 15/11.

## 2. Outcome

Đo được, không phải cảm nhận.

**Khóa luận (26/12):**
- Mọi `[CHỜ]`, `[CẦN]` trong 7 chương được điền số hoặc ghi rõ "không làm, vì sao".
- RQ1 có cả hai vế. RQ2 có LightRAG thật. RQ3 có thêm hai phép kiểm độ bền.
- Ba câu hỏi hội đồng chắc chắn hỏi đều có **số mới** để trả lời, không chỉ lời giải trình (mục 6, WP-E).
- Demo trả lời một câu trong thời gian trình diễn được.

**Paper (28/01):**
- Bảy khẳng định ở mục 4 đều đạt cột "mức cần có".
- Bản ACM `sigconf` ẩn danh, tối đa 10 trang, qua `paper_check.py` và `evidence-gate`.
- Không còn lý do loại vì hình thức (mẫu, ẩn danh, preprint, model mở).

## 3. Hiện trạng ngày 15/11 [XM]

### 3.1. Số đã có trên bộ cuối (318 dòng, hai lần chạy)

| Hệ | Accuracy | Sai phiên bản | TCS | MRR |
|---|---|---|---|---|
| Lai ghép phẳng (`b4`) | 0,324 / 0,296 | 0,291 / 0,294 | 0,071 / 0,047 | 0,445 |
| Lọc theo ngày văn bản (`b7`) | 0,487 / 0,509 | 0,177 / 0,162 | 0,315 / 0,346 | 0,493 |
| Lọc theo khoảng phiên bản (`b7plus`) | 0,654 / 0,648 | 0,008 / 0,011 | 0,654 / 0,646 | 0,456 |
| Cấu hình đầy đủ (`proposed2`) | 0,667 / 0,664 | 0,008 / 0,008 | 0,661 / 0,646 | 0,453 |
| In ngày vào prompt (`bvdate`) | 0,409 / 0,418 | 0,064 / 0,060 | — | — |
| LightRAG | 0,346 / 0,355 | 0,355 / 0,351 | 0,055 / 0,055 | — |
| Oracle đúng mốc | 0,956 / 0,959 | 0 | 0,961 / 0,969 | 1 |
| Oracle bản hiện hành | 0,456 / 0,456 | 0,502 | 0 | 1 |

Nguồn: `runs/final_g4_20261112/{r1,r2}/test/all.score.json` (đọc lại hôm nay, khớp PAPER_GAP); `bvdate` và LightRAG chép từ `REFACTOR_PLAN.md`.

### 3.2. Việc trong PAPER_GAP: xong, đang làm, chưa làm

| Việc | Trạng thái | Ghi chú |
|---|---|---|
| P0-1 TCS, MRR vào paper | Xong trong paper | Số **chưa qua evidence-gate** |
| P0-2 Người chấm cờ sai phiên bản | Phiếu 33 câu đã dựng, **chưa chấm** | `data/review/human_score_g4/recheck_versions/phieu.xlsx` |
| P0-3 Generator mở | **Dev xong 15 hệ** (16/11, gồm `bvnone`, `bvdate`; evidence-gate PASS) | `runs/qwen_gen_20261115/`, dòng sổ chạy 15/11. Thứ tự hệ giữ. Bộ cuối cần amendment |
| P0-4 Gold mù người trên bộ cuối | Chưa | Hiện phủ 24/156 lineage, 0 dòng T6 |
| P0-5 Người thứ hai kiểm nhãn | Chưa | |
| P0-6 Ẩn danh, preprint | Bản ACM ẩn danh có rồi. Repo công khai vẫn chứa bản thảo | `develop` đã push, trùng `origin` |
| P0-7 Mẫu ACM | Xong, 8/10 trang | Còn 2 trang cho nội dung mới |
| P1-1 Retriever mạnh | Code reranker nằm trong working tree, **chưa commit, chưa chạy** | 35 test qua. Kế hoạch chính ghi "reranker cắt 05/11" |
| P1-2 LightRAG | Xong, thăm dò | Số chưa qua evidence-gate; thiếu log và revision từ Colab |
| P1-3 Bãi bỏ | Chưa | 7/23 |
| P1-4 Câu hỏi thật | Chưa | |
| P1-5 Vế LLM của RQ1 | Chưa | |
| P2-6 Sửa đáp án ngắn T1 | Nháp amendment có, chờ duyệt | Oracle T1 2/43 lên 37/43 |
| W1–W6, W8 | Xong | |
| W7, W9–W12 | Chưa | |

Khóa luận: còn 50 chỗ `[CHỜ]`, `[CẦN]` (chương 6: 11 + 1; chương 2: 13; chương 4: 7 + 2; chương 5: 2 + 3; chương 1: 3; chương 3: 1 + 2). Bảng từng chỗ ở mục 6, WP-E chi tiết. Chương 6 mới nhắc LightRAG một lần, chưa có Qwen3.8 và reranker.

### 3.3. Sáu điều thấy thêm khi rà, PAPER_GAP chưa ghi

1. **Gói Qwen thiếu `bvnone` và `bvdate`.** `colab_upload/qwen_gen/dev/` có 13 hệ, không có hai hệ này. "Lọc cứng hơn in ngày 0,245" là một trong ba số chính của abstract. Reviewer sẽ hỏi: model lớn hơn có tự dùng được ngày không? Prompt đã có sẵn ở `runs/posthoc_g4_20261113/{dev,test}/prompts/`. Thêm vào gói là xong.
2. **CMT không còn mù.** CMT đã duyệt mọi dòng bộ cuối, có thấy đáp án của kho. Gold mù phải do người khác đọc [SL]. Người gán A của các vòng cũ cũng đã thấy đáp án của 51/132 lineage chưa có gold (qua `kiem_A.tsv`); người gán B thấy 16, đều nằm trong 51 đó [XM].
3. **Reranker không chạy nổi trên máy này.** Máy không có GPU (4 nhân, 8 GB) [XM]; `retrieve.py` ghi cứng `device="cpu"`. 512 truy vấn × 100 ứng viên × vài hệ thì quá chậm [SL]. Phần chấm cặp (câu hỏi, đoạn) phải đưa lên Colab.
4. **Chế độ `ranh_gioi` có dữ liệu, chưa có dự đoán.** File release có đủ 722 dòng (361 × 2 chế độ); file điểm toàn số 0.
5. **Paper còn đúng 2 trang.** Mọi nội dung thêm phải vừa 2 trang (ngân sách ở WP-D).
6. **Lần Colab LightRAG thiếu log, phiên bản thư viện, revision model.** Lần Qwen này phải lưu đủ ngay từ đầu.

## 4. Chiến lược: bảy khẳng định và bằng chứng cần có

Paper mạnh khi mỗi khẳng định có bằng chứng độc lập với chính hệ của tác giả.

| # | Khẳng định | Bằng chứng hiện có | Mức cần có | Việc |
|---|---|---|---|---|
| C1 | RAG phẳng trích sai phiên bản 25–29%; MRR không thấy lỗi này | Theo scorer; một generator; retriever yếu | Người xác nhận cờ; giữ với model mở; giữ với retriever mạnh | A1, B1, B2 |
| C2 | Đọc bản hiện hành mất nửa điểm (0,956 xuống 0,456) | Một generator | Giữ với model mở | B1 |
| C3 | Thứ khử lỗi là lọc cứng theo khoảng trên kho phiên bản; in ngày không thay được | Xác nhận (F4, F5) và thăm dò (`b7v`, `bvdate`) | Giữ với model mở và retriever mạnh; giữ trên phần có gold người | B1, B2, A2 |
| C4 | GraphRAG thật không hơn RAG phẳng ở bài này | LightRAG, thăm dò | Số qua gate; khai ba chỗ không ngang hàng | D1 |
| C5 | Benchmark đo đúng luật | Gold mù 24/156; nhãn AI | Gold mù người khoảng 2/3 bộ cuối, đủ T6; đồng thuận người–người và người–AI | A2, A3 |
| C6 | Lọc không làm hại điều khoản không đổi | Cột T1 hỏng | Cột T1 chấm lại theo amendment | B4 |
| C7 | LLM không truy xuất không biết phiên bản nào áp dụng | Accuracy 0,006, thước không hợp | Phép chọn một trong hai, 2–3 model | B3 |

Bãi bỏ (T6) **không** nằm trong bảng. Viết thẳng là bài toán mở: oracle 22/23, hệ 7/23, tức lỗi ở khâu tìm và quyết định, không ở khâu đọc. Với paper benchmark, một lát chưa ai giải được là điểm cộng nếu chẩn đoán rõ.

## 5. Thứ tự ưu tiên

| Hạng | Việc | Vì sao đứng đây | Tốn |
|---|---|---|---|
| 1 | A2 Gold mù người, 80 lineage | Phá lập luận "tự chấm bài mình". Điều kiện chặn | 16–18 giờ người |
| 2 | B1 Qwen: xong dev, lên bộ cuối, thêm `bvdate` | ICAIL yêu cầu; hết câu hỏi "một model" | GPU, 0 đồng |
| 3 | A1 Chấm phiếu 33 câu | Số chính 25–29% có người xác nhận | 2–3 giờ người |
| 4 | B2 Bảng retriever × bộ lọc | Câu hỏi đầu tiên của reviewer IR | GPU, khoảng 2 USD |
| 5 | A3 Người thứ hai kiểm nhãn | Trả lời "nhãn do AI gán" | 5–7 giờ người |
| 6 | B4 Sửa T1, B3 chọn một trong hai | Gần như miễn phí; đóng C6, C7 | Dưới 1 USD |
| 7 | D Viết lại paper; E hoàn thiện khóa luận | Sau khi số đã khóa | 2–3 tuần |
| 8 | C1–C4 phân tích 0 đồng và lát câu hỏi do người viết | Tăng sức thuyết phục, không chặn | 4 giờ người |

## 6. Các gói việc

### WP-A. Người kiểm thước đo (bắt đầu ngay, không chờ máy)

**A1. Chấm cờ sai phiên bản.** CMT chấm phiếu 33 câu đã dựng. Xong khi có độ chính xác của cờ kèm khoảng Wilson. Ghi rõ người chấm là tác giả và đã thấy các câu này ở phiếu trước.

**A2. Gold mù người trên bộ cuối. Việc quan trọng nhất của plan.**
- **Đã dựng 15/11** ở `data/review/gold_final/` (lệnh dựng: `build.sh` cùng thư mục) [XM].
- Không rút mẫu. Lấy **hết 81 lineage** của bộ cuối mà chưa có gold mù đợt 1 và chưa người gán nào thấy đáp án của kho: 23 T6 (14 bãi bỏ trực tiếp, 9 qua nút cha), 58 T2 (19 lời văn gần giống, 39 thường). Cộng 24 lineage cũ thành **105/156, khoảng hai phần ba bộ cuối**.
- Vì sao không phải 80 rút từ 132: 51 lineage còn lại (50 T2 lô silver, 1 T3) đã bị người gán A thấy kèm đáp án. Phiếu này đúng dù NMT là A hay B. Nếu NMT là B và còn giờ, có thể đọc thêm 35 lineage mà B chưa thấy.
- Mỗi lineage một dòng. T6 lấy dòng sau bãi bỏ, vì đó là khẳng định cần kiểm (23 dòng của lát F7). Phiếu không hiện nhóm, đáp án hay ngày của kho.
- Người đọc chính (NMT): `gold_A.xlsx`, 81 dòng. Người đọc thứ hai: `gold_B.xlsx`, 30 dòng chung (12 T6, 18 T2), để có đồng thuận người–người. **Chưa chọn người thứ hai.**
- Người đọc không phải CMT, chưa xem phiếu duyệt của các lô này, không mở `data/vilextime_final/` và `gold_sample.tsv`. Đọc văn bản gốc hoặc văn bản hợp nhất.
- Trả file xong: `independent_gold.py import A --review data/review/gold_final`, rồi `reveal A --review … --release data/vilextime_final/internal/derived/vilextime/release.jsonl`.
- Báo: tỷ lệ khớp **thô trước phân xử** và sau phân xử, tách riêng, kèm Wilson. Phân xử do người làm, mỗi dòng lệch có lý do viết ra. AI không đề xuất `dong_y`.
- Tính lại F1–F6 trên 105 lineage (ADR 0006 §7). Xem lại G002 và quy ước `dong_y` của đợt 1 theo cùng quy tắc.
- Việc này cũng là M2 (đối chiếu tay) mà đề cương hứa. Ghi rõ như vậy, không làm M2 riêng.
- Ngưỡng: giữ B6 của kế hoạch chính (95% sau phân xử). Không hạ.

**A3. Người thứ hai kiểm nhãn (đặc tả 15/11).**

Câu hỏi: nhãn "AI gán, CMT duyệt" lệch nhãn của một người độc lập bao nhiêu.

- **Người gán:** NMT, sau khi xong A2. Người đọc thứ hai của A2 nếu có. Luật sư: 30 dòng `dat`.
- **Mẫu: 139 lineage, không rút ngẫu nhiên** [XM]:
  - 81 lineage `dat`: chính 81 lineage của A2. NMT đã đọc nguồn nên pha này nhanh.
  - 58 lineage `khong_dat`: toàn bộ dòng bị loại của hai lô mới. Lô 2: 55 (T2 35, T6 18, T3 2), là 128 lineage của `data/review/the4/lo2_moi_worksheet.jsonl` trừ `lo2_dat` trong `data/review/ai_research/2026-11-10_cmt_confirmed/cmt_confirmed.json`. Lô bổ sung: 3, từ `2026-11-08_supp18/cmt_accepted_labels.jsonl`.
  - Không lấy 87 dòng bị loại của lô silver: người gán A đã tự gán chúng ngày 25/10.
  - `data/vilextime_final/excluded_rows.jsonl` rỗng, không dùng làm nguồn.
- **Phiếu:** câu hỏi, các mốc, đáp án, toàn văn nguồn (worksheet đã có sẵn). Không hiện nhãn AI, lý do của AI, quyết định của CMT. Trộn thứ tự hai loại. Người gán trả lời Q1–Q4 theo hướng dẫn 4.0 (`docs/vilextime-annotation.md`) và ghi phút.
- **Q1 của phần `dat` không hỏi lại:** lấy từ kết quả A2, vì đó là lần đọc mù. Pha này chỉ thêm Q2–Q4 cho 81 dòng đó.
- **Thứ tự:** chỉ đưa phiếu này sau khi bước `reveal` của A2 đã khóa. Phiếu hiện đáp án của kho.
- **Luật sư:** 30 dòng `dat` trùng 30 dòng chung của A2 (12 T6, 18 T2). Ba người cùng xem 30 dòng này.
- **Đo:** phán quyết `dat`/`khong_dat` và từng Q: AC1, κ, p_neg, kèm KTC. Người–AI trên 139 dòng; người–người trên phần hai người cùng gán; tỷ lệ luật sư đồng ý kèm Wilson.
- **Còn phải làm trước:** script dựng phiếu. Mẫu phiếu người đã có ở `data/review/the4/gan_nhan_B.xlsx`; chưa xác định script nào sinh ra nó. Kiểm `scripts/review/ai_labels.py measure` có đọc được nhãn người không.
- **Giờ:** 58 dòng mới × 4–5 phút, 81 dòng đã đọc × 1–2 phút: khoảng 6–8 giờ [ước lượng].
- **Phải khai khi báo:** NMT là tác giả; phần `dat` chỉ gồm lô mới và T6; chỉ gọi là alt-test nếu đủ ba người gán.

**A4. Việc người còn nợ, làm nếu còn giờ:** TVER theo người (khoảng 100 trích dẫn, khoảng 3 giờ); mã hóa lỗi E7; kiểm 20 ứng viên T6 bị bộ lọc LLM loại (chương 4 hứa, khoảng 2 giờ, CMT làm được vì không cần mù). Không làm thì ghi "không làm" trong khóa luận, không để `[CHỜ]`. **CMT chốt làm hay không trước 22/11.**

### WP-B. Độ bền (máy làm)

Mọi cấu hình mới chọn trên dev. Lên bộ cuối sau **một amendment gộp** của ADR 0006 (mục 7).

**B1. Generator mở (đang chạy).**
- Khi dev xong: tải `raw_dev/` về `runs/qwen_gen_20261115/dev/raw/`, nhập, chấm, so với cột GPT-4o mini trên dev. Lưu kèm log vLLM, `pip freeze`, revision model.
- Thêm `bvnone`, `bvdate` vào gói (mục 3.3 điểm 1).
- Kiểm trước khi lên bộ cuối: định dạng, cắt cụt, và oracle dev không sụp. Ngưỡng cụ thể CMT chốt trong amendment.
- Bộ cuối: 15 hệ × 2 lần. Báo F1–F5, cặp oracle, `b7plus − bvdate`, `proposed2 − lightrag`.
- Đo luôn tỷ lệ câu trả lời trùng nguyên văn giữa hai lần. Nếu gần 100% thì có cột không dao động, trả lời ca `b5 − b4` đổi dấu.
- Tùy chọn, 0 đồng: thêm Qwen3-4B (đường chạy có sẵn theo ADR 0004) để có ba cỡ model.

**B2. Bảng retriever × bộ lọc.**
- **Bước 1 xong 15/11: vùng 100 ứng viên không chặn trần reranker** [XM, `runs/rerank_pool_dev_20261115/pool_recall.json`, dev]. Chưa cần đổi embedding.

  | Hệ, T2 dev (72 dòng) | TV-Recall@1 | @20 | @100 |
  |---|---|---|---|
  | `b4` (không lọc) | 0,181 | 0,889 | 0,958 |
  | `b7` (lọc ngày văn bản) | 0,319 | 0,917 | 0,972 |
  | `b7plus` (lọc khoảng phiên bản) | 0,444 | 0,944 | 1,000 |
  | `bvnone` (kho phiên bản, không lọc) | 0,194 | 0,903 | 0,972 |

  T3 (19 dòng): @100 = 1,000 ở cả bốn hệ. T6 (42 dòng): Recall@100 theo đơn vị 0,833–0,952, thấp hơn. Đọc: căn cứ đúng gần như luôn nằm trong 100 ứng viên, nhưng chỉ đứng đầu ở 18–44% dòng. Chỗ để reranker cải thiện là rất lớn; câu hỏi của B2 là RAG phẳng hưởng bao nhiêu.
- Ứng viên reranker: ba model trong PAPER_GAP P1-1. **Chọn theo MRR của RAG phẳng trên dev, không theo độ lợi của bộ lọc.** Chọn retriever tốt nhất cho đối thủ thì kết quả mới công bằng.
- **Bước 2, chờ CMT chạy Colab:** gói `colab_upload/rerank/` (14.012 cặp của dev, `rerank_score.py`, `README_COLAB.md`). T4 là đủ.
- **Bước 3:** đặt file điểm vào `runs/rerank_pool_dev_20261115/scores/`, chạy `select.sh`. Tiêu chí chọn đã ghi trong script trước khi có điểm: MRR của `b4` trên `all`. Xếp lại đọc vùng ứng viên từ bộ đệm, không truy xuất lại (chạy thử với điểm giả: 151 câu trong 2,7 giây).
- Số gốc để so trên dev, lai ghép k=20 (tập dượt G3): `b4` MRR 0,536, TV-R@1 0,212; `b7` 0,604, 0,331; `b7plus` 0,565, 0,411.
- Bảng: {retriever hiện tại, retriever mạnh} × {không lọc, lọc ngày văn bản, lọc khoảng phiên bản}, thêm `bvdate`.
- Truy xuất (TV-R@1, MRR) chạy cả thang, miễn phí và tất định. Sinh câu trả lời: Qwen (miễn phí) và GPT-4o mini hai lần cho 4 ô.
- Dự đoán [GT]: reranker tăng MRR của RAG phẳng, TCS gần như đứng yên. Nếu đúng, đây là bằng chứng mạnh nhất cho C1.

**B3. Vế LLM của RQ1: chọn một trong hai.**
- Mỗi dòng T2: câu hỏi, ngày, hai đoạn (bản đúng mốc, bản khác), thứ tự xáo theo seed, không in ngày. Hỏi đoạn nào áp dụng. Đoán mò 50%.
- Thêm biến thể có in khoảng hiệu lực làm mức trần.
- Model: GPT-4o mini, Qwen3.8-27B, tùy chọn Qwen3-4B. Không dùng họ Claude, DeepSeek (ADR 0004 §3).
- Thử trên dev trước.

**B4. Sửa đáp án ngắn T1.** Duyệt nháp amendment đã có trong `REFACTOR_PLAN.md`. Chấm lại dự đoán đã lưu, không gọi model. Báo cả bản trước và sau.

**B5. Mốc sát biên (`ranh_gioi`).** Chạy truy xuất cả thang (miễn phí); sinh bằng Qwen. Bảng phụ.

**B6. Không làm thêm lần chạy GPT-4o mini** chỉ để đo dao động, trừ khi B1 cho thấy Qwen cũng dao động.

### WP-C. Tính hợp lệ của dữ liệu (phần lớn 0 đồng)

**C1. Một bảng phễu duy nhất**, từ dữ liệu cổng đến dòng được giữ. Kèm so sánh phân bố giữa 40,2% sự kiện áp được và phần còn lại (loại văn bản, năm, loại thao tác). Trả lời "bộ này chỉ gồm thứ đường ống dựng được" bằng số.

**C2. Lát câu hỏi do người viết.** Một người (không phải LLM) viết lại câu hỏi cho 40 lineage T2, chỉ nhìn điều khoản. Chạy 4 hệ đã khóa. Báo riêng, thăm dò. Rẻ hơn và kiểm soát tốt hơn việc lấy bộ câu hỏi ngoài. Lấy câu hỏi thật từ bộ công khai (ViLegalExpert, VLQA) là việc thêm, nếu còn thời gian và giấy phép cho phép.

**C3. Bảng phân tầng theo người viết câu hỏi** vào paper (số đã có: 0,507 / 0,775 / 0,889), kèm ba nguồn về thiên lệch benchmark do LLM sinh.

**C4. Giá trị của đồ thị lúc dựng kho, đo trên toàn kho** [GT]: bao nhiêu đơn vị có từ hai phiên bản; bao nhiêu khoảng hiệu lực được chốt bởi lệnh ở văn bản khác; bao nhiêu do lan truyền từ nút cha. Đây là câu trả lời bằng số cho câu hỏi "đề tài tên đồ thị mà đồ thị làm gì". Kiểm trước xem kho có đủ trường để đếm không.

**C5. Đối chiếu nguồn độc lập** (P2-2): 40 phiên bản so với một nguồn khác cổng vbpl. Máy tải và so chuỗi; người phân xử chỗ lệch. Làm sau A2.

### WP-D. Viết lại paper (sau khi số khóa)

**Trục kể chuyện:** (1) chỉ số truy xuất mù với phiên bản; (2) thang phân rã chỉ ra đúng thứ khử lỗi; (3) kết luận giữ khi đổi generator và retriever; (4) benchmark có người độc lập kiểm.

**Ngân sách 2 trang còn lại:**

| Thêm | Khoảng |
|---|---|
| Bảng kiểm chứng: gold mù, đồng thuận nhãn, scorer–người, cờ sai phiên bản | 0,4 trang |
| Bảng độ bền: 2–3 generator × 2 retriever | 0,5 trang |
| Hình MRR so với TCS, mỗi hệ một điểm | 0,3 trang |
| Chọn một trong hai (C7), cột T1 (C6) | 0,25 trang |
| Khung pháp lý: "còn hiệu lực" khác "được áp dụng" (W9) | 0,15 trang |
| Tài liệu tham khảo từ 33 lên khoảng 45 | 0,4 trang |

Thiếu chỗ thì rút bảng hạng hậu nghiệm và Bảng I.

**Việc viết:**
- D1. `evidence-gate` cho số TCS/MRR và LightRAG đang nằm trong paper.
- D2. W7 (ô ✗ ở Bảng I), W9 (tra số điều bằng công cụ luật, không viết theo trí nhớ), W10 (giấy phép), W11, W12.
- D3. Hai tác giả đọc bản gốc các nguồn mới (P2-7). Chưa đọc thì không dẫn.
- D4. Dẫn GraphRAG-Bench và dòng GraphRAG có thời gian để đặt kết quả LightRAG vào đúng chỗ.
- D5. Một người ngoài nhóm đọc bản gần cuối (GVHD hoặc bạn cùng lab). Phản biện giả lập bằng AI cùng họ model không thay được việc này.

### WP-E. Khóa luận (26/12)

- E1. Chương 6: thêm LightRAG, TCS/MRR, Qwen, bảng retriever, chọn một trong hai, cột T1, kết quả người kiểm. Dọn 11 chỗ `[CHỜ]`: chỗ nào thuộc vòng thử cũ thì xóa hoặc ghi "không làm".
- E2. Chương 3: bảng phễu (C1), M2 (A2), một ví dụ chuỗi sửa đổi có nguồn, số của C4.
- E3. Chương 4: phễu T6, số người kiểm, datasheet khớp manifest.
- E4. Chương 2: hai tác giả đọc và xác minh 13 chỗ `[CẦN]`.
- E5. Chương 1 mục 1.6 và chương 7: cập nhật bảng lệch đề cương. Phụ lục khai báo AI; tra quy định của UIT về dùng AI.
- E6. Demo: đo xem 5 phút mỗi câu chậm ở đâu rồi mới sửa.
- E7. Ba câu hỏi hội đồng và số mới để trả lời:

| Hội đồng hỏi | Trả lời bằng |
|---|---|
| Vì sao 361 dòng thay vì 1.150? | Bảng MDE có sẵn; 105/156 lineage có người đọc mù (A2); phễu công khai (C1) |
| Vì sao AI gán nhãn? | Đồng thuận người–AI và luật sư (A3); scorer khớp người 96/100 |
| Đề tài tên đồ thị, đồ thị làm gì? | F5 +0,115 là phần của chuỗi phiên bản; số toàn kho ở C4; thẳng thắn: lúc truy vấn không thêm gì, LightRAG cũng không |

- E8. `thesis-critic` và `evidence-gate` rà toàn văn sau ngày khóa số.

#### WP-E chi tiết: từng chỗ `[CHỜ]`, `[CẦN]` (rà 15/11, 50 chỗ)

"Agent" là phiên Claude hoặc Codex. Hạn theo bốn đợt: **22/11** số đã có, chỉ việc điền; **29/11** cần tính hoặc đối soát nhỏ; **06/12** cần người đọc hoặc chờ số người kiểm; **10/12** khóa số.

| Chỗ | Đang chờ gì | Đóng bằng | Ai | Hạn |
|---|---|---|---|---|
| C1:49 | Kết quả bộ cuối cho RQ và giả thuyết | F1–F7 từ `runs/final_g4_20261112/r1/results.md` | Agent | 22/11 |
| C1:61 | X8 đúng mốc so với hiện hành | Cặp oracle bộ cuối (0,956 / 0,456) | Agent | 22/11 |
| C1:107, C6:27 | Amendment ghi các lần đã nhìn | Dẫn ADR 0006 §6, §8 | Agent | 22/11 |
| C2:24 | Đối chiếu PDF với bản trích | Mở PDF, kiểm số trang từng nguồn đã dẫn | CMT, NMT | 06/12 |
| C2:48, C5:59 | BM25 so với FTS5; DPR so với embedding thật | Đối chiếu code (`retrieve.py`) với nguồn; sửa chỗ lệch tập, trang | Agent, tác giả đọc | 29/11 |
| C2:61 | Cấu hình nếu so trực tiếp với GraphRAG | Ba chỗ không ngang hàng trong amendment 15/11 | Agent | 22/11 |
| C2:75 | SAT-Graph: arXiv v5 so với kỷ yếu | Đối chiếu hai bản, chốt bản dẫn | NMT | 06/12 |
| C2:123 | Nơi công bố của VLQA | Tra bản đã xuất bản | Agent tra, CMT xác nhận | 29/11 |
| C2:147 | Đọc đủ VLegal-Bench, ViLegalExpert, LegalGraphRAG | Đọc; chưa đọc thì bỏ đoạn | CMT, NMT | 06/12 |
| C2:199 | Nguồn của Holm và bootstrap theo cụm | Thêm khóa bib sau khi đọc bản gốc | Agent tìm, tác giả đọc | 29/11 |
| C2:214 (5 chỗ) | Năm nguồn gần chưa có trong bib | Đọc bản gốc rồi thêm, hoặc bỏ. Trùng việc D3 của paper | CMT, NMT | 06/12 |
| C2:220 | Chuẩn gốc Akoma Ntoso, LRMoo | Thêm bib, hoặc giữ câu "theo SAT-Graph RAG" | NMT | 06/12 |
| C3:51, C4:206a, C4:250 | Phễu dữ liệu; phễu ứng viên; phân bố năm và loại văn bản | Bảng phễu C1, cùng một snapshot; dùng `docs/reports/pheu-loc-lo-moi.md` | Agent | 29/11 |
| C3:126 | M2, gold mù, TVER theo người | Số A2 (cũng là M2); TVER theo quyết định A4 | Agent, sau NMT | 10/12 |
| C3:140 | Một ví dụ chuỗi sửa đổi đã kiểm độc lập | Một ca của A2 sau phân xử | Agent, NMT xác nhận | 10/12 |
| C4:94 | Log thời gian, nghĩa cột `phut` | Ghi "không có log"; báo trung vị `phut` của A2 | Agent, CMT xác nhận | 10/12 |
| C4:97 | Kết quả mẫu luật sư | 30 dòng của A3; không có luật sư thì ghi "không làm" | CMT lo người | 06/12 |
| C4:200 | Số lô thử, nhãn bộ cuối, AC1, p_neg | `docs/reports/g2-co-mau-dong-thuan-20261109.md`, `resolve-nhan-va-dong-thuan-20261108.md` | Agent | 22/11 |
| C4:206b | Người kiểm 20 câu T6 bị LLM loại | Việc A4; không làm thì ghi rõ | CMT | 06/12 |
| C4:220, C4:223 | Ai đọc gold của lineage nào; độ mù theo người | Bảng từ `gold_sample.tsv` hai đợt; khai 51 lineage người gán A đã thấy | Agent | 10/12 |
| C4:232 | Đọc bản gốc Datasheets for Datasets | Đọc | CMT | 06/12 |
| C5:64 | Nguồn của RRF | Thêm khóa bib bài gốc sau khi đọc | Agent tìm, tác giả đọc | 29/11 |
| C5:124a, C6:426 | Dev của `b7pp`, `proposed2`, `p2a2`, `p2a3` | `runs/final_rehearsal_g3_20261112/`, `runs/rebuild_20261110_dev/dev/` | Agent | 22/11 |
| C5:124b | Cấu hình đã khóa và kết quả bộ cuối | ADR 0006 §2 và G4 | Agent | 22/11 |
| C5:181, C6:584 | GPU, phiên bản thư viện, chi phí thật | Trường `gpu` trong `*.run.json`; số tiền API do CMT đưa | Agent, CMT | 29/11 |
| C6:33, C6:570 | TVER theo người | Theo quyết định A4 | CMT chốt | 22/11, số 06/12 |
| C6:290, C6:299 | Đầu ra sinh `b7plus` ở vòng cũ (XN5) | Ghi "không chạy ở vòng đó; xem F5 bộ cuối" | Agent | 22/11 |
| C6:409 | Kết quả theo nguồn câu hỏi (silver, lô mới) | Tính từ dự đoán G4 theo `qsource`; ghi thăm dò | Agent | 29/11 |
| C6:412 | Họ kiểm định cuối, giả định cỡ mẫu | ADR 0006 §3, §6; `data/vilextime_final/g2_mde_table.md` | Agent | 22/11 |
| C6:431 | Dev của `proposed3` | `runs/gpt4omini_dev/dev/`; audit 13/11 mục 8.1 | Agent | 22/11 |
| C6:437 | X3 với generator khác, T6 cấp sẵn căn cứ | Oracle T6 của cột Qwen (B1) | Agent, sau Colab | 10/12 |
| C6:445 | Đúng mốc so với hiện hành trên dev | `runs/final_rehearsal_g3_20261112/r1/dev/` | Agent | 22/11 |
| C7:75 | Đọc đủ các nguồn còn thiếu | Xong các dòng C2 ở trên | CMT, NMT | 06/12 |
| C7:86 | Tác giả và GVHD rà đóng góp, phạm vi | GVHD đọc bản 14/12 | CMT, GVHD | 20/12 |
| Phụ lục AI:114 | Quy định của UIT về dùng AI | Hỏi khoa và GVHD | CMT | 29/11 |
| README:18, :26 | Bảng tổng các chỗ chờ | Cập nhật sau cùng | Agent | 10/12 |

Đếm theo hạn: 22/11 có 14 chỗ, số đã có, chỉ việc điền. 29/11 có 12 chỗ. 06/12 có 15 chỗ, phần lớn chờ hai tác giả đọc bản gốc. 10/12 có 8 chỗ, chờ số người kiểm hoặc Colab. 20/12 có 1 chỗ. Tổng 50, gồm 2 chỗ trong `README.md` của thư mục khóa luận.

**Nội dung mới phải viết, ngoài các chỗ chờ:**

| Mục | Nội dung | Nguồn số | Ai | Hạn |
|---|---|---|---|---|
| C6, mới | TCS, MRR; LightRAG | G4; `runs/lightrag_20261113/` | Agent | 22/11 |
| C6, mới | Cột Qwen; bảng retriever × bộ lọc | B1, B2 | Agent | 10/12 |
| C6, mới | Chọn một trong hai (RQ1); cột T1 chấm lại | B3, B4 | Agent | 10/12 |
| C4, C6 | Gold mù bộ cuối; đồng thuận nhãn; cờ sai phiên bản | A1, A2, A3 | Agent, sau người | 10/12 |
| C3, C5 | Giá trị của đồ thị lúc dựng kho | C4 của plan | Agent | 06/12 |
| C1 mục 1.6, C7 | Bảng lệch đề cương theo trạng thái mới | Toàn bộ | Agent, CMT duyệt | 12/12 |
| Slide bảo vệ | Ba câu hỏi hội đồng (E7) | — | CMT, NMT | 20/12 |

### WP-F. Nộp bài

- F1. CMT mở trang gốc ICAIL kiểm lại quy định (hôm 15/11 mới đọc qua công cụ tóm tắt).
- F2. Xử lý repo công khai (mục 8, Q4). Link code và dữ liệu qua dịch vụ ẩn danh. Không đăng arXiv trước 19/04/2027.
- F3. Hỏi GVHD: khóa luận nộp 26/12 có bị coi là công bố trước không.
- F4. Chạy `paper_check.py`; điền CRediT, tài trợ; soát khai báo AI.

## 7. Amendment gộp cho ADR 0006

Viết **sau khi có số dev** của B1 và B2, duyệt **trước** khi chạm bộ cuối. Một amendment, khai đủ:

- Đã thấy gì: toàn bộ G4, hậu nghiệm, LightRAG, và số dev của các cấu hình mới.
- Hệ thêm: cột Qwen cho 15 hệ; các hệ có reranker; phép chọn một trong hai; `ranh_gioi`; lát câu hỏi do người viết.
- Tất cả là thăm dò, ngoài Holm, không đổi phán quyết F1–F7.
- Cách đọc khai trước:

| Thí nghiệm | Nếu | Thì viết |
|---|---|---|
| Qwen | F1–F5 cùng dấu, KTC loại 0 ở cả hai lần | "Kết luận không phụ thuộc generator" |
| Qwen | Có hiệu đổi dấu hoặc KTC chứa 0 | Nêu đúng hiệu đó; khẳng định tương ứng chỉ còn cho GPT-4o mini |
| Qwen, `bvdate` | `b7plus − bvdate` chứa 0 | Sửa số chính thứ ba: model lớn dùng được ngày; lọc cứng vẫn rẻ và chắc hơn |
| Reranker | `b7plus-rr − b4-rr` loại 0 ở cả hai lần | "Lợi ích của lọc còn với retriever mạnh", kèm tỷ lệ so với hiệu gốc |
| Reranker | Khoảng cách co hơn một nửa | Viết lại: xếp hạng sửa một phần, lọc sửa phần còn lại |
| Reranker | Khoảng cách mất | Viết lại thông điệp chính. Vẫn công bố |
| Gold mù | Dưới ngưỡng B6 | Báo tỷ lệ lỗi; chấm lại phần đó theo gold người; thu hẹp khẳng định. Không sửa kho trước hạn nộp |

## 8. Cần CMT chốt

| # | Quyết định | Đề xuất | Chặn |
|---|---|---|---|
| Q1 | Ai đọc gold mù (không phải CMT)? Ai là người thứ hai? | **Chốt 15/11: NMT đọc chính (81 dòng).** Người thứ hai (30 dòng) chưa chọn; đề xuất luật sư hoặc một sinh viên luật | Người thứ hai chặn đồng thuận người–người |
| Q2 | Mở lại reranker (đã cắt 05/11)? | ~~Chốt 15/11: mở lại.~~ **Chốt 16/11: bỏ lại** (hết quota, ưu tiên việc chính). Giữ số truy xuất dev; ghi vào giới hạn của paper | — |
| Q3 | Duyệt amendment gộp (mục 7) khi có số dev | Có | B1–B5 trên bộ cuối |
| Q4 | Repo công khai đang chứa bản thảo có tên | Chuyển riêng tư đến 19/04/2027; hoặc ít nhất gỡ `docs/paper/` khỏi nhánh công khai. Hỏi GVHD | F2 |
| Q5 | Nơi nộp | ICAIL bài dài. Ngày 10/01 chưa có A2 và B1 thì chuyển bài ngắn. GVHD chốt | WP-D |
| Q6 | Dựng bộ test mới trước 28/01? | Không. Để sau khi nộp, cùng việc nâng độ phủ kho và bãi bỏ | — |
| Q7 | Ai viết 40 câu hỏi cho C2? | Người ngoài nhóm nếu có; không thì NMT | C2 |

## 9. Lịch

| Tuần | Máy | Người | Mốc |
|---|---|---|---|
| 16–22/11 | Qwen dev xong, nhập, chấm (gồm `bvnone`, `bvdate`). Reranker: Recall@100, đường chấm cặp trên Colab, chọn trên dev. Dựng phiếu A3. Gate số TCS, LightRAG. Khóa luận: 14 chỗ hạn 22/11 | CMT chấm 33 câu; chốt A4, người đọc thứ hai. NMT bắt đầu A2 | **M1 22/11:** amendment gộp được duyệt |
| 23–29/11 | Bộ cuối: Qwen 15 hệ; bảng retriever; B3; B4; B5 | A2 tiếp | |
| 30/11–06/12 | Chấm, bootstrap, gate. C1, C3, C4 | A2 xong, phân xử. A3 pha 2 | **M2 06/12:** có số người kiểm |
| 07–13/12 | Tính lại F1–F6 trên 105 lineage. Chương 6, 3, 4 | Đọc nguồn chương 2. C2 viết câu hỏi | **M3 10/12:** khóa số khóa luận |
| 14–20/12 | `thesis-critic`, `evidence-gate`. Demo | GVHD đọc | |
| 21–26/12 | Sửa theo góp ý | | **M4 26/12:** nộp khóa luận |
| 27/12–10/01 | Viết lại paper theo WP-D. C2 chạy. C5 | Đọc bản gốc nguồn mới | **M5 10/01:** chọn bài dài hay ngắn |
| 11–24/01 | Gate, `paper_check.py`, gói ẩn danh | Người ngoài đọc | **M6 21/01:** khóa bản thảo |
| 25–28/01 | Dự phòng | Nộp | **28/01** |

Giờ người: A1 3; A2 16–18 (81 dòng của NMT và 30 dòng của người thứ hai); A3 6–8; phân xử 2; C2 4. Tổng khoảng 32 giờ, chia cho CMT, NMT, luật sư. **Các số này là ước lượng, chưa đo.** Sau 10 dòng đầu của NMT, lấy trung vị cột `phut` rồi chỉnh lại lịch.
Tiền API: bảng retriever khoảng 2 USD, B3 và C2 dưới 1 USD mỗi việc [SL, tính từ 5,3 USD cho 24 lượt hệ ở G4].

## 10. Không làm

- Không cố làm đồ thị lúc truy vấn "thắng". Đã chốt ở audit 13/11.
- Không dựng bộ test mới, không nâng độ phủ kho, không làm bước quyết định bãi bỏ trước 28/01. Ba việc này đi cùng nhau, để sau.
- Không LLM giám khảo. Không chạy T-GRAG, TG-RAG và các hệ tương tự; chỉ dẫn.
- Không thêm biến thể LightRAG.
- Không đổi P, F1–F7, scorer, gold, prompt của hệ đã khóa.

## Risks And Recovery

| Rủi ro | Xử lý |
|---|---|
| NMT không đọc kịp 81 dòng | Ưu tiên 23 T6 và 30 dòng chung trước. Dưới 60 dòng thì nộp bài ngắn (Q5) |
| Gold mù lộ lỗi kho | Báo đúng số; chấm lại theo gold người; không sửa kho trước hạn |
| Model mở hoặc reranker đảo một kết luận | Viết theo bảng mục 7. Biết trước reviewer vẫn hơn |
| Trùng hạn khóa luận | Khóa số 10/12. Sau ngày đó số mới chỉ vào paper |
| Colab ngắt | `vllm_generate.py` chạy tiếp được từ dòng dở |
| Lẫn artifact | Mỗi việc một thư mục `runs/<tên>_<ngày>/`; không ghi vào `runs/final_g4_20261112/` |
| Lộ danh tính khi phản biện kín | Q4, F2 |

Hoàn tác: plan này chỉ thêm file và thư mục run mới. Xóa thư mục run và revert commit là về trạng thái 15/11.

## Progress

- [x] 15/11 Rà hiện trạng, lập plan.
- [x] 15/11 Q1 (người đọc chính: NMT), Q2 (mở lại reranker): CMT chốt. Còn Q3–Q7 và người đọc thứ hai.
- [ ] A1 Chấm phiếu 33 câu.
- [x] 15/11 A2 dựng phiếu: `data/review/gold_final/` (commit `afd6bd4`). `independent_gold.py` thêm `--release`, cỡ riêng từng tầng, `--solo`; test mới; 788 test qua. Đã kiểm: 81 dòng A, 30 dòng B nằm trong A, 23 dòng T6 đều là dòng sau bãi bỏ, 0 lineage trùng gold đợt 1 hay danh sách đã thấy, 0 ô chứa đáp án của kho, `reveal` chạy thử trên bản sao.
- [ ] A2 NMT đọc / người thứ hai đọc / phân xử / tính lại F1–F6.
- [x] 15/11 A2: NMT đọc mù 81/81 và tự đối chiếu sau khi mở khóa. Hiệu lực khớp kho 80/81; kho đúng 79/81 (2 dòng T2 `kg_missed_amendment`, 1 dòng T6 `annotator_error`); T6 23/23. Cột `ly_do` chuyển về mã theo CMT duyệt. F1–F7 trên 103 lineage có gold người (bỏ 2 lineage kho sai): F1–F6 ủng hộ, F7 không đủ bằng chứng, cả hai lần (`runs/gold_final_subset_20261115/`). Còn: người đọc thứ hai 30 dòng (`gold_B.xlsx`); NMT không ghi `phut`.
- [x] 15/11 CMT yêu cầu viết chi tiết: thêm đặc tả A3 và bảng 50 chỗ `[CHỜ]`, `[CẦN]` của khóa luận (WP-E chi tiết).
- [ ] A3 Dựng phiếu / NMT gán sau khi A2 khóa / luật sư 30 dòng / đo đồng thuận.
- [ ] B1 Qwen: dev / thêm `bvdate` / bộ cuối.
- [x] 15/11 B1 dev 13 hệ × 2 lần nhập và chấm (`runs/qwen_gen_20261115/run_dev.sh`, exit 0). Qwen giữ thứ tự: `b4` 0,424, `b7plus` 0,715, `proposed2` 0,762; oracle 0,894 với oracle hiện hành 0,497. Điểm mới: `b7` ngang `b7plus` về Accuracy (0,715) nhưng sai phiên bản 0,129 so với 0,012, nên C3 phải dựa vào sai phiên bản và TCS, không dựa riêng Accuracy. Hai lần trùng nguyên văn 97,1%. Còn: `bvnone`, `bvdate`; log vLLM, `pip freeze`.
- [x] 16/11 B1 dev thêm `bvnone`, `bvdate` (Qwen, r1/r2): `bvnone` Acc 0,437/0,430, sai phiên bản 0,388/0,376, TCS 0,167; `bvdate` Acc 0,715/0,709, sai phiên bản 0,047, TCS 0,611 (`b7plus` 0,715; 0,012; 0,750). Model lớn dùng được ngày: `b7plus − bvdate` có KTC chứa 0 ở Accuracy [−0,087; 0,089], sai phiên bản [−0,096; 0,015] và TCS [−0,033; 0,314] (khác GPT-4o mini +0,245); chênh điểm ở sai phiên bản và TCS chưa phân biệt được với 0. Evidence-gate PASS (chấm lại byte-khớp, hệ cũ không đổi). Hậu nghiệm, dev. Log vLLM, `pip freeze` ở `runs/qwen_gen_20261115/env/`; ghi chú ở `NOTE_bv_20261116.md`. Còn: bộ cuối, GPT-4o mini ô `bv*` trong `compare_dev.json`.
- [x] 15/11 B2 code reranker commit `56b9c3e` (viết trước đó trong ngày, 35 test liên quan qua).
- [x] 15/11 B2 bước 1: vùng ứng viên trên dev, 4 hệ, xong 11:42 UTC, exit 0 (`runs/rerank_pool_dev_20261115/`, dòng sổ chạy 15/11). T2 TV-Recall@100 từ 0,958 đến 1,000.
- [x] 15/11 B2 bước 3: chọn reranker trên dev (`select.sh`, exit 0). Theo tiêu chí khai trước (MRR `b4`): **`AITeamVN/Vietnamese_Reranker`** 0,696 (bge-m3 0,685, ViRanker 0,624, không reranker 0,536). Reranker không thay bộ lọc: TV-Recall@1 `b4` 0,285 so với `b7plus` 0,550. Còn: sinh câu trả lời với reranker trên dev.
- [x] 15/11 B2 đường chấm trên GPU: `scripts/eval/rerank_score.py` (`pairs`, `score`), `Reranker.from_scores`, cờ `--rerank-scores` ở `run_vilextime.py` và `colab_b1.py export`, vùng ứng viên dùng chung bộ đệm với lượt `--hybrid --k 100`. Thiếu điểm của một cặp thì báo lỗi, không tự chạy CPU. Test mới trong `tests/test_rag_retrieve.py`.
- [ ] B2 CMT chạy Colab chấm cặp / `select.sh` chọn trên dev / amendment / bộ cuối.
- [ ] B3 Chọn một trong hai.
- [ ] B4 Sửa T1, chấm lại.
- [ ] B5 `ranh_gioi`.
- [ ] Amendment gộp ADR 0006.
- [ ] C1 Bảng phễu. C3 Bảng theo người viết. C4 Số toàn kho. C2 Lát câu hỏi người viết. C5 Nguồn độc lập.
- [ ] D1–D5 Paper.
- [ ] E1–E8 Khóa luận.
- [ ] F1–F4 Nộp.

## Decisions

- 2026-11-15: đề xuất không dựng bộ test mới trước 28/01; dồn giờ người cho gold mù. Chờ CMT.
- 2026-11-15 (CMT): NMT là người đọc chính của gold mù. Mở lại reranker.
- 2026-11-15: A3 lấy hết 81 lineage `dat` của A2 và 58 lineage `khong_dat` của hai lô mới, không rút mẫu. Bỏ lô silver vì người gán A đã gán nó.
- 2026-11-15: gold mù lấy hết 81 lineage chưa ai thấy đáp án, thay cho "80 rút từ 132". Lý do: người gán A cũ đã thấy 51 lineage còn lại, nên chúng không thể đọc mù; lấy hết thì khỏi phải rút mẫu và phiếu đúng dù NMT là A hay B.

## Validation

- Mỗi số mới truy được về một file trong `runs/` kèm hash đầu vào, và qua `evidence-gate` trước khi vào khóa luận hay paper.
- Mỗi cấu hình mới có dòng trong `runs/README.md` và nằm trong amendment đã duyệt trước khi chạy bộ cuối.
- Số người kiểm báo cả thô và sau phân xử.
- Lệnh nền: `.venv/bin/python -m pytest -q`, `git diff --check`, `latexmk -xelatex` ở `docs/paper/acm/`.

## Result

Chưa có.
- [x] 16/11 CMT bỏ reranker (B2 từ bước 2): không chạy Qwen và GPT cho 4 ô, không lên bộ cuối. Giữ số truy xuất dev (`runs/rerank_pool_dev_20261115/`) và gói đã dựng (`runs/qwen_gen_rr_20261116/`, chưa chạy). Paper ghi vào giới hạn. Nháp amendment đã gỡ reranker.
- [x] 16/11 CMT duyệt amendment gộp ("Chốt"); đã chép vào `docs/decisions/0006-*.md` (Amendment 2026-11-16). Cổng mở cho Qwen trên bộ cuối (15 hệ × 2 lần). B3, C2, reranker không làm.
- [x] 16/11 B1 bộ cuối: Qwen3.8-27B qua Chutes (FP8, amendment 16/11 (b)), 15 hệ × 2 lần, evidence-gate qua sau khi sửa nhãn F7 (`runs/qwen_chutes_20261116/test/NOTE_ket_qua.md`). F1–F3 cùng dấu với GPT-4o mini, KTC loại 0; F7 không đủ bằng chứng (+0,087 [0; 0,217]); `b7plus − bvdate` +0,085 [+0,041; +0,132] loại 0 (ở dev vLLM chứa 0). Còn: cập nhật paper (cột Qwen; ghi "GPT-4o mini" cạnh 0,245); báo MRR, TV-R@1, oracle, `ranh_gioi` nếu cần.
- [x] 16/11 A2 người đọc thứ hai (luật sư) trả `gold_B` 30/30: đồng thuận `hieu_luc` với NMT 29/30, κ 0,932, AC1 0,935. Dòng lệch F019: luật sư đúng (TT 36/2026/TT-BXD Điều 16 bãi bỏ TT 11/2021/TT-BXD từ 01/07/2026), kho và NMT sai. Chờ CMT quyết sửa gold theo ADR 0006 §7 (`data/review/gold_final/DONG_THUAN_B_20261116.md`).
- [x] 16/11 Sửa gold F019 theo ADR 0006 §7 (CMT "sửa luôn"): bản release sửa ở `runs/gold_fix_20261116/`, không đụng `data/vilextime_final`. F1–F7 không đổi phán quyết (GPT, Qwen, cả hai lần); tập con gold mù 103 lineage F1–F6 ủng hộ. Paper: đoạn gold mù và giới hạn (i) cập nhật (105/156, luật sư 30 dòng, κ 0,932). Còn: 2 lineage `kg_missed_amendment` mới loại, chưa sửa gold.
- [x] 16/11 Sửa nốt gold F016, F060 (NMT, `kg_missed_amendment`) theo §7: 3 lineage, 4 dòng; phán quyết F1–F7 không đổi (|Δ| ≤ 0,0033); phần gold mù 105 lineage/215 dòng F1–F6 ủng hộ. Paper giữ số chính theo gold phát hành, nêu kết quả gold đã sửa. Còn: errata ViLexTime (CMT quyết).
