# Master Plan — Khóa luận Temporal-Aware KG RAG

Date: 2026-09-14 · Cập nhật gần nhất: 2026-09-17

> **Nguồn sự thật về tiến độ dự án.** Timeline bám theo mục "Kế hoạch thực hiện"
> trong `DeCuongKLTN_23521635_23521643.docx` (01/09/2026 – 01/02/2027).
> Mọi tài liệu kế hoạch khác chỉ còn giá trị lịch sử.

## Status

Active. Hiện ở cuối Giai đoạn 1; Giai đoạn 2–3 đang đi trước kế hoạch.

## Cách đọc và cập nhật file này

- Ký hiệu trạng thái: ✅ xong · 🟡 đang làm / làm dở · ⬜ chưa bắt đầu · ⛔ bị chặn.
- **Chỉ đổi trạng thái khi có bằng chứng**: file, commit, lệnh chạy được hoặc số
  đo. Viết bằng chứng vào cột "Bằng chứng / tiêu chí xong".
- Mỗi lần đổi trạng thái: cập nhật bảng Tổng quan và thêm một dòng vào Nhật ký.
- Quyết định lâu dài ghi vào `docs/decisions/`; ở đây chỉ đặt link.
- Phụ trách theo đề cương: **CMT** = Cao Minh Trí · **NMT** = Nguyễn Minh Trí.

---

## 1. Tổng quan

| GĐ | Thời gian | Nội dung | Trạng thái | Việc xong | So với kế hoạch |
|---|---|---|---|---:|---|
| 1 | 01/09 – 14/09 | Hoàn thiện đề cương | 🟡 | 2/6 | Đến hạn hôm nay |
| 2 | 15/09 – 05/10 | Thu thập & xử lý dữ liệu | ✅ | 12/12 | Backfill v2 xong, snapshot đóng băng trước M1 |
| 3 | 06/10 – 26/10 | Xây dựng đồ thị tri thức (L0–L3) | 🟡 | 4/19 | Bắt đầu sớm; **đường găng** |
| 4 | 27/10 – 16/11 | Bộ dữ liệu ViLexTime | ⬜ | 0/9 | — |
| 5 | 17/11 – 30/11 | Cài đặt & đánh giá đường cơ sở | ⬜ | 0/14 | — |
| 6 | 01/12 – 21/12 | Hệ thống đề xuất (L4–L5) | ⬜ | 0/7 | — |
| 7 | 22/12 – 04/01 | Thực nghiệm & phân tích | ⬜ | 0/5 | — |
| 8 | 05/01 – 11/01 | Viết bài báo khoa học | ⬜ | 0/3 | — |
| 9 | 12/01 – 01/02 | Hoàn thiện khóa luận | ⬜ | 0/5 | — |
| | | **Tổng** | | **18/80** | |

### Mốc kiểm tra

| Mốc | Hạn | Điều phải chứng minh được | Trạng thái |
|---|---|---|---|
| M1 | 05/10 | **Snapshot v2** đóng băng sau backfill, tải về kiểm tra được ([plan](../completed/2026-09-17-backfill-corpus-v2.md)) | ✅ (17/09, trước hạn) |
| M2 | 26/10 | Chuỗi phiên bản thật trong Neo4j; `snapshot(u,t)` đúng trên 100 truy vấn đối chiếu tay | ⬜ |
| M3 | 16/11 | ViLexTime đủ 1.150 câu; Cohen κ ≥ 0,6 trên 300 câu | ⬜ |
| M4 | 30/11 | **Điểm quyết định B7**: chọn hướng đóng góp phương pháp hay tài nguyên–phân tích | ⬜ |
| M5 | 21/12 | Hệ thống end-to-end trả lời (x, t) kèm trích dẫn đã qua Verifier | ⬜ |
| M6 | 04/01 | Đủ kết quả A1–A7, phân rã theo T1–T6 | ⬜ |
| M7 | 11/01 | Nộp bài báo | ⬜ |
| M8 | 01/02 | Nộp khóa luận, demo chạy được | ⬜ |

