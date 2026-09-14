# 0002 Phạm vi neo thời gian, vai trò VBHN và dữ liệu dẫn xuất

Date: 2026-09-14

## Status

Accepted

## Context

`docs/audit_dataset.md` §4 tính 1.819 văn bản "mất neo thời gian". Kiểm tra lại
ngày 14/09/2026 cho thấy khoảng 833 trong số đó là loại văn bản vốn không có
hiệu lực riêng: 359 Công văn và 113 Văn bản hợp nhất (VBHN) thiếu `effFrom`,
361 VBHN thiếu `effStatus`. Nếu điền khuyết cho nhóm này, hệ thống sẽ bịa ra
hiệu lực pháp lý không tồn tại.

Cùng ngày còn xác nhận thêm ba điều:

- **Cây nguồn dừng ở cấp Điều.** 7.620 chuỗi `expiryProvisions` không định vị
  được. Trong đó 6.815 chuỗi (89,4%) tìm được marker Khoản/Điểm tương ứng trong
  HTML của Điều.
- **Ngày trong history bị lệch có quy luật.** Dòng `DATE_*` do `Job` ghi với giờ
  `T00:00` lớn hơn ngày pháp lý đúng 1 ngày (13.424 dòng). Dòng có giờ `T07:00`
  thì trùng ngày. Căn cứ: NĐ 100/2019 và NĐ 168/2024 có `effFrom` đúng ngày hiệu
  lực; khi lệch 1 ngày, `effFrom` rơi vào ngày 1 của tháng ở 21% trường hợp,
  còn `DATE_HL` chỉ 3%.
- **`raw` không lỗi múi giờ.** Giá trị `T17:00` có tỷ lệ rơi vào ngày 1 là 18%,
  xấp xỉ mức nền 19%.

## Decision

1. **Truy xuất theo mốc t và benchmark ViLexTime chỉ dùng văn bản quy phạm pháp
   luật (QPPL) cấp trung ương.** Danh sách loại văn bản được chốt ở bước T2.1
   của plan backfill. Công văn, VBHN, bản dịch và văn bản hành chính nằm ngoài
   phạm vi point-in-time. Chúng vẫn được giữ trên đĩa và vẫn là mắt xích phả hệ.
2. **VBHN không được truy xuất trực tiếp.** VBHN là nguồn **kiểm chứng L3**: text
   hợp nhất tại một ngày dùng để đối chiếu với `snapshot(u, t)`. Việc đối chiếu
   luôn kèm cảnh báo về rủi ro hợp nhất tự động.
3. **Khoản/Điểm được tách tất định từ HTML của Điều** khi cây nguồn không khai
   báo. Kết quả nằm trong file dẫn xuất riêng, không ghi đè `data/trees/`, và
   chỉ được dùng sau khi đo độ chính xác trên mẫu kiểm tay.
4. **Mọi giá trị suy dẫn nằm ngoài dữ liệu nguồn.** `data/raw`, `data/history`,
   `data/trees`, `data/diagrams` luôn là response gốc. Giá trị dẫn xuất mang
   phương pháp, bằng chứng, confidence và trạng thái review. Kết quả chính của
   khóa luận chỉ dùng dữ liệu `observed` và `derived_verified`.
5. **Ngày trong history chỉ là bằng chứng chéo**, sau khi áp quy tắc chuẩn hóa
   ở mục Context. Không bao giờ chép đè `effFrom` hoặc `effTo`.
6. **Corpus được backfill rồi đóng băng thành snapshot v2** trước mốc M1
   (05/10/2026). Mọi thí nghiệm dùng v2; mỗi văn bản giữ `last_crawled_at`.

### Quy tắc phân loại (chốt ở T2.1, 15/09/2026)

Cài đặt tại `src/legal_crawler/vocab/scope.py`. Thứ tự xét:

1. **Bản dịch** (`isTranslationDoc` hoặc loại "Bản dịch văn bản") → ngoài phạm vi.
2. **VBHN** (`docType.parentCode = VBHN`) → ngoài phạm vi, chỉ dùng kiểm chứng L3.
3. **Không phải QPPL**: `parentCode ≠ VBQPPL` và không thuộc 4 loại quy phạm
   lịch sử (Hiến pháp, Sắc lệnh, Sắc luật, Thông tư liên bộ) → ngoài phạm vi.
   Gồm Công văn, Chương trình, Thông báo, văn bản hành chính, văn bản hệ
   thống hóa.
4. **Địa phương**: tên cơ quan ban hành bắt đầu bằng UBND/HĐND, hoặc (khi không
   có tên cơ quan) số hiệu chứa HĐND/UBND → ngoài phạm vi. **Không dùng
   `organization.orgType`**: 26 văn bản của Chính phủ, Thủ tướng, Quốc hội
   mang giá trị "địa phương".
5. Còn lại là **QPPL trung ương** → trong phạm vi.

Kết quả trên v1: 20.318 QPPL · 1.243 địa phương · 481 VBHN · 394 không phải QPPL
· 114 bản dịch. "Quyết định" không được tách thêm: metadata không phân biệt
quyết định cá biệt với quyết định quy phạm.

Văn bản trong phạm vi nhưng **body rỗng** chỉ vào hàng đợi điền tay khi còn
hiệu lực hoặc hết hiệu lực một phần, hoặc khi đã hết hiệu lực toàn bộ nhưng vừa
là seed vừa nằm trên chuỗi phả hệ. Các văn bản body rỗng còn lại bị loại khỏi
truy xuất và benchmark (quyết định 15/09/2026).

## Alternatives Considered

1. Điền khuyết cho mọi loại văn bản. Bị loại vì tạo ra hiệu lực không có thật.
2. Loại hẳn VBHN. Bị loại vì bỏ phí nguồn text phiên bản do chính cơ quan nhà
   nước công bố.
3. Chấp nhận 24,7% expiry không định vị được là giới hạn. Bị loại vì đo được
   89,4% trong số đó có marker tách được.
4. Giữ bản crawl 12/09 và không backfill. Bị loại vì 1.017 diagram thiếu làm hở
   chiều tác động vào.

## Consequences

Positive:

- Số "lỗ hổng thời gian" phản ánh đúng thiếu hụt thật, tập trung vào 685 văn
  bản hết hiệu lực toàn bộ nhưng thiếu `effTo`.
- L2 có thể định vị target ở cấp Khoản/Điểm cho phần lớn chuỗi expiry.

Tradeoffs:

- "Quyết định" gồm cả QPPL lẫn văn bản cá biệt; một danh sách loại văn bản
  không phân biệt được hai nhóm này.
- Văn bản sửa đổi chứa đoạn trích dẫn text mới có đánh số "1.", "a)". Tách
  Khoản/Điểm trong vùng trích dẫn sẽ gán nhầm cấu trúc.
- Backfill thay đổi corpus, nên số liệu trong `docs/audit_dataset.md` phải được
  đo lại trên v2.

## Follow-Up

- `docs/plans/active/backfill-corpus-v2.md`.
