# Hồ sơ tiếp tục: 23 ca chưa chốt và đồng thuận AI–AI

Ngày lập: 08/11/2026. Dùng cho phiên tiếp tục ngày 09/11/2026.

Đây là phân tích nguyên nhân và checklist đề xuất, **không phải quyết định sửa
thẻ, sửa nhãn hoặc miễn cổng**. Kế hoạch đang có hiệu lực vẫn là
[master-plan](../plans/active/master-plan.md). Không tạo kế hoạch điều phối riêng.

## 1. Trạng thái cần giữ khi mở lại

| Tập | CMT chấp nhận đạt | CMT chấp nhận không đạt | Chưa chốt |
|---|---:|---:|---:|
| Silver trước đó | 81 | 87 | 0 |
| Lô mới 128 câu | 69 | 39 | 20 |
| Lô bổ sung 18 câu | 12 | 3 | 3 |

- CMT đã tự báo đọc xong và duyệt qua hội thoại ngày 08/11. Hồ sơ xác nhận
  gắn hash nằm ở `cmt_acceptance.json` của từng lô; không suy ra lịch sử đọc
  từng dòng hoặc chữ ký trong Excel.
- Tổng **162 câu đạt được CMT chấp nhận**, đủ ngưỡng **số lượng** G2 ≥130.
- Còn **23 ca chưa có nhãn cuối**. Duyệt các kết luận hiện có không tạo đáp án
  Q1–Q4 mới cho các ca này. Chúng vẫn ngoài nhãn cuối/tập test chính.
- Có 55 ca hòa giải, 32 ca có đề xuất đã giải quyết, 23 ca unresolved.
  Validator gốc đã qua đủ 49 ca lo2 và 6 ca supp18.
- Đồng thuận trước hòa giải chưa đạt; chưa phát hành dataset. Các yêu cầu G2
  khác như gold mù, đối chiếu VBHN, datasheet/manifest và không rò dev phải
  được kiểm riêng, không suy ra từ số lượng 162.

### Hồ sơ gốc để tiếp tục

- [Tổng hợp hiện tại](../../data/review/ai_research/2026-11-08_lo2/combined_review_summary.json).
- [23 ca mở, có lineage ID và câu hỏi còn thiếu](../../data/review/ai_research/2026-11-08_lo2/open_cases_for_CMT.jsonl).
- [Phiếu CMT lô 128](../../data/review/ai_research/2026-11-08_lo2/duyet_CMT_after_adjudication.xlsx).
- [Phiếu CMT lô 18](../../data/review/ai_research/2026-11-08_supp18/duyet_CMT_after_adjudication.xlsx).
- [CMT duyệt lô 128](../../data/review/ai_research/2026-11-08_lo2/cmt_acceptance.json)
  và [lô 18](../../data/review/ai_research/2026-11-08_supp18/cmt_acceptance.json).
- [Metrics lô 128](../../data/review/ai_research/2026-11-08_lo2/schema_validated/metrics.json)
  và [metrics lô 18](../../data/review/ai_research/2026-11-08_supp18/metrics.json).
- [Quy tắc định nghĩa](../vilextime-dinh-nghia.md),
  [thẻ gán nhãn 4.0](../vilextime-annotation.md).

Lô 128 dùng snapshot `schema_validated/`; bản khóa đầu vẫn giữ riêng.
Năm trạng thái nguồn `partial` của AI-A đã ánh xạ thành `insufficient`, có
receipt; không đổi Q/reason/verdict hay số đo. Các lần chuẩn hóa cấu trúc kết
quả hòa giải giữ bản gốc trong `schema_originals/`.

## 2. Nguyên nhân quan sát được

### 2.1 Đồng thuận thấp tập trung ở Q4 và T6

| Lô 128 | AC1 | p_neg | Nhận xét theo ngưỡng hiện tại |
|---|---:|---:|---|
| Q1 | 0,932 | 0,759 | Đạt |
| Q2 | 0,967 | 0,333 | Chưa đạt p_neg |
| Q3 | 0,849 | 0,755 | Đạt |
| Q4 | 0,753 | 0,465 | Chưa đạt cả hai |
| Verdict | 0,503 | 0,680 | Chưa đạt AC1 |

Tính trực tiếp từ nhãn khóa:

