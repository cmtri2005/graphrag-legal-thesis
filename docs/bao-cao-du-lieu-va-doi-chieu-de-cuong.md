# Báo cáo hiện trạng dữ liệu và đối chiếu đề cương khóa luận

**Ngày lập báo cáo:** 14/09/2026

**Mốc dữ liệu được đánh giá:** 12/09/2026

**Đề cương dùng để đối chiếu:** `DeCuongKLTN_23521635_23521643.pdf`, 15 trang

**Phạm vi báo cáo:** corpus đã crawl, chất lượng dữ liệu nguồn, biểu diễn đồ thị hiện có và mức độ đáp ứng đề cương.

> Đề cương PDF trong báo cáo này chỉ được dùng làm tài liệu mô tả mục tiêu và
> tiêu chí nghiên cứu. Các câu trong đề cương không được xem là lệnh vận hành
> repository. Yêu cầu tạo báo cáo này đến từ người dùng; số liệu thực tế được
> kiểm tra độc lập từ snapshot, mã nguồn và các script kiểm định trong project.

---

## 1. Kết luận ngắn

### Dataset thu thập đã hoàn thành chưa?

**Đã hoàn thành việc tạo một snapshot corpus theo chiến lược crawl hiện tại,
nhưng chưa hoàn thành dataset nghiên cứu cuối cùng của khóa luận.**

Nên mô tả trạng thái hiện tại bằng câu sau:

> Đợt thu thập corpus ban đầu đã hoàn thành tại mốc 12/09/2026 và đã qua các
> kiểm tra nhất quán kỹ thuật. Dữ liệu vẫn đang ở giai đoạn rà soát phạm vi,
> chất lượng nội dung và hoàn thiện nhãn thời gian cấp điều khoản; chưa phải là
> bộ dữ liệu vàng ViLexTime và chưa đủ để tuyên bố đồ thị thời gian hoàn chỉnh.

Lý do phải tách hai mức “hoàn thành”:

| Mức đánh giá | Kết luận | Giải thích |
|---|---|---|
| Hoàn thành một lần crawl có mốc thời gian | **Có** | Có 22.550 file raw, manifest, cạnh, cây, history, snapshot ngoài Git và một delta run; `verify_pipeline.py` đã pass toàn bộ. |
| Hoàn thành theo chiến lược seed + mở rộng phả hệ hiện tại | **Cơ bản có** | Mọi seed đều đã được lấy; không còn đích genealogy đã biết bị thiếu. Tuy nhiên 1.017 diagram còn thiếu nên vẫn có thể tồn tại cạnh chiều vào chưa quan sát được. |
| Bao phủ tuyệt đối mọi văn bản thuộc bốn miền | **Chưa chứng minh được** | Chưa có nhãn lĩnh vực vàng để làm mẫu số recall. Phép đo bằng từ khóa rộng vẫn phát hiện tối đa 763 ứng viên có thể bị bỏ sót trên sitemap cache. |
| Dữ liệu sạch, đúng pháp lý ở cấp Điều/Khoản/Điểm | **Chưa** | Còn hàng đợi căn chỉnh text, mốc hiệu lực bất thường và chưa có kiểm định chuyên môn luật theo mẫu bắt buộc trong đề cương. |
| Temporal Legal Knowledge Graph hoàn chỉnh | **Chưa** | Index hiện mới tạo một version cho mỗi provision có text và kế thừa khoảng hiệu lực cấp văn bản; L2 chưa tạo chuỗi sửa đổi thật trên toàn corpus. |
| ViLexTime 1.150 câu | **Chưa** | Chưa có artifact benchmark, nhãn vàng, kiểm định chéo 300 câu hoặc Cohen's kappa. |

---

## 2. Căn cứ và phương pháp đánh giá

Báo cáo sử dụng bốn lớp bằng chứng:

1. **Đề cương PDF đính kèm:** chuẩn đối chiếu mục tiêu, phạm vi, kiến trúc L0–L5,
   ViLexTime và yêu cầu kiểm định.
2. **Snapshot dữ liệu cục bộ:** `data/SNAPSHOT.txt`, `data/raw/`, `data/trees/`,
   `data/history/`, `data/provisions/`, `data/diagrams/`, `data/edges.jsonl` và
   `data/temporal.sqlite`.
3. **Mã nguồn hiện tại:** cách crawl, chuẩn hóa cạnh, ingest và truy vấn snapshot
   trong `src/legal_crawler/`.
4. **Kiểm tra thực thi ngày 13/09/2026:**
   `scripts/check/verify_pipeline.py`, `scripts/check/data_status.py` và
   `scripts/pipeline/build_store.py`.

Thông tin snapshot:

| Thuộc tính | Giá trị |
|---|---:|
| `as_of` | 2026-09-12 |
| Số văn bản khai báo | 22.550 |
| Commit tạo snapshot | `5b8ee70b1b80874f7ec98ff8653f63f6ac557d66` |
| Thời điểm đóng gói | 2026-09-13T11:46:15Z |
| Kiểm tra checksum khi pull | Đạt |

