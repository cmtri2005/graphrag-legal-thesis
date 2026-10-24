# Hướng dẫn gán nhãn ViLexTime

**Phiên bản 3.0** (20/10/2026; viết gọn lại 24/10/2026, không đổi quy tắc). Hướng dẫn này cài đặt
`docs/vilextime-dinh-nghia.md`; hai tài liệu mâu thuẫn thì định nghĩa đúng. ⚖ đánh dấu quy tắc
pháp lý luật sư đã đồng ý (21/10/2026). Bản 1.2 và 2.0 xem trong lịch sử git; mỗi nhãn ghi phiên
bản đã dùng ở cột `guideline_version`.

## 1. Bạn kiểm cái gì

Mỗi dòng gồm một câu hỏi, một mốc `as_of` và đáp án chuẩn, tức nội dung có hiệu lực tại mốc đó.
Máy dựng đáp án, model viết nháp câu hỏi. Mỗi dòng bạn trả lời một câu:

> Một luật sư đọc câu hỏi, biết ngày `as_of`, tra đúng văn bản. Người đó có trả lời **đúng bằng
> cột đáp án** không, và chỉ trả lời được **một cách** không?

Có thì gán `dat`. Không thì gán `khong_dat` kèm mã lý do.

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

| Ô | Điền gì | Dòng nào |
|---|---|---|
| `verdict` | `dat` hoặc `khong_dat`. Đồng thuận tính trên ô này | mọi dòng |
| `reasons` | một hoặc nhiều mã ở bảng dưới, cách nhau bằng dấu phẩy | chỉ dòng `khong_dat` |
| `note` | tự do; phân vân thì ghi `[phân vân] …` | bắt buộc với `gold_wrong`, `relocated`, `superseded_by_other_norm`, `other` |
| `da_xem_van_ban_tac_dong` | số hiệu các văn bản tác động đã xem, hoặc "không có" | mọi dòng |
| `cham_lan_sua` | những ngày chuyển mà câu hỏi chạm tới | T2, T3, T4 |
| `noi_dung_con_o_dau` | "không có", chỗ mới (văn bản, Điều, Khoản), hoặc "không chắc" | T6 |
| `phut` | số phút đã dùng (số nguyên) | mọi dòng |

Bốn ô cuối là dẫn chứng để dòng vào tập test, nên chỉ bắt buộc với người kiểm tập test (A); thiếu thì phiếu
không nạp được. B gán mẫu gán đôi để đo đồng thuận, chỉ cần `verdict`, `reasons`, `note` (24/10/2026).

**Mã lý do** (danh sách đóng, không thêm mã trong đợt kiểm; cách dùng ở §3). `note` bắt buộc
với mã in đậm.

| Bước | Mã |
|---|---|
| 1. Đúng phiên bản | **`gold_wrong`** · `transitional_rule` |
| 2. Chạm chỗ đổi | `group_mismatch` · `cosmetic_only` · `rename_only` · `auto_reference_update` |
| 3. Một điều khoản, một cách | `question_ambiguous` · `unanswerable_as_asked` |
| 4. Không để lộ | `question_leaks` |
| 5. Nội dung pháp lý | `reference_only` |
| 6. Không bị đè | **`superseded_by_other_norm`** · `restructuring_2025` |
| 7. T6 chuyển chỗ | **`relocated`** · `relocation_unclear` |
| 8. Đáp án ngắn, lỗi khác | **`other`** |

Lớp phụ, chỉ có ở `data/review/labels.tsv` và không tính vào đồng thuận: `meta_issues` ghi lỗi siêu
dữ liệu không làm sai đáp án (`valid_to_wrong` · `valid_from_wrong` · `group_wrong` ·
`citation_path_wrong` · `doc_number_wrong` · `lead_in_wrong` · `other`).

## 3. Kiểm tám bước

Kiểm theo thứ tự dưới đây, đủ cả tám bước. Bước nào không đạt thì ghi mã của bước đó; một dòng có
thể mang nhiều mã. Đạt cả tám bước thì gán `dat`. Gợi ý của máy (`cac_phien_ban`, `goi_y_cho_moi`,
`note_for_annotator`) chỉ cho biết chỗ cần nhìn, không cho biết nhãn.

