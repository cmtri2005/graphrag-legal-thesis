# Hướng dẫn gán nhãn ViLexTime

**Phiên bản 4.0** (05/11/2026). **Chờ luật sư xem trước lô thử.**
Hướng dẫn này cài đặt `docs/vilextime-dinh-nghia.md`; hai tài liệu mâu thuẫn thì định nghĩa đúng.
⚖ đánh dấu quy tắc pháp lý luật sư đã đồng ý (21/10/2026).
Bản 3.0 đọc ở commit `32c66ed`; đó là bản đã dùng cho v1.0.
Bản 1.2 và 2.0 xem trong lịch sử git; mỗi nhãn ghi phiên bản đã dùng ở `guideline_version`.
Bản 4.0 gộp hướng dẫn 3.0 và thẻ 4.0, chỉ đổi cách hỏi, không đổi quy tắc.
Căn cứ: định nghĩa §3 R1–R7, §6 tám điều kiện, §7 mã loại; sổ quyết định ở §7 dưới đây.

## 1. Bạn gán cái gì

**Một câu hỏi**, không phải một dòng. Trên màn hình có: câu hỏi; các mốc và đáp án ở mỗi mốc (chỗ khác
nhau giữa các phiên bản được tô màu, đoạn đáp án ngắn in đậm); trích văn bản tác động; link văn bản gốc.

Nhóm chỉ có ba:

| Nhóm | Câu hỏi đúng là câu hỏi mà… |
|---|---|
| **T2** | hỏi ở hai mốc thì ra **hai đáp án khác nhau**. Thẻ "gần giống": hai bản giống ≥ 90%, khác ở một con số hay một cụm |
| **T3** | hỏi qua các mốc thì ra **ít nhất ba đáp án khác nhau** |
| **T6** | mốc trước có đáp án; mốc sau điều khoản **đã bị bãi bỏ** (đích danh hoặc theo điều khoản cấp trên), nên đáp án đúng là "không còn quy định" |

Mỗi mốc gồm ngày `as_of` và đáp án chuẩn, tức nội dung có hiệu lực tại mốc đó.
Máy dựng đáp án, model viết nháp câu hỏi.

> Một luật sư đọc câu hỏi, biết ngày `as_of` ở mỗi mốc, tra đúng văn bản. Người đó có trả lời **đúng bằng
> đáp án ở từng mốc** không, và chỉ trả lời được **một cách** không?

Ba quy tắc nền:

1. **`as_of` là ngày tính hiệu lực pháp lý** ⚖. Đáp án là phiên bản có hiệu lực tại `as_of` theo
   khoảng hiệu lực do chính các văn bản quy định, kể cả hiệu lực trở về trước. Sự việc coi như
   phát sinh tại `as_of`. Điều khoản chuyển tiếp chỉ giữ bản cũ cho việc đang thực hiện thì không
   làm đổi đáp án.
2. **Câu hỏi hỏi nội dung, không hỏi vị trí.** Đáp án là quy phạm đang điều chỉnh nội dung được hỏi
   tại `as_of`. Chỉ đổi mức phạt thì vẫn là cùng một quy phạm.
3. **Câu dẫn là một phần của đáp án.** Mục trong danh sách phải đọc cùng câu dẫn của nút cha tại
   `as_of` (cột `lead_in`). Ở nghị định xử phạt, mức phạt nằm ở câu dẫn của khoản.

## 2. Điền phiếu

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
chuyển sang chỗ khác không (bảy yếu tố, §3 Q4, Bước 7).
- ○ Không
- ○ Có → `superseded_by_other_norm` · `restructuring_2025` · `transitional_rule` · `relocated`
  (ghi chỗ mới)
- ○ Không chắc → `relocation_unclear` (ghi chỗ nghi)

### Dẫn chứng (bắt buộc, thiếu thì phiếu không lưu)

