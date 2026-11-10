# G2: cỡ mẫu và đồng thuận, 09/11/2026

Trạng thái: tái lập phép tính; chưa xác nhận cổng G2 đạt.

Lệnh: `PYTHONPATH=src .venv/bin/python scripts/check/audit_g2_statistics.py`.
Script chỉ đọc dữ liệu/nhãn; ghi báo cáo này và JSON kèm hash đầu vào.

## Manifest và cỡ mẫu

Main: 769 dòng/246 lineage. Silver: 859 dòng/178 lineage. Số đếm từng ô và 5 hash file phát hành khớp manifest; không sửa manifest.

Toàn bộ lượt AI gán đôi được kiểm: 460 cặp lượt gán/344 lineage riêng biệt. Không đếm snapshot trùng lần hai.
Phần sản xuất không trùng lineage: **314 lineage** = silver 168 + lo2 128 + supp18 18. Không tính các lượt gán lại hoặc pilot thành mẫu nghiên cứu mới.

| Nguồn duyệt CMT | Kết luận được nhận | Đạt | Tầng |
|---|---:|---:|---|
| silver | 168 | 80 | ai_labeled_human_confirmed_10_11 |
| lo2 | 128 | 73 | ai_labeled_human_confirmed_10_11 |
| supp18 | 15 | 12 | ai_labeled_human_approved_via_conversation |

**165 lineage đạt** (silver 80 + lo2 73 + supp18 12), vượt 130 là 35. Silver và lo2 theo phiếu xlsx CMT điền và xác nhận 10/11 (`2026-11-10_cmt_confirmed`); xác nhận qua hội thoại, không đo thời gian từng dòng. Supp18 (12) vẫn là lời duyệt qua hội thoại. Không có bằng chứng hai người độc lập kiểm bộ cuối. Chưa tính A/B gold mù.
Không đưa 314 cặp AI vào cỡ mẫu đã đạt và không coi 165 là dataset test đã phát hành.

## AC1 và p_neg trước hòa giải

Dùng hàm native `ai_labels.metric`, giữ mọi nhãn hợp lệ kể cả thiếu nguồn. Mỗi ô là AC1 / p_neg. Nhãn âm: Q1≠dung, Q2/Q3≠co, Q4≠khong; verdict=khong_dat. Không dùng nhãn hòa giải để tăng đồng thuận.

| Lượt | N cặp | Q1 | Q2 | Q3 | Q4 | Verdict |
|---|---:|---|---|---|---|---|
| pilot0 | 30 | 0.963168 / 0.666667 | 1.000000 / NA | 0.901961 / 0.833333 | 0.928826 / 0.500000 | 0.781022 / 0.750000 |
| pilot_cross_model | 14 | 1.000000 / NA | 1.000000 / NA | 0.735016 / 0.000000 | 0.653787 / 0.333333 | 0.366516 / 0.444444 |
| pilot_sonnet_partial | 14 | 0.923288 / 0.000000 | 1.000000 / NA | 0.735016 / 0.000000 | 0.885714 / 0.857143 | 0.873303 / 0.888889 |
| round2_claude | 44 | 0.973374 / 0.857143 | 0.929936 / 0.900000 | 0.945545 / 0.750000 | 0.970909 / 0.909091 | 0.867003 / 0.918919 |
| round2_codex | 44 | 0.875882 / 0.714286 | 0.875882 / 0.714286 | 0.912727 / 0.727273 | 0.940541 / 0.833333 | 0.727835 / 0.857143 |
| round2_cross_model | 44 | 0.854545 / 0.545455 | 0.841556 / 0.666667 | 0.829237 / 0.400000 | 0.886158 / 0.600000 | 0.689673 / 0.810811 |
| round3_mixed | 106 | 0.870889 / 0.705882 | 0.932982 / 0.666667 | 0.870889 / 0.705882 | 0.976820 / 0.909091 | 0.681541 / 0.824742 |
| silver01 | 18 | 0.911111 / 0.888889 | 1.000000 / 1.000000 | 0.911111 / 0.888889 | 1.000000 / NA | 0.889231 / 0.947368 |
| lo2 | 128 | 0.931564 / 0.758621 | 0.967251 / 0.333333 | 0.848789 / 0.754717 | 0.752821 / 0.465116 | 0.503322 / 0.679612 |
| supp18 | 18 | 0.941272 / 0.000000 | 1.000000 / NA | 0.875862 / 0.000000 | 0.803279 / 0.000000 | 0.538462 / 0.000000 |

**Gộp mô tả toàn bộ 314 lineage sản xuất**, gồm lo2 128. Không trộn các lượt gán lại của cùng lineage. Model khác nhau giữa các lô; số gộp không thay cổng từng lô và không phải đồng thuận người–người.

