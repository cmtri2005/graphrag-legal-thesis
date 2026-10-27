# Ghi chú đọc paper cho khóa luận ViLexTime

Mỗi file là bản ghi chú chi tiết của một tài liệu trong `related_paper/`. Quy ước mỗi file: **0. Thông tin chung → 1. WHY → 2. HOW → 3. WHAT → hạn chế/phê phán → dùng gì cho khóa luận**. Số liệu lấy từ văn bản PDF; chỗ nào chỉ nằm trong biểu đồ hoặc có mâu thuẫn trong bản gốc thì đã ghi chú.

| # | File | Tài liệu | Mức ưu tiên |
|---|---|---|---|
| 1 | [01-temporal-misgrounding-fiscalqa-pro.md](01-temporal-misgrounding-fiscalqa-pro.md) | Temporal Misgrounding in Legal RAG (FiscalQA Pro, luật thuế Pháp) | Đọc kỹ |
| 2 | [02-sat-graph-rag-legal-norms.md](02-sat-graph-rag-legal-norms.md) | SAT-Graph RAG (Hiến pháp Brazil) | Đọc kỹ |
| 3 | [03-vihermes.md](03-vihermes.md) | ViHERMES (multihop QA quy định y tế VN) | Đọc kỹ |
| 4 | [04-temporal-graphrag-vietnamese-law-report.md](04-temporal-graphrag-vietnamese-law-report.md) | Báo cáo Temporal GraphRAG cho pháp luật VN | Đọc kỹ, **không trích như nguồn học thuật** |
| 5 | [05-vietlegal-benchmark.md](05-vietlegal-benchmark.md) | VietLegal (23 LLM, 22 tác vụ) | Đọc lướt |
| 6 | [06-vlqa-dataset.md](06-vlqa-dataset.md) | VLQA (QA pháp lý tiếng Việt) | Đọc lướt |
| 7 | [07-graphrag-bench.md](07-graphrag-bench.md) | GraphRAG-Bench (giáo trình CS) | Đọc lướt, lấy phương pháp |
| 8 | [08-legalgraphrag-acl2026.md](08-legalgraphrag-acl2026.md) | LegalGraphRAG (ACL 2026, hình sự Trung Quốc) | Đọc lướt |
| 9 | [09-verifiable-reasoning-framework-icoco2026.md](09-verifiable-reasoning-framework-icoco2026.md) | Verifiable Reasoning Framework (ICOCO 2026, UIT) | Đọc lướt |

Chưa có ghi chú cho các tài liệu đã xếp "bỏ qua": `2605.18747v1.pdf` (Code as Agent Harness), `Procedural Graphs...pdf`, `infor617.pdf` (Legal-Onto), `peerj-cs-1786.pdf`; và `2608.09393v1.pdf` trùng với bài 1.

## Bức tranh chung

| Chiều | 01 | 02 | 03 | 05 | 06 | 07 | 08 | 09 |
|---|---|---|---|---|---|---|---|---|
| Miền / ngôn ngữ | thuế Pháp | Hiến pháp Brazil | y tế VN | pháp luật VN | pháp luật VN | giáo trình CS | hình sự TQ | VN (BHXH, DN, thuế) |
| Có yếu tố **thời gian/phiên bản** | **Có (cốt lõi)** | **Có (cốt lõi)** | Chưa (nêu là hướng tương lai) | Chỉ như lỗi quan sát (Task 1.5, recency blindness) | Chỉ loại mẫu lỗi thời | Không | Không | Chỉ là thuộc tính, chưa dùng |
| Đồ thị | Không | Có (ontology LRMoo) | Có (SRKG) | KG để chú giải | Không | So sánh 9 GraphRAG | Có (HierarGraph) | Luật Horn, không đồ thị |
| Chấm điểm | **Tất định (nugget)** | Chưa có số liệu | F1 + LLM-judge | Accuracy / ROUGE-L | ROUGE + BERTScore + người | Accuracy + LLM-judge | ACC/F1/MAE | IRAC thủ công 1 người |
| Có số liệu thực nghiệm | Có | Không | Có | Có | Có | Có | Có | Có |

## Mạch lập luận gợi ý cho khóa luận
1. **Vấn đề**: bản luật hiện hành ≠ bản áp dụng tại ngày hỏi → bài 01 đặt tên và đo (RAG tĩnh chọn đúng phiên bản 0%, một phần do xây dựng bộ lọc); bài 05 và 06 cho bằng chứng gián tiếp trên tiếng Việt (mọi LLM sai ở các luật 2024–2025; 7,19% mẫu VLQA phải sửa cả đáp án lẫn điều vì Nghị định 38/2019 bị Nghị định 24/2023 sửa).
2. **Mô hình dữ liệu**: bài 02 (Work/Expression, CTV, Action, aggregation), bài 03 (SRKG, Amends/Replaces/Supplements, validity tracing), bài 09 (luật Horn có provenance); bài 04 là bản đồ tài nguyên và hướng lộ trình (phải kiểm chứng từng số liệu).
3. **Đánh giá**: bài 01 (nugget + coverage/strict/provenance, thống kê theo cụm, canary, bộ lọc độ khó); bài 07 (đánh giá theo tầng, R/AR); bài 08 (Traceable Correct); bài 03/05/06 (baseline và quy trình chú giải tiếng Việt).
4. **Khoảng trống**: chưa bài nào có (a) benchmark point-in-time bằng tiếng Việt, (b) so sánh GraphRAG với chỉ mục-phiên-bản đơn giản trên câu hỏi vượt single-anchor (so sánh trước/sau, chuỗi sửa đổi, tác động phân cấp).

## Điểm cần kiểm chứng trước khi trích
- Bài 04 là báo cáo tổng hợp không tác giả/ngày/danh mục tài liệu; mọi số liệu cần lần về nguồn gốc.
- Bài 05: số liệu Task 3.1 trong văn bản (43,83%) và bảng (59,83% của Claude Sonnet 4.5) không khớp nhau.
- Bài 08: cột "All" ở Bảng 2 không phải trung bình đơn giản của các ô; PDF lỗi nén nhẹ, số trong các hình không đọc được.
- Bài 01: bộ truy hồi C_prod độc quyền, kết quả 98,3% không tái lập được từ artefact công khai.
- Bài 02: chỉ là case study định tính; không có số liệu.