Vì pháp luật và vbpl.vn tiếp tục thay đổi, mọi kết luận “đã thu thập xong” trong
báo cáo đều phải hiểu là **đúng tại mốc 12/09/2026**, không phải hoàn thành vĩnh
viễn.

---

## 3. Mô tả chi tiết corpus

### 3.1. Nguồn dữ liệu và cách thu thập

Nguồn chính là Cơ sở dữ liệu quốc gia về văn bản quy phạm pháp luật `vbpl.vn`,
đúng nguồn được đề cương chỉ định. Pipeline lấy dữ liệu JSON từ gateway công
khai của cổng, thay vì parse phần HTML giao diện.

Luồng thu thập hiện tại:

1. Đọc 12 sitemap shard Trung ương.
2. Lọc seed bằng từ khóa trên slug cho bốn miền.
3. Mở rộng chiều xuôi qua `references[]` để lấy phả hệ văn bản.
4. Đọc `/diagram` để tìm chiều vào: văn bản nào sửa đổi, bãi bỏ, thay thế hoặc
   tác động lên văn bản đang giữ.
5. Tải raw JSON, cây điều khoản, lịch sử hiệu lực và diagram.
6. Căn chỉnh body HTML với node cây để tạo dữ liệu text cấp provision.
7. Chạy delta để cập nhật văn bản mới hoặc văn bản thay đổi.
8. Đóng gói snapshot, kiểm checksum và dựng lại SQLite index từ dữ liệu nguồn.

`data/raw/{id}.json` là lớp dữ liệu nguồn trong project. Mỗi record có thể gồm:

- ID cổng, số hiệu, tiêu đề, loại văn bản và cơ quan ban hành;
- ngày ban hành, ngày hiệu lực, ngày hết hiệu lực và trạng thái hiệu lực;
- nội dung HTML;
- lĩnh vực/ngành do cổng gán;
- danh sách quan hệ tới văn bản khác;
- các cờ như văn bản hợp nhất, văn bản hành chính, có nội dung hoặc có PDF gốc.

Lưu ý: project giữ response JSON và nội dung HTML, **chưa lưu đầy đủ file PDF
gốc**. Vì vậy khả năng tái lập snapshot dữ liệu API đã tốt, nhưng chưa tương
đương lưu bản sao nguyên trạng của mọi văn bản ký số, phụ lục, bảng biểu hoặc
ảnh trên cổng.

### 3.2. Quy mô theo tầng

| Tầng dữ liệu | Số lượng | Độ phủ so với raw | Đánh giá |
|---|---:|---:|---|
| Raw document | 22.550 | 100,00% | Hoàn thành snapshot |
| Provision tree | 22.532 | 99,92% | Thiếu 18 văn bản đã được ghi nhận |
| History | 22.548 | 99,99% | Thiếu 2 văn bản đã được ghi nhận |
| Diagram | 21.533 | 95,49% | Thiếu 1.017; ảnh hưởng khả năng thấy cạnh chiều vào |
| Provision text artifact | 19.279 | 85,49% | Phần lớn khoảng trống do văn bản không có cấu trúc điều khoản |
| Cạnh giữa văn bản | 157.795 | — | 71.799 genealogy và 85.996 open citation |
| Provision trong SQLite | 1.264.594 | — | Toàn bộ node của các cây không rỗng |
| Provision version có text | 1.136.483 | 89,87% số provision | Hiện mỗi provision tối đa một version từ source hiện có |

Khoảng trống 3.271 văn bản không có artifact provision text được giải thích
như sau:

| Nguyên nhân | Số văn bản |
|---|---:|
| Không có tree artifact | 18 |
| Cây rỗng/không có cấu trúc Điều/Khoản/Điểm | 3.236 |
| Có cây nhưng API không trả body text | 17 |
| Không giải thích được | 0 |

Ngoài ra:

- 54 raw document không có body HTML.
- 287 file provision tồn tại nhưng không căn chỉnh được node text nào.
- Tổng cộng 304 văn bản có cấu trúc nhưng không sinh được version có text khi
  dựng SQLite: 17 trường hợp không có body và 287 trường hợp kết quả căn chỉnh
  rỗng.
- 778 văn bản có coverage dưới 50%; nhóm này khai báo 123.415 node nhưng chỉ
  căn chỉnh được 9.561 node có text.
- Ngoài nhóm coverage thấp, text đạt 1.126.922/1.138.700 node, tương đương
  **98,97%**.
- Nếu tính tất cả provision có artifact căn chỉnh, coverage là
  1.136.483/1.262.115, tương đương **90,04%**.
- Nếu tính thêm 2.479 node cấu trúc của 17 văn bản không có body, coverage text
  trên toàn bộ 1.264.594 provision là **89,87%**.

Ba mẫu số trên đo ba câu hỏi khác nhau, vì vậy không nên chỉ báo cáo con số
98,97% mà bỏ qua hàng đợi review và các văn bản không có body.

