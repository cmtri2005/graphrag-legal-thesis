# Execution Plan: Chốt ViLexTime và chạy thực nghiệm (giao Codex)

Date: 2026-10-27

## Status

Active. Claude soạn 27/10 theo yêu cầu của CMT. Đây là **hàng việc chính** từ 27/10 đến hết đợt chạy
test. Hai plan cũ giữ phần lý do và bối cảnh, việc còn lại của chúng được chép vào đây:
[`test-agent-kiem.md`](test-agent-kiem.md) (agent kiểm), [`ke-hoach-thuc-nghiem.md`](ke-hoach-thuc-nghiem.md)
(hệ, LLM, thí nghiệm), [`vilextime-dinh-nghia-chot.md`](vilextime-dinh-nghia-chot.md) (bước 6–8).

## Outcome

1. Bản ViLexTime final: mọi dòng `ranh_gioi` của `test` có nhãn cuối (người, luật sư hoặc agent đã hiệu
   chuẩn), `export_release.py --final` chạy không lỗi, datasheet và manifest khớp số.
2. ADR 0005 cập nhật số của bản final, nhóm duyệt sang Accepted và commit **trước** lần chạy test đầu tiên.
3. E1–E5 (và E6 nếu có gold) chạy trên `test`, mỗi cấu hình một lần; XN1–XN9 kèm Holm; bảng kết quả và
   sổ chạy `runs/README.md` đủ để viết khóa luận.

Hạn: chạy xong 31/10/2026 (quyết định A1, MASTER_RESEARCH_GUIDE §0.6).

## Quy tắc cho Codex (đọc trước mọi việc)

- Đọc `AGENTS.md`, `docs/WORKFLOW.md`, rồi chỉ mục được nhắc ở việc đang làm.
- Python: `.venv/bin/python` (python hệ thống thiếu `pytest`, `openpyxl`). Kiểm toàn repo:
  `.venv/bin/python -m pytest -q` (27/10: 546 qua).
- **Không commit, không tag, không push.** Làm xong một việc thì dừng ở diff, ghi vào mục Progress, CMT commit.
  Riêng ADR 0005 phải được commit trước khi chạy test: chờ CMT báo đã commit.
- **Không chạy hệ nào trên `test`** trước cổng G (mục Phần C). Mọi tinh chỉnh chỉ trên `dev`.
- Không sửa tay file dự đoán `runs/**/*.jsonl`, không đổi ngưỡng (AC1 ≥ 0,80, p_neg ≥ 0,60), không sửa
  scorer sau khi ADR 0005 Accepted. Không dùng `--fast-retrieval` cho số được báo. Luôn truyền `--split`.
- Không sửa nhãn người (`kiem_A.tsv`, `kiem_B.tsv`, `hoa_giai_kiem.tsv`, `gold_*.tsv`) và không mở các file
  đó khi đang làm việc gán nhãn mù (A2).
- Không in, không ghi khóa API ra file hay log. Khóa ở `.env` (hiện có Groq, DeepSeek).
- Không dùng Lawgical (20 lượt/ngày, để cho người). Tra văn bản: `data/raw`, web.
- Q1–Q5 đã có quyết định (bảng dưới). Gặp câu hỏi mới về chính sách mà repo chưa trả lời: dừng việc đó,
  làm việc khác không phụ thuộc, ghi lại trong Progress.
- Mỗi việc xong phải có bằng chứng chạy được (lệnh + số) ghi vào Progress. Không ghi "xong" khi chỉ đọc code.

## Quyết định của CMT (27/10)

| Mã | Câu hỏi | Quyết định | Áp vào |
|---|---|---|---|
| Q1 | Ai gán 714 dòng? | **Codex gán.** Định nghĩa §6 và hướng dẫn §6 đã sửa 27/10: agent kiểm là Codex, tên agent + model ghi ở `labeler` | A2 |
| Q2 | Dòng A đã gán một mình mà agent gán khác: lấy nhãn nào? | **Ưu tiên `dat`**: một trong hai ghi `dat` thì dòng `dat` | A4 |
| Q3 | 149 dòng thuộc 75 lineage gold của A: giao agent gán luôn? | **Có**, gán cùng 714 dòng. Nhãn agent không đưa lên trang gán nhãn, để gold của A vẫn mù nếu A làm sau | A1, A2, E6 |
| Q4 | Nhà cung cấp generator? | **CMT đổi quyết định 27/10: chạy trọng số Hugging Face trên Google Colab, không dùng thinking/API key trả phí cho B1.** Quyết định Groq ban đầu được giữ trong nhật ký bên dưới. | B1, B2, B5 |
| Q5 | Ba bổ sung "[đề xuất]" của `ke-hoach-thuc-nghiem.md` §5? | **Duyệt cả ba**: ngữ cảnh đúng, B4 lai RRF, bảng nhiều LLM (các model Hugging Face qua cổng B1) | B5 |

## Phần A — Chốt bộ dữ liệu

Hiện trạng đo 27/10 (Claude, `.venv/bin/python`):

- `test` có 934 dòng `ranh_gioi`. 220 dòng đã có nhãn của cả A và B theo hướng dẫn 3.0 (133 trùng nhau,
  87 lệch đã được luật sư hòa giải ở `hoa_giai_kiem.tsv`). **714 dòng còn lại cần agent kiểm** (khớp
  `test-agent-kiem.md`).
- `kiem_A.tsv`: 1.120 dòng, 971 có nhãn 3.0, 149 trống (lineage gold bị ẩn).
- Chưa có `data/review/kiem_agent.tsv`.
- `scripts/review/agent_packs.py build` hiện ra 832 dòng = 267 hiệu chuẩn + 565 cần gán. Lệch plan ở hai chỗ,
  xem A1.

### A1. Sửa `agent_packs.py` cho khớp plan — Codex

Vấn đề:

1. Tập hiệu chuẩn đang gồm cả 89 dòng hòa giải ngày 26/10. Luật sư đã xem phiếu của Claude khi chốt các
   dòng đó, nên chúng không mù. Plan chỉ cho hiệu chuẩn trên **178 dòng**: 166 dòng A = B theo 3.0 và 12 dòng
   lô 0 luật sư tự chốt (24/10, không dùng AI).
2. Tập cần gán đang bỏ 149 dòng lineage gold. Theo Q3, đưa chúng vào → **714 dòng**.

Cách làm:

- Phân biệt hai loại dòng hòa giải bằng dữ liệu có sẵn (lô 0 ở cột `lo` = `0`; dòng 26/10 là phần còn lại
  của `hoa_giai_kiem.tsv`). Nếu không phân biệt được bằng cột có sẵn thì dừng, báo lại.
- Dòng hòa giải 26/10 không vào gói (đã có nhãn cuối, không dùng để chấm agent).
- Khóa hiệu chuẩn `key_calib.tsv` vẫn ghi ra **ngoài** thư mục gói và ngoài repo.
- Thêm một test nhỏ trong `tests/` cho phép chọn dòng (một dòng hòa giải 26/10 bị loại, một dòng lô 0 được giữ).

Xong khi: `build --out <ngoài repo>/packs` in đúng `892 dòng (178 hiệu chuẩn, 714 cần gán)`, 18 gói;
`pytest` qua. Số khác 178/714 thì dừng và ghi số đo vào Progress.

### A2. Gán mù 892 dòng — Codex (Q1), trong phiên riêng

Phiên Codex đang làm trong repo **không được** tự gán: nó đã đọc được nhãn người và khóa hiệu chuẩn.
Việc gán chạy trong **một phiên Codex mới**, mở ở thư mục ngoài repo.

Phiên trong repo chuẩn bị:

- `prompts/vilextime/agent_kiem.md`: lời dặn cố định cho agent, viết từ `docs/vilextime-annotation.md`
  (8 bước, mã loại đóng, §7 Hỏi đáp gồm sáu kết luận lô 0 và ba quy tắc 26/10). Lời dặn không chứa nhãn
  hay ví dụ lấy từ dòng nằm trong gói. Đầu ra mỗi dòng đúng các cột `OUT_COLS` của `agent_packs.py`.
  Ghi sha256 của prompt vào Progress; **không sửa prompt giữa hiệu chuẩn và gán hàng loạt**.
- Thư mục gán, ví dụ `~/vilextime_gan_mu/`: chỉ chứa `pack_*.jsonl`, prompt, và một `AGENTS.md` ngắn ghi
  "chỉ đọc file trong thư mục này và văn bản luật trên web; không mở thư mục `graphrag-legal-thesis`".
  Khóa `key_calib.tsv` **không** nằm trong thư mục này.

Phiên gán (CMT mở Codex trong thư mục gán): gán cả 18 gói theo prompt, ghi `result.tsv` tab-separated.
Dòng hiệu chuẩn và dòng cần gán trộn lẫn, phiên gán không biết dòng nào bị chấm. Ghi model Codex
(tên + phiên bản) để điền `labeler`.

Kiểm mù sau khi gán: CMT hoặc phiên trong repo tìm trong log phiên gán xem có đường dẫn tới repo, tới
`kiem_*.tsv`, `hoa_giai_*.tsv` hay `key_calib.tsv` không. Có thì hiệu chuẩn mất giá trị: ghi lại, gán lại
trong thư mục sạch.

### A3. Chấm hiệu chuẩn — Codex

```bash
.venv/bin/python scripts/review/agent_packs.py score --out <dir>/packs <dir>/result.tsv
```

- Đạt (AC1 ≥ 0,80 **và** p_neg ≥ 0,60 trên 178 dòng): sang A4. Ghi bảng theo nhóm T1/T2/T3/T6 vào Progress.
- Không đạt: **dừng cả Phần A**, ghi số đo. CMT chọn hướng 2 hoặc 3 của `test-agent-kiem.md`. Không đổi
  ngưỡng, không gán lại cùng gói với prompt khác rồi chọn lần tốt hơn.

### A4. Ghi `kiem_agent.tsv` và nối vào bản phát hành — Codex

- `data/review/kiem_agent.tsv`: chỉ 714 dòng cần gán; cột như `kiem_A.tsv` phần nhãn (`id`, `verdict`,
  `reasons`, `note`, bốn ô dẫn chứng) cộng `labeler` (tên agent + model) và `guideline_version` = `3.0`.
  Kiểm mã loại bằng cùng hàm kiểm của `label_ui.py` / `crosscheck_xlsx.py import`.
- `scripts/pipeline/export_release.py`: thứ tự lấy nhãn cuối của một dòng
  1. luật sư (`hoa_giai_kiem.tsv`),
  2. A và B cùng nhãn theo 3.0,
  3. dòng trong `kiem_agent.tsv`: nhãn agent; nếu A cũng gán dòng đó theo 3.0 và hai nhãn khác nhau thì
     lấy **`dat`** (Q2). `reasons` của dòng đó giữ mã của bên `khong_dat` ở `meta` để phân tích sau.
  `meta` ghi `review.labeler`; `manifest.json` đếm riêng dòng người kiểm, dòng agent kiểm, và số dòng A–agent
  lệch đã lấy `dat` theo Q2 (định nghĩa §6 điều 3).
- Test: một dòng chỉ có nhãn agent ra đúng nhãn agent; một dòng có cả luật sư và agent ra nhãn luật sư;
  A `dat`, agent `khong_dat` ra `dat`; A `khong_dat`, agent `dat` ra `dat`.

Xong khi: `export_release.py` (không `--final`) chạy, manifest có hai số đếm, `pytest` qua.

### A5. Luật sư kiểm 50 dòng agent — Codex chuẩn bị, luật sư làm

- Codex rút 50 dòng ngẫu nhiên trong 714 dòng agent, seed `luat-su-agent-2710` (ghi seed vào Decisions),
  xuất `data/review/luat_su_kiem_agent.xlsx` cùng kiểu phiếu `hoa_giai_kiem.xlsx` (có trích văn bản gốc,
  có nhãn và ghi chú của agent, ô để luật sư điền `dong_y` / `khong_dong_y` + lý do).
- Luật sư điền. Codex nạp, báo `x/50` kèm khoảng Wilson 95% vào Progress và datasheet. Không tự sửa nhãn
  agent theo kết quả này; nếu luật sư không đồng ý nhiều dòng (dưới 45/50), dừng và báo CMT.

### A6. Loại dòng hỏng của phiếu `kiem` — Codex

- Thêm `drop` cho bộ `kiem` vào `scripts/review/adjudicate.py` (đã có cho D4): lineage có một dòng ranh giới
  `khong_dat` vào `dropped.jsonl` với mã loại; dòng anh em (`giua_khoang`, `truoc_hieu_luc`) đi theo.
- Báo cơ cấu sau khi loại so với sàn ở định nghĩa §9. Dưới sàn: **giảm quota, không nới điều kiện**
  (đã chốt). Không lấy dòng dự trữ trừ khi CMT bảo, vì dòng thay cũng phải được kiểm.

### A7. Đóng băng — Codex, CMT commit và tag

Thứ tự:

1. `export_release.py --final` chạy không lỗi (từ chối nếu còn dòng chưa có nhãn cuối).
2. `scripts/check/check_release.py` (hoặc lệnh kiểm release hiện có) OK.
3. `docs/vilextime-datasheet.md`: cập nhật số dòng, câu hỏi, lineage theo nhóm và split; mục người kiểm ghi
   đúng: 220 dòng hai người (AC1 thô 0,377, chưa đạt), luật sư hòa giải 101 dòng (89 có phiếu Claude hỗ trợ),
   714 dòng agent Codex (AC1, p_neg hiệu chuẩn; luật sư x/50), số dòng A–agent lệch đã lấy `dat` (Q2),
   A gán ~5 giây/dòng và 288 ghi chú nháp của Claude.
   Bỏ mọi mục "chưa xong" hoặc chuyển thành giới hạn đã nêu.
4. Bảng "Chỗ lệch với đề cương" của datasheet: thêm gán chéo 106 thay 25%, agent kiểm phần lớn test.
5. `manifest.json` có sha256 của các file phát hành. CMT commit và tạo tag `vilextime-v1.0`.
6. E0 chạy lại trên bản final (dev và test): probe oracle đạt trần, `hedge` bị phạt. Lệnh:
   `.venv/bin/python scripts/eval/score_vilextime.py --probes --ci 1000 --split <dev|test> --release
   data/vilextime_dataset/vilextime.jsonl --out runs/E0_final/<split>/probes.score.json`. Probe không phải
   hệ nên được chạy trên test sau khi đóng băng.

## Phần B — Chuẩn bị trên `dev` (song song Phần A, không cần nhãn)

### B0. Lọc theo chế độ `as_of` trong runner — Codex

`run_vilextime.py` hiện chạy mọi dòng của split, kể cả `ranh_gioi` và `truoc_hieu_luc`. Quyết định C2:
**sinh câu trả lời chỉ ở `giua_khoang`**, các chế độ khác chỉ truy xuất. Thêm cờ `--as-of-strategy`
(mặc định giữ nguyên hành vi cũ), ghi vào `run.json`. Test nhỏ: với cờ, chỉ dòng đúng chế độ ra file.
Nếu không có cờ này, đợt test tốn gấp đôi lời gọi LLM.

### B1. Chọn generator (W1-09, MASTER_RESEARCH_GUIDE §7.5) — Codex, CMT đọc 20 câu