### Đường găng

Mọi việc phía sau đều phụ thuộc vào việc có **chuỗi phiên bản thật**:

```text
P3.1 hạ tầng Docker ─► P3.4 loader Neo4j ─► P3.9 lưu event ─► P3.10/P3.11 event L2
      ─► P3.15 áp event lên dữ liệu thật ─► P3.18 kiểm chứng 100 snapshot   (M2)
      ─► P4.2 so khớp phiên bản ─► ViLexTime (M3) ─► baseline + B7 (M4)
      ─► L4/L5 (M5) ─► ablation (M6)
```

Hiện chỉ lõi logic L3 (`src/legal_crawler/temporal/`) đã xong, và mới chạy trên
fixture tự tạo. Trên dữ liệu thật, mỗi nút chỉ có 1 phiên bản mang khoảng hiệu
lực của cả văn bản (`src/legal_crawler/ingest.py`), tức mới tương đương B7.

---

## 2. Giai đoạn 1 — Hoàn thiện đề cương (01/09 – 14/09)

| ID | Việc | Phụ trách | Trạng thái | Bằng chứng / tiêu chí xong |
|---|---|---|---|---|
| P1.1 | Rà soát phạm vi, RQ1–RQ3, giả thuyết | CMT, NMT | ✅ | `DeCuongKLTN_23521635_23521643.docx` (4 miền, khoảng 8.700 VB) |
| P1.2 | Sửa mâu thuẫn trong đề cương (xem §12) | CMT, NMT | ⬜ | Không còn mục nào ở §12 |
| P1.3 | Khảo sát RAG, GraphRAG, LightRAG, RAPTOR, IRCoT | CMT | 🟡 | Nháp `docs/graph_justification.md` §5; còn trích dẫn chưa kiểm |
| P1.4 | Khảo sát temporal RAG và Legal NLP tiếng Việt | NMT | 🟡 | Nháp như trên; cần đối chiếu SAT-Graph RAG, VersionRAG với bài gốc |
| P1.5 | Thống nhất giả thuyết H1–H4 và ký hiệu công thức với chương Phương pháp | CMT, NMT | ⬜ | H1–H4 được đưa vào đề cương hoặc bị loại có ghi lý do |
| P1.6 | Chốt tech stack | CMT, NMT | ✅ | `docs/decisions/0001-neo4j-milvus-la-kho-dan-xuat.md` |

## 3. Giai đoạn 2 — Thu thập & xử lý dữ liệu (15/09 – 05/10)

| ID | Việc | Phụ trách | Trạng thái | Bằng chứng / tiêu chí xong |
|---|---|---|---|---|
| P2.1 | Crawl vbpl.vn 4 miền, lưu bản gốc | CMT | ✅ | 22.550 file `data/raw/`; `scripts/check/verify_pipeline.py` pass |
| P2.2 | Ghi rõ nguồn và phương pháp thu thập | CMT | ✅ | `docs/crawling-plan.md`, `README.md` |
| P2.3 | Bảng mã quan hệ và trạng thái hiệu lực đã kiểm chứng | CMT | ✅ | `data/reference_type_map.json`, `data/eff_status_map.json` |
| P2.4 | Cây Chương/Mục/Điều/Khoản/Điểm | NMT | ✅ | `data/trees/` phủ 99,9% |
| P2.5 | Gắn nội dung chữ vào từng nút | NMT | ✅ | `data/provisions/` phủ 98,97% nút khớp được; 778 VB trong hàng đợi review |
| P2.6 | Delta crawl và mốc "as of" | CMT | ✅ | `scripts/pipeline/delta_crawl.py`, `data/delta_runs.jsonl` |
| P2.7 | Sao lưu snapshot ra ngoài máy | CMT | ✅ | 14/09: `pull_snapshot.sh` tải v1 từ HF, sha256 OK, `verify_pipeline.py` pass trên bản tải về (backfill T0.1) |
| P2.8 | Quy tắc phạm vi QPPL và cờ `temporal_anchor` | CMT, NMT | ✅ | 14/09: `vocab/scope.py` + `build_eligibility.py`; 20.318 QPPL trung ương, 16.993 đủ điều kiện benchmark; hàng đợi điền tay 308 (backfill T2) |
| P2.9 | Sửa gốc pipeline; backfill 1.017 diagram; 19 VB không sinh cạnh | CMT | ✅ | 17/09: closure hội tụ, 0 genealogy target chưa tải, `edges.jsonl` hàm thuần của `data/raw` (backfill T1, T3.1) |
| P2.10 | Candidate thời gian cấp văn bản: `effTo` từ văn bản bãi bỏ duy nhất, `issueDate` làm cận dưới | CMT, NMT | ✅ | 17/09: 381/388 candidate quyết định (367 accept, 14 reject) qua đối chiếu văn bản gốc, không chỉ tin referenceType (backfill T4) |
| P2.11 | Tách Khoản/Điểm từ HTML của Điều | NMT | ✅ | 17/09: 424.409 node + 10.302 preamble; 100/100 mẫu kiểm tay đúng, vượt ngưỡng 95% (backfill T5) |
| P2.12 | Đóng băng snapshot v2 (M1) | CMT | ✅ | 17/09: đẩy HF (`7d8ab0c`), tải về thư mục khác kiểm chứng `verify_pipeline.py` pass (backfill T3.3) |

