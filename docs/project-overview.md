# Tổng quan đề tài và hiện trạng dự án

> Tài liệu này liên kết nội dung trong đề cương khóa luận với phần đã được triển
> khai trong repository `graphrag-legal-thesis`. Mục đích là tạo một điểm tham
> chiếu chung trước khi tiếp tục xây dựng Stage 6 và hệ thống hỏi đáp.
>
> Cập nhật: 11/09/2026.

## 1. Thông tin đề tài

**Tên tiếng Việt:** Truy xuất tăng cường dựa trên đồ thị tri thức có nhận biết
thời gian cho hỏi đáp pháp luật Việt Nam theo mốc hiệu lực.

**Tên tiếng Anh:** Temporal-Aware Knowledge Graph RAG for Point-in-Time
Vietnamese Legal Question Answering.

Đề tài giải quyết bài toán hỏi đáp pháp luật theo mốc thời gian. Đầu vào không
chỉ là câu hỏi pháp lý `x`, mà là cặp `(x, t)`, trong đó `t` là thời điểm phát
sinh hành vi hoặc quan hệ pháp luật cần tra cứu. Đầu ra gồm câu trả lời `a` và
tập bằng chứng `E` ở cấp Điều/Khoản/Điểm còn hiệu lực tại thời điểm `t`.

Mục tiêu quan trọng nhất là giảm **ảo giác theo thời gian**: hệ thống có thể
trích đúng số hiệu điều luật nhưng sử dụng sai phiên bản hiệu lực.

## 2. Câu hỏi và giả thuyết nghiên cứu

Đề tài đặt ra ba câu hỏi nghiên cứu:

- **RQ1:** Các LLM và hệ thống RAG hiện có áp dụng sai phiên bản quy phạm ở mức
  độ nào trên pháp luật Việt Nam?
- **RQ2:** Biểu diễn văn bản pháp luật bằng đồ thị theo phiên bản có giảm lỗi so
  với RAG phẳng và GraphRAG không có thời gian hay không?
- **RQ3:** Mức cải thiện đến từ cấu trúc đồ thị hay chỉ từ việc lọc theo metadata
  thời gian?

Giả thuyết chính là việc mô hình hóa tường minh chuỗi phiên bản và lan truyền
hiệu lực trên cây điều khoản sẽ tốt hơn việc chỉ lọc theo ngày hiệu lực ở cấp
văn bản. Lợi ích dự kiến rõ nhất ở các câu hỏi cần truy vết nhiều lần sửa đổi.

## 3. Sản phẩm nghiên cứu dự kiến

Đề tài hướng tới bốn nhóm sản phẩm:

1. **ViLexTime:** bộ dữ liệu hỏi đáp pháp luật tiếng Việt theo mốc thời gian,
   có câu hỏi tương phản và bằng chứng cấp Điều/Khoản/Điểm.
2. **Temporal Legal Knowledge Graph:** đồ thị tri thức biểu diễn cấu trúc văn
   bản, quan hệ pháp lý, phiên bản và khoảng hiệu lực.
3. **Temporal GraphRAG:** hệ thống lọc hiệu lực, truy xuất lai, mở rộng theo đồ
   thị, sinh câu trả lời và kiểm chứng trích dẫn.
4. **Khung đánh giá:** các chỉ số chuẩn cùng TVER, VCR và TCS để đo độ tin cậy
   thời gian.

## 4. Kiến trúc mục tiêu L0–L5

### L0–L1: Cấu trúc văn bản và quan hệ metadata

- Thu thập văn bản từ `vbpl.vn`.
- Biểu diễn cây phân cấp linh hoạt: Văn bản → Phần/Chương/Mục → Điều → Khoản →
  Điểm.
- Lưu metadata như ngày ban hành, ngày hiệu lực, cơ quan ban hành, loại văn bản
  và trạng thái hiệu lực.
- Tạo các cạnh giữa văn bản như sửa đổi, thay thế, bãi bỏ, đính chính, hợp nhất
  và dẫn chiếu.

### L2: Trích xuất thao tác sửa đổi

Chuẩn hóa nội dung sửa đổi thành các sự kiện gần với dạng:

```text
(target_unit, operation, new_text, effective_time, source_document)
```

Trong đó `operation` thuộc các nhóm sửa đổi, bổ sung, thay thế, bãi bỏ hoặc tạm
ngưng. Regex/luật hình thức xử lý các mẫu chuẩn; mô hình ngôn ngữ chỉ hỗ trợ ca
phức tạp và kết quả phải kiểm chứng được.

### L3: Hợp nhất phiên bản và lan truyền hiệu lực