1. Hai ứng viên khác họ, tải trọng số từ Hugging Face và chạy cục bộ trên Colab GPU:
   `Qwen/Qwen3-4B-Instruct-2507` (chỉ non-thinking) và `microsoft/Phi-3.5-mini-instruct`.
   Ghi model revision, GPU, thời gian, lượng token và chi phí Colab thực tế; không coi tầng miễn phí là
   tài nguyên được bảo đảm.
2. Xuất **cùng một** bộ 100 prompt `b2ctx`, `dev`, `giua_khoang` (không gold) bằng
   `scripts/eval/colab_b1.py export`, rồi dùng `scripts/eval/colab_b1_runtime.py` trên Colab với
   greedy decoding (`do_sample=False`), 4-bit NF4, `max_new_tokens=512`. Mỗi model có file raw riêng,
   checkpoint theo từng câu trên Drive. Nạp raw bằng `colab_b1.py import` để tạo file scorer.
3. Đo: tỷ lệ đúng định dạng (`HIỆU LỰC` / `TRẢ LỜI` / trích dẫn) ≥ 95%; 0 câu cắt cụt; token vào/ra trung
   bình; chi phí ước cho cả đợt test. Nếu runner chưa ghi đủ để đo hai điều đầu, thêm phần ghi tối thiểu.
4. Xuất 20 câu trả lời ngẫu nhiên của mỗi ứng viên qua cổng tự động ra một file để CMT đọc.
5. Chọn model qua cổng có thời gian/chi phí Colab thấp hơn làm generator chính; model qua cổng khác họ
   làm model độ bền. Không model nào qua thì dừng chọn và báo CMT. Codex soạn amendment ADR 0004
   (model, revision, phần cứng, chi phí, ngày, số đo cổng); CMT duyệt.

### B2. Chạy thử có sinh câu trả lời trên dev — Codex

- Mọi hệ có trên `test` sau này, cùng generator ở B1, `--split dev --as-of-strategy giua_khoang`:
  `b1 b2ctx b7 b7v b7plus b7pp proposed b5 b6 a1 a2 a3 a4` (`b5`, `b6` và thang dùng `--no-dense`); `b3`
  với `--embed data/derived/embed/asis-vietnamese-embedding`.
- Trước B2, mở rộng cách chạy batch Colab cho mọi hệ: xuất prompt riêng cho từng cấu hình cùng runner,
  nhập raw vào scorer và giữ `run.json`/provenance. Không dùng lệnh `--provider` API trong B2 khi model
  được chọn chỉ có trọng số cục bộ.
- Chấm: `score_vilextime.py ... --split dev --ci 2000`. Chạy `confirm_vilextime.py --retrieval
  runs/E1_2610/dev --generation runs/E3_try/dev --split dev` để chắc công cụ đọc được đủ XN1–XN9.
- Dao động: `proposed` chạy lần hai trên 100 dòng dev (`--restart`, file khác). Ghi chênh lệch giữa hai lần
  vào Progress; ADR 0005 §7 dùng số này để giảm nhẹ kết luận.
- Ghi từng lượt vào bảng nhật ký `runs/README.md`.
- Mục đích: bắt lỗi đường ống, đo token và thời gian. **Không** dùng số dev để chọn giả thuyết.

### B3. Cập nhật ADR 0005 theo bản final — Codex soạn, nhóm duyệt

Sau A7. Sửa §1: đường dẫn và sha256 của release final, số dòng và lineage của bảng chính và từng lát (đếm
bằng chính `SLICES` của `confirm_vilextime.py`), số dòng T5. Sửa §2 nếu B0/B1 đổi lệnh. Giữ `Proposed`.
CMT và NMT duyệt, đổi sang `Accepted` (ghi người duyệt, ngày), **CMT commit**. Codex không tự đổi Status.

### B4. Chuẩn bị bảng kết quả — Codex

Một script nhỏ đọc các `*.score.json` và `confirm.json` của `runs/**/test/` ra bảng Markdown
`docs/reports/ket_qua_test.md` (bảng chính theo nhóm, thang, XN1–XN9 với p sau Holm và khoảng tin cậy,
số dòng và lineage). Chạy thử trên số dev, ghi rõ trên đầu file là số dev cho tới khi có test.

### B5. Ba bổ sung (Q5 đã duyệt) — Codex

Cả ba là phần mô tả, không vào họ XN1–XN9, không sửa ADR 0005 §4. Làm và chạy thử trên dev trước cổng G.

- **Ngữ cảnh đúng (oracle context):** script riêng ngoài runner (runner bị khóa không thấy gold), đưa đúng
  đoạn có hiệu lực tại mốc cho generator; báo là cận trên. Test ở C10.
- **B4 lai RRF:** BM25 + dense trộn thứ hạng RRF, không reranker; bỏ `NotImplementedError` ở
  `framework/retrieve.py` chỉ cho trường hợp này; test cho phép trộn. Tên hệ ghi rõ "không reranker".
  Test cùng C2.
- **Bảng nhiều LLM:** `b1`, `b2ctx`, `proposed` trên hai model Hugging Face qua cổng B1. Test ở C11.

## Phần C — Chạy trên `test`

### Cổng G (kiểm cả bốn trước lệnh test đầu tiên, ghi bằng chứng vào Progress)

1. A7 xong: release final, CMT đã commit và tag.
2. ADR 0005 `Accepted` và đã commit (ghi hash commit). Ngày commit phải sớm hơn mọi file trong `runs/**/test/`.
3. Amendment ADR 0004 ghi generator và model độ bền đã commit.
4. `pytest` qua; B2 chạy được mọi hệ trên dev không lỗi.

### Thứ tự chạy

Mọi lệnh có `--split test --release data/vilextime_dataset/vilextime.jsonl`; mỗi cấu hình **một lần**;
mỗi lượt một dòng ở `runs/README.md` (ngày, mã, hệ, commit, mục đích, tóm tắt, ghi chú). Chạy hỏng giữa
chừng thì chạy tiếp (runner giữ dòng đã có), không `--restart`.

| Bước | Thí nghiệm | Hệ | Cờ | Thư mục |
|---|---|---|---|---|
| C1 | E1 thang chỉ truy xuất | `b2ctx b7 b7v b7plus b7pp` | `--no-dense --retrieval-only`, mọi chế độ | `runs/E1/test` |
| C2 | E2 | `b1`, `b2`, `b2ctx`, `b3`, `b4` (RRF) | `--as-of-strategy giua_khoang`; `b3`, `b4` với `--embed` | `runs/E2/test` |
| C3 | E3 thang có sinh | `b7 b7v b7plus b7pp proposed` | `--no-dense --as-of-strategy giua_khoang` | `runs/E3/test` |
| C4 | E5 ablation | `a4` trước, rồi `a1 a2 a3` | như C3 | `runs/E5/test` |
| C5 | E4 đồ thị phi thời gian | `b5`, `b6` | như C3 | `runs/E4/test` |
| ~~C6~~ | Độ bền (bỏ 29/10, phase 2) | `b2ctx b7 proposed` với model độ bền | như C3, `--model <độ bền>` | `runs/robust/test` |
| C7 | XN1–XN9 + Holm | — | `confirm_vilextime.py --retrieval runs/E1/test --generation runs/E3/test --split test --draws 10000` (hệ `b1`, `b2ctx`, `b5` phải có mặt trong thư mục `--generation`: chép hoặc chỉnh đường dẫn, không chạy lại) | `runs/confirm_test.json` |
| C8 | E6 gold độc lập | thang + baseline chính | chỉ khi có gold (Q3) | `runs/E6/test` |
| C9 | Bảng kết quả | — | B4 trên số test | `docs/reports/ket_qua_test.md` |
| C10 | Ngữ cảnh đúng (mô tả) | script B5 | `giua_khoang` | `runs/oracle_ctx/test` |
| ~~C11~~ | Bảng nhiều LLM (bỏ 29/10, phase 2) | `b1 b2ctx proposed` × model Hugging Face qua cổng | batch Colab theo B2 | `runs/multi_llm/test` |

