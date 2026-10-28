# Execution Plan: Thực nghiệm trên ViLexTime (mô hình, baseline, LLM, lịch chạy)

Date: 2026-10-21

## Status

Từ 27/10 việc còn lại theo dõi ở [`codex-chot-du-lieu-va-thuc-nghiem.md`](codex-chot-du-lieu-va-thuc-nghiem.md) (Phần B, C).

Active. Bản nháp do Claude soạn ngày 21/10 theo yêu cầu của CMT; CMT bổ sung. Chưa có quyết định mới nào
trong file này được duyệt: những chỗ ghi **[đề xuất]** chờ nhóm chốt.

## Outcome

Mọi hệ chạy end-to-end trên `test` của bản ViLexTime final, mỗi cấu hình một lần, sau khi ADR 0005
được Accepted; RQ1–RQ3 và H0–H4 có số kèm khoảng tin cậy; bảng kết quả, sổ chạy `runs/` và lệnh tái
lập đủ để viết khóa luận và bài báo.

## Context

- Đề cương: `docs/DeCuongKLTN_23521635_23521643_UIT.docx` (nội dung 5–6: phương pháp so sánh, thực nghiệm).
- Thiết kế đã chốt 11/10: `MASTER_RESEARCH_GUIDE.md` §2.3–2.4 (RQ, giả thuyết), §7 (baseline, chọn LLM),
  §8 (E0–E8, thống kê), §9 (chỉ số).
- [ADR 0004](../../decisions/0004-framework-truy-xuat-va-sinh.md): thang biểu diễn, BM25 FTS5, generator
  không thuộc họ Claude/DeepSeek, dense PhoBERT (amendment 19/10).
- [ADR 0005](../../decisions/0005-ke-hoach-phan-tich.md) (Proposed): đại lượng chính, XN1–XN9, Holm,
  bootstrap theo lineage. **Số liệu trong đó là của bản 11/10, phải cập nhật.**
- Code: `src/vilexgraph/framework/systems.py` (REGISTRY, LADDER), `scripts/eval/run_vilextime.py`,
  `score_vilextime.py` (`--release`, `--ci`, `--probes`), `confirm_vilextime.py`, `judge_vilextime.py`.
- Dữ liệu: `data/vilextime_dataset/vilextime.jsonl` (bản công bố, `docs/vilextime-schema-phat-hanh.md`);
  bản final chỉ có sau khi kiểm nhãn xong (`docs/plans/active/vilextime-dinh-nghia-chot.md`).
- Sổ chạy hiện có: `runs/README.md` (E0, E1 dev ngày 11/10 trên corpus cũ; W2-12 dense dev 19–20/10).

## Scope

In scope:

- E0–E7 trên dev rồi test; chọn generator; ba bổ sung chuẩn paper ở mục "Bổ sung" (nếu nhóm đồng ý).

Out of scope:

- Fine-tune; sửa scorer; thêm nhóm câu hỏi; chạy test trước khi ADR 0005 Accepted.

## Approach

### 1. Các hệ

Mọi baseline là hệ đề xuất bị tắt một phần, cùng bộ truy xuất, cùng LLM, cùng prompt, cùng `k = 20`.

| Mã | Là gì | Nhóm trong đề cương | Trạng thái code |
|---|---|---|---|
| `b1` | Chỉ LLM, không truy xuất | LLM không truy xuất | có |
| `b2`, `b2ctx` | BM25 lớp A, không / có tiêu đề cấu trúc | RAG phẳng | có |
| `b3` | Dense (`dangvantuan/vietnamese-embedding`) | RAG phẳng | có; dev: R@1 0,253 so với `b2ctx` 0,409 |
| `b4` | Lai BM25 + dense + reranker | RAG phẳng | **chưa có**: `retrieve.searcher` báo NotImplemented cho trộn và reranker |
| `b5`, `b6` | Mở rộng 1 bước, không thời gian: cạnh sửa đổi / cạnh cha–con | GraphRAG phi thời gian, KG phân cấp | có, chạy `--no-dense` |
| `b7` | Lọc theo ngày hiệu lực cấp văn bản (đối chứng chính) | Lọc siêu dữ liệu | có |
| `b7v`, `b7plus`, `b7pp` | Lời văn theo phiên bản → khoảng phiên bản → khoảng lan truyền | Nấc của hệ đề xuất | có |
| `proposed` | `b7pp` + mở rộng 1 bước + Verifier `reject` | Hệ đề xuất | có |
| `a1`–`a4` | Bỏ ràng buộc thời gian / mở rộng / Verifier / lan truyền | Ablation | có |
| LightRAG | GraphRAG thật trên tập con văn bản (C3) | GraphRAG phi thời gian | chưa làm |