### 3.3. Phạm vi bốn miền

Số seed là số membership theo miền, không phải số văn bản độc lập:

| Miền | Dự kiến trong PDF | Seed hiện có | So với dự kiến |
|---|---:|---:|---:|
| Đất đai | 700 | 772 | 110,3% |
| Thuế – phí – hải quan – hóa đơn | 3.000 | 3.486 | 116,2% |
| Doanh nghiệp và đầu tư | 3.000 | 3.745 | 124,8% |
| Giao thông | 2.000 | 2.545 | 127,3% |
| Tổng dự kiến | 8.700 | 9.806 seed ID duy nhất | 112,7% |

Tổng bốn dòng seed là 10.548 membership; có 742 membership trùng do một văn bản
có thể khớp nhiều miền. Sau mở rộng phả hệ, corpus tăng lên 22.550 văn bản,
tương đương 259,2% quy mô 8.700 văn bản dự kiến.

Không được diễn giải 22.550 là “mỗi miền đều có hơn kế hoạch”, vì các văn bản
do BFS và reverse expansion kéo vào chưa có nhãn miền độc quyền. Nhiều văn bản
chỉ là mắt xích cần thiết để giữ đầy đủ chuỗi sửa đổi.

Phép đo recall cục bộ trên `central_sitemap.json` cache cho thấy:

| Chỉ số | Giá trị |
|---|---:|
| Vũ trụ sitemap Trung ương trong cache | 57.074 |
| Văn bản corpus nằm trong cache | 20.818 |
| Văn bản corpus không nằm trong cache | 1.732 |
| Văn bản Trung ương trong cache không giữ | 36.256 |
| Ứng viên bị từ khóa rộng đánh dấu có thể thuộc bốn miền | 763 ID duy nhất |
| Seed khớp bộ từ khóa chính nhưng còn thiếu | 0 |

763 là **cận trên dựa trên từ khóa rộng**, không phải 763 văn bản chắc chắn bị
bỏ sót. Trong đó có các nhóm gây tranh cãi như kế toán, kiểm toán, đấu thầu hoặc
xuất nhập khẩu. Cache sitemap cũng cũ hơn delta run gần nhất, nên cần refresh và
duyệt thủ công trước khi dùng số này làm recall chính thức.

### 3.4. Phạm vi Trung ương và loại văn bản

Đề cương giới hạn ở văn bản quy phạm pháp luật cấp Trung ương. Corpus vật lý
hiện rộng hơn giới hạn này vì graph expansion giữ cả văn bản hỗ trợ:

| Dấu hiệu từ metadata nguồn | Số văn bản | Tỉ lệ corpus |
|---|---:|---:|
| `organization.orgType = 0` | 21.218 | 94,09% |
| `organization.orgType = 1` | 1.275 | 5,65% |
| Thiếu `orgType` | 57 | 0,25% |
| `docType.parentCode = VBQPPL` | 21.507 | 95,37% |
| Không mang parent code `VBQPPL` | 1.043 | 4,63% |
| Văn bản hợp nhất | 481 | 2,13% |
| Văn bản hành chính được cổng đánh dấu | 5 | 0,02% |

Nhóm `orgType = 1` có nhiều cơ quan địa phương như Tuyên Quang, Cà Mau, Nghệ
An, Lào Cai và Hải Phòng. Metadata của cổng cũng có ngoại lệ bất thường, nên
không nên xóa tự động chỉ bằng một cờ. Cách đúng là:

- giữ chúng trong **corpus hỗ trợ/phả hệ** để không làm đứt quan hệ;
- thêm cờ **eligible_for_retrieval** và **eligible_for_benchmark**;
- chỉ dùng tập Trung ương + QPPL đã được xác nhận khi báo cáo thực nghiệm theo
  phạm vi đề cương.

---

## 4. Độ chính xác và độ tin cậy của dữ liệu

### 4.1. Không nên dùng một con số “accuracy” duy nhất

Độ chính xác của corpus có nhiều lớp khác nhau. Việc file JSON hợp lệ không
chứng minh ngày hiệu lực đúng; ngày hiệu lực đúng ở cấp văn bản cũng không
chứng minh một Khoản còn hiệu lực. Báo cáo vì vậy tách các lớp sau.

