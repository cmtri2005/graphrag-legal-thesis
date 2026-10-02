# Khóa luận này là gì — từ đầu đến cuối

Date: 2026-10-01

> Tài liệu định hướng. Mục đích: đọc một lần là hiểu **cái gì**, **để làm gì**,
> **tại sao phải làm thế**, và **đang ở đâu**. Mọi con số trong đây đều lấy từ
> dữ liệu thật trong repo, kèm đường dẫn để tự kiểm tra lại.
>
> Thứ tự đọc: §1 (vấn đề) → §2 (ví dụ chạy suốt) → §3 (vì sao cần đồ thị) →
> §4 (sáu tầng) → §5 (dữ liệu nằm đâu) → §6 (bộ đánh giá) → §7 (đo bằng gì) →
> §8 (so với cái gì) → §9 (đang ở đâu) → §10 (quyết định) → §11 (rủi ro).

---

## 1. Khóa luận trả lời câu hỏi gì

**Bài toán.** Cho một câu hỏi pháp luật `x` **và một mốc thời gian `t`**, trả về
câu trả lời đúng *tại thời điểm t*, kèm trích dẫn điều khoản **đang có hiệu lực
tại t**.

Khác biệt với hỏi đáp pháp luật thường: truy vấn là một **cặp `(x, t)`**. Cùng
một câu hỏi, hai mốc khác nhau, có thể hai đáp án khác nhau và hai bộ trích dẫn
khác nhau.

**Vì sao đây là vấn đề thật.** Hệ RAG thông thường mặc định kho tri thức là
tĩnh: mỗi đoạn văn bản là một đơn vị độc lập, xếp hạng theo độ giống câu hỏi.
Với văn bản pháp luật, giả định đó sai — điều khoản liên tục bị sửa đổi, bổ
sung, thay thế, bãi bỏ. Hậu quả là **"ảo giác theo thời gian"** (*temporal
hallucination*): hệ thống trích đúng số hiệu Điều/Khoản nhưng đọc nội dung của
một phiên bản **đã hết hiệu lực**. Trích dẫn trông rất đúng, nội dung thì sai.

Đây là loại lỗi tệ nhất trong miền pháp lý, vì nó *không trông giống lỗi*.

---

## 2. Ví dụ chạy suốt — hãy nhớ đúng ví dụ này

Một điều khoản thật trong corpus của bạn:

> **Điểm đ, Khoản 4, Điều 84, Nghị định 98/2020/NĐ-CP**
> (xử phạt vi phạm hành chính trong thương mại, sản xuất, buôn bán hàng giả)
>
> Khoản 4 nói về thẩm quyền của *Cục trưởng Cục điều tra chống buôn lậu,
> Cục trưởng Cục kiểm tra sau thông quan* thuộc Tổng cục Hải quan.

Câu hỏi: **"Người này được áp dụng những biện pháp khắc phục hậu quả nào?"**

Nội dung thật của điều khoản đó qua thời gian:

| Phiên bản | Hiệu lực | Nội dung |
|---|---|---|
| **v1** | `[2020-10-15, 2022-01-31)` | "…quy định tại các điểm **a, b, d và e** khoản 3 Điều 4 của Nghị định này." |
| **v2** | `[2022-01-31, 2025-02-21)` | "…quy định tại các điểm **a, b, d, e và l** khoản 3 Điều 4 của Nghị định này." |
| **v3** | `[2025-02-21, …)` | "…quy định tại các điểm **d, đ, g, i khoản 1 Điều 28 của Luật Xử lý vi phạm hành chính** và khoản 3 Điều 4 của Nghị định này." |

Tự kiểm tra: `grep provision:40778740-2c7f-11f1-abee-c9b7a53cf5c7 data/derived/versions.jsonl`

**Ba điều rút ra, và cả ba đều là một phần của khóa luận:**

1. **Câu hỏi có ba đáp án đúng khác nhau, tùy `t`.** Hỏi ở mốc 2021 → v1. Hỏi ở
   mốc 2023 → v2. Hỏi hôm nay → v3. Một hệ thống chỉ lưu "nội dung hiện hành"
   sai ở hai trong ba giai đoạn. Một hệ thống crawl về rồi để nguyên cũng vậy.

2. **v1 và v2 khác nhau đúng một chữ: thêm "và l".** Hai phiên bản gần như giống
   hệt nhau về mặt từ vựng và ngữ nghĩa. Mọi bộ truy xuất dựa trên độ tương đồng
   — BM25 hay embedding — đều **không thể phân biệt** chúng, vì chúng *thực sự*
   giống nhau. Chỉ có khoảng hiệu lực phân biệt được. Đây chính là nhóm câu hỏi
   **T4 (bẫy trích dẫn)** trong bộ dữ liệu.

3. **Ai đã sửa nó?** Phiên bản 2 do **Nghị định 17/2022/NĐ-CP** tạo ra — mà
   Nghị định 17/2022 có tên là *"quy định về xử phạt vi phạm hành chính trong
   lĩnh vực hóa chất và vật liệu nổ"*. **Một lĩnh vực hoàn toàn khác.** Không
   có mô hình ngữ nghĩa nào nối "hàng giả" với "hóa chất và vật liệu nổ". Chỉ
   có **quan hệ tường minh giữa hai văn bản** làm được việc đó.

   Event thật đã tạo ra v2:

   ```
   id            event:152897:8c19e3f6c0e5e324292ec151
   actor         17/2022/NĐ-CP  (document:152897)
   operation     amend          effective_on 2022-01-31
   evidence      "Sửa đổi, bổ sung Điều 84 như sau"
   status        auto_accepted
   ```

Điểm 3 là lý do khóa luận cần một **đồ thị**, không phải chỉ một kho vector.

---

## 3. Vì sao phải là đồ thị có phiên bản — lập luận hình thức

Phần này là `docs/graph_justification.md`. Diễn giải lại cho dễ hiểu.

### 3.1 Bốn công thức

Gọi `𝒰` là tập đơn vị pháp lý (Phần, Chương, Mục, Điều, Khoản, Điểm). Mỗi đơn
vị `u` có đơn vị cấp trên `π(u)` và một chuỗi phiên bản.