- Dán **một câu trích nguyên văn** từ văn bản tác động mà bạn đã đọc.
- T6, Q4 = Không: ghi đã tìm ở đâu ("cùng văn bản bãi bỏ; khoản anh em; …").
- Phân vân: vẫn chọn, ghi `[phân vân] …` ở ghi chú để hỏi luật sư.

## 3. Kiểm theo bốn câu

Kiểm đủ tám bước dưới bốn câu Q1–Q4. Ở mỗi bước, kiểm các mốc có trên trang.
Bước nào không đạt thì chọn câu trả lời và một lý do ở Q tương ứng theo §2.
Mã `transitional_rule` ở Bước 1 được ghi ở Q4 theo §2.
Nhãn `dat` / `khong_dat` do máy suy ra theo §2.
Các bước có nhắc T1, T4, T5 là quy tắc giữ từ bản 3.0; bộ đang gán chỉ có T2, T3, T6.

### Q1. Đáp án ở mỗi mốc có đúng văn bản không?

**Bước 1. Đáp án đúng phiên bản có hiệu lực tại `as_of`.** Đối chiếu cả lời văn và câu dẫn với văn
bản gốc, văn bản tác động, các mốc và đáp án trên trang (chỗ khác nhau giữa các phiên bản được tô màu,
đoạn đáp án ngắn in đậm).
- Sai phiên bản, hoặc lời văn thiếu hay thừa so với văn bản gốc → `gold_wrong`.
- Văn bản gốc trên cổng đã là lời văn sau sửa, nên vế trước không đúng → `gold_wrong`.
- Văn bản tác động có hiệu lực tách phần ("trừ quy định tại khoản 2, 3 Điều này", "các quy định
  về … có hiệu lực kể từ ngày ký"): đọc điều hiệu lực của nó. Lần sửa ở mốc đang kiểm thuộc phần ngoại lệ
  → `gold_wrong`, ghi ngày đúng. Danh sách văn bản cần đọc: `data/review/hieu_luc_tach.tsv`.
- Chữ hỏng dấu hoặc ký tự ẩn do trích xuất ("sản xuât", "giây phép") → `gold_wrong`, ghi chữ đúng theo
  Công báo. Không sửa tay lời văn. Danh sách chỗ nghi: `data/review/chu_hong_dau.tsv` (khoảng một nửa là
  chữ đúng nhưng hiếm, như "dược điển").
- T5a (hồi tố: mốc nằm giữa ngày hiệu lực và ngày ký của văn bản sửa): đáp án là **bản mới**. Việc
  văn bản có hồi tố hay không đã được luật sư chốt (`data/review/t5_documents.tsv`, 12/10/2026),
  người gán không xét lại.
- T5b (đã ký, chưa có hiệu lực): đáp án là **bản cũ**. Đối chiếu ngày ký, ngày hiệu lực ghi ở phiếu
  với văn bản.
- T6: văn bản bãi bỏ phải còn hiệu lực. T6a: câu bãi bỏ nêu đích danh điều khoản. T6b: câu bãi bỏ
  nêu điều khoản cấp trên; nếu câu đó giữ lại điều khoản này (ví dụ "trừ điểm a") → `gold_wrong`.
- Điều khoản chuyển tiếp giữ bản cũ cho đúng quan hệ câu hỏi tự nêu, hoặc buộc chính sự việc phát sinh
  tại `as_of` theo bản cũ → `transitional_rule`, ghi Điều chuyển tiếp ở `note`.

**Bước 5. Đáp án là nội dung pháp lý** (R5). Đáp án chỉ dẫn chiếu ("thực hiện theo quy định tại
Chương IV Thông tư này") → `reference_only`, kể cả khi khớp lời văn.

**Bước 8. Đáp án ngắn đúng và đủ.** Sai, hoặc thiếu ý mà câu hỏi hỏi → `other`. Ghi ở `note` ý bị
thiếu và đoạn đúng **trích nguyên từ đáp án**; không viết lời mới. Nếu lỗi thật ra nằm ở câu hỏi
(câu hỏi rộng hơn đáp án, hoặc vấn đề còn được quy định ở văn bản khác) thì dùng mã của bước 3
hoặc bước 6.

### Q2. Câu hỏi có hỏi vào đúng phần tô màu không?

**Bước 2. Câu hỏi chạm đúng chỗ đổi** (T2–T6).
- T2, T4: một câu hỏi, hai mốc, kiểm cả hai mốc. Hai mốc trả lời như nhau →
  `group_mismatch`. Ở T4, chỗ đổi thường chỉ là một con số hay một cụm từ; câu hỏi phải hỏi vào
  đúng chỗ đó.
- T3: câu hỏi phải ra ít nhất 3 đáp án khác nhau qua các mốc; chỉ ra 2 → `group_mismatch`. Lần đổi
  chỉ về tên hay hình thức không tính là trạng thái mới.
- T5a, T5b: câu hỏi phải hỏi vào phần thật sự đổi → nếu không, `group_mismatch`.
- T6: câu **chỉ** hỏi có/không → `group_mismatch`. Câu ghép có vế hỏi nội dung thì chấm theo vế đó.
- **Không** tính là thay đổi (R1) ⚖: chỉ đổi hình thức → `cosmetic_only`; chỉ đổi tên cơ quan, đơn
  vị do sắp xếp bộ máy mà nhiệm vụ giữ nguyên (Bộ Giao thông vận tải → Bộ Xây dựng; Bộ Tài nguyên và
  Môi trường → Bộ Nông nghiệp và Môi trường; căn cứ khoản 1 Điều 3 Nghị quyết 190/2025/QH15) →
  `rename_only`; chỉ cập nhật dẫn chiếu mà văn bản đã quy định tự áp → `auto_reference_update`.
- **Có** tính là thay đổi: chuyển sang cơ quan khác về chức năng (không phải cơ quan kế thừa); thay
  danh sách đơn vị hành chính không tương ứng 1-1, ví dụ "xã, phường, thị trấn" → "xã, phường, đặc
  khu" (cấp xã không còn thị trấn, Luật 72/2025/QH15 Điều 1 khoản 1 điểm b).

### Q3. Câu hỏi có rõ không?

**Bước 3. Câu hỏi chỉ khớp một điều khoản và trả lời được bằng đáp án này, một cách.**
- Với mục trong danh sách (kể cả T1), câu hỏi phải ghim đúng mục. Câu hỏi chung mà nhiều khoản cùng
  trả lời được → `question_ambiguous`.
- Hỏi "khi nào" mà đáp án không có thời hạn, hỏi "ai" mà đáp án không nêu chủ thể →
  `unanswerable_as_asked`.

**Bước 4. Câu hỏi không để lộ** ngày, số hiệu văn bản, Điều, Khoản, ký hiệu mục ("loại c)"), và không
chép sẵn đáp án. Không đạt → `question_leaks`. Câu hỏi chứa sẵn vế trước của đáp án thì Q3 Không khi kiểm
mốc trước. Câu hỏi nêu sẵn cụm của bản cũ mà bản mới đã đổi (ví dụ "xã, phường, thị trấn") thì Q3 Không
ở cả hai mốc.

### Q4. Có quy định nào khác đang thay cho đáp án này không?

**Bước 6. Không có quy phạm khác đè lên, không vướng sắp xếp bộ máy.**
- ⚖ Văn bản cấp cao hơn, hoặc văn bản cùng cơ quan ban hành sau, quy định khác về cùng vấn đề mà
  không sửa điều khoản này → `superseded_by_other_norm` (R3).
- ⚖ `as_of` sau ngày sắp xếp (bộ: 01/03/2025; cấp huyện, tỉnh: 01/07/2025) mà đáp án vẫn nêu cơ
  quan, cấp, địa danh cũ chưa được sửa lời văn → `restructuring_2025` (R4).

**Bước 7. (T6) Nội dung bị bãi bỏ còn ở đâu** ⚖ (R2). Luôn làm bước này.
Tìm theo thứ tự: (a) cùng văn bản bãi bỏ, ở các cụm "Bổ sung…", "Sửa đổi Điều… như sau" cùng đợt;
(b) khoản cha, khoản anh em của cùng điều; (c) văn bản khác có hiệu lực cùng ngày hoặc được dẫn
tới; (d) văn bản cấp cao hơn quy định cùng vấn đề, khi đó dùng `superseded_by_other_norm`.
Rồi so quy định cũ với chỗ mới theo bảy yếu tố (luật sư xác nhận 12/10/2026). Chỉ xét **phần câu hỏi hỏi**: chỗ mới đổi phần câu
hỏi không hỏi (ví dụ thẩm quyền cho loại hàng khác) thì không làm hỏng yếu tố.

| # | Yếu tố | Đạt khi |
|---|---|---|
| 1 | Hành vi | giữ nguyên về bản chất |
| 2 | Đối tượng, chủ thể | giữ nguyên; địa danh chỉ đổi tên do sáp nhập, phạm vi giữ nguyên, vẫn đạt |
| 3 | Điều kiện áp dụng | giữ nguyên |
| 4 | Cấu trúc quy định | chỉ đổi vị trí, thời hạn |
| 5 | Chế tài, hậu quả pháp lý | cùng loại chế tài; mức được đổi. Đổi loại chế tài hay thêm hình thức phạt bổ sung thì không đạt |
| 6 | Thẩm quyền, hiệu lực kế thừa | cùng cơ quan ban hành (hoặc cơ quan kế thừa sau sắp xếp), hiệu lực pháp lý không thấp hơn |
| 7 | Dấu vết chuyển tiếp | có dấu vết nối hai quy định: cùng đợt "Bãi bỏ… Bổ sung…", câu "thay thế", điều khoản chuyển tiếp |

- Đạt đủ bảy yếu tố → `relocated`, ghi chỗ mới (văn bản, vị trí, trích đoạn).
- Không chắc ở yếu tố nào, hoặc yếu tố 7 không có dấu vết → `relocation_unclear`, ghi chỗ nghi.
- Không có quy định kế thừa, hoặc yếu tố 1–6 rõ ràng không đạt → bước này đạt.
- Khoảng trống: khoản cũ hết hiệu lực từ ngày A, chỗ mới có hiệu lực từ ngày B sau A. Hỏi giữa A và B
  thì đáp án rỗng là đúng. Trước khi kết luận có khoảng trống, kiểm: chuyển tiếp có giữ khoản cũ
  không; văn bản khác có quy định cùng vấn đề trong giai đoạn đó không; quy định mới có hồi tố về A
  không; A và B có thật khác nhau không.

**Ba lỗi hay gặp.**
- Gán `dat` khi mới nhìn qua. Ở lô 0, cả 12 dòng gán như vậy đều bị luật sư chốt `khong_dat`. Dòng
  nào cũng phải mở văn bản tác động và ghi đã thấy gì.
- Bỏ bước 7 ở T6. Đợt D4 có 26 dòng lệch vì một người gán `dat` mà không tìm chỗ chuyển đến.
- So câu hỏi với cả điều khoản thay vì với chỗ đổi (bước 2).

## 4. Ví dụ (đã đối chiếu văn bản gốc ngày 20/10/2026)

| Nhóm | Dòng | Nhãn | Vì sao |
|---|---|---|---|
| T2 | TT 12/2017/TT-BGTVT điểm b khoản 2 Điều 28, hỏi "phải lưu trữ những bài sát hạch và biên bản nào", mốc 30/11/2019 và 01/12/2019 | `dat` cả hai | TT 38/2019 thêm "bài sát hạch lái xe trên phần mềm mô phỏng các tình huống giao thông": câu hỏi chạm đúng phần đổi |
| T2 | TT 52/2022/TT-BGTVT khoản 2 Điều 4, "giấy chứng nhận loại tàu bay được cấp, công nhận theo bộ quy chế do bộ nào ban hành", mốc 30/06/2025 và 01/07/2025 | `khong_dat`: `rename_only` | Khoản 1 Điều 29 TT 09/2025/TT-BXD chỉ thay "Bộ Giao thông vận tải" bằng "Bộ Xây dựng". Từ 01/03/2025 tên cơ quan đã chuyển theo khoản 1 Điều 3 NQ 190/2025/QH15, nên hai mốc cùng một đáp án pháp lý |
| T3 | TT 12/2017/TT-BGTVT khoản 13 Điều 33, "giấy phép lái xe hợp lệ khi đáp ứng điều kiện gì về cơ quan cấp và thông tin trên giấy phép" | `dat` | Ba đáp án khác nhau: trước 01/12/2019; đến 31/05/2024; từ 01/06/2024 thêm VNeID |
| T4 | NĐ 355/2025/NĐ-CP điểm n khoản 1 Điều 30, "được cấp dầu gội đầu với định lượng bao nhiêu mỗi năm" | `dat` | 800 ml → 1.000 ml từ 01/07/2026 (khoản 5 Điều 43 NĐ 170/2026) |
| T5a | NĐ 242/2025/NĐ-CP điểm c khoản 3 Điều 33, mốc 03/02/2026 | `dat` | NĐ 119/2026 ký 03/04/2026 nhưng có hiệu lực 01/01/2026: đáp án là bản mới |
| T5b | Như T4, mốc 01/06/2026 | `dat` | NĐ 170/2026 đã ký 15/05/2026 nhưng chưa có hiệu lực: đáp án 800 ml |
| T6a | NĐ 67/2013/NĐ-CP điểm c khoản 3 Điều 26 (diện tích 03 m² khi bán lẻ thuốc lá), mốc 10/08/2021 | `dat` | Khoản 4 Điều 2 NĐ 106/2017 bãi bỏ; không có quy định kế thừa |
| T6b | NĐ 23/2016/NĐ-CP điểm a khoản 1 Điều 23 (trình độ cán bộ quản lý vận hành cơ sở hỏa táng), mốc 09/06/2026 | `dat` | Khoản 2 Điều 138 NĐ 14/2026 bãi bỏ khoản 1 (cấp trên); không có quy định kế thừa |
| T6 | NĐ 37/2017/NĐ-CP Điều 8 khoản 2 (điều kiện phòng cháy khi khai thác cảng biển), mốc sau 24/10/2018, đáp án rỗng | `khong_dat`: `relocated` | Cùng NĐ 147/2018 viết lại Điều 7 và đưa vào khoản 2 "Đáp ứng các điều kiện về an toàn, vệ sinh lao động, phòng, chống cháy, nổ…". `note`: khoản 2 Điều 7 NĐ 37/2017 (sửa bởi khoản 3 Điều 5 NĐ 147/2018) |
| T6 | TT 41/2011/TT-BCA khoản 1 Điều 4 (hồ sơ giấy thông hành sang Lào), mốc 14/11/2021 | `khong_dat`: `superseded_by_other_norm` | Từ 01/07/2020 NĐ 76/2020/NĐ-CP (cấp cao hơn) quy định tờ khai M01 thay mẫu TK7 |
| — | "…hình thức xử phạt chính loại c) được quy định như thế nào?" | `khong_dat`: `question_leaks` | Ký hiệu mục là vị trí, không phải nội dung |
| — | "Những hành vi nào bị phạt tiền từ 20.000.000 đồng đến 40.000.000 đồng?" (đáp án: một mục b) | `khong_dat`: `question_ambiguous` | Đáp án đúng là cả danh sách |

## 5. Quy trình

1. **Công cụ.** A và B gán trên trang web. Trang lưu sau mỗi câu và ghi thời gian từng câu.
   Hai người nhận cùng một bộ dẫn chứng do máy chuẩn bị; máy không điền nhãn.
2. **Độc lập.** A và B gán độc lập, không trao đổi trong lúc làm. Không hỏi bất kỳ AI nào về câu
   đang gán. Người gán không thấy nhãn, gợi ý hay ghi chú của AI, và không thấy kết quả hệ.
   Tên thật chỉ ghi ở plan.
3. **Lô 0 hiệu chuẩn** (lô thử). Hai người làm độc lập và gửi trước, rồi cùng luật sư xem các câu
   lệch. Kết luận dạng quy tắc chung ghi vào §7 trước khi làm lô 1. Lô 0 không tính vào AC1.
4. **Lô 30–50 câu.** Sau lô 3, 6, 9, 12, 15 đo đồng thuận trên các câu chung. Dưới ngưỡng thì hiệu
   chuẩn lại trên câu mới, **không sửa nhãn đã gán**: nhãn thô chính là số đo đồng thuận.
5. **Một phiên bản hướng dẫn cho mọi nhãn.** Mọi nhãn trong đợt này dùng bản 4.0.
   Không tái dùng nhãn cũ cho câu chưa được kiểm theo bản 4.0.
6. **Phân vân.** Vẫn chọn câu trả lời Q1–Q4, ghi `[phân vân] …` ở `note` để hỏi luật sư.
7. **Đồng thuận.** AC1 và p_neg đo trên **từng câu Q1–Q4** và trên nhãn suy ra; ngưỡng AC1 ≥ 0,80
   và p_neg ≥ 0,60; κ báo kèm; báo theo nhóm và theo phiên bản hướng dẫn.
   Q4: AC1 giữ trên ba mức. Khi tính p_neg, `Có` và `Không chắc` gộp thành một mức bất lợi
   (Không so với {Có, Không chắc}); căn cứ ADR 0005, điều chỉnh 03/11/2026 mục 3.
   AC1 được chọn làm chỉ số chính **sau lượt pilot ngày 07/10/2026**, vì nghịch lý
   prevalence của κ; đây không phải chỉ số đăng ký trước.
8. **Hòa giải.** Dòng lệch do người thứ ba là luật sư quyết, không dùng AI; cột `adjudicator` ghi
   đúng người quyết. Không có phiếu AI. Nhãn thô của từng người giữ nguyên và được phát hành
   (ADR 0003 §9).
9. **Dòng `khong_dat` sau hòa giải bị loại** bằng mã tương ứng, hoặc thay bằng câu dự trữ. Không sửa
   đáp án chuẩn bằng tay.

## 6. Nhãn do model gán

Nhãn model **không được tính là kiểm định**. Đo ngày 19/10/2026: trên 13 dòng D4 có nhãn model, chỉ
7 dòng khớp kết luận cuối của người, và model gán `khong_dat` ít hơn người nhiều lần.
Dòng chỉ có nhãn model là dòng chưa kiểm (`not_verified`) và không vào tập test do người kiểm.
Quy trình hiện tại theo §5: người gán không thấy nhãn hay gợi ý của AI.

### Lịch sử v1.0

Các đoạn dưới đây ghi lại quy trình v1.0, không áp dụng cho đợt người gán theo §5.
Đọc đầy đủ ở commit `32c66ed` và định nghĩa §6.

Nhãn model chỉ
dùng để xếp thứ tự dòng cần người xem trước. Nhãn model cũ ở `data/review/labels.tsv` giữ nguyên để
phân tích phụ, có ghi `labeler`. Dòng chỉ có nhãn model là dòng chưa kiểm (`not_verified`) và không
vào tập test.

**Ngoại lệ từ 26/10/2026 (CMT):** nhãn của agent kiểm (từ 27/10 là Codex, ghi ở `labeler`; có tra văn bản gốc, trích dẫn
nguồn) được tính là kiểm định cho dòng test khi đã qua kiểm chứng ở mục 6 của định nghĩa: gán mù
trên dòng có nhãn người, đạt AC1 ≥ 0,80 và p_neg ≥ 0,60, và luật sư kiểm mẫu 50 dòng. Nhãn agent ở
`data/review/kiem_agent.tsv`, không trộn vào phiếu A hay B.

**Giới hạn từ 28/10/2026 (CMT):** agent không đạt AC1 0,80 ở mức toàn tập (0,721), nên nhãn agent chỉ
có giá trị ở nhóm T1 và T6; xem mục 6 của định nghĩa.

Lớp phụ, chỉ có ở `data/review/labels.tsv` và không tính vào đồng thuận: `meta_issues` ghi lỗi siêu
dữ liệu không làm sai đáp án (`valid_to_wrong` · `valid_from_wrong` · `group_wrong` ·
`citation_path_wrong` · `doc_number_wrong` · `lead_in_wrong` · `other`).

## 7. Hỏi đáp (sổ quyết định)

Mỗi mục ghi: ngày, người chốt, câu hỏi chung (không nêu dòng gán đôi cụ thể), kết luận và chỗ đã đưa
vào hướng dẫn. Kết luận chỉ làm rõ cách áp quy tắc đã có. Quy tắc mới thì phải sửa định nghĩa và
tăng phiên bản hướng dẫn.

- **24/10/2026, luật sư, lô 0** (`data/review/hoa_giai_lo0_chot.xlsx`). 12/21 dòng lệch; cả 12 là một người
  gán `dat` không ghi `note`, người kia gán `khong_dat` kèm lý do. Luật sư chốt cả 12 là `khong_dat`.
  Sáu kết luận:
  1. T6 xét bảy yếu tố trong phạm vi câu hỏi: điều khoản sang văn bản mới mà nội dung được hỏi giữ
     nguyên là `relocated` (bước 7).
  2. Đáp án chỉ dẫn chiếu là `reference_only`, kể cả khi khớp lời văn (bước 5).
  3. "Thị trấn" → "đặc khu" không phải `rename_only`; câu hỏi nêu sẵn cụm của bản cũ là
     `question_leaks` ở cả hai mốc (bước 2, bước 4).
  4. Đáp án ngắn thiếu ý là `other`; không viết lời mới. Lỗi ở câu hỏi thì dùng mã của câu hỏi (bước 8).
  5. Văn bản tác động có hiệu lực tách phần có thể làm mốc sai; thuộc phần ngoại lệ là `gold_wrong` (bước 1).
  6. Chữ hỏng dấu do trích xuất là `gold_wrong`; không sửa tay (bước 1).
- **26/10/2026, luật sư, lô 1–18** (`data/review/hoa_giai_kiem.xlsx`). 89 dòng lệch. Luật sư đọc phiếu
  kiểm trước của Claude (`data/review/hoa_giai_kiem_claude.tsv`) và đồng ý, nên lần hòa giải này **có AI
  hỗ trợ**, khác §5 mục 8; biên bản D5 phải ghi rõ. Hai kết luận:
  1. T6, dòng mốc trước ngày bãi bỏ, đáp án đúng tại mốc: `dat`, kể cả khi nội dung sau đó chuyển sang
     văn bản khác. `group_mismatch` ở T6 chỉ dùng cho câu hỏi có/không; chuyển chỗ xét ở dòng mốc sau (bước 7).
  2. Luật và văn bản dưới luật cùng quy định vấn đề được hỏi tại `as_of`: đáp án theo Luật; văn bản
     dưới luật khác Luật → `superseded_by_other_norm` (bước 7d).
  3. Câu hiệu lực "áp dụng từ năm ngân sách X" là hiệu lực trở về trước, tính từ 01/01/X (Luật
     17/2008/QH12 Điều 79, khoản 1 Điều 83; năm ngân sách theo Luật 01/2002/QH11 Điều 14). Mốc trong năm X
     trước ngày hiệu lực lấy đáp án bản mới, như T5a (bước 1).
- **D4, biên bản D5 §2.** Ba bài học: luôn làm bước 7 ở T6; dùng một phiên bản hướng dẫn cho mọi
  nhãn (§5 mục 5); so câu hỏi với chỗ đổi (bước 2).

### Kết luận của lô thử bản 4.0

(Lô 0 ghi kết luận ở đây: ngày, người chốt, câu hỏi chung, kết luận.)
