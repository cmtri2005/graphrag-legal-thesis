# Thử tải văn bản hợp nhất — 05/11/2026

Claude thực hiện tải và đối chiếu khoảng 00:34–00:43 UTC. Codex tiếp quản,
kiểm lại artifact trên đĩa và ghi báo cáo này. Đây là khảo sát khả năng sử dụng
nguồn VBHN để kiểm đồ thị; chưa phải bộ gold độc lập đã được xác nhận.

## Phạm vi và bằng chứng

Đầu vào là 299 VBHN có trạng thái `source_body_empty` trong
`data/derived/consolidated_snapshot_report.json`. Liệt kê file trả về:

| Kết quả | Số lượng |
|---|---:|
| Văn bản đã liệt kê | 299 |
| Văn bản có file đính kèm | 238 |
| File PDF trong danh sách | 492 |
| File RAR trong danh sách | 2 |
| File DOC/DOCX trong danh sách | 0 |
| Văn bản liên quan các bộ dữ liệu được chọn để thử tải | 48 |
| Tải được PDF, một file/văn bản | 40 |
| Không có PDF | 8 |
| Tổng dung lượng PDF | 182.530.450 byte |

File được tải từ cổng VBPL qua mẫu URL mà giao diện cổng dùng:
`https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/minio/buckets/vbpl/{id}/{fileName}/download`.
Lần tải ban đầu có khoảng nghỉ 1,5 giây sau mỗi file. Không thay nội dung
`data/raw/`, corpus hay release.

Artifact cục bộ:

- `data/vbhn_files/related_files.jsonl`: danh sách file cho 299 văn bản.
- `data/vbhn_files/relevant_ids.json`: 48 ID được chọn.
- `data/vbhn_files/pdf/{id}/source.pdf`: 40 PDF đã tải.
- `data/vbhn_files/relevant_quality.json`: dung lượng, số trang và chỉ báo lớp chữ.
- `data/vbhn_files/pdf_compare.json`: kết quả đối chiếu và ví dụ từng đơn vị.
- `data/vbhn_files/source/`: ba script liệt kê, tải và đối chiếu khôi phục từ
  lệnh trong log Claude, gồm các chỉnh sửa cuối trước khi phiên dừng.
- `data/vbhn_files/pdf_compare.reproduced.json`: kết quả Codex chạy lại từ PDF
  cục bộ, **khớp từng byte** với `pdf_compare.json`.
- `data/vbhn_files/probe.sha256`: hash của 48 file (40 PDF, năm file metadata
  và ba script).

Codex kiểm lại: đủ 40 PDF, magic bytes `%PDF`, kích thước khớp metadata,
không có file thiếu hoặc lệch kích thước. Có thể kiểm lại nội dung bằng:

```bash
sha256sum -c data/vbhn_files/probe.sha256
```

## Chất lượng chữ và phép đối chiếu thử

37/40 PDF có ít nhất 50 ký tự sau khi trích chữ; 3 PDF chỉ có 12–32 ký tự.
21/40 file có ít nhất ba dòng bắt đầu bằng `Điều` theo bộ dò ban đầu.
Những chỉ báo này chưa xác nhận độ chính xác OCR hay khả năng tách điều khoản.

Phép thử đọc lớp chữ PDF, căn theo Điều/Khoản và so snapshot của văn bản gốc
tại ngày ban hành VBHN. Kết quả cho cả 48 đầu vào:

| Trạng thái | Số văn bản |
|---|---:|
| Đối chiếu được | 18 |
| Không tìm được dấu Điều trong chữ PDF | 19 |
| Thiếu ngày | 2 |
| Không có PDF | 8 |
| Bản ghi trùng bị bỏ | 1 |

Tổng đơn vị của 18 văn bản đối chiếu:

| Trạng thái | Số đơn vị |
|---|---:|
| Khớp chữ chính xác sau chuẩn hóa | 1.773 |
| Khác chữ, độ giống ≥ 0,98 | 121 |
| Độ giống từ 0,90 đến dưới 0,98 | 74 |
| Độ giống dưới 0,90 | 344 |
| Không có khóa cấu trúc tương ứng ở văn bản gốc | 122 |
| Kho không có chữ | 21 |
| Dấu bãi bỏ khớp trạng thái kho | 14 |
| Dấu bãi bỏ lệch trạng thái kho | 10 |

17/18 văn bản có trung vị độ giống ≥ 0,90. Đây là mô tả kết quả căn thử,
không phải tỷ lệ đúng của đồ thị.

## Giới hạn và việc cần làm trước khi dùng làm gold

Mã thử nghiệm ban đầu ở thư mục tạm của Claude không còn trên đĩa khi tiếp quản;
đã khôi phục từ log phiên và chạy lại bằng lệnh sau, chỉ dùng dữ liệu cục bộ:

```bash
PYTHONPATH=src .venv/bin/python data/vbhn_files/source/vbhn_compare.py
```

Script ghi riêng `pdf_compare.reproduced.json`. Phép so chữ gần đúng dùng
`SequenceMatcher` trên tối đa 1.500 ký tự đầu mỗi phía. Preview trong JSON
chỉ giữ 160 ký tự mỗi phía. Vì vậy điểm giống cao không chứng minh toàn văn đúng.

Ví dụ lệch cho thấy bộ tách đôi lúc gộp tiêu đề Điều với nội dung Khoản, để lẫn
số chú thích hoặc không tách được dòng xuống hàng. Có cả khác biệt từ ngữ có
thể là lỗi dựng phiên bản; chưa phân xử nguyên nhân cho từng trường hợp.
Các mục khớp chính xác có thể chỉ là tiêu đề ngắn.

Muốn dùng nguồn này làm gold cần lưu mã trích/căn có thể chạy lại, kiểm chứng
trường ngày dùng cho snapshot, và rà các cặp đầy đủ để tách lỗi nguồn/PDF/căn
đoạn khỏi lỗi đồ thị. Chưa có cơ sở dùng kết quả thử này thay nhãn người cho
ViLexTime hoặc suy ra độ chính xác của từng câu benchmark.
