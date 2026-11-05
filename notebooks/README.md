# Gói upload Google Colab: tầng sinh câu trả lời (XN2, XN8, XN9)

Tạo 03/11/2026. Mô hình: Qwen/Qwen3-4B-Instruct-2507 (NF4, greedy, 512 token). Runtime: Colab GPU T4.

## Upload những gì

Hai phiên Colab riêng (mỗi phiên tối đa 7 file prompt):

| Phiên | Thư mục | File upload |
|---|---|---|
| 1 | `../runs/E3_test2/prompts/` | `b1.jsonl b2ctx.jsonl b7.jsonl b7pp.jsonl b5.jsonl proposed.jsonl` (227 prompt mỗi file) |
| 2 | `../runs/E3_v1/prompts/` | cùng 6 tên (211 prompt mỗi file) |

Chỉ upload các file `.jsonl`. Giữ lại các file `.export.json` ở máy này, lúc nhập kết quả cần chúng.

## Cách chạy

1. Colab mới, Runtime > GPU (T4).
2. Cell 1: `%pip -q install -U 'transformers==5.20.2' accelerate bitsandbytes`
3. Cell 2: dán toàn bộ `../scripts/eval/colab_b1_runtime.py`, chạy, chọn 6 file `.jsonl` của MỘT thư mục khi hộp upload hiện.
4. Kết quả ghi vào Google Drive: `MyDrive/vilextime_b2/<hệ>__Qwen__Qwen3-4B-Instruct-2507__<hash>.jsonl` kèm `.meta.json`.
   Có checkpoint từng dòng: nếu bị ngắt, chạy lại cell 2 với cùng file, nó tiếp tục.
5. Ước lượng: khoảng 12 giây mỗi dòng (đo 29/10), tức khoảng 45 phút mỗi hệ, khoảng 4,5 giờ cho 6 hệ. T4 miễn phí có thể ngắt giữa chừng.

## Sau khi chạy xong

Tải các file `.jsonl` (không phải `.meta.json`) từ Drive về, đưa lại cho Claude. Nhập từ gốc repo bằng:

    python scripts/eval/colab_b1.py import --prompts runs/E3_<tập>/prompts/<hệ>.jsonl --raw <file kết quả> --out runs/E3_<tập>/test/<hệ>.jsonl

Đây là hồ sơ hai vòng thử đã chạy. Trạng thái hiện tại xem [master plan](../docs/plans/active/master-plan.md).

Mỗi cấu hình chạy trên test một lần (ADR 0005). Đừng chạy lại một hệ để chọn kết quả đẹp hơn.

Đợt 2 (các hệ còn thiếu trên v1.0 và test 2): gói ở `colab_upload/round2/` (gitignore), hướng dẫn trong README của gói.