**(1) Phiên bản tại thời điểm t.** `snapshot(u, t)` = phiên bản `vᵢ` mà
`sᵢ ≤ t < eᵢ`, hoặc `⊥` nếu không có. *(Khoảng nửa mở `[s, e)` — mốc đầu tính
vào, mốc cuối không. Dùng nhất quán khắp dự án.)*

**(2) Khoảng hiệu lực từ đâu ra.** `sᵢ, eᵢ` **không phải thuộc tính của chính
`u`**. Chúng do tập văn bản tác động `Act(u)` quyết định — mỗi văn bản tác động
`a` với thao tác `op ∈ {sửa đổi, bổ sung, thay thế, bãi bỏ}` mở hoặc đóng một
phiên bản tại ngày `τ(a)` mà `a` có hiệu lực. Và `a` **tự nó cũng có thể đã bị
sửa**, nên `Act` phải xét theo **bao đóng bắc cầu**.

**(3) Hiệu lực lan truyền trên cây.** Một đơn vị chỉ có hiệu lực khi *bản thân
nó* có phiên bản hiện hành **và** *đơn vị cấp trên của nó* cũng có hiệu lực:

```
valid(u, t) = [snapshot(u, t) ≠ ⊥] ∧ [π(u) = ⊥ ∨ valid(π(u), t)]
```

Nghĩa là: bãi bỏ **Điều 84** làm mọi Khoản, Điểm bên dưới mất hiệu lực, dù bản
thân chúng chưa bị ai chạm tới.

**(4) Bài toán.** Hệ thống phải trả về bằng chứng `E(x,t) ⊆ 𝒰ₜ`, với
`𝒰ₜ = {u | valid(u, t)}`.

### 3.2 Mệnh đề quyết định cả kiến trúc

Gọi *biểu diễn* `ρ(u)` là "những gì hệ truy xuất quan sát được về `u`".

> **Định nghĩa (biểu diễn đủ).** `ρ` là *đủ* nếu tồn tại hàm `g` sao cho
> `valid(u,t) = g(ρ(u), t)` với mọi `u`, mọi `t`.
>
> **Mệnh đề 1.** Nếu có `u, u'` và `t` mà `ρ(u) = ρ(u')` nhưng
> `valid(u,t) ≠ valid(u',t)`, thì `ρ` **không đủ**.

**Hệ quả — và đây là luận điểm trung tâm:** nếu biểu diễn không đủ, thì **không
bộ xếp hạng nào, không mô hình sinh nào** khôi phục được thông tin đã mất.
Nguyên nhân nằm ở **biểu diễn**, không nằm ở năng lực của model. Đổi sang LLM
to hơn không sửa được.

Quay lại ví dụ §2: với biểu diễn "chỉ có nội dung chữ", v1 và v2 gần như trùng
nhau nhưng hiệu lực khác nhau → đúng tiền đề của Mệnh đề 1 → biểu diễn đó
không đủ. Xong, chứng minh.

### 3.3 Ba loại thông tin phải có

Từ (1)–(3), `valid(u,t)` phụ thuộc ba thứ **nằm ngoài nội dung của `u`**:

| | Thông tin | Từ công thức | Nằm ở đâu trong đồ thị |
|---|---|---|---|
| **I1** | Chuỗi phiên bản và khoảng hiệu lực | (1) | cạnh `VERSION_OF`, nút `ProvisionVersion` |
| **I2** | Chuỗi đơn vị cấp trên `π(u), π(π(u))…` | vế đệ quy của (3) | cạnh `CONTAINS` |
| **I3** | Các văn bản tác động + bao đóng bắc cầu | (2) | 13 loại cạnh giữa văn bản |

Ba cái này là lý do tồn tại của đồ thị. Không phải vì "đồ thị đang hot".

### 3.4 Bằng chứng trên dữ liệu thật

Lập luận hình thức chỉ nói "có thể thiếu". Đo trên corpus cho thấy thiếu ở
**quy mô không bỏ qua được** (số của `graph_justification.md`, snapshot v1):

- **8.210** nhóm điều khoản có nội dung **trùng khớp** nhưng hiệu lực **trái ngược**
- **27,8%** đơn vị thuộc văn bản **hết hiệu lực một phần**
- **14.157** đơn vị mất hiệu lực **chỉ vì** đơn vị cấp trên bị bãi bỏ (I2)
- chuỗi tác động bắc cầu lên một văn bản có thể gồm tới **2.963** văn bản (I3)

---

## 4. Sáu tầng L0 → L5: mỗi tầng là gì, sinh ra cái gì

Đây là xương sống kỹ thuật. Mỗi tầng có đầu vào, đầu ra, và một file trên đĩa.

```
       vbpl.vn (Cơ sở dữ liệu quốc gia về văn bản pháp luật)
            │  crawl
            ▼
  ┌─────────────────────────────────────────────────────────┐
  │ L0  VĂN BẢN THÔ            data/raw/*.json      23.139  │
  │     + cây điều khoản       data/trees/                  │
  │     + nội dung chữ         data/provisions/             │
  ├─────────────────────────────────────────────────────────┤
  │ L1  CẤU TRÚC + METADATA                                 │
  │     1.700.484 đơn vị (Phần→Điểm), quan hệ CONTAINS      │
  │     128.548 cạnh giữa văn bản, 13 loại   data/edges.jsonl│
  ├─────────────────────────────────────────────────────────┤
  │ L2  THAO TÁC SỬA ĐỔI  ← phần khó nhất                   │
  │     "Sửa đổi Điều 84 như sau" → event có cấu trúc       │
  │     50.623 event      data/derived/provision_events.jsonl│
  ├─────────────────────────────────────────────────────────┤
  │ L3  CHUỖI PHIÊN BẢN + LAN TRUYỀN HIỆU LỰC               │
  │     áp event → v1,v2,v3 + khoảng hiệu lực thực          │
  │     1.595.823 phiên bản  data/derived/versions.jsonl    │
  ├═════════════════════════════════════════════════════════┤
  │ L4  TRUY XUẤT CÓ RÀNG BUỘC THỜI GIAN                    │
  │     lọc về 𝒰ₜ rồi mới xếp hạng    src/vilexgraph/framework/│
  ├─────────────────────────────────────────────────────────┤
  │ L5  SINH CÂU TRẢ LỜI + VERIFIER                         │
  │     trích dẫn cấp Điều/Khoản/Điểm, soi lại hiệu lực tại t│
  └─────────────────────────────────────────────────────────┘
       L0–L3 = offline, dựng một lần.  L4–L5 = chạy lúc truy vấn.
```

