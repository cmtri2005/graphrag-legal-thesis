# Crawling Plan — vbpl.vn → Temporal Legal KG

## 1. Kiến trúc nguồn dữ liệu

- Frontend: `vbpl.vn` (Next.js, SSR nghèo dữ liệu — không parse HTML trực tiếp).
- Backend thật: `https://vbpl-bientap-gateway.moj.gov.vn/api` — REST JSON, không cần auth cho các endpoint `public`.
- Danh sách văn bản: các endpoint `/qtdc/public/doc/search`, `/docs`, `/doctype`, `/org` đều trả `401 Unauthorized` (token FE nội bộ, CORS-only).
  **NHƯNG `POST /qtdc/public/doc/all` thì KHÔNG cần auth và dùng được** — xem §1b.
  (Bản kế hoạch cũ kết luận "không dùng listing API được" là **sai**: lúc đó chưa
  thử endpoint `/doc/all`.)
- Nguồn liệt kê đang dùng làm xương sống: **sitemap.xml** (`https://vbpl.vn/sitemap.xml` → 36 shard: 1 trang tĩnh, 12 shard Trung ương, 23 shard Địa phương). Mỗi `<url>` dạng:
  `https://vbpl.vn/van-ban/chi-tiet/{slug}--{id}` — `id` cuối cùng chính là khóa để gọi API chi tiết.

## 1b. Listing API `/doc/all` — dùng được, không cần auth

`POST https://vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/all`

Body ví dụ: `{"pageSize": 500, "pageNumber": 1, "sortBy": "issueDate", "sortDirection": "desc"}`

Đã test thật (2026-09-04). Tham số nào có tác dụng, tham số nào không:

| Tham số | Kết quả đo được |
|---|---|
| *(không lọc gì)* | `total = 172.193` (cả trung ương lẫn địa phương) |
| `pageSize` | tới **500** vẫn OK → ~345 trang cho toàn bộ, không phải 36.916 |
| `keyword: "đất đai"` | 172.193 → **56.733** |
| `issueDateFrom` / `issueDateTo` | ✅ (trước 2000 → 21.759; từ 2026 → 5.831) |
| `agencyIds` | ✅ có lọc thật (uuid sai → total 0) |
| `sortBy` | chỉ `issueDate` và `viewCount` chạy; `updatedDate`/`id` → **HTTP 500** |
| `sortByViewCount: true` | ⚠ không phải chỉ sắp xếp — nó **lọc còn 37.293** |
| `updatedDateFrom`, `majorIds`, `fieldIds`, `docTypeIds`... | ❌ bị bỏ qua im lặng (total không đổi) |

Hai điều quan trọng rút ra:

1. **Mỗi item trong listing đã kèm sẵn `documentMajors`, `effStatus`, `effFrom`,
   `effTo`, `docType`, `agencyName`, `issueDate`.** Nên câu "phải tải hết chi
   tiết mới biết field" ở §3 **không còn đúng** — lọc lĩnh vực làm được ngay ở
   tầng listing, trước khi tốn request tải chi tiết.
2. **Không có `updatedDateFrom`** → vẫn **không có** cách hỏi "cái gì đã đổi từ
   ngày X". Sitemap `lastmod` vẫn là tín hiệu delta duy nhất (§6b giữ nguyên).

⚠ **Đừng phân trang bằng `sortBy: viewCount`.** `viewCount` thay đổi ngay trong
lúc crawl → thứ tự trôi giữa các trang → văn bản vừa bị bỏ sót vừa bị lặp, mà
không có lỗi nào báo. Nếu dùng `/doc/all` để duyệt tuần tự thì sắp xếp theo
`issueDate` (bất biến).

**Dùng endpoint này vào việc gì?** Không thay thế sitemap + BFS phả hệ (đã chạy
xong, ổn định). Giá trị lớn nhất của nó là **đo recall**: `keyword` cho biết tổng
số văn bản nhắc tới một chủ đề, đối chiếu với tập seed lọc theo slug sẽ ra con số
"đã bỏ sót bao nhiêu" — thứ mà từ trước tới nay chỉ đoán chứ chưa đo được.

## 2. Endpoint API xác nhận dùng được

| Endpoint | Method | Nội dung |
|---|---|---|
| `/qtdc/public/doc/{id}` | GET | Chi tiết đầy đủ: `docNum`, `title`, `issueDate/effFrom/effTo`, `effStatus`, `documentContent.content` (full-text HTML, có `Điều N.` đánh dấu rõ), `documentFields`/`documentMajors`, `references[]` (quan hệ tới văn bản khác + `referenceType`), `documentIssues` (người ký), `hasClauseRelation`, `isConsolidatedDocument` |
| `/qtdc/public/doc/{id}/history` | GET | Lịch sử hiệu lực theo mốc thời gian (`DATE_BH` ban hành, `DATE_HL` hiệu lực, `CHL` hết hiệu lực...) — **cốt lõi cho point-in-time** |
| `/qtdc/public/doc/{id}/diagram` | GET | Sơ đồ văn bản liên quan phân theo loại quan hệ |
| `/qtdc/public/doc/{id}/related` | GET | Bản dịch / văn bản gốc liên quan |

`id` có thể là số nguyên (văn bản cũ) hoặc UUID (văn bản mới, 2024+). Cả hai dạng đều hoạt động với cùng endpoint.

### `referenceType` — nhãn của cạnh (quan hệ giữa hai văn bản)

Trong `references[]`, mỗi quan hệ tới văn bản khác có một trường `referenceType`
là **một con số trần**, ví dụ `10`. API không hề trả kèm nhãn chữ. Số `10` nghĩa
là gì thì không có chỗ nào trong dữ liệu nói cho ta biết.

