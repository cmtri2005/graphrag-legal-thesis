# Phương án điền khuyết và backfill dữ liệu

**Ngày lập:** 14/09/2026

**Mốc corpus:** 12/09/2026

**Tài liệu đầu vào:** `docs/bao-cao-du-lieu-va-doi-chieu-de-cuong.md`

**Mục tiêu:** khôi phục tối đa dữ liệu còn thiếu mà không làm mất provenance,
không ghi đè dữ liệu nguồn bằng giá trị suy đoán và không đưa dữ liệu chưa xác
minh vào truy vấn point-in-time hoặc benchmark ViLexTime.

---

## 1. Kết luận

Không nên dùng một cơ chế imputation chung cho tất cả khoảng trống. Các trường
hợp thiếu hiện tại thuộc ba nhóm có bản chất khác nhau:

1. **Chưa tải được artifact:** diagram, tree hoặc history chưa có file.
2. **Nguồn có dữ liệu nhưng pipeline chưa đọc đúng:** HTML có text nhưng bộ căn
   chỉnh chọn sai phương pháp hoặc không nhận dạng được cấu trúc.
3. **Nguồn thực sự thiếu hoặc mâu thuẫn:** không có body, thiếu ngày hiệu lực,
   ngày kết thúc sai hoặc không biết văn bản nào gây ra thay đổi.

Thứ tự xử lý phù hợp là:

```text
Backfill lại từ nguồn
        -> sửa parser bằng quy tắc tất định
        -> suy dẫn từ nhiều nguồn có provenance
        -> review thủ công
        -> imputation chỉ dùng cho phân tích độ nhạy
```

Kết quả thử nghiệm cho thấy:

- backfill diagram có khả năng thành công rất cao;
- một lỗi trong lựa chọn ID/marker đang làm mất ít nhất 4.187 node text có thể
  phục hồi mà không cần đoán nội dung;
- retry endpoint không giải quyết trực tiếp các tree, history và body đã được
  ghi nhận là lỗi;
- có thể tạo mốc `effective_to` ứng viên cho một phần văn bản hết hiệu lực,
  nhưng không được tự động coi các mốc này là ground truth.

---

## 2. Nguyên tắc bắt buộc

### 2.1. Không sửa dữ liệu nguồn bằng giá trị suy đoán

Các file dưới đây phải tiếp tục phản ánh đúng response đã thu thập:

- `data/raw/`;
- `data/history/`;
- `data/trees/` đối với tree lấy trực tiếp từ source;
- `data/diagrams/`.

Giá trị suy dẫn phải nằm trong artifact riêng và luôn mang:

- phương pháp tạo;
- bằng chứng nguồn;
- thời điểm tạo;
- confidence;
- trạng thái review;
- phiên bản schema.

### 2.2. Ưu tiên recovery hơn imputation

Thứ tự độ tin cậy:

| Mức | Loại dữ liệu | Được dùng cho point-in-time? |
|---|---|---|
| 1 | `observed`: lấy trực tiếp từ source hợp lệ | Có |
| 2 | `derived_verified`: suy dẫn tất định và đã kiểm tra | Có |
| 3 | `candidate`: có bằng chứng nhưng chưa đủ chắc chắn | Không |
| 4 | `lower_bound`/`upper_bound`: chỉ xác định được cận | Không như một ngày chính xác |
| 5 | `unknown` | Không |

### 2.3. Không xóa mắt xích phả hệ

Văn bản thiếu text, thiếu ngày hoặc ngoài tập benchmark vẫn được giữ trong
corpus vật lý nếu nó tham gia chuỗi sửa đổi/bãi bỏ/thay thế. Quyền tham gia
retrieval và benchmark phải được quản lý bằng eligibility flag, không bằng xóa
file.

### 2.4. Tách strict dataset và augmented dataset

Nên duy trì ít nhất hai view:

- **Strict:** chỉ sử dụng dữ liệu `observed` và `derived_verified`.
- **Augmented:** bổ sung candidate đã review hoặc dữ liệu phục hồi từ PDF/OCR.

Kết quả chính của khóa luận phải báo cáo trên strict view. Augmented view dùng
cho ablation hoặc phân tích độ nhạy, tránh để imputation làm kết quả có vẻ tốt
hơn thực tế.

