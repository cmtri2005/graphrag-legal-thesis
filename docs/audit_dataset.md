# Audit dataset — hiện trạng corpus

**Ngày audit:** 2026-09-12 · **Mốc dữ liệu (as of):** 2026-09-12 (1 delta run đã ghi vào `data/delta_runs.jsonl`)

Tái lập toàn bộ số liệu dưới đây:

```bash
python scripts/check/data_status.py      # tồn kho, khoảng trống, temporal coherence
python scripts/check/verify_pipeline.py  # gate nhất quán, exit != 0 khi hỏng
python scripts/pipeline/resolve_expiry_targets.py --unresolved
```

---

## 1. Quy mô

- **22,550** văn bản · **128,289** cạnh phân biệt · **1,136,483** node có text (trên 1.26M node cấu trúc)
- `edges.jsonl` có 157,795 dòng nhưng 29,506 dòng là bản lặp của cùng (nguồn, đích, loại quan hệ) — chỉ ở nhóm phả hệ, có cạnh lặp tới 206 lần; các dòng lặp chỉ khác `id` của chính dòng reference (`referenceProvisions` rỗng ở toàn bộ 158,115 reference), nên không mang thêm thông tin. Mọi thống kê cạnh phải khử trùng lặp
- 2.7 GB trên đĩa (nén còn ~830 MB)
- 4 miền: `dat_dai`, `thue`, `doanh_nghiep_dau_tu`, `giao_thong`

## 2. Độ phủ theo tầng

| Tầng | Số file | So với `raw` |
|---|---|---|
| `raw` | 22,550 | 100% |
| `trees` | 22,532 | 99.9% |
| `history` | 22,548 | 100% |
| `diagrams` | 21,533 | 95.5% |
| `provisions` | 19,279 | 85.5% |

- Text phủ **98.97%** số node khớp được; 90.0% nếu tính cả hàng đợi review
- Khoảng trống `provisions` (3,271): 3,236 văn bản không có cấu trúc điều khoản + 17 không có body text + 0 chưa giải thích được

## 3. Trạng thái hiệu lực

| Trạng thái | Số văn bản |
|---|---|
| Hết hiệu lực toàn bộ | 12,206 |
| Còn hiệu lực | 7,745 |
| **Hết hiệu lực một phần** | **2,051** |
| Không có `effStatus` | 467 |
| Ngưng hiệu lực / Chưa có hiệu lực / Không còn phù hợp | 81 |

## 4. Lỗ hổng thời gian — 4.4% không gian truy xuất mất neo

**49,818 / 1,136,483 node** thuộc **1,819 văn bản** không định vị được trên trục thời gian:

| Nguyên nhân | Node | Khả năng cứu |
|---|---|---|
| Thiếu `effFrom` | 29,410 | 690/724 văn bản có `issueDate` làm cận dưới; 84% không có cạnh vào |
| Chết toàn bộ nhưng không có `effTo` | 14,700 | 48% suy được từ 1 VB tác động; **23% không cứu được** |
| Thiếu `effStatus` | 5,244 | — |
| `effTo` sớm hơn `effFrom` | 451 | lỗi nhập liệu của cổng; `effTo` không dùng được |
| "Còn hiệu lực" mà `effTo` đã qua | 13 | — |

## 5. `expiryProvisions` — ground truth cấp khoản

- **46,379** dòng trong `data/expiry_targets.jsonl`: 23,532 toàn bộ văn bản + **31,175 cấp Điều/Khoản/Điểm**
- Map được về node id trong cây: **22,847 (73.3%)**; theo cặp (văn bản, điều khoản) không trùng: 5,956/8,412 (70.8%)
- Không map được (24.7%): **cây của cổng dừng ở cấp Điều**, không khai báo Khoản/Điểm mà chuỗi expiry nhắc tới — giới hạn dữ liệu nguồn, không phải lỗi parser
- 274 trường hợp khớp nhiều node: chuỗi thiếu cấp (`"Khoản 2, Chương II"` không nói Điều nào) hoặc cây có node trùng tên

### Phát hiện quyết định: metadata cho biết **cái gì**, không cho biết **khi nào**

- `history[]` chỉ có 6 trường, **không trường nào là ngày hiệu lực pháp lý**. `createdDate` là dấu thời gian nhập liệu của cổng (NĐ 100/2019 hiệu lực 2020, lịch sử đề ngày 2026, tạo bởi `Admin`/`System Scheduler`)
- `sourceDocumentName` trỏ về chính văn bản đó, không phải văn bản đã sửa nó
- Muốn có `eff_to` phải nối 3 nguồn: `expiryProvisions` (khoản nào) + cạnh genealogy (ai sửa) + `effFrom` của văn bản sửa (khi nào)

| Văn bản có expiry cấp Điều/Khoản | Số | Tỉ lệ |
|---|---|---|
| Chỉ 1 văn bản tác động → quy được thời điểm | 228 | **19.3%** |
| ≥2 văn bản tác động → không biết cái nào bãi bỏ khoản nào | 940 | **79.7%** |
| Không có cạnh vào | 11 | 0.9% |

Đuôi phân bố rất nặng: cá biệt có văn bản bị **216** văn bản khác tác động.

**Gold set miễn phí:** từ 228 văn bản có phép nối xác định, rút ra **843 bộ ba (văn bản, node, ngày)** — đúng dạng đầu ra L2 phải sinh, 100% gán được ngày, mỗi mẫu trỏ tới node id kiểm toán được.