| Chỉ số | N | AC1 | p_neg | Nhãn âm (hai bên) | Cổng native |
|---|---:|---:|---:|---:|---|
| q1 | 314 | 0.903787 | 0.735632 | 87 | pass |
| q2 | 314 | 0.948733 | 0.681818 | 44 | pass |
| q3 | 314 | 0.870489 | 0.733945 | 109 | pass |
| q4 | 314 | 0.877670 | 0.625000 | 80 | pass |
| verdict | 314 | 0.607519 | 0.764045 | 267 | not_met |

## Phần gán đôi lịch sử, tách khỏi bộ cuối

| Bộ/hướng dẫn | N dòng | AC1 verdict | p_neg verdict |
|---|---:|---:|---:|
| crosscheck/1.2 | 101 | 0.863555 | 0.521739 |
| crosscheck/2.0 | 134 | 0.684381 | 0.157895 |
| crosscheck/mixed(1.2/2.0) | 65 | 0.053254 | 0.589744 |
| kiem/3.0 | 246 | 0.377277 | 0.394558 |
| kiem/3.0 calibration | 21 | 0.034483 | 0.000000 |
| pilot_T6/2.0 | 20 | 0.750520 | 0.727273 |

Test2 AI–AI riêng: 138 lineage.
- q1: AC1 0.907250, p_neg 0.476190.
- q2: AC1 0.884464, p_neg 0.222222.
- q3: AC1 0.766315, p_neg 0.133333.
- q4: AC1 0.869160, p_neg 0.000000.
- verdict: AC1 0.501449, p_neg 0.376812.

Manifest hướng dẫn 3.0: 246 dòng người–người, AC1 0,377277; p_neg 0,394558. Theo 138 lineage: AC1 0,389639; p_neg 0,483516. Không gộp hướng dẫn cũ và mới. Các bảng lịch sử chồng dòng với nhau, không cộng N.

## Power tại cỡ mẫu thật

Bộ cuối chưa có dự đoán nên **không có power thực nghiệm của bộ cuối**. Bảng dưới là phân tích độ nhạy tại N thật. Giữ hiệu và phương sai cụm từ E1 test2 đã có; không chạy hay tinh chỉnh hệ trên test. Công thức cùng `scripts/paper/paper_values.py`: delta là tỷ số tổng chênh hit/tổng dòng; SE sandwich theo lineage; SE(N)=SE(cũ)√(101/N). Power chuẩn hai phía = Φ(−z−delta/SE(N))+1−Φ(z−delta/SE(N)).

Nguồn lịch sử: 211 dòng/101 lineage; delta=0.028436019, SE=0.022161707.

| N lineage | Ý nghĩa | Power α=0,05 | Power α=0,05/6 | MDE 80%, α=0,05 |
|---|---|---:|---:|---:|
| 81 | mới đạt, CMT tự báo đọc | 0.209652 | 0.068295 | 0.069331 |
| 130 | ngưỡng G2 | 0.307362 | 0.118517 | 0.054726 |
| 165 | gồm silver nhận hàng loạt | 0.374661 | 0.159089 | 0.048576 |
| 314 | toàn bộ AI sản xuất, chưa lọc chất lượng | 0.618853 | 0.353513 | 0.035213 |

α/6 là ngưỡng đầu Holm bảo thủ cho sáu phép lịch sử ADR 0005. Không phải power sau Holm duy nhất và không khóa họ cho bộ cuối. N=314 chỉ minh họa hậu quả đếm nhầm mọi nhãn AI thành mẫu đạt. Không phải cỡ mẫu hợp lệ để kết luận. Công thức MDE dùng xấp xỉ z; cần giả định phân bố/số dòng mỗi lineage tương tự test2. Không suy power cho Accuracy hoặc TVER từ phương sai TV-Recall.

## Giới hạn và việc cần chốt

Rà 11/11 dạng sai suy luận theo skill: Simpson và base rate được xử lý bằng bảng từng lô và số nhãn âm; sinh thái, chọn mẫu và survivorship bằng tách lineage/lượt, giữ nhãn thiếu nguồn; không có mô hình điều chỉnh collider. Không suy cải thiện trước/sau từ các lô khác nhau (regression to mean). Báo mọi Q và mọi lô, giữ ngưỡng/họ (look-elsewhere, forking paths). Không kết luận nhân quả hoặc chiều nhân quả từ IAA. Phân tích power có điều kiện và sau quan sát, không phải đăng ký trước.

CMT đã xác nhận (10/11) phiếu silver và lo2; 165 đạt vượt 130. Khai rõ đây là xác nhận qua hội thoại, không đo thời gian. M2/gold mù và phân xử các ca mở vẫn cần người có thẩm quyền. Không sửa nhãn người.