---

## 3. Kết quả thử nghiệm khả năng backfill

Các thử nghiệm ngày 14/09/2026 chỉ đọc dữ liệu và gọi endpoint công khai; không
ghi đè corpus.

| Nhóm thiếu | Quy mô | Thử nghiệm | Kết quả | Đánh giá |
|---|---:|---|---:|---|
| Diagram | 1.017 | 60 ID ngẫu nhiên | 60/60 thành công | Nên backfill toàn bộ |
| Tree | 18 | Thử lại toàn bộ, kèm một control thành công | 0/18 phục hồi | Retry trực tiếp ít giá trị |
| History | 2 | Gọi lại `/history` | 0/2, đều 4xx | Không thể backfill từ endpoint hiện tại |
| Body của văn bản có tree | 17 | Gọi lại `/doc/{id}` | 0/17 có body | Phải dùng PDF hoặc nguồn khác |
| Provision có 0 node text | 287 | Thử marker fallback | 27 văn bản, 4.129 node | Có lỗi parser có thể sửa |
| Tất cả văn bản coverage thấp | 778 | So sánh ID join với marker | 31 văn bản tăng 4.187 node | Nên sửa parser rồi reprocess |
| Thiếu `effFrom` | 724 | Tìm `DATE_HL` tin cậy trong history | 0 ứng viên trực tiếp | Không tự động điền |
| Hết hiệu lực toàn bộ nhưng thiếu `effTo` | 685 | Suy từ văn bản bãi bỏ/thay thế | 399 có một ngày ứng viên; 395 ngày sau `effFrom` | Tạo candidate để review |
| `effTo <= effFrom` | 103 | Đối chiếu `DATE_HHL` | Không có xác nhận độc lập đủ mạnh | Giữ trạng thái không neo thời gian |
| Thiếu status | 467 | Đối chiếu history | 374 có status row không do `Job` tạo | Candidate review, không auto-accept |

### 3.1. Chi tiết thử nghiệm diagram

Toàn bộ 60 diagram trong mẫu đều trả payload thành công. Điều này chứng minh
endpoint hiện hoạt động với các ID đang thiếu, nhưng không chứng minh chắc chắn
cả 1.017 ID đều thành công.

Backfill diagram có thể:

- đóng khoảng trống artifact;
- phát hiện thêm văn bản tác động theo chiều vào;
- bổ sung chuỗi sửa đổi/bãi bỏ/thay thế;
- làm thay đổi `raw`, manifest, reverse seeds và graph khi chạy closure đầy đủ.

### 3.2. Chi tiết thử nghiệm tree

Control document trả tree thành công, nên `NEXT_ACTION_ID` hiện tại vẫn hoạt
động. Trong 18 trường hợp thiếu:

- 16 response không có payload row mà parser yêu cầu;
- 2 gặp lỗi kết nối trong lần thử;
- không trường hợp nào tạo được tree mới.

Không nên tiếp tục retry hàng loạt vô hạn. Có thể retry riêng hai lỗi mạng với
backoff, còn 16 trường hợp thiếu payload nên chuyển sang phương án phục hồi từ
HTML.

### 3.3. Chi tiết thử nghiệm body

Cả 17 document vẫn trả `documentContent.content` rỗng khi gọi lại API. Trong
nhóm này:

- 14 record có `hasOriginalPdf = true`;
- cả 17 record có tên file PDF;
- có các văn bản quan trọng như Luật và văn bản sửa đổi thuộc miền nghiên cứu.

Do đó re-fetch JSON không giải quyết được. Hướng tiếp theo là tải PDF qua giao
diện công khai hoặc browser session, sau đó trích text/OCR có provenance.

---

## 4. Phương án A — sửa căn chỉnh provision text

### 4.1. Nguyên nhân đã xác định

`align()` hiện chọn ID join nếu thấy bất kỳ paragraph nào có HTML `id`. Một số
văn bản có ID phục vụ trình bày nhưng không có ID nào giao với provision tree.
Kết quả là:

1. parser chọn ID join;
2. `align_by_id()` không tìm được tree ID;
3. artifact được ghi với 0 node;
4. marker matching, dù có thể tìm được text, không bao giờ được chạy.