Chi tiết thực hiện P2.7–P2.12: [`2026-09-17-backfill-corpus-v2.md`](../completed/2026-09-17-backfill-corpus-v2.md).

## 4. Giai đoạn 3 — Xây dựng đồ thị tri thức L0–L3 (06/10 – 26/10)

Đề cương phân công: CMT làm L0–L2, NMT làm L3 và kiểm chứng snapshot.

### 3A. Hạ tầng (phát sinh từ ADR 0001)

| ID | Việc | Phụ trách | Trạng thái | Bằng chứng / tiêu chí xong |
|---|---|---|---|---|
| P3.1 | `docker-compose` cho Neo4j và Milvus có giới hạn RAM; runbook bật/tắt | CMT | ⬜ | Hai dịch vụ healthy; runbook theo `docs/templates/application-runbook.md` |
| P3.2 | Đo RAM thực tế khi nạp đủ corpus | CMT | ⬜ | Số đo được ghi lại; chốt có phải tắt `legal-rag-api` hay không |

### 3B. L0–L1: cấu trúc và cạnh metadata

| ID | Việc | Phụ trách | Trạng thái | Bằng chứng / tiêu chí xong |
|---|---|---|---|---|
| P3.3 | Domain model và ID tất định | NMT | ✅ | `temporal/models.py`, `temporal/ids.py`; test pass |
| P3.4 | Loader `data/` → Neo4j: Document, Provision, `CONTAINS`, Version | CMT | ⬜ | Tái dùng `ingest.py`; chạy lại không tạo nút trùng; số nút khớp `data/` |
| P3.5 | Nạp cạnh giữa văn bản thành quan hệ có kiểu (khử trùng lặp 157.795 → 128.289) | CMT | ⬜ | Đếm theo 13 loại khớp `data/representation_benchmark.json` M1 |
| P3.6 | Chuyển `target_resolver` và `resolve_expiry_targets.py` sang Neo4j; bỏ index SQLite | CMT | ⬜ | Tỷ lệ resolve vẫn là 73,3%; xóa được `index.py`, `build_store.py` |

### 3C. L2: trích xuất thao tác sửa đổi