- 33 ca khác verdict: **20 chỉ khác Q4**, 10 chỉ khác Q3, 3 chỉ khác Q1.
- 27 ca khác Q4: **26 có ít nhất một bên báo insufficient**.
- Q4=`khong_chac`: A 5 câu, B 20 câu. Hai bên có dấu hiệu dùng ngưỡng
  thận trọng khác nhau khi thiếu nguồn; chưa chứng minh bên nào đúng hơn.
- Verdict AC1 theo nhóm: T2 0,697 (85 câu); T6 **0,075** (41 câu).
  T3 chỉ 2 câu, được code đánh dấu chưa đủ đánh giá cổng.
- Q2 có 123 câu cùng `co`, chỉ 1 câu cùng `khong` và 4 câu lệch. Vì vậy AC1
  cao không chứng minh đã thống nhất cách phát hiện nhãn bất lợi.

Lô 18: verdict AC1 0,538, p_neg=0. Hai bên cùng đạt 12 câu, nhưng không có
câu cùng không đạt. Các Q có quá ít nhãn bất lợi nên nhiều kết quả là
`not_evaluable`, không phải PASS. `adverse_labels` của code đếm lượt nhãn
trên cả A và B, không phải số câu bất lợi duy nhất.

Đây là mô tả và liên hệ trong hồ sơ, **không phải thí nghiệm chứng minh nguyên
nhân nhân quả**. Nhóm nhỏ, nguồn bị thiếu và cách chọn ứng viên hạn chế khả
năng khái quát hóa. Chưa có khoảng tin cậy cho các phân tích bổ sung này.

### 2.2 Không chỉ ca bất đồng mới cần rà

Trong các câu hai AI cùng verdict đạt, có **19 câu ít nhất một bên báo
insufficient**: 14 ở lo2 và 5 ở supp18. Không kết luận 19 câu này sai; cần rà
bằng chứng trước khi gọi chúng là đã kiểm chứng độc lập đầy đủ.

CMT chấp nhận nhãn, độ đúng pháp lý và đồng thuận AI–AI là ba loại bằng chứng
khác nhau. Quy trình chỉ hòa giải ca lệch có thể bỏ sót lỗi hai bên cùng mắc.

### 2.3 Ba loại nút thắt trong 23 ca

Phân nhóm dưới đây là chẩn đoán sơ bộ của người phân tích, chưa phải taxonomy
được duyệt: 7 ca chủ yếu thiếu nguồn; 5 ca chủ yếu cần quyết định phạm vi/cách
chấm; 11 ca vừa thiếu nguồn vừa vướng diễn giải. Mỗi ca chỉ nằm một nhóm trong
bảng để tiện phân công, nhưng nguyên nhân có thể thay đổi sau khi đọc nguồn.