### L0 — Thu thập (xong ✅)

Crawl `vbpl.vn` bốn miền. Giữ **bản gốc không chỉnh sửa** trong `data/raw/`.

Bốn miền (`src/vilexgraph/build/config.py`): `dat_dai` (đất đai, nhà ở, bất động
sản), `thue` (thuế, phí, hải quan, hóa đơn), `doanh_nghiep_dau_tu` (doanh
nghiệp, đầu tư, chứng khoán), `giao_thong` (đường bộ, đường sắt, đường thủy,
hàng không).

**Nguyên tắc:** tầng thu thập **ghi** vào `data/` và không bao giờ *diễn giải*;
tầng diễn giải **đọc** `data/` và không bao giờ *ghi*. Mọi giá trị suy dẫn nằm
ở `data/derived/`, kèm phương pháp và trạng thái duyệt.

### L1 — Cấu trúc và quan hệ (xong ✅)

Dựng cây Phần › Chương › Mục › Điều › Khoản › Điểm, gắn nội dung chữ vào từng
nút. 13 loại quan hệ giữa văn bản đã **kiểm chứng tay** với tab "Lược đồ" của
cổng (`data/reference_type_map.json`), ví dụ: `1` = văn bản bị bãi bỏ,
`10` = văn bản được sửa đổi bổ sung, `12` = văn bản được thay thế.

### L2 — Trích xuất thao tác sửa đổi (🟡 đang làm, **khó nhất**)

**Việc gì:** biến câu văn tiếng Việt thành thao tác máy hiểu được.

> Đầu vào: `"Sửa đổi, bổ sung Điều 84 như sau"` + lời văn mới
> Đầu ra: `{operation: amend, target: provision:4075…, effective_on: 2022-01-31}`

**Vì sao khó:** 79,7% văn bản bị **nhiều** văn bản khác tác động, và cổng không
nói văn bản nào sửa khoản nào. Phải đọc lời văn.

**Đang ở đâu:** 50.623 event; precision kiểm tay **96,7%** (58/60), recall theo
`expiryProvisions` **62,2%**. Ba trạng thái: `verified` (cổng liệt kê đúng nút) ·
`auto_accepted` · `needs_review` (~21.900 event — **không bao giờ áp âm thầm**).

**Đây là nguồn sai số lớn nhất của cả dự án.** Recall 62,2% nghĩa là khoảng 38%
thao tác chưa bắt được → một số chuỗi phiên bản còn thiếu mắt.

### L3 — Hợp nhất phiên bản và lan truyền hiệu lực (🟡 gần xong)

Áp event lên cây → sinh chuỗi `v1 → v2 → v3`, rồi tính **khoảng hiệu lực thực**
bằng công thức (3): giao khoảng của chính phiên bản với khoảng của văn bản **và
của mọi tổ tiên**.

Lõi logic nằm ở `src/vilexgraph/build/temporal/`, **chỉ dùng stdlib, không phụ
thuộc database** — để có thể test được và để chỉ có *một* định nghĩa "có hiệu
lực tại t" (`ValidityService`).

**Hai loại khoảng, phải phân biệt — rất dễ nhầm:**

| | Là gì | Nằm đâu |
|---|---|---|
| **cục bộ** | khoảng của riêng chuỗi phiên bản | `valid_from`/`valid_to` trong `data/derived/versions.jsonl` |
| **lan truyền** | đã giao với văn bản **và mọi tổ tiên** — công thức (3) | `effective_intervals` trong `data/derived/corpus/versions.jsonl` |

Hai cột này khác nhau trên **790.025 / 1.595.823 phiên bản (49,5%)**. Trộn lẫn
chúng là lỗi *im lặng* — hệ thống vẫn chạy, vẫn ra số, chỉ là số vô nghĩa.

### L4 — Truy xuất có ràng buộc thời gian (🟡 vừa dựng xong tuần này)

Công thức (4): **thu hẹp về `𝒰ₜ` TRƯỚC khi xếp hạng**, không phải lọc sau khi
lấy top-k. Lọc sau thì đã xếp hạng tranh chấp với những đơn vị vốn phải bị loại.

### L5 — Sinh câu trả lời + Verifier (⬜ chưa làm)

Sinh câu trả lời **ràng buộc trích dẫn** ở cấp Điều/Khoản/Điểm, rồi
**Temporal Verifier** soi lại từng trích dẫn: nó có thật sự có hiệu lực tại `t`
không? Nếu không → loại bỏ hoặc cảnh báo.

---

## 5. Dữ liệu: cái gì nằm ở đâu, và nó trông như thế nào

Nguyên tắc nền (ADR 0001): **`data/` là nguồn sự thật duy nhất.** Neo4j và
Milvus là *kho dẫn xuất* — xóa đi dựng lại được. Mọi thứ trong `data/derived/`
cũng là dẫn xuất, sinh lại được bằng script.

### 5.1 Dữ liệu thô — crawl về trông ra sao

Một file `data/raw/<id>.json` là **bản ghi API nguyên trạng của cổng vbpl.vn**.
Ví dụ `data/raw/152897.json` (Nghị định 17/2022/NĐ-CP) có các trường chính:

| Trường | Giá trị thật | Ý nghĩa |
|---|---|---|
| `id` | `152897` | id của cổng |
| `docNum` | `17/2022/NĐ-CP` | số hiệu |
| `title` | `Nghị định số 17/2022/NĐ-CP quy định về xử phạt…` | tên |
| `issueDate` | `2022-01-31T00:00:00` | ngày ban hành |
| `effFrom` / `effTo` | `2022-01-31` / `None` | hiệu lực **cấp văn bản** |
| `effStatus` | `{…}` | mã trạng thái hiệu lực |
| `references` | **237 items** | quan hệ tới văn bản khác, mỗi cái có `referenceType` |
| `provisionTree` | `None` | cây điều khoản — **thường rỗng ở đây**, phải crawl riêng |
| `isConsolidatedDocument` | `False` | có phải văn bản hợp nhất (VBHN) |

Hai điều đáng chú ý ngay:

