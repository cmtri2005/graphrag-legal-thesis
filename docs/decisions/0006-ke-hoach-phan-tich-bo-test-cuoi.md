# 0006 Kế hoạch phân tích cho bộ test cuối

Date: 2026-11-05

## Status

**Proposed, bản nháp.** Phải được CMT và NMT duyệt, chuyển sang Accepted và commit **trước** lần chạy đầu tiên của bất kỳ hệ nào trên bộ test cuối (cổng G3 của `docs/plans/active/master-plan.md`). `scripts/eval/final_run.py` từ chối chạy split `test` khi chưa có commit đó.

Các chỗ ghi `[ĐIỀN Ở G2]`, `[ĐIỀN Ở G3]` được điền bằng số đo thật trước khi duyệt. Không chỗ nào được điền sau khi đã thấy kết quả của bộ test cuối.

ADR này không sửa ADR 0005. Kết luận đã báo của v1.0 và test 2 giữ nguyên theo ADR 0005 và các amendment của nó.

## Context

- ADR 0005 khai báo trước họ XN1–XN9 cho v1.0, rồi amendment 03/11 lặp lại trên test 2 (nhãn LLM). Kết quả: v1.0 có 6/6 kiểm định ủng hộ. Test 2 có XN2, XN3, XN8, XN9 ủng hộ, còn XN1, XN4 không đủ bằng chứng.
- Ngày 05/11, sau khi đã thấy các kết quả này, nhóm quyết định dựng một bộ test cuối mới (lúc đầu định do người gán; từ 06/11 đổi thành AI gán, CMT duyệt, xem §1 và §11), vì ba lý do đo được: nhãn chưa đáng tin (AC1 0,377; 90/211 dòng v1.0 chỉ có nhãn Codex; test 2 toàn nhãn LLM), đáp án dẫn từ chính đồ thị của hệ, và hệ đã chạy chưa có lai ghép như L4 của đề cương. Việc gọi v1.0 và test 2 là "vòng thử" có từ ngày đó. Không được viết như thể vai này có từ đầu.
- Phản biện ngày 05/11 (`docs/reports/phan-bien-ban-nhap-20261105.md`) chỉ ra:
  - TVER, Verifier và gold cùng dùng cửa sổ hiệu lực của đồ thị, nên TVER = 0 của `b7pp` là do cách dựng;
  - nấc lan truyền đo được bằng 0 ở tầng truy xuất (`b7pp` = `b7plus` mọi nhóm, cả hai bộ);
  - thông báo bãi bỏ của `proposed3` lấy từ cùng sự kiện với gold T6.
- Công trình gần nhất là LawInForce-eCFR và NitiBench+ (`related_paper/notes/2026-11-05-doc-nguon-va-tinh-moi.md`). Phần còn riêng của đề tài: pháp luật Việt Nam, và phép tách có đối chứng trên cùng dữ liệu giữa lọc theo ngày văn bản và lọc theo khoảng hiệu lực phiên bản.

## Decision

### 1. Dữ liệu