Thang chính (RQ3): `b2ctx → b7 → b7v → b7plus → b7pp`, truy xuất từ vựng (`--no-dense`), hai nấc kề nhau
khác đúng một trường.

### 2. LLM

| Vai trò | Cách chọn | Ghi chú |
|---|---|---|
| Generator chính | 100 dòng dev `giua_khoang`, nhiệt độ 0; cổng: đúng định dạng ≥ 95%, không cắt cụt, người đọc 20 câu; chọn model rẻ nhất qua cổng (MASTER_RESEARCH_GUIDE §7.5) | Không thuộc họ Claude, DeepSeek (ADR 0004 §3) |
| Kiểm độ bền | Model rẻ nhất qua cổng, khác họ | Chạy `b2ctx`, `b7`, `proposed` |
| Bảng phụ | Claude, DeepSeek | Tách theo `question_source` |
| Giám khảo LLM | Cột phụ, hiệu chuẩn 100 mẫu người (`judge_vilextime.py`) | Sau 31/10 (C4) |

Ứng viên generator, giá OpenRouter tải 21/10/2026, USD / 1 triệu token vào / ra (ghi lại giá vào ngày chọn):
`openai/gpt-oss-120b` 0,03 / 0,14 (batch; nhóm có khóa Groq) · `qwen/qwen3.7-flash` 0,03 / 0,13 ·
`mistralai/mistral-small-2603` 0,075 / 0,30 (batch) · `openai/gpt-6-luna` 0,10 / 0,50 ·
`google/gemini-3.1-flash-lite` 0,25 / 1,50.

Chi phí ước: khoảng 15 hệ × 914 dòng ≈ 14.000 lệnh gọi × khoảng 4.800 token (ước 11/10: 4.500 vào, 300 ra;
đo lại trên dev). Với model rẻ: vài USD đến khoảng 15 USD cho cả đợt.

### 3. Dữ liệu và lát (đếm 21/10 trên bản chưa kiểm xong; số cuối sẽ nhỏ hơn)

| Lát (test, `giua_khoang`) | Dòng | Lineage | Dùng cho |
|---|---:|---:|---|
| all = T1, T2, T3, T6 | 914 | 501 | Bảng chính |
| all, có đáp án | 767 | 501 | XN1, XN3, XN4 |
| T2 gần giống / T2 thường | 132 / 236 | 66 / 118 | H1 (XN6) |
| T6 bãi bỏ qua nút cha, không đáp án | 104 | 104 | H3 (XN5) |
| T6 bãi bỏ trực tiếp | 86 | 43 | Mô tả |
| T2 ∪ T3 | 490 | 224 | H2 (XN7) |
| T5 | 20 | 10 | Chỉ mô tả |

`ranh_gioi` (934) và `truoc_hieu_luc` (116) của test: chỉ truy xuất, chỉ mô tả (C2). Dev: 399 dòng
(186 `giua_khoang`, 158 có đáp án).

### 4. Thí nghiệm

| Mã | Mục đích | Hệ | Chi phí | Ưu tiên |
|---|---|---|---|---|
| E0 | Kiểm công cụ: oracle đạt trần, câu rào đón bị phạt; tier `propagated` khớp `ValidityService` | probe | 0 | P0, chạy lại trên bản mới |
| E1 | Thang chỉ truy xuất (RQ3, H0) | 5 nấc | 0 lệnh gọi LLM | P0 |
| E2 | LLM và RAG phẳng sai phiên bản bao nhiêu (RQ1, H1) | `b1`, `b2ctx`, `b3` | LLM | P0 |
| E3 | Thang có sinh câu trả lời (RQ2, RQ3, H2) | E1 + `proposed` | LLM | P0 |
| E4 | Đồ thị phi thời gian (RQ2) | `b5`, `b6`; LightRAG trên tập con | LLM | P1 |
| E5 | Ablation (H3) | `a1`–`a4` | LLM | `a4` P0, còn lại P1 |
| E6 | Kiểm lại trên gold độc lập | thang + baseline chính | thấp | P0 nếu có gold |
| E7 | Phân tích lỗi theo mã lỗi (MASTER_RESEARCH_GUIDE §9.4) | `proposed`, `b7`, `b2ctx`, `b1` | giờ người | P0 |
| E8 | Độ nhạy: `k`, chế độ `as_of`, model khác, theo miền | | tùy | Sau 31/10 |

Thống kê theo ADR 0005: đơn vị phân tích là lineage; bootstrap theo lineage B = 10.000, ghép cặp khi so
hai hệ; XN1–XN9 với Holm α = 0,05; luôn báo độ lớn hiệu ứng kèm khoảng tin cậy và số dòng, số lineage.