- `effFrom`/`effTo` là hiệu lực **cấp văn bản**. **Nó không đại diện cho hiệu
  lực cấp điều khoản.** Một văn bản còn hiệu lực hoàn toàn có thể chứa nhiều
  khoản đã bị bãi bỏ. Đây là lý do tồn tại của cả L2–L3, và là lý do đường cơ
  sở B7 (chỉ lọc theo ngày văn bản) **không đủ**.
- `references` cho biết *có* quan hệ, nhưng **không** cho biết văn bản nào sửa
  *khoản nào*, cũng không cho biết *khi nào*. Đó là việc của L2.

### 5.2 Bản đồ thư mục `data/`

Toàn bộ `data/` bị gitignore theo mặc định rồi whitelist từng file — tổng
khoảng 4 GB, không được vào git.

**Tầng thu thập (L0–L1), sinh ra bởi crawl:**

| Đường dẫn | Lượng | Là gì |
|---|---|---|
| `data/raw/` | 23.139 file · 1,6 GB | bản ghi API nguyên trạng |
| `data/trees/` | 23.121 file · 300 MB | cây Chương/Mục/Điều |
| `data/provisions/` | 19.794 file · 548 MB | nội dung chữ từng nút |
| `data/history/` | 23.137 file · 96 MB | lịch sử hiệu lực theo cổng |
| `data/diagrams/` | 23.023 file · 258 MB | tab "Lược đồ" (quan hệ ngược) |
| `data/edges.jsonl` | 128.548 cạnh | quan hệ giữa văn bản, 13 loại |
| `data/temporal.sqlite` | 1,6 GB | index offline L0–L1 (**chưa áp event**) |

**Tầng diễn giải (L2–L3), sinh ra bởi script:**

| Đường dẫn | Lượng | Là gì |
|---|---|---|
| `data/derived/eligibility.jsonl` | 23.139 | VB nào đủ điều kiện vào benchmark |
| `data/derived/provision_events.jsonl` | 50.623 | **L2** — thao tác sửa đổi |
| `data/derived/versions.jsonl` | 1.595.823 · 1,1 GB | **L3** — chuỗi phiên bản + khoảng hiệu lực |
| `data/derived/corpus/asis.jsonl` | 1.503.700 | **lớp A** — corpus "như công bố" |
| `data/derived/corpus/versions.jsonl` | 1.474.324 | **lớp B** — corpus "theo phiên bản" |
| `data/derived/corpus/index.sqlite` | 2.978.024 đơn vị · 3,7 GB | index truy xuất + BM25 (**dựng 01/10**) |
| `data/derived/vilextime/release.jsonl` | 2.481 dòng | **bộ dữ liệu đánh giá** |

> **Vì sao `temporal.sqlite` có 1.151.790 phiên bản còn corpus có 1.474.324?**
> Không phải lỗi. `temporal.sqlite` là index **trước khi áp event** — mỗi điều
> khoản một phiên bản, đúng như công bố. `derived/versions.jsonl` là output
> **sau L3** — đã nở ra thành chuỗi v1→v2→v3. Kiểm lại bằng ví dụ §2: truy
> `temporal.sqlite` chỉ ra **một** phiên bản; truy `versions.jsonl` ra **ba**.

### 5.3 Phạm vi: cái gì được truy xuất, cái gì không (ADR 0002)

Không phải mọi thứ crawl về đều vào benchmark:

- **Chỉ văn bản quy phạm pháp luật (QPPL) cấp trung ương** được truy xuất theo
  mốc `t`. Đo được: 20.318 QPPL trung ương; **17.307** văn bản vào corpus.
- **Văn bản hợp nhất (VBHN) KHÔNG được truy xuất.** VBHN là bản gộp do cơ quan
  nhà nước phát hành — dùng nó làm nguồn truy xuất là *gian lận*, vì nó đã làm
  sẵn công việc mà L2–L3 phải làm. VBHN chỉ dùng để **kiểm chứng** L3.
- Công văn, văn bản cá biệt, bản dịch, văn bản địa phương: giữ trên đĩa (vì là
  mắt trong chuỗi phả hệ) nhưng **loại khỏi truy xuất và benchmark**.
- **Không xóa văn bản đã hết hiệu lực.** Loại trừ bằng skip-list ở tầng đọc.
  Văn bản hết hiệu lực chính là thứ cần có để trả lời câu hỏi về quá khứ.

### 5.4 Corpus hai lớp — vì sao phải hai

| | Lớp A `asis.jsonl` | Lớp B `versions.jsonl` |
|---|---|---|
| Đơn vị | 1.503.700 | 1.474.324 |
| Mã | `asis:provision:<id>`, `asis:event:<id>` | `version:<provision>:<n>` |
| Là gì | "như công bố" — lời văn gốc | "theo phiên bản" — output của L2–L3 |
| Ai dùng | B2–B6, B7 | hệ đề xuất, B7+ |

Lớp A là **những gì bất kỳ ai làm RAG trên cổng cũng có được**. Đó là đối chứng
công bằng: nếu hệ đề xuất thắng, phải thắng trên cùng dữ liệu nguồn.

Lớp A có thêm **48.328 "đơn vị lệnh"** (`asis:event:…`): bản thân câu lệnh sửa
đổi, kèm lời văn nó trích. Lý do: cây điều khoản của văn bản sửa đổi **bỏ mất
lời văn được trích trong khoảng một phần ba trường hợp** — không có các đơn vị
này thì lời văn mới *không tồn tại ở đâu* mà một baseline phẳng có thể tìm, và
so sánh sẽ bất công với baseline.

---

## 6. ViLexTime — bộ dữ liệu đánh giá

### 6.1 Ý tưởng: gold không do LLM quyết định

Quy trình **diff-driven**: tìm các cặp `snapshot(u,t₁) ≠ snapshot(u,t₂)` trong
chính đồ thị → trích khác biệt thành (trước, sau, mốc chuyển) → **code tìm khác
biệt, LLM chỉ diễn đạt câu hỏi**. Nhãn vàng không phụ thuộc LLM.

Một câu hỏi cho mỗi lineage, và **mốc thời gian KHÔNG nằm trong câu hỏi** — nó
là trường `as_of` riêng. Nhờ vậy *cùng một câu hỏi* phục vụ được cả hai nửa của
một cặp tương phản.

### 6.2 Sáu nhóm T1–T6

