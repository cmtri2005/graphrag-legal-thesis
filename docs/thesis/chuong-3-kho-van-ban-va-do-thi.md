# Chương 3. Kho văn bản và đồ thị tri thức có phiên bản

> Bản nháp dựa trên trạng thái kho mã tại commit `68364f3`. Các kết quả kiểm chứng lịch sử được ghi đúng phạm vi đo; chưa thay thế kiểm định pháp lý độc lập.

**Câu hỏi của chương:** Có thể biến văn bản nguồn và các lệnh sửa đổi thành những đơn vị truy xuất theo mốc thời gian như thế nào, và bằng chứng hiện có cho phép tin cậy quá trình đó đến đâu?

## 3.1. Phạm vi dữ liệu và đơn vị biểu diễn

Kho văn bản được thu thập từ vbpl.vn. Pipeline lưu văn bản nguồn, cây cấu trúc, lịch sử và quan hệ giữa văn bản trước khi tạo các bảng dẫn xuất. Phạm vi đánh giá tập trung vào văn bản quy phạm pháp luật trung ương có khả năng neo thời gian. Văn bản hợp nhất được giữ làm nguồn đối chiếu, không đồng nhất với một văn bản quy phạm mới trong không gian truy xuất. Khóa luận phân biệt nội dung cổng cung cấp với nội dung hệ thống suy ra: sự tồn tại của một trường siêu dữ liệu không tự bảo đảm rằng trường đó mô tả đúng hiệu lực pháp lý.
<!-- nguồn: docs/decisions/0002-pham-vi-neo-thoi-gian-va-du-lieu-dan-xuat.md -->
<!-- nguồn: scripts/pipeline/build_eligibility.py -->

Đơn vị cơ bản là điều khoản có danh tính ổn định, ký hiệu (p). Một phiên bản (v) chứa lời văn của (p) trong khoảng thời gian cục bộ nhất định. Danh tính điều khoản và lời văn được tách riêng để việc sửa đổi không buộc hệ thống coi mỗi bản lời văn là một điều khoản độc lập. Văn bản sở hữu điều khoản, quan hệ cha–con và sự kiện pháp lý bổ sung ngữ cảnh cần thiết để xác định phiên bản nào có thể được sử dụng tại thời điểm hỏi.
<!-- nguồn: src/vilexgraph/build/temporal/models.py -->
<!-- nguồn: src/vilexgraph/build/temporal/version_chain.py -->

Các chương sau dùng thống nhất các ký hiệu sau. Đây là ký hiệu trình bày, không tạo thêm chỉ số đánh giá.

| Ký hiệu | Ý nghĩa |
|---|---|
| (x,t) | Câu hỏi và mốc `as_of` |
| (p) | Danh tính điều khoản; tương ứng `lineage_id` khi dựng ViLexTime |
| (v) | Phiên bản lời văn của điều khoản |
| (W_v) | Khoảng hiệu lực cục bộ của phiên bản |
| (C_p) | Hợp các khoảng mà điều khoản có phiên bản, sau ràng buộc văn bản và tổ tiên |
| $\mathcal{U}_t$ | Tập đơn vị được bộ lọc của cấu hình cho phép tại (t) |
| (E^*(x,t)) | Các ID bằng chứng được bộ chấm chấp nhận cho dòng đánh giá |
| (R_k(x,t)) | Danh sách đơn vị truy xuất ở các vị trí đầu đến (k) |

Nguồn định nghĩa thao tác cho các ký hiệu thời gian là các lớp miền và bộ lọc; định nghĩa bằng chứng đánh giá được xác định riêng bởi scorer.
<!-- nguồn: src/vilexgraph/build/temporal/effective_intervals.py -->
<!-- nguồn: src/vilexgraph/framework/temporal.py -->
<!-- nguồn: scripts/eval/score_vilextime.py -->

## 3.2. Chất lượng nguồn và phễu dữ liệu

Bản audit ngày 12/09 ghi nhận 22.550 văn bản, 128.289 cạnh phân biệt và 1.136.483 nút có lời văn. Đây là ảnh chụp lịch sử trước các bước backfill, không phải quy mô corpus truy xuất cuối cùng. Audit đồng thời chỉ ra cạnh lặp, văn bản thiếu cây điều khoản và các trường hợp không xác định được khoảng hiệu lực. Vì vậy, không dùng số lượng file thu thập làm mẫu số đại diện cho số đơn vị có thể đánh giá theo thời gian.
<!-- nguồn: docs/audit_dataset.md -->

