# Kết quả đọc mù ngẫu nhiên 30 dòng (22/11/2026)

Luật đếm theo README, chốt trước khi mở đáp án. Luật quyết định nêu trước khi mở: 0–1 lỗi kho thì nộp DiB kèm
mục giới hạn; từ 2 lỗi trở lên thì đọc nốt 64 lineage trước khi nộp.

## Trạng thái phiếu
- **A:** `import` đủ 30/30, `reveal` xong (`gold_A.reveal.tsv`, câu trả lời khóa ở sha256 `b8cb1bfbfb64…`).
  A không ghi số phút.
- **B:** lần nộp đầu bị `import` từ chối vì R29 thiếu `noi_dung`. B nộp lại ngày 22/11; so máy với bản trước thì chỉ
  R29 đổi (`noi_dung`, `ghi_chu`). `import` đủ 30/30, `reveal` xong (`gold_B.reveal.tsv`, khóa ở sha256
  `9c671e8adc32…`).

## So với kho (so máy: hiệu lực khớp, và lời văn người đọc dán nằm trong lời văn kho sau chuẩn hóa)
| | Hiệu lực khớp | Lời văn khớp | Văn bản áp dụng khớp A |
|---|---|---|---|
| A | 30/30 | 30/30 | — |
| B | 30/30 | 29/30 | 30/30 |

**Phân xử R09** (B ghi "GDP", kho và A ghi "GPP"): điểm c khoản 2 Điều 13 Thông tư 03/2018/TT-BYT, bản ban hành,
ghi nguyên văn "Đã được đào tạo, huấn luyện về GPP, thanh tra, đánh giá GPP và nắm vững các nguyên tắc, tiêu chuẩn
GPP;". Ngày hỏi 24/07/2020 là trước khi Thông tư 09/2020/TT-BYT có hiệu lực (25/07/2020). Vậy kho đúng, B sai
(`annotator_error`).
Ghi chú phụ: lời văn của kho ở dòng này lặp cụm "và nắm vững các nguyên tắc, tiêu chuẩn GPP" hai lần. Đây là lỗi
ghép chữ, không phải lỗi phiên bản. Câu hỏi này cũng bám vào chỗ văn bản gốc viết nhầm GPP, nên ghi nhận như một vấn
đề về chất lượng câu hỏi.

## Số liệu
- **Lỗi kho: 0/30.** Khoảng Wilson 95%: 0–11,4%.
- Suy cho cả bộ: lỗi ở 105 lineage đã đọc đều đã sửa, nên lỗi còn lại ≤ (94/199) × 11,4% ≈ **5,4%** (cận trên 95%).
- **Đồng thuận A–B:** hiệu lực 30/30 (cả 30 dòng đều là "còn", nên κ không xác định); nội dung 29/30 (96,7%). Dòng lệch duy nhất là lỗi của người đọc.

## Giới hạn của mẫu
- Không có dòng bãi bỏ nào, vì cả 23 lineage bãi bỏ đã đọc mù từ trước. Mẫu gồm 15 two_versions, 14 control,
  1 multi_versions.
- Người đọc và kho cùng đọc lời văn từ vbpl. Sửa đổi mà vbpl không ghi thì phép đo này không bắt được.
- A là đồng tác giả, không phải người ngoài.