| Nhóm | Là gì | Đo năng lực gì | Quota |
|---|---|---|---|
| **T1** | tra cứu một phiên bản, không mơ hồ thời gian | đối chứng — ai cũng nên làm được | 251 |
| **T2** | **cặp tương phản**: cùng câu hỏi, hai mốc | phân biệt phiên bản theo `t` | 400 |
| **T3** | chuỗi ≥3 phiên bản A→B→C | lần theo nhiều bước sửa đổi | 199 |
| **T4** | **bẫy trích dẫn**: phiên bản cũ còn trong kho, nội dung gần như trùng | không lấy nhầm phiên bản cũ | 150 |
| **T5** | hiệu lực hồi tố (Điều 152 Luật BHVBQPPL) | ca pháp lý khó | 38 |
| **T6** | **hết hiệu lực một phần** ở cấp Khoản/Điểm | lan truyền hiệu lực (I2) | 112 |

Tổng **1.150** dòng QA cho mỗi chế độ `as_of`.

Ví dụ §2 chính là một dòng **T3** (`num_versions=3`), và nó cũng là bẫy T4 vì
v1/v2 khác nhau một chữ.

### 6.3 Ba chế độ `as_of` — cùng câu hỏi, ba kiểu mốc

| Chế độ | Mốc đặt ở đâu | Dùng để | Số dòng |
|---|---|---|---|
| `giua_khoang` | giữa khoảng hiệu lực | **bảng kết quả chính** | 1.150 |
| `ranh_gioi` | đúng ngày trước mốc chuyển | phép thử biên — khó nhất | 1.150 |
| `sau_het_hieu_luc` | sau khi văn bản hết hiệu lực | phép thử metadata cấp văn bản | 181 |

Tổng **2.481 dòng**, 666 lineage, 517 văn bản. Chia **dev 500 / test 1.981**;
λ, μ và mọi tham số **chỉ được tinh chỉnh trên dev**.

### 6.4 Một dòng gồm gì

40 trường. Những trường quan trọng (lấy từ ví dụ §2):

```
id               vilextime:T3:provision:40778740-…:2022-01-30
group / split    T3 / test        as_of 2022-01-30 (ranh_gioi)
question         "Khi Cục trưởng Cục điều tra chống buôn lậu xử phạt…"
answer           lời văn đầy đủ của phiên bản đúng tại as_of
short_answer     các cụm bắt buộc phải xuất hiện, nối bằng " … "
answerable       True            in_force True
version_id       version:40778740-…:1      ← phiên bản vàng
valid_from/to    [2020-10-15 , 2022-01-31)
target           {law_id, citation "Điểm đ Khoản 4 Điều 84",
                  provision_path "Chương III › Điều 84 › Khoản 4 › Điểm đ", lead_in…}
derivation.transitions  [{on, from_version, to_version, op, actor, event_id, evidence}]
evidence_set     các version lớp B (role: gold | lead_in)
accepted_evidence các đơn vị lớp A được chấp nhận
```

**`answerable=false` (293 dòng)** là phần quan trọng và dễ bị bỏ qua: câu trả
lời đúng là *"không có hiệu lực tại mốc này"*, với **lý do** theo từ vựng đóng:
`not_yet_in_force` · `provision_repealed` · `document_repealed` · `out_of_corpus`.
Chuỗi "KHÔNG CÒN HIỆU LỰC" **không bao giờ xuất hiện trong trường `answer`** —
vì **lý do chính là thứ đang được đo**, không phải một câu chữ.

### 6.5 Phần chưa xong — phải biết rõ

Bộ dữ liệu **đã dựng xong về mặt máy**, nhưng **chưa được người kiểm**:

- `review.status == "unchecked"` trên **cả 2.481 dòng**
- Cohen κ: **0/300** câu kiểm định chéo (`crosscheck_A/B.tsv` còn trống)
- **0/490** audit bắt buộc đã làm
- cột luật sư cho T5: **trống** (`t5_items.tsv`)

**Nghĩa là:** framework chạy được không đồng nghĩa bảng kết quả chính dùng được.
Đây là hai mốc khác nhau. Mốc M3 cần κ ≥ 0,6 trên 300 câu.

---

## 7. Đo bằng gì — và mỗi chỉ số bắt lỗi gì

Scorer: `scripts/eval/score_vilextime.py` (đã xong, P5.4/P5.5 ✅). Một bài nộp
là JSONL, mỗi dòng một câu:

```json
{"id": …, "answer": "…", "answerable": true,
 "citations": ["version:<provision>:<n>", …],
 "retrieved": ["<unit id>", …]}
```

| Chỉ số | Đo gì | Bắt lỗi gì |
|---|---|---|
| **Recall@k** | top-k có chứa *điều khoản* vàng | tìm được đúng chỗ không |
| **TV-Recall@k** | top-k có chứa *phiên bản* có hiệu lực tại `as_of` | tìm đúng chỗ **và** đúng phiên bản |
| **MRR** | nghịch đảo hạng của hit đầu | xếp hạng tốt không |
| **Accuracy** | chứa mọi cụm của `short_answer` **và không** chứa cụm chỉ phiên bản khác có | **tương phản** — đọc hết mọi phiên bản bị tính SAI |
| **EM / F1** | so với `short_answer`, token âm tiết | báo F1; EM gần 0 với câu sinh |
| **TVER** | tỉ lệ câu có **trích dẫn không còn hiệu lực tại `t`** | ảo giác theo thời gian — **chỉ số trung tâm** |
| **VCR** | trích đúng điều khoản nhưng **sai phiên bản** | lấy nhầm phiên bản cũ |
| **TCS** | đúng ở **cả hai** mốc của một cặp T2 | hiểu `t` thật, không đoán may |
| `citation_coverage`, `tver_strict` | có trích dẫn không, phân giải được không | tránh "không trích dẫn" được điểm oan |

**Hai điểm thiết kế quan trọng:**

1. **Accuracy là tương phản.** Một hệ thống "khôn lỏi" đọc ra *mọi* phiên bản để
   chắc chắn trùng đáp án sẽ bị tính **sai**, vì nó chứa cụm chỉ thuộc phiên bản
   khác. Scorer có probe `hedge` để tự kiểm điều này: `hedge` đạt
   Accuracy 0,057 trên T2 (nhưng 1,000 dưới định nghĩa "lỏng" — lý do dùng định
   nghĩa tương phản).