Corpus dùng trong thực nghiệm hiện tại có quy mô được manifest ghi như sau. Các lớp là những biểu diễn khác nhau trên cùng nguồn đủ điều kiện; chúng không phải các mẫu văn bản độc lập để cộng thành số văn bản của kho.

| Thành phần | Số lượng manifest ghi nhận |
|---|---:|
| Văn bản sở hữu đơn vị corpus | 17.333 |
| Đơn vị lời văn gốc ở lớp A | 1.455.372 |
| Đơn vị lệnh sửa đổi hoặc bãi bỏ ở lớp A | 53.991 |
| Đơn vị phiên bản ở lớp B | 1.477.089 |

<!-- nguồn: data/derived/corpus/manifest.json -->

Phễu dữ liệu có thể mô tả bằng chuỗi: dữ liệu cổng → chuẩn hóa và khử trùng quan hệ → điều kiện tham gia benchmark → cấu trúc điều khoản và sự kiện → chuỗi phiên bản → corpus truy xuất. Manifest corpus lưu mã băm đầu vào và đầu ra để truy nguyên đúng bản dẫn xuất. Tuy nhiên, chưa có một bảng phễu duy nhất, cùng ngày chụp, liên kết mọi bước thu thập với corpus hiện tại. [CẦN XÁC MINH: đối soát phễu thu thập–backfill–eligibility trên cùng snapshot trước khi điền tỷ lệ hao hụt toàn pipeline].
<!-- nguồn: data/derived/corpus/manifest.json -->
<!-- nguồn: docs/audit_dataset.md -->

Một giới hạn căn bản của nguồn là ngày nhập thông tin không nhất thiết là ngày có hiệu lực. Tương tự, trạng thái “hết hiệu lực một phần” ở cấp văn bản không xác định được khoản nào đã hết hiệu lực hoặc thời điểm kết thúc của khoản đó. Pipeline vì thế không dùng trực tiếp dấu thời gian lịch sử của cổng để đóng phiên bản. Những trường hợp thiếu ngày, thiếu đích duy nhất hoặc đích mơ hồ được giữ lại để kiểm tra thay vì tự suy đoán thành một lịch sử hoàn chỉnh.
<!-- nguồn: docs/audit_dataset.md -->
<!-- nguồn: scripts/pipeline/extract_provision_events.py -->

| Khuyết tật | Xử lý trong biểu diễn | Phần rủi ro còn lại |
|---|---|---|
| Văn bản không đủ neo thời gian | Kiểm điều kiện tham gia benchmark | Không đại diện toàn bộ pháp luật hiện có |
| Thiếu cây hoặc thiếu lời văn của một nút | Giữ phân biệt thiếu dữ liệu với bị bãi bỏ | Khuyết tật chưa được dựng lại có thể làm mất sự kiện |
| Quan hệ văn bản lặp | Phân biệt cạnh với bản ghi nguồn | Audit cũ không tự mô tả quy mô mới |
| Lệnh sửa đổi không xác định được đích | Resolver theo cấu trúc, chuyển hàng đợi kiểm tra | Recall sự kiện bị giới hạn |
| Nội dung chuyển sang văn bản khác | Gắn mã loại khi kiểm ViLexTime | Không thể suy “không có đáp án” chỉ từ một lệnh bãi bỏ |

<!-- nguồn: docs/audit_dataset.md -->
<!-- nguồn: scripts/pipeline/extract_provision_events.py -->
<!-- nguồn: docs/vilextime-dinh-nghia.md -->

## 3.3. Từ lệnh pháp lý đến chuỗi phiên bản

Lớp trích xuất nhận dạng câu lệnh và bộ định vị theo cấu trúc Điều/Khoản/Điểm, sau đó phân giải văn bản và điều khoản đích. Đầu ra giữ loại thao tác, ngày hiệu lực, câu chứng cứ, đích và trạng thái xử lý. Câu lệnh có thể được nhận dạng nhưng chưa đủ điều kiện áp dụng; hai trạng thái này không được gộp. Tệp sự kiện dẫn xuất vì thế chứa cả những trường hợp phải xem lại, còn nhật ký dựng phiên bản ghi kết quả xử lý từng sự kiện được xét.
<!-- nguồn: scripts/pipeline/extract_provision_events.py -->
<!-- nguồn: scripts/pipeline/build_versions.py -->

