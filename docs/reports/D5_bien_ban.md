# Biên bản D5 — kiểm chéo D4 và hoà giải

Ngày lập: 19/10/2026. Nguồn số liệu: `data/review/crosscheck_result.json`
(`scripts/review/crosscheck.py kappa`), `data/review/hoa_giai_D4.tsv`
(`scripts/review/adjudicate.py`). Ánh xạ A, B sang người thật chỉ ghi trong plan, không phát hành.

## 1. Người gán, phiên bản hướng dẫn

- Hai người gán độc lập, mù với nhau, trên cùng 300 dòng (thứ tự đọc khác nhau): T2 100
  (50 thường + 50 gần giống), T3 50, T5 38, T6 112.
- Nhãn đợt trước (gán theo hướng dẫn 1.2): A 166 dòng, B 165 dòng; bản lưu
  `data/review/crosscheck_{A,B}.20261011.tsv`.
- Phần còn lại gán theo hướng dẫn 2.0, file nộp ngày 14/10, nạp ngày 19/10. B gán lại 64 dòng cũ
  theo 2.0; A giữ nhãn 1.2 trên các dòng cũ. Một ô `reasons` của B chứa lời giải thích: đã chuyển sang
  `note`, đặt mã `gold_wrong`.

## 2. Độ đồng thuận (đăng ký trước: AC1 ≥ 0,80 và p_neg ≥ 0,60; κ báo kèm)

| Phạm vi | n | Đồng ý | AC1 [KTC 95%] | p_neg | κ |
|---|---:|---:|---|---:|---:|
| **Toàn tập** | 300 | 0,750 | **0,612** [0,511; 0,697] | 0,460 | 0,323 |
| T2 | 100 | 0,780 | 0,699 [0,548; 0,809] | 0,312 | 0,210 |
| T3 | 50 | 0,700 | 0,438 [0,168; 0,677] | 0,762 | 0,357 |
| T5 | 38 | 0,842 | 0,785 [0,576; 0,935] | 0,500 | 0,433 |
| T6 | 112 | 0,714 | 0,622 [0,461; 0,748] | 0,000 | −0,018 |
| Theo lineage | 141 | 0,667 | 0,459 [0,308; 0,600] | 0,356 | 0,203 |
| Cùng HD 1.2 | 101 | 0,891 | 0,864 [0,770; 0,939] | 0,522 | 0,476 |
| Cùng HD 2.0 | 134 | 0,761 | 0,684 [0,570; 0,795] | 0,158 | 0,122 |
| Khác phiên bản | 65 | 0,508 | 0,053 [−0,190; 0,309] | 0,590 | 0,140 |

**Kết luận: chưa đạt ngưỡng đăng ký trước.** Số này được báo nguyên trạng; hoà giải không sửa nhãn thô.

Nguyên nhân lệch, đo trên 75 dòng:
- 26 dòng T6 cùng hướng dẫn 2.0: A `dat`, B `khong_dat` (25 `gold_wrong`). B ghi chỗ nội dung chuyển
  đến; A để trống `note`. A gán 111/112 dòng T6 là `dat`: bước tìm nội dung chuyển chỗ (§3, bước 2)
  gần như không được làm.
- 31 dòng lệch do một người gán theo 1.2, người kia theo 2.0.
- Phần còn lại: hiểu khác về T2/T3 (thay đổi có chạm phần được hỏi không) và câu hỏi mơ hồ.

## 3. Dòng không mù

- 19 dòng đã có nhãn từ ngoài D4 trước khi gán (`human:excel` 6, `claude-opus-5-5` 13).
- 166 (A) và 165 (B) dòng mang nhãn từ đợt 07/10, gán trước khi bộ D4 được dựng lại ngày 11/10.

## 4. Hoà giải

Quy trình thực tế, ghi đúng như đã xảy ra:
1. Bản nháp hoà giải do một trợ lý AI viết theo yêu cầu của A; 36/75 dòng tự ghi "chưa đối chiếu
   độc lập văn bản gốc".
2. `claude-opus-5-5` đối chiếu từng dòng với văn bản gốc trong kho (`data/raw`): điều khoản bị bãi bỏ
   hoặc sửa, văn bản tác động, chỗ nội dung chuyển đến, điều khoản hiệu lực và chuyển tiếp. Mỗi quyết
   định ghi dẫn chứng ở cột `note`.
3. A xác nhận ngày 19/10/2026. Cột `adjudicator` của `hoa_giai_D4.tsv` ghi đúng điều này.

Kết quả: 75 dòng → 14 `dat`, 61 `khong_dat` (`gold_wrong` 35, `group_mismatch` 20,
`question_ambiguous` 9, `unanswerable_as_asked` 6). So với bản nháp, đổi 2 dòng: một dòng T6 về `dat`
(khoản 5 Điều 8 NĐ 126/2020 trùng đáp án), một dòng T6 về `khong_dat` (định nghĩa chuyển sang khoản 2
Điều 3 Luật 134/2025/QH15). Một dòng `dat` kèm `unclear`, chuyển cố vấn luật (Luật Biên phòng 2020 so
với NĐ 34/2014).

Quy tắc áp dụng nhất quán khi hoà giải:
- đổi tên cơ quan do cơ quan kế thừa (Điều 3 NQ 190/2025/QH15) không tạo tương phản T2/T3;
- văn bản cấp cao hơn thay nội dung mà không bãi bỏ (NĐ thay TT, NQ UBTVQH thay NĐ) thì đáp án theo
  văn bản cấp cao hơn;
- điều khoản tự cập nhật dẫn chiếu được tính từ ngày văn bản được dẫn chiếu bị thay.

Sau hoà giải, 93/300 dòng D4 là `khong_dat` (T3 32, T6 29, T2 23, T5 9).

## 5. Lỗi dựng dữ liệu lộ ra, chuyển W2-09

1. Khoản có ngày hiệu lực riêng muộn hơn văn bản bị áp từ ngày văn bản (TT 17/2023/TT-BGTVT).
2. Điều khoản tự cập nhật dẫn chiếu không được tính (TT 84/2018/TT-BTC, TT 241/2017/TT-BQP).
3. Văn bản cấp cao hơn thay nội dung mà không bãi bỏ (NĐ 76/2020 với TT 41/2011; NQ 111/2025 với NĐ 33/2025).
4. Đích bãi bỏ sai (TT 01/2023/TT-BCT nhắm hợp đồng mẫu, đồ thị nhận thành định nghĩa).
5. `valid_to` sai (Điều 59 NĐ 05/2021).
6. Thay toàn bộ điều/khoản bằng văn bản sửa đổi bị bỏ sót (NĐ 115/2016 với Điều 23 NĐ 163/2013;
   TT 11/2021 với khoản 2 Điều 9 TT 21/2011).
7. Lời văn dẫn chiếu tới điều khoản cấp trên đã bị thay (TT dẫn điểm c, d khoản 3 Điều 4 NĐ 67/2014
   sau khi NĐ 17/2018 thay khoản đó): đồ thị không có quan hệ dẫn chiếu nên không thấy.
