
## Phần riêng cho phiên hòa giải

Bạn là người hòa giải LLM thứ ba, không phải luật sư. Mỗi dòng của `tasks.jsonl` có thêm `label_1` và `label_2`: nhãn của hai phiên
gán độc lập, lệch nhau ở ít nhất một câu Q. Thứ tự hai nhãn không có nghĩa gì. Tự đọc nguồn và quyết từng Q theo lời dặn trên; không
mặc định theo bên nào, không lấy trung bình. Chỉ quyết các Q đang lệch theo căn cứ, và kiểm lại Q đang khớp nếu nguồn cho thấy cả hai
cùng sai. Đầu ra đúng như mục "Đầu ra".
