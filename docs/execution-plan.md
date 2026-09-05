# Execution Plan — 3 việc còn lại trước Stage 6

> `crawling-plan.md` trả lời **vì sao** và ghi lại những gì đã học.
> File này trả lời **làm gì tiếp, theo thứ tự nào, xong thì biết bằng cách nào**.
> Cập nhật 2026-09-04, sau khi corpus đạt 20.749 văn bản / 148.505 cạnh /
> 1.201.670 node điều khoản, `verify_pipeline.py` PASS toàn bộ.

## Thứ tự và phụ thuộc

```
   ┌─ A. Bảng mã trạng thái ──┐
   │   (nhỏ, ~2h)             ├──→  Stage 6: dựng temporal graph
   └─ B. Stage 5b: ghép text ─┘      (ngoài phạm vi file này)
        (lớn nhất, 3-5 ngày)

   C. Delta crawl — độc lập, chen vào lúc nào cũng được
```

A và B **không phụ thuộc nhau**, làm song song được. Cả hai đều phải xong trước
Stage 6. C độc lập hoàn toàn.

**Làm A trước** dù B mới là việc lớn: A chỉ tốn một buổi và nó quyết định *hình
dạng dữ liệu* mà Stage 6 sẽ đọc. Biết sớm thì thiết kế B không phải sửa.

---

## A. Bảng mã trạng thái hiệu lực — ✅ ĐÃ XONG (2026-09-04)

**Kết quả**: `data/eff_status_map.json` (13 mã, đều verified) +
`src/legal_crawler/status_codes.py` (loader fail-loud) +
`scripts/collect_status_codes.py` + 6 test. `verify_pipeline.py` có thêm kiểm
tra "mọi mã trong `data/history/` đều nằm trong bảng". Tổng 38 test PASS.

**Mục tiêu ban đầu**: mọi mã trong `history[].content` đều có nghĩa được xác
minh, và gặp mã lạ thì chương trình dừng chứ không đoán bừa (kỷ luật §3b).

### Đã giải quyết xong — mapping nằm sẵn trong API

Không cần scrape UI như đã lo. Trường `effStatus` trong `/doc/{id}` trả về **cả
`code` lẫn `name`**, tức chính nguồn đang dùng đã tự khai:

| Mã | Nghĩa | Số văn bản |
|---|---|---|
| `HHL` | Hết hiệu lực toàn bộ | 11.214 |
| `CHL` | Còn hiệu lực | 7.102 |
| `HHL1P` | Hết hiệu lực một phần | 1.899 |
| `TNHL` | Ngưng hiệu lực | 29 |
| `CCHL` | Chưa có hiệu lực | 27 |
| `KCPH` | Không còn phù hợp | 20 |

Kiểm chứng chéo: các dòng text tự do trong `history` ghi cùng phép chuyển bằng
chữ (`CHL → HHL1P` và "Hết hiệu lực một phần → Hết hiệu lực toàn bộ"), khớp.

### Còn lại 2 nhóm

**Nhóm `DATE_*`** — `DATE_BH`, `DATE_HL`, `DATE_HHL`. Nghĩa gần như chắc chắn là
ngày ban hành / ngày có hiệu lực / ngày hết hiệu lực, và đối chiếu số học đã ủng
hộ (`DATE_HL` khớp `effFrom`). **Vẫn phải xác minh** trên 2-3 văn bản mẫu bằng
cách so với ngày hiển thị trên UI — rẻ, và đây là mã Stage 6 dùng nhiều nhất.

**Nhóm `DATE_*`** đã xác minh bằng đối chiếu số học trên toàn corpus: với dòng do
`Job` ghi, `DATE_BH` khớp `issueDate`, `DATE_HL` khớp `effFrom`, `DATE_HHL` khớp
`effTo`.

### Hậu tố số — điều tra kỹ, và KẾT LUẬN LÀ "KHÔNG BIẾT"

`HHL1P1`, `HHL1P2`, `HHL1P3`, `HHL1P4`, `TNHL1P`. Đã thử 5 hướng:

| Hướng điều tra | Kết quả |
|---|---|
| Hậu tố = cấp điều khoản (Chương/Điều/Khoản)? | ❌ cả 4 mã đều trộn Khoản/Điều/Điểm tỷ lệ tương tự |
| Hậu tố = đợt nhập liệu? | ❌ 120 văn bản chứa cả `HHL1P1` lẫn `HHL1P3` cùng lúc |
| Hậu tố = loại quan hệ gây ra? | ⚠ tương quan mạnh nhưng không tuyệt đối: `HHL1P1`→bãi bỏ 75%, `HHL1P3`→sửa đổi 85% |
| Nhãn trong JS bundle? | ❌ chuỗi `HHL1P` **không xuất hiện ở đâu** trong bundle — giao diện không bao giờ hiển thị mã này |
| Server action nào trả nhãn? | ❌ đã thử 7 action, không cái nào có |

**Phát hiện quan trọng kèm theo — frontend phân biệt một phần / toàn bộ bằng một
trường KHÁC**, tên `effectAllType`, nằm trên đối tượng quan hệ:

```js
ABROGATES + effectAllType ∈ {1,3}      → "Bãi bỏ một phần"
ABROGATES + effectAllType ∈ {0,2,null} → "Bãi bỏ toàn bộ"
REPLACES  + effectAllType ∈ {1,3,null} → "Thay thế một phần"
REPLACES  + effectAllType ∈ {0,2}      → "Thay thế toàn bộ"
AMENDS_SUPPLEMENTS / SUPPLEMENTS       → "Sửa đổi, bổ sung"
```
*(trích từ `page-*.js`, hàm `matches`/`getSubtitle` của tab Lược đồ)*

Đây **đúng là thứ Stage 6 cần**: phân biệt tác động một phần với toàn bộ ở mức
từng cạnh. Nhưng `effectAllType` **không có trong bất kỳ endpoint nào ta với tới
được** — không có trong `references[]`, không trong `/diagram`, không trong 7
server action đã thử. Cùng số phận với `provisionTree` và `referenceProvisions`
(cả hai cũng luôn rỗng/null).

→ **Quyết định**: dùng **tiền tố**, thứ đã xác minh chắc chắn. Mọi `HHL1P*` đều
mang `effect = "expired_partial"`; giữ nguyên mã gốc trong dữ liệu; **không gán
nghĩa pháp lý cho chữ số**. Ghi rõ trong `_on_the_numeric_suffixes` của file
mapping, kèm cả tương quan thống kê và lời cảnh báo rằng đó chỉ là tương quan.

Đây là kết luận theo đúng tinh thần §3b: **không biết thì ghi là không biết**,
và chọn cách xử lý không phụ thuộc vào phần chưa biết.

### Hai cái bẫy đã được đóng gói thành code

1. `is_legal_date(row)` — `createdDate` chỉ là ngày pháp lý khi
   `createdBy == "Job"`. Dòng `Admin` (107.074 dòng, chiếm đa số) mang dấu thời
   gian lúc nhân viên gõ vào.
2. `parse_transition(content)` — 13 loại câu text tự do được nhận diện và tách
   thành cặp (từ → sang), thay vì ném lỗi "mã lạ". Chính các câu này là bằng
   chứng chéo xác nhận `CHL`/`HHL`/`HHL1P`.

---

## B. Stage 5b — ghép text vào cây điều khoản — ✅ ĐÃ XONG

**Kết quả**: `src/legal_crawler/provision_text.py` +
`scripts/attach_provision_text.py` + `data/provisions/{id}.json` + 6 test.
`verify_pipeline.py` có thêm 4 kiểm tra Stage 5b.

### Điều bất ngờ: bài toán dễ hơn plan tưởng rất nhiều

Plan này viết dựa trên giả định "phải dò regex `Điều N` trên nội dung rồi căn
chỉnh với cây". **Giả định đó sai với phần lớn corpus.** Mở nội dung HTML ra
xem thì server đã tự gắn sẵn id của node cây vào từng đoạn:

```html
<p id="078fd8b7-5846-40a8-b41e-6c4cd2179180" class="prov-article">Điều 1. Phạm vi điều chỉnh</p>
<p id="cdad2135-e580-4ef6-8f3b-274bf5645f40" class="prov-clause">1. Thông tư này quy định ...</p>
```

`id` ở đây **trùng khít** `id`/`key` trong `data/trees/`. Với những văn bản đó
việc ghép không phải là căn chỉnh, mà là **phép nối chính xác** — không đoán,
không có ca lệch, không cần hàng đợi review.

Bài học: **mở dữ liệu ra xem trước khi thiết kế thuật toán.** Plan đã dành 3-5
ngày cho một bài toán mà 60% khối lượng của nó không tồn tại.

### Hai định dạng nội dung, hai đường xử lý

| Định dạng | Dấu hiệu | Cách ghép | Độ phủ đo được |
|---|---|---|---|
| Mới | `<p id="uuid" class="prov-*">` | nối theo id | **99,1%** |
| Cũ | `<!DOCTYPE html>`, không id | dò marker theo thứ tự cây | **88,0%** |

Đường "marker" đi tuần tự: cây và nội dung đều đã đúng thứ tự văn bản, nên chỉ
quét tới. Node nào không tìm thấy marker thì **bỏ qua node đó** rồi đi tiếp, chứ
không dịch toàn bộ phần còn lại — một lỗi lệch không được phép lan.

### Hai lỗi thật đã sửa trong lúc làm

1. **Văn bản cũ dùng `<div>` chứ không phải `<p>`.** Parser chỉ tách theo `<p>`
   trả về **rỗng hoàn toàn** cho những văn bản này — trông y hệt "văn bản không
   có nội dung". Sửa: tách theo cả `div`/`li`/`td`/`h1..h6`. Độ phủ đường marker
   nhảy từ 78,9% lên 88,0%.
2. **Đoạn không có id là đoạn nối, không phải node mới.** Phải gắn vào node liền
   trước; nếu không thì `Chương I` mất mất dòng tiêu đề `QUY ĐỊNH CHUNG` của nó.

### Cái KHÔNG làm, và vì sao

- **Không chuẩn hoá dấu thanh kiểu cũ** (`thuỷ`→`thủy`). Plan có đề xuất, nhưng
  đây là **chính văn pháp luật**: sửa chính tả nghĩa là câu trích dẫn không còn
  khớp nguồn. Chỉ chuẩn hoá Unicode NFC (an toàn, không đổi chữ).
- **Không lưu offset ký tự.** Plan đề xuất để "giữ đường về văn bản gốc" — nhưng
  chính `node_id` đã là đường về đó, và nó nằm sẵn trong HTML. Lưu text thẳng.
- **Không lưu node rỗng.** Bộ xương đã có trong `data/trees/`; nhân bản 1,2 triệu
  node rỗng không được gì.
- **Không đoán cho cây không đánh số.** Văn bản cũ có cây kiểu `Phần` / `Điều` /
  năm node cùng tên `Khoản 1`, trong khi thân bài đánh `I.` / `1.1.`. Không có
  cách ghép trung thực → vào `data/provision_review.txt` (§3b).

### Đầu ra

`data/provisions/{doc_id}.json` (~29 KB/văn bản):

```json
{"doc_id": "...", "method": "id", "coverage": 1.0, "total_nodes": 717,
 "nodes": {"<uuid>": {"level": "Article", "title": "Điều 3",
                      "order_index": 12, "parent_id": "<uuid>", "text": "..."}}}
```

---

## C. Delta crawl — ✅ ĐÃ XONG

**Kết quả**: `scripts/delta_crawl.py` + 6 test + `data/delta_runs.jsonl`.

### Ý chính: không crawl lại, chỉ **xoá cache của phần đã cũ**

Mọi script tải dữ liệu ở đây đều đã resumable và bỏ qua thứ đã có trên đĩa. Nên
delta crawl không cần một đường BFS riêng — nó chỉ cần **quyết định cái gì cũ và
xoá file cache của cái đó**, rồi pipeline thường lấp đúng chỗ trống. Viết lại BFS
cho nhánh delta là nhân đôi phần khó rồi trông chờ hai bản tự đồng bộ.