### 5. Bổ sung để đạt chuẩn paper [đề xuất]

1. **Dòng ngữ cảnh đúng (oracle context):** LLM nhận đúng đoạn luật có hiệu lực tại mốc; tách lỗi truy
   xuất khỏi lỗi đọc hiểu (bộ ba: không truy xuất / RAG / ngữ cảnh đúng). Runner bị khóa không thấy gold,
   nên làm script riêng, ghi rõ là cận trên, không vào họ kiểm định. Ước 1 giờ.
2. **Bảng nhiều LLM (mô tả):** `b1`, `b2ctx`, `proposed` trên 4–5 model: generator chính, model độ bền,
   một model mạnh đóng (ví dụ `openai/gpt-6.1-sol`, 2 / 10 USD), một model mạnh mở (Qwen 3.8, GLM-5.3).
   Khoảng 35 USD cho mỗi model mạnh.
3. **B4 lai đơn giản:** BM25 + dense trộn thứ hạng RRF, không reranker; ghi rõ là bỏ reranker. Ước 1–2 giờ.

LightRAG (E4) tốn nhất; không kịp trước 31/10 thì ghi vào phần giới hạn.

### 6. Lịch

| Ngày | Việc |
|---|---|
| 21–25/10 (song song gán nhãn) | E0, E1 trên dev với bản mới; chọn generator; chạy thử sinh trên dev mọi hệ; chạy lặp 2 lần đo dao động; `confirm_vilextime.py` trên dev; bổ sung ở mục 5 nếu được duyệt |
| ~26/10 | Đóng băng (`export_release.py --final`, tag, manifest); cập nhật số trong ADR 0005; nhóm duyệt → Accepted → commit |
| 27–29/10 | Test: E1 → E2, E3, E5 → E4 (`b5`, `b6`) → model độ bền, bảng nhiều LLM → E6 → XN1–XN9 |
| 30–31/10 | Bảng kết quả; bắt đầu E7 |
| Sau 31/10 | E7, E8, giám khảo LLM, LightRAG nếu còn |

### 7. Lệnh

```bash
# dev, chỉ truy xuất (E1)
for s in b2ctx b7 b7v b7plus b7pp; do
  python scripts/eval/run_vilextime.py --system $s --no-dense --retrieval-only --split dev \
      --release data/vilextime_dataset/vilextime.jsonl --out runs/E1_ladder/dev/$s.jsonl
done
python scripts/eval/score_vilextime.py runs/E1_ladder/dev/{b2ctx,b7,b7v,b7plus,b7pp}.jsonl --split dev \
    --release data/vilextime_dataset/vilextime.jsonl --ci 2000 --out runs/E1_ladder/dev/ladder.score.json
```

`run_vilextime.py` chỉ đọc `id`, `question`, `as_of`, `split` nên đọc được file công bố (đã đọc code, chưa
chạy thử trên file này); `score_vilextime.py --release` đã đối chiếu: trùng báo cáo nội bộ 2.383/2.383 dòng.

## Risks And Recovery

- Lịch sát: test chỉ chạy được khi kiểm nhãn xong và ADR 0005 Accepted. Mọi việc dev làm trước.
- Gold do đồ thị suy ra và bộ lọc tier cùng nguồn `versions.jsonl`: ưu thế của nấc 3–4 là cận trên
  (MASTER_RESEARCH_GUIDE §7.4, K-08); cần cột gold độc lập (E6).
- Hiệu ứng nhỏ của mở rộng đồ thị và Verifier: báo đúng mức, không thổi phồng (§7.6).
- Thiên lệch người viết câu hỏi: cột chính không dùng Claude/DeepSeek.
- Chạy hỏng giữa chừng: runner chạy tiếp được (`--out` giữ dòng đã có), cache truy xuất và lời gọi LLM ở
  `data/derived/rag/*.sqlite`.

## Progress

- [x] Soạn kế hoạch (21/10, Claude).
- [ ] CMT bổ sung, nhóm duyệt các mục [đề xuất].
- [ ] Khóa API cho cổng chọn generator (`.env` hiện chỉ có Groq, DeepSeek).
- [ ] E0, E1 dev trên bản mới.
- [ ] Chọn generator, ghi amendment ADR 0004.
- [ ] Cập nhật ADR 0005 theo bản final; Accepted; commit.
- [ ] Chạy test E1–E6; XN1–XN9.
- [ ] E7.

## Decisions

- (chưa có)

## Validation

- Focused proof: probe E0 đạt trần; `assert_monotone`; test `tests/test_rag_*.py`.
- Integration: `run_vilextime.py` → `score_vilextime.py` trên dev cho mọi hệ.
- Repository-required checks: `python -m pytest`.

## Result

(Điền khi xong.)
