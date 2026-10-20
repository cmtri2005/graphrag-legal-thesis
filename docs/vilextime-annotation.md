# Hướng dẫn gán nhãn ViLexTime

Phiên bản hướng dẫn: **3.0** (20/10/2026). Bản này cài đặt `docs/vilextime-dinh-nghia.md`
(định nghĩa bộ dữ liệu, bản chốt). Hai tài liệu mâu thuẫn thì định nghĩa đúng. Các quy tắc pháp
lý đánh dấu ⚖ ở định nghĩa đang chờ luật sư ký (`data/review/gui_luat_su_dinh_nghia.xlsx`).

Thay đổi so với 2.0:
- **đổi tên cơ quan, đơn vị do sắp xếp bộ máy không còn là thay đổi** (định nghĩa R1). Ví dụ
  "đổi tên cơ quan → `dat`" của bản 2.0 bị bỏ;
- T6 **không chắc** về chuyển chỗ thì `khong_dat`, mã `relocation_unclear` (bản 2.0: `dat` kèm
  `unclear`). Chuyển chỗ rõ ràng dùng mã `relocated` (bản 2.0: `gold_wrong`);
- T3 phải ra **≥ 3 đáp án khác nhau** cho chính câu hỏi;
- T5 tách **T5a** (hồi tố) và **T5b** (đã ký, chưa có hiệu lực);
- bỏ loại dòng `sau_het_hieu_luc`;
- thêm mã `superseded_by_other_norm`, `restructuring_2025`, `reference_only`, `relocated`,
  `relocation_unclear` và các mã máy (mục 2);
- mỗi dòng kiểm có **ô bắt buộc** (mục 5): người kiểm ghi đã xem gì, không chỉ ghi kết luận;
- tập test chỉ gồm dòng người đã kiểm; nhãn model không còn được tính là kiểm định (mục 6).

Bản 2.0 (12/10/2026) và 1.2 (29/09/2026) còn trong lịch sử git. Mỗi nhãn ghi phiên bản hướng dẫn
đã dùng (cột `guideline_version`).

## 1. Bạn đang kiểm cái gì

Mỗi dòng là **một câu hỏi được hỏi ở một mốc thời gian** (`as_of`), kèm **đáp án chuẩn**: nội
dung điều khoản có hiệu lực tại mốc đó. Đáp án do máy dựng từ chuỗi phiên bản. Câu hỏi do model
viết nháp.

Bạn trả lời **một câu cho mỗi dòng**:

> Một luật sư đọc câu hỏi, biết ngày `as_of`, tra đúng văn bản — người đó có trả lời **đúng
> bằng nội dung trong cột đáp án** không, và trả lời được **chỉ một cách** không?

Có → `dat`. Không → `khong_dat` và ghi mã lý do.

Ba quy tắc nền:

- **Mốc `as_of` là ngày tính hiệu lực pháp lý** ⚖. Đáp án là phiên bản có hiệu lực tại `as_of`
  theo khoảng hiệu lực mà chính các văn bản quy định, **kể cả hiệu lực trở về trước**. Sự việc
  hiểu là phát sinh tại `as_of`. Điều khoản chuyển tiếp chỉ giữ bản cũ cho việc **đang thực
  hiện** thì không đổi đáp án.
- **Câu hỏi hỏi nội dung, không hỏi vị trí.** Đáp án là quy phạm đang điều chỉnh nội dung được
  hỏi tại `as_of`. Chỉ đổi mức phạt thì vẫn là cùng một quy phạm.
- **Câu dẫn là một phần của đáp án.** Với mục trong danh sách, đọc điểm cùng câu dẫn của nút
  cha tại `as_of` (cột `lead_in`). Ở nghị định xử phạt, mức phạt nằm ở câu dẫn của khoản.

## 2. Nhãn

| Cột | Giá trị | Ghi chú |
|---|---|---|
| `verdict` | `dat` · `khong_dat` | Đồng thuận tính trên cột này |
| `reasons` | một hoặc nhiều mã bên dưới, cách nhau bằng dấu phẩy | Chỉ điền khi `khong_dat` |
| `note` | tự do | Bắt buộc khi có `gold_wrong`, `relocated`, `superseded_by_other_norm` hoặc `other` |