### 4.2. Quy tắc sửa

1. Flatten tree và tạo tập `tree_node_ids`.
2. Parse HTML và tạo tập `paragraph_ids`.
3. Chỉ dùng ID join làm phương pháp chính khi:

   ```text
   tree_node_ids intersection paragraph_ids != empty
   ```

4. Nếu không có giao nhau, dùng marker matching.
5. Nếu ID coverage thấp, chạy marker như fallback.
6. Exact-ID match luôn có độ ưu tiên cao hơn marker.
7. Marker chỉ được bổ sung node chưa có và không được ghi đè exact text.
8. Ghi rõ method: `id`, `marker`, hoặc `id_marker_fallback`.

### 4.3. Trường hợp đã chứng minh có thể cứu

| Document ID | Node hiện có | Marker tìm được | Tổng node |
|---|---:|---:|---:|
| `178597` | 0 | 1.808 | 1.885 |
| `178340` | 0 | 506 | 507 |
| `18729` | 0 | 340 | 348 |
| `110455` | 0 | 290 | 290 |
| `163761` | 0 | 237 | 237 |
| `174705` | 0 | 236 | 397 |
| `67154` | 0 | 137 | 137 |
| `178434` | 0 | 122 | 122 |

### 4.4. Cách chạy an toàn

Không chạy `--force` trực tiếp lên toàn corpus ngay sau khi sửa parser. Quy
trình nên là:

1. Lấy danh sách 778 document coverage thấp.
2. Tạo output trong thư mục tạm.
3. Chạy parser cũ và parser mới trên cùng input.
4. So sánh:
   - node count;
   - coverage;
   - exact-ID text có thay đổi hay không;
   - có node lạ hoặc overshoot hay không.
5. Review các document tăng coverage lớn.
6. Chỉ sau khi pass mới promote artifact.

### 4.5. Tiêu chí nghiệm thu

- Có test HTML chứa ID không thuộc tree.
- Có test exact ID được ưu tiên hơn marker.
- Không document nào có số node text lớn hơn số node tree.
- Không exact-ID text nào bị marker ghi đè.
- Ít nhất 31 document đã đo được tăng coverage.
- Tổng node tăng tối thiểu 4.187 trên snapshot hiện tại, trừ khi review phát
  hiện match sai.

---

## 5. Phương án B — tái tạo đầy đủ review queue

### 5.1. Vấn đề

`attach_provision_text.py` bỏ qua artifact đã tồn tại. Danh sách review lại chỉ
được tạo từ các document vừa xử lý trong lần chạy và sau đó ghi đè file cũ.
Vì vậy `provision_review.txt` hiện có 20 record trong khi scan toàn corpus phát
hiện 778 document dưới 50%.

### 5.2. Cách sửa

Tách việc sinh review queue khỏi việc căn chỉnh:

1. Quét toàn bộ `data/provisions/*.json` sau khi pipeline kết thúc.
2. Chọn mọi record có `coverage < threshold`.
3. Sắp xếp ổn định theo `doc_id`.
4. Ghi atomically một file review đầy đủ.
5. Gate phải so sánh tập ID thực tế với tập ID trong review file, không chỉ
   kiểm tra file có tồn tại.

### 5.3. Tiêu chí nghiệm thu

- Số record review bằng đúng số document dưới threshold.
- Thiếu một ID phải làm `verify_pipeline.py` fail.
- Thêm ID không còn dưới threshold cũng phải được phát hiện.
- Chạy lại nhiều lần cho output giống nhau.

---

## 6. Phương án C — backfill diagram và đóng lại graph

### 6.1. Chuẩn bị

Vì `expand_reverse.py` có thể tải thêm raw document và cập nhật manifest, cần:

1. lưu snapshot/checksum hiện tại;
2. ghi lại số document, diagram, edge và reverse seed ban đầu;
3. đặt circuit breaker hợp lý;
4. không chạy đồng thời với delta crawl.

### 6.2. Luồng chạy

```bash
python scripts/pipeline/expand_reverse.py

python scripts/pipeline/build_graph.py \
  --max-documents 40000 \
  --extra-seeds data/reverse_seeds.json

python scripts/pipeline/fetch_provision_trees.py
python scripts/pipeline/fetch_histories.py
python scripts/pipeline/attach_provision_text.py
python scripts/check/verify_pipeline.py
```