| Case ID | Nhóm sơ bộ | Việc cần giải quyết trước |
|---|---|---|
| lo2-002 | Hỗn hợp | Hạn đăng ký 31/12/2015 và ngoại lệ/chuyển tiếp ảnh hưởng các mốc 2023, Q1/Q2/Q4 |
| lo2-003 | Phạm vi/cách chấm | Điều kiện chuyên môn của người phụ trách có trực tiếp thay yêu cầu giấy tờ của giám đốc trong hồ sơ không? |
| lo2-004 | Hỗn hợp | Quy định quản lý xe hợp đồng/du lịch còn áp dụng; phân biệt dùng khung phạt làm điều kiện hỏi với lộ đáp án |
| lo2-006 | Hỗn hợp | Đọc NĐ217/2025 và quy định ngành tài chính; chốt tác động cải cách thanh tra tới đáp án và Q2 |
| lo2-007 | Hỗn hợp | Chế định thẻ/mã A06 và các cuộc thanh tra chuyển tiếp; không suy hết hiệu lực dây chuyền |
| lo2-008 | Phạm vi/cách chấm | Q2 xét đáp án pháp lý hay thay đổi hình thức điều khoản khi quy phạm cấp cao hơn đã đè lên từ trước? |
| lo2-009 | Thiếu nguồn | Kiểm quy phạm kế thừa về nhân sự cơ sở hỏa táng tại 14–15/01/2026 |
| lo2-016 | Phạm vi/cách chấm | Thẩm quyền ban hành văn bản chung có kế thừa đúng nhiệm vụ chuyên ngành bị bãi bỏ không? |
| lo2-021 | Phạm vi/cách chấm | Phạm vi Luật Giá, danh mục công và nhiệm vụ về giá trong hoạt động quy hoạch |
| lo2-022 | Hỗn hợp | QĐ08/QĐ-BXD và ngày kế thừa cơ quan; cách đếm đáp án T3 trong phần câu hỏi thực sự hỏi |
| lo2-024 | Thiếu nguồn | Luật67/2011, NĐ17/2012 và các sửa đổi áp dụng 01/07/2024; không dùng văn bản 2025 hồi chiếu |
| lo2-030 | Hỗn hợp | NĐ56/2022, phân cấp nhiệm vụ cứu hộ; tách tổng cục thành hai cục có phải chỉ đổi tên? |
| lo2-031 | Thiếu nguồn | Luật15/2023, NĐ96/2023, BHYT và sửa đổi về chăm sóc sức khỏe ban đầu quanh 24/05/2024 |
| lo2-032 | Hỗn hợp | Cụm của bản cũ nằm ở tên điều có tính là lộ đáp án? Kiểm Luật Hải quan và quy phạm về máy soi |
| lo2-033 | Hỗn hợp | Đọc phần toàn văn NĐ14/2026 còn bị cắt; quy phạm môi trường/an toàn; quy định song song và kiểm chuyển chỗ |
| lo2-035 | Thiếu nguồn | Tìm/xác minh Phụ lục II; xử lý nhất quán bản quét trên cổng cấp tỉnh thay vì đồng nhất thiếu nguồn với nguồn chưa được chấp nhận |
| lo2-036 | Hỗn hợp | Thứ tự nhánh bảy yếu tố, quy định song song của bộ khác; hiệu lực QĐ16/2008 và Luật Giáo dục nghề nghiệp |
| lo2-041 | Hỗn hợp | Câu hỏi thẩm quyền phạt có phải nêu cá nhân/tổ chức? Đọc Luật XLVPHC đúng phiên bản và NĐ127/2021 |
| lo2-043 | Hỗn hợp | Luật Xuất bản áp dụng năm 2011; câu hỏi nhập thiết bị ngành in có đủ ghim máy photocopy màu không? |
| lo2-049 | Phạm vi/cách chấm | T3 theo số khoản hay theo nội dung khi cùng chủ đề chuyển khoản và câu hỏi không ghim lĩnh vực? |
| supp18-001 | Thiếu nguồn | Quy định kiểm tra luật sư cá nhân tại 01/07/2013, NĐ28/2007 và giai đoạn chuyển đổi Điều92a(2) |
| supp18-002 | Thiếu nguồn | Đọc đủ Điều67 Luật15/2023 và quy định suất ăn/thuê ngoài; kiểm cả hợp đồng, chế biến tại bệnh viện, giám sát |
| supp18-004 | Thiếu nguồn | Quy phạm hướng dẫn QĐ24/2014/cắt giảm thủ tục: còn đúng thành phần thuyết minh dự án tại 18/02/2019 không? |

Nguồn đầy đủ, lời văn lập luận và lineage ID: xem `open_cases_for_CMT.jsonl`.
Không dùng bảng tóm tắt này thay việc đọc nguồn gốc để quyết định pháp luật.

## 3. Trình tự xử lý đề xuất cho phiên ngày mai

### Bước A — Đóng khoảng trống nguồn

- [ ] Mở lại danh sách 23 ca và phân biệt: chưa lấy được nguồn, đã lấy nhưng
  chưa đọc đủ, và đã đọc nhưng chưa xác định phạm vi pháp lý.
- [ ] Đọc toàn văn chính thức có sẵn trước khi gọi web; đối chiếu đúng số
  hiệu/phiên bản. Không dùng metadata hiệu lực làm căn cứ thay điều hiệu lực.
- [ ] Mỗi ca có câu hỏi thực sự hỏi gì, as_of, văn bản gốc/tác động, hiệu lực,
  chuyển tiếp và ứng viên kế thừa. Đánh dấu chính xác điều khoản đã/chưa đọc.
- [ ] Cho hai bên cùng bộ bằng chứng đầy đủ; nguồn dài được chia đoạn, không
  cắt mất điều khoản quyết định. Giữ cache, URL, hash và phân biệt cached/live.
- [ ] Với Q4=`khong`, ghi phạm vi tìm kiếm hữu hạn theo bước 7(a)–(d), nguồn
  đã kiểm và lý do ứng viên không phù hợp. Không đòi chứng minh tuyệt đối
  không tồn tại bất kỳ quy phạm nào; cũng không suy không có từ một tìm kiếm rỗng.

Hồ sơ nguồn đã có trong
`data/review/ai_research/2026-11-08_lo2/schema_validated/adjudication_native/full_sources/`:
index theo batch, bản trích toàn văn không giới hạn 30.000 ký tự, hash. Nguồn
cached là toàn văn chính thức lấy sẵn, không phải một lượt kiểm live mới.

