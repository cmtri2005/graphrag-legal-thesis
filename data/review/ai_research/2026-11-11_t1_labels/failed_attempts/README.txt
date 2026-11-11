attempt1 b_chunk01 truncated mid-line (8/30 lines, no closing fence/provenance); rerun once per contract

b_chunk02 attempt1 (11/11): 30/30 dòng giống hệt, provenance ghi WebFetch gateway trả Internal Error cho 30 URL -> lỗi transport, không phải nhãn. Gateway kiểm lại trả 200, chạy lại chunk02 một lần (quyết định phiên điều phối).
b_chunk02 attempt2 (11/11): 31 dòng, trùng e74e9512 với hai nhãn mâu thuẫn, 45feb198 Q3=co kèm mã -> lỗi định dạng, không sửa tay; chạy lại lần cuối (attempt3).
b_chunk02 attempt3 (11/11): khối jsonl rỗng, chỉ có provenance -> thất bại. Dừng, chờ CMT quyết.