Nếu reverse expansion tìm thêm document, phải tiếp tục lấy tree, history,
diagram và provision text cho các document mới cho tới khi closure hội tụ.

### 6.3. Tiêu chí nghiệm thu

- Giảm mạnh hoặc giải trình toàn bộ 1.017 diagram thiếu.
- Không hit `--max-new` circuit breaker.
- Mọi genealogy target mới được tải hoặc ghi nhận gone/failed.
- `reverse_seeds.json` chỉ tăng theo phép hợp, không mất ID cũ.
- Rebuild graph không làm giảm bất thường số edge/source coverage.
- `verify_pipeline.py` pass sau toàn bộ vòng backfill.

---

## 7. Phương án D — phục hồi tree từ HTML

### 7.1. Khả năng phục hồi

Trong 18 document thiếu tree:

- 17 có body text thực;
- 15 có class nguồn như `prov-article` và `prov-clause`;
- 16 có cờ PDF gốc;
- nhiều paragraph đã có ID nguồn.

Điều này cho phép dựng tree dẫn xuất từ HTML cho phần lớn trường hợp mà không
cần tự sinh nội dung.

### 7.2. Thiết kế `HTMLTreeBackfill`

1. Đọc paragraph theo thứ tự source.
2. Ánh xạ class sang level:
   - `prov-part` -> Part;
   - `prov-chapter` -> Chapter;
   - `prov-section` -> Section;
   - `prov-article` -> Article;
   - `prov-clause` -> Clause;
   - `prov-point` -> Point.
3. Dùng ID có sẵn; không tạo ID mới nếu source đã cung cấp.
4. Dựng parent bằng stack cấp cấu trúc và thứ tự xuất hiện.
5. Không ép cây phải có đủ mọi cấp.
6. Lưu artifact riêng hoặc thêm metadata:

   ```json
   {
     "tree_source": "html_class_backfill",
     "source_document_id": "...",
     "confidence": 1.0,
     "review_status": "needs_review"
   }
   ```

7. Toàn bộ tree dẫn xuất phải được review trước khi dùng cho gold benchmark.

### 7.3. Trường hợp không có class

Hai document có body nhưng không có `prov-*` class chỉ được dựng tree bằng
marker khi:

- marker Điều/Khoản xuất hiện rõ ràng;
- thứ tự tăng hợp lệ;
- không có ambiguity;
- output được đánh dấu `marker_synthetic` và bắt buộc review.

Document không có cả body lẫn tree phải chuyển sang PDF recovery.

---

## 8. Phương án E — phục hồi text từ PDF/OCR

### 8.1. Đối tượng ưu tiên

Ưu tiên theo giá trị nghiên cứu:

1. Luật, Bộ luật, Nghị định và Thông tư sửa đổi.
2. Văn bản nằm trên nhiều genealogy path.
3. Văn bản hết hiệu lực một phần.
4. Văn bản thuộc seed domain.
5. Sau cùng mới tới văn bản hỗ trợ hoặc ngoài benchmark.

### 8.2. Pipeline đề xuất

```text
Tải PDF gốc
  -> lưu checksum và URL
  -> thử text extraction
  -> nếu không có text: OCR
  -> chuẩn hóa Unicode tối thiểu
  -> căn chỉnh với tree
  -> kiểm tra coverage và trích mẫu
  -> review
```

Metadata cần lưu:

| Trường | Ý nghĩa |
|---|---|
| `text_source` | `original_pdf` hoặc `ocr` |
| `source_file` | Tên file nguồn |
| `source_url` | URL tải |
| `source_sha256` | Chứng minh artifact không đổi |
| `extractor` | Công cụ và phiên bản |
| `coverage` | Tỉ lệ node được căn chỉnh |
| `confidence` | Độ tin cậy |
| `review_status` | `needs_review`, `verified`, `rejected` |

### 8.3. Quy tắc sử dụng

- PDF có text layer và khớp tree có thể được nâng lên `derived_verified` sau
  review.