| ID | Việc | Phụ trách | Trạng thái | Bằng chứng / tiêu chí xong |
|---|---|---|---|---|
| P3.7 | Khuôn dữ liệu trích xuất | CMT | ✅ | `extraction/models.py`; test pass |
| P3.8 | Target resolver ("Khoản 1, Điều 3" → id nút) | CMT | ✅ | `extraction/target_resolver.py`; 22.847/31.175 chuỗi expiry map được. Chưa kiểm tiêu đề bất thường |
| P3.9 | Định dạng lưu event đã duyệt trong `data/` | CMT, NMT | ⬜ | Hệ quả ADR 0001; dựng lại Neo4j từ file cho ra cùng kết quả |
| P3.10 | Event BÃI BỎ từ 228 VB chỉ có một văn bản tác động (843 bộ ba) | CMT | ⬜ | 843 event `VERIFIED` có provenance |
| P3.11 | Bộ trích xuất regex: SỬA ĐỔI / BỔ SUNG / BÃI BỎ / THAY THẾ | CMT | ⬜ | Chạy trên văn bản tác động; ca không chắc chắn vào `NEEDS_REVIEW` |
| P3.12 | LLM cho ca phức tạp | CMT | ⬜ | Chỉ gọi khi regex bó tay; ghi `method=LLM` |
| P3.13 | Đo độ chính xác L2 | CMT, NMT | ⬜ | Trên 843 mẫu gold và 200 mẫu kiểm tay; số liệu có trong khóa luận |

### 3D. L3: hợp nhất phiên bản và lan truyền hiệu lực

| ID | Việc | Phụ trách | Trạng thái | Bằng chứng / tiêu chí xong |
|---|---|---|---|---|
| P3.14 | Logic version chain, event applier, validity, snapshot | NMT | ✅ | `temporal/`; test pass (fixture tự tạo) |
| P3.15 | Áp event lên dữ liệu thật → chuỗi phiên bản trong Neo4j | NMT | ⬜ | Có đơn vị với 2 phiên bản trở lên, `created_by_event_id` khác rỗng |
| P3.16 | Tính trước khoảng hiệu lực thực của mỗi phiên bản (cách A) | NMT | ⬜ | Khớp `ValidityService` trên mẫu ngẫu nhiên |
| P3.17 | Hợp nhất định nghĩa "có hiệu lực tại t" | NMT | ⬜ | Chỉ còn một đường tính; `index.version_at` bị bỏ |
| P3.18 | Kiểm chứng snapshot trên 100 truy vấn đối chiếu tay | NMT | ⬜ | Bảng 100 truy vấn, kết quả, người kiểm |
| P3.19 | Giải dẫn chiếu chéo có nhận biết thời gian | NMT | ⬜ | "khoản 2 Điều 5 của Luật này" → đúng phiên bản tại t |

**Tiêu chí xong Giai đoạn 3:**
- ID ổn định, khoảng `[start, end)` dùng nhất quán.
- Bốn thao tác chạy được ở cấp Điều/Khoản/Điểm; bãi bỏ nút cha vô hiệu đúng cây con.
- Event chưa chắc chắn không bị áp âm thầm; có thống kê coverage và hàng đợi review.
- Chuỗi A → B → C có test; P3.18 đạt; chạy lại không tạo phiên bản hay cạnh trùng.

## 5. Giai đoạn 4 — Bộ dữ liệu ViLexTime (27/10 – 16/11)

Đề cương phân công: NMT chủ trì quy trình diff-driven; CMT kiểm định chéo và làm việc với cố vấn luật.

| ID | Việc | Phụ trách | Trạng thái | Bằng chứng / tiêu chí xong |
|---|---|---|---|---|
| P4.1 | Hướng dẫn gán nhãn; thống nhất định nghĩa T1–T6 | NMT | ⬜ | Tài liệu hướng dẫn; hết mâu thuẫn T6/T7 |
| P4.2 | So khớp phiên bản: cặp `snapshot(u,t₁) ≠ snapshot(u,t₂)` | NMT | ⬜ | Cần P3.15 |
| P4.3 | Trích khác biệt thành bộ ba (trước, sau, mốc chuyển) | NMT | ⬜ | Mỗi bộ ba truy ngược được về nút và event |
| P4.4 | Sinh câu hỏi bằng LLM (chỉ để diễn đạt) | NMT | ⬜ | Nhãn vàng không phụ thuộc LLM |
| P4.5 | Đủ số lượng: T1 250 · T2 400 · T3 200 · T4 150 · T5 50 · T6 100 | NMT | ⬜ | Tổng 1.150 |
| P4.6 | Loại VB không neo thời gian khỏi benchmark | NMT | ⬜ | Cần P2.8 |
| P4.7 | Kiểm định chéo 300 câu, Cohen κ | CMT | ⬜ | κ ≥ 0,6; nếu thấp hơn thì viết lại hướng dẫn và kiểm lại |
| P4.8 | Cố vấn chuyên môn luật cho T5, T6 | CMT | ⬜ | Có người kiểm và biên bản |
| P4.9 | Chia tập dev/test | NMT | ⬜ | λ, μ chỉ tinh chỉnh trên dev |