| Lớp chất lượng | Bằng chứng hiện có | Đánh giá hiện tại |
|---|---|---|
| Nguồn và truy vết | Mỗi document có ID nguồn; index sinh URL vbpl.vn; raw response được giữ trong snapshot | **Tốt về provenance**, nhưng không thay thế xác minh văn bản gốc/PDF |
| Toàn vẹn file raw | 22.550/22.550 JSON hợp lệ; 0 ID lệch tên file; 0 thiếu title | **Đạt về kỹ thuật** |
| Mapping quan hệ | 13/13 code xuất hiện đều có mapping; nhãn cạnh hiện tại không stale | **Tốt**, nhưng code 2 được xác nhận bằng loại trừ thay vì quan sát UI trực tiếp |
| Đầy đủ phả hệ đã biết | 0/15.394 đích genealogy chưa được lấy hoặc giải trình | **Đạt trong tập cạnh đã quan sát** |
| Cây cấu trúc | 99,92% văn bản có tree | **Độ phủ cao**, không đồng nghĩa 100% đúng nội dung |
| Căn chỉnh text | 98,97% ngoài review; 89,87% trên toàn cấu trúc | **Tốt với dữ liệu khớp được**, còn đuôi lỗi đáng kể |
| Metadata thời gian cấp văn bản | Có `effFrom`, `effTo`, `effStatus` và history | **Có ích nhưng nhiễu/thiếu**, cần chính sách bảo thủ |
| Hiệu lực cấp provision | Có `expiryProvisions` và resolver nền | **Chưa hoàn thiện**, chưa đủ để cấp chứng nhận pháp lý |
| Độ đúng pháp lý cuối cùng | Chưa có 200 mẫu L2, 100 snapshot và kiểm định chuyên gia như đề cương | **Chưa đo được** |

Nguồn vbpl.vn là nguồn chính thống được đề cương lựa chọn và có giá trị cao cho
nghiên cứu. Tuy nhiên, dữ liệu tự động trích từ cổng vẫn có thể sai, thiếu hoặc
không phản ánh đầy đủ bản gốc. Vì thế sản phẩm phải ghi rõ: kết quả nghiên cứu
không có giá trị thay thế tư vấn pháp luật hay văn bản chính thức.

### 4.2. Chất lượng cấu trúc và text

Các kiểm tra và hàng đợi hiện có cho thấy:

- 243 văn bản được ghi trong `tree_content_mismatch.txt`: cây khai báo Điều mà
  body không thể hiện tương ứng.
- 778 văn bản có coverage dưới 50%.
- `provision_review.txt` hiện chỉ có 20 record dữ liệu, trong khi phép quét phát
  hiện 778 văn bản dưới ngưỡng. Gate hiện tại chỉ kiểm tra file review có tồn
  tại, chưa kiểm tra đủ từng ID. Vì vậy hàng đợi review phải được tái sinh đầy
  đủ trước khi tuyên bố mọi lỗi coverage đã được quản lý.
- 17 văn bản có cây nhưng không có body text; trong đó có văn bản luật và văn
  bản sửa đổi thuộc miền nghiên cứu.
- Dữ liệu cũ có hai dạng HTML khác nhau. Dạng hiện đại cho phép join bằng UUID;
  dạng cũ cần heuristic và dễ gặp cây không đánh số, node trùng tiêu đề hoặc
  cấu trúc kiểu `I.`/`1.1.`.

Các nguyên tắc đúng đang được code áp dụng là dùng node ID ổn định, không đoán
node khi cấu trúc mơ hồ và đưa trường hợp chất lượng thấp vào review. Điểm còn
thiếu là phải hoàn thiện chính hàng đợi review và báo cáo kết quả duyệt.

### 4.3. Chất lượng metadata thời gian

Phân bố trạng thái hiệu lực theo raw source:

| Trạng thái | Số văn bản |
|---|---:|
| Hết hiệu lực toàn bộ | 12.206 |
| Còn hiệu lực | 7.745 |
| Hết hiệu lực một phần | 2.051 |
| Thiếu `effStatus` | 467 |
| Chưa có hiệu lực | 31 |
| Ngưng hiệu lực | 30 |
| Không còn phù hợp | 20 |

Các bất thường ảnh hưởng trực tiếp tới truy vấn point-in-time:

| Bất thường | Ảnh hưởng |
|---|---:|
| 724 văn bản thiếu `effFrom` | 29.410 version node không có neo thời gian |
| Văn bản hết hiệu lực toàn bộ nhưng thiếu `effTo` | 14.700 version node không xác định được lúc kết thúc |
| Thiếu `effStatus` | 5.244 version node |
| 29 trường hợp `effTo < effFrom` | 451 version node thuộc nhóm lỗi này trong audit temporal |
| 74 trường hợp `effTo = effFrom` | Cũng bị loại vì khoảng nửa mở rỗng |
| Tổng `effTo <= effFrom` bị bỏ khi ingest | 103 văn bản |
| “Còn hiệu lực” nhưng `effTo` đã qua | 13 version node |
| Tổng không gian truy xuất chưa neo được thời gian | 49.818/1.136.483 node, **4,4%**, thuộc 1.819 văn bản |

Index hiện áp dụng các quy tắc sau:

- không tự dùng `issueDate` thay cho `effFrom`;
- version không có `valid_from` sẽ không được trả về cho truy vấn tại thời điểm
  `t`;
- `effTo <= effFrom` bị bỏ, nhưng document và text vẫn được giữ;
- khoảng hiệu lực dùng quy ước nửa mở `[valid_from, valid_to)`.