- OCR luôn bắt đầu ở `candidate`.
- Không tự sửa chính tả, dấu hoặc số hiệu pháp lý bằng LLM.
- Bảng biểu và phụ lục ảnh vẫn phải ghi là ngoài phạm vi nếu không có quy trình
  kiểm chứng riêng.

---

## 9. Phương án F — điền khuyết metadata thời gian

### 9.1. Schema candidate

Không ghi đè `effFrom`/`effTo` trong raw. Nên tạo artifact dẫn xuất dạng:

```json
{
  "schema_version": 1,
  "document_id": "...",
  "field": "effective_to",
  "candidate_value": "2025-07-01",
  "method": "unique_repealing_document_effective_from",
  "evidence_document_ids": ["..."],
  "evidence_relation_codes": [1],
  "confidence": 0.9,
  "status": "needs_review",
  "warnings": []
}
```

### 9.2. Thiếu `effFrom`

Hiện có 724 document thiếu `effFrom`:

- không document nào có `DATE_HL` do `Job` tạo để backfill trực tiếp;
- 690 có `issueDate`.

`issueDate` chỉ nên được lưu là `lower_bound`, không được coi là `effFrom`, vì
ngày ban hành và ngày có hiệu lực là hai khái niệm khác nhau và đề tài còn có
trường hợp hiệu lực trở về trước.

### 9.3. Hết hiệu lực toàn bộ nhưng thiếu `effTo`

Trong 685 document thuộc nhóm này:

- 448 có ít nhất một actor bãi bỏ/thay thế;
- 399 có đúng một ngày ứng viên từ actor thuộc code 1 hoặc 12;
- 395 ngày ứng viên nằm sau `effFrom` của document đích;
- 398/399 trường hợp chỉ có một source document duy nhất.

Đây là nhóm phù hợp nhất để tạo candidate. Điều kiện auto-accept trong tương
lai chỉ nên được xét nếu đồng thời:

1. trạng thái đích là hết hiệu lực toàn bộ;
2. chỉ có một source document bãi bỏ/thay thế;
3. source có `effFrom` hợp lệ;
4. ngày source lớn hơn `effFrom` của target;
5. nội dung source xác nhận phạm vi toàn bộ;
6. mẫu kiểm định thủ công đạt ngưỡng đã định trước.

Trước khi điều kiện 5 và 6 hoàn thành, 395 record vẫn phải là `candidate`.

### 9.4. `effTo <= effFrom`

Không nên sửa nhóm 103 document bằng `DATE_HHL` trong history:

- 101 có một history date do `Job` tạo;
- 84 history date chỉ bằng raw `effTo + 1 ngày`;
- trên toàn corpus, cùng độ lệch một ngày xuất hiện có hệ thống.

History vì vậy không phải bằng chứng độc lập cho việc sửa ngày. Các document
này phải được đánh dấu `temporal_anchor = false` cho tới khi có nguồn khác hoặc
review thủ công.

### 9.5. Thiếu status

Trong 467 document thiếu status:

- 374 có ít nhất một status row trong history;
- không status row nào trong nhóm này do `Job` tạo.

Có thể tạo `candidate_status`, nhưng không suy ra ngày chuyển trạng thái từ
`createdDate`. 93 document còn lại giữ `unknown`.

### 9.6. Hiệu lực một phần

Không thể chỉ lấy một ngày actor rồi đóng toàn document hoặc toàn provision.
Cần nối đồng thời:

```text
expiryProvisions
  + target resolver
  + cạnh tới văn bản tác động
  + effFrom của văn bản tác động
  + nội dung L2 xác định phạm vi sửa đổi/bãi bỏ
```

Nếu thiếu một mắt xích, event phải ở trạng thái `needs_review`.

---

## 10. Tại sao không dùng history date trực tiếp

Đối chiếu các document đã có metadata ngày cho thấy:

| So sánh | Trùng ngày | Lệch đúng +1 ngày | Tổng có một history date |
|---|---:|---:|---:|
| `DATE_HL` với `effFrom` | 7.284 | 13.574 | 20.862 |
| `DATE_HHL` với `effTo` | 5.113 | 5.348 | 10.469 |

