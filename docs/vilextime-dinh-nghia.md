# ViLexTime — định nghĩa bộ dữ liệu (bản chốt)

**Chốt ngày 20/10/2026 (CMT).** Đây là bản định nghĩa duy nhất của ViLexTime. Nó thay cho
`docs/vilextime-dinh-nghia-nhom-v2-draft.md` và mọi định nghĩa nhóm rải trong các tài liệu cũ.
Hướng dẫn gán nhãn (`docs/vilextime-annotation.md`, từ bản 3.0) và code dựng dữ liệu phải
theo tài liệu này. Khi có chỗ mâu thuẫn, tài liệu này đúng.

Các quy tắc pháp lý đánh dấu ⚖ chờ luật sư ký một lần (`data/review/gui_luat_su_dinh_nghia.xlsx`).
Luật sư không đồng ý điểm nào thì sửa đúng điểm đó trước khi gán nhãn, rồi khóa.

---

## 0. Quy tắc giữ định nghĩa không đổi

1. Sau khi luật sư ký, **định nghĩa không sửa nữa**: không thêm nhóm, không nới điều kiện,
   không thêm mã loại.
2. Việc được phép làm: **loại dòng** bằng một mã ở mục 7, kèm lý do.
3. Sửa lỗi đồ thị làm đổi đáp án của một dòng thì dòng đó phải được người kiểm lại. Không đổi
   định nghĩa cho vừa với dữ liệu.
4. Ca nào máy không làm đúng được thì loại ra kèm mã, không sửa đáp án bằng tay.

---

## 1. Bài toán