Chấm mỗi bước: `score_vilextime.py <các file> --split test --release ... --ci 10000 --out <thư mục>/<tên>.score.json`
(nhiều hệ một lệnh để scorer đọc `versions.jsonl` một lần).

Kết luận theo ADR 0005 §6 nguyên văn: ủng hộ / bác / không đủ bằng chứng. Nếu XN1 không được ủng hộ thì ghi
nhánh "điểm quyết định B7", không tìm chỉ số khác cho đẹp. Mọi số ngoài XN1–XN9 ghi nhãn "thăm dò".

### Sau 31/10

- E7 phân tích lỗi (MASTER_RESEARCH_GUIDE §9.4): Codex rút mẫu từ `proposed`, `b7`, `b2ctx`, `b1` ra phiếu có
  mã lỗi; người gán.
- Giám khảo LLM (C4): `judge_vilextime.py sample` 100 dòng → người gán → `agree`; chỉ là cột phụ.
- E8 độ nhạy, LightRAG trên tập con (C3), bảng nhiều LLM ngoài hai ứng viên B1 khi có nguồn lực.

## Lịch đề xuất

| Ngày | Phần A (dữ liệu) | Phần B/C (thực nghiệm) |
|---|---|---|
| 27/10 | A1, chuẩn bị A2 | B0, B1 chạy cổng |
| 28/10 | A2 gán, A3 chấm, A4 | CMT đọc 20 câu, chốt generator; B2 trên dev |
| 29/10 | A5 gửi luật sư, A6, A7 | B3 soạn ADR 0005; B4 |
| 30/10 | Nạp A5, CMT commit + tag | Cổng G; C1 → C5 |
| 31/10 | — | C6 → C11 |

Trễ ở A2/A3 thì C dời theo, **không** chạy test trên bản chưa final.

## Risks And Recovery

- Agent không đạt hiệu chuẩn: Phần C không chạy được trên bản final trước 31/10. Phần B vẫn làm được;
  báo CMT ngay khi có số của A3.
- Lộ nhãn khi gán mù (agent đọc được repo): hiệu chuẩn mất giá trị. Phòng bằng thư mục làm việc riêng ở A2;
  nếu nghi lộ, ghi lại và gán lại cả 18 gói trong thư mục sạch.
- Colab hết GPU, ngắt phiên hoặc thiếu VRAM: batch checkpoint từng câu lên Drive; nạp lại cùng prompt hash,
  model revision và cấu hình. Ước 13 hệ × 934 dòng ≈ 12.000 lần sinh; cổng 100 câu không chứng minh
  Colab miễn phí đủ tài nguyên cho toàn đợt, cần đo tốc độ trước cổng G.
- Chạy nhầm trên `test` trước cổng G: không xóa file. Ghi một dòng ở `runs/README.md` (lệnh, giờ, lý do) và
  báo CMT; dòng đó là bằng chứng phải công bố.
- Sửa `export_release.py` làm đổi bản phát hành ngoài ý muốn: so `vilextime.jsonl` trước và sau sửa trên
  cùng nhãn (chỉ dòng có nhãn agent được phép đổi).

## Progress

- 29/10, Claude, C1 xong: E1 trên test, 5 hệ × 441 dòng, chấm `--ci 10000` → `runs/E1/test/ladder.score.json`
  (số ở `runs/README.md`). Sự cố `b7pp` (hai tiến trình cùng ghi sau khi phiên bị ngắt) đã xử lý như ghi ở sổ chạy:
  giữ file gốc, bản sạch đủ 441/441 ID. Bài học: trước khi chạy tiếp một runner, kiểm `ps` xem tiến trình cũ đã
  chết chưa. Đang xuất prompt test Colab vào `runs/test_prompts/` (xong `b1 b2ctx b7 b7pp`).
- 29/10, Claude, **Cổng G qua**: (1) release final commit `3e487c4`, tag `vilextime-v1.0` (CMT bảo tag),
  sha256 `7cf51ee6…`, export và `data/review` không đổi tới HEAD; (2) ADR 0005 Accepted, commit `a64a5bc`,
  trước mọi file dự đoán trên test (`runs/**/test/` lúc đó chỉ có probe E0); (3) amendment ADR 0004 đã
  commit, không có model độ bền (C6, C11 hoãn), còn thiếu chi phí Colab; (4) `.venv/bin/python -m pytest -q`
  → **564 passed**. Bắt đầu C1.
- 29/10, Claude, ADR 0005 Accepted: CMT chọn chuyển XN5–XN7 sang thăm dò (Holm trên 6: XN1–XN4, XN8,
  XN9), bỏ C6/C11 cho phase 2, người duyệt CMT và NMT. `confirm_vilextime.py`: `EXPLORATORY`, `FAMILY`;
  XN5–7 vẫn tính, `p_Holm=—`, kết luận "thăm dò". Confirm dev chạy lại: Holm 6/6, XN1–4, XN8, XN9 ủng hộ.
  `colab_b1.py` nhận `--split test` chỉ khi Status của ADR 0005 ở HEAD là Accepted (`adr_accepted`, đọc
  bằng `git show`); import nhận dev hoặc test. Runtime và notebook nhận split test. Lệnh xuất test bị từ
  chối đúng khi ADR còn Proposed. Test: `test_colab_b1 test_confirm_vilextime test_report_results
  test_export_release test_agent_sample` qua. Còn tag `vilextime-v1.0` (CMT) trước C1.
- 29/10, Claude, nạp luật sư lượt 2 (`data/review/luat_su_kiem_q2_da_chot.xlsx`): 67/67 dòng, cột gốc
  không bị sửa; chốt `dat` 13 (T6 8, T1 5), `khong_dat` 54; đồng ý agent 54/67. `luat_su_kiem_agent.tsv` gộp
  117 dòng. `export_release.py --final` → sha256 `7cf51ee6…`, 769 dòng chính, 859 silver; dev 328/328 không
  đổi. Test `giua_khoang` **211/165**: T1 123, T2 46, T3 12, **T6 30/15**; `t6_ancestor_repealed` **12/12**.
  7/8 dòng T6 luật sư chốt `dat` là dòng trước ngày bãi bỏ; dòng ngày bãi bỏ cùng lineage bị chốt
  `khong_dat` (nội dung chuyển chỗ), nên lineage vẫn bị loại. Nguồn nhãn 211 dòng ranh giới test: luật sư 33,
  A+B 88, agent 90. E0 chạy lại (`runs/E0_final/{dev,test}/probes.score.json`, `--ci 1000`): oracle 1,000
  cả ba chế độ; 12/246 trích dẫn chữ không phân giải. Cập nhật ADR 0005 §1 (vẫn Proposed), định nghĩa §6
  điều 4–5, datasheet. Chờ nhóm: họ XN với các lát T6 nhỏ; xác nhận phiếu luật sư có dùng AI hỗ trợ không;
  tag.
