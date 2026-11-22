# Đăng ký trước: kiểm chất lượng ViLexTime bản 6.x (22/11/2026)

Tài liệu này được commit **trước khi giao bất kỳ phiếu nào** của W1, W2, W3. Commit hash ghi vào
`docs/plans/active/2026-11-22-dib-qa-v6.md`.
- Sau mốc này, mọi thay đổi luật phải ghi ở mục 7 (Sai lệch), kèm ngày và lý do. Bài báo cáo cả bản luật cũ lẫn bản mới.
- Kết quả được tính trên bản phát hành 6.0.0: `data/vilextime_dib/vilextime.jsonl`, sha256 `78387004f2cd…`.

## 0. Người tham gia và độ mù

| Vai | Ai | Được làm | Không được làm |
|---|---|---|---|
| A, B | Nhóm gán nhãn hai người, giữ như đợt random30. A là đồng tác giả | Đọc mù W1, chấm W2, xác nhận ứng viên W3 | Mở file có đáp án kho; trao đổi với nhau trước khi cả hai khóa phiếu |
| Luật sư | Luật sư cộng tác | Chốt mọi xung đột (mục 1.5) | — |
| CMT | Tác giả duyệt | Chốt ca máy móc, ra quyết định ở các điểm kiểm | Đọc hay chấm, vì đã thấy mọi đáp án |
| Claude | Agent | Dựng phiếu, so máy, tìm ứng viên W3, đề xuất phân xử | Đứng tên gold, chấm thay người |

- **Xác nhận độ mù.** Trước lô đầu tiên, A và B mỗi người ký một dòng trong `data/review/qa_v6/attestation.md`:
  chưa mở `data/review/gold_random30/*.reveal.tsv`, `KET_QUA.md`, `data/vilextime_dib/`, repo phát hành, hay bất kỳ
  file nào có đáp án kho của các lineage trong phiếu.
- Ai đã xem đáp án của lineage nào thì không đọc lineage đó, và việc này được ghi lại.
- Nếu một người đã đọc lời văn của một điều khoản ở đợt trước, chấm W2 ghi cờ `seen_provision` cho câu đó.

## 1. W1: đọc mù để phủ mọi trạng thái đáp án

**Đơn vị.** Một cặp (lineage, trạng thái đáp án). Trạng thái là một phiên bản (`version_id`) hoặc trạng thái "không
còn hiệu lực". Bộ 6.0.0 có 362 cặp. Đợt 1–3 đã phủ 135 cặp, mỗi lineage một ngày (`blind_gold.as_of_read`).

**Mẫu, tất định:**
- **W1a**, phủ lineage: 64 lineage chưa ai đọc. Mỗi lineage một dòng, chọn ngẫu nhiên như random30:
  `random.Random("20261122:w1a:<lineage_id>").choice(rows sắp theo as_of)`.
  Kết quả: 64 dòng (35 two_versions, 29 control). Xong W1a thì 199/199 lineage có người đọc.
- **W1b**, phủ trạng thái: mọi cặp còn chưa phủ sau W1a. Mỗi cặp lấy **dòng có `as_of` muộn nhất** trong trạng
  thái đó, vì dòng muộn nhất nhạy nhất với lỗi "kho giữ một phiên bản quá hạn".
  Kết quả: 163 dòng (128 two_versions, 23 repealed, 12 multi_versions). Xong W1b thì 362/362 cặp có người đọc.
- Hai người cùng đọc toàn bộ 227 dòng.
- Thứ tự trong phiếu xáo bằng `random.Random("20261122:w1:order")`. Các dòng của cùng một lineage không đặt liền
  nhau. Lô 1 gồm toàn bộ W1a; W1b chia thành các lô khoảng 55 dòng.
- Phiếu có cùng các cột như random30. Không có đáp án kho, ngày chuyển, nhóm hay id dòng.

**Chấm.** Máy so, người đọc không tự chấm. Một dòng "khớp kho" khi:
- `hieu_luc` bằng nhau;
- với dòng còn hiệu lực: lời văn người đọc dán, sau chuẩn hóa (NFC, chữ thường, bỏ dấu câu, gộp khoảng trắng), nằm
  trong lời văn của kho. Đây là hàm `machine_agrees` trong `scripts/pipeline/build_dib_release.py`.

**1.5 Xung đột và phân xử.**
- *Xung đột* là một trong ba trường hợp: A khác B; ít nhất một người khác kho; người phân xử không chắc.
- `legal-adjudicator` đề xuất kết luận kèm trích nguyên văn từ văn bản ban hành hoặc Công báo.
- **Luật sư chốt mọi xung đột có nội dung pháp lý.** CMT chỉ chốt ca máy móc, ví dụ người đọc dán thiếu chữ hoặc
  dán nhầm điểm. Mỗi ca ghi theo mẫu `gold_random30/adjudication.jsonl`.