- **Bộ test cuối** chỉ gồm lineage chưa từng có dự đoán của hệ nào trong `runs/`: silver T2, T3 (`data/review/the4/lo1_silver_worksheet.jsonl`), lô mới T2, T6 (`lo2_moi_worksheet.jsonl`) và lô bổ sung (`data/review/ai_research/2026-11-08_supp18/`). Đếm ngày 11/11 (`data/review/ai_research/2026-11-11_final_count/count_final.py`): **156 lineage** = T2 127, T6 23, T3 6.
- **T1 đối chứng (thêm 11/11, CMT duyệt):** 60 lineage T1 mới được gán (`data/review/the4/t1_moi_worksheet.jsonl`), **43 đạt** (`data/review/ai_research/2026-11-11_t1_labels/cmt_confirmed_t1.json`), cùng điều kiện chưa có dự đoán, không trùng văn bản với dev, cùng quy trình nhãn như phần còn lại. Câu hỏi và đáp án ngắn T1 do `claude-haiku-5-5` viết. T1 **không** vào lát `all` và **không** vào họ Holm; chỉ dùng cho phép kiểm không làm hại ở §4.
- **Điều kiện vào bộ cuối (quy trình thật, từ 06/11):** AI-A (Claude) và AI-B (Codex) gán mù độc lập theo thẻ 4.0; `legal-adjudicator` đề xuất cho dòng lệch và chốt ca khó (CMT ủy quyền 11/11, thay luật sư); CMT duyệt mọi dòng; nhãn cuối là `dat`. Không có người gán độc lập thứ hai và không có luật sư kiểm các ca này (§11).
- **Đồng thuận AI–AI trước hòa giải** (verdict, Gwet AC1): gộp silver + lo2 + supp18 **0,608** trên 314 lineage, **dưới ngưỡng 0,80** (`docs/reports/g2-co-mau-dong-thuan-20261109.md`; lo2 0,503, supp18 0,538); T1 **0,919** trên 60 lineage. Phần chính của bộ cuối vì vậy không đạt ngưỡng đồng thuận đặt ra; mọi kết quả phải kèm giới hạn này.
- **Dòng bị loại sau khi gán** (quyết định không dùng đầu ra hệ nào trên bộ cuối):

  | Mã | Căn cứ | Lineage bộ cuối |
  |---|---|---:|
  | `relocation_unclear` (R2) | `legal-adjudicator`, `data/review/ai_research/2026-11-11_t6_r2/` | 3 |
  | `reference_only` (N2, CMT 11/11) | e9ffd3da | 1 |
  | đồ thị trỏ nhầm văn bản (lo2 `dafc3b40`, CMT 11/11) | sự kiện `event:168125:…` | 0 (không nằm trong tập đạt) |
  | `relocation_unclear` (Q1, CMT 11/11) | chỉ dev: 6cab03a0, 6caa8e70, 1a267400 | 0 |
- **Danh sách khóa (G2, 12/11):**
  - Lineage: `data/vilextime_final/lineages_199.txt` sha256 `d34a1ff2086b293152f24706006c25afcaf983b19326a64c014228e3156b4f1d` (156 chính + 43 T1).
  - Release: `data/vilextime_final/vilextime.jsonl` sha256 `5766f9162939bd7c37471d8b995b56b6b5dae0c0da11e52ff13d8030587e534c`; meta `vilextime_meta.jsonl` sha256 `22142241f8eae7296b48ddad042a3552746070a89d1042663fd41c586acaaa49`; manifest `manifest.json` sha256 `87093c3f78f4205e77b2c64a45b116cb3dd627465c47b7491a8f264d6675cbcd`.
  - 722 dòng; ở `giua_khoang`: `all` 156 lineage / 318 dòng (295 có đáp án), `t6_unanswerable` 23, `t6_ancestor` 9, `t2_near` 38, `t1_control` 43. Dựng bằng `scripts/pipeline/build_final_release.py`; `check_release.py` qua; 0 trùng lineage và văn bản với dev; 0 dự đoán trong `runs/`. Đáp án của 676 dòng có đáp án khớp cửa sổ và lời văn của đồ thị dựng lại 10/11 (kể cả 27 lineage không còn trong `vilextime_pool.jsonl`).
- **Dev:** giữ nguyên 151 dòng `dev`, `giua_khoang`, như ADR 0005.
- **Lát khai báo trước** trên `giua_khoang`:

  | Lát | Điều kiện |
  |---|---|
  | `all` | T2, T3, T6 |
  | `all_answerable` | `all`, có đáp án |
  | `t6` | T6 |
  | `t6_unanswerable` | T6, không có đáp án |
  | `t6_ancestor` | T6 bãi bỏ qua nút cha |
  | `t2_near` | T2 gần giống |
  | `qsource_silver`, `qsource_new`, `qsource_supp` | theo quy trình viết câu hỏi |
  | `t1_control` | T1 đối chứng; ngoài `all` |

- **Không gộp** dòng của v1.0 hay test 2 vào bộ cuối. Dòng T6 của hai bộ đó đã được xem, nên chỉ báo riêng với nhãn "đã thấy".

### 2. Hệ và cấu hình bị khóa