- 29/10, Claude, Q2 đảo, chờ luật sư lượt 2: CMT đồng ý hướng 1 (A–agent lệch thì lấy nhãn agent).
  `export_release.py` đọc thêm `data/review/luat_su_kiem_agent.tsv` (nhãn luật sư, cùng mức ưu tiên với
  `hoa_giai_kiem.tsv`). Field manifest đổi thành `a_agent_disagreement`. `agent_sample.py --load` nạp phiếu
  luật sư và gộp theo id; `--q2` xuất phiếu cho các dòng còn lại. `export_release.py --final` (chưa commit,
  sha256 `8f16f3a7…`): dev không đổi 328/328. Test `giua_khoang` còn **204/159**, T6 **28/14**,
  `t6_ancestor_repealed` **11/11** (trước đó 333/226, 152/76, 56/56). Mình đã ước mất khoảng 40–50 lineage,
  thực tế mất 67, vì đảo Q2 loại cả 80 dòng xung đột chứ không chỉ phần hỏng. Gốc rễ: 59/82 dòng Q2 bị agent
  gắn `relocation_unclear` (R2: bãi bỏ có nội dung chuyển sang văn bản thay thế). CMT chọn hướng 3: luật sư
  xem 67 dòng còn lại, `data/review/luat_su_kiem_q2.xlsx` (T6 62, T1 5). Nạp bằng `agent_sample.py --load`,
  rồi chạy lại `--final`. Test `test_agent_sample.py`, `test_export_release.py` → 4 passed. Chưa sửa
  định nghĩa §6 điều 4, datasheet, ADR 0005 §1, E0; chờ số cuối.
- 29/10, Claude, A5 nạp phiếu luật sư (`data/review/luat_su_kiem_agent_da_chot.xlsx`): 50/50 dòng, cùng
  ID và thứ tự với phiếu gốc, cột gốc không bị sửa, đủ `dong_y`/`ly_do`; thêm `ket_luan_chot`, `do_tin_cay`.
  Đồng ý với agent **43/50 = 0,86, Wilson 95% [0,738; 0,930]**: **dưới ngưỡng 45/50, theo A5 dừng và báo
  CMT**, không sửa nhãn. Agent `dat` 27/27; agent `khong_dat` 16/23. Cả 7 dòng lệch đều là agent
  `khong_dat`, luật sư `dat`. Hệ quả cho release: 36/50 dòng nằm trong test chính, nhãn cuối khớp luật sư ở
  28/36 [0,619; 0,883]. Cả 8 dòng sai đều do Q2 ghi đè (A `dat` / agent `khong_dat` → `dat`) trong khi luật
  sư chốt `khong_dat`. Trong 12 dòng Q2 được luật sư xem, luật sư đứng về phía agent ở 8/12 [0,391; 0,862].
  Q2 chạm 82 dòng ranh giới test (T6 75, T1 7), 72/226 lineage, 137/333 dòng `giua_khoang`. 14/50 dòng
  mẫu không có trong release công bố. Chờ CMT chọn hướng xử lý Q2 trước A7/tag.
- 29/10, Claude, đóng phần dev: CMT chọn `oracle` bản 1. `colab_b1.py` trả về bản 1 (bỏ `last_version`).
  Xuất lại ra đúng sha256 `e092986c…`, nạp raw cũ, 151/151. Bản 2 giữ làm số chẩn đoán ở
  `runs/B2_dev/{prompts,dev}/oracle_v2.*`. Chấm lại 17 hệ (`all.score.json`, `--ci 2000`): `oracle` Acc 0,854
  [0,796; 0,904], TVER 0. Sinh lại `docs/reports/ket_qua_test.md`. Test
  `test_colab_b1 test_report_results test_rag_systems test_export_release` → 18 passed. Dev còn lại một
  việc: cổng B1 cho Phi-3.5 (model độ bền, bảng nhiều LLM) nếu nhóm giữ C6/C11.
- 29/10, Claude, `oracle` bản 2 trên dev: Acc 0,834, TVER 0,126, T6 bãi bỏ 3/21 (bản 1: 0,854, TVER 0,
  6/21). Có lời văn điều khoản thì model trả "còn" ở 18/21 dòng. Bản 2 kém hơn và đưa vào một đoạn đã hết
  hiệu lực, trái định nghĩa B5. Đề xuất (chờ CMT): quay lại bản 1 (prompt `e092986c…`, raw đã có, không cần
  chạy lại), giữ bản 2 làm số chẩn đoán. Hệ quả cho H3: ở dòng bãi bỏ, generator là nút thắt ngay cả khi
  ngữ cảnh đúng; nên ghi vào phần giới hạn khi viết XN5, XN7.
- 29/10, Claude: CMT đồng ý sửa `oracle`. Dòng bãi bỏ nay có hai đoạn: phiên bản cuối của điều khoản
  được hỏi (`last_version` trong `colab_b1.py`), rồi đến lệnh bãi bỏ. Dòng có đáp án không đổi: 130/130
  hash prompt trùng bản cũ, 21 dòng bãi bỏ có 2 đoạn. Prompt mới `runs/B2_dev/prompts/oracle.jsonl` sha256
  `35b510ec…`; cả 152 dòng bãi bỏ của test đều có phiên bản. Raw cũ (`e092986c…`) giữ ở `raw/` làm bằng
  chứng; chờ CMT chạy lại trên Colab.
- 29/10, Claude, nạp `b2` và `oracle` dev: hash prompt khớp, mỗi hệ 151/151; chấm lại 17 hệ →
  `runs/B2_dev/dev/all.score.json`, `docs/reports/ket_qua_test.md` sinh lại. `oracle` Acc 0,854, nhưng T6
  bãi bỏ chỉ đạt 6/21: với `repeal_mode = ancestor`, ngữ cảnh chỉ có lệnh bãi bỏ Điều cha, không có điều
  khoản được hỏi. Đề xuất (chờ CMT): dòng bãi bỏ đưa phiên bản cuối của điều khoản rồi mới tới lệnh bãi bỏ,
  sau đó chạy lại `oracle` dev. XN không đổi (`b2`, `oracle` không thuộc họ).
- 29/10, Claude: CMT chọn chạy `b2` trên test (C2 thêm `b2`, khớp ADR 0005 §2). Đã xuất
  `runs/B2_dev/prompts/b2.jsonl`: 151 dòng dev, sha256 `5adbe3bd…`, không có header phân cấp. Runtime và
  notebook nhận `b2` (code nhúng khớp byte). Chờ chạy trên Colab dev trước cổng G.
- 29/10, Claude, E0 và hai ADR (bản nháp): chạy lại `score_vilextime.py --probes --split dev|test
  --release data/vilextime_dataset/vilextime.jsonl` trên code hiện tại: oracle Accuracy **1,000** ở cả ba
  chế độ (dev 151, test 333). Con số 0,993/0,982 trong nhật ký 28/10 là từ trước khi sửa `lead_in`; việc
  "tìm dòng oracle chưa đủ trần" coi như xong. Còn 12/307 trích dẫn chữ không phân giải, đều ở T1 test
  (thiếu Điều hoặc nhãn lạ), đã ghi là giới hạn ở ADR 0005 §1. ADR 0004: thêm amendment 29/10 (generator
  Qwen3-4B, số đo cổng B1, chưa có model độ bền, chi phí chờ CMT điền). ADR 0005 (vẫn Proposed): §1 thêm
  E0, §2 thêm generator và `b3`/`b4`, §7 thay việc chạy hai lần bằng 553/553. Chờ nhóm quyết: XN6/XN7 có
  chuyển sang thăm dò không; `b2` có trong §2 nhưng không có ở bảng C; model độ bền. Phát hiện chặn C:
  `colab_b1.py` export/import chỉ nhận `--split dev`, nên chưa xuất được prompt test qua Colab.