### Bước B — CMT/luật sư chốt nguyên tắc chung

Các ý sau chỉ là đề xuất để xem xét; chưa sửa tài liệu authority:

| Quyết định cần có | Hướng đề xuất |
|---|---|
| Đơn vị nội dung T2/T3 | Theo nội dung pháp lý trả lời phần câu hỏi hỏi, không theo số khoản đơn thuần |
| R3 đè lên từ trước cả hai mốc | Q2 xét đáp án pháp lý thực tế; Q4 ghi nguyên nhân quy phạm thay thế |
| Phạm vi câu hỏi rộng hơn đáp án | Chấm lỗi phạm vi ở Q3; không lấy thay đổi ngoài phần hỏi để tạo tương phản |
| Bất định Q4 | Phân biệt chưa đọc đủ nguồn với chưa chắc quan hệ pháp lý sau khi đã đọc |
| Bảy yếu tố chuyển chỗ | Viết rõ thứ tự ưu tiên, điều kiện dừng và yếu tố không áp dụng; quy định song song xử lý thế nào |
| Cá nhân/tổ chức và nguồn chính thức | Chốt tiêu chí chung, không quyết tùy từng ca để chọn nhãn mong muốn |

- [ ] Mỗi nguyên tắc được chấp thuận có căn cứ, người quyết định, ngày, ví dụ
  đạt và không đạt; nếu cần đổi thẻ thì phiên bản mới phải được ghi rõ.
- [ ] Giải thích vì sao đây là làm rõ cách vận hành hay thay đổi định nghĩa.
  Không tự thay phạm vi bài toán để giải hết tranh chấp.

### Bước C — Chốt ca và kiểm phạm vi ảnh hưởng

- [ ] Có nguồn và nguyên tắc đủ rõ thì giao legal-adjudicator kiểm lại toàn bộ
  Q/reason, không chỉ chọn bên có verdict mong muốn.
- [ ] Một Q sai chắc chắn nhưng Q khác thiếu nguồn: ghi riêng kết luận cục bộ;
  không gọi toàn bộ nhãn sufficient chỉ vì đã đủ căn cứ không giữ câu.
- [ ] Ca còn bất định thực chất tiếp tục cách ly khỏi test chính; không ép
  đạt/không đạt để đủ số lượng hoặc để bảng hết unresolved.
- [ ] Rà 19 câu cùng đạt nhưng có ít nhất một bên thiếu nguồn.
- [ ] Khi đổi cách hiểu quy tắc, rà mọi câu chịu ảnh hưởng, kể cả trước đây
  hai AI đồng ý. Không chỉ sửa 23 ca đang lệch.
- [ ] Giữ nhãn ban đầu, kết quả kiểm mới và xác nhận CMT thành các lớp riêng;
  không ghi đè hồ sơ đã được duyệt hoặc file/hash đã khóa.

### Bước D — Kiểm định độc lập sau khi làm rõ

- [ ] Chọn trước một lô mới chưa được thảo luận; đề xuất khởi đầu theo lô 30
  câu của G1, tăng mẫu nếu khoảng tin cậy rộng hoặc quá ít ca bất lợi.
- [ ] Hai bên gán độc lập, cùng thẻ/nguồn/công cụ; khóa nhãn trước khi xem nhau.
- [ ] Báo từng Q và verdict: n, nhãn bất lợi, ma trận, AC1, p_neg, κ, KTC.
  Không coi undefined hoặc `not_evaluable` là đạt.
- [ ] Có bộ ca khó để kiểm áp dụng nguyên tắc, nhưng báo riêng với mẫu đại
  diện; không trộn mẫu cố tình giàu ca khó rồi gọi là tỷ lệ toàn bộ dữ liệu.
- [ ] Nếu nhiều câu chung văn bản/sự kiện, xem xét KTC theo cụm văn bản/sự kiện;
  không coi các mốc cùng lineage là mẫu độc lập. Phương pháp KTC cần định trước.
- [ ] Nếu vẫn không đạt, công bố đúng và đi đường lui G1 đã ghi; không đổi
  chỉ số/ngưỡng hoặc chạy nhiều lượt để chọn lượt đẹp nhất.

## 4. Cách hiểu cổng và giới hạn phương pháp