2. **Có trần oracle để tự bắt rò rỉ.** Probe `oracle` được cho sẵn điều khoản
   vàng, chỉ phải chọn phiên bản: F1 ≈ 0,589, TV-Recall@1 = 1,0. **Hệ nào vượt
   oracle là có rò rỉ gold**, không phải giỏi. Chạy:
   `python scripts/eval/score_vilextime.py --probes`

   Probe `nearest` ("chọn phiên bản có `start` gần `as_of` nhất", không logic
   thời gian nào) đã đạt **0,772 trên T2 / 0,713 trên T3**. Đây là trần dưới
   thật: mọi kết luận phải so với nó, không so với 0.

**Khoảng tin cậy: bootstrap theo lineage, không theo dòng.** Vì 2.481 dòng chỉ
đến từ 666 lineage, bootstrap theo dòng sẽ phóng đại độ chắc chắn.

---

## 8. So với cái gì — và luận điểm thật của khóa luận

### 8.1 Phát hiện ngày 01/10: đồ thị thắng ở đâu

Trước khi viết code, đã đo bề mặt thực tế của từng cơ chế trên chính bộ dữ liệu:

| Cơ chế | Bề mặt đo được |
|---|---|
| Lọc theo phiên bản | ~1.043 dòng — **nhưng đây là năng lực của B7+** |
| Lan truyền, vế đệ quy của (3) → H3 | **24 dòng** trên bảng chính |
| Bao đóng bắc cầu của (2) | **4 dòng** (970/974 văn bản tác động vẫn còn hiệu lực tại `as_of`) |
| Ngữ cảnh cấu trúc biến thiên theo `t` | **0,53%** nút mang ngữ cảnh có >1 phiên bản |
| Ngữ cảnh cấu trúc làm tín hiệu recall | mọi dòng, +0,185 độ phủ — **nhưng không độc quyền của đồ thị** |

**Kết luận (quyết định M4, chốt 01/10):** trên ViLexTime, **tính đúng theo thời
gian do *biểu diễn* quyết định, không do kiến trúc duyệt đồ thị lúc truy vấn.**

Luận điểm của khóa luận do đó là:

> **B7+ không phải "đường cơ sở không dùng đồ thị". Nó CHÍNH LÀ hệ đề xuất khi
> tháo phần đồ thị online — và nó chỉ tồn tại được vì L2 (trích xuất thao tác)
> và L3 (lan truyền hiệu lực) đã dựng ra biểu diễn cấp phiên bản ở tầng offline.
> Giá trị của đồ thị nằm ở việc KIẾN TẠO 𝒰ₜ, không nằm ở việc DUYỆT nó.**

Đối chứng chính do đó là **B7** (chỉ lọc ngày cấp văn bản), nơi khoảng cách lớn
và đã đo được: 42,3% dòng bảng chính là bẫy B7, và **482/485** trong số đó có
lệnh sửa đổi *vẫn còn hiệu lực ở cấp văn bản* — nên không bộ lọc cấp văn bản nào
bắt được.

### 8.2 Bảng kết quả chính: thang đủ của biểu diễn

Mệnh đề 1 biến thành **bốn điểm đo** trên **cùng một** retriever, cùng
generator, cùng prompt, cùng `k` — **chỉ đổi `ρ`**:

| Tier | `ρ(u)` = | Thêm gì | Là hệ nào |
|---|---|---|---|
| 1 `none` | nội dung chữ | — | B2/B3/B4 |
| 2 `document` | + ngày hiệu lực **văn bản** | metadata | **B7** |
| 3 `version` | + khoảng **cục bộ** của phiên bản | **I1** | **B7+** |
| 4 `propagated` | + khoảng của **mọi tổ tiên**, công thức (3) | **I2** | **hệ đề xuất** |

Đã kiểm trên corpus thật: `𝒰ₜ(propagated) ⊆ 𝒰ₜ(version) ⊆ 𝒰ₜ(document)`.
Tại `as_of = 2024-05-01`, trên 1.474.324 đơn vị lớp B:

```
none 1.474.324  →  document 673.017  →  version 656.621  →  propagated 650.119
```

Đây là bảng chính của paper: **một cái thang đo được**, không phải một lập luận.

### 8.3 Mười bốn hệ thống, mỗi hệ một dòng cấu hình

`src/vilexgraph/framework/systems.py`. Một baseline **không phải** một cài đặt
riêng — nó là hệ đề xuất bị tắt một công tắc. Nhờ vậy không ai phản biện được
"baseline của bạn bị làm yếu".

| Hệ | layer | lex | dense | rerank | `temporal` | ctx | expand | verify |
|---|---|---|---|---|---|---|---|---|
| B1 LLM thuần | — | · | · | · | none | · | · | off |
| B2 BM25 | A | ✓ | · | · | none | · | · | off |
| B2+ctx | A | ✓ | · | · | none | ✓ | · | off |
| B3 Dense | A | · | ✓ | · | none | ✓ | · | off |
| B4 Hybrid+rerank | A | ✓ | ✓ | ✓ | none | ✓ | · | off |
| B5 GraphRAG phi thời gian | A | ✓ | ✓ | · | none | ✓ | 1 (𝓔_rel) | off |
| B6 KG phân cấp | A | ✓ | ✓ | · | none | ✓ | 1 (𝓔_part) | off |
| **B7** đối chứng chính | A | ✓ | ✓ | ✓ | **document** | ✓ | · | off |
| **B7+** | B | ✓ | ✓ | ✓ | **version** | ✓ | · | off |
| **Đề xuất** | B | ✓ | ✓ | ✓ | **propagated** | ✓ | 1 | reject |
| A1 bỏ ràng buộc thời gian | B | ✓ | ✓ | ✓ | *none* | ✓ | 1 | reject |
| A2 bỏ mở rộng đồ thị | B | ✓ | ✓ | ✓ | propagated | ✓ | *0* | reject |
| A3 bỏ Verifier | B | ✓ | ✓ | ✓ | propagated | ✓ | 1 | *off* |
| A4 bỏ lan truyền | B | ✓ | ✓ | ✓ | *version* | ✓ | 1 | reject |