- **Generator:** `gpt-4o-mini-2024-07-18` (OpenAI), nhiệt độ 0, `max_tokens` 1024, `seed` 20261109, theo amendment 09/11 của ADR 0004 (Accepted 12/11, CMT). Qwen3-4B rev `cdbee75` chỉ ở bảng phụ RQ1 và các vòng thử lịch sử, không đặt số cạnh cột chính.
- **Embedding:** `dangvantuan/vietnamese-embedding`. X6 (`AITeamVN`) **không chạy trước G3**, nên theo quy tắc gốc giữ `dangvantuan`; X6 không được chạy để đổi embedding sau khi ADR này Accepted.
- **Thang truy xuất** (F4–F6): `b2ctx → b7 → b7v → b7plus → b7pp`, từ vựng, `k = 20`, như ADR 0005, để so được với v1.0 và test 2.
- **Hệ có sinh câu trả lời:** `b1`, `b2ctx`, `b3`, `b4`, `b5`, `b6`, `b7`, `b7plus`, `b7pp`, `oracle`, `oracle_now` và **P**. Danh sách gốc là `FINAL_GENERATION` trong `src/vilexgraph/framework/systems.py`; bảng cấu hình in bằng `python -m vilexgraph.framework.systems`. Mọi hệ có truy xuất dense chạy ở chế độ lai ghép (`--hybrid`), không reranker.
- **Chỉ chạy trên dev:** `proposed2`, `proposed3` để chọn P; `p2a2`, `p2a3` để mô tả thành phần.
- **Trình bày:** mọi hệ đều chạy. Paper giữ 7 hệ lõi cộng `b1` ở bảng chính và `oracle`, `oracle_now` ở bảng chẩn đoán; khóa luận báo đầy đủ.
- **P** là đúng một hệ, chọn trên dev theo quy tắc khai trước:
  - P là `proposed3` nếu trên dev, `proposed3` − `proposed2` ở `t6_unanswerable` có KTC ghép cặp > 0, **và** trên các dòng có đáp án, cận dưới KTC của hiệu Accuracy ≥ −0,02.
  - Ngược lại, P là `proposed2`.
  - Kết quả áp quy tắc trên dev (09/11, `runs/gpt4omini_dev/select_p.json`): **P = `proposed2`**. Ở `t6_unanswerable` (21 dòng), `proposed3` − `proposed2` = +2/21, KTC ghép cặp [0; 0,238], cận dưới không > 0 nên điều kiện đầu không đạt. Dòng có đáp án (112 dòng): +1/112, KTC [0; 0,028]. Nếu quy tắc chạy lại vì đồ thị đổi (mục 7), ghi kết quả mới ở đây.
  - Chạy lại sau khi sửa đồ thị một lần (11/11, `runs/rebuild_20261110_dev/select_p.json`, quy tắc không đổi): **P = `proposed2`**. `t6_unanswerable`: +1/21, KTC [−0,095; 0,190]; dòng có đáp án: +1/112, KTC [0; 0,028]. Gate: `docs/reports/gate/h6-gate2-dev-20261111.md`.
  - Chấm lại dev sau khi loại 12 lineage T6 theo R2 và Q1 (11/11, `runs/t6_dev_r2_20261111/rescore.json`, không gọi API mới): `t6_unanswerable` còn 9 dòng, hiệu 0, KTC [−0,33; 0,33]; **P = `proposed2`**.
  - **P = `proposed2` khóa tại commit Accepted của ADR này.** Mọi phân tích dev sau đó (kể cả chẩn đoán T6) chỉ báo cáo, không mở lại P, không đổi prompt hay cấu hình hệ.

### 3. Họ kiểm định xác nhận (Holm, α = 0,05)

