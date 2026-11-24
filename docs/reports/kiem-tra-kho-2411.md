# Kiểm tra kho phiên bản, 24/11/2026

Chỉ đọc. Kho = `data/derived/versions.jsonl` + `event_log.jsonl` (dựng 10/11). `data/temporal.sqlite` chỉ là chỉ mục
bản gốc, mỗi điều khoản đúng 1 bản. Script: lệnh trong phiên, tái lập bằng `data/review/qa_v6/w3/store_check.py` cho mục 3.

## 1. Cấu trúc: đạt
1.598.662 phiên bản / 1.576.199 điều khoản. 0 điều khoản mồ côi, 0 khoảng hiệu lực chồng, hở hay âm.

## 2. Độ phủ lệnh sửa đổi: yếu
Áp 21.892 / 56.624 lệnh (38,7%): sửa đổi 15.428/35.432, bãi bỏ 6.430/13.138, **bổ sung 0/5.653**, thay thế 32/2.228,
đình chỉ 0/36. Từ chối vì: 18.982 `needs_review` chưa ai duyệt (hàng duyệt `data/review/provision_events.jsonl` có 909
dòng, đều `auto_rejected`, 0 dòng LLM hay người duyệt); 14.765 văn bản đích không có trong kho.
Hệ quả: 98,6% điều khoản chỉ có 1 phiên bản. Khớp số 09/11: kho phủ 40,2% lần hết hiệu lực (`g2-recall-m2-20261109.md`).

## 3. Trong 199 lineage của bộ
20 lineage có lệnh bị kho từ chối nhắm đúng lineage hoặc cấp trên; 11 lệnh có hiệu lực trước dòng muộn nhất, 8 trong số
đó kho đã có ranh giới phiên bản đúng ngày (không phải lỗi). Còn 3 ứng viên, 1 đã có trong phiếu W3, 2 thêm thành
`X115`, `X116` (S15).

## 4. Lỗi nhỏ
2.503 cặp phiên bản liền nhau trùng lời văn (1 cặp trong bộ, không có dòng hỏi bản đó). 30.313 phiên bản thiếu ngày
bắt đầu (244 văn bản), 727 văn bản thiếu ngày hiệu lực; không chạm bộ.

## 5. Đối chiếu với GraphRAG
Không phải GraphRAG kiểu Microsoft (trích thực thể bằng LLM, cộng đồng, tóm tắt cộng đồng). Đồ thị = cây
Điều→Khoản→Điểm + cạnh lệnh sửa đổi/bãi bỏ, biên dịch offline thành phiên bản có khoảng hiệu lực. Lúc truy vấn chỉ
mở rộng 1 bước bằng SQL (`src/vilexgraph/framework/graphx.py`), không chạy Neo4j; bao đóng bắc cầu ở công thức (2) của
`docs/graph_justification.md` chưa làm. Số đo đã có: đi đồ thị lúc truy vấn +0,013 [−0,009; +0,035].
Viết được là "đồ thị pháp lý theo thời gian biên dịch offline" (khung 17/11), không viết là GraphRAG kiểu Microsoft.

## 6. Hệ quả
Lỗi chính của kho là sót sửa đổi; W1 dùng cùng lời văn vbpl nên không bắt được, W3 và W3.4 mới bắt. Duyệt 18.982 lệnh
chờ là việc của 7.0; bản 6.x ghi là giới hạn.