## 6. Giai đoạn 5 — Cài đặt & đánh giá đường cơ sở (17/11 – 30/11)

Đề cương phân công: CMT làm B1–B4; NMT làm B5–B7 và tổng hợp điểm quyết định.

| ID | Việc | Phụ trách | Trạng thái | Bằng chứng / tiêu chí xong |
|---|---|---|---|---|
| P5.1 | Chốt LLM sinh và embedding model | CMT, NMT | ⬜ | Ghi thành decision |
| P5.2 | Collection Milvus theo phiên bản: vector, `eff_from`/`eff_to` thực, level, doc | CMT | ⬜ | Kiểm chứng analyzer BM25 tiếng Việt trước |
| P5.3 | Embedding khoảng 1,14 triệu nút có text | CMT | ⬜ | ⚠ CPU có thể mất nhiều ngày; ghi thời gian thực tế |
| P5.4 | Chỉ số Recall@k, MRR, TV-Recall@k, Accuracy, EM/F1 | NMT | ⬜ | Có unit test |
| P5.5 | Chỉ số TVER, VCR, TCS (công thức 6–8) | NMT | ⬜ | Có unit test trên ví dụ tay |
| P5.6 | LLM-as-judge hiệu chuẩn trên 100 mẫu | NMT | ⬜ | Báo cáo độ đồng thuận với người chấm |
| P5.7 | B1 — LLM không truy xuất | CMT | ⬜ | |
| P5.8 | B2 — BM25 + sinh | CMT | ⬜ | |
| P5.9 | B3 — Dense + sinh | CMT | ⬜ | |
| P5.10 | B4 — Hybrid + reranker | CMT | ⬜ | |
| P5.11 | B5 — GraphRAG phi thời gian (LightRAG) | NMT | ⬜ | |
| P5.12 | B6 — KG phân cấp cho pháp luật Việt Nam | NMT | ⬜ | Tái hiện theo tài liệu [10], [11] của đề cương |
| P5.13 | B7 — lọc metadata cấp văn bản, không dùng đồ thị | NMT | ⬜ | Làm sớm nhất có thể |
| P5.14 | 🚩 Điểm quyết định B7 (M4) | CMT, NMT | ⬜ | Nếu B7 gần mức trần thì đánh giá lại L2–L4 |

## 7. Giai đoạn 6 — Hệ thống đề xuất L4–L5 (01/12 – 21/12)

Đề cương phân công: CMT làm L4; NMT làm L5.

| ID | Việc | Phụ trách | Trạng thái | Bằng chứng / tiêu chí xong |
|---|---|---|---|---|
| P6.1 | Lọc 𝒰ₜ (công thức 4): Milvus lọc, Neo4j xác nhận top-k | CMT | ⬜ | Không trả bằng chứng mất hiệu lực trên tập dev |
| P6.2 | Chấm điểm lai (công thức 5): từ vựng + ngữ nghĩa + láng giềng AMENDS/REFERS_TO | CMT | ⬜ | Lưu riêng từng tín hiệu để làm ablation |
| P6.3 | Tinh chỉnh số bước mở rộng, λ, μ trên dev | CMT | ⬜ | |
| P6.4 | Sinh câu trả lời ràng buộc trích dẫn Điều/Khoản/Điểm | NMT | ⬜ | |
| P6.5 | Tác tử suy luận mốc thời gian | NMT | ⬜ | |
| P6.6 | Temporal Verifier | NMT | ⬜ | Loại bỏ hoặc cảnh báo trích dẫn không hợp lệ tại t |
| P6.7 | Giao diện chọn mốc t, xem đường dẫn bằng chứng | NMT | ⬜ | |