| Mã | Câu hỏi | So sánh | Đại lượng | Lát | Dự đoán |
|---|---|---|---|---|---|
| F1 | RQ2, so với RAG phẳng lai ghép | P − `b4` | Accuracy | all | > 0 |
| F2 | RQ2, so với mở rộng đồ thị phi thời gian (`b5` không phải GraphRAG thật; LightRAG báo riêng) | P − `b5` | Accuracy | all | > 0 |
| F3 | RQ2, lỗi sai phiên bản | P − `b4` | `wrong_version` | all | < 0 |
| F4 | RQ3, lọc ngày văn bản | `b7` − `b2ctx` | TV-Recall@1 | all_answerable | > 0 |
| F5 | RQ3, lọc khoảng phiên bản | `b7plus` − `b7` | TV-Recall@1 | all_answerable | > 0 |
| F6 | Giả thuyết đề cương (H0) | `b7pp` − `b7` | TV-Recall@1 | all_answerable | > 0 |
| F7 | T6 | P − `b7pp` | Accuracy | t6_unanswerable | > 0 |

- **F7** chỉ vào họ khi lát có ít nhất 20 lineage. Không đủ thì tự chuyển sang thăm dò; công cụ ghi rõ. Đếm trước khi Accepted (11/11): `t6_unanswerable` có **23 lineage**, nên họ Holm có **7** phép thử. Báo T6 tách dòng có và không có đáp án.
- **H0 chỉ quyết bằng F6.** Trên `all_answerable` lớp B luôn bằng 0, nên về cấu trúc `b7pp` ≡ `b7plus` và F6 trùng F5: H0 đo bước lọc theo chuỗi phiên bản, **không** đo lan truyền. Phép đo lan truyền duy nhất là `b7pp` − `b7plus` trên `t6_ancestor` (§4, thăm dò).
- **F3–F6 đo "nhất quán với đồ thị"**, vì gold và cửa sổ hiệu lực của hệ cùng lấy từ đồ thị phiên bản. Bằng chứng đúng với luật đến từ gold mù (§7) và TVER theo người (§4), không từ F3–F6.
- F1–F7 được chọn sau khi đã thấy dev và hai vòng thử (§8): đây là **xác nhận có điều kiện**, không phải kiểm định độc lập hoàn toàn.
- **TVER không còn là kiểm định xác nhận**, vì nó dùng chung cửa sổ của đồ thị với gold. Công cụ vẫn tính nó dưới mã F8, luôn ngoài Holm, như một phép kiểm nhất quán nội bộ.

### 4. Thăm dò và mô tả (ngoài Holm)

- `b7pp` − `b7plus`, Accuracy trên `t6_ancestor`: phép đo duy nhất cho nấc lan truyền. Chỉ được nói lan truyền có tác dụng khi khoảng tin cậy loại trừ 0.
- **TVER theo người:** rút có seed khoảng 100 đơn vị được trích bởi `b2ctx`, `b7`, `b7pp`, P. Người đọc văn bản gốc, không thấy cửa sổ đồ thị, rồi xác định đơn vị đó còn hiệu lực tại mốc hay không. Báo tỷ lệ kèm Wilson.
- **Hai điều kiện cấp sẵn căn cứ:** `oracle` (bản đúng mốc) và `oracle_now` (bản hiện hành), theo nhóm, có T1 của v1.0 làm đối chứng.
- **Không làm hại trên T1 (`t1_control`, ngoài Holm, khai trước 11/11):**
  - Hiệu Accuracy ghép cặp P − `b2ctx`, KTC 95% như §5. Biên không làm hại δ = 0,05: nói "không làm hại" chỉ khi cận dưới KTC > −0,05; cận dưới ≤ −0,05 thì báo "không chứng minh được không làm hại", không đổi thành "có hại" trừ khi cận trên < 0.
  - Cùng phép đo cho `b7`, `b7pp` so với `b2ctx`, báo mô tả.
  - Số dòng T1 mà mỗi hệ khẳng định "không còn hiệu lực" (khẳng định sai, vì T1 không đổi): đếm và tỷ lệ kèm Wilson. Cài ở `confirm_vilextime.py --family final` (khóa `t1_no_harm`).
  - Với khoảng 60 lineage, KTC dự kiến rộng khoảng ±0,1; phép kiểm này chỉ bắt được tác hại lớn. Ghi đúng như vậy.