Đã tìm và **xác nhận không có sẵn ở đâu cả**: grep toàn bộ JS bundle của cả
trang danh sách lẫn trang chi tiết — không có object/switch nào ánh xạ số →
nhãn; các endpoint đoán thử (`/relations`, `/relation-groups`, `/basis`...) đều
404. Trên giao diện web thì nhãn tiếng Việt có hiện ("căn cứ ban hành", "sửa đổi
bổ sung", "thay thế"...), nhưng trong code chúng chỉ là chuỗi i18n rời rạc,
không dính với số nào.

→ Vì vậy phải **tự dựng bảng tra số → nhãn bằng tay**. Quy trình đã làm và kết
quả: xem §3b. Bảng cuối cùng nằm ở `data/reference_type_map.json`.

**Trạng thái: XONG.** 13 mã đã được xác minh (`1,2,3,4,5,6,7,8,9,10,11,12,14`).
Đừng đoán lại nhãn từ con số nữa — cứ đọc file mapping.

## 2b. Cạnh chiều ngược — lỗ hổng của BFS chiều xuôi

**Vấn đề, nói cho dễ hiểu**: `references[]` chỉ ghi quan hệ **một chiều**. Nếu
văn bản B sửa đổi văn bản A, cạnh đó nằm trong `references[]` **của B**, chứ
**không** nằm trong của A. BFS ở Stage 2 chỉ đi *ra ngoài* từ những văn bản đã
có → nếu B chưa từng được phát hiện bằng đường nào khác, **ta không bao giờ biết
A đã bị sửa**. Và một lần bãi bỏ không tải về là một lần bãi bỏ Stage 6 không
bao giờ áp dụng được → trả lời point-in-time sai mà không có dấu hiệu gì.

**Đo thật (mẫu 150 văn bản ngẫu nhiên, 2026-09-04)**: **27%** có ít nhất một
hàng xóm phả hệ không nằm trong corpus. Kiểm tay một lô: **7/7 văn bản sửa đổi
đều thiếu**.

⚠ `verify_pipeline.py` **không phát hiện được lỗi này** — nó chỉ kiểm tra được
những cạnh ta đã biết. Cạnh chưa bao giờ nhìn thấy thì không có gì để kiểm.

**Lời giải**: `/doc/{id}/diagram` trả về hai bản đồ cùng khoá `referenceType`:

| Trường | Ý nghĩa |
|---|---|
| `documentNamesByType` | chiều ra — trùng với `references[]`, đã có rồi |
| `documentNamesBySource` | **chiều vào** — chiều ta đang mù |

**Hướng cạnh**: cạnh chiều ngược được chuẩn hoá về **cùng hướng với cạnh chiều
xuôi** — văn bản *ra tay* luôn là `source_id`. Một mục code 10 ở chiều vào của
văn bản Y trở thành `Edge(source=văn bản sửa, target=Y, type=10)`, đúng hình
dạng mà `references[]` của văn bản sửa sẽ tạo ra. Nhờ vậy **phần code phía sau
không cần biết tới khái niệm "chiều ngược"**.

**Mở rộng qua cạnh nào?** (`REVERSE_EXPANDABLE` trong `src/legal_crawler/diagram.py`)

- ✅ **1, 5, 6, 10, 11, 12** — bãi bỏ / đình chỉ / đính chính / sửa đổi bổ sung /
  tạm ngưng / thay thế. Đây là các quan hệ **thay đổi hiệu lực**, và hữu hạn tự
  nhiên: một văn bản chỉ có vài văn bản sửa nó.
- ❌ **9 (được quy định chi tiết, hướng dẫn thi hành)** — chiều vào nghĩa là
  "mọi nghị định, thông tư hướng dẫn tôi". Với một Luật là hàng chục văn bản
  trải khắp lĩnh vực khác. Chiếm **453/494** hàng xóm thiếu trong mẫu đo.
- ❌ **3 (căn cứ ban hành)** — chiều vào nghĩa là "mọi văn bản lấy tôi làm căn
  cứ". Đo được **17.460 lần chỉ trong 184 diagram**. Đi theo là kéo về gần như
  toàn bộ 172k văn bản.
- ❌ **7 (được hợp nhất)** — văn bản phái sinh, ngoài phạm vi §4, và 85% không
  có nội dung (§5d).

Vẫn **ghi lại** các cạnh này, chỉ không dùng làm điểm xuất phát — đúng nguyên
tắc §5 đã áp cho nhóm "trích dẫn mở" ở chiều xuôi.

### Kết quả chạy thật (2026-09-04)

16.222 diagram → **phát hiện 2.335 văn bản mới**, corpus 13.863 → 16.223
(và còn tăng tiếp khi BFS chiều xuôi chạy lại trên các văn bản mới này).

Số lần quan hệ chiều vào gặp được — con số này cho thấy chọn sai nhóm cạnh thì
hỏng hẳn phạm vi:

| Đi theo ✅ | | Không đi theo ❌ | |
|---|---|---|---|
| code 10 (sửa đổi bổ sung) | 5.237 | **code 3 (căn cứ ban hành)** | **555.592** |
| code 12 (được thay thế) | 4.993 | code 4 (dẫn chiếu) | 46.346 |
| code 1 (bị bãi bỏ) | 4.275 | code 9 (quy định chi tiết) | 33.945 |
| code 6 / 5 / 11 | 112 / 17 / 16 | code 7 (được hợp nhất) | 2.938 |

**555.592 so với 14.650** — nếu đi theo chiều ngược của code 3 thì crawl sẽ kéo
về gần như toàn bộ cơ sở dữ liệu 172k văn bản.

**Vá được bao nhiêu?** Trong nhóm văn bản "hết hiệu lực một phần" mà trước đó
không có cạnh sửa đổi nào giải thích: **374/588 (64%) nay đã có văn bản sửa nó
trong corpus**.

⚠ **Bài học khi đo**: 214 ca còn lại thoạt nhìn tưởng vẫn hỏng, nhưng 178 trong
số đó có cạnh chiều vào **code 1 (bị bãi bỏ)** — tức trạng thái "hết hiệu lực
một phần" đến từ việc **bãi bỏ một số điều**, không phải sửa đổi. Code 1 vốn đã
nằm trong `REVERSE_EXPANDABLE` nên các văn bản đó đã được tải về.
→ **Đừng chỉ nhìn code 10 khi truy nguyên "ai làm tôi hết hiệu lực một phần"** —
phải xét cả nhóm 1, 5, 6, 10, 11, 12.

**Quy trình chạy** (`scripts/pipeline/expand_reverse.py`, resume được):
1. Tải `/diagram` cho mọi văn bản đang có → `data/diagrams/{id}.json`.
2. Đọc chiều vào, tìm văn bản "ra tay" mà ta chưa có → tải về `data/raw/`.
3. Văn bản mới cũng được đưa vào hàng đợi lấy diagram → lặp tới khi hội tụ
   (nhờ vậy cả chuỗi sửa đổi mới đầy đủ, không phải chỉ một bậc).
4. Ghi id mới ra `data/reverse_seeds.json`.
5. **Chạy lại** `build_graph.py --extra-seeds data/reverse_seeds.json` để sinh
   lại `edges.jsonl`. Diagram chỉ dùng để **phát hiện**; cạnh vẫn lấy từ
   `references[]` của chính văn bản mới — nên không có cạnh trùng hay cạnh bịa.

## 3. Chiến lược lọc theo 4 lĩnh vực

Không dùng taxonomy API (401, và phải tải hết chi tiết mới biết field). Thay vào đó:

1. **Lọc thô** trên sitemap bằng từ khóa trong slug (không tốn request):
   - Đất đai: `dat-dai`, `nha-o`, `kinh-doanh-bat-dong-san`
   - Thuế: `thue`, `phi-va-le-phi`, `hai-quan`
   - Doanh nghiệp/Đầu tư: `doanh-nghiep`, `dau-tu`, `chung-khoan`, `hop-tac-xa`
   - Giao thông: `giao-thong`, `duong-bo`, `duong-sat`, `duong-thuy`, `hang-khong`, `hang-hai`, `van-tai`

   Danh sách này là nguồn duy nhất, sống trong `KEYWORDS_BY_DOMAIN`
   (`src/legal_crawler/config.py`) — sửa ở đó, không chép lại vào script.

   **Vì sao có Giao thông (thêm sau, có chủ đích)**: ba lĩnh vực đầu chọn theo
   giá trị ứng dụng. Giao thông được thêm vào vì đây là lĩnh vực **thay đổi
   liên tục** (nghị định xử phạt, quy chuẩn kỹ thuật, biểu phí... sửa đổi/thay
   thế với tần suất cao hơn hẳn) → cho phả hệ văn bản dày, nhiều mốc hiệu lực
   chồng lấn. Đúng loại dữ liệu cần để kiểm chứng suy luận point-in-time: một
   corpus toàn văn bản ổn định sẽ không phân biệt được hệ thống trả lời đúng
   theo mốc thời gian hay chỉ trả lời theo bản mới nhất.
2. **Mở rộng qua graph liên kết**: với mỗi văn bản gốc (luật khung) tìm được, đệ quy theo `references[]` (loại "quy định chi tiết", "hướng dẫn thi hành", "sửa đổi bổ sung") để bắt các nghị định/thông tư con dù title không chứa từ khóa.
3. **Rà soát có người duyệt sau khi tải chi tiết** (KHÔNG phải lọc tự động — xem §3c): dùng `documentFields`/`documentMajors` để **gợi ý** văn bản khả nghi sai lĩnh vực, rồi người quyết định.

## 3b. Cách đã dựng bảng mapping `referenceType` — ✅ ĐÃ XONG

> **Đọc mục này khi nào?** Khi crawl lộ ra một mã `referenceType` mới chưa có
> trong `data/reference_type_map.json` (chương trình sẽ dừng và báo lỗi
> `UnknownReferenceTypeError`). Lúc đó làm lại đúng 6 bước dưới đây cho riêng mã
> mới. Còn nếu chỉ đang dùng bảng có sẵn thì không cần đọc — cứ đọc file JSON.

**Kết quả đã có**: quét toàn bộ 7.116 văn bản seed (không phải mẫu nhỏ) → tìm ra
đúng 13 mã. 12 mã xác minh bằng khớp trực tiếp với giao diện web thật; mã `2`
xác minh bằng suy luận loại trừ (chi tiết trong chính file JSON). Ngày chốt:
2026-08-24.

**Nguyên tắc: không đoán, không suy diễn từ code minified. Build ground-truth bằng quan sát thực tế trên UI, có kiểm chứng chéo.**

Quy trình (đã thực hiện — lặp lại y hệt nếu có mã mới):
1. **Thu thập union toàn bộ giá trị `referenceType`**: chạy một pass quét nhẹ (chỉ gọi `/doc/{id}`, không cần tải nội dung đầy đủ — hoặc tận dụng luôn dữ liệu Stage 3) trên một tập mẫu đa dạng: Luật, Nghị định, Thông tư, Nghị quyết, văn bản cũ (trước 1990) lẫn mới (2024+), văn bản còn hiệu lực lẫn hết hiệu lực. Gom `set()` tất cả `referenceType` xuất hiện → đây là phạm vi cần map đầy đủ, không map thiếu.
2. **Đối chiếu ground-truth bằng tay**: với mỗi giá trị số, mở trực tiếp 2-3 văn bản mẫu chứa giá trị đó trên trình duyệt thật (không phải qua API), vào tab "Lược đồ"/quan hệ văn bản trên vbpl.vn, dùng DevTools Network để xem đúng văn bản/đúng dòng quan hệ đó hiển thị nhãn tiếng Việt nào. Ghi lại `{referenceType: nhãn}` kèm ảnh chụp/link bằng chứng.
3. **Kiểm chứng chéo bằng heuristic phụ** (không dùng làm nguồn chính, chỉ để phát hiện mapping sai): so sánh `issueDate` của văn bản nguồn vs `targetDocument.issueDate`, và cặp `docType` — ví dụ quan hệ "sửa đổi bổ sung" luôn có văn bản sửa đổi ban hành SAU văn bản gốc; "căn cứ ban hành" luôn trỏ tới văn bản có hiệu lực TRƯỚC thời điểm ban hành. Nếu heuristic mâu thuẫn với nhãn ghi ở bước 2 → nghi ngờ, kiểm tra lại thủ công.
4. **Đóng băng bảng mapping thành file cấu hình tĩnh** (`reference_type_map.json` hoặc tương tự), có version, checked vào repo — không hard-code rải rác trong code.
5. **Fail-loud khi gặp code lạ**: graph builder khi gặp `referenceType` không có trong bảng mapping phải **raise lỗi / log vào hàng đợi "cần review thủ công"**, tuyệt đối không âm thầm gán nhãn mặc định hay bỏ qua cạnh — vì một cạnh gán sai nhãn (VD: nhầm "bãi bỏ" thành "sửa đổi") sẽ làm sai lệch suy luận point-in-time.
6. Việc build mapping này làm **một lần, trước khi viết Stage 5-6 (graph builder)**, không vừa crawl vừa đoán nhãn giữa chừng.

Hai script phục vụ việc này (chạy theo đúng thứ tự): `collect_reference_types.py`
(quét raw JSON, gom danh sách mã đang có) → `scrape_luoc_do.py` (mở trình duyệt
ẩn, đối chiếu từng mã với tab "Lược đồ" thật trên vbpl.vn).

## 3c. Bài học: KHÔNG được lọc lĩnh vực tự động bằng `documentFields`/`documentMajors`

**Tóm tắt cho người vội**: hai trường metadata này là do nguồn (vbpl.vn) tự gán,
và chúng **sai/thiếu nhiều tới mức không dùng để lọc tự động được**. Chỉ được
dùng làm gợi ý cho người xem, không được dùng để tự động loại bỏ văn bản.

Kế hoạch ban đầu định dùng chúng làm bộ lọc tinh tự động ở Stage 4.
**Đã thử trên corpus thật và bác bỏ**, vì hai lý do:

- **56% số văn bản không có phân loại nào** (đều ghi `Chưa phân loại`). Lọc theo
  trường này sẽ quét sạch hơn nửa dữ liệu, trong đó có rất nhiều văn bản đúng
  lĩnh vực.
- **Có những văn bản bị gán sai hẳn.** Hai ví dụ có thật gặp trong lúc làm:
  - một nghị định hướng dẫn *Luật Thuế thu nhập cá nhân* lại được gán **chỉ**
    mỗi `Lao động - Thương binh và Xã hội` (không hề có `Tài chính`);
  - một chỉ thị về thi hành *thuế GTGT* bị gán `Công an` (kèm `Tài chính`).

  Lọc tự động theo lĩnh vực sẽ vứt nhầm cả hai văn bản này — mà đây đều là văn
  bản thuế, tức đúng ngay lĩnh vực đang cần.

Vì vậy quy trình đã chốt (đang chạy trong `src/legal_crawler/field_filter.py`):

1. Một văn bản chỉ bị coi là **khả nghi** khi **TẤT CẢ** lĩnh vực/ngành của nó
   đều nằm trong danh sách chặn (`data/field_filter_map.json`). Chỉ cần có
   **một** tag đúng lĩnh vực là giữ lại ngay — đây chính là cái cứu hai ví dụ
   phía trên khỏi bị loại nhầm.
2. Kết quả chỉ là **danh sách chờ người duyệt** (`data/field_filter_review.txt`).
   Máy không bao giờ tự xoá gì cả.
3. Người đọc danh sách đó, quyết định, rồi ghi quyết định vào
   `CONFIRMED_EXCLUSIONS` trong `scripts/review/apply_field_review.py`; chạy script này
   mới sinh ra `data/excluded_ids.txt`.
4. **"Loại bỏ" ở đây = bỏ qua lúc đọc, KHÔNG xoá file.** Không bước nào trong
   pipeline được phép xoá `data/raw/`. Muốn nhận lại một văn bản đã loại thì chỉ
   cần sửa một dòng cấu hình, không phải đi crawl lại từ đầu.

⚠ Đừng bỏ qua bước người duyệt kiểu "chỉ lần này thôi cho nhanh". Mở
`data/excluded_ids.txt` ra xem là thấy ngay loại nhầm lẫn mà việc bỏ qua sẽ gây ra.

## 4. Phạm vi

- Chỉ văn bản **QPPL trung ương** (loại trừ địa phương, văn bản hành chính thường).
- Lấy **toàn bộ lịch sử**, kể cả văn bản đã hết hiệu lực — bắt buộc để trả lời câu hỏi point-in-time đúng theo từng mốc thời gian.

  > ⚠ Đây là chỗ dễ làm hỏng cả luận văn nhất. Một crawler vbpl.vn công khai
  > khác lọc bỏ mọi văn bản `effStatus = "Hết hiệu lực toàn bộ"` ngay ở bước tiền
  > xử lý — hợp lý nếu chỉ cần "luật hiện hành", nhưng với ta thì đó chính là dữ
  > liệu cần nhất. Cùng một nguồn, thiết kế cho *"luật đang áp dụng"* và cho
  > *"luật tại thời điểm T"* cho ra hai corpus khác hẳn nhau.
  > **Không bao giờ lọc theo `effStatus`.**
- Ưu tiên crawl theo **họ văn bản** (luật gốc + toàn bộ nghị định/thông tư/văn bản sửa đổi liên quan) thay vì crawl phẳng toàn bộ 57k+ URL.
- Kết quả thực tế của cách làm này: **13.863 văn bản** thay vì 57k+ — tức chỉ
  lấy ~1/4 số URL nhưng là đúng phần liên quan tới 4 lĩnh vực đã chọn, kèm đầy
  đủ phả hệ sửa đổi của chúng.

## 5. Pipeline đề xuất

```
Stage 1 — Seed discovery
  Tải 12 shard sitemap Trung ương → lọc slug theo từ khóa 4 lĩnh vực
  → danh sách seed URL/id (luật gốc + văn bản có từ khóa)

Stage 2 — Graph expansion (BFS qua references[], giới hạn theo LOẠI cạnh, không giới hạn theo SỐ HOP)
  Với mỗi seed: GET /doc/{id} → đọc references[]
  → chỉ mở rộng qua các cạnh thuộc nhóm "gia phả văn bản" (bounded by nature):
     sửa đổi bổ sung, thay thế, đính chính, bãi bỏ, hợp nhất,
     quy định chi tiết/hướng dẫn thi hành
  → KHÔNG mở rộng đệ quy qua nhóm cạnh "trích dẫn mở" (unbounded, dễ nổ phạm vi
     sang lĩnh vực khác): dẫn chiếu, áp dụng, giải thích, căn cứ ban hành
     (nhóm này vẫn lưu là cạnh 1 hop nếu văn bản đã nằm trong tập, nhưng
     không dùng làm điểm xuất phát để mở rộng thêm)
  → dùng visited-set để tránh lặp vô hạn do cạnh có thể cyclic
  → lặp tới khi hàng đợi rỗng (tự hội tụ vì mỗi luật chỉ có một "phả hệ"
     sửa đổi/thay thế hữu hạn — không cần cắt cứng theo hop)
  → vẫn giữ một circuit breaker an toàn (--max-documents) chỉ để bắt lỗi/bug,
     KHÔNG phải cơ chế giới hạn phạm vi chính
     ⚠ Luôn truyền --max-documents CAO HƠN HẲN số file trong data/raw hiện có.
       edges.jsonl được sinh lại từ đầu mỗi lần chạy, theo đúng tập văn bản mà
       lần chạy đó gom được — nên chạm breaker giữa chừng sẽ ghi đè edges.jsonl
       bằng bản bị cắt cụt mà không báo lỗi (đã xảy ra thật với mức mặc định
       5000 khi corpus đã vượt mốc đó; raw JSON không sao, chỉ edges.jsonl hỏng).
       Corpus hiện tại ~13.9k văn bản → dùng --max-documents 25000.

Stage 2b — Đóng kín cạnh CHIỀU NGƯỢC (xem §2b)
  references[] chỉ ghi quan hệ một chiều → BFS chiều xuôi không bao giờ biết
  "ai đã sửa đổi/bãi bỏ tôi". Lấy /doc/{id}/diagram → documentNamesBySource
  → mở rộng CHỈ qua code 1, 5, 6, 10, 11, 12 (bãi bỏ/đình chỉ/đính chính/
    sửa đổi/tạm ngưng/thay thế) — hữu hạn, và là thứ point-in-time cần
  → KHÔNG mở rộng qua chiều ngược của code 9 (quy định chi tiết) và 3
    (căn cứ ban hành): sẽ nổ phạm vi ra toàn bộ 172k văn bản

Stage 3 — Full fetch
  Với mỗi id trong tập đã gom: GET /doc/{id} + /doc/{id}/history
  Lưu raw JSON (idempotent, cache theo id — resume được khi bị ngắt)

Stage 4 — Field-based review pass (KHÔNG tự động loại — xem §3c)
  Dùng documentFields/documentMajors để GỢI Ý văn bản khả nghi sai lĩnh vực
  → sinh danh sách chờ duyệt, người quyết định, ghi vào excluded_ids.txt
  → loại trừ áp dụng lúc đọc, raw JSON không bị xoá

Stage 5 — Content parsing (xem §5b: KHÔNG còn phải tự đoán cấu trúc)
  5a. Lấy cây Phần/Chương/Mục/Điều/Khoản/Điểm có sẵn từ server
      → fetch_provision_trees.py → data/trees/{id}.json
  5b. Map text trong documentContent.content vào đúng node của cây
      → dùng chính cây làm bộ kiểm chứng kết quả parse
  → đơn vị node cấp điều khoản cho KG (không chỉ node cấp văn bản)

Stage 6 — Temporal graph build
  Dùng effFrom/effTo + history[] để gắn interval hiệu lực [t_start, t_end)
  cho từng văn bản/điều khoản → nền tảng cho point-in-time QA
```

> Lưu ý thứ tự: Stage 3b (mapping `referenceType`) phải hoàn thành **trước** khi
> code logic phân nhóm cạnh ở Stage 2 — vì việc quyết định cạnh nào thuộc nhóm
> "gia phả" (mở rộng được) hay "trích dẫn mở" (không mở rộng) phụ thuộc vào
> bảng mapping đã được kiểm chứng, không phải suy đoán từ số.

## 5b. Cây điều khoản lấy sẵn từ server — Stage 5 dễ đi rất nhiều

**Tóm tắt**: không cần viết parser đoán cấu trúc văn bản nữa. Server trả sẵn cây
Phần/Chương/Mục/Điều/Khoản/Điểm, mỗi node có UUID ổn định.

**Lấy ở đâu?** Không phải ở API gateway. `provisionTree` trong `/doc/{id}` **luôn
null** (đã kiểm tra 1.501 file raw, 0 file có dữ liệu). Cây chỉ lấy được qua một
**Next.js server action** trên chính `vbpl.vn`:

```
POST https://vbpl.vn/van-ban/chi-tiet/x--{id}
header  next-action: <build id>
body    ["{id}"]
```

Phản hồi là React Flight (không phải JSON thuần); cây nằm ở dòng bắt đầu bằng
`1:`. Code: `src/legal_crawler/provision_tree.py`,
chạy bằng `scripts/pipeline/fetch_provision_trees.py` → `data/trees/{id}.json`.

Bốn điều đã kiểm chứng, cần nhớ:

1. **Phần slug trong URL không quan trọng.** Server chỉ đọc `--{id}` ở cuối; gọi
   `x--187835` vẫn ra đúng kết quả. Không cần dựng lại slug từ title.
2. **Cây rỗng `[]` là câu trả lời hợp lệ, không phải lỗi.** Công văn, Bản dịch,
   Văn bản hợp nhất, Sắc lệnh thập niên 1940 thường không có cấu trúc điều khoản.
   Vẫn ghi file rỗng ra đĩa để lần chạy sau không fetch lại.
3. **Số tầng thay đổi tùy văn bản.** Có văn bản bắt đầu từ Phần, có văn bản vào
   thẳng Điều. Đừng hard-code độ sâu, cứ đi theo `children` tới đâu hay tới đó.
4. **`next-action` là build id của Next.js — sẽ đổi khi vbpl.vn deploy lại.** Khi
   đó phản hồi mất hẳn dòng `1:`. Code cố tình **ném lỗi** (`StaleNextActionError`)
   chứ không trả `[]`, vì trả `[]` sẽ âm thầm ghi đè cả corpus bằng cây rỗng. Lấy
   build id mới bằng cách mở một trang văn bản trên trình duyệt, xem tab Network,
   copy header `next-action` của request POST tương ứng.

**Vì sao đây là thay đổi lớn**: Stage 5 từ *"viết parser HTML lồng nhau, mỗi loại
văn bản một kiểu, phải xem nhiều mẫu mới tin được"* trở thành *"đã có sẵn bộ
xương đúng từ server, chỉ còn map text vào"*. Và quan trọng không kém — cây này
dùng làm **bộ kiểm chứng**: parse HTML xong thì đối chiếu với cây, lệch là biết
parser sai ngay, không cần ngồi soát tay.

Lưu ý cây chỉ có tiêu đề (`"Điều 1"`, `"Khoản 2"`) và id, **không có nội dung
text** — ghép text vào vẫn là việc của Stage 5b.

## 5c. Kiểm chứng pipeline — `scripts/check/verify_pipeline.py`

Chạy `python scripts/check/verify_pipeline.py` (chỉ đọc file local, không gọi mạng,
chạy lại thoải mái). Thoát với mã 1 nếu có kiểm tra nào fail, nên dùng làm cổng
chặn trước khi tin dữ liệu cho bước sau.

**Kiểm tra quan trọng nhất — độ đầy đủ của phả hệ**: mọi cạnh `genealogy` phải
trỏ tới văn bản ta *đang có*, hoặc văn bản đã được ghi nhận rõ là đã mất. Một
đích genealogy chỉ đơn giản "không có" nghĩa là BFS ở Stage 2 đã đứt mất một
nhánh sửa đổi — và một văn bản bãi bỏ mà ta không tải về là một lần bãi bỏ ta
không bao giờ áp dụng được, tức sai lặng lẽ ở Stage 6.

### Sau Stage 2b — corpus phình 48%, cần biết rõ

| | Trước Stage 2b | Sau |
|---|---|---|
| Văn bản | 13.863 | **20.491** |
| Cạnh | 87.587 | **147.413** |
| Đích phả hệ | 8.283 | 14.076 (0 thiếu) |

Nguồn gốc từng văn bản (tra được từ `seeds.json` + `reverse_seeds.json`):

| Nhóm | Số văn bản |
|---|---|
| Seed — lọc từ khóa slug | 9.329 |
| BFS chiều xuôi | 8.827 |
| Stage 2b — chiều ngược | 2.335 |

**Thành quả chính**: trong 1.890 văn bản "hết hiệu lực một phần",
**1.846 (97,7%) nay đã biết văn bản nào tác động VÀ có đủ văn bản đó trong
corpus** (xét cả 6 mã 1/5/6/10/11/12). Chỉ còn 44 ca (2,3%) không truy được.
Đây chính là điều làm đường dự phòng của Stage 6 (§6c) trở nên khả thi.

⚠ **Câu hỏi còn bỏ ngỏ — độ lệch lĩnh vực.** Corpus tăng 48%, và trong nhóm mở
rộng có những văn bản trông rõ ràng ngoài 4 lĩnh vực ("Luật Viên chức", "tổ chức
pháp chế", "lãnh sự danh dự"). **Đã thử đo và THẤT BẠI**: dùng `documentMajors`
để chấm điểm thì 47,4% văn bản *seed* — vốn được chọn vì khớp từ khóa lĩnh vực —
cũng bị chấm là "ngoài lĩnh vực". Đúng lại bài học §3c: tag của nguồn quá nhiễu
để đo bất cứ thứ gì. Chỉ nói được định tính: nhóm mở rộng có tỷ lệ "toàn tag lạ"
cao hơn seed (70% và 64% so với 47%) → **có** lệch, nhưng không định lượng được.

Quan điểm xử lý: các văn bản này vào corpus là **đúng về mặt pháp lý** — mỗi cái
đều tác động lên, hoặc bị tác động bởi, một văn bản trong phạm vi. Thiếu chúng
thì suy luận point-in-time sai. Độ thuần lĩnh vực ảnh hưởng tới **chất lượng
truy hồi**, không ảnh hưởng tới **tính đúng đắn thời gian** — và truy hồi thì tự
nhiên sẽ không lôi "Luật Viên chức" ra cho câu hỏi về thuế.
→ **Giữ lại, nhưng luôn tra được nguồn gốc** (seed / BFS / Stage 2b) để khâu
đánh giá có thể đo cả hai cách: trên toàn corpus và chỉ trên phần seed.

Kết quả lần chạy 2026-09-04 (trước Stage 2b) — **toàn bộ PASS**:

| Hạng mục | Kết quả |
|---|---|
| 13.863 file raw | JSON hợp lệ, id khớp tên file, đều có title |
| Mã `referenceType` trong raw | 13 mã, đều nằm trong bảng đã xác minh |
| 87.587 cạnh | không cạnh nào có nguồn lạ; nhãn khớp bảng hiện tại |
| **8.283 đích genealogy** | **8.272 đã tải + 11 ghi nhận đã mất + 0 thiếu** |
| 9.329 seed | đều đã tải; slug đều thật sự khớp từ khóa domain |
| 8 văn bản loại trừ | đều thuộc seed (không đụng văn bản tìm qua BFS) |
| Manifest | 13.863 dòng, không trùng, phủ đúng corpus |
| Nguồn gốc văn bản | **0 văn bản mồ côi** — mọi văn bản đều là seed hoặc đích của một cạnh |

Hai con số hay bị hiểu nhầm:

- **Seed: cộng dồn 9.917 nhưng chỉ 9.329 id duy nhất.** 588 văn bản khớp từ khóa
  của **nhiều lĩnh vực** cùng lúc (VD thuế + giao thông). Cộng số liệu từng
  domain là đếm trùng.
- **Corpus 13.863 = 9.329 seed + 4.534 tìm thêm qua BFS phả hệ.** Tức mở rộng
  theo phả hệ đóng góp ~1/3 corpus — phần mà lọc từ khóa slug không bao giờ thấy.

**Đích open_citation không có nội dung là chuyện bình thường** (1.831/6.215) —
theo thiết kế, nhóm cạnh này được ghi lại nhưng không bao giờ dùng để đi tiếp.

### Độ tin cậy của cây điều khoản (mẫu 800 cây)

Cây từ server tốt, nhưng **không phải 100%** — Stage 5b phải đối chiếu, không
được tin mù:

| | |
|---|---|
| Khớp hoàn toàn với nội dung HTML | 63,9% |
| Khớp, nhưng có node `Article` **không đánh số** (chỉ ghi `"Điều"`) | 3,1% |
| Cây rỗng | 20,8% |
| Có cây nhưng không có node `Article` nào | 9,1% |
| HTML kiểu cũ, không đánh số Điều (dùng Mục I, II...) | 2,0% |
| ⚠ **Cây liệt kê Điều mà HTML KHÔNG có** | **1,1%** |

Hai điều Stage 5b bắt buộc phải xử lý:

1. **Không được lấy số Điều bằng cách parse tiêu đề node.** Có node chỉ ghi
   `"Điều"` trống trơn (VD doc `24657`, Thông tư kiểu cũ). Dùng `orderIndex` và
   `id` của node làm khoá, tiêu đề chỉ để hiển thị.
2. **Cây có thể thừa so với nội dung.** VD doc `113443`: cây khai có `Điều 10`
   và `Điều 12`, nhưng HTML chỉ tới `Điều 9` và kết thúc bình thường bằng `./.`
   (không phải nội dung bị cắt). Khi cây và nội dung mâu thuẫn → **ghi vào hàng
   đợi review, không tự chọn bên nào**, đúng tinh thần §3b.

## 5d. Độ đầy đủ nội dung — đo trên toàn bộ 13.863 văn bản (2026-09-04)

**Kết luận ngắn: 1.385 văn bản (10%) KHÔNG có nội dung text. Nhưng phần lớn số
đó là loại văn bản mà §4 vốn đã tuyên bố nằm ngoài phạm vi.**

Tách theo phạm vi §4 ("chỉ QPPL trung ương, loại trừ văn bản hành chính thường"):

| Nhóm | Số văn bản | Rỗng |
|---|---|---|
| **QPPL** (Luật, Bộ luật, Hiến pháp, Pháp lệnh, Lệnh, Nghị định, Nghị quyết, Quyết định, Thông tư, TT liên tịch, Sắc lệnh) | 12.820 (92,5%) | **698 (5,4%)** |
| **Ngoài phạm vi §4** (Công văn, Văn bản hợp nhất, Chỉ thị, Bản dịch, Thông báo...) | 1.043 (7,5%) | **687 (65,9%)** |

Nói cách khác: gần **một nửa số văn bản rỗng là loại lẽ ra không nên có trong
corpus**. Chúng lọt vào qua mở rộng phả hệ ở Stage 2 (cạnh phả hệ của một Luật
trỏ sang Văn bản hợp nhất, Công văn của nó) — không phải bug của BFS, nhưng
đúng là lệch với phạm vi đã tuyên bố.

Rỗng theo loại, các con số đáng chú ý:

| Loại | Rỗng / tổng | |
|---|---|---|
| Công văn | 314/357 (88%) | ngoài phạm vi, giá trị pháp lý thấp |
| Văn bản hợp nhất | 372/437 (85%) | ngoài phạm vi, là văn bản **phái sinh** |
| Thông tư | 435/5.501 (7,9%) | ⚠ mất thật |
| Quyết định | 132/3.239 (4,1%) | |
| Nghị định | 66/2.425 (2,7%) | |
| **Luật** | **4/444 (0,9%)** | rất tốt |
| Pháp lệnh, Bộ luật, Hiến pháp, Lệnh, Sắc lệnh | 0 | trọn vẹn |

**Nội dung mất có lấy lại được không?** 97% văn bản có `hasOriginalPdf: True` và
tên file kiểu `tvHienThiToanVan_*.pdf` (toàn văn). Nhưng endpoint tải file
`/api/qtdc/public/file/{tên file}` trả **401** — cùng bức tường auth như search
API (§1). Muốn lấy phải đi đường headless browser + parse PDF (+ có thể OCR).
**Chưa làm — xem đánh giá bên dưới.**

⚠ `hasContent` **nói dối**: 287 văn bản ghi `hasContent: True` nhưng nội dung
rỗng hoàn toàn. Đừng dùng cờ này để lọc, hãy đo độ dài text thật.

### Tại sao chưa đi lấy PDF

Câu hỏi quyết định không phải "mất bao nhiêu" mà **"phần mất có chặn Stage 6
không"**. §6c đã chỉ ra: với ~78% văn bản hết hiệu lực một phần,
`expiryProvisions` rỗng nên phải đọc **nội dung của văn bản sửa đổi**. Vậy đo
đúng chỗ đó:

| | |
|---|---|
| Văn bản dính vào cạnh "sửa đổi bổ sung" mà bị rỗng | chỉ **2,0-2,8%** |
| Văn bản "hết hiệu lực một phần" bị **bí hoàn toàn** (mọi văn bản sửa đổi nó đều rỗng) | **4 / 1.054** |
| Văn bản "hết hiệu lực một phần" **không có cạnh sửa đổi nào** | 227 — vấn đề riêng, không phải do thiếu nội dung |

→ **Đường dự phòng của Stage 6 đi được với ~98% trường hợp.** Đầu tư vào
headless-browser + PDF + OCR để cứu 5,4% QPPL, trong đó chỉ 4 văn bản thực sự
chặn đường, là không đáng ở giai đoạn này. **Ghi nhận tỷ lệ, đi tiếp**; quay lại
nếu khâu đánh giá cho thấy đúng những văn bản đó mới quan trọng.

Bốn văn bản Luật rỗng (để tra khi cần): `139882`, `101890` (sửa đổi Luật Thuế
GTGT/TTĐB — đúng lĩnh vực đề tài), `187763` (sửa đổi Luật Quản lý nợ công, còn
hiệu lực), `139878`.

## 5e. Đo recall — bỏ sót bao nhiêu? (`scripts/check/measure_recall.py`)

**Đây là điểm mù mà không kiểm tra cục bộ nào chạm tới được.** `verify_pipeline.py`
chỉ suy luận được trên văn bản đã có; văn bản chưa bao giờ phát hiện thì không
để lại dấu vết nào để mà kiểm.

**Không dùng `keyword` của `/doc/all` làm mẫu số**: nó là tìm toàn văn rất nhiễu
trên cả 172k văn bản kể cả địa phương — "giao thông" trả về 102k kết quả, trong
đó có cả thông tư về hội đồng trường (khớp rời "giao"/"thông"). Không định nghĩa
được "văn bản thuộc lĩnh vực này".

**Thước đo dùng thay thế: sitemap trung ương** — tập đếm được đầy đủ, đúng định
nghĩa Stage 1 đã dùng.

| | |
|---|---|
| Vũ trụ trung ương (sitemap) | 57.074 |
| Đang giữ | **19.589 (34,3%)** |
| Không giữ | 37.485 |
| Corpus không nằm trong sitemap trung ương | 902 (phả hệ kéo về, id UUID mới) |

Trong 37.485 văn bản không giữ, đối chiếu với **danh sách từ khóa RỘNG hơn**
Stage 1 (cố tình rộng để ra cận trên): **1.031 ca (1,8% vũ trụ)** trông có vẻ
thuộc lĩnh vực. Bóc tách:

| | |
|---|---|
| Chỉ khớp danh sách rộng → **ứng viên bỏ sót thật** | 915 (89,4%) |
| Văn bản hợp nhất — ngoài phạm vi §5d | 108 (10,6%) |

**Từ khóa nào đang thiếu trong `config.py`** (số ca bắt được):

| Rõ ràng thuộc lĩnh vực | | Còn tranh cãi — là ngành luật riêng | |
|---|---|---|---|
| `su-dung-dat` + `giao-dat` + `quy-hoach-su-dung-dat` | 94 | `ke-toan` | 273 |
| `hoa-don` | 42 | `kiem-toan` | 192 |
| `cang-bien` | 25 | `xuat-nhap-khau` | 114 |
| `dang-kiem` | 22 | `dau-thau` | 58 |
| `co-phan-hoa` | 21 | `canh-tranh` | 28 |
| `dang-ky-kinh-doanh` | 18 | `thu-ngan-sach` | 20 |

⚠ **Lỗ hổng đáng chú ý nhất: `dat-dai` không khớp "sử dụng đất"** — cách diễn đạt
phổ biến NHẤT trong luật đất đai (VD "Nghị quyết về kế hoạch sử dụng đất",
"Nghị định quy định thời điểm xác định giá đất"). Đây là bỏ sót thật, không phải
nhiễu của phép đo.

→ **Kết luận: recall cao, khoảng trống thật rơi vào 0,4%-1,6% vũ trụ trung ương**
tuỳ định nghĩa lĩnh vực rộng hay hẹp, và tập trung ở vài cách diễn đạt cụ thể mà
danh sách từ khóa không phủ.

### Đã xử lý (2026-09-04)

Bổ sung 8 từ khóa vào `KEYWORDS_BY_DOMAIN` — **chỉ nhóm rõ ràng thuộc lĩnh vực**:
`su-dung-dat`, `giao-dat` (đất đai) · `hoa-don` (thuế) · `co-phan-hoa`,
`dang-ky-kinh-doanh` (doanh nghiệp) · `dang-kiem`, `cang-bien` (giao thông).

Kết quả chạy lại Stage 1: **seed 9.329 → 9.806 (+477)**, không mất seed nào.
`dat_dai` tăng mạnh nhất: **438 → 772 (+76%)**, xác nhận `su-dung-dat` đúng là lỗ
hổng lớn nhất. Trong 477 seed mới, 235 đã có sẵn trong corpus (phả hệ đã kéo về
từ trước) — chỉ 242 cần tải mới.

*Không thêm* `quy-hoach-su-dung-dat`: cách khớp là nguyên-từ-liên-tiếp nên
`su-dung-dat` đã bao trùm nó. Đừng thêm dạng dài, chỉ tổ làm rối.

### Quyết định phạm vi: nhóm "tranh cãi" bị loại — có căn cứ, có số đo

`ke-toan`, `kiem-toan`, `xuat-nhap-khau`, `dau-thau`, `canh-tranh`,
`thu-ngan-sach` **không** được thêm. Đây là quyết định có chủ đích, không phải
bỏ sót — lý do đo được:

| Từ khóa | Tổng TW | Đã có trong corpus | Độ phủ |
|---|---|---|---|
| `dau-thau` | 169 | 109 | **64,5%** |
| `thu-ngan-sach` | 61 | 39 | 63,9% |
| `ke-toan` | 523 | 228 | 43,6% |
| `xuat-nhap-khau` | 202 | 86 | 42,6% |
| `canh-tranh` | 61 | 24 | 39,3% |
| `kiem-toan` | 350 | 129 | 36,9% |

**Loại trừ ≠ vắng mặt.** Mở rộng phả hệ đã tự kéo về 37-65% số văn bản này —
đúng những cái *có liên kết pháp lý* với 4 lĩnh vực. Phần còn thiếu là phần không
sửa đổi, không bị sửa đổi bởi, và không hợp nhất với bất kỳ văn bản nào trong
phạm vi — tức luật kế toán/kiểm toán đứng độc lập. Cơ chế phả hệ đã lọc đúng phần
cần lấy mà không cần khai báo lĩnh vực.

Viết vào phần *giới hạn phạm vi* của luận văn theo đúng dạng này (có số), chứ
đừng im lặng — loại trừ có đo là quyết định, loại trừ im lặng là sơ suất.

⚠ **Rủi ro còn lại phải ghi vào phần hạn chế**: một văn bản thuế có thể *trích
dẫn* thông tư kế toán qua cạnh `căn cứ ban hành`/`dẫn chiếu`. Cạnh đó **được ghi
lại** nhưng ta cố tình không đi theo (§5, §2b) — hiện có **1.870 đích
open_citation không có nội dung**. Nếu một câu hỏi point-in-time phụ thuộc đúng
vào một trong số đó, hệ thống sẽ trả lời thiếu. Rủi ro này bị chặn và đo được;
đi theo cạnh trích dẫn thì nổ phạm vi (code 3 chiều ngược: 555.592 lần).

**Đảo ngược được**: thêm từ khóa chỉ là sửa một dòng `config.py` rồi chạy lại
Stage 1-2 (cộng dồn, không crawl lại). Danh sách ứng viên giữ ở
`data/recall_candidates.txt`.

**Phát hiện phụ — bằng chứng sống cho §6b**: 12 văn bản khớp cả danh sách **hẹp**
nhưng không có trong corpus. Kiểm tra: cả 12 đều **không có trong `seeds.json`**,
tức chúng xuất hiện trên sitemap **sau** ngày crawl (24/08 → 04/09, 11 ngày). Cả
12 đều là Văn bản hợp nhất. Nguồn thực sự thêm văn bản mới liên tục → delta crawl
(§6b) là việc bắt buộc, không phải tuỳ chọn.

## 6. Vận hành crawl (rate & lưu trữ)

- Latency tự nhiên ~1s/request → **không cần thêm delay nhân tạo lớn**. Thực tế
  đang chạy **tuần tự, một luồng**, cách nhau tối thiểu 0.3s
  (`ApiClient(min_interval_seconds=0.3)`), retry tối đa 3 lần. Chạy hết
  ~13.9k văn bản ở tốc độ này là chấp nhận được nên **chưa cần song song hoá**;
  nếu sau này thật sự cần nhanh hơn thì mới thêm luồng, và giữ mức 3-5 luồng
  thôi — đây là hạ tầng của Bộ Tư pháp, chưa thấy rate-limit cứng nhưng nên
  tôn trọng.

- **Hai header BẮT BUỘC** (`REQUEST_HEADERS` trong `config.py`) — thiếu một
  trong hai là hỏng:
  - `Referer: https://vbpl.vn/`
  - `User-Agent` bất kỳ trông giống trình duyệt. **User-Agent mặc định của thư
    viện `requests` bị WAF của site chặn thẳng 403.** Đây là lỗi rất dễ mất thời
    gian debug vì nó không giống lỗi "sai header", nó giống lỗi "bị cấm truy cập".

  Ngoài hai header trên thì **không** cần token hay cookie gì cho các endpoint
  `public`.

- **Lỗi 4xx KHÔNG BAO GIỜ được retry.** Đây là quy tắc quan trọng, đã cài trong
  `sources/api_client.py` (`DocumentNotFoundError`):
  - `/doc/{id}` trả **HTTP 400** kèm `invalid.document.entity.not.found` khi
    văn bản đó đã bị gỡ khỏi vbpl.vn nhưng vẫn còn văn bản khác trỏ tới nó
    (gọi là *dangling reference* — trích dẫn treo). Chuyện này xảy ra bình
    thường, không phải bug.
  - Đây là tình trạng **vĩnh viễn**, thử lại 3 lần cũng vẫn 400 → chỉ tốn gấp 3
    số request. Nên gặp 4xx là bỏ qua văn bản đó ngay và ghi lại id.
  - Chỉ **lỗi mạng và 5xx** mới được retry/backoff.
  - Nếu về sau thấy 4xx bị retry trở lại → đó là code bị hỏng lại, không phải
    tính năng.
- Lưu raw JSON theo `id` (một file/id hoặc DB) để pipeline resume được và tách biệt "raw scrape" khỏi "parse/transform" — tránh phải crawl lại khi đổi logic parse.
- `robots.txt` chỉ disallow `/api/` và `/Pages/` trên domain `vbpl.vn` (không áp dụng cho domain gateway) — nguồn sitemap và API gateway đều không bị chặn.

## 6b. Crawl lại phần thay đổi (delta crawl) — ⬜ CHƯA CÓ SCRIPT

**Vấn đề**: luật thay đổi liên tục, nên sau lần crawl đầu ta cần cách cập nhật
**chỉ phần đã đổi**, chứ không tải lại toàn bộ 13.9k văn bản mỗi lần.

Nhưng API không có endpoint kiểu "cho tôi những gì đã đổi từ ngày X" (search API
401). May là sitemap có `<lastmod>` cho từng URL — đó là tín hiệu chính để biết
cái gì vừa đổi.

1. **Manifest (sổ ghi chép cục bộ)**: một bảng SQLite lưu, cho mỗi văn bản:
   `id → {sitemap_lastmod, last_crawled_at, content_hash, eff_status, eff_to,
   removed_at}`. Bảng này **đã có sẵn** ở `data/manifest.sqlite`.
2. **Mỗi lần chạy delta**:
   - Tải lại 12 shard sitemap Trung ương (nhẹ, ~1.5MB/shard) → so `lastmod` mới với cái đã ghi trong manifest.
   - `id` mới, hoặc `lastmod` đã đổi → cho vào hàng đợi tải lại (đi qua Stage 3-6 như thường, nhưng chỉ trên tập nhỏ này).
   - `id` biến mất khỏi sitemap (hiếm) → đánh dấu `removed_at`, **không xoá khỏi graph** (còn cần cho truy vấn lịch sử) nhưng thôi không crawl nữa.
3. **Cái bẫy riêng của lĩnh vực pháp luật — hiệu lực đổi mà `lastmod` KHÔNG đổi.**
   Một văn bản có thể tự động hết hiệu lực đúng vào ngày `effTo` đã ghi sẵn từ
   trước, mà trang web chẳng sửa nội dung gì cả → `lastmod` y nguyên, và cơ chế
   so `lastmod` ở trên sẽ **không phát hiện được**.
   → Vì vậy: với mọi văn bản đang được đánh dấu "còn hiệu lực" trong manifest,
   **luôn gọi lại `/doc/{id}/history` mỗi lần chạy delta**, bất kể `lastmod` có
   đổi hay không. Payload nhỏ, rẻ, và đây là thứ giữ cho dữ liệu point-in-time
   không bị sai.
4. **Chạy lại nhiều lần phải ra cùng kết quả (idempotency)**: Stage 3-6 chạy lặp
   trên cùng một `id` không được sinh bản trùng — dùng `id` làm khoá chính xuyên
   suốt raw store, parsed store và graph (ghi đè/upsert, không phải thêm mới).
5. **`content_hash` để phân biệt "đổi thật" với "đổi vặt"**: hash của JSON trả về,
   dùng để biết nội dung có thay đổi thực sự không (VD văn bản hợp nhất được cập
   nhật). Nếu không có nó thì mỗi lần crawl đều tưởng là "có thay đổi" chỉ vì
   `viewCount` tăng thêm vài lượt xem.

## 6c. `/doc/{id}/history` — vì sao bắt buộc phải có

**Tóm tắt**: `effFrom`/`effTo` trong `data/raw/` chỉ là **ảnh chụp trạng thái tại
lúc crawl**. `history` mới là **chuỗi sự kiện theo thời gian**. Thiếu nó thì
Stage 6 không dựng nổi khoảng hiệu lực cấp điều khoản.

Ví dụ Pháp lệnh Thuế tài nguyên (`7804`). Trong raw chỉ có:
`effFrom = 1998-06-01`, `effTo = 2010-07-01`, `effStatus = "Hết hiệu lực toàn bộ"`.

`history` trả về từng mốc: `1998-04-16 DATE_BH` (ban hành) → `1998-06-02 DATE_HL`
(có hiệu lực) → `2010-07-02 DATE_HHL` (hết hiệu lực).

Ba thứ chỉ `history` mới có:

1. **`expiryProvisions` — điều/khoản nào hết hiệu lực. CÓ, NHƯNG PHỦ RẤT MỎNG.**
   Corpus có **1.054 văn bản "Hết hiệu lực một phần"** (so với 7.389 hết hiệu lực
   toàn bộ và 4.968 còn hiệu lực). Với nhóm này `effTo` là `null` và `effStatus`
   không nói gì về điều nào đã chết.

   Khi `expiryProvisions` có dữ liệu, nó ghi đường dẫn đầy đủ và ghép thẳng được
   vào cây §5b: `"Khoản 3, Điều 9, Mục 3, Chương II"`, `"Điểm b, Điều 2"`,
   `"Điều 5, Chương II"`.

   **Đo trên TOÀN BỘ 1.054 văn bản "hết hiệu lực một phần"** (backfill đã chạy
   xong, 13.862 file history):

   | | |
   |---|---|
   | **RỖNG — không nói điều nào chết** | **749 (71,1%)** |
   | Có liệt kê điều khoản cụ thể | 251 (23,8%) |
   | Chỉ ghi "Toàn bộ văn bản" | 54 (5,1%) |

   Ví dụ Luật Chứng khoán 2006 (`15052`) có 44 dòng `HHL1P3` — nhưng cả 44 dòng
   đều `expiryProvisions: []` và `sourceDocumentName: null`, tức biết "có 44 lần
   sửa" mà không biết sửa ở đâu.

   ⚠ **Hệ quả cho Stage 6**: không thể dựa vào một mình `history` để dựng khoảng
   hiệu lực cấp điều khoản — **76% trường hợp không có dữ liệu**. Phải đi đường
   khác: theo cạnh `referenceType = 10` sang văn bản sửa đổi rồi đọc chính nội
   dung văn bản đó (nó luôn ghi rõ "sửa đổi Điều X, Khoản Y"). **Đây chính là lý
   do Stage 2b (§2b) quan trọng**: nếu văn bản sửa đổi còn không có trong corpus
   thì đường dự phòng này cũng tắc.
2. **`sourceDocumentName` — văn bản nào gây ra thay đổi.** Dùng để kiểm chứng
   chéo các cạnh dựng từ `referenceType`: graph bảo A bãi bỏ B mà history của B
   không nhắc A → một trong hai sai.
3. **Dữ liệu gốc thay vì dữ liệu tóm tắt.** Hai nguồn đã lệch nhau ngay ở ví dụ
   trên (`effTo = 2010-07-01` vs `DATE_HHL = 2010-07-02`). Khi mâu thuẫn, tin
   bên ghi lại từng sự kiện.

### ⚠ Hai cái bẫy phải xử lý trước khi Stage 6 đọc `history`

**Bẫy 1 — `createdDate` KHÔNG phải ngày pháp lý.** Nó là ngày dòng dữ liệu được
tạo trong hệ thống. Phân biệt bằng `createdBy` (đo trên 1.377 file):

| `createdBy` | Số dòng | Ý nghĩa |
|---|---|---|
| `Job` | 2.435 | nhập theo lô — `createdDate` **là ngày pháp lý thật** |
| `Admin` | 3.692 | người nhập tay — `createdDate` là **lúc gõ vào**, không phải ngày pháp lý |
| `System Scheduler` | 35 | máy tự cập nhật trạng thái |

Ví dụ hỏng nếu bỏ qua: Luật Chứng khoán 2006 có dòng `DATE_BH` ghi
`createdDate = 2025-12-24` (do `Admin`) — dùng thẳng sẽ ra "Luật ban hành năm
2025". Đối chiếu: dòng `DATE_HL` do `Job` ghi `2007-01-02`, khớp `effFrom`.
→ **Chỉ tin `createdDate` ở các dòng `createdBy = "Job"`**; các dòng `Admin`
dùng để biết *có sự kiện gì*, không dùng để biết *sự kiện xảy ra khi nào*.

**Bẫy 2 — `content` là mã không có tài liệu, đúng lại bài toán `referenceType`
(§3b).** Toàn bộ tập giá trị, đếm trên 13.862 file history:

| Mã | Số dòng | | Mã | Số dòng |
|---|---|---|---|---|
| `CHL` | 22.715 | | `HHL1P1` | 1.412 |
| `HHL1P3` | 20.522 | | `HHL1P4` | 159 |
| `DATE_BH` | 19.737 | | `TNHL1P` | 81 |
| `HHL` | 14.518 | | `CCHL` | 75 |
| `DATE_HL` | 12.840 | | `HHL1P2` | 63 |
| `DATE_HHL` | 6.606 | | `TNHL` / `HHL1P` | 21 / 17 |

Ngoài ra ~1.400 dòng **không phải mã mà là câu tiếng Việt tự do**
("Cập nhật trạng thái hiệu lực từ X sang Y.").

**Điều may mắn: chính các dòng text tự do đó khai nghĩa của mã.** Cùng một phép
chuyển được ghi khi thì bằng mã, khi thì bằng chữ:

| Bằng mã | Bằng chữ | ⇒ suy ra |
|---|---|---|
| `CHL → HHL1P` (22 lần) | — | `CHL` = Còn hiệu lực |
| `HHL1P → HHL` (2 lần) | `Hết hiệu lực một phần → Hết hiệu lực toàn bộ` (1 lần) | `HHL1P` = Hết hiệu lực một phần, `HHL` = Hết hiệu lực toàn bộ |

Đây là ground-truth **lấy từ chính dữ liệu**, kiểm chứng chéo được — tốt hơn hẳn
đoán mò. **Vẫn còn chưa biết**: chữ số cuối trong `HHL1P1/2/3/4` nghĩa là gì, và
`TNHL`, `TNHL1P`, `CCHL` (đoán là *tạm ngưng hiệu lực* / *chưa có hiệu lực* —
**nhưng ĐOÁN, chưa xác minh**).

→ **Áp dụng đúng kỷ luật §3b trước khi diễn giải bất kỳ mã nào**: gom đủ tập giá
trị (xong, bảng trên) → đối chiếu ground-truth (một phần lấy được từ text tự do,
phần còn lại phải xem UI) → đóng băng thành file mapping → fail-loud khi gặp mã
lạ. Đoán nghĩa `HHL1P3` là đúng kiểu sai lầm mà §3b tồn tại để ngăn.

## 7. Trạng thái hiện tại (cập nhật 2026-08-25)

### Đã xong ✅

- [x] **Stage 1 — Seed discovery.** `scripts/pipeline/collect_seeds.py` → `data/seeds.json`.
      4 lĩnh vực: đất đai 438 seed, thuế 3.404, doanh nghiệp/đầu tư 3.679,
      giao thông 2.396.
- [x] **Stage 2+3 — BFS mở rộng + tải chi tiết.** Gộp chung trong
      `scripts/pipeline/build_graph.py` (chạy lại được, ngắt giữa chừng không sao).
      Kết quả: **13.863 văn bản** trong `data/raw/`, **87.587 cạnh** trong
      `data/edges.jsonl`, manifest trong `data/manifest.sqlite`.
- [x] **Stage 3b — Bảng mapping `referenceType`.** 13 mã, xác minh thủ công,
      đóng băng trong `data/reference_type_map.json`. Xem §3b.
- [x] **Stage 4 — Rà soát lĩnh vực có người duyệt.** `filter_by_field.py` sinh
      danh sách khả nghi → người duyệt → `apply_field_review.py` chốt vào
      `data/excluded_ids.txt`. Xem §3c để hiểu vì sao KHÔNG tự động hoá bước này.

### Chưa xong ⬜

- [~] **Stage 5a — Tải cây điều khoản** (`scripts/pipeline/fetch_provision_trees.py` →
      `data/trees/`). **Đang chạy** trên toàn bộ 13.863 văn bản, ~1.7 giờ.
      Chạy lại được, ngắt giữa chừng không sao (file đã có = đã xong).
- [ ] **Stage 5b — Map text vào cây.** Ghép nội dung trong
      `documentContent.content` vào đúng node của cây đã tải ở 5a, rồi dùng
      chính cây làm bộ kiểm chứng. **Nhẹ hơn hẳn so với kế hoạch cũ** (viết
      parser đoán cấu trúc) — xem §5b. Stage 6 phải chờ bước này xong.
- [~] **Backfill `/doc/{id}/history`** (`scripts/pipeline/fetch_histories.py` →
      `data/history/`). **Đang chạy.** Đây từng là lỗ hổng: kế hoạch §5 ghi
      Stage 3 tải cả `/doc/{id}` **và** `/doc/{id}/history`, nhưng
      `build_graph.py` thực tế chỉ gọi `get_document()` — chưa từng gọi
      `get_history()` lần nào. Xem §6c để biết vì sao thiếu nó là hỏng Stage 6.
- [ ] **Stage 6 — Dựng temporal graph**: gắn khoảng hiệu lực `[t_start, t_end)`
      từ `effFrom`/`effTo`/`history[]` vào từng văn bản/điều khoản. Đây chính là
      nền tảng cho hỏi-đáp point-in-time — mục tiêu cuối của cả dự án.
      Phụ thuộc: Stage 5b (có node điều khoản) + backfill history ở trên.
- [ ] **Delta crawl (§6b) — chưa có script chạy.** Bảng manifest thì đã có sẵn
      và đúng schema rồi (`data/manifest.sqlite`: `doc_id`, `sitemap_lastmod`,
      `content_hash`, `eff_status`, `eff_to`, `last_crawled_at`, `removed_at`),
      chỉ còn thiếu đoạn code: tải lại sitemap → so `lastmod` → nạp lại phần
      thay đổi, và re-check `/history` cho mọi văn bản đang "còn hiệu lực".