**B2 có mặt hai lần (có/không ngữ cảnh) là cố ý.** Header cấu trúc nâng độ phủ
token từ 0,555 lên 0,740, nhưng đó là **mẹo chunk-header phổ thông**, không phải
đóng góp của đồ thị. Cho mọi baseline dùng nó và **báo rõ độ lợi** — nếu chỉ cho
hệ đề xuất dùng thì đó là thắng gian.

**A4 = bỏ lan truyền** chính là biến thể "bỏ vế đệ quy của (3)" mà H3 cần.
(A4 trong đề cương chỉ là *proxy*.)

---

## 9. Đang ở đâu — chín giai đoạn

Timeline theo đề cương: **01/09/2026 → 01/02/2027**. Hôm nay **01/10/2026**.

| GĐ | Thời gian | Nội dung | Trạng thái |
|---|---|---|---|
| 1 | 01–14/09 | Hoàn thiện đề cương | 🟡 2/6 — **quá hạn**, còn P1.2 (sửa mâu thuẫn), P1.5 (chốt H1–H4) |
| 2 | 15/09–05/10 | Thu thập & xử lý dữ liệu | ✅ **12/12, M1 đạt sớm 17/09** |
| 3 | 06/10–26/10 | Đồ thị tri thức L0–L3 | 🟡 13/19 — **đường găng**, M2 chưa đạt |
| 4 | 27/10–16/11 | Bộ dữ liệu ViLexTime | 🟡 release 2.481 dòng đã dựng, **chưa gán nhãn người** |
| 5 | 17/11–30/11 | Cài đặt & đánh giá đường cơ sở | 🟡 **bắt đầu sớm 01/10** — P1/P2 framework xong |
| 6 | 01/12–21/12 | Hệ đề xuất L4–L5 | ⬜ |
| 7 | 22/12–04/01 | Thực nghiệm & phân tích | ⬜ |
| 8 | 05/01–11/01 | Viết bài báo | ⬜ |
| 9 | 12/01–01/02 | Hoàn thiện khóa luận | ⬜ |

### Tám mốc phải chứng minh được

| Mốc | Hạn | Phải chứng minh | Trạng thái |
|---|---|---|---|
| M1 | 05/10 | Snapshot v2 đóng băng, tải về kiểm được | ✅ 17/09 |
| M2 | 26/10 | `snapshot(u,t)` đúng trên **100 truy vấn kiểm tay** | ⬜ — E1 mới đạt 80,02% tự động, chưa có 100 đáp án tay |
| M3 | 16/11 | ViLexTime 1.150 câu + **Cohen κ ≥ 0,6** trên 300 câu | ⬜ — κ chưa đo |
| M4 | 30/11 | **Điểm quyết định B7** | ✅ **chốt sớm 01/10** (xem §8.1) |
| M5 | 21/12 | End-to-end trả lời `(x,t)` kèm trích dẫn qua Verifier | ⬜ |
| M6 | 04/01 | Đủ kết quả A1–A7, phân rã theo T1–T6 | ⬜ |
| M7 | 11/01 | Nộp bài báo | ⬜ |
| M8 | 01/02 | Nộp khóa luận + demo | ⬜ |

### Đã xây được gì trong framework (01/10)

| Thành phần | Trạng thái |
|---|---|
| `rag/corpus.py` + `index_corpus.py` | ✅ index 2.978.024 đơn vị, 3,7 GB, đếm khớp manifest |
| `rag/temporal.py` — bốn tier | ✅ đã chứng minh lồng nhau trên corpus thật |
| `rag/systems.py` — 14 hệ | ✅ cấu hình sai bị từ chối ngay lúc tạo |
| `rag/generate.py` — prompt + bóc trích dẫn | ✅ |
| `rag/retrieve.py` — BM25 + cache | ✅ |
| `run_vilextime.py` — runner | ✅ **B1 đã chạy thật end-to-end** |
| Test | ✅ 429 test pass, 60 test mới |
| L5 Verifier · dense/Milvus · 𝓔_rel expansion · LLM-judge | ⬜ |

---

## 10. Những quyết định đã chốt, và vì sao

| ADR | Quyết định | Lý do cốt lõi |
|---|---|---|
| **0001** | Neo4j + Milvus là **kho dẫn xuất**; `data/` là nguồn sự thật duy nhất | xóa đi dựng lại được; không có trạng thái nào chỉ tồn tại trong DB |
| **0001 §3** | **Phương án A**: tính trước khoảng hiệu lực offline, online chỉ lọc | phương án "lọc thô rồi tinh" bị loại vì *có thể thiếu ứng viên*; phương án "Neo4j trả 𝒰ₜ trước" bị loại vì 𝒰ₜ có hàng trăm nghìn id |
| **0002** | Chỉ QPPL trung ương được truy xuất; **VBHN chỉ để kiểm chứng** | dùng VBHN làm nguồn truy xuất là gian lận — nó đã làm sẵn việc của L2–L3 |
| **0002** | Mọi giá trị suy dẫn nằm **ngoài** dữ liệu nguồn, kèm phương pháp và trạng thái duyệt | kết quả chính chỉ dùng `observed` và `derived_verified` |
| **0003** | Sáu nhóm T1–T6, **`group` là cột phân tầng** không phải biến thể schema | một schema cho mọi nhóm |
| **0003 §3** | Tách *trạng thái pháp lý* khỏi *nội dung đáp án*; `no_answer_reason` từ vựng đóng | **lý do chính là thứ đang được đo** |
| **0003 §7** | File là authority, trường `split` chỉ là tiện lợi; chỉ `test` được chấm mặc định | "một cờ mà scorer được tin là sẽ tôn trọng thì một phần người dùng sẽ bỏ qua" |
| **0003 §10** | **Code tìm khác biệt, LLM chỉ diễn đạt**; mốc thời gian không nằm trong câu hỏi | nhãn vàng không phụ thuộc LLM; một câu hỏi phục vụ cả cặp tương phản |
| **0004** | BM25 bằng **SQLite FTS5**; generator đa provider qua `.env`; cột chính **không dùng model họ Claude** | Milvus 2.4.15 không có BM25 native; câu hỏi do `claude-opus-5-5` viết nên dùng Claude để trả lời là xung đột lợi ích |

**Mười hai nguyên tắc miền (D1–D12)** trong master plan §11 — quan trọng nhất:

- **D1** khoảng hiệu lực luôn nửa mở `[start, end)`
- **D2** tách *danh tính* `Provision` khỏi *nội dung* `ProvisionVersion`
- **D3** lõi logic thời gian **không phụ thuộc DB** (chỉ stdlib)
- **D4** event thiếu ngày hoặc thiếu target duy nhất **không được áp**
- **D6** bãi bỏ nút cha **không** đóng phiên bản của cây con; hiệu lực con tính động
- **D8** tham chiếu mơ hồ **chỉ giữ candidate**, không chọn tạm
- **D10** resolver chỉ nhận **đúng một** kết quả khớp cấu trúc, **không fuzzy**
- **D12** nút không có phiên bản (Chương/Mục, hoặc Điều thiếu text) là **trong suốt** khi lan truyền

Tinh thần chung: **"không coi 'thiếu dữ liệu' là 'dữ liệu nói khác'"**.

---

## 11. Rủi ro đã biết và chưa giải — đọc kỹ phần này

| # | Rủi ro | Mức độ | Hiện trạng |
|---|---|---|---|
| 1 | **Vòng tuần hoàn gold (JUDGE N1)** | **nghiêm trọng** | Gold lớp B sinh từ chính chuỗi L2–L3 mà hệ đề xuất dùng → **lỗi của KG vô hình trên benchmark này**. Với L2 recall 62,2%, đây là đe dọa cấu trúc với RQ2/RQ3. Giải pháp đã chốt *về nguyên tắc*: tập gold độc lập ~120 dòng (J7) + **hai cột kết quả "gold theo KG" / "gold độc lập"**. **Chưa dựng.** |
| 2 | **Gold chưa được người kiểm** | **nghiêm trọng** | κ 0/300, 490 audit chưa làm, cột luật sư T5 trống. Chặn M3. |
| 3 | **H3 không đủ lực thống kê** | cao | 24 dòng / 24 lineage. Bootstrap theo lineage trên 24 lineage là vô nghĩa. **Phải báo số và nói thẳng**, không chạy phép thử yếu rồi diễn giải. |
| 4 | L2 recall 62,2% | cao | ~38% thao tác chưa bắt được → một số chuỗi phiên bản thiếu mắt |
| 5 | M2 chưa đạt | cao | E1 mới 80,02% khớp tự động trên 51/356 VBHN; chưa có 100 đáp án kiểm tay (E2–E3) |
| 6 | Phủ hiện tượng lệch | trung bình | mọi transition là `amend`/`repeal`; **không có dòng `supplement`/`replace`**; T5 chỉ từ 3 văn bản tác động → "kết luận T5 và H3 chỉ ở mức minh họa" |
| 7 | RAM 7 GB < Neo4j 4g + Milvus 4g | trung bình | hoãn được: L4 tính offline nên P1–P3 không cần Docker |
| 8 | Hạ tầng đã mất | thấp | volume Docker không còn; graph phải nạp lại (~10 phút) |
| 9 | Đề cương còn mâu thuẫn | thấp | bản UIT đã nộp không sửa được → công bố chỗ lệch theo `vilextime-datasheet.md` |

---

## 12. Việc tiếp theo, theo thứ tự

**Không cần Docker cho ba việc đầu** — L4 chạy offline từ corpus + SQLite.

1. **Chạy thang truy xuất trên dev** (`--retrieval-only`, **0 lệnh gọi LLM**)
   → bốn tier × T1–T6. Đây là **kết quả khoa học đầu tiên** của khóa luận.
2. **Sinh lại `probes.json`** (bản hiện tại cũ: viết 28/09, release rebuild
   29/09) → có trần oracle để bắt rò rỉ.
3. **Chạy nửa sinh câu trả lời trên dev** → Accuracy, F1, TVER, VCR, TCS.
4. **P3**: Verifier + abstention có nêu nguyên nhân → RQ3. *Cần chốt ADR 0004 §5.*
5. **P4**: embedding → B3/B4. *Cần chốt ADR 0004 §4.*
6. **P5**: 𝓔_rel expansion, B5/B6, A1–A7, LLM-judge. *Cần Neo4j.*

**Song song, việc người phải làm (không ai làm thay được):**

- **Kiểm định chéo 300 câu để có Cohen κ** — chặn M3, chặn mọi kết quả chính.
- **Cố vấn luật cho T5** (34 dòng trong `data/review/t5_items.tsv`).
- **Chốt H1–H4** (P1.5) — `graph_justification.md` §7 ghi rõ H1–H4 **không có
  trong đề cương** và cần nhóm thống nhất **trước khi** chạy thực nghiệm.
- **Dựng tập gold độc lập J7** (~120 dòng) — đây là thứ duy nhất phá được vòng
  tuần hoàn ở rủi ro #1.

---

## Tự kiểm tra lại mọi con số trong tài liệu này

```bash
# ví dụ §2: ba phiên bản của cùng một điều khoản
grep provision:40778740-2c7f-11f1-abee-c9b7a53cf5c7 data/derived/versions.jsonl

# đếm của index truy xuất
python scripts/eval/index_corpus.py --counts

# bộ dữ liệu: phân bố nhóm, chế độ as_of, split
python -c "
import json,collections
r=[json.loads(l) for l in open('data/derived/vilextime/release.jsonl',encoding='utf-8')]
print(len(r),'dòng')
for k in ('group','as_of_strategy','split','answerable','no_answer_reason'):
    print(k, dict(collections.Counter(x.get(k) for x in r)))"

# trần oracle và các probe kiểm scorer
python scripts/eval/score_vilextime.py --probes

# toàn bộ test
python3 -m pytest

# tính nhất quán của corpus (không chạm data/)
python3 scripts/check/verify_pipeline.py
```

## Đọc tiếp

| Muốn hiểu | Đọc |
|---|---|
| Lập luận chọn biểu diễn, công thức, H1–H4 | `docs/graph_justification.md` |
| Tiến độ chính thức, D1–D12, rủi ro | `docs/plans/active/master-plan.md` |
| Bộ dữ liệu: schema, cách báo kết quả, chỗ lệch đề cương | `docs/vilextime-datasheet.md` |
| Phê bình độc lập về bộ dữ liệu | `docs/reports/JUDGE_DATASET.md` |
| Cách crawl, 13 loại quan hệ | `docs/crawling-plan.md` |
| Framework truy xuất/sinh đang làm | `docs/plans/active/phase-5-6-framework.md` |
| Các quyết định | `docs/decisions/` |
