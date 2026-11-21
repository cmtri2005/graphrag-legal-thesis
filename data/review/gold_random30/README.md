# Đọc mù ngẫu nhiên 30 dòng (21/11/2026)

## Vì sao
- 105 lineage đã đọc mù **không phải mẫu ngẫu nhiên** của bộ phát hành, nên tỷ lệ lỗi đo trên đó không đại
  diện cho cả bộ. Đợt này rút **ngẫu nhiên 30 trong 94 lineage chưa ai đọc mù** (seed `20261121:random30`,
  mỗi lineage một dòng, chọn ngẫu nhiên trong mọi dòng của lineage, cả hai chế độ ngày).
- Cùng 30 dòng giao cho **ba người đọc độc lập** (A, B, C). Có ≥ 3 người trên cùng mục thì đo được đồng thuận
  người–người và làm được Alternative Annotator Test cho nhãn AI (Calderon và cộng sự). Không có phép thử này
  thì bài **không được viết** "nhãn AI ngang nhãn người".

Mẫu rút ra: two_versions 15, control 14, multi_versions 1; mid_interval 18, boundary 12; 30/30 có đáp án
(cả 23 lineage bãi bỏ đều đã được đọc mù từ trước nên không còn trong 94).

## Ai đọc
Người đọc **chưa từng thấy đáp án của kho cho các lineage này**. Tác giả duyệt (CMT) đã thấy mọi lineage
kèm đáp án nên **không được đọc**. Đề xuất: A = đồng tác giả đọc mù (như đợt 2), B = luật sư, C = một người
không học luật (đồng thời trả lời câu hỏi của GVHD: hướng dẫn có dùng được cho người ngoài ngành không).
Ghi lại ai là A/B/C ở đây khi giao phiếu; tên người không công bố.

## Giao và nhận
1. Gửi `gold_A.xlsx` / `gold_B.xlsx` / `gold_C.xlsx` (giống hệt nhau). Sheet "Đọc trước" có hướng dẫn; chỉ 5 cột
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
- **Đồng thuận người–người**: trên `hieu_luc` và trên nội dung (khớp đáp án kho sau chuẩn hóa), từng cặp và
  Fleiss κ cho ba người; báo kèm Gwet AC1 vì gần như mọi dòng là "còn".
- **Alt-test** (chỉ khi đủ 3 người): nhãn AI cho cùng 30 dòng phải được làm **mù** (agent AI-A và AI-B đọc đúng
  phiếu này, không thấy kho), rồi so theo thủ tục của Calderon và cộng sự. Kết quả đạt hay không đều báo.
- Không đổi luật đếm sau khi thấy kết quả; nếu phải đổi, báo cả hai bản.

`build.py` dựng lại toàn bộ thư mục (từ chối ghi đè phiếu đã có nhãn).