- **Khẳng định "đã bãi bỏ":** precision trên dòng có đáp án và recall trên dòng không đáp án, mọi hệ.
- **Các chỉ số khác:** TCS, VCR, MRR, EM/F1.
- **Các lát:** theo miền, theo quy trình câu hỏi, theo mức trùng chữ giữa câu hỏi và đáp án.
- **Về nhãn:** AC1 riêng trên phần A chưa từng thấy (A đã gán 131/168 lineage silver ở vòng 25/10). So nhãn LLM của test 2 với nhãn người trên lô thử.
- **Accuracy T6 của `proposed3`** là cận trên khi đồ thị đúng. Chỉ kết luận trên dòng T6 đã qua gold mù.

### 5. Thống kê

Như ADR 0005 §5: bootstrap theo cụm lineage, B = 10.000, khoảng phân vị 95%, ghép cặp dùng chung lần lấy mẫu lại. Với B = 10.000, p nhỏ nhất khác 0 là 0,0002; p bằng 0 trong file được ghi là "p < 0,0002".

### 5b. Dao động của generator API

GPT-4o mini ở nhiệt độ 0 vẫn đổi câu trả lời giữa các lần gọi (dev: 3–5/151 câu). Vì vậy (CMT chọn 12/11):
- Mỗi hệ có sinh câu trả lời chạy **hai lần độc lập** trên bộ cuối, cùng prompt và seed. **Lần 1 là kết quả chính**, khai trước; lần 2 chỉ để đo độ ổn định. Không được chọn lần "đẹp hơn".
- Một kiểm định chỉ được gọi là **ủng hộ** khi phán quyết giống nhau ở cả hai lần. Khác nhau thì báo "không ổn định", tính như không đủ bằng chứng.
- Ghi `system_fingerprint` và model trả về cho mọi lần gọi; báo tỷ lệ câu đổi giữa hai lần theo hệ và lát.
- Các hệ chỉ truy xuất (F4–F6) không chịu dao động này.
- Công cụ (12/11): `api_generate.py --run-tag r1|r2`, `final_run.py --run-tag`, so hai lần bằng `scripts/eval/compare_runs.py`. `final_run` tự kiểm model, nhiệt độ 0, `max_tokens` 1024, seed 20261109, và file truy xuất F4–F6 là từ vựng k = 20; sai thì dừng.

### 5c. Đọc câu trả lời (khai trước 12/11)

Parser nhận nhãn `HIỆU LỰC`, `CĂN CỨ` ở đầu dòng hoặc viết HOA giữa dòng ("TRẢ LỜI: … HIỆU LỰC: không CĂN CỨ: [1]"); lần xuất hiện cuối thắng. Sửa trên dev đổi 6 dòng `format_ok`, 0 dòng đổi đúng/sai, P vẫn `proposed2` (`runs/parse_fix_dev_20261112/`). Áp như nhau cho mọi hệ.

### 6. Quy tắc kết luận

- **Ủng hộ, bác, không đủ bằng chứng:** như ADR 0005 §6.
- **Kết luận chính chỉ lấy từ bộ test cuối.** v1.0 (xác nhận lần 1) và test 2 (lần lặp, nhãn LLM) được báo cạnh nhau, không gộp, không dùng để đổi phán quyết của bộ cuối.
- **Kết luận cho H0 theo F6 của bộ cuối:**

  | F6 bộ cuối | Kết luận cho H0 |
  |---|---|
  | Ủng hộ | Ủng hộ, kèm ghi chú là lần lặp test 2 không đủ bằng chứng |
  | Không đủ bằng chứng | **Không được ủng hộ.** Đề tài theo nhánh tài nguyên và phân tích, dù v1.0 ủng hộ |
  | Bác | Bác |