**Chỉ số:**
- Lỗi kho trên mỗi cặp (lineage, trạng thái) và trên mỗi lineage, theo nhóm, kèm Wilson 95%.
- Đồng thuận A–B về hiệu lực và nội dung: tỷ lệ khớp thô, Gwet AC1, Cohen κ. Nếu một bên chỉ có một hạng, κ ghi
  "không xác định".
- Lỗi của người đọc sau phân xử.
- **Báo riêng W1a và W1b.** W1a là mẫu ngẫu nhiên; W1b được chọn có chủ đích.
- Phút đọc từng dòng là bắt buộc; dòng thiếu phút thì trình nhập từ chối.

**Luật quyết định:**
- Mọi lỗi kho đã xác nhận đều sửa ở tầng kho, đánh cờ `store_corrected_*`, đưa vào CHANGELOG.
- Nếu ≥ 2 lỗi ở control, hoặc có bất kỳ lỗi `kg_missed_amendment` nào, thì W3 làm lineage đó và cả văn bản chứa
  nó trước.

## 2. W2: chấm chất lượng câu hỏi

**Mẫu:**
- 199 câu hỏi của bộ.
- 30 câu hỏi mốc của người dân. Nguồn: chuyên mục hỏi đáp chính sách trên cổng thông tin của Chính phủ và các bộ,
  thuộc 4 lĩnh vực của đề cương (đất đai, thuế, doanh nghiệp–đầu tư, giao thông). Lấy theo thứ tự đăng mới nhất
  trước ngày 22/11/2026.
  - Chỉ nhận câu hỏi về một quy định chung, không nhận câu hỏi xin tư vấn cho riêng một vụ việc.
  - Chỉ giữ câu hỏi chính. Bỏ tên người, số hiệu văn bản và ngày tháng.
  - Ghi URL nguồn. Chỉ dùng để chấm, không phát hành nguyên văn.
- 10 câu chạy thử: rút ngẫu nhiên từ `annotation/excluded_lineages.jsonl`, `random.Random("20261122:w2:pilot")`.

**Lượt 1, chỉ có câu hỏi:**
- 229 câu xáo trộn (`random.Random("20261122:w2:order")`). Người chấm không biết câu nào là câu mốc.
- `ro_nghia`: 1 là không hiểu được câu hỏi gì; 3 là hiểu nhưng phải đoán một phần; 5 là rõ hoàn toàn.
- `tu_nhien`: 1 là không ai hỏi như vậy; 3 là có thể nhưng gượng; 5 là giống người thật hỏi.
- **Lượt 1 phải khóa trước khi mở W1 lô 1.**

**Lượt 2, chỉ 199 câu của bộ, kèm lời văn điều khoản tại một ngày:**
- `tra_loi_duy_nhat`: có / không / không chắc.
- `lo_dap_an`: có / không.

**Chạy thử:** 10 câu theo cả hai lượt. Sửa câu chữ của thang nếu cần, rồi khóa thang. Giữ lại bản chạy thử.

**Chỉ số:**
- Phân phối điểm theo `question_source.model`, theo nhóm, và cho câu mốc.
- Krippendorff α thứ bậc cho thang 1–5; AC1 cho các câu có/không.
- Tương quan Spearman giữa `tu_nhien` và tỷ lệ token đáp án có trong câu hỏi.

**Luật quyết định: gắn cờ, không xóa, không viết lại.**
- Câu bị gắn cờ khi cả A và B chọn `tra_loi_duy_nhat = không` hoặc `lo_dap_an = có`, và người phân xử đồng ý. Mã
  lấy từ §7: `question_ambiguous`, `unanswerable_as_asked`, `question_leaks`.
- Dòng của câu bị gắn cờ có `recommended_eval: false`. Mọi dòng khác có `true`.
- Bài báo cáo cả hai tập: toàn bộ và tập khuyến nghị.

## 3. W3: đối chiếu với nguồn độc lập với vbpl

**Nguồn**, theo thứ tự:
1. Chú thích văn bản sửa đổi, bổ sung trong VBHN của cơ quan ban hành.
2. Công báo.
3. Lawgical.
4. Trang thứ ba: chỉ dùng để gợi ý, không dùng làm căn cứ.

**Cách làm:**
- Với mỗi văn bản, agent lập danh sách văn bản sửa đổi và bãi bỏ từ nguồn trên **mà không nhìn kho**.
- Máy so danh sách đó với sự kiện của kho cho điều khoản đích và các điều khoản cấp trên. Văn bản tác động chưa có
  trong kho, hoặc có mà bị từ chối, thành ứng viên.
- A hoặc B đọc văn bản tác động của mọi ứng viên. Xung đột xử lý như mục 1.5.

**Cổng tin cậy, chạy trước:**
- Chạy cách làm trên trạng thái kho trước khi sửa của 6 lineage có lỗi đã biết. Phải tìm ra ≥ 5/6. Không đạt thì
  sửa cách làm, chạy lại, và ghi cả lần trượt.
- Rút ngẫu nhiên 10% lineage không có ứng viên (`random.Random("20261122:w3:neg")`). A hoặc B tra độc lập các
  lineage này để ước lượng tỷ lệ bỏ sót.