## 8. Giai đoạn 7 — Thực nghiệm & phân tích (22/12 – 04/01)

| ID | Việc | Phụ trách | Trạng thái | Bằng chứng / tiêu chí xong |
|---|---|---|---|---|
| P7.1 | Ablation A1–A4 (bỏ ràng buộc thời gian / mở rộng đồ thị / Verifier / trích xuất cấp khoản) | CMT | ⬜ | |
| P7.2 | Phân tích lỗi miền giao thông đường bộ | CMT | ⬜ | |
| P7.3 | Ablation A5–A6 (độ chi tiết đơn vị, quy mô model) | NMT | ⬜ | |
| P7.4 | A7 — chuyển sang miền Thuế, không tinh chỉnh | NMT | ⬜ | |
| P7.5 | Phân rã kết quả theo T1–T6 và kiểm định giả thuyết | CMT, NMT | ⬜ | |

## 9. Giai đoạn 8 — Viết bài báo (05/01 – 11/01)

| ID | Việc | Phụ trách | Trạng thái | Bằng chứng / tiêu chí xong |
|---|---|---|---|---|
| P8.1 | Phần phương pháp và thực nghiệm | CMT | ⬜ | |
| P8.2 | Phần tổng quan, kết quả, thảo luận | NMT | ⬜ | Tái dùng `docs/graph_justification.md` |
| P8.3 | Chọn hội nghị và nộp | CMT, NMT | ⬜ | |

## 10. Giai đoạn 9 — Hoàn thiện khóa luận (12/01 – 01/02)

| ID | Việc | Phụ trách | Trạng thái | Bằng chứng / tiêu chí xong |
|---|---|---|---|---|
| P9.1 | Demo phần hệ thống | CMT | ⬜ | |
| P9.2 | Demo phần dữ liệu và đánh giá | NMT | ⬜ | |
| P9.3 | Viết các chương | CMT, NMT | ⬜ | |
| P9.4 | Công bố ViLexTime và code tái lập | CMT, NMT | ⬜ | |
| P9.5 | Chuẩn bị bảo vệ | CMT, NMT | ⬜ | |

---

## 11. Quyết định và nguyên tắc đang hiệu lực

**Stack:** [0001 — Neo4j và Milvus là kho dẫn xuất từ `data/`](../../decisions/0001-neo4j-milvus-la-kho-dan-xuat.md).

**Dữ liệu:** [0002 — Phạm vi neo thời gian, vai trò VBHN và dữ liệu dẫn xuất](../../decisions/0002-pham-vi-neo-thoi-gian-va-du-lieu-dan-xuat.md). Chỉ QPPL được truy xuất theo mốc t; VBHN dùng để kiểm chứng L3; không ghi đè dữ liệu nguồn.

**Nguyên tắc domain** (kế thừa từ roadmap cũ, vẫn đúng với code hiện tại):

| # | Nguyên tắc | Nơi thể hiện |
|---|---|---|
| D1 | Khoảng hiệu lực luôn nửa mở `[start, end)` | `TemporalInterval` |
| D2 | Tách danh tính `Provision` khỏi nội dung `ProvisionVersion` | `temporal/models.py` |
| D3 | Lõi logic thời gian không phụ thuộc DB | `temporal/` chỉ dùng stdlib |
| D4 | Event thiếu ngày hoặc target duy nhất không được áp | `LegalEvent.is_applicable` |
| D5 | Áp event nguyên tử: lỗi một target thì không đổi gì | `EventApplier.apply` |
| D6 | Bãi bỏ nút cha không đóng phiên bản của cây con; hiệu lực con tính động | `ValidityService` |
| D7 | Hai event cùng ngày trên cùng một nút phải gộp trước khi áp | `EventApplier` |
| D8 | Tham chiếu mơ hồ chỉ giữ candidate, không chọn tạm | `extraction/models.py` |
| D9 | "Thay cụm từ" phải chuyển thành toàn văn trước khi áp | `TextUpdate` |
| D10 | Resolver chỉ nhận đúng một kết quả khớp cấu trúc, không fuzzy | `target_resolver.py` |
| D11 | Bằng chứng truy xuất phải lấy từ đúng snapshot hợp lệ | Áp dụng khi làm L4 (P6.1) |