Quy tắc với `valid_from` là bảo thủ và tránh tạo câu trả lời từ ngày đoán. Tuy
nhiên, cách bỏ một `effTo` lỗi hiện biến version thành khoảng **mở vô hạn**.
Tương tự, văn bản được đánh dấu hết hiệu lực toàn bộ nhưng thiếu `effTo` vẫn có
thể được `version_at()` trả về sau `valid_from`, vì truy vấn hiện chỉ xét hai
cột ngày và chưa xét `raw_status_code`. Đây là rủi ro false-positive về hiệu
lực, không chỉ là giảm recall.

Con số 49.818 node/4,4% đến từ phép audit hiện tại và không cộng 74 trường hợp
`effTo = effFrom`; do đó nó là số đo tối thiểu của vùng dữ liệu có vấn đề, chưa
phải cận trên đầy đủ. Trước khi dùng index cho benchmark, các document có
`effTo <= effFrom` hoặc đã hết hiệu lực nhưng thiếu ngày kết thúc phải được gắn
`temporal_anchor = false`/đưa vào review, thay vì mặc nhiên coi là open-ended.

### 4.4. Hiệu lực một phần và dữ liệu history

Fresh scan của history ghi nhận:

| Dữ liệu `expiryProvisions` | Số occurrence |
|---|---:|
| “Toàn bộ văn bản” | 23.532 |
| Cấp Điều/Khoản/Điểm | 31.175, trên 1.432 văn bản |
| Tổng occurrence | 54.707 |
| File history không có entry | 549 |

`expiryProvisions` cho biết **đơn vị nào** hết hiệu lực, nhưng không tự cung cấp
đủ bộ ba “ai tác động – tác động gì – có hiệu lực khi nào”. `createdDate` trong
history có thể là thời điểm cổng nhập dữ liệu, không phải ngày hiệu lực pháp lý.
Muốn dựng `eff_to` cấp provision phải nối:

1. mô tả đơn vị trong `expiryProvisions`;
2. cạnh tới văn bản sửa đổi/bãi bỏ;
3. `effFrom` của văn bản tác động;
4. nội dung điều khoản sửa đổi khi có nhiều tác nhân khả dĩ.

Audit ngày 12/09 từng ghi nhận resolver map được 22.847/31.175 occurrence cấp
provision, tương đương 73,3%; theo cặp mô tả không trùng là 5.956/8.412,
tương đương 70,8%. Có 274 trường hợp mơ hồ. Artifact
`data/expiry_targets.jsonl` không nằm trong snapshot hiện tại, nên các số mapping
này phải được tái sinh sau lần build store mới trước khi dùng làm kết quả chính
thức.

### 4.5. Độ chính xác của cạnh

Kết quả kiểm tra hiện tại:

- 157.795 cạnh đọc được từ `edges.jsonl`.
- 0 cạnh có source không nằm trong corpus.
- 0 nhãn cạnh lệch bảng mapping hiện hành.
- 13/13 mã `referenceType` đã được nhận diện.
- 0 đích genealogy chưa được tải hoặc giải trình.
- 15/19.037 văn bản có `references[]` không xuất hiện trong cạnh; tỉ lệ nhỏ hơn
  ngưỡng gate 1%, nhưng vẫn cần xem lại nếu dùng graph cho benchmark.
- 1.839/8.959 đích open citation không được giữ. Đây là chủ ý phạm vi: cạnh mở
  được ghi nhận nhưng không dùng để mở rộng vô hạn.

Mapping của 12 code đã được đối chiếu trực tiếp trên UI. Code `2` (“Văn bản
được công bố”) được xác nhận bằng suy luận loại trừ và đã được nhóm chấp nhận;
đây là code có mức bằng chứng yếu hơn các code còn lại và nên được ghi chú
trong luận văn.

---

## 5. Mô tả phần đồ thị

### 5.1. Ba lớp cần phân biệt

```text
Lớp thu thập
raw JSON + history + tree + diagram
        |
        v
Lớp đồ thị quan hệ văn bản
22.550 Document -- 157.795 quan hệ metadata --> Document
        |
        v
Lớp index cấu trúc/thời gian hiện tại
Document -> Provision hierarchy -> ProvisionVersion [from, to)
```

Đồ thị hiện không phải một database graph duy nhất. Hai artifact vật lý chính
là:

- `data/edges.jsonl`: mạng quan hệ giữa văn bản;
- `data/temporal.sqlite`: bảng `documents`, `provisions`, `versions` phục vụ
  truy vấn cấu trúc và snapshot.

Quan hệ Điều/Khoản/Điểm trong SQLite được biểu diễn bằng `parent_id` và
materialized path. Quan hệ version được biểu diễn bằng `versions.provision_id`.
Các cạnh trong `edges.jsonl` **chưa được import vào SQLite**, và SQLite hiện
chưa có bảng legal event.

### 5.2. Node

