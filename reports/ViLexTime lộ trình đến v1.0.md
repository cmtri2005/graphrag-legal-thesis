# ViLexTime: bức tranh toàn cảnh đến khi hoàn chỉnh

Soạn 05/10/2026. Mốc lấy từ `docs/plans/active/master-plan.md`. Số liệu "đã kiểm" là số mình
đo hoặc đọc từ file trong repo trong các phiên làm việc gần đây. Số "ước" là ước lượng, chưa
đo, và được ghi rõ.

---

## 0. Đã xác nhận: người gán A là người thật (05/10)

Bộ nhớ dự án từng ghi (02/10) rằng A có thể là hội đồng LLM. Người dùng xác nhận ngày 05/10 rằng
nhãn trong `crosscheck_A.tsv` do **người thật** gán. Vậy κ(A, B) là đồng thuận giữa người với
người và được báo là IAA.

Việc còn lại: ghi vào biên bản D5 tên hai người gán, và 13/300 dòng không mù (8 dòng
`human:excel`, 5 dòng `claude-opus-5-5`).

Chênh lệch giữa hai người đáng chú ý, và nó là **chênh lệch hiệu chỉnh giữa hai người**, không
phải bằng chứng về model: A gắn cờ 16% dòng và ghi chú 4 dòng, B gắn cờ 34% và ghi chú 97 dòng.
Đúng loại khoảng cách mà cổng hiệu chỉnh trước khi gán sản xuất (mục W4, G2) nhằm thu hẹp.

---

## 1. "Hoàn chỉnh 100%" nghĩa là gì

Không có một định nghĩa duy nhất. Có ba cấp, mỗi cấp bao cấp trước.

| Cấp | Dùng cho | Điều kiện |
|---|---|---|
| **1. Đủ mốc M3** (16/11) | Khóa luận | Đủ 1.150 câu (theo định nghĩa "câu" đã chốt với khoa); κ ≥ 0,6 trên 300 câu; khai đủ chỗ lệch đề cương |
| **2. v1.0 đóng băng** | Khóa luận và phát hành | Mọi mục "chưa xong" của datasheet §7: audit 490 nhãn bắt buộc; luật sư chốt T5; phân xử các dòng bất đồng; gold độc lập; split; manifest sha256; datasheet đầy đủ; giấy phép; tag `vilextime-v1.0` |
| **3. Đủ chuẩn công bố** | Bài báo (ARR 01/2027) | Overlap ≥300 dòng (mục tiêu 600) do **hai người thật** gán, nhãn thô phát hành; Croissant và RAI; mục kiểm tra nhiễm dữ liệu; mục Ethics; canary GUID; kết quả có khoảng tin cậy; bảng lý do loại và tỷ lệ người sửa |

Cấp 1 và 2 bắt buộc cho khóa luận. Cấp 3 chỉ cần nếu nộp bài báo. Hiện tại bộ dữ liệu **chưa
đạt cấp nào hoàn toàn**.

---

## 2. Hiện trạng đã kiểm (05/10)

| Hạng mục | Trạng thái | Bằng chứng |
|---|---|---|
| Pool ứng viên | ✅ | 11.507 lineage; 6 file nhóm 20.922 dòng; T6 lan truyền 264 → 2.000; dòng hỏi sau ngày chụp 40 → 0 |
| Mã và test | ✅ | 479 test pass; vòng retry sinh câu hỏi; cấu hình DeepSeek (thiếu key) |
| Câu hỏi đã sinh | 🟡 | 951 lineage, giữ 771 (81,1%); **950/951 do Claude qua phiên chat**, 1 qua API |
| Nhãn pilot (tập κ) | 🟡 | 300/300 dòng do hai người gán; p_o 0,700, κ **0,236** [0,066; 0,400], AC1 0,520 |
| Phân xử bất đồng | ⬜ | Hàng audit 120 dòng (46 pháp lý, 31 T6, 23 khác, 20 cả hai loại); chưa ai điền |
| Audit nhãn bắt buộc | ⬜ | 0/490 |
| Phiếu T5 cho luật sư | ⬜ | 8 dòng `t5_documents.tsv`, chờ từ 20/09 |
| Cố vấn luật | 🟡 | Đã gửi xlsx 77 dòng. **Đã trả lời 05/10** về chuyển chỗ (mức phạt: tuỳ, không đặt ngưỡng; sang văn bản khác: vẫn là chuyển chỗ). Còn chờ: phiếu T5 và tiêu chí `khong_dat` cho T2/T3/T4 |
| Định nghĩa T6 | 🟡 | Hai người đồng ý 47,3%. Quy tắc chuyển chỗ đã có (`docs/vilextime-annotation-v2-draft.md`); 25 dòng / 20 lineage nghi chuyển chỗ, **2 đã đối chiếu văn bản thô**, 18 chưa kiểm |
| Gold độc lập | ⬜ | Chưa có |
| Scorer | 🟡 | Có chấm tương phản, TVER/VCR, probe; **chưa có** CI, McNemar, `--by-year`, khớp số, điều kiện oracle |
| Release | 🟡 | Schema 1.2.0, chưa đóng băng, chưa dựng lại từ pool mới |
| Datasheet | 🟡 | Có bản thảo; thiếu phễu, bảng lý do loại, tỷ lệ sửa, Ethics, contamination |
| M2 (Neo4j, 100 truy vấn) | ⬜ | E2–E3 chưa làm; 26/10; **cùng hai người** |