`EventApplier` áp dụng sự kiện trên bản sao trạng thái. Chỉ khi thao tác hợp lệ và các bất biến chuỗi vẫn được bảo toàn thì trạng thái làm việc mới được nhận. Với thao tác sửa lời văn, phiên bản đang mở được đóng tại ngày hiệu lực của sự kiện và phiên bản mới bắt đầu từ ngày đó. Phần thay cụm từ được chuyển thành lời văn mới trong pipeline; không coi riêng câu “thay cụm từ” là toàn văn phiên bản sau. Lệnh bãi bỏ đóng chuỗi cục bộ của đích; hệ thống giữ provenance để truy ngược nguyên nhân đóng.
<!-- nguồn: src/vilexgraph/build/temporal/event_applier.py -->
<!-- nguồn: scripts/pipeline/build_versions.py -->

Mỗi khoảng được biểu diễn nửa mở ([start,end)). Phiên bản cục bộ tồn tại tại ngày hỏi chưa đủ để kết luận điều khoản có hiệu lực. `ValidityService` còn kiểm khoảng của văn bản và trạng thái tổ tiên. Ngược lại, sửa lời văn của nút cha không mặc nhiên bãi bỏ nút con: điều cần xét là độ phủ hiệu lực của tổ tiên. Nút chưa từng có lời văn được coi là trong suốt khi kiểm tổ tiên; nó không cung cấp chứng cứ rằng các nút con đã hết hiệu lực.
<!-- nguồn: src/vilexgraph/build/temporal/validity.py -->
<!-- nguồn: src/vilexgraph/build/temporal/version_chain.py -->

Có thể trình bày phép tính khoảng hiệu lực thực bằng giao của khoảng phiên bản với độ phủ của các tổ tiên và văn bản sở hữu. `effective_intervals_by_version` thực hiện phép giao đệ quy, gộp các khoảng kề nhau và giữ các khoảng rời nhau khi tồn tại khoảng trống. Các khoảng này được tính ngoại tuyến; truy xuất trực tuyến dùng chúng qua chỉ mục. Công thức là đặc tả của mô hình dữ liệu, chưa phải một bảo đảm rằng mọi sự kiện pháp lý trong nguồn đều đã được trích đủ.
<!-- nguồn: src/vilexgraph/build/temporal/effective_intervals.py -->

## 3.4. Đồ thị dẫn xuất và hai lớp corpus

Lược đồ khái niệm gồm văn bản, điều khoản, phiên bản và sự kiện. Văn bản sở hữu điều khoản; điều khoản có quan hệ cha–con; phiên bản thuộc điều khoản; sự kiện tạo hoặc kết thúc lời văn và giữ câu nguồn. Biểu diễn này cho phép tách nguồn gốc của lời văn khỏi điều kiện sử dụng lời văn tại một mốc. Dữ liệu gốc và các file trung gian là nguồn tái dựng; các cơ sở dữ liệu phục vụ truy vấn là kho dẫn xuất.
<!-- nguồn: docs/decisions/0001-neo4j-milvus-la-kho-dan-xuat.md -->
<!-- nguồn: scripts/pipeline/load_neo4j.py -->
<!-- nguồn: scripts/pipeline/build_versions.py -->

Lớp A giữ lời văn gốc cùng các lệnh sửa đổi, bãi bỏ dưới dạng đơn vị truy xuất riêng. Lớp B giữ lời văn từng phiên bản đã được materialize. Một baseline phẳng dùng lớp A vẫn có cơ hội lấy được câu lệnh viết ra phiên bản mới, thay vì bị giới hạn vào văn bản ban đầu. Ngược lại, lớp B đưa sẵn lời văn đã hợp nhất nên mang lợi ích của công đoạn ngoại tuyến. Khi so sánh hai lớp, cần nhận diện lợi ích của biểu diễn này trước khi quy chênh lệch cho suy luận đồ thị trực tuyến.
<!-- nguồn: scripts/pipeline/build_corpus.py -->
<!-- nguồn: docs/decisions/0004-framework-truy-xuat-va-sinh.md -->