Mã lý do (danh sách đóng, không thêm mã trong đợt kiểm):

| Mã | Khi nào |
|---|---|
| `question_ambiguous` | Câu hỏi khớp **nhiều điều khoản** hoặc nhiều mục; đáp án chuẩn chỉ là một trong số đó |
| `question_leaks` | Câu hỏi nói sẵn đáp án, nêu số hiệu, Điều, Khoản, ký hiệu mục ("c)"), hoặc để lộ phiên bản |
| `unanswerable_as_asked` | Đúng chủ đề nhưng đáp án không trả lời được điều câu hỏi hỏi (hỏi "khi nào" mà đáp án không có thời hạn…) |
| `group_mismatch` | Câu hỏi không làm được việc của nhóm (mục 3) |
| `gold_wrong` | Cột đáp án không phải phiên bản có hiệu lực tại `as_of`: sai phiên bản, lời văn thiếu hay thừa so với văn bản gốc, vế "trước sửa đổi" thực ra đã là bản sửa |
| `transitional_rule` | Điều khoản chuyển tiếp giữ bản cũ cho đúng quan hệ câu hỏi **tự nêu**, hoặc buộc chính sự việc phát sinh tại `as_of` theo bản cũ. Ghi Điều chuyển tiếp ở `note` |
| `relocated` | (T6) Nội dung bị bãi bỏ đã chuyển chỗ, đạt đủ 7 yếu tố (mục 3). Ghi chỗ mới ở `note` |
| `relocation_unclear` | (T6) Không chắc có chuyển chỗ hay không. Ghi chỗ nghi ở `note` |
| `superseded_by_other_norm` | ⚖ Văn bản cấp cao hơn, hoặc văn bản cùng cơ quan ban hành sau, quy định khác về cùng vấn đề mà không sửa điều khoản này. Ghi văn bản ở `note` |
| `restructuring_2025` | ⚖ `as_of` sau ngày sắp xếp bộ máy (bộ: 01/03/2025; cấp huyện, tỉnh: 01/07/2025) mà đáp án vẫn nêu cơ quan, cấp, địa danh cũ chưa được sửa lời văn |
| `reference_only` | Đáp án chỉ là dẫn chiếu ("thực hiện theo Thông tư X"), không có nội dung pháp lý |
| `rename_only` · `cosmetic_only` · `auto_reference_update` | Lần đổi mà câu hỏi dựa vào chỉ là đổi tên cơ quan do sắp xếp, đổi hình thức, hoặc cập nhật dẫn chiếu tự áp (định nghĩa R1). Máy đã lọc phần lớn; người dùng khi phát hiện còn sót |
| `other` | Lỗi khác, mô tả ở `note` |

Lớp phụ, chỉ ở `data/review/labels.tsv` và không vào đồng thuận: `meta_issues` ghi lỗi siêu dữ
liệu không làm sai đáp án tại `as_of` (`valid_to_wrong` · `valid_from_wrong` · `group_wrong` ·
`citation_path_wrong` · `doc_number_wrong` · `lead_in_wrong` · `other`).

## 3. Cách kiểm từng nhóm

Đọc **câu hỏi → mốc → đáp án**. Đọc đoạn trích văn bản gốc và văn bản tác động ở phiếu; mở link
(`source_url`) khi cần đọc thêm.

**T1 — đối chứng (một phiên bản).** Kiểm `question_ambiguous`: với mục trong danh sách, câu hỏi
phải ghim được đúng mục.

**T2 — cặp tương phản; T4 — cặp gần giống (lát của T2).** Hai dòng cùng câu hỏi, khác mốc, gán
riêng từng dòng.
- Câu hỏi phải chạm đúng phần đã đổi. Đọc câu hỏi mà hai đáp án trả lời được như nhau →
  `group_mismatch`.