**Thứ tự:** control, multi_versions, two_versions, repealed.

**Luật quyết định:**
- Lỗi đã xác nhận thì sửa như W1.
- Nếu tổng số lineage có lỗi mới vượt 10 (5% của 199), CMT quyết định nộp bản sửa hay chờ thêm. Quyết định ghi vào
  plan.

## 4. Mốc dừng

- **Thứ Tư 25/11, tối:** nếu dự kiến không xong W1, B chỉ đọc W1a và 30% W1b, rút bằng
  `random.Random("20261122:w1:b30")`. A vẫn đọc hết. Đồng thuận A–B tính trên phần chung.
- **Thứ Năm 26/11, 23:59: chốt dữ liệu.** Phần chưa xong giữ nguyên trạng thái "chưa đọc", không ngoại suy.

## 5. Không làm trong 6.x

- Viết lại câu hỏi.
- Thêm nhóm hay mã loại.
- Đổi định nghĩa.
- Dựng gold độc lập với kho.

## 6. Giới hạn biết trước

- Người đọc thấy cùng một câu hỏi ở nhiều ngày. Điều đó gợi ý rằng đáp án có thể đổi giữa các ngày ấy.
- Ngày kiểu ranh giới có thể gợi ý ngày chuyển của kho.
- A là đồng tác giả.
- Ở W1, người đọc và kho dùng cùng lời văn của vbpl. W3 là bước bù cho giới hạn này.

## 7. Sai lệch so với đăng ký

Mọi mục dưới đây ghi ngày 22/11/2026, trước khi giao phiếu W2 nào.

**S1. Nguồn và lĩnh vực của 30 câu mốc (§2).**
- Chỉ lấy từ một cổng: chinhsachonline.chinhphu.vn (Cổng Giải đáp chính sách của Chính phủ). Cổng không chia theo
  4 lĩnh vực; agent web-fetch xếp câu vào lĩnh vực theo nội dung.
- Cổng gần như không có câu hỏi về hoạt động vận tải. Đọc 12 trang mục Xây dựng (từ 02/10 đến 22/11/2026) chỉ được 6
  câu gắn với giao thông, đều về công trình giao thông hoặc hành lang đường bộ. Ngoài ra có M29 (chi phí gói thầu có
  phần công trình giao thông) và M30 (cầu, kè qua công trình thủy lợi), giữ lại để đủ 30.
- Chia lĩnh vực: đất đai 8, thuế 8, doanh nghiệp–đầu tư 7, xây dựng 1, giao thông 6 (trong đó 2 câu ranh giới).
  Đăng ký trước không định số câu mỗi lĩnh vực.
- Ghi chú: 199 lineage của bộ trải trên nhiều lĩnh vực hơn 4 lĩnh vực này (đếm theo tên văn bản, chỉ khoảng 24 văn bản
  thuộc giao thông). Vì vậy câu mốc là mốc "câu người thật hỏi về pháp luật", không khớp lĩnh vực với bộ.
- Câu đăng đúng ngày 22/11/2026 bị loại, theo chữ "trước ngày 22/11/2026".

**S2. "Chỉ giữ câu hỏi chính" được làm thành một luật kiểm được bằng máy.**
- Thư của người dân dài và có ngữ cảnh. Bản đưa vào phiếu chỉ được: (1) bỏ nguyên câu; (2) xóa số hiệu văn bản, ngày
  tháng năm, tên người, địa danh; (3) viết hoa chữ đầu câu khi phần xóa đứng đầu câu. Không thêm hay thay chữ nào.
- Giữ lại các câu dẫn cần để hiểu câu hỏi (tránh "trường hợp trên" không rõ là gì). Tham chiếu Điều, Khoản được giữ,
  vì đăng ký trước chỉ yêu cầu bỏ số hiệu văn bản.
- Nguyên văn, bản rút gọn và URL nằm trong `data/review/qa_v6/w2/moc_src.py`. Hàm `check()` kiểm luật này; đã thử âm
  (thêm một chữ thì bị bắt).

**S3. Giới hạn mới của W2: độ mù về nguồn câu yếu.** Câu mốc dài hơn và thường xưng "tôi", nên người chấm có thể
đoán câu nào là câu của người dân. Bài phải ghi điều này khi so điểm câu mốc với câu của bộ.

**S4. Lời văn ở lượt 2 của bản chạy thử.** Dùng phiên bản đầu tiên của lineage. Với lineage cấp khoản không có lời
văn riêng trong kho, dùng lời văn của Điều chứa nó. Bản chạy thử chỉ để thử câu chữ của thang, không dùng để tính số.

**S5. Cờ `seen_provision` (§0).** Lượt 1 có cột tự khai `da_gap` (có / không). Ngoài ra `pass1_key.tsv` ghi bằng máy
vai người đã đọc mù lineage đó ở đợt trước (`read_before_by`). Bài báo cáo cả hai.