| Node logic | Số lượng hiện có | Vai trò |
|---|---:|---|
| `Document` | 22.550 | Văn bản nguồn, metadata, trạng thái và URL truy vết |
| `Provision` | 1.264.594 | Định danh ổn định cho Phần/Chương/Mục/Tiểu mục/Điều/Khoản/Điểm |
| `ProvisionVersion` | 1.136.483 | Text của provision trên một khoảng hiệu lực |
| `LegalEvent` | Chưa materialize từ corpus | Sửa đổi, bổ sung, bãi bỏ, thay thế, đính chính, tạm ngưng hoặc tiếp tục hiệu lực |

Mỗi provision dùng ID của tree source và có `document_id`, `level`, `parent_id`,
`order_index`, `path`. Mỗi version có `ordinal`, `text`, `valid_from`,
`valid_to`. Version không có `valid_from` vẫn được lưu nhưng không được trả về
trong point-in-time query.

### 5.3. Cạnh giữa văn bản

| Code | Quan hệ tiếng Việt | Nhóm | Số cạnh |
|---:|---|---|---:|
| 3 | Căn cứ ban hành | Open citation | 67.601 |
| 10 | Văn bản được sửa đổi bổ sung | Genealogy | 29.129 |
| 9 | Văn bản được quy định chi tiết, hướng dẫn thi hành | Genealogy | 19.559 |
| 4 | Văn bản được dẫn chiếu | Open citation | 17.999 |
| 1 | Văn bản bị bãi bỏ | Genealogy | 12.159 |
| 12 | Văn bản được thay thế | Genealogy | 9.772 |
| 7 | Văn bản được hợp nhất | Genealogy | 874 |
| 8 | Văn bản được hướng dẫn áp dụng | Open citation | 349 |
| 6 | Văn bản được đính chính | Genealogy | 209 |
| 11 | Văn bản bị tạm ngưng hiệu lực | Genealogy | 50 |
| 5 | Văn bản bị đình chỉ thi hành | Genealogy | 47 |
| 14 | Văn bản được giải thích | Open citation | 24 |
| 2 | Văn bản được công bố | Open citation | 23 |
| **Tổng** |  | **71.799 genealogy + 85.996 open citation** | **157.795** |

Chiều cạnh được chuẩn hóa theo hướng văn bản “ra tay” là source. Ví dụ, văn bản
B sửa A được lưu theo hướng `B -> A`. API gốc chỉ thể hiện một chiều trong
`references[]`, nên `/diagram.documentNamesBySource` được dùng để tìm các văn
bản tác động theo chiều ngược rồi chuẩn hóa về cùng hướng.

### 5.4. Đồ thị thời gian hiện làm được gì?

Đã làm được:

- giữ định danh document/provision ổn định;
- giữ cây cha–con và truy vấn hậu duệ;
- lưu text theo `ProvisionVersion`;
- áp dụng khoảng nửa mở `[from, to)`;
- truy vấn một version hợp lệ tại ngày `t` khi có mốc thời gian;
- không trả version thiếu `valid_from`;
- dựng index tất định từ snapshot mà không cần dịch vụ graph bên ngoài.

Chưa làm được trên dữ liệu thật:

- trích xuất đầy đủ bộ bốn `(target, operation, new_text, effective_time)` từ
  văn bản sửa đổi;
- nối `LegalEvent` với văn bản nguồn, provision đích và version được tạo/đóng;
- dựng nhiều version thật cho một provision qua chuỗi A -> B -> C;
- đóng version cấp Khoản/Điểm theo bãi bỏ một phần;
- lan truyền hiệu lực từ node cha xuống toàn cây con bằng dữ liệu sự kiện thật;
- giải dẫn chiếu động theo snapshot;
- cung cấp provenance hoàn chỉnh cho từng thay đổi;
- kiểm chứng 100 snapshot thủ công theo đề cương.

Điểm quan trọng nhất: `build_versions()` hiện ghi rõ corpus chỉ có current
consolidated text, nên mỗi provision có text được tạo **một version ordinal 1**
và kế thừa `effFrom/effTo` của document. Đây là base hợp lệ để tiếp tục làm L2
và L3, nhưng chưa phải Temporal Legal Knowledge Graph hoàn chỉnh mà đề cương mô
tả.

---

## 6. Đối chiếu trực tiếp với đề cương PDF