- Lần đổi chỉ là đổi tên cơ quan do sắp xếp bộ máy (Bộ Giao thông vận tải → Bộ Xây dựng; Bộ Tài
  nguyên và Môi trường → Bộ Nông nghiệp và Môi trường), đổi hình thức, hoặc cập nhật dẫn chiếu tự
  áp → `rename_only` / `cosmetic_only` / `auto_reference_update`. Căn cứ: khoản 1 Điều 3 Nghị
  quyết 190/2025/QH15, tên cơ quan trong văn bản đã được chuyển theo cơ quan tiếp nhận từ ngày
  sắp xếp.
- Đổi sang **cơ quan khác về chức năng** (không phải cơ quan kế thừa) là thay đổi thật.
- Kiểm **vế trước** với văn bản gốc: văn bản gốc trên cổng đã là lời văn sau sửa → `gold_wrong`.
- Câu hỏi chứa sẵn vế trước của đáp án → dòng ngày trước `question_leaks`.
- T4: chỗ đổi thường chỉ là một con số hay một cụm từ; câu hỏi phải hỏi đúng vào chỗ đó.

**T3 — chuỗi nhiều bước.** Câu hỏi phải ra **≥ 3 đáp án khác nhau** qua các mốc. Chỉ tách được
hai trạng thái → `group_mismatch`. Lần đổi giữa hai mốc chỉ là đổi tên hay hình thức thì không
tính là một trạng thái mới.

**T5a — hồi tố.** Mốc nằm giữa ngày hiệu lực và ngày ký của văn bản sửa đổi; đáp án là **nội
dung mới**. Văn bản có thật sự hồi tố không là việc của luật sư (`data/review/t5_documents.tsv`,
đã chốt 12/10/2026), không phải của người gán. Kiểm câu hỏi có hỏi vào phần thật sự đổi không
(`group_mismatch`).

**T5b — đã ký, chưa có hiệu lực.** Mốc sau ngày ký, trước ngày có hiệu lực của văn bản sửa đổi;
đáp án là **nội dung cũ**. Kiểm ngày ký và ngày hiệu lực ở cột ghi chú của phiếu với văn bản.

**T6a — bị bãi bỏ đích danh; T6b — mất hiệu lực vì điều khoản cấp trên bị bãi bỏ.** Mốc sau có
đáp án rỗng. Câu **chỉ** hỏi có/không → `group_mismatch`; câu ghép có thêm vế hỏi nội dung thì
chấm theo vế nội dung. Quy trình:

1. **Có thật bị bãi bỏ không?** T6a: câu bãi bỏ nêu đích danh điều khoản. T6b: câu bãi bỏ nêu
   điều khoản cấp trên (Khoản, Điều, Mục, Chương); kiểm câu đó không giữ lại điều khoản này (ví dụ
   "trừ điểm a"), nếu giữ thì `gold_wrong`. Văn bản phải còn hiệu lực.
2. **Nội dung còn ở đâu không?** Tìm theo thứ tự: (a) cùng văn bản bãi bỏ — cụm "Bổ sung…",
   "Sửa đổi Điều… như sau" cùng đợt; (b) khoản cha, khoản anh em của cùng điều; (c) văn bản khác
   có hiệu lực cùng ngày hoặc được dẫn tới; (d) văn bản cấp cao hơn còn hiệu lực quy định cùng vấn
   đề (khi đó dùng `superseded_by_other_norm`).
3. **Chuyển chỗ khi đạt đủ bảy yếu tố** giữa quy định cũ và quy định ở chỗ mới (luật sư xác nhận
   12/10/2026):

   | # | Yếu tố | Đạt khi |
   |---|---|---|
   | 1 | Hành vi | giữ nguyên về bản chất |
   | 2 | Đối tượng, chủ thể | giữ nguyên |
   | 3 | Điều kiện áp dụng | giữ nguyên |
   | 4 | Cấu trúc quy định | chỉ đổi vị trí, thời hạn |
   | 5 | Chế tài, hậu quả pháp lý | cùng loại chế tài; **mức** được đổi, không dùng ngưỡng. Đổi loại chế tài hay thêm hình thức phạt bổ sung: không đạt |
   | 6 | Thẩm quyền, hiệu lực pháp lý kế thừa | cùng cơ quan ban hành (hoặc cơ quan kế thừa sau sắp xếp), hiệu lực pháp lý không thấp hơn |
   | 7 | Dẫn chiếu, kỹ thuật chuyển tiếp | có dấu vết nối hai quy định: cùng đợt "Bãi bỏ… Bổ sung…", câu "thay thế", điều khoản chuyển tiếp |

   Địa danh chỉ đổi **tên** do sáp nhập mà phạm vi, ranh giới giữ nguyên thì yếu tố 2 đạt.