Mỗi đơn vị pháp lý `u` có chuỗi phiên bản `V_u`. Mỗi phiên bản tồn tại trên một
khoảng nửa mở `[eff_from, eff_to)`. Hàm cốt lõi là:

```text
snapshot(u, t) = phiên bản của u có khoảng hiệu lực chứa t
```

Hiệu lực cấp con phụ thuộc vào hiệu lực của tổ tiên trong cây. Bãi bỏ một Chương
làm vô hiệu cây con; bãi bỏ riêng một Khoản không làm Điều cha mất hiệu lực.

### L4: Truy xuất có ràng buộc thời gian

Trước tiên lọc không gian tìm kiếm về các đơn vị hợp lệ tại `t`, sau đó kết hợp:

- tín hiệu từ vựng;
- embedding/ngữ nghĩa;
- reranking;
- mở rộng láng giềng qua các cạnh đồ thị thích hợp.

### L5: Sinh câu trả lời và kiểm chứng

- Sinh câu trả lời có trích dẫn cấp Điều/Khoản/Điểm.
- Temporal Verifier kiểm tra từng trích dẫn có đúng phiên bản và còn hiệu lực
  tại thời điểm truy vấn hay không.
- Giao diện cho phép chọn mốc thời gian và xem đường dẫn bằng chứng.

## 5. Hiện trạng repository

Repository hiện tập trung vào crawler và phần nền dữ liệu cho đồ thị thời gian.
Theo README, corpus đầy đủ ở môi trường làm việc gốc gồm khoảng 20.749 văn bản,
148.505 cạnh và hơn 1,19 triệu node điều khoản. Các thư mục dữ liệu lớn không
được đưa vào Git; checkout chỉ giữ mã nguồn, bảng mã đã xác minh, quyết định
review và các thống kê cần thiết.

| Thành phần | Trạng thái | Đầu ra/chức năng chính |
|---|---|---|
| Stage 1: phát hiện seed | Đã có | `data/seeds.json`, 9.806 seed duy nhất trong 4 miền |
| Stage 2: forward BFS | Đã có | Mở rộng qua cạnh phả hệ hữu hạn |
| Stage 2b: reverse closure | Đã có | 2.335 reverse seed, tìm “ai đã sửa/bãi bỏ tôi” |
| Stage 3: tải văn bản | Đã có | Raw JSON, edges và manifest; hỗ trợ resume |
| Mapping quan hệ | Đã có | 13 `referenceType` được đóng băng và kiểm tra fail-loud |
| Stage 4: rà soát lĩnh vực | Đã có | Danh sách ứng viên và 8 loại trừ do người duyệt |
| Stage 5a: cây điều khoản | Đã có | Cây cấu trúc từ Next.js server action |
| History backfill | Đã có | Chuỗi sự kiện hiệu lực làm đầu vào cho Stage 6 |
| Stage 5b: ghép nội dung | Đã có | Ghép bằng UUID hoặc marker; ca yếu đưa vào review |
| Delta crawl | Đã có | Phát hiện cache cũ và làm mới theo pipeline hiện hữu |
| Stage 6/L2–L3 | Chưa có | Trích xuất sửa đổi, version chain, validity propagation, snapshot |
| L4–L5 | Chưa có | Retrieval, generation, verifier và giao diện |
| ViLexTime và thực nghiệm | Chưa có | Dataset, baseline, ablation và metric |

## 6. Luồng dữ liệu hiện tại

```text
Sitemap vbpl.vn
    ↓ lọc slug theo 4 miền
data/seeds.json
    ↓ forward BFS qua references[]
data/raw/*.json + data/edges.jsonl + manifest.sqlite
    ↓ /diagram, đọc documentNamesBySource
data/reverse_seeds.json
    ↓ tải cây + lịch sử hiệu lực
data/trees/*.json + data/history/*.json
    ↓ ghép documentContent.content vào node cây
data/provisions/*.json
    ↓ chưa triển khai
Temporal graph + version chains + snapshot(u, t)
    ↓ chưa triển khai
Temporal retrieval + answer generation + verifier
```

Các package chính:

- `sources/`: giao tiếp với sitemap, JSON gateway và nguồn cây điều khoản.
- `storage/`: quy ước lưu dữ liệu và manifest SQLite.
- `vocab/`: bảng mã quan hệ, trạng thái và chính sách rà soát lĩnh vực.
- `graph/`: forward expansion và reverse-edge closure.
- `provisions/`: đọc cây và gắn nội dung vào từng node.
- `scripts/pipeline/`: các bước chạy pipeline có checkpoint.
- `scripts/check/`: kiểm tra tính nhất quán và ước lượng recall.
- `scripts/review/`: các bước cần quyết định của con người.
- `tests/`: kiểm thử các hành vi cốt lõi của crawler và parser.