Tài liệu kiến trúc ban đầu nhấn mạnh Neo4j và Milvus. Đường thực nghiệm hiện tại dùng SQLite FTS5 cho truy xuất từ vựng, bảng khoảng hiệu lực và truy vấn SQL để lấy láng giềng. Đồ thị vẫn tham gia dựng lịch sử và khoảng hiệu lực ngoại tuyến; mở rộng quan hệ trong lúc trả lời được cài đặt riêng. Do đó, sự hiện diện của đồ thị trong pipeline không chứng minh rằng mọi câu trả lời đã thực hiện suy luận nhiều bước trên một máy chủ đồ thị.
<!-- nguồn: src/vilexgraph/framework/corpus.py -->
<!-- nguồn: src/vilexgraph/framework/retrieve.py -->
<!-- nguồn: src/vilexgraph/framework/graphx.py -->

## 3.5. Bằng chứng kiểm chứng và phạm vi của chúng

Các số đo chất lượng dưới đây là mô tả thăm dò trên phạm vi kiểm lịch sử, không thuộc họ XN của thực nghiệm hỏi đáp.

Kết quả kiểm tay L2 lịch sử ghi 58/60 sự kiện áp được là đúng, tương ứng 96,7%, khoảng Wilson 95% từ 88,6% đến 99,1%. Phép đo này có mẫu nhỏ và chỉ lấy trong các sự kiện đã áp được. Recall đối chiếu theo `expiryProvisions` được ghi là 62,2%. Hai số đo không cùng mẫu số, không được nhân hoặc diễn giải thành xác suất “toàn đồ thị đúng”. Các mở rộng pipeline sau thời điểm đo cũng chưa đương nhiên được xác nhận bởi mẫu đó.
<!-- nguồn: docs/plans/active/l2-event-store.md -->

Đối chiếu tự động với văn bản hợp nhất có 51 văn bản đủ điều kiện, 5.762/7.201 cặp lời văn khớp chính xác, tương ứng 80,02%; 299 văn bản trong kiểm kê thiếu body nên không thuộc phạm vi so sánh. Đây là phép kiểm trên phần quan sát được, không phải độ chính xác của toàn corpus hoặc kiểm định pháp lý độc lập.
<!-- nguồn: docs/plans/active/phase-3-kg-l0-l3.md -->

M2 yêu cầu bộ truy vấn đối chiếu tay; kế hoạch vẫn để mở phần kiểm tay 100 truy vấn. Vì chưa có bằng chứng hoàn tất tương ứng, bản nháp này coi **M2 chưa đạt**. Việc các phép tính khoảng hiệu lực nội bộ khớp `ValidityService` chỉ chứng minh hai đường thực hiện cùng mô hình nhất quán với nhau; chúng có thể cùng bỏ sót một sự kiện trong nguồn. Không có cơ sở để dùng kiểm tra nội bộ làm thay thế M2.
<!-- nguồn: docs/plans/active/phase-3-kg-l0-l3.md -->
<!-- nguồn: docs/plans/active/master-plan.md -->

## 3.6. Câu trả lời có thể rút ra

Kho hiện có hỗ trợ tách danh tính điều khoản, lịch sử lời văn và khoảng sử dụng theo mô hình thời gian. Provenance, nhật ký sự kiện và các kiểm tra chuỗi tạo điều kiện truy nguyên và tái dựng. Bằng chứng kiểm tay và đối chiếu tự động cho thấy pipeline có khả năng tạo lịch sử hữu ích, đồng thời chỉ rõ độ phủ chưa hoàn chỉnh. Đóng góp có thể bảo vệ là một cơ chế dẫn xuất và truy nguyên phiên bản trên nguồn đã thu thập; chưa thể khẳng định đồ thị đúng hoặc đầy đủ về pháp lý.
<!-- nguồn: scripts/pipeline/build_versions.py -->
<!-- nguồn: docs/plans/active/l2-event-store.md -->
<!-- nguồn: docs/plans/active/phase-3-kg-l0-l3.md -->

## Việc còn thiếu trước khi nộp

- Hoàn tất hoặc công bố việc chưa hoàn tất M2; lưu từng truy vấn và chứng cứ người kiểm.
- Đối soát phễu dữ liệu trên cùng snapshot; không trộn quy mô audit cũ với corpus cuối.
- Bổ sung hình lược đồ và ví dụ chuỗi có provenance từ dữ liệu thật. [CẦN XÁC MINH: chọn và kiểm độc lập một ví dụ pháp lý trước khi đưa lời văn điều luật vào chương].
- Đo lại chất lượng các phần L2 đã mở rộng sau mẫu kiểm tay lịch sử; báo cả lỗi bỏ sót.