- 29/10, Claude, B2 đóng, B4, B5 ngữ cảnh đúng: CMT đồng ý dùng 553/553 dòng output trùng làm số dao
  động thay lần `--restart` 100 dòng (B2 xong). B4: `scripts/eval/report_results.py <score.json…>
  --confirm <confirm.json> --out docs/reports/ket_qua_test.md` chỉ đọc số scorer/confirm đã ghi (bảng
  chính, Acc theo nhóm, hiệu ghép cặp, XN1–XN9 với Holm, dòng/lineage); tự ghi "Số dev" ở đầu khi có file
  dev. Đã chạy trên `runs/B2_dev/dev/`. B5 ngữ cảnh đúng: `colab_b1.py export --system oracle` đưa đúng
  một đơn vị gold làm căn cứ: `version_id` (phiên bản có hiệu lực tại mốc), dòng bãi bỏ thì lệnh bãi bỏ
  trong `accepted_evidence`; khung prompt như `b2ctx`, không qua runner. Dev: 151 prompt (130 phiên bản,
  21 lệnh bãi bỏ), `runs/B2_dev/prompts/oracle.jsonl` sha256 `e092986c…`; runtime và notebook nhận
  `oracle` (code nhúng khớp byte). Nhập thử raw giả 151/151 qua. Chưa chạy Qwen. Test:
  `tests/test_colab_b1.py tests/test_report_results.py` → 3 passed.
- 29/10, Claude, nạp B2 lượt 2–3: CMT upload raw `b3 b4` (1×T4) và `b5 b6 a1 a2 a3 a4` (2×T4,
  backend `t4_sdpa_force_repeat_kv`, bản này **không có trong repo**). Hash prompt khớp cả 8 file; raw
  chuyển vào `runs/B2_dev/raw/`. `colab_b1.py import` vỡ vì runtime mới ghi `gpu` dạng list; sửa để
  nối thành chuỗi như cũ. 151/151 dòng mỗi hệ. Chấm 15 hệ một lệnh → `runs/B2_dev/dev/all.score.json`
  (lượt 1 trùng số cũ); confirm dev **9/9 XN** (XN8 `proposed − b5` +0,305 [+0,218; +0,391]); số ở
  `runs/README.md`. Dao động: prompt trùng byte cho output trùng byte ở 553/553 dòng giữa hai lượt Colab
  (`a3`≡`proposed`, `a2`≡`b7pp`, một phần `b5`, `a4`), nên greedy ổn định qua lần chạy và backend.
  Đây chưa phải lần chạy `--restart` 100 dòng mà B2 ghi; CMT quyết có thay được không. Verifier không
  bác dòng nào trên dev, nên A3 hiện không đo được gì. `pytest tests/test_colab_b1.py` → 2 passed.
- 28/10, Claude, Colab lượt 2: notebook repo hết bộ nhớ ở `b3` (SDPA trên T4 rơi về kernel math vì
  KV nhóm, đòi 29 GiB). Bản lượt 1 (`t4_sdpa_repeat_kv`) không có trong repo, nên viết lại trong
  `colab_b1_runtime.py` (nhân head KV, ép kernel memory-efficient, truyền `attention_mask`) và chép
  vào notebook; meta ghi `attention_backend`. Kiểm trên CPU (Qwen3 nhỏ, kernel math thay efficient):
  logits và 20 token greedy trùng eager, hàm được gọi 42 lần. Chưa chạy trên GPU thật. Truy xuất dev
  `giua_khoang` 151 dòng: R@1 `b3` 0,272, `b4` 0,411 (`b2ctx` 0,391), ở `runs/B2_dev/retrieval/`.
- 28/10, Claude B2 (lượt 1, 7 hệ): CMT chạy Qwen3-4B-Instruct-2507 (rev `cdbee75`, NF4, greedy,
  2×T4) trên Colab, raw ở `runs/B2_dev/raw/`. Nạp bằng `colab_b1.py import` → `runs/B2_dev/dev/`,
  151/151 dòng mỗi hệ, đúng định dạng 97,4–100%, cắt cụt ≤ 3. `proposed` lúc đầu không nhập được:
  Verifier chấm nút lệnh `asis:event` theo tier `propagated` (không có cửa sổ → "hết hiệu lực") trong
  khi bước mở rộng nhận nó theo ngày hiệu lực văn bản. Sửa `temporal.windows_for` cho nút
  `instruction` dùng cửa sổ văn bản ở mọi tier; test `test_rag_graphx.py` hỏng khi bỏ bản sửa.
  Đường truy xuất không đổi, nên prompt đã chạy vẫn hợp lệ. `confirm_vilextime.py` đọc release nội
  bộ (186 dòng dev) thay vì bản công bố (151): thêm `--release` dùng `load_rows` của scorer; lệnh C7
  vốn đã ghi `--release`. Kết quả `giua_khoang` xem `runs/README.md`; confirm dev 8/9 XN (XN8 chờ
  `b5`). Xuất tiếp prompt `b5 b6 a1 a2 a3 a4` (`--no-dense`) cho lượt Colab 2. Chưa làm: `b3`
  (export Colab chặn dense), lần chạy 2 của `proposed` (greedy + checkpoint theo hash sẽ bỏ qua dòng
  đã có). Ước test: 333 dòng × ~12,5 s ≈ 70 phút/hệ trên 2×T4. Test theo file: **560 passed**
  (chạy cả repo một lệnh bị kill do thiếu RAM).
- 28/10, Codex bàn giao prompt B2 cho Colab: `runs/B2_dev/prompts/{b1,b2ctx,b7,b7v,b7plus,b7pp,proposed}.jsonl`
  đã xuất đủ 151 dòng `dev giua_khoang` mỗi hệ từ release final, 151 ID riêng và cùng tập ID;
  không có trường gold, SHA256 từng file khớp `.export.json`. Notebook
  `notebooks/colab_b2_dev.ipynb` và `colab_b1_runtime.py` nhận 1–7 prompt JSONL trong một lần
  upload, nạp Qwen một lần, checkpoint riêng theo hệ/model/hash. Đã kiểm cú pháp runtime và
  code nhúng trong notebook khớp byte; `.venv/bin/python -m pytest -q tests/test_colab_b1.py`
  → **2 passed**. Chưa chạy model trên Colab hoặc hệ nào trên test.
- 28/10, Codex E0/B3/B2 (theo yêu cầu sau nhật ký Claude): trên release final SHA256
  `19c515baca1b1628afe9916055a6b77ff432f6325808b39cfc502aeeccebe437`, oracle trượt
  2 dòng dev (1 lineage T1 × `giua_khoang`/`ranh_gioi`) và 12 dòng test (6 lineage T1 × hai mốc).
  Tất cả thiếu span ở câu dẫn cấp cha (`lead_in`): scorer đọc `context` làm đáp án nhưng đặt
  `target.lead_in = None`; probe chỉ ghép text của điểm, nên thiếu mức phạt hoặc chủ thể trong
  `short_answer`. Cùng phép chuyển đổi đó tạo trích dẫn chữ rỗng. Đã sửa đường đọc release trong
  `score_vilextime.py` để ghép `target`, `near_identical`, `repeal_mode` từ
  `vilextime_meta.jsonl` theo ID; không đổi công thức Accuracy hay bộ phân giải trích dẫn.
  Chạy lại đúng lệnh A7.6 (`--probes --ci 1000 --split dev|test --release ... --out
  runs/E0_final/<split>/probes.score.json`): oracle Accuracy **1,000** ở cả ba chế độ trên cả
  dev/test; `hedge` ở `giua_khoang` **0,298 dev / 0,607 test**. Sau khi trả lại metadata,
  12/307 chuỗi trích dẫn chữ riêng vẫn không phân giải (thiếu Điều hoặc nhãn nguồn khác thường);
  cần sửa metadata/citation nguồn hoặc công bố giới hạn, không nới parser chỉ để làm số đẹp.
  ADR 0005 §1 đã cập nhật số `SLICES` trên final; Status vẫn Proposed, H1/H2 chỉ là đề xuất
  chuyển sang thăm dò, chờ nhóm duyệt trước Accepted.