## 6. Khiếm khuyết còn tồn

- **778** văn bản coverage < 50%: 123,415 node khai báo, chỉ 9,561 có text (phần lớn là cây không đánh số)
- **17** văn bản có cây nhưng API trả `documentContent.content` rỗng — gồm 2 Luật (`105/2025/QH15`, `141/2025/QH15`). Đã ghi danh trong `data/fetch_failures.txt` stage `text`
- **19** văn bản có `references[]` hợp lệ nhưng không sinh cạnh nào — không phải seed cũng không phải reverse_seed, nên chưa bao giờ là gốc của lượt duyệt
- `diagrams` thiếu **1,017** (corpus lớn thêm sau lần `expand_reverse` cuối)
- **549** file history rỗng

## 7. Bug đã phát hiện và vá

Cả ba thuộc loại *hỏng mà không báo*:

1. **`delta_seeds.json` sai định dạng so với bộ đọc** — `build_graph.py` làm `set(read_json(path))` trên dict → nạp *tên domain* làm doc id; 23 văn bản mới của delta run không được fetch
2. **Quy trình delta tự truncate `edges.jsonl`** — hướng dẫn in ra bảo chạy `build_graph` hai lần với hai file seed khác nhau; lần hai ghi đè bằng phạm vi hẹp hơn (148,505 → 90,931 cạnh)
3. **`expand_reverse.py` ghi đè `reverse_seeds.json`** thay vì cộng dồn — mất 2,335 id, đồ thị tụt còn 17,439 văn bản

Gate mới trong `verify_pipeline.py`, cả hai đã kiểm chứng bắt đúng lỗi thật:
- `every tree without provision text is accounted for`
- `edges.jsonl covers every referencing document` (đo trên văn bản thật sự có references, vì ~6% corpus vốn không có cạnh nào)

## 8. Quyết định thiết kế: không xoá văn bản bất thường

Xoá 1,819 văn bản bất thường sẽ làm đứt **4,646 / 42,303 cạnh phả hệ phân biệt (11.0%)**. Nghiêm trọng hơn, các văn bản bất thường nhất chính là **văn bản bãi bỏ**:

```
148 cạnh | thiếu effFrom    | 151/2020/NĐ-CP  Về việc bãi bỏ một số văn bản...
113 cạnh | thiếu effStatus  | 763/QĐ-UBND     Bãi bỏ các Quyết định...
 72 cạnh | effTo<effFrom    | 25/2012/TT-NHNN Về việc bãi bỏ một số văn bản...
```

Xoá `151/2020/NĐ-CP` là xoá 148 phép bãi bỏ → 148 văn bản sẽ trông như vẫn còn hiệu lực. Đó đúng là *temporal hallucination* mà đề tài sinh ra để chống.

**Cách làm thay thế** — tách ba khái niệm đang bị gộp:

| Tầng | Với 1,819 văn bản này |
|---|---|
| Corpus (giữ gì trên đĩa) | giữ **tất cả** |
| Đủ điều kiện truy xuất | **không** trả về cho câu hỏi có mốc `t`; đếm số lần bị chặn |
| Đủ điều kiện làm benchmark | **không** dùng sinh câu hỏi ViLexTime |

Thực hiện bằng cờ dẫn xuất `temporal_anchor` + skip-list ở tầng đọc, theo đúng pattern Stage 4 đã dùng cho `excluded_ids.txt`. Không xoá file: dữ liệu không tái tạo được (vbpl.vn thay đổi liên tục — 123 văn bản đổi nội dung, 23 văn bản mới chỉ trong 8 ngày).

## 9. Việc cần làm với đề cương

1. **L2 là bắt buộc, không phải tuỳ chọn** — với 79.7% mơ hồ, trích xuất từ văn bản là thứ duy nhất quy được phép bãi bỏ về đúng văn bản sửa đổi và đúng ngày. Sửa câu *"khai thác siêu dữ liệu công khai... giảm đáng kể chi phí gán nhãn"*: metadata miễn phí phần **định vị**, không miễn phí phần **định thời**
2. **Thay 200 mẫu thủ công bằng 843 mẫu miễn phí**, giữ 200 mẫu làm tập kiểm tra chéo độc lập
3. **Tuyên bố giới hạn bằng số thật** ở mục "Khó khăn và thử thách": 4.4% không gian truy xuất không neo được thời gian; 23% văn bản đã chết không xác định được thời điểm chết
4. **Ghi rõ quy tắc dùng `issueDate` làm cận dưới** cho 690/724 văn bản thiếu `effFrom` — ảnh hưởng trực tiếp tới `valid(u,t)`
5. **Lệch phạm vi**: đề cương ghi 120–170 văn bản / 2 miền, corpus có 22,550 / 4 miền; miền Bảo hiểm xã hội của Giai đoạn 7 **chưa có dữ liệu** (chỉ 145 văn bản lọt vào qua BFS, không phải seed domain)

## 10. Rủi ro lưu trữ

- Toàn bộ phần nặng của `data/` đang bị gitignore; chỉ `seeds.json` và `reverse_seeds.json` được git giữ
- Corpus **không tái tạo được** — bản crawl 12/09/2026 không thể dựng lại vào 01/2027
- Chưa có bản sao ngoài máy này