Các quyết định cũ **đã bị thay thế**: serialization envelope, repository Protocol, query schema riêng (bị xóa ở `5b8ee70`), và "Neo4j là nguồn sự thật" (bị thay bởi 0001).

**Nguyên tắc dữ liệu:**
- Không xóa văn bản đã hết hiệu lực hoặc bất thường; loại trừ bằng skip-list ở tầng đọc.
- Không tự lọc theo `documentFields`/`documentMajors`; chỉ tạo ứng viên để người duyệt.
- Không đoán mã lạ; không coi mọi `createdDate` là ngày pháp lý.
- Không coi "thiếu dữ liệu" là "dữ liệu nói khác"; không đoán căn chỉnh điều khoản.
- Hiệu lực cấp văn bản không đại diện cho hiệu lực cấp điều khoản.

## 12. Vấn đề mở cần nhóm chốt

| Vấn đề | Chặn việc | Ghi chú |
|---|---|---|
| Đề cương ghi "bốn mục tiêu" nhưng liệt kê 5 | P1.2 | |
| Giả thuyết nhắc T1–T7, Bảng 2 chỉ có T1–T6; `graph_justification.md` gọi nhóm hết hiệu lực một phần là T7 | P1.2, P4.1 | |
| Hai công thức cùng đánh số (5); lỗi chính tả "driff-driven", "cuarm ô hình", "mình họa"; MSSV `23621643` khác tên file `23521643` | P1.2 | |
| Câu "metadata giảm đáng kể chi phí gán nhãn": metadata cho biết *khoản nào* hết hiệu lực, không cho biết *khi nào* | P1.2 | `docs/audit_dataset.md` §9 |
| Có dùng H1–H4 không; A4 chỉ là proxy cho H3 | P1.5 | |
| Chọn embedding model và LLM | P5.1 | |
| Danh sách loại văn bản QPPL; "Quyết định" lẫn văn bản cá biệt | P2.8 | backfill T2.1 |
| 1.626 QPPL có chữ nhưng không có cây Điều/Khoản: dựng cấu trúc hay dùng cả văn bản làm một đơn vị | P2.11, P3.4 | backfill T2 Validation |
| Hội nghị mục tiêu | P8.3 | |

## 13. Rủi ro

| Rủi ro | Ảnh hưởng | Giảm thiểu |
|---|---|---|
| L2 khó: 79,7% VB bị nhiều văn bản tác động, không biết văn bản nào bãi bỏ khoản nào | Trễ M2, kéo trễ mọi giai đoạn sau | Làm P3.10 (843 mẫu gold) trước; regex theo mẫu; LLM chỉ cho ca khó |
| RAM 7 GB cho Neo4j + Milvus với full corpus | Không chạy được hoặc rất chậm | Đo ở P3.2; giới hạn RAM; tắt dịch vụ không cần |
| Embedding khoảng 1,14 triệu nút trên CPU | Trễ M4 | Đo tốc độ sớm; tìm GPU; chạy nền theo lô có checkpoint |
| Corpus không tái tạo được | Mất dữ liệu là mất đề tài | Hoàn tất P2.7 trước M1 |
| Nhãn T5/T6 cần chuyên môn luật | κ thấp, trễ M3 | Liên hệ cố vấn luật từ Giai đoạn 3 |

## 14. Không làm (giới hạn theo đề cương)