- **Đầu vào:** câu hỏi pháp lý `x` bằng tiếng Việt, mốc thời gian `t`.
- **Đầu ra:** câu trả lời `a` cùng tập bằng chứng `E` gồm các Điều, Khoản, Điểm có hiệu lực tại `t`.
- **`t` nghĩa là gì** ⚖ — phiên bản có **hiệu lực pháp lý tại `t`**, theo khoảng hiệu lực mà
  chính các văn bản quy định, **kể cả hiệu lực trở về trước**. Câu hỏi hỏi "pháp luật quy định
  gì về việc này tại `t`"; sự việc được hiểu là phát sinh tại `t`. Căn cứ:
  khoản 1 Điều 156 Luật 80/2015/QH13 và khoản 2 Điều 58 Luật 64/2025/QH15 ("trường hợp văn
  bản quy phạm pháp luật có quy định hiệu lực trở về trước thì áp dụng theo quy định đó");
  Điều 152 Luật 80/2015/QH13 và Điều 55 Luật 64/2025/QH15 về hiệu lực trở về trước.
- **Không** hỏi "xử lý hôm nay một hành vi xảy ra tại `t`" (áp dụng văn bản mới nhẹ hơn theo
  khoản 4 Điều 156 Luật 80/2015/QH13; điều khoản chuyển tiếp cho việc đang thực hiện).
- **Một mục dữ liệu** gồm: câu hỏi, `t`, trạng thái đáp án (`còn hiệu lực` hoặc `đã hết hiệu
  lực`), phiên bản đúng, bằng chứng được chấp nhận, đáp án ngắn, dấu vết pháp lý (văn bản tác
  động, câu lệnh, ngày hiệu lực).
- **Đếm theo bốn cấp:** văn bản → câu hỏi (một lineage, tức một điều khoản và chuỗi phiên bản
  của nó) → cặp (câu hỏi, mốc) → mẫu. Đối chiếu khung 1.100–1.300 của đề cương bằng số cặp ở
  chế độ ranh giới.

## 2. Phạm vi

| Trong phạm vi | Ngoài phạm vi (ghi ở phần giới hạn) |
|---|---|
| Văn bản quy phạm pháp luật cấp trung ương trên vbpl.vn (ADR 0002) | Văn bản địa phương, văn bản cá biệt, VBHN (VBHN chỉ dùng để kiểm chứng) |
| **Sửa đổi**, kể cả **thay thế ở cấp điều khoản** ("Thay thế Điều 48 như sau…"), vì về pháp lý đó là sửa toàn bộ nội dung | **Bổ sung** điều khoản mới (khoản 3a, Điều 51a): điều khoản chưa từng tồn tại cần một kiểu đáp án khác |
| **Bãi bỏ** điều khoản, kể cả bãi bỏ điều khoản cấp trên | Hiệu lực theo không gian, theo đối tượng; xung đột quy phạm |
| Hiệu lực trở về trước; văn bản đã ký nhưng chưa có hiệu lực | Áp dụng văn bản mới nhẹ hơn cho hành vi trong quá khứ; câu hỏi cần nhiều điều khoản |

**Ngày hết hiệu lực của văn bản** ⚖. Văn bản hết hiệu lực trong ba trường hợp (Điều 154 Luật
80/2015/QH13; khoản 1 Điều 57 Luật 64/2025/QH15): hết thời hạn ghi trong văn bản; bị sửa đổi,
bổ sung hoặc thay thế bằng văn bản mới của chính cơ quan đã ban hành; bị bãi bỏ. Do đó:
- ngày hết hiệu lực phải có **căn cứ viết thành chữ**: thời hạn trong chính văn bản, hoặc câu
  thay thế, bãi bỏ trong văn bản khác;
- ngày trên cổng chỉ là **nguồn tra cứu**: dùng khi khớp với căn cứ; khi chưa tìm được căn cứ
  thì dùng tạm, và dòng nào phụ thuộc vào ngày đó phải được người kiểm xác nhận; khi cổng sai thì
  theo căn cứ;
- văn bản mới quy định khác mà không nói thay thế **không** làm văn bản cũ hết hiệu lực: đó là
  xung đột, xử lý theo quy tắc R3;
- **không suy ra** hết hiệu lực dây chuyền giữa các văn bản (văn bản hướng dẫn theo văn bản được
  hướng dẫn), vì quy tắc này khác nhau giữa khoản 4 Điều 154 Luật 80/2015/QH13 và khoản 2 Điều
  57 Luật 64/2025/QH15.

## 3. Quy tắc chung cho mọi dòng

**R1. Thay đổi thực chất** ⚖. Một lần chuyển phiên bản chỉ được tính là thay đổi khi nó đổi nội
dung pháp lý. Không tính:
- (i) chỉ đổi hình thức: hoa thường, dấu câu, khoảng trắng, đánh số;
- (ii) chỉ **đổi tên cơ quan hoặc đơn vị hành chính** do sắp xếp bộ máy, nhiệm vụ giữ nguyên
  (ví dụ Bộ Giao thông vận tải sang Bộ Xây dựng). Căn cứ: khoản 1 Điều 3 Nghị quyết
  190/2025/QH15, tên gọi cơ quan trong văn bản "được chuyển đổi theo tên gọi của cơ quan, chức
  danh tiếp nhận chức năng, nhiệm vụ, quyền hạn đó", nên đáp án pháp lý đã đổi từ ngày sắp xếp,
  không đợi văn bản sửa tên;
- (iii) chỉ cập nhật dẫn chiếu sang văn bản mới, khi chính văn bản đã quy định tự áp văn bản thay
  thế (ví dụ khoản 3 Điều 7 Thông tư 84/2018/TT-BTC).

**R2. Chuyển chỗ** ⚖. Câu hỏi về nội dung được trả lời bằng quy phạm đang điều chỉnh nội dung
đó (cố vấn chốt 05/10/2026). Một điều khoản bị bãi bỏ mà nội dung **đã chuyển** sang chỗ khác
(đạt đủ bảy yếu tố ở `docs/vilextime-annotation.md` §3) thì **không** dùng làm dòng "không có
đáp án": loại với mã `relocated`, ghi chỗ mới vào phụ lục phát hành, không chấm điểm. Không chắc
thì loại với mã `relocation_unclear`.

**R3. Quy phạm khác đè lên** ⚖. Văn bản có hiệu lực pháp lý cao hơn, hoặc văn bản cùng cơ quan
ban hành sau, quy định khác về cùng vấn đề mà không sửa điều khoản này (khoản 2–3 Điều 156 Luật
80/2015/QH13; khoản 3–4 Điều 58 Luật 64/2025/QH15): loại dòng, mã `superseded_by_other_norm`.

**R4. Sắp xếp bộ máy 2025** ⚖. Dòng có `t` sau ngày sắp xếp (hợp nhất bộ từ 01/03/2025; bỏ cấp
huyện và sáp nhập tỉnh từ 01/07/2025) mà đáp án vẫn nêu cơ quan, cấp hay địa danh cũ chưa được
sửa lời văn: loại, mã `restructuring_2025`. Máy dò, người xác nhận.

**R5. Đáp án phải là nội dung pháp lý.** Điều khoản chỉ có dẫn chiếu ("thực hiện theo Thông tư
X") không dùng làm đáp án: mã `reference_only`.

**R6. Sự kiện chưa áp.** Dòng có sự kiện sửa đổi hoặc bãi bỏ ở trạng thái `needs_review` chạm
điều khoản đích hoặc điều khoản cấp trên, có hiệu lực trước `t`, thì chưa được vào tập test cho
tới khi sự kiện được xử lý (`scripts/review/pending_events.py`).

**R7. Không có mốc sau ngày chụp kho văn bản.**

## 4. Sáu nhóm

Thang biểu diễn dùng để định nghĩa nhóm (`src/vilexgraph/framework/temporal.py`):
`none` (không dùng thời gian) → `document` (lọc theo ngày của văn bản) → `version` (lọc theo
khoảng hiệu lực của chính điều khoản) → `propagated` (lan truyền hiệu lực từ điều khoản cấp trên).

| Nhóm (nhãn đề cương) | Năng lực được đo | Bậc trong thang | Điều kiện (ở cấp câu hỏi) | Đáp án đúng | Chỉ số chính |
|---|---|---|---|---|---|
| **T1** Đối chứng | Thêm khả năng thời gian có làm hỏng câu không phụ thuộc thời gian không | đối chứng | Điều khoản chỉ có 1 phiên bản; văn bản còn hiệu lực tại `t`; điều khoản cấp trên không bị bãi bỏ | Phiên bản duy nhất | Chênh lệch so với hệ không dùng thời gian; tỷ lệ từ chối sai |
| **T2** Cặp tương phản | Chọn đúng phiên bản | `document` → `version` | Câu hỏi có **đúng 2 đáp án khác nhau** trong lịch sử; lần đổi là thay đổi thực chất (R1) và chạm đúng phần được hỏi | Mỗi mốc một phiên bản; đáp án ngắn của bản này không nằm trong bản kia | Accuracy tương phản, TCS |
| **T3** Chuỗi nhiều bước | Chọn phiên bản trong chuỗi dài | như T2, khó hơn | Câu hỏi có **≥ 3 đáp án khác nhau**; mỗi lần đổi là thay đổi thực chất. Chỉ một lần đổi chạm câu hỏi thì chuyển sang T2 | Mỗi mốc một phiên bản | Accuracy tương phản, chuẩn hóa theo mức ngẫu nhiên |
| **T4** Bẫy gần giống (lát của T2) | Không bị đánh lừa bởi bản cũ gần như y hệt | như T2 | Là cặp T2; độ giống hai phiên bản ≥ 0,90; phần khác nhau quyết định đáp án (số tiền, thời hạn, chủ thể, phạm vi, điều kiện), người kiểm xác nhận | Như T2 | Như T2, cộng TVER, VCR |
| **T5a** Hồi tố | Đáp án không suy ra được từ ngày ban hành | `none` → `document` | Văn bản tác động có ngày hiệu lực **trước** ngày ký; luật sư xác nhận từng văn bản; `t` nằm giữa ngày hiệu lực và ngày ký | Bản **mới** | Báo số đếm theo văn bản tác động (tập chẩn đoán, không vào con số chung) |
| **T5b** Đã ký, chưa hiệu lực | Không lấy văn bản mới khi nó chưa là luật | `none` → `document` | Văn bản sửa đổi đã ký trước `t` nhưng có hiệu lực sau `t` (chế độ `truoc_hieu_luc`) | Bản **cũ** | Accuracy tương phản, báo riêng |
| **T6a** Bãi bỏ đích danh | Biết khoản, điểm đã hết hiệu lực | `version` | Cấp Khoản hoặc Điểm; bị bãi bỏ bằng câu lệnh nêu đích danh; văn bản vẫn còn hiệu lực; người kiểm xác nhận không chuyển chỗ (R2) | Không có đáp án: phải nói đã bãi bỏ | Recall, precision của việc từ chối; TVER |
| **T6b** Mất hiệu lực theo cấp trên | Biết hiệu lực lan xuống điều khoản cấp dưới | `version` → `propagated` | Cấp Khoản hoặc Điểm; điều khoản cấp trên (Khoản, Điều, Mục, Chương) bị bãi bỏ; câu bãi bỏ không nêu tên điều khoản này; không chuyển chỗ (R2) | Không có đáp án | Như T6a, cộng TV-Recall@1 |

## 5. Chế độ đặt mốc

| Chế độ | Dùng cho | Vai trò |
|---|---|---|
| `ranh_gioi` | mọi nhóm | Hai ngày liền nhau quanh lần chuyển; đếm cỡ bộ dữ liệu theo chế độ này |
| `giua_khoang` | mọi nhóm | Cách hai đầu khoảng ≥ 30 ngày; **bảng kết quả chính** |
| `truoc_hieu_luc` | T5b | Sau ngày ký, trước ngày hiệu lực của văn bản sửa đổi |
| ~~`sau_het_hieu_luc`~~ | **bỏ khỏi phần chấm điểm** | Văn bản bị thay thế thì văn bản mới thường quy định tiếp nội dung (ví dụ 4 ở mục 10); hiện tượng "không còn đáp án" đã được T6 đo, có kiểm chuyển chỗ |

## 6. Điều kiện để một dòng vào tập test

Người kiểm đánh dấu đủ các ô sau, kèm dẫn chứng:

1. Đáp án đúng là phiên bản có hiệu lực pháp lý tại `t`, đối chiếu văn bản gốc (cả lời văn, không chỉ đoạn được hỏi).
2. Câu hỏi chạm đúng phần thay đổi: hỏi ở hai mốc thì đáp án khác nhau (T2, T4), hoặc ra ≥ 3 đáp án (T3).
3. Câu hỏi chỉ khớp một điều khoản, có một đáp án duy nhất.
4. Câu hỏi không nêu ngày, số hiệu văn bản, Điều hay Khoản, và không chép sẵn đáp án.
5. Đáp án là nội dung pháp lý (R5).
6. Không có quy phạm khác đè lên, không vướng sắp xếp bộ máy (R3, R4).
7. (T6) Đã kiểm bảy yếu tố chuyển chỗ, kết luận không chuyển (R2).
8. Đáp án ngắn đúng và đủ.

Thêm điều kiện máy: R6, R7 đạt.

## 7. Mã loại dòng (danh sách đóng, 19 mã)

| Mã | Khi nào |
|---|---|
| `cosmetic_only` | Lần chuyển chỉ đổi hình thức (R1-i) |
| `rename_only` | Lần chuyển chỉ đổi tên cơ quan, đơn vị (R1-ii) |
| `auto_reference_update` | Lần chuyển chỉ cập nhật dẫn chiếu tự áp (R1-iii) |
| `single_change` | Chuỗi không đủ ≥ 3 đáp án khác nhau cho T3 và cũng không đạt T2 |
| `relocated` | Nội dung bị bãi bỏ đã chuyển chỗ (R2) |
| `relocation_unclear` | Không chắc có chuyển chỗ hay không (R2) |
| `superseded_by_other_norm` | Quy phạm khác đè lên (R3) |
| `restructuring_2025` | Vướng sắp xếp bộ máy 2025 (R4) |
| `reference_only` | Đáp án chỉ là dẫn chiếu (R5) |
| `pending_event` | Có sự kiện chưa áp (R6) |
| `after_snapshot` | Mốc sau ngày chụp kho (R7) |
| `group_mismatch` | Câu hỏi không làm được việc của nhóm: không chạm phần thay đổi (T2, T4), không chạm ≥ 2 lần sửa (T3), chỉ hỏi có/không (T6), hỏi vào phần không đổi (T5) |
| `question_ambiguous` | Câu hỏi khớp nhiều điều khoản hoặc nhiều đáp án |
| `question_leaks` | Câu hỏi để lộ đáp án, số hiệu, Điều, Khoản hoặc phiên bản |
| `unanswerable_as_asked` | Đáp án không trả lời được đúng điều câu hỏi hỏi |
| `gold_wrong` | Đáp án không phải phiên bản có hiệu lực tại `t` |
| `transitional_rule` | Đáp án phụ thuộc điều khoản chuyển tiếp mà câu hỏi tự nêu, hoặc chuyển tiếp buộc chính sự việc phát sinh tại `t` theo bản cũ |
| `other` | Lỗi khác, mô tả ở ghi chú |
| `not_verified` | Chưa được người kiểm; phát hành ở phần silver, không chấm |

Mã `cosmetic_only`, `rename_only`, `auto_reference_update`, `single_change`, `pending_event`,
`after_snapshot` do máy gán khi dựng; các mã còn lại do người gán khi kiểm (người cũng được dùng
mã của máy khi phát hiện).

## 8. Câu hỏi, đáp án và kiểm định

- **Câu hỏi:** model viết bản nháp, **người duyệt mọi câu trong tập test** (giữ, sửa hoặc viết
  lại); `question_source` ghi rõ nguồn. Thêm khoảng 100 câu người viết lại mà không nhìn đáp
  án, để đo thiên lệch do model viết.
- **Đáp án ngắn:** người duyệt cùng lúc với dòng.
- **Tập test chỉ gồm dòng người đã kiểm** có dẫn chứng. 25% số dòng do hai người gán độc lập
  để đo đồng thuận (AC1 ≥ 0,80 và p_neg ≥ 0,60; κ báo kèm). Dòng lệch do **người thứ ba** hòa
  giải, không dùng AI. Model chỉ được trích dẫn chứng, không được ra kết luận.
- **Silver:** dòng chưa kiểm phát hành riêng, mã `not_verified`.
- **Gold độc lập:** 120 + 30 dòng gán mù, ngưỡng ≥ 114/120 (quyết định B6, 11/10/2026).

## 9. Quy mô mục tiêu

Đếm theo cặp (câu hỏi, mốc) ở chế độ `ranh_gioi`. Thiếu thì lấy từ câu dự trữ và kho ứng viên;
không đạt sàn thì giảm quota, không nới điều kiện.

| Nhóm | Mục tiêu | Sàn |
|---|---:|---:|
| T1 | 150 | 150 |
| T2 thường | 300 | — |
| T4 (lát của T2) | 150 | — |
| T3 | 150 | 120 |
| T5a | khoảng 34 | toàn bộ ca luật sư xác nhận |
| T6a | — | 100 |
| T6b | 250 | 200 |
| **Tổng** | **khoảng 1.100–1.150** | |

T5b báo riêng (hiện 153 dòng ở chế độ `truoc_hieu_luc`), không cộng vào tổng trên.

## 10. Ví dụ đã đối chiếu văn bản gốc (20/10/2026)

| Nhóm | Điều khoản | Mốc và đáp án | Căn cứ |
|---|---|---|---|
| T1 | Khoản 2 Điều 78 Luật 62/2014/QH13 (điều động Thẩm phán) | 30/07/2023: Chánh án TANDTC quyết định | Lược đồ cổng: không văn bản nào sửa; luật hết hiệu lực theo khoản 2 Điều 151 Luật 34/2024/QH15 |
| T2 | Điểm b khoản 2 Điều 28 TT 12/2017/TT-BGTVT (hồ sơ sát hạch phải lưu) | 30/11/2019: không có bài sát hạch mô phỏng; 01/12/2019: có | Điểm b khoản 17 Điều 1 TT 38/2019/TT-BGTVT; khoản 1 Điều 2 |
| T3 | Khoản 13 Điều 33 TT 12/2017/TT-BGTVT (giấy phép lái xe hợp lệ) | 3 đáp án: trước 01/12/2019; 01/12/2019–31/05/2024; từ 01/06/2024 (thêm VNeID) | Điểm a khoản 19 Điều 1 TT 38/2019; điểm a khoản 24 Điều 4 TT 05/2024/TT-BGTVT |
| T4 | Điểm n khoản 1 Điều 30 NĐ 355/2025/NĐ-CP (dầu gội cho phạm nhân chưa thành niên) | 800 ml trước 01/07/2026; 1.000 ml từ 01/07/2026 | Khoản 5 Điều 43 NĐ 170/2026/NĐ-CP; khoản 1 Điều 44 |
| T5a | Điểm c khoản 3 Điều 33 NĐ 242/2025/NĐ-CP (Bộ Tài chính lấy ý kiến) | 03/02/2026: bản mới (thêm Bộ Công an, Bộ Quốc phòng; 07 ngày), dù văn bản sửa ký 03/04/2026 | Điểm d khoản 19 Điều 1, khoản 3 Điều 6 NĐ 119/2026/NĐ-CP; luật sư xác nhận 12/10/2026 |
| T5b | Như T4 | 01/06/2026: 800 ml (NĐ 170/2026 đã ký 15/05/2026, chưa có hiệu lực) | Như T4 |
| T6a | Điểm c khoản 3 Điều 26 NĐ 67/2013/NĐ-CP (diện tích tối thiểu 03 m² khi bán lẻ thuốc lá) | 07/03/2017: 03 m²; 10/08/2021: không còn quy định | Khoản 4 Điều 2 NĐ 106/2017/NĐ-CP; không tìm thấy quy định kế thừa |
| T6b | Điểm a khoản 1 Điều 23 NĐ 23/2016/NĐ-CP (trình độ cán bộ quản lý vận hành cơ sở hỏa táng) | 28/03/2023: kỹ sư các ngành…; 09/06/2026: không còn | Khoản 2 Điều 138 NĐ 14/2026/NĐ-CP bãi bỏ khoản 1 (cấp trên); không tìm thấy quy định kế thừa |

Ví dụ bị loại, cũng đã đối chiếu:

1. **`relocated`:** Điều 8 NĐ 37/2017/NĐ-CP (an toàn lao động, phòng cháy khi khai thác cảng
   biển) bị bãi bỏ bởi khoản 5 Điều 5 NĐ 147/2018/NĐ-CP. Nhưng khoản 3 Điều 5 của cùng nghị định
   viết lại Điều 7 và thêm "Đáp ứng các điều kiện về an toàn, vệ sinh lao động, phòng, chống
   cháy, nổ theo quy định của pháp luật".
2. **`relocated`:** Điều 23 NĐ 163/2013/NĐ-CP đã bị khoản 21 Điều 1 NĐ 115/2016/NĐ-CP thay
   toàn bộ từ 15/09/2016 (biên bản D5).
3. **`pending_event`:** khoản 5 Điều 95 NĐ 168/2025/NĐ-CP. NĐ 296/2026/NĐ-CP vừa đổi "03 ngày
   làm việc" thành "02 ngày làm việc", vừa "bãi bỏ cụm từ 'nơi đã nộp hồ sơ'", nhưng câu thứ hai
   chưa được áp.
4. **Lý do bỏ `sau_het_hieu_luc`:** Luật 62/2014/QH13 hết hiệu lực từ 01/01/2025, nhưng Điều 106
   Luật 34/2024/QH15 vẫn quy định việc điều động Thẩm phán. Ngày 21/11/2025 câu hỏi vẫn có đáp án.

## 11. Chỗ lệch so với đề cương (đưa vào bảng lệch của khóa luận)

| Đề cương | Định nghĩa này | Lý do |
|---|---|---|
| T1 250 câu | 150 | Đủ cho vai trò đối chứng |
| T3 200 | sàn 120, mục tiêu 150 | Điều kiện chặt ở cấp câu hỏi |
| T4 là nhóm riêng, 150 | Lát của T2, 150 dòng | Cùng năng lực với T2, khác ở độ khó |
| T5 "hiệu lực trở về trước có lợi cho đối tượng áp dụng", 50 | T5a hồi tố (bỏ vế "có lợi") và T5b đã ký chưa hiệu lực | "Có lợi" là điều kiện cho phép hồi tố, không làm bài toán khó hơn |
| T6 100 | T6a sàn 100, T6b sàn 200 | T6b là bậc lan truyền, phần đóng góp riêng của đề tài |
| "LLM chỉ hỗ trợ diễn đạt câu hỏi" | Model viết nháp, người duyệt mọi câu trong test | Khớp lại tinh thần đề cương |