- **Không đủ bằng chứng** được viết theo mẫu: "KTC không loại trừ 0 và không loại trừ hiệu ≥ MDE; không diễn giải là không có hiệu ứng".
- **Cỡ mẫu và power:** ghi cạnh mọi phán quyết. Bảng MDE cho F1–F7 ở N thật (156 lineage; F7 23 lineage), tính từ phương sai ghép cặp của test 2 và dev, ghi rõ là ước lượng trước khi chạy: xấp xỉ chuẩn, power 80% (`data/vilextime_final/g2_mde.py`, `g2_mde_table.md`). Power 0,37 trước đây chỉ là kịch bản xấu cho F5/F6.

  | Mã | MDE α 0,05 | MDE Holm xấu nhất α/7 | Nguồn SD | Hiệu đã thấy (dev / test 2) |
  |---|---:|---:|---|---|
  | F1 | 0,084 | 0,106 | dev | +0,377 / — |
  | F2 | 0,080 (test 2: 0,068) | 0,100 (0,086) | dev, test 2 | +0,351 / +0,186 |
  | F3 | 0,072 | 0,091 | dev | −0,399 / — |
  | F4 | 0,087 (test 2: 0,032) | 0,110 (0,040) | dev, test 2 | +0,138 / +0,046 |
  | F5, F6 | 0,058 (test 2: 0,047) | 0,073 (0,060) | dev, test 2 | +0,085 / +0,028 |
  | F7 | 0,185 | 0,233 | dev (21 dòng, trước R2) | 0 / — |

  F5/F6 có hiệu đã thấy gần hoặc dưới MDE: "không đủ bằng chứng" là khả năng thật. F7 chỉ phát hiện được hiệu rất lớn.

### 7. Gold mù và sửa gold

- Gold mù theo B6, mù theo từng người (`independent_gold.py` với `--only`). Đạt khi ≥ 114/120 khớp.
  - Đợt 1 (người, T2/T3): **119/120 khớp, đạt** (H4, CMT xác nhận 10/11).
  - Đợt 2 (30 dòng T1/T6): do AI gán mù, **không phải người**; 28/30 khớp. Gold mù người cho T1/T6 (H3) chưa có, ghi là giới hạn.
- **Dòng mà gold mù cho thấy gold sai:** giữ trong bộ cuối với gold đã sửa, không loại. **Khác** với các dòng bị loại theo quy tắc nhãn (R2, Q1, N2, `partial_repeal`, đồ thị trỏ nhầm) ở §1: các dòng đó loại theo quy tắc đã chốt trước khi chạy test, không dựa trên đầu ra hệ.
- **Lỗi đồ thị phải sửa:** dựng lại release và chạy lại mọi hệ trên dev trước G3. Không sửa sau khi đã chạy test.
- **Báo song song** F1–F6 trên phần gold mù.

### 8. Kết quả đã thấy trước khi viết ADR này

- **Đã thấy:**
  - kết quả test của v1.0 (E1, E3) và test 2 (E1, E3, lần chấm sai và lần chấm lại);
  - mọi kết quả dev (B2, lai ghép, X4, tập dượt, và từ 09/11 cả 15 hệ sinh bằng GPT-4o mini, gồm `proposed2`, `proposed3`);
  - phân rã lỗi E7 do máy; hiệu chuẩn lời dặn v2; phản biện 05/11; đối chiếu VBHN;
  - chẩn đoán T6 dev, X8 C0/C1 (dùng gold), chấm lại T6 dev sau R2/Q1 (11/11);
  - **nhãn và câu hỏi của chính bộ cuối** (khi gán, hòa giải, rà R2 và sửa đồ thị): sửa đồ thị có nhìn lineage của bộ cuối, nhưng chưa nhìn đầu ra hệ nào trên chúng.
- **Chưa thấy:** mọi dự đoán trên bộ test cuối; kết quả Colab đợt 2 (niêm phong, xem mục 9).

### 9. Niêm phong Colab đợt 2

Kết quả đợt 2 (các hệ còn thiếu trên v1.0 và test 2) được nhập, lưu sha256 vào `runs/README.md`, nhưng **chỉ chấm sau khi ADR này được commit**. Mục đích: không để kết quả test của `b3`, `b4`, `oracle` và ablation ảnh hưởng đến việc chọn embedding, lai ghép hay P.

### 10. Thay đổi so với ADR 0005

