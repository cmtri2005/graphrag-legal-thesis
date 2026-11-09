# Đối chiếu VBHN — C7b, 05/11/2026

Phạm vi: T2/T3/T6 của silver, test 2 và toàn bộ v1.0; 71 nguồn VBHN ứng viên, 51 lineage có cạnh liên quan. Không sửa đồ thị, benchmark hay nhãn; không gọi LLM.
Tải: C7 trước đã bổ sung 25 PDF (158.300.803 byte), C7b tải thêm 0; 59/71 nguồn đích có PDF, 12 không có PDF trong metadata. Script tải tuần tự, nghỉ ≥1,5 giây; lượt C7b không cần gửi yêu cầu mạng.
Lệnh: `PYTHONPATH=src .venv/bin/python scripts/check/compare_benchmark_vbhn.py --fetch`, rồi bỏ `--fetch` để đối chiếu; `sha256sum -c data/vbhn_files/c7.sha256` để kiểm đầu vào.
Test: `PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_compare_benchmark_vbhn.py` — 8 qua; đã sửa khôi phục đích sự kiện được chấp nhận, mẫu số bỏ sót ca chưa phân xử và nhận nhầm dấu phân cách số là khác nhỏ.
Phương pháp: `pdftotext -layout`, căn duy nhất theo Điều/Khoản/Điểm, so toàn văn riêng của đơn vị với mọi phiên bản; chỉ kết luận chọn sai khi khớp chính xác bản khác. `issueDate` phải trùng ngày xác thực trong PDF; cách ly nguồn có ngày tương lai trong lời dẫn. 6 nguồn đạt cổng, 39 cần xem, 14 không đủ lớp chữ, 12 thiếu PDF.

| Bộ | Lineage tổng | Có cạnh VBHN | Xác minh nguồn/ngày | Căn được | Mốc cùng version_id / tổng |
|---|---:|---:|---:|---:|---:|
| silver | 168 | 21 | 1 | 1 | 2/819 |
| test 2 | 101 | 17 | 2 | 0 | 0/492 |
| v1.0 | 105 | 13 | 3 | 1 | 2/487 |
Độ phủ mốc là dòng benchmark có đáp án `version_id` trùng snapshot tại ngày VBHN sau căn đoạn; tương ứng 2/0/2 cặp (lineage, ngày) riêng biệt. Ngày truy vấn trùng ngày VBHN: 0 cả ba bộ; mốc bãi bỏ được phủ: 0.

| Phân loại 96 cặp (lineage, VBHN), gộp dòng cùng lineage | Khớp | Khác nhỏ | Chọn sai | Cần người xem | Không căn được | PDF không đủ chữ | Không PDF |
|---|---:|---:|---:|---:|---:|---:|---:|
| Số cặp | 1 | 0 | 0 | 9 | 45 | 24 | 17 |
Trong 2 cặp có đủ hai toàn văn để so: 1 khớp, 1 cần người xem; tỷ lệ khớp đã xác nhận 1/2 = 50%, Wilson 95% [9,45%; 90,55%]. Giữ ca chưa phân xử trong mẫu số; chưa xác định nó sai. Các ca không căn/thiếu chữ/thiếu ngày không thuộc mẫu số này.
Độ gần: bản chọn gần nhất 1 cặp; bản khác gần hơn 1 cặp nhưng không khớp chính xác, nên chưa kết luận chọn sai. Khác nhỏ chỉ cho phép cùng token chữ/số, giữ dấu phân cách số; không tự bỏ chú thích để nhận khớp.
Dấu bãi bỏ: rà riêng toàn bộ đơn vị căn được của nguồn đạt cổng, 2 dấu; khớp trạng thái 0, lệch 2, cần xem 0. Đây là tín hiệu cần phân xử, không cộng vào mẫu số so chữ hoặc tự kết luận lỗi đồ thị.
Giới hạn: Wilson chỉ mô tả tỷ lệ xác nhận trong 2 cặp đã so, không phải ước lượng độ đúng toàn benchmark; nguồn chọn thuận tiện, có phụ thuộc lineage/VBHN. Không suy rộng ngoài phần có VBHN, không thay gold mù do người làm.
Chỗ dừng: đã hết PDF có thể tải trong metadata; 54 cặp cần người xem hoặc không căn được, cùng các nguồn thiếu PDF/lớp chữ/ngày, còn chưa phân xử. Không OCR, không thử né nguồn, không sửa nhãn.
Chi tiết và hàng cần xem chỉ ở `data/vbhn_files/doi_chieu_chi_tiet.jsonl`; bằng chứng ngày/nguồn ở `c7_sources.json`, dấu bãi bỏ ở `c7_repeal.json`, số tổng ở `c7_summary.json`, hash ở `c7.sha256` trong cùng thư mục gitignore. 47/48 hash thăm dò cũ còn khớp; metadata cũ nguyên vẹn 299 dòng đầu, chỉ nối thêm 10 dòng và đã có hash mới.

## Chạy lại G2, 09/11/2026

Lệnh: `PYTHONPATH=src .venv/bin/python scripts/check/compare_benchmark_vbhn.py`.
Kết quả: exit 0; 71 nguồn, 96 cặp. Khớp 1; khác nhỏ 0; chọn sai phiên bản
đã chứng minh 0; cần người xem 9; không căn được 45; PDF thiếu chữ 24;
không PDF 17. Hai cặp so được có 1 khớp và 1 chưa phân xử.
Có 2 tín hiệu lệch trạng thái bãi bỏ. **Không suy ra tổng số lỗi pháp lý**
từ các ca chưa phân xử. Số lỗi chọn sai được máy chứng minh: **0/2 cặp so chữ**.
Đây không phải bằng chứng toàn kho không lỗi. Các số không đổi so với 05/11.

Kiểm: `PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_compare_benchmark_vbhn.py`;
`sha256sum -c data/vbhn_files/c7.sha256`. Kết quả: 8 passed (0,28 giây); toàn bộ hash OK.
Không tải mạng hoặc thay nhãn. Dừng phân xử 9 ca và 2 tín hiệu bãi bỏ
cho người có thẩm quyền; không dùng VBHN thay gold mù.
