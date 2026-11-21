# Đọc mù ngẫu nhiên 30 dòng (21/11/2026)

## Vì sao
- 105 lineage đã đọc mù **không phải mẫu ngẫu nhiên** của bộ phát hành, nên tỷ lệ lỗi đo trên đó không đại
  diện cho cả bộ. Đợt này rút **ngẫu nhiên 30 trong 94 lineage chưa ai đọc mù** (seed `20261121:random30`,
  mỗi lineage một dòng, chọn ngẫu nhiên trong mọi dòng của lineage, cả hai chế độ ngày).
- Cùng 30 dòng giao cho **hai người đọc độc lập** (A, B; chốt 21/11), đo thêm đồng thuận người–người.
  Alternative Annotator Test (Calderon và cộng sự) cần ≥ 3 người nên **không làm**; vì vậy bài **không được viết**
  "nhãn AI ngang nhãn người".

Mẫu rút ra: two_versions 15, control 14, multi_versions 1; mid_interval 18, boundary 12; 30/30 có đáp án
(cả 23 lineage bãi bỏ đều đã được đọc mù từ trước nên không còn trong 94).

## Ai đọc
Người đọc **chưa từng thấy đáp án của kho cho các lineage này**. Tác giả duyệt (CMT) đã thấy mọi lineage
kèm đáp án nên **không được đọc**. Đề xuất: A = đồng tác giả đọc mù (như đợt 2), B = luật sư.
Ghi lại vai trò của A/B ở đây khi giao phiếu; tên người không công bố.

## Giao và nhận
1. Gửi `gold_A.xlsx` / `gold_B.xlsx` (giống hệt nhau). Sheet "Đọc trước" có hướng dẫn; chỉ 5 cột
   được mở. Không gửi `gold_sample.tsv`, `release_joined.jsonl`.
2. Người đọc trả file → chép đè vào thư mục này rồi:
   ```
   python3 scripts/review/independent_gold.py import A --review data/review/gold_random30
   python3 scripts/review/independent_gold.py reveal A --review data/review/gold_random30 \
       --release data/review/gold_random30/release_joined.jsonl
   ```
   `import` từ chối toàn bộ nếu có cột khóa bị sửa hoặc giá trị ngoài danh sách. `reveal` khóa câu trả lời bằng
   sha256 rồi mới đặt đáp án của kho bên cạnh.
3. Ở `gold_X.reveal.tsv`, điền `dong_y` (có/không) và `ly_do` khi lệch; ca lệch phân xử bằng nguồn chính thức
   như đợt 20/11.

## Phân tích (chốt trước khi xem kết quả)
- **Tỷ lệ lỗi kho** trên 30 dòng: số dòng kho sai sau phân xử / 30, kèm khoảng Wilson 95%. Ước lượng cho cả bộ:
  lỗi ở 105 lineage đã đọc đều đã sửa, nên phần còn lại ≈ (94/199) × tỷ lệ trên 30 dòng. Báo cả khoảng.
- **Đồng thuận người–người** (A–B): trên `hieu_luc` và trên nội dung (khớp đáp án kho sau phân xử); Cohen κ kèm
  Gwet AC1 và tỷ lệ khớp thô, vì gần như mọi dòng là "còn" (κ dễ thấp giả do mất cân bằng).
- Không làm Alt-test (chỉ 2 người). Nhãn AI chỉ được mô tả là nhãn AI.
- Không đổi luật đếm sau khi thấy kết quả; nếu phải đổi, báo cả hai bản.

`build.py` dựng lại toàn bộ thư mục (từ chối ghi đè phiếu đã có nhãn).