### Bốn thứ bị coi là "cũ"

1. `lastmod` trên sitemap mới hơn bản ta giữ
2. Id mới, slug khớp keyword lĩnh vực
3. **Hết hiệu lực âm thầm**: manifest ghi `Còn hiệu lực` nhưng `effTo` đã qua.
   Đây chính là cái bẫy khiến `lastmod` một mình không đủ — một luật tới ngày
   hết hiệu lực của chính nó thì **trang không đổi gì cả**.
4. Biến mất khỏi sitemap → `removed_at`, **không xoá** (truy vấn lịch sử còn cần)

### Hai lỗi thật, phát hiện ngay lần chạy đầu

Lần dry-run đầu tiên báo **2.345 văn bản cũ** và **904 văn bản biến mất**. Cả hai
đều sai:

| Báo cáo sai | Nguyên nhân | Sau khi sửa |
|---|---|---|
| 2.345 "đã đổi" | 3.168 văn bản tìm bằng BFS có `sitemap_lastmod` **rỗng**; so `""` với một lastmod thật thì cái nào cũng "khác" | **84** |
| 904 "biến mất" | Chúng **chưa bao giờ** có trên shard trung ương (BFS tìm ra). Vắng mặt không chứng minh được gì | **0** |

Sửa: lastmod rỗng chỉ là *lỗ hổng ghi chép của ta*, không phải bằng chứng trang
đã đổi — chỉ coi là cũ khi lần sửa trên sitemap **mới hơn** `last_crawled_at`. Và
chỉ đánh dấu `removed_at` cho văn bản ta **từng thấy** trên sitemap.

Cả hai lỗi đều thuộc một dạng: **coi "không có dữ liệu" là "dữ liệu nói khác".**

### Trạng thái hiện tại (dry-run 2026-09-05)

57.082 mục sitemap · **84** cũ (9 do quá `effTo`) · **5** văn bản mới đúng lĩnh
vực · **0** biến mất.

### Ghi mốc thời gian

Mỗi lần chạy ghi một dòng vào `data/delta_runs.jsonl`, kể cả khi không có gì
đổi. Corpus point-in-time mà không ghi mốc là corpus không trả lời được câu
"tính tới lúc nào".

---

## Việc dọn dẹp kèm theo — ✅ ĐÃ XONG

- **Kiểm tra mã trạng thái** (sau A): `verify_pipeline.py` đòi mọi mã `content`
  trong `data/history/` phải nằm trong `eff_status_map.json`.
- **Kiểm tra Stage 5b** (sau B): 4 kiểm tra — không có file provisions mồ côi;
  **không văn bản nào có số node ghép được lớn hơn số node trong cây** (đây là
  kiểu hỏng duy nhất sẽ vô hình về sau: thuật toán bịa ra node); ≥90% node toàn
  corpus có text; mọi văn bản độ phủ thấp đều nằm trong hàng đợi review.
- **Danh sách lỗi có tên**: `data/fetch_failures.txt` ghi 18 văn bản không lấy
  được cây + 2 văn bản không lấy được history, kèm tiêu đề để tra cứu được.
  Đã thử lại toàn bộ 20 văn bản: **đều hỏng vĩnh viễn** (HTTP 500 từ chính
  vbpl.vn, hoặc phản hồi không có payload row).

  Kèm theo là một lỗi thật được phát hiện nhờ lần thử lại đó:
  `fetch_provision_trees.py` có ngưỡng "5 lỗi liên tiếp ⇒ NEXT_ACTION_ID hết
  hạn". Khi chạy lại mà **chỉ còn toàn văn bản đã biết hỏng**, ngưỡng này báo
  động nhầm ngay lập tức. Sửa: mặc định bỏ qua các id trong
  `fetch_failures.txt`, có cờ `--retry-failures` để thử lại khi cần.

---

## Còn lại gì

Stage 6 — dựng temporal graph. Mọi thứ nó cần đã có: cạnh phả hệ đã phân loại,
mốc thời gian pháp lý phân biệt được với dấu thời gian nhập liệu, và giờ là
**text ở cấp điều khoản**.
