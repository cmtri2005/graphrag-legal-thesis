# Thẻ gán nhãn ViLexTime 4.0 (bộ test 2)

**29/10/2026: CMT duyệt; chờ luật sư xem trước lô 0.** Thẻ này chỉ đổi **cách hỏi**: quy tắc vẫn là
`docs/vilextime-dinh-nghia.md` (§3 R1–R7, §6 tám điều kiện, §7 mã loại) và các kết luận ở
`docs/vilextime-annotation.md` §3 và §7. Hai tài liệu mâu thuẫn thì định nghĩa đúng.

## Bạn gán cái gì

**Một câu hỏi**, không phải một dòng. Trên màn hình có: câu hỏi; các mốc và đáp án ở mỗi mốc (chỗ khác
nhau giữa các phiên bản được tô màu, đoạn đáp án ngắn in đậm); trích văn bản tác động; link văn bản gốc.

Nhóm chỉ có ba:

| Nhóm | Câu hỏi đúng là câu hỏi mà… |
|---|---|
| **T2** | hỏi ở hai mốc thì ra **hai đáp án khác nhau**. Thẻ "gần giống": hai bản giống ≥ 90%, khác ở một con số hay một cụm |
| **T3** | hỏi qua các mốc thì ra **ít nhất ba đáp án khác nhau** |
| **T6** | mốc trước có đáp án; mốc sau điều khoản **đã bị bãi bỏ** (đích danh hoặc theo điều khoản cấp trên), nên đáp án đúng là "không còn quy định" |

## Bốn câu hỏi

Trả lời đủ bốn câu. Nhãn `dat` / `khong_dat` do máy suy ra: `dat` khi Q1 Đúng, Q2 Có, Q3 Có, Q4 Không.
Chọn câu trả lời "xấu" thì chọn thêm **một lý do** trong danh sách ngay dưới câu đó.

**Q1. Đáp án ở mỗi mốc có đúng văn bản không?** (định nghĩa §6 điều 1, 5, 8)
Mở văn bản tác động, đọc câu sửa đổi hoặc bãi bỏ và điều hiệu lực của nó. Đối chiếu cả đoạn đầy đủ
lẫn đoạn ngắn in đậm.
- ○ Đúng
- ○ Sai → `gold_wrong` (sai phiên bản, sai ngày, chữ hỏng dấu) · `reference_only` (đáp án chỉ là
  "thực hiện theo…") · `other` (đoạn ngắn thiếu ý câu hỏi hỏi; ghi ý thiếu)

**Q2. Câu hỏi có hỏi vào đúng phần tô màu không?** (§6 điều 2)
Đọc câu hỏi, che đáp án, tự hỏi: ở hai mốc, người trả lời có phải nói hai điều khác nhau không?
T6: câu hỏi phải hỏi nội dung, không chỉ hỏi "còn hay không".
- ○ Có
- ○ Không → `group_mismatch` · `cosmetic_only` (phần tô màu chỉ là hình thức) · `rename_only`
  (chỉ đổi tên cơ quan do sắp xếp, nhiệm vụ giữ nguyên) · `auto_reference_update`

**Q3. Câu hỏi có rõ không?** (§6 điều 3, 4) Rõ là: chỉ một điều khoản trả lời được, một đáp án, không
lộ ngày, số hiệu, Điều, Khoản, ký hiệu mục, không chép sẵn đáp án.
- ○ Có
- ○ Không → `question_ambiguous` · `unanswerable_as_asked` · `question_leaks`

**Q4. Có quy định nào khác đang thay cho đáp án này không?** (§6 điều 6, 7)
T2, T3: văn bản cấp cao hơn hoặc ban hành sau quy định khác mà không sửa điều khoản này; mốc sau sắp
xếp bộ máy 2025 mà đáp án còn nêu cơ quan, cấp cũ; điều khoản chuyển tiếp. T6: nội dung bị bãi bỏ có
chuyển sang chỗ khác không (bảy yếu tố, hướng dẫn 3.0 bước 7).
- ○ Không
- ○ Có → `superseded_by_other_norm` · `restructuring_2025` · `transitional_rule` · `relocated`
  (ghi chỗ mới)
- ○ Không chắc → `relocation_unclear` (ghi chỗ nghi)

## Dẫn chứng (bắt buộc, thiếu thì phiếu không lưu)

- Dán **một câu trích nguyên văn** từ văn bản tác động mà bạn đã đọc.
- T6, Q4 = Không: ghi đã tìm ở đâu ("cùng văn bản bãi bỏ; khoản anh em; …").
- Phân vân: vẫn chọn, ghi `[phân vân] …` ở ghi chú để hỏi luật sư.

## Đồng thuận

AC1 và p_neg đo trên **từng câu Q1–Q4** và trên nhãn suy ra; ngưỡng AC1 ≥ 0,80 và p_neg ≥ 0,60.
A và B gán độc lập, không trao đổi. Dòng lệch do luật sư chốt, không dùng AI.

## Hỏi đáp (sổ quyết định của thẻ 4.0)

(Lô 0 ghi kết luận ở đây: ngày, người chốt, câu hỏi chung, kết luận.)