Master-plan G1 quy định làm rõ hướng dẫn với luật sư, thử lô 30 câu khác;
trượt tiếp thì vẫn gán đôi và ghi “đồng thuận không đạt”, không hạ ngưỡng.
G2 còn yêu cầu đủ số lượng, báo số đo toàn phần gán đôi, gold mù, VBHN,
datasheet/manifest và không rò dev. Vì vậy không nên diễn giải “AC1 thấp” thành
nghiên cứu phải dừng vô thời hạn; cũng không được gọi cổng đã PASS sau duyệt.

- Phân biệt **đồng thuận AI–AI**, **nhãn CMT chấp nhận** và **độ đúng pháp lý
  kiểm chứng độc lập**. CMT đã xem nhãn AI nên không gọi phép đo tiếp theo
  giữa CMT và những nhãn đó là đồng thuận mù người–AI hay người–người.
- Không tính đồng thuận sau hòa giải để thay số trước hòa giải.
- Không loại ca lệch/thiếu nguồn khỏi số đo cũ; không chỉ đo trên 162 câu được giữ.
- Không dùng lại câu đã biết kết quả rồi tuyên bố đó là kiểm định mù mới.
- Thay thẻ lớn có thể đòi rà lại toàn bộ phạm vi liên quan; báo riêng các phiên
  bản/lượt, không gộp thành một phép đo như chưa có thay đổi.
- Ngưỡng 0,80/0,60 là tiêu chí hiện hành của dự án; không phải chứng minh tự
  động về độ đúng pháp lý, và không đổi hồi cứu để hợp kết quả.

## 5. Kiểm tra đã có và lệnh tra cứu

Các lệnh sau kiểm/đóng gói **bằng chứng hiện có**, không giải quyết ca mở bằng
chính việc chạy lại. Script có thể cập nhật summary/hash và tạo phiếu nếu
chưa có; không chạy như lệnh read-only. Summary hòa giải là trạng thái trước
phê duyệt, phải đọc kèm `cmt_acceptance.json`. Sau thay đổi nguồn/nhãn cần
lưu phiên mới và quyết định tác động trước, không ghi đè kết quả cũ.

```sh
.venv/bin/python data/review/ai_research/2026-11-08_lo2/finalize_native.py
.venv/bin/python data/review/ai_research/2026-11-08_supp18/package_review.py
```

Validator owner:
`data/review/ai_research/2026-11-07_adjudication_all/package_review.py:load_validate`.
Không hạ yêu cầu validator về evidence_status để ép ca thành resolved.

Phiên lập hồ sơ này chỉ lưu phân tích/checklist; không chạy lại gán nhãn,
không sửa thẻ, không thay kết luận pháp lý hay quyết định CMT.

## 6. Tài liệu phương pháp đã đối chiếu

1. Artstein, R. & Poesio, M. (2008). *Inter-Coder Agreement for Computational
   Linguistics*. Computational Linguistics, 34(4), 555–596.
   [Bài gốc](https://aclanthology.org/J08-4004/),
   [PDF](https://aclanthology.org/J08-4004.pdf).
   Phân biệt reliability/validity: hai người đồng ý vẫn có thể cùng sai;
   diễn giải hệ số phải xét mục tiêu, cách gán và phân bố nhãn.
2. Oortwijn, Y., Ossenkoppele, T. & Betti, A. (2021). *Interrater Disagreement
   Resolution: A Systematic Procedure to Reach Consensus in Annotation Tasks*.
   [Bài gốc](https://aclanthology.org/2021.humeval-1.15/),
   [PDF](https://aclanthology.org/2021.humeval-1.15.pdf).
   Phân tích nguyên nhân bất đồng, thống nhất khái niệm và hướng dẫn; khi thay
   cách hiểu khái niệm phải xem lại cả các nhãn đã đồng ý.
3. Gwet, K. L. (2008). *Computing inter-rater reliability and its variance in
   the presence of high agreement*. British Journal of Mathematical and
   Statistical Psychology, 61, 29–48.
   [PubMed/abstract](https://pubmed.ncbi.nlm.nih.gov/18482474/),
   [DOI](https://doi.org/10.1348/000711006X126600).
   Đã đối chiếu abstract, không khẳng định đã đọc toàn văn bài này. AC1 xử lý
   một số hạn chế của κ; không thay việc sửa nguồn và thẻ gán nhãn.

Các bước thao tác đề xuất ở mục 3 là vận dụng cho repository này, không phải
quy trình nguyên văn hoặc bảo đảm sẽ nâng đồng thuận lên ngưỡng.