| Yêu cầu trong đề cương | Trang PDF | Bằng chứng hiện tại | Mức đáp ứng | Khoảng trống |
|---|---:|---|---|---|
| Thu thập từ vbpl.vn, giữ bản gốc và ghi nguồn/phương pháp | 6, 8 | Raw API snapshot, source URL, manifest, docs pipeline, snapshot có checksum | **Đáp ứng phần lớn** | Chưa giữ đầy đủ PDF/file gốc và phụ lục; cần mô tả rõ raw API JSON là artifact gốc của pipeline |
| Bốn miền, khoảng 8.700 văn bản | 8–9 | 9.806 seed duy nhất; 22.550 sau graph expansion | **Vượt quy mô nhưng lệch cách đếm** | Cần chốt tập đánh giá đúng miền; không dùng toàn corpus hỗ trợ như corpus benchmark |
| Chỉ văn bản QPPL cấp Trung ương | 12 | 21.507 record mang parent code `VBQPPL`; 1.275 record mang `orgType=1` | **Chưa đáp ứng ở corpus vật lý** | Tạo eligibility view thay vì xóa mắt xích phả hệ |
| Cây Văn bản -> Chương -> Mục -> Điều -> Khoản -> Điểm | 6, 8–9 | 22.532 tree; 1.264.594 provision; parent/path ổn định | **Đáp ứng phần nền** | 18 tree thiếu, 243 mismatch, 778 coverage thấp, 304 structured document không có version text |
| Chuẩn hóa metadata hiệu lực và liên kết L0–L1 | 6, 9 | 13 relation code, 157.795 cạnh, metadata ngày/trạng thái | **Cơ bản đạt** | Metadata nguồn nhiễu; 1.017 diagram thiếu; 4,4% node chưa neo thời gian |
| L2 trích xuất sửa đổi bằng rule + LLM, đo trên 200 mẫu | 7, 9 | Có domain model, target resolver và dữ liệu `expiryProvisions` | **Chưa hoàn thành** | Chưa chạy extraction toàn corpus, chưa có 200 mẫu và precision/recall/F1 hoặc accuracy được kiểm chứng |
| L3 hợp nhất version và lan truyền hiệu lực | 7, 9 | Có model, interval, index và point lookup nền | **Mới là base** | Dữ liệu thật vẫn một version/provision; chưa materialize event hoặc partial repeal |
| Kiểm chứng `snapshot` trên 100 truy vấn thủ công | 9, 15 | Có API/index để truy vấn | **Chưa thực hiện** | Chưa có bộ 100 truy vấn, biên bản đối chiếu và kết quả |
| ViLexTime 1.100–1.300, bảng chốt 1.150 câu | 5, 9–10 | Chưa có dataset benchmark trong repo | **Chưa thực hiện** | Thiếu T1–T6, 200 cặp T2, nhãn vàng và evidence cấp provision |
| Kiểm định chéo 300 câu, Cohen's kappa >= 0,6 | 10 | Chưa có kết quả annotation | **Chưa thực hiện** | Cần guideline, hai annotator, adjudication và chuyên gia luật cho nhóm khó |
| L4 temporal retrieval, hybrid và graph expansion | 7–8, 10 | Có nền model/index; một số module retrieval cũ còn trong source | **Chưa chứng minh trên corpus mới** | Cần pipeline tương thích refactor và thực nghiệm B2–B7 |
| L5 generation và Temporal Verifier | 8, 10 | Có nền code verifier từ base trước | **Chưa có end-to-end evidence** | Chưa có answer artifact và kiểm chứng trích dẫn trên dữ liệu thật |
| B1–B7, TVER/VCR/TCS và A1–A7 | 10–12 | Có một số contract/metric nền | **Chưa thực nghiệm** | Chưa có benchmark nên chưa thể báo cáo kết quả |
| Chỉ xử lý text, không ảnh/bảng đa phương thức | 12 | Pipeline hiện dựa trên HTML/text | **Phù hợp** | Phải công bố giới hạn với PDF, bảng biểu và phụ lục ảnh |

### 6.1. Điểm phù hợp mạnh

- Nguồn dữ liệu đúng vbpl.vn.
- Bốn miền seed khớp phạm vi đề cương và đều vượt số lượng dự kiến.
- Giữ cả văn bản cũ/hết hiệu lực, phù hợp bài toán point-in-time.
- Có cây provision, quan hệ giữa văn bản, metadata thời gian và snapshot có thể
  dựng lại.
- Quy ước `[start, end)` khớp công thức snapshot trong đề cương.
- Cách không đoán ngày khi thiếu dữ liệu phù hợp mục tiêu giảm temporal
  hallucination.

### 6.2. Điểm lệch hoặc chưa đủ

- Corpus thực tế rộng hơn phạm vi Trung ương + QPPL; đây có thể là graph hỗ trợ
  hợp lý nhưng phải tách khỏi tập benchmark.
- Quy mô lớn hơn không bù cho việc thiếu L2, chuỗi version thật và nhãn vàng.
- Metadata cấp document chưa giải quyết trạng thái hết hiệu lực một phần ở cấp
  Khoản/Điểm.
- Chưa có các phép kiểm định thủ công mà chính đề cương yêu cầu.
- Chưa có ViLexTime nên chưa thể trả lời RQ1–RQ3.
- Đề cương nói phân rã T1–T7 ở trang 5 nhưng Bảng 2 trang 9–10 chỉ định nghĩa
  T1–T6 và tổng 1.150 câu. Cần sửa thống nhất trước khi khóa thiết kế benchmark.
- Đề cương viết “bốn mục tiêu cụ thể” nhưng liệt kê năm bullet. Đây là lỗi biên
  tập nhỏ nhưng nên chỉnh khi cập nhật đề cương/khóa luận.