---

## 3. Tám luồng việc

**W1. Quyết định và guideline** (chặn gần như mọi thứ)
- ~~Gửi cố vấn hai câu về mức phạt và quy định chung~~ **Xong 05/10**: tuỳ, không đặt ngưỡng mức
  phạt; chuyển sang văn bản khác vẫn là chuyển chỗ (xem `docs/vilextime-annotation-v2-draft.md`).
- Chốt tiêu chí `khong_dat` cho T6, T4, T3, T2. Hướng lệch đổi chiều theo nhóm nên lỗ guideline
  nằm ở từng nhóm.
- Cố vấn phán 8 phiếu T5.
- Đầu ra: guideline v2.0 có ví dụ đúng/sai cho từng nhóm, cố vấn ký.

**W2. Dữ liệu**
- Gắn liên kết kế thừa cho ≥25 dòng T6 nghi chuyển chỗ; ghi bằng chữ nếu kho thiếu điều
  khoản đích (ví dụ khoản 2 Điều 17 trong kho chỉ có điểm a, b, c, không có điểm d).
- Sửa lỗi so cụm từ hoa/thường và áp lại các event `needs_review` (606 ca lấy lại được; khoảng
  21.900 event kẹt). Đây là đòn bẩy vừa tăng số lượng vừa sửa gold.
- Đổi `QUOTA` sang đơn vị lineage ở cả hai file (chờ quyết định "câu" là gì); `PER_DOCUMENT`;
  giảm T1.
- Mốc `as_of` thứ tư cho ca "đã ký chưa hiệu lực" (3.856 transition ≥30 ngày) — đổi schema.
- **Dựng lại pool và đóng băng id trước khi có bất kỳ nhãn mù nào.**

**W3. Sinh câu hỏi**
- Điền `DEEPSEEK_API_KEY`; chạy thử 20 câu, xem tỷ lệ giữ, độ đa dạng mở đầu (dưới 35% cho 5
  cụm đầu), lý do loại.
- Chạy T2, T3, T4 trước; **hoãn T6** tới khi W1 xong.
- Khoảng 10% câu do người viết từ đầu, gắn `question_source`, để chạy ablation theo nguồn câu.
- Xếp hạng `--ancestor-rows 200` (ghi vào `sample.jsonl` đã commit).

**W4. Gán nhãn người** (cửa sổ một lần)
1. Cổng hiệu chỉnh: 50 mẫu có phản hồi, ≥85% đồng thuận với nhãn chuẩn do cố vấn ký (theo
   VLegal-Bench).
2. Gán lại 90 dòng bất đồng và xử lý 20 dòng cả hai loại.
3. Pilot 2: ~50 lineage, nặng T3 và T6.
4. Đợt overlap sản xuất: **600 dòng (sàn 300), hai người thật, mù**, giấu nhãn model, cài lỗi
   kiểm soát, ghi phút mỗi dòng.
5. Audit 300–500 dòng do người không gán dòng đó làm.
- Nhãn thô trước hoà giải được lưu và phát hành. **Không ghi đè `crosscheck_A/B.tsv`.**

**W5. Gold độc lập**: 100–150 dòng do người đọc văn bản thô (`crosscheck_evidence.py` đã cắt
sẵn bằng chứng); báo kết quả hai cột "gold theo KG" và "gold độc lập".

