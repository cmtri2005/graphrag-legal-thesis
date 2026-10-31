# Lọc ứng viên ViLexTime bộ test 2 — hướng dẫn cố định

Bạn lọc ứng viên cho một bộ dữ liệu hỏi đáp pháp luật Việt Nam theo mốc hiệu lực. Chỉ đọc các `pack_*.jsonl` và
tài liệu trong thư mục này, cùng văn bản pháp luật gốc tra trên web. Không mở thư mục nào khác. Một số mục đã có
kết luận của người và dùng để chấm bạn; bạn không biết mục nào, đừng đoán. Gợi ý của máy (`goi_y_cho_moi`) chỉ cho
biết chỗ cần nhìn, không phải kết luận.

## Mỗi mục là gì

Một điều khoản (Điều, Khoản hoặc Điểm) cùng chuỗi phiên bản của nó. Sau bước lọc, người ta sẽ viết **một câu hỏi**
cho điều khoản này và hỏi ở các mốc trong `cac_moc`. Bạn quyết điều khoản có đáng đưa cho người gán không.

- `nhom` = `T2`: hỏi ở hai mốc phải ra hai đáp án pháp lý khác nhau. `T2 gần giống`: như T2, hai bản gần như y hệt.
- `nhom` = `T3`: qua các mốc phải ra ít nhất ba đáp án pháp lý khác nhau.
- `nhom` = `T6 đích danh` / `T6 cấp trên`: mốc trước có đáp án; mốc sau điều khoản đã bị bãi bỏ (tự nó, hoặc theo
  điều khoản cấp trên), nên đáp án đúng là "không còn quy định".

Các trường: `loi_van` (lời văn từng phiên bản và khoảng hiệu lực), `cac_phien_ban` (chuỗi phiên bản và chỗ đổi),
`van_ban_goc` (đoạn văn bản gốc), `van_ban_tac_dong` (đoạn sửa đổi hoặc bãi bỏ, điều khoản chuyển tiếp, điều hiệu
lực), `goi_y_cho_moi` (T6: chỗ nội dung có thể đã chuyển tới), `cau_dan` (câu dẫn của nút cha).

## Giữ hay loại

Giữ (`giu`) chỉ khi **đủ cả** các điều dưới đây. Thiếu một điều thì loại (`loai`) với đúng một mã. **Không chắc thì
loại**: kho ứng viên còn nhiều, câu hỏi tốt quan trọng hơn số lượng.

Mọi nhóm:

1. **Lời văn là nội dung pháp lý.** Chỉ dẫn chiếu ("thực hiện theo quy định tại Chương IV…") → `reference_only`.
2. **Chuỗi phiên bản khớp văn bản tác động.** Ngày hiệu lực của lần sửa, bãi bỏ đúng theo điều hiệu lực của văn bản
   tác động, kể cả hiệu lực tách phần ("trừ quy định tại khoản 2…"); lời văn không hỏng dấu do trích xuất ("sản
   xuât") → nếu không, `gold_wrong`.
3. **Không bị quy phạm khác đè.** Văn bản cấp cao hơn, hoặc cùng cơ quan ban hành sau, quy định khác về cùng vấn đề
   mà không sửa điều khoản này → `superseded_by_other_norm`. Luật và văn bản dưới luật khác nhau: theo Luật.
4. **Không vướng sắp xếp bộ máy 2025.** Mốc sau 01/03/2025 (bộ) hoặc 01/07/2025 (cấp huyện, tỉnh) mà lời văn còn nêu
   cơ quan, cấp, địa danh cũ chưa được sửa → `restructuring_2025`.
5. **Không có điều khoản chuyển tiếp** buộc sự việc phát sinh tại mốc theo bản cũ → `transitional_rule`.

T2, T3 thêm:

6. **Mỗi lần chuyển là thay đổi thực chất.** Chỉ đổi hình thức (hoa thường, dấu câu, đánh số) → `cosmetic_only`.
   Chỉ đổi tên cơ quan, đơn vị do sắp xếp mà nhiệm vụ giữ nguyên (Bộ Giao thông vận tải → Bộ Xây dựng; tên cơ quan
   đã chuyển từ ngày sắp xếp theo khoản 1 Điều 3 Nghị quyết 190/2025/QH15) → `rename_only`. Chỉ cập nhật dẫn chiếu
   mà văn bản đã tự áp văn bản thay thế → `auto_reference_update`. Đổi sang cơ quan khác về chức năng, hay "xã,
   phường, thị trấn" → "xã, phường, đặc khu", **là** thay đổi thật.
7. **T3: ít nhất ba trạng thái pháp lý khác nhau** sau khi bỏ các lần chuyển không thực chất; không đủ →
   `single_change`.
8. **Phần đổi hỏi được thành một câu hỏi rõ**: một nội dung cụ thể (mức tiền, thời hạn, chủ thể, điều kiện, hồ sơ…)
   mà chỉ điều khoản này trả lời. Phần đổi rời rạc hoặc vô nghĩa khi đứng riêng → `other`, ghi lý do.

T6 thêm:

9. **Văn bản bãi bỏ còn hiệu lực**, và câu bãi bỏ không giữ lại điều khoản này ("trừ điểm a") → nếu không,
   `gold_wrong`.
10. **Nội dung không chuyển sang chỗ khác.** Tìm theo thứ tự: cùng văn bản bãi bỏ ("Bổ sung…", "Sửa đổi Điều… như
    sau" cùng đợt); khoản cha, khoản anh em; văn bản khác có hiệu lực cùng ngày hoặc được dẫn tới; văn bản cấp cao
    hơn (khi đó dùng mã ở điều 3). So quy định cũ với chỗ mới theo bảy yếu tố: hành vi; đối tượng, chủ thể; điều kiện
    áp dụng; cấu trúc (chỉ đổi vị trí, thời hạn); loại chế tài, hậu quả (mức được đổi); thẩm quyền và hiệu lực kế
    thừa; dấu vết nối hai quy định. Đủ bảy → `relocated`, ghi chỗ mới. Không chắc ở yếu tố nào → `relocation_unclear`,
    ghi chỗ nghi. Rõ là không có quy định kế thừa → điều này đạt.

## Đầu ra

Một file `result.tsv` UTF-8, đúng một dòng cho mỗi `item` trong mọi gói, header chính xác:

```text
item	quyet_dinh	ma	can_cu	ghi_chu
```

- `quyet_dinh`: `giu` hoặc `loai`.
- `ma`: trống khi `giu`; khi `loai` đúng một mã trong: `reference_only`, `gold_wrong`, `superseded_by_other_norm`,
  `restructuring_2025`, `transitional_rule`, `cosmetic_only`, `rename_only`, `auto_reference_update`,
  `single_change`, `relocated`, `relocation_unclear`, `other`.
- `can_cu`: một câu trích nguyên văn từ văn bản tác động (hoặc văn bản khác) làm căn cứ; với T6 giữ lại, ghi đã tìm
  chỗ chuyển ở đâu.
- `ghi_chu`: lập luận ngắn; bắt buộc khi `loai`.

Không thêm cột, không dùng tab hoặc xuống dòng trong ô. Làm xong từng gói thì kiểm số mục và mục trùng. Không đổi
hướng dẫn giữa chừng.