4. **Gán nhãn:**
   - đạt đủ bảy yếu tố → `khong_dat`, `relocated`, ghi chỗ mới (văn bản, vị trí, trích đoạn);
   - không có quy định kế thừa, hoặc yếu tố 1–6 không đạt rõ ràng → `dat` (nếu không có lỗi khác);
   - không chắc ở yếu tố nào, hoặc yếu tố 7 không có dấu vết → `khong_dat`, `relocation_unclear`.
5. **Khoảng trống.** Khoản cũ hết hiệu lực từ ngày A, quy định ở chỗ mới có hiệu lực từ ngày B > A:
   hỏi giữa A và B thì đáp án rỗng là đúng. Trước khi kết luận trống, kiểm: điều khoản chuyển tiếp
   giữ khoản cũ; văn bản khác quy định cùng vấn đề trong giai đoạn đó; quy định mới hồi tố về A;
   A và B có thật khác nhau.

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

## 5. Quy trình kiểm

1. **Phiếu kiểm** có đoạn trích văn bản gốc và văn bản tác động (`crosscheck_evidence.py`). Model
   chỉ được trích dẫn chứng, không được điền kết luận.
2. **Ô bắt buộc** cho mỗi dòng, ngoài `verdict`, `reasons`, `note`:
   - `da_xem_van_ban_tac_dong`: liệt kê số hiệu các văn bản tác động đã xem (hoặc "không có");
   - `cham_lan_sua` (T2, T3, T4): những ngày chuyển mà câu hỏi chạm tới;
   - `noi_dung_con_o_dau` (T6): "không có", hoặc chỗ mới, hoặc "không chắc";
   - `phut`: số phút đã dùng.
   Thiếu ô bắt buộc thì phiếu không nạp được.
3. **Tập test: mọi dòng có người kiểm.** 25% số dòng do hai người gán độc lập, không trao đổi
   trong lúc làm; dùng mã `A`, `B` (bảng ánh xạ tên thật chỉ ở plan).
4. **Đồng thuận:** `python scripts/review/crosscheck.py kappa`. Ngưỡng đăng ký trước: AC1 ≥ 0,80 và
   p_neg ≥ 0,60; κ báo kèm; báo theo nhóm và theo phiên bản hướng dẫn.
5. **Hòa giải:** dòng lệch do **người thứ ba** quyết, ghi ở cột `adjudicated`
   (`scripts/review/adjudicate.py`, cột `adjudicator` ghi đúng người quyết). Không dùng AI để hòa
   giải. Nhãn thô của từng người giữ nguyên và phát hành (ADR 0003 §9).
6. **Dòng `khong_dat` sau hòa giải bị loại** bằng mã tương ứng, hoặc thay bằng câu dự trữ. Không
   sửa đáp án chuẩn bằng tay.
7. Làm theo lô 30–50 dòng; ghi `phut` để lập lại kế hoạch giờ công sau lô đầu.

## 6. Nhãn do model gán

Từ bản 3.0, nhãn của model **không được tính là kiểm định**: trên 13 dòng D4 có nhãn model, chỉ 7
dòng khớp kết luận cuối của người, và model gắn `khong_dat` ít hơn người nhiều lần (đo 19/10/2026).
Nhãn model chỉ dùng để **xếp thứ tự** dòng cần người xem trước. Nhãn model cũ trong
`data/review/labels.tsv` giữ nguyên làm phân tích phụ (đồng thuận model–người), có ghi `labeler`.
Dòng chỉ có nhãn model là dòng chưa kiểm (`not_verified`), không vào tập test.