- 28/10, Codex B2: thêm `notebooks/colab_b2_dev.ipynb`, mở rộng `colab_b1.py` export/import
  cho `b1 b2ctx b7 b7v b7plus b7pp proposed`, `--split dev --as-of-strategy giua_khoang`,
  `--no-dense` cho thang, `--limit 0` cho toàn dev. Prompt B2 có hash, nhãn dev và sidecar
  `.export.json` chứa release SHA, corpus SHA, spec; Colab checkpoint theo hệ/model/hash trên
  Drive; import giữ signals và kiểm Verifier cho `proposed`. Xuất thử 1 dòng thật cho cả 7 hệ
  đều qua; raw giả lập của `b1` và `proposed` nhập thành 1 dòng scorer mỗi hệ, không tính là
  kết quả mô hình. Chưa chạy Colab Qwen, chưa chấm B2 và chưa chạy hệ nào trên test.
  `.venv/bin/python -m pytest -q` → **557 passed**.
- 28/10, A2/A3: CMT báo A2 hoàn tất. `~/gan_mu_root/x/gan_mu/result.tsv` có **892/892 ID riêng**, trùng đúng 892 ID trong 18 gói (0 thiếu, 0 thừa); 656 `dat`, 236 `khong_dat`. Chưa kiểm log phiên gán để xác nhận mù. Vì khóa nằm riêng ở `~/gan_mu_key/key_calib.tsv`, `agent_packs.py score` nhận thêm `--key`; `parse_intermixed_args` cho phép lệnh theo thứ tự đã ghi trong plan. Lệnh `.venv/bin/python scripts/review/agent_packs.py score --out /home/trica/gan_mu_root/x/gan_mu --key /home/trica/gan_mu_key/key_calib.tsv /home/trica/gan_mu_root/x/gan_mu/result.tsv` → hiệu chuẩn **178/178**, ID lạ **0**. Toàn tập **AC1 0,721, p_neg 0,610**; T1 `n=38, AC1=0,970, p_neg=0,800`; T2 `n=67, 0,704, 0,211`; T3 `n=23, 0,473, 0,200`; T6 `n=50, 0,681, 0,833`. **CHƯA ĐẠT** vì AC1 < 0,80. Theo A3, dừng Phần A; không đưa 714 nhãn agent vào release, không đổi ngưỡng hoặc prompt. CMT cần chọn hướng 2 hoặc 3 của `test-agent-kiem.md`. Test khóa rời: `.venv/bin/python -m pytest -q tests/test_agent_packs.py` → **2 passed**; toàn repo `.venv/bin/python -m pytest -q` → **553 passed**; `git diff --check` sạch.
- 28/10, A4 (phần code, chờ A2/A3): `export_release.py` đọc `kiem_agent.tsv` khi có, ưu tiên luật sư → A=B theo 3.0 → agent; A–agent lệch lấy `dat` theo Q2, giữ mã lý do của phía `khong_dat` trong `review.reasons` và ghi `review.labeler`. Manifest thêm `review_counts` (người, agent, số Q2). Test dữ liệu giả kiểm cả hai chiều lệch, agent đơn lẻ, luật sư và A=B: `.venv/bin/python -m pytest -q tests/test_export_release.py` → **2 passed**. Chạy `.venv/bin/python scripts/pipeline/export_release.py --out runs/a4_export_candidate` → 1.675 chính, 210 silver; manifest **1.020 người, 0 agent, 0 Q2** vì chưa có `kiem_agent.tsv`. So với bản code ở HEAD trên cùng dữ liệu, SHA256 `vilextime.jsonl` và `vilextime_silver.jsonl` trùng từng byte. `.venv/bin/python -m pytest -q` → **552 passed**; `git diff --check` sạch. Chưa ghi `kiem_agent.tsv` thật, chưa chạy `--final`; cần A2 hoàn tất và A3 đạt ngưỡng mới hoàn tất A4. Dừng ở diff trước A6.
- 28/10, B1 (phương án, chưa chạy): Groq giới hạn 8.000 TPM trong khi một request `b2ctx` đo được 18.203 token, nên lần chạy thẳng báo 413. Hai cách có thể xem xét: giảm `k` để prompt dưới giới hạn (làm đổi cấu hình phép đo), hoặc dùng batch trọng số Hugging Face trên Colab qua `scripts/eval/colab_b1.py` đã xuất được 100 prompt dev và có test import/hash ở nhật ký 27/10. Q4 hiện ghi hướng Colab; vẫn chờ CMT chốt cách chạy B1, không tự chọn generator và chưa chạy thêm B1.
- [x] A1 sửa `agent_packs.py` (178 + 714)
- [ ] A2 prompt cố định + thư mục gán mù đã chuẩn bị; 18 gói chờ phiên gán mù riêng
- [ ] A3 chấm hiệu chuẩn
- [ ] A4 `kiem_agent.tsv` + nối `export_release.py`
- [ ] A5 luật sư 50 dòng
- [ ] A6 `drop` cho `kiem`, báo cơ cấu so với sàn §9
- [ ] A7 đóng băng, datasheet, E0 lại
- [x] B0 `--as-of-strategy`
- [x] B1 chọn generator, amendment ADR 0004 (không có model độ bền)
- [x] B2 chạy thử mọi hệ trên dev, đo dao động
- [x] B3 ADR 0005 cập nhật số, Accepted, commit
- [x] B4 script bảng kết quả
- [ ] B5: B4 RRF và ngữ cảnh đúng xong trên dev; bảng nhiều LLM chờ model thứ hai (cổng Phi-3.5)
- [x] Cổng G
- [ ] C1–C11

### Nhật ký 27/10 — Codex

- A1: `calibration_verdict` giữ dòng A=B theo 3.0 và dòng lệch lô `0` có luật sư chốt;
  loại dòng lệch hòa giải 26/10 khỏi hiệu chuẩn và gói. Đưa 149 dòng lineage gold vào tập cần gán.
  `.venv/bin/python scripts/review/agent_packs.py build --out /tmp/vilextime_a1/packs`
  in `892 dòng (178 hiệu chuẩn, 714 cần gán)`, `18 gói`; khóa ở `/tmp/key_calib.tsv`,
  ngoài thư mục gói và ngoài repo. Test chọn dòng lô 0 và dòng lô sau qua.
- B0: runner nhận `--as-of-strategy`, lọc trước `--limit`, ghi giá trị trong `.run.json`;
  test chạy runner với `--retrieval-only` xác nhận file chỉ chứa dòng `giua_khoang`.
  `.venv/bin/python -m pytest -q`: **548 passed**; `git diff --check`: sạch.
- A2 chuẩn bị: `prompts/vilextime/agent_kiem.md` đã cố định từ hướng dẫn 3.0 và §7, SHA256
  `553683fc3ed8df291fa2ff08ba9e465fe591d723b1fe76926ed23dd5ded967e7`.
  `/tmp/vilextime_gan_mu/` chứa đúng 18 `pack_*.jsonl`, prompt và `AGENTS.md`: 892 dòng, 892 ID riêng,
  20 file thường, 0 symlink; không có `key_calib.tsv`. Chưa mở phiên mới để gán, chưa có `result.tsv`.
- B1: `vilexgraph.llm.list_models('groq')` trả ba model chat phù hợp: `openai/gpt-oss-20b`,
  `openai/gpt-oss-120b`, `qwen/qwen3.8-27b` (hai họ). Giá ngày 27/10 theo
  <https://console.groq.com/docs/models>, USD/1M token vào/ra: 20B `0.075/0.30`,
  120B `0.15/0.60`, Qwen `0.80/4.00`. Runner đã được bổ sung `format_ok` và token
  vào/ra cho mỗi dòng để đo cổng. Lệnh 100 dòng `dev giua_khoang`, `b2ctx`, GPT-OSS 20B
  dừng ở dòng đầu với Groq 413: giới hạn tài khoản `8.000 TPM`, request `18.203 token`.
  File dự đoán rỗng, log thất bại còn ở `runs/W1-09_generator/dev/openai/`.
  **Chưa chọn generator, chưa chạy các ứng viên còn lại, chưa soạn amendment ADR 0004.**
  CMT sau đó đổi hướng sang Colab/Hugging Face; lỗi Groq là lịch sử, không còn là blocker B1.
