# Bản nháp khóa luận

Bản C9b tiếp nối nháp ở `3f43bf2`, phục vụ mốc D0. Các chương còn là bản AI hỗ trợ soạn, chờ tác giả và GVHD duyệt. v1.0 (nhãn hỗn hợp người/agent) và test 2 (nhãn LLM) là vòng thử; bộ test cuối chưa chạy. Kế hoạch có thẩm quyền vẫn là [master plan](../plans/active/master-plan.md).
<!-- nguồn: docs/plans/active/master-plan.md; yêu cầu C9b của tác giả -->

| Chương / phụ lục | Trạng thái | Marker chờ | Marker cần |
|---|---|---:|---:|
| [Chương 1. Mở đầu](chuong-1-mo-dau.md) | Đã hẹp luận điểm; chờ X8 và kết luận cuối | 2 | 0 |
| [Chương 2. Cơ sở lý thuyết và công trình liên quan](chuong-2-co-so-ly-thuyet.md) | Đã cập nhật mức đọc; còn xác minh nguồn | 0 | 9 |
| [Chương 3. Kho văn bản và đồ thị tri thức có phiên bản](chuong-3-kho-van-ban-va-do-thi.md) | Nháp; M2 và đối chiếu độc lập chưa đạt | 1 | 2 |
| [Chương 4. Bộ dữ liệu ViLexTime](chuong-4-vilextime.md) | Đã khai tiếp xúc cũ của A; gold1 còn trống | 2 | 2 |
| [Chương 5. Phương pháp và các hệ so sánh](chuong-5-phuong-phap.md) | Nháp cơ chế; còn kết quả sinh/ablation | 2 | 3 |
| [Chương 6. Thực nghiệm và phân tích](chuong-6-thuc-nghiem.md) | Đã báo riêng các vòng thử; còn Colab và bộ cuối | 18 | 1 |
| [Chương 7. Kết luận và hướng phát triển](chuong-7-ket-luan.md) | Kết luận tạm; chờ bằng chứng bộ cuối | 6 | 2 |
| [Phụ lục. Khai báo sử dụng AI](phu-luc-khai-bao-ai.md) | Đã thêm khai báo C9b; chờ người duyệt/quy định UIT | 1 | 1 |
<!-- nguồn: docs/thesis/chuong-1-mo-dau.md; docs/thesis/chuong-2-co-so-ly-thuyet.md; docs/thesis/chuong-3-kho-van-ban-va-do-thi.md; docs/thesis/chuong-4-vilextime.md; docs/thesis/chuong-5-phuong-phap.md; docs/thesis/chuong-6-thuc-nghiem.md; docs/thesis/chuong-7-ket-luan.md; docs/thesis/phu-luc-khai-bao-ai.md -->

Các mục `[CHỜ]`, nhóm theo việc (marker chi tiết nằm trong chương):

- Chương 3–4: lô thử, nhãn người, thời gian/đồng thuận, gold1 theo người, đối chiếu VBHN và khóa dữ liệu. A đã thấy đáp án đồ thị của phần silver cũ; không khai gán lại là mù mới.
- Chương 1, 5–7: sinh dev cho hybrid/`proposed2` và ablation; `proposed3`; X8 cấp sẵn căn cứ đúng mốc so với hiện hành, dev trước rồi bộ cuối.
- Chương 6: Colab đợt 2 trên từng vòng thử theo danh sách ở §6.6.1; không dùng số để chọn cấu hình. LightRAG trên tập con báo riêng.
- Chương 1, 5–7: khóa amendment và họ xác nhận; kết quả bộ cuối cho RQ, T6, thành phần/miền, gold mù, E7 người kiểm và giám khảo LLM.
- Phụ lục: hồ sơ người kiểm và công cụ ở các lượt tiếp theo.

Các mục `[CẦN]`, nhóm theo việc:

- Chương 2: kiểm trực quan PDF; đối chiếu BM25/FTS5, DPR/embedding và cấu hình GraphRAG/LightRAG; giữ mâu thuẫn tập/trang BM25; chốt phiên bản SAT-Graph RAG, xuất bản VLQA; đọc đủ VLegal-Bench, ViLegalExpert và nguồn gần; mở lại phần khảo sát bị chặn.
- Chương 2: nguồn đã xác minh cho Holm, bootstrap theo cụm và các chuẩn nếu trình bày độc lập; chưa tự thêm khóa ngoài bibliography hiện có.
- Chương 3–4: phễu dữ liệu cùng snapshot, ví dụ pháp lý kiểm độc lập, phân bố năm/loại văn bản, nguồn Datasheets.
- Chương 5–6: nguồn RRF, topology GPU, thư viện và chi phí thực chạy theo provenance/biên nhận.
- Chương 7 và phụ lục: tác giả/GVHD rà đóng góp, phạm vi; xác minh quy định UIT và cách khai AI.

Paper được dựng lại ở [bản nháp paper](../paper/nhap-paper-vilextime.md), có danh sách chờ riêng. Đếm marker trên các chương và phụ lục, không gộp README hoặc paper. Đếm từ bằng tách khoảng trắng sau khi bỏ comment HTML.

Kiểm C9b: 25.683 từ trong các chương/phụ lục; 32 marker chờ, 20 marker cần. Paper: 8.315 từ. `paper_check.py`: 0 sai lệch, bắt 3/3 lỗi cấy.
<!-- nguồn: các file chương/phụ lục và docs/paper/nhap-paper-vilextime.md; scripts/paper/paper_check.py; phép đếm cục bộ /tmp/c9b-summary.json -->

Quét số chương 3–7: không còn số thập phân thiếu comment nguồn trong ±5 dòng; mẫu ngẫu nhiên seed `20261105` khớp 40/40, sai 0. Đây là kiểm vị trí nguồn và kiểm mẫu, chưa chứng nhận mọi số còn lại đã đối chiếu ngữ nghĩa. Script và biên nhận tạm ngoài repo: `/tmp/c9b_numeric_audit.py`, `/tmp/c9b-final.json`, `/tmp/c9b-final-broad.json`, `/tmp/c9b_verify40.py`, `/tmp/c9b-40-receipts.json`, `/tmp/c9b-exposure.json`.
<!-- nguồn: /tmp/c9b-final.json; /tmp/c9b-final-broad.json; /tmp/c9b-40-receipts.json; /tmp/c9b-exposure.json -->
