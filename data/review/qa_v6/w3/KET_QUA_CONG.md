# Cổng tin cậy W3, chạy 22/11/2026

Lô: `gate_batch.jsonl`, gồm 12 văn bản: 6 văn bản chứa lỗi đã biết, trộn với 6 văn bản control. Hai agent
`vn-law-verifier` làm mù theo lời dặn: không mở repo, không dùng Lược đồ vbpl. Danh sách thô của agent:
`gate_agent_D01-D06.jsonl` và `gate_agent_D07-D12.jsonl`. So máy: `compare.py`, kết quả ở
`gate_batch.candidates.jsonl`.

## Kết quả: ĐẠT, 5/6 (ngưỡng ≥ 5/6, đăng ký trước S6)

| Lỗi đã biết | Văn bản tác động đúng | Agent liệt kê | touches_target | Máy gắn ứng viên |
|---|---|---|---|---|
| F016, NĐ 20/2008 Đ20 | 92/2017/NĐ-CP | có | yes | có |
| NĐ 33/2010 Đ7 K1 đ | 53/2012/NĐ-CP | có | unclear | có |
| NĐ 05/2015 Đ14 K3 b | 145/2020/NĐ-CP | có | yes | có |
| NĐ 135/2004 Đ61 K3 | 221/2013/NĐ-CP | có | yes | có |
| F019, TT 11/2021 Đ10 K5 a | 36/2026/TT-BXD | có (chỉ có nguồn thứ ba) | unclear | có |
| **F060, TT 23/2014 Đ4 K1** | 32/2016/TT-NHNN | có | **no** (sai) | không |

**Vì sao sót F060.** Agent dựa vào trang tổng hợp của caselaw. Trang này không ghi Điều 4 trong các điều bị
32/2016 sửa. Agent lại thấy VBHN ghi khoản 1 Điều 4 được sửa bởi 02/2019, mà 02/2019 chính là lần ban hành lại với
cùng lời văn. Đây đúng là kiểu lỗi đã đánh lừa kho. Bài học: nếu chỉ có nguồn thứ ba nói "không chạm" thì chưa
đủ để loại. Cách chạy toàn bộ được sửa như sau: actor nào agent ghi `no` mà chỉ dựa trên `third_party_hint` thì
máy vẫn đưa vào ứng viên, loại `weak_no` (sai lệch S8).

## Ứng viên mới, chờ người xác nhận (6)

D01 ← 36/2025 và 39/2025/TT-BNNMT; D02 ← 380/QĐ-BGTVT (quyết định công bố hệ thống hóa, gần như chắc không phải
văn bản tác động); D03 ← 02/2018/TT-NHNN; D06 ← 60/2025/TT-BXD; D08 ← 04/2016/TT-BVHTTDL.

## Thay đổi luật sau khi thấy kết quả (S7)

Lần chạy đầu có 18 ứng viên. 7 trong số đó là văn bản thay thế toàn bộ, mà kho đã thể hiện bằng ngày hết hiệu lực
của văn bản chứ không bằng sự kiện. Luật thêm vào: nếu ngày hiệu lực của actor trùng ngày bắt đầu hoặc kết thúc một
phiên bản của lineage hoặc của văn bản, thì không gắn ứng viên. Sau khi thêm còn 11 ứng viên. Cả 5 lỗi đã bắt vẫn
còn, và `test_compare.py` vẫn đạt.

## Sau S8

Với luật `weak_no`, lô này có 19 ứng viên, trong đó 8 thuộc loại `weak_no`, và F060 được gắn. Cổng vẫn báo theo luật
lúc chạy, tức 5/6. Con số 6/6 sau S8 là con số hậu nghiệm, không dùng để khẳng định cách làm tốt hơn.