## 7. Phạm vi dữ liệu

Bốn miền hiện tại:

| Miền | Số seed |
|---|---:|
| Đất đai, nhà ở, bất động sản | 772 |
| Thuế, phí, hải quan, hóa đơn | 3.486 |
| Doanh nghiệp, đầu tư, chứng khoán | 3.745 |
| Giao thông | 2.545 |

Phạm vi chỉ gồm văn bản cấp trung ương. Văn bản hết hiệu lực vẫn được giữ vì
chúng là dữ liệu bắt buộc cho truy vấn lịch sử. Các cạnh dẫn chiếu mở được ghi
nhận nhưng không dùng để crawl đệ quy nhằm tránh mở rộng sang toàn bộ cơ sở dữ
liệu ngoài phạm vi.

## 8. Các nguyên tắc dữ liệu phải giữ nguyên

1. **Không lọc bỏ văn bản vì đã hết hiệu lực.** Phiên bản cũ là thành phần chính
   của bài toán point-in-time.
2. **Không tự động loại văn bản theo `documentFields` hoặc `documentMajors`.**
   Metadata này thiếu và có trường hợp gán sai; nó chỉ tạo ứng viên review.
3. **Không đoán mã lạ.** `referenceType` và trạng thái history chưa có trong
   bảng xác minh phải làm pipeline dừng rõ ràng.
4. **Không coi mọi `createdDate` là ngày pháp lý.** Chỉ dòng history do `Job`
   tạo được dùng trực tiếp làm mốc pháp lý; dòng `Admin` thường là thời gian
   nhập liệu.
5. **Không coi dữ liệu thiếu là một giá trị phủ định.** Không có metadata không
   đồng nghĩa văn bản đã đổi, bị xóa hoặc không thuộc phạm vi.
6. **Không đoán căn chỉnh điều khoản.** Node không ghép chắc chắn phải bị bỏ qua
   và đưa vào review, không được gán gần đúng âm thầm.
7. **Giữ raw data và provenance.** Biến đổi về sau phải truy ngược được tới văn
   bản, node và sự kiện nguồn.
8. **Hiệu lực cấp văn bản không đại diện cho mọi điều khoản.** Trạng thái “hết
   hiệu lực một phần” bắt buộc phải được xử lý ở cấp cây.

## 9. Các vấn đề Stage 6 phải giải quyết

### 9.1. Thiếu phạm vi hết hiệu lực ở cấp điều khoản

Phần lớn văn bản hết hiệu lực một phần không có `expiryProvisions` đủ chi tiết.
Đường dự phòng là tìm văn bản tác động qua các cạnh bãi bỏ/sửa đổi/thay thế rồi
phân tích chính nội dung của văn bản đó.

### 9.2. Ánh xạ mô tả pháp lý sang node ổn định

Các biểu thức như “điểm đ khoản 3 Điều 6”, “các Điều 5, 7 và 12” hoặc “bãi bỏ
Chương II” phải được giải thành đúng UUID node trong cây của đúng văn bản đích.
Việc ánh xạ cần hỗ trợ nhiều mục tiêu, cây con và các node có tiêu đề bất thường.

### 9.3. Ngữ nghĩa của thao tác sửa đổi

Cần phân biệt ít nhất:

- thay toàn bộ nội dung node;
- chèn node mới vào một vị trí;
- bãi bỏ node hoặc cả cây con;
- thay cụm từ ở một hay nhiều điều;
- tạm ngưng rồi khôi phục hiệu lực;
- thay thế toàn bộ văn bản;
- sửa đổi gián tiếp qua nhiều văn bản.

### 9.4. Xung đột và độ tin cậy nguồn

`effFrom/effTo`, history, metadata quan hệ và câu chữ trong văn bản tác động có
thể không hoàn toàn trùng nhau. Stage 6 cần quy tắc ưu tiên nguồn, lưu lại bằng
chứng và phát cảnh báo thay vì âm thầm chọn một giá trị.

### 9.5. Tái lập và kiểm toán

Mỗi phiên bản sinh ra nên truy được về:

- văn bản và node gốc;
- văn bản gây sửa đổi;
- câu/mệnh đề sửa đổi đã trích xuất;
- mốc hiệu lực được sử dụng;
- phương pháp trích xuất và mức tin cậy;
- trạng thái kiểm duyệt thủ công nếu có.

## 10. Hướng triển khai tiếp theo hợp lý

Thứ tự phụ thuộc đề xuất:

1. Chốt schema cho document, provision, version, legal event và provenance.
2. Xây bộ phân tích sự kiện sửa đổi L2 với fixture thực tế và hàng đợi review.
3. Xây resolver ánh xạ mục tiêu pháp lý sang node UUID.
4. Áp dụng sự kiện theo thứ tự hiệu lực để tạo version chain.
5. Cài đặt lan truyền hiệu lực và `snapshot(u, t)`.
6. Kiểm chứng thủ công `snapshot` trên ít nhất 100 truy vấn như đề cương.
7. Xuất temporal graph sang storage được chọn sau khi mô hình miền đã ổn định.
8. Xây ViLexTime theo hướng diff-driven từ các version chain đã kiểm chứng.
9. Cài đặt B1–B7, ưu tiên B7 để kiểm tra sớm đóng góp thực của đồ thị.
10. Xây L4–L5, Temporal Verifier, metric và các ablation A1–A7.

## 11. Tiêu chí hoàn thành tối thiểu cho Stage 6

Stage 6 chỉ nên được xem là hoàn thành khi:

- mọi node và phiên bản có định danh ổn định;
- khoảng hiệu lực dùng quy ước nửa mở `[eff_from, eff_to)` nhất quán;
- sửa đổi/bổ sung/bãi bỏ/thay thế hoạt động ở cấp Điều/Khoản/Điểm;
- bãi bỏ node cha vô hiệu hóa đúng cây con;
- `snapshot(u, t)` trả kết quả tất định và kèm provenance;
- sự kiện không giải được không bị áp dụng âm thầm;
- có thống kê coverage, lỗi và hàng đợi review;
- các trường hợp nhiều bước A → B → C có test;
- ít nhất 100 truy vấn snapshot đã được đối chiếu thủ công;
- pipeline có thể chạy lại mà không tạo phiên bản hoặc cạnh trùng.

## 12. Giới hạn đã xác định

- Chỉ xử lý hiệu lực theo thời gian, chưa bao phủ đầy đủ hiệu lực theo lãnh thổ
  và đối tượng áp dụng.
- Chỉ xử lý văn bản cấp trung ương.
- Chưa xử lý bảng biểu, phụ lục ảnh và dữ liệu đa phương thức.
- Việc hợp nhất tự động có thể sai và không có giá trị thay thế tư vấn pháp lý.
- Không huấn luyện lại LLM; đóng góp tập trung vào dữ liệu, biểu diễn tri thức,
  truy xuất và kiểm chứng.
- Một số văn bản cũ có cây không đánh số hoặc nội dung không thể căn chỉnh đáng
  tin cậy.
- Ý nghĩa chữ số cuối của `HHL1P1`–`HHL1P4` chưa xác định; chỉ tiền tố “hết hiệu
  lực một phần” được sử dụng.

## 13. Ghi chú về checkout hiện tại

Các thư mục crawl lớn như `data/raw/`, `data/history/`, `data/trees/`,
`data/provisions/`, `data/diagrams/`, `data/edges.jsonl` và
`data/manifest.sqlite` được loại khỏi Git. Vì vậy, các thống kê corpus trong tài
liệu là thống kê của lần chạy đầy đủ, không thể tái kiểm chứng chỉ từ checkout
nhẹ hiện tại nếu chưa khôi phục dữ liệu crawl.

## 14. Domain model nền cho Stage 6

Module `src/legal_crawler/temporal/models.py` là lớp mô hình độc lập với Neo4j
và Milvus, biểu diễn các khái niệm bắt buộc của đề cương:

- `LegalDocument`: văn bản nguồn, kể cả văn bản cũ hoặc hết hiệu lực;
- `Provision`: định danh ổn định của Phần/Chương/Mục/Điều/Khoản/Điểm;
- `ProvisionVersion`: nội dung của một đơn vị trên khoảng `[start, end)`;
- `LegalEvent`: thao tác sửa đổi đã chuẩn hóa cùng trạng thái kiểm duyệt;
- `Provenance`: bằng chứng và phương pháp tạo ra một fact;
- `GraphEdge`: quan hệ có kiểu và có thể mang khoảng hiệu lực;
- các enum dùng chung cho loại node, cấp điều khoản, thao tác và quan hệ.

Đây là source of truth ở tầng domain. Adapter Neo4j/Milvus sau này chỉ chuyển
đổi các object này sang schema lưu trữ, không tự định nghĩa lại ngữ nghĩa thời
gian. Sự kiện chưa xác định được ngày hoặc node đích vẫn được lưu ở trạng thái
`needs_review`, nhưng không được phép áp dụng vào chuỗi phiên bản.