Ngoài ra còn một số ít sai lệch lớn. Độ lệch +1 ngày có tính hệ thống, có thể
do ngữ nghĩa thời điểm chuyển trạng thái hoặc cách portal lưu date. Chưa có căn
cứ để tự động cộng/trừ một ngày.

Quyết định:

- history date dùng làm evidence/cross-check;
- không chép đè raw metadata;
- không suy ra quy tắc `history - 1 day` nếu chưa xác minh trên văn bản gốc;
- mọi quy tắc hiệu chỉnh phải được đo trên mẫu và ghi thành quyết định phương
  pháp trong khóa luận.

---

## 11. Kế hoạch triển khai

| Pha | Công việc | Rủi ro | Kết quả mong đợi |
|---|---|---|---|
| P0 | Khóa snapshot và ghi baseline | Thấp | Có thể rollback và so sánh |
| P1 | Sửa ID/marker fallback và review queue | Thấp | Phục hồi tối thiểu 4.187 node đã chứng minh |
| P2 | Backfill 1.017 diagram, chạy reverse closure | Trung bình | Đóng phần lớn khoảng trống chiều vào |
| P3 | Rebuild graph và downstream artifact | Trung bình | Corpus nhất quán sau document mới |
| P4 | HTML tree backfill cho 18 document | Trung bình | Phục hồi phần lớn tree thiếu có provenance |
| P5 | Sinh temporal candidate artifact | Thấp nếu không sửa raw | 395 `effTo` candidate và các hàng đợi review |
| P6 | PDF/text extraction và OCR có chọn lọc | Cao về chi phí và sai số | Cứu văn bản quan trọng không có body |
| P7 | Review thủ công và promote | Cần chuyên môn | Chuyển candidate đủ bằng chứng thành verified |

### 11.1. Baseline cần ghi trước mỗi pha

- số raw/tree/history/diagram/provision file;
- số node text và tổng node;
- số document dưới 50% coverage;
- số edge theo type/group;
- số genealogy target thiếu;
- số document/node không có temporal anchor;
- checksum của artifact bị thay đổi.

### 11.2. Validation sau mỗi pha

```bash
python scripts/check/verify_pipeline.py
python scripts/check/data_status.py
python scripts/pipeline/build_store.py
python scripts/pipeline/resolve_expiry_targets.py
```

Ngoài các gate hiện có, cần bổ sung:

- review queue membership chính xác;
- exact-ID text không bị thay đổi bởi fallback;
- candidate temporal không xuất hiện trong strict snapshot;
- mọi giá trị dẫn xuất có provenance;
- không interval lỗi nào bị biến thành open-ended và được retrieval trả về.

---

## 12. Tiêu chí hoàn thành tổng thể

Phần điền khuyết/backfill chỉ được xem là hoàn thành khi:

- toàn bộ diagram tải được hoặc có failure reason;
- graph được đóng lại sau reverse expansion;
- 18 tree thiếu được phân loại thành source-backfilled, HTML-derived,
  PDF-derived hoặc unresolved;
- review queue chứa đúng toàn bộ document dưới threshold;
- parser fallback có test và không làm hỏng exact match;
- text phục hồi luôn có source/checksum/method;
- raw metadata không bị ghi đè bởi candidate;
- temporal query strict chỉ nhận dữ liệu đủ tin cậy;
- candidate được đo coverage và review status;
- `verify_pipeline.py` cùng các gate mới đều pass;
- báo cáo trước/sau ghi rõ số trường hợp đã cứu, còn thiếu và bị loại khỏi
  benchmark.

---

## 13. Ưu tiên thực hiện ngay

Ba việc có tỉ lệ lợi ích/rủi ro tốt nhất là:

1. **Sửa ID/marker fallback và review queue.** Đã có bằng chứng phục hồi 4.187
   node từ dữ liệu hiện hữu, không cần network hay imputation.
2. **Backfill diagram.** Mẫu 60/60 thành công; đây là khoảng trống nguồn có khả
   năng đóng cao nhất.
3. **Sinh temporal candidate riêng cho 395 `effective_to`.** Không sửa raw,
   không cho strict query sử dụng trước review.

PDF/OCR và tree tổng hợp nên làm sau ba việc trên vì chi phí cao hơn và cần
kiểm định thủ công nhiều hơn.