- Hiệu lực theo lãnh thổ và đối tượng áp dụng; giải xung đột quy phạm chỉ là mở rộng tùy chọn.
- Văn bản địa phương; bảng biểu, phụ lục dạng ảnh.
- Huấn luyện lại LLM.
- Thao tác `SUSPEND`/`RESUME` là mở rộng, không bắt buộc.

## Validation

- Repository: `python3 -m pytest` từ thư mục gốc.
- Dữ liệu: `python3 scripts/check/verify_pipeline.py` sau mỗi lần crawl.

## Nhật ký

| Ngày | Thay đổi | Bằng chứng |
|---|---|---|
| 2026-09-04 | Xong Stage 1–5b, delta crawl, bảng mã trạng thái | `docs/plans/completed/2026-09-04-truoc-stage-6.md` |
| 2026-09-11 → 12 | Lõi domain thời gian, resolver, adapter Neo4j (chưa chạy server thật) | commit `a9170a9` → `10b33ab` |
| 2026-09-12 | Audit corpus: 22.550 VB, lỗ hổng thời gian 4,4% | `docs/audit_dataset.md` |
| 2026-09-13 | Refactor sang index SQLite, xóa adapter Neo4j/vector; snapshot lên HF | commit `5b8ee70`, `fa90cb5` |
| 2026-09-14 | Chốt stack Neo4j + Milvus (ADR 0001); lập master plan; dọn tài liệu cũ | File này |
| 2026-09-14 | Review bản nháp backfill; chốt phạm vi QPPL, vai trò VBHN, tách Khoản/Điểm, snapshot v2 (ADR 0002). Đo: 6.815/7.620 expiry chưa định vị có marker; ngày history `T00:00` lệch +1 | `../completed/2026-09-17-backfill-corpus-v2.md` |
| 2026-09-14 | Backfill T0 (snapshot v1 kiểm chứng) và T1 (edges thuần từ raw, review queue chính xác, `align()` +4.199 node, chuẩn hóa ngày history, `anchor_problem`). Lộ 115 đích phả hệ chưa tải → T3.1 | `../completed/2026-09-17-backfill-corpus-v2.md` mục Validation |
| 2026-09-14 | Backfill T2: phạm vi QPPL trung ương (20.318), hàng đợi điền tay 308, phát hiện 1.626 QPPL có chữ nhưng không có cấu trúc | `../completed/2026-09-17-backfill-corpus-v2.md` |
| 2026-09-17 | Backfill T3.1: closure genealogy hội tụ (115→40→0 target chưa tải), vá bug `attach_provision_text.py` không ghi nhận `no_content` | `../completed/2026-09-17-backfill-corpus-v2.md` |
| 2026-09-17 | Backfill T4.3: 381/388 candidate `effective_to` quyết định qua đối chiếu văn bản gốc (không chỉ tin referenceType); sửa 5 lỗi thuật toán so khớp; bắt thêm 2 candidate sai (`3639`, cùng lớp lỗi với `46742`) | `../completed/2026-09-17-backfill-corpus-v2.md` |
| 2026-09-17 | Backfill T5.2: kiểm tra tính đầy đủ toàn bộ 65.216 Điều/Khoản phát hiện 15% mất câu dẫn nhập (2,57M ký tự) → thêm field `preambles`; 100/100 mẫu kiểm tay đúng | `src/legal_crawler/provisions/subtree.py`, `../completed/2026-09-17-backfill-corpus-v2.md` |
| 2026-09-17 | Backfill T5.4: tái lập đúng phương pháp v1 — 243 văn bản một tác nhân, 919 bộ ba gold (v1: 228/843) | `../completed/2026-09-17-backfill-corpus-v2.md` |
| 2026-09-17 | Backfill T3.3: commit code (`7794627`), đóng băng snapshot v2, đẩy HF (`7d8ab0c`), tải về thư mục khác kiểm chứng `verify_pipeline.py` pass — **M1 đạt trước hạn** | `../completed/2026-09-17-backfill-corpus-v2.md` |