| Thay đổi | Lý do | Đã thấy gì lúc đổi |
|---|---|---|
| Bỏ TVER (XN2) khỏi họ xác nhận | Dùng chung cửa sổ đồ thị với gold | TVER `b7pp` = 0 ở cả hai bộ |
| Thêm `wrong_version` cho RQ2 | Đề cương hỏi việc giảm lỗi sai phiên bản | Kết quả hai vòng thử |
| P thay `proposed` | `proposed` chưa có lai ghép như L4 | Lai ghép và `rel_up` trên dev |
| RQ2 so với `b4` | `b4` là RAG phẳng lai ghép, cùng chế độ truy xuất với P | Không có số test của `b4` |
| Bỏ XN8, XN9 dạng cũ | XN9 với `b1` để trống gần hết là phép so tầm thường; XN8 trộn nhiều yếu tố | Kết quả hai vòng thử |
| T5 ngoài họ | Quá ít dòng | Như ADR 0005 |

RQ1–RQ3 giữ nguyên văn đề cương.

### 11. Giới hạn phải khai cạnh kết quả

- **Nhãn:** bộ cuối là **silver-AI có CMT duyệt**, không gọi là gold. Không có người gán độc lập thứ hai; ca khó do `legal-adjudicator` chốt, CMT ủy quyền, chưa qua luật sư (danh sách ở `data/review/ai_research/2026-11-11_h7/`, `2026-11-11_t6_package/`, `2026-11-11_t6_r2/`, `2026-11-11_t6_dev4/`, `2026-11-11_t1_labels/`). AC1 AI–AI gộp 0,608 < 0,80. CMT duyệt qua hội thoại, thời gian từng dòng không đo.
- **T1:** AI-A là Claude Sonnet (các lô khác Opus); AI-B dùng bản gán lại, phiên đó đã thấy nhãn AI-B lượt trước (không thấy AI-A). Câu hỏi và đáp án ngắn do Haiku viết.
- **Một generator chính** (GPT-4o mini); **một nguồn dữ liệu** (vbpl); 111 sự kiện "Luật/Pháp lệnh <tên>" và 2.633 sự kiện danh sách điều khoản chưa đo.
- **Cỡ mẫu nhỏ:** T3 6 lineage, chỉ báo mô tả.
- **`b5` không phải GraphRAG thật** (một bước láng giềng, không cộng đồng).

## Alternatives Considered

1. **Giữ v1.0 làm bộ xác nhận chính.** Bị loại: 43% dòng test chỉ có nhãn Codex, AC1 0,377, T3 chỉ 4 lineage. (Bộ cuối cũng chỉ có nhãn AI + CMT duyệt; lợi thế của nó là chưa hệ nào thấy, không phải nhãn tốt hơn hẳn.)
2. **Gộp ba bộ thành một phân tích tổng hợp.** Bị loại: khác cách gán nhãn và quy trình câu hỏi, và vai các bộ đổi sau khi thấy kết quả.
3. **Giữ TVER trong họ.** Bị loại vì là phép đo do cách dựng.
4. **Chọn P sau khi chạy test.** Bị loại: chọn trên dev theo quy tắc ở mục 2.

## Consequences

Positive:

- Có một lần xác nhận trên bộ chưa hệ nào thấy, nhãn "AI gán, CMT duyệt", với cấu hình đúng L4–L5 của đề cương.
- Mọi bậc tự do đã dùng được ghi ra.

Tradeoffs:

- Bộ cuối nhỏ (156 lineage chính), nên power cho hiệu cỡ +0,03 thấp. Kết quả "không đủ bằng chứng" là khả năng thật.
- F7 có thể không vào họ vì T6 thiếu. Nấc lan truyền có thể chỉ có bằng chứng thăm dò.
- Kết luận về bãi bỏ chỉ đúng với generator đã khóa (GPT-4o mini) và với đồ thị hiện tại.

## Follow-Up

- G2: điền danh sách lineage, sha256, cỡ mẫu, power.
- G3: điền kết quả áp quy tắc chọn P, generator, embedding; CMT, NMT duyệt; commit; rồi mới chạy test.
- `confirm_vilextime.py --family final` đã khớp mục 3 (05/11): F1–F7, F8 là TVER luôn ngoài Holm.