---

## 7. Những việc cần hoàn thành trước khi tuyên bố dataset hoàn chỉnh

### Ưu tiên bắt buộc

1. **Khóa phạm vi nghiên cứu:** tạo nhãn/cờ riêng cho corpus lưu trữ, tập được
   truy xuất và tập đủ điều kiện benchmark; xác nhận Trung ương + QPPL.
2. **Refresh recall:** tải lại sitemap Trung ương, chạy phép đo mới và duyệt 763
   ứng viên từ khóa rộng; báo cáo recall với định nghĩa miền rõ ràng.
3. **Đóng khoảng trống crawl:** xử lý hoặc giải trình 1.017 diagram, 18 tree và
   2 history còn thiếu; chạy lại reverse closure sau khi đủ diagram.
4. **Sửa quản trị review:** tái sinh danh sách đủ 778 văn bản coverage dưới 50%,
   ưu tiên văn bản Luật/Nghị định/Thông tư và các văn bản tác động trong chuỗi
   sửa đổi.
5. **Tái sinh `expiry_targets.jsonl`:** chạy resolver trên SQLite mới, lưu thống
   kê resolved/ambiguous/unresolved và chọn tập kiểm chứng thủ công.
6. **Chặn interval không đáng tin:** không cho point-in-time query trả version
   thuộc văn bản hết hiệu lực nhưng thiếu `effTo`, hoặc có `effTo <= effFrom`,
   cho tới khi có mốc được xác minh.
7. **Hoàn thành L2 trên dữ liệu thật:** trích xuất thao tác sửa đổi, lưu evidence
   span, confidence, trạng thái review và đo trên ít nhất 200 mẫu thủ công.
8. **Materialize L3:** tạo version chain nhiều mốc, đóng/mở interval, áp dụng bãi
   bỏ một phần và lan truyền hiệu lực trên cây.
9. **Kiểm chứng 100 snapshot:** bao gồm biên trước/sau ngày hiệu lực, chuỗi nhiều
   bước, hết hiệu lực một phần, thiếu metadata và mốc bằng nhau.
10. **Xây ViLexTime:** chốt T1–T6 hay T1–T7, tạo 1.150 câu theo diff-driven,
   kiểm định chéo 300 câu và báo Cohen's kappa.

### Không nên làm

- Không xóa văn bản bất thường khỏi corpus vật lý nếu chúng là mắt xích phả hệ.
- Không dùng `documentFields` hoặc `documentMajors` làm bộ lọc tự động tuyệt đối.
- Không coi `issueDate` là `effFrom` nếu chưa có quyết định phương pháp được ghi
  rõ.
- Không dùng `history.createdDate` như ngày hiệu lực pháp lý nếu chưa kiểm tra
  nguồn tạo record.
- Không gọi current consolidated text là chuỗi version lịch sử.
- Không báo cáo 98,97% như coverage toàn corpus mà không nêu mẫu số.
- Không tuyên bố “độ chính xác pháp lý” trước khi hoàn thành kiểm định thủ công.

---

## 8. Trạng thái cuối cùng theo sản phẩm của đề cương

| Sản phẩm | Trạng thái ngày 14/09/2026 |
|---|---|
| Corpus raw bốn miền và phả hệ | **Đã có snapshot, cần re-check phạm vi và độ phủ chiều vào** |
| Dữ liệu cấu trúc Điều/Khoản/Điểm | **Đã có phần lớn, còn review chất lượng** |
| Đồ thị quan hệ văn bản L0–L1 | **Cơ bản hoàn thành** |
| Temporal graph cấp provision L2–L3 | **Mới hoàn thành base/index, chưa hoàn thành dữ liệu sự kiện và version chain thật** |
| ViLexTime | **Chưa hoàn thành** |
| Baseline, hệ thống đề xuất và ablation | **Chưa có kết quả thực nghiệm trên dataset hoàn chỉnh** |

**Kết luận chính thức:** phần thu thập thô không cần crawl lại từ đầu và có thể
dùng làm nền tiếp tục nghiên cứu. Tuy nhiên, tại thời điểm báo cáo, chưa nên
đánh dấu “dataset hoàn thành” trong kế hoạch khóa luận. Trạng thái phù hợp nhất
là **“hoàn thành snapshot thu thập ban đầu; đang kiểm định và hoàn thiện dữ
liệu đồ thị thời gian”**.

---

## 9. Lệnh tái kiểm tra

Chạy từ thư mục gốc project sau khi kích hoạt virtual environment:

```bash
python scripts/check/verify_pipeline.py
python scripts/check/data_status.py
python scripts/pipeline/build_store.py
python scripts/pipeline/resolve_expiry_targets.py
```

Ba lệnh đầu đã được chạy thành công trên snapshot trong lần đánh giá này.
`resolve_expiry_targets.py` cần chạy lại để tái sinh artifact mapping expiry cho
SQLite mới trước khi chốt số liệu L2/L3.