- B1 Colab: thêm `scripts/eval/colab_b1.py` để xuất 100 prompt không gold và nhập raw có kiểm
  hash/ID/revision; thêm `scripts/eval/colab_b1_runtime.py` để sinh greedy trên GPU 4-bit và lưu checkpoint
  trên Drive. Lệnh xuất:
  `.venv/bin/python scripts/eval/colab_b1.py export --split dev --as-of-strategy giua_khoang --limit 100 --out runs/W1-09_generator/dev/prompts.jsonl`.
  Kết quả: 100 ID riêng, 20 căn cứ/câu, 2.341.795 byte; SHA256 file
  `991eada91760159a1234ed46ba84bf4f450aaa0bb09c41124cdcaf1bb5a91182`.
  File chỉ có `id, system, user, ids, retrieved, prompt_sha256`.
  Trên Colab: chọn GPU; cài `%pip -q install -U 'transformers>=4.54,<5' accelerate bitsandbytes`;
  upload file prompt, dán/chạy code trong `colab_b1_runtime.py` cho từng `MODEL_ID`; tải JSONL raw từ
  `MyDrive/vilextime_b1/`. Nạp bằng
  `.venv/bin/python scripts/eval/colab_b1.py import --prompts runs/W1-09_generator/dev/prompts.jsonl --raw <file-tải-về>.jsonl --out runs/W1-09_generator/dev/<model>.jsonl`.
  `tests/test_colab_b1.py` kiểm nhập đúng hợp đồng scorer và từ chối hash prompt sai;
  `.venv/bin/python -m pytest -q`: **549 passed**; `git diff --check`: sạch.
  Chưa có raw của Colab nên **B1 chưa qua cổng**, chưa chọn model hay amendment ADR 0004.
- B5, B4 lai RRF: `b4` nay là BM25+dense, RRF offset 60, không reranker; `retrieve.searcher` trộn
  hai danh sách đã lọc theo cùng lớp/mốc/k và giữ tín hiệu `lexical_rrf`/`dense_rrf` riêng. Hệ cần
  reranker khác vẫn báo chưa triển khai. Test thứ hạng, giới hạn k và tích hợp B4 với dense giả:
  `.venv/bin/python -m pytest -q tests/test_rag_retrieve.py tests/test_rag_systems.py` → **33 passed**.
  Lượt thật `b4 --retrieval-only --split dev --as-of-strategy giua_khoang --limit 1 --embed
  data/derived/embed/asis-vietnamese-embedding --out /tmp/b4_rrf_dev.jsonl` → 1 dòng, 20 hit,
  cả hai tín hiệu RRF, `rerank=false`, 0 lỗi; 164,6 giây cho truy vấn đầu khi pytest chạy song song.
  Đã chạy lại toàn repo: **551 passed**. Chạy tiếp dòng dev thứ hai cùng cấu hình, không có pytest
  đồng thời: 1 dòng mới, 0 lỗi trong **192,5 giây**. Đây là thời gian truy xuất quá chậm để tự nhận
  sẽ chạy đủ bảng B4 trên test đúng lịch; cần tối ưu dense không đổi định nghĩa phép đo hoặc CMT
  quyết định lịch/tài nguyên trước C2. Không giảm k, không dùng `--fast-retrieval` để báo số.

### Nhật ký 28/10 — Claude (A4–A7 theo phạm vi T1+T6)

- CMT chọn phạm vi: nhãn agent chỉ T1 và T6 (định nghĩa mục 6 và hướng dẫn mục 6 đã sửa); trên test một người không đủ; T2, T3, T5 chưa đủ người kiểm vào silver; Q2 giữ nguyên.
- `data/review/kiem_agent.tsv`: 325 dòng T1, T6 (labeler `Codex gpt-6-sol`); 389 dòng T2, T3, T5 ở `kiem_agent_ngoai_pham_vi.tsv`, không dùng. Hiệu chuẩn 178 dòng bị loại khỏi hai file.
- `export_release.py`: `AGENT_GROUPS`, `OUT_OF_SCOPE`; `final_labels(review, scope)`; `--final` chỉ từ chối khi còn dòng chưa kiểm ngoài các dòng ngoài phạm vi. Test mới trong `tests/test_export_release.py`; `pytest` toàn repo 555 qua.
- `export_release.py --final` đã ghi `data/vilextime_dataset/`: `final: true`, 1.013 dòng chính, 859 silver. Test ranh giới trong file chính: T1 123, T2 46, T3 12, T6 152, T5 0 (333 dòng). Nguồn: người 98 (A+B 88, luật sư 10), agent 235 (78 trong số đó lấy `dat` của A theo Q2).
- Q2 ghi đè: 85 dòng ranh giới A `dat` / agent `khong_dat` thành `dat`, trên 132 nhãn `khong_dat` của agent ở T1, T6.
- A5: `scripts/review/agent_sample.py` → `data/review/luat_su_kiem_agent.xlsx` (50 dòng, seed `luat-su-agent-2710`, không hiện nhãn A). Chờ luật sư điền.
- E0 trên bản final (`runs/E0_final/{dev,test}/probes.score.json`): oracle Accuracy 0,993 (dev), 0,982 (test), không phải 1,000; scorer báo 1 trích dẫn chữ không phân giải. **Việc cho Codex: tìm các dòng oracle chưa đủ trần và giải thích trước khi ADR 0005 Accepted.**
- Chưa làm: luật sư điền 50 dòng; tag `vilextime-v1.0` (CMT); gold độc lập; B3 (ADR 0005 cập nhật số: test chính còn 333 dòng, lát T2/T3 rất nhỏ, đếm lại bằng `SLICES` của `confirm_vilextime.py`).

## Decisions

- 2026-10-27: hàng việc chốt dữ liệu và thực nghiệm gộp vào file này; plan cũ giữ lý do (Claude, theo yêu cầu CMT).
- 2026-10-27 (CMT): Q1 Codex gán 714 dòng (sửa định nghĩa §6, hướng dẫn §6); Q2 A–agent lệch thì lấy `dat`;
  Q3 149 dòng lineage gold giao agent; Q4 chỉ LLM trên Groq; Q5 duyệt cả ba bổ sung. Hệ quả của Q2: nhãn
  `khong_dat` của agent bị nhãn nhanh của A (~5 giây/dòng, 92,5% `dat`) ghi đè, nên datasheet phải báo số
  dòng bị ghi đè.
- 2026-10-27 (CMT, sau lỗi Groq): Q4 đổi sang Google Colab chạy model nhẹ Hugging Face không thinking;
  B1 giữ nguyên 100 dòng dev, `b2ctx` và cổng định dạng/cắt cụt. Hai ứng viên khác họ là Qwen3 4B Instruct
  2507 và Phi 3.5 mini; chưa chốt generator cho tới khi có số đo.

## Validation

- Focused proof: test mới ở A1, A4, B0; `agent_packs.py score`; probe E0 trên bản final.
- Integration: `export_release.py --final` OK; `run_vilextime.py` → `score_vilextime.py` →
  `confirm_vilextime.py` chạy trọn trên dev rồi test.
- Repository-required checks: `.venv/bin/python -m pytest -q`.

## Result

(Điền khi xong.)