**Bước 1. Đáp án đúng phiên bản có hiệu lực tại `as_of`.** Đối chiếu cả lời văn và câu dẫn với văn
bản gốc, văn bản tác động, `cac_phien_ban` (dòng đang kiểm là bản đánh dấu ◀) và chữ đỏ đậm trong
`answer` (chữ phiên bản khác không có).
- Sai phiên bản, hoặc lời văn thiếu hay thừa so với văn bản gốc → `gold_wrong`.
- Văn bản gốc trên cổng đã là lời văn sau sửa, nên vế trước không đúng → `gold_wrong`.
- Văn bản tác động có hiệu lực tách phần ("trừ quy định tại khoản 2, 3 Điều này", "các quy định
  về … có hiệu lực kể từ ngày ký"): đọc điều hiệu lực của nó. Lần sửa của dòng thuộc phần ngoại lệ
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

**Bước 2. Câu hỏi chạm đúng chỗ đổi** (T2–T6).
- T2, T4: hai dòng cùng câu hỏi, hai mốc, gán riêng từng dòng. Hai mốc trả lời như nhau →
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

**Bước 3. Câu hỏi chỉ khớp một điều khoản và trả lời được bằng đáp án này, một cách.**
- Với mục trong danh sách (kể cả T1), câu hỏi phải ghim đúng mục. Câu hỏi chung mà nhiều khoản cùng
  trả lời được → `question_ambiguous`.
- Hỏi "khi nào" mà đáp án không có thời hạn, hỏi "ai" mà đáp án không nêu chủ thể →
  `unanswerable_as_asked`.

**Bước 4. Câu hỏi không để lộ** ngày, số hiệu văn bản, Điều, Khoản, ký hiệu mục ("loại c)"), và không
chép sẵn đáp án. Không đạt → `question_leaks`. Câu hỏi chứa sẵn vế trước của đáp án thì gán ở dòng
mốc trước. Câu hỏi nêu sẵn cụm của bản cũ mà bản mới đã đổi (ví dụ "xã, phường, thị trấn") thì gán
ở cả hai mốc.

**Bước 5. Đáp án là nội dung pháp lý** (R5). Đáp án chỉ dẫn chiếu ("thực hiện theo quy định tại
Chương IV Thông tư này") → `reference_only`, kể cả khi khớp lời văn.

**Bước 6. Không có quy phạm khác đè lên, không vướng sắp xếp bộ máy.**
- ⚖ Văn bản cấp cao hơn, hoặc văn bản cùng cơ quan ban hành sau, quy định khác về cùng vấn đề mà
  không sửa điều khoản này → `superseded_by_other_norm` (R3).
- ⚖ `as_of` sau ngày sắp xếp (bộ: 01/03/2025; cấp huyện, tỉnh: 01/07/2025) mà đáp án vẫn nêu cơ
  quan, cấp, địa danh cũ chưa được sửa lời văn → `restructuring_2025` (R4).

**Bước 7. (T6) Nội dung bị bãi bỏ còn ở đâu** ⚖ (R2). Luôn làm bước này; bắt đầu từ `goi_y_cho_moi`.
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

**Bước 8. Đáp án ngắn đúng và đủ.** Sai, hoặc thiếu ý mà câu hỏi hỏi → `other`. Ghi ở `note` ý bị
thiếu và đoạn đúng **trích nguyên từ đáp án**; không viết lời mới. Nếu lỗi thật ra nằm ở câu hỏi
(câu hỏi rộng hơn đáp án, hoặc vấn đề còn được quy định ở văn bản khác) thì dùng mã của bước 3
hoặc bước 6.

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

1. **Công cụ.** Gán trên trang web (tự đo `phut`, lưu sau mỗi dòng) hoặc trên phiếu Excel. Hai
   người nhận cùng một bộ dẫn chứng do máy chuẩn bị; máy không điền nhãn.
2. **Độc lập.** Dòng gán đôi (mẫu `data/review/kiem_cheo.txt`) do A và B làm độc lập, không trao đổi
   trong lúc làm, và không biết dòng nào là dòng gán đôi. Tên thật chỉ ghi ở plan.
3. **Lô 0 hiệu chuẩn** (khoảng 20 dòng, nghiêng về T6 và T2 gần giống). Hai người làm độc lập và gửi
   trước, rồi cùng luật sư xem các dòng lệch. Kết luận dạng quy tắc chung ghi vào §7 trước khi làm lô
   1. Lô 0 không tính vào AC1.
4. **Lô 30–50 dòng.** Sau lô 3, 6, 9, 12, 15 đo đồng thuận trên các dòng chung. Dưới ngưỡng thì hiệu
   chuẩn lại trên dòng mới, **không sửa nhãn đã gán**: nhãn thô chính là số đo đồng thuận.
5. **Một phiên bản hướng dẫn cho mọi nhãn.** Nhãn D4 (bản 1.2, 2.0) đang có trong phiếu phải được xác
   nhận lại theo 3.0; để nguyên thì dòng đó vẫn tính là chưa kiểm.
6. **Phân vân.** Vẫn chọn một nhãn theo câu hỏi ở §1, ghi `[phân vân] …` ở `note` để hỏi luật sư.
7. **Đồng thuận.** Ngưỡng: AC1 ≥ 0,80 và p_neg ≥ 0,60; κ báo kèm; báo theo nhóm và theo phiên bản
   hướng dẫn. AC1 được chọn làm chỉ số chính **sau lượt pilot ngày 07/10/2026**, vì nghịch lý
   prevalence của κ; đây không phải chỉ số đăng ký trước.
8. **Hòa giải.** Dòng lệch do người thứ ba là luật sư quyết, không dùng AI; cột `adjudicator` ghi
   đúng người quyết. Nhãn thô của từng người giữ nguyên và được phát hành (ADR 0003 §9).
9. **Dòng `khong_dat` sau hòa giải bị loại** bằng mã tương ứng, hoặc thay bằng câu dự trữ. Không sửa
   đáp án chuẩn bằng tay.

Lệnh cho người điều phối:

| Việc | Lệnh (`scripts/review/`) |
|---|---|
| Dựng phiếu kiểm | `kiem_hints.py` → `crosscheck.py kiem` → `crosscheck_xlsx.py export --set kiem` |
| Gán trên web | `label_ui.py --who A` (thêm `--ids data/review/kiem_cheo.txt` để chỉ hiện dòng gán đôi) |
| Nạp phiếu Excel | `crosscheck_xlsx.py import --set kiem --who A` |
| Đo đồng thuận | `crosscheck.py kappa --set kiem` |
| Hòa giải | `adjudicate.py export --set kiem`, rồi `adjudicate.py import --set kiem --by "luật sư <tên>"` |
| Văn bản có hiệu lực tách phần | `effect_split_scan.py` → `data/review/hieu_luc_tach.tsv` |
| Chữ hỏng dấu, ký tự ẩn | `diacritic_scan.py` → `data/review/chu_hong_dau.tsv` |

## 6. Nhãn do model gán

Nhãn model **không được tính là kiểm định**. Đo ngày 19/10/2026: trên 13 dòng D4 có nhãn model, chỉ
7 dòng khớp kết luận cuối của người, và model gán `khong_dat` ít hơn người nhiều lần. Nhãn model chỉ
dùng để xếp thứ tự dòng cần người xem trước. Nhãn model cũ ở `data/review/labels.tsv` giữ nguyên để
phân tích phụ, có ghi `labeler`. Dòng chỉ có nhãn model là dòng chưa kiểm (`not_verified`) và không
vào tập test.

## 7. Hỏi đáp (sổ quyết định)

Mỗi mục ghi: ngày, người chốt, câu hỏi chung (không nêu dòng gán đôi cụ thể), kết luận và chỗ đã đưa
vào hướng dẫn. Kết luận chỉ làm rõ cách áp quy tắc đã có. Quy tắc mới thì phải sửa định nghĩa và
tăng phiên bản hướng dẫn.

- **24/10/2026, luật sư, lô 0** (`docs/hoa_giai_lo0_chot.xlsx`). 12/21 dòng lệch; cả 12 là một người
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
- **D4, biên bản D5 §2.** Ba bài học: luôn làm bước 7 ở T6; dùng một phiên bản hướng dẫn cho mọi
  nhãn (§5 mục 5); so câu hỏi với chỗ đổi (bước 2).