**W6. Chấm điểm và thí nghiệm**
- Thêm `--ci` (bootstrap theo lineage và theo văn bản), `--compare` (McNemar, Holm), cờ
  `value_in_current` (33 dòng, 3,0%), bảng con "nhạy thời gian" (~395 dòng), `--by-year`, khớp
  số có chuẩn hoá (~39% dòng có số).
- Thêm hệ thống `oracle` đầu cuối và static-RAG chỉ bản mới nhất.
- Nêu H1–H4 trước khi chạy.
- Chạy baseline trên dữ liệu **đã đóng băng**.

**W7. Phát hành và tài liệu**: `enrich` (twin, dòng sau hết hiệu lực, split theo văn bản);
`check_release --manifest`; datasheet bổ sung phễu, bảng lý do loại, tỷ lệ người sửa, Ethics
(người gán là tác giả, không được trả công), contamination, canary; Croissant và RAI; giấy phép;
đẩy HF hoặc Dataverse; tag.

**W8. Bài báo và khóa luận**: định vị ("benchmark point-in-time đầu tiên cho luật Việt Nam, cấp
khoản/điểm, có bãi bỏ một phần và hiệu lực lan truyền"), bảng so sánh với 12 bộ đã đọc,
Limitations nêu thẳng.

---

## 4. Đường găng và lịch

```
Cố vấn trả lời (W1) ─► guideline v2.0 ─► cổng hiệu chỉnh ─► gán lại + pilot 2 ─► overlap ─► audit ─► ĐÓNG BĂNG ─► baseline
        │                                    ▲                                              (13–14/11)    (17/11)
        └─ song song được: W3 (T2–T4), W6 (mã), W7 (tài liệu), gắn kế thừa 25 dòng
```

| Tuần | Việc chính | Mốc |
|---|---|---|
| 05–11/10 | Gửi cố vấn hai câu; ghi biên bản D5; điền key DeepSeek, thử 20 câu; viết mã W6 (CI, cờ, by-year); gắn kế thừa 25 dòng; bản thảo guideline v2.0 | |
| 12–18/10 | Buổi cố vấn; guideline v2.0 ký; cổng hiệu chỉnh; pilot 2 | **18/10: go/no-go** |
| 19–25/10 | Gán lại 90 dòng; sinh câu T2–T4; dựng lại pool cuối cùng | |
| 26/10–01/11 | Đợt overlap; **M2 chiếm cùng hai người** | **M2 26/10** |
| 02–08/11 | Xong overlap; κ trên nhãn thô; audit | |
| 09–15/11 | Hoà giải; `enrich`; datasheet; **đóng băng 13–14/11** | |
| | | **M3 16/11** |
| 17–30/11 | Baseline trên dữ liệu đã đóng băng | **M4 30/11** (quyết định B7) |
| Sau đó | Hệ thống đề xuất, thực nghiệm, bài báo (M7 11/01), khóa luận (M8 01/02) | |

Ràng buộc cứng: mọi thay đổi dữ liệu sau khi đóng băng buộc chạy lại baseline; tính BM25 và
embedding cho khoảng 1,5 triệu đơn vị trên 4 CPU, 7 GB RAM, không GPU là giới hạn thật.

Ngày ARR tháng 1/2027 chưa công bố; ICAIL 2027 ghi 28/01/2027 theo một trang tổng hợp, cần kiểm lại.

---

## 5. Các cổng quyết định

| Cổng | Khi nào | Điều kiện | Nếu trượt |
|---|---|---|---|
| ~~G0~~ | Xong 05/10 | A là người thật | — |
| **G1** | ~12/10 | Phán T5 và tiêu chí `khong_dat` cho T2/T3/T4 (chuyển chỗ đã xong 05/10) | T2–T4 và T5 chưa gán lại được; T6 đã gán lại được sau khi kiểm 18 lineage |
| **G2** | Trước gán lại | Guideline v2.0 ký; đạt ≥85% trên 50 mẫu pilot | Hiệu chỉnh thêm một vòng, không gán sản xuất |
| **G3** | 18/10 | Phút trung vị mỗi dòng sau pilot 2: ≤3 giữ mục tiêu; 3–4 giữ nếu gác bớt M2; >4 cắt | Thứ tự cắt: T1 → T4 → T3. **Không cắt** T2, T6 lan truyền dưới 150, overlap |
| **G4** | 13–14/11 | Đóng băng v1.0 | Dùng bản lõi ~1.150–1.200 |
| **G5** | 30/11 (M4) | Điểm quyết định B7 | Đánh giá lại L2–L4 |

Sàn thấp nhất vẫn vượt yêu cầu M3: khoảng 1.100–1.200 lineage. Nếu phải chọn: một bộ ~1.200
lineage có đồng thuận người–người, gold kiểm trên văn bản gốc và chấm tương phản đứng vững hơn
một bộ 1.500 lineage chỉ có một lượt kiểm.

---

## 6. Rủi ro hàng đầu

| Rủi ro | Bằng chứng | Giảm thiểu |
|---|---|---|
| **Cố vấn chậm** | Phiếu T5 trống từ 20/09 | Gửi hai câu ngắn, hẹn lịch cụ thể; việc song song không chờ |
| **Giờ công không đủ** | Ước 250–465 giờ sinh viên so với 175–325 giờ hiện có, tuỳ M2 (ước, chưa đo) | Cổng G3; cân nhắc gác bớt M2 |
| **κ không đạt mốc M3** | κ thô 0,236, cận trên 0,400 | Sửa T6 rồi đo lại; hoặc xin khoa nhận AC1. **Không hoà giải để làm κ đẹp**: chốt theo A ra 0,619, theo B ra 0,769, cả hai vô nghĩa |
| **T3 và T6 mỏng hơn pool** | T3 người loại ~50% (≈190 dùng được); T6 xoá hẳn thật chưa biết sau khi tách chuyển chỗ | Tính quota theo con số sau khi người lọc |
| **Gold dùng chung nguồn với hệ thống (N1)** | Recall L2 62,2%; ví dụ điều 17 cho thấy có nút bị thiếu | W5; ghi giới hạn trong khóa luận |
| **Thiên lệch người soạn câu** | 950/951 câu do Claude | DeepSeek, 10% người viết, baseline chính ngoài họ Claude |
| **Chạy lại baseline** | Dữ liệu đổi sau đóng băng | Đóng băng đúng hạn, hai ngày đệm |

---

## 7. Việc làm được ngay, không bị chặn

1. Ghi biên bản D5 (tên hai người gán; 13 dòng không mù).
2. Kiểm 18 lineage còn lại trong `audit_queue_relocation.tsv` (mở văn bản đích, điền `norm_continuity`).
3. Điền key DeepSeek, chạy `--limit 20` cho T2.
4. Viết `--ci`, `--compare`, cờ `value_in_current`, `--by-year` trong scorer.
5. Gắn kế thừa tay cho 25 dòng T6 (ước 2–4 giờ).
6. Điền 20 dòng tier 4 trong hàng audit: sửa câu hỏi hay bỏ lineage.
7. Dựng bản thảo guideline v2.0 theo câu trả lời của cố vấn về Q1–Q4.

---

## 8. Quyết định cần chốt

| # | Quyết định | Đề xuất | Chặn gì |
|---|---|---|---|
| ~~1~~ | ~~A là ai~~ | Đã xác nhận: người thật | — |
| 2 | "Câu" là lineage hay dòng QA | Báo cả hai; hỏi khoa | Quota |
| 3 | Gác bớt M2 hay chấp nhận bản lõi | Quyết sau G3 | Giờ công |
| 4 | Mô hình schema cho chuyển chỗ | Bản gọn: `norm_continuity` + `successor`; `substantive_change` suy ra từ diff | W2 |
| 5 | Rebuild trước khi gán mù | Có | W4 |
| 6 | Ngưỡng đồng thuận | Đăng ký AC1 ≥ 0,80 và p_neg ≥ 0,6; κ báo minh bạch | Guideline |
| 7 | Phạm vi T5 | Cố vấn quyết; 30–45 lineage có trần theo văn bản | Tập κ |
| 8 | Giờ và thù lao cố vấn; thẩm định đạo đức UIT | Hỏi khoa | Datasheet |

---

## 9. Không thuộc "100%"

Để khỏi mở rộng phạm vi:
- Văn bản địa phương (23 shard, ~116 nghìn văn bản).
- Track tác vụ siêu dữ liệu kiểu LexKairos (bổ sung cho bài báo, không tính vào M3).
- Câu hỏi nhiều điều khoản (ViLexTime chưa có hiện tượng này; khai trong Limitations).
- Mục tiêu 1.500 lineage nếu giờ công không đủ.
