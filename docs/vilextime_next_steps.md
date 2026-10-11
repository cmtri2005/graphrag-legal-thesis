# ViLexTime: việc còn lại để hoàn thành bộ dữ liệu

Lập ngày 11/10/2026, theo trạng thái repo ở commit `f58c101` (nhánh `feature/framework`).
Mốc M3 trong master plan: **16/11/2026**.

Bản phát hành hiện tại: `data/derived/vilextime/release.jsonl`, 2.730 dòng, gồm 1.225 dòng ranh
giới và 653 câu hỏi (lineage). `check_release.py` OK, 499 test pass. Phần máy làm được đã xong.
Mọi việc dưới đây cần người, hoặc cần người quyết trước rồi Claude mới làm tiếp.

Người làm: **A = CMT**, **B = NMT** (hướng dẫn §5), **LS** = cố vấn luật, **Khoa** = khoa/GVHD,
**Claude** = phần máy, chạy khi có đầu vào của người.

---

## 0. Tổng quan và thứ tự

| # | Việc | Ai | Chặn việc nào | Khối lượng |
|---|---|---|---|---|
| 1 | Đẩy nhánh lên GitHub để sao lưu | A | — (làm ngay) | 1 lệnh |
| 2 | Chốt hướng dẫn gán nhãn v2.0 | A + LS | 3, 4, 7 | 1 tài liệu |
| 3 | Gán bộ kiểm chéo D4 | A, B (riêng, mù) | 5, 13 | A 134 dòng, B 135 dòng |
| 4 | Claude gán nhãn model 276 dòng T6, rồi người audit | Claude → A/B | 13 | 276 dòng |
| 5 | Tính đồng thuận, hoà giải D5, biên bản | A, B | 13 | các dòng lệch |
| 6 | Audit nhãn model | A/B (người không gán dòng đó) | 13 | 385 dòng trong 3 phiếu |
| 7 | Luật sư chốt T5 và nhận định giấy phép | LS | 13 | 8 văn bản, 34 dòng |
| 8 | Hàng đợi chuyển chỗ (T6) | A hoặc B | 13 | 20 dòng |
| 9 | Cờ "cấp huyện" trong hàng đợi hiệu lực | A hoặc B | 13 | 8 cờ |
| 10 | Kiểm ngày ký cho chế độ `truoc_hieu_luc` | A hoặc B | 13 | 30 dòng |
| 11 | Hỏi khoa: "câu" là dòng hay lineage; AC1 là thước đo chính | A | M3 | 1 buổi trao đổi |
| 12 | Gold độc lập (J7) | Quyết định → Claude → A/B | 13 | khoảng 120 dòng |
| 13 | Đóng băng v1.0 | Claude, A duyệt | — | — |
| 14 | (Tùy chọn) Chuẩn công bố bài báo | A, B, Claude | — | — |

Thứ tự đi nhanh nhất: **1 → 2 → (3 và 4 song song) → 5 → 6 → 13**. Các việc 7, 8, 9, 10, 11, 12
không phụ thuộc nhau, làm song song ngay từ bây giờ.

**Quy tắc chung khi gán nhãn**
- Chỉ điền vào cột nhãn. Không sửa câu hỏi, đáp án hay bất kỳ cột dữ liệu nào: `import` sẽ từ chối
  toàn bộ file nếu một ô dữ liệu bị đổi.
- Không xem nhãn của người kia hay của model trước khi tự gán (D4 phải mù).
- Mọi file nhãn nằm trong `data/review/`. Không chép ra thư mục khác để làm rồi quên chép về.
- Xong mỗi đợt thì commit ngay. Nhãn người là thứ duy nhất không dựng lại được.

---

## 1. Đẩy nhánh lên GitHub (làm ngay)

**Vì sao:** nhánh `feature/framework` chưa có trên GitHub và đang đi trước `origin/main` 58 commit.
Câu hỏi đã trả tiền API, nhãn người và đáp án ngắn hiện chỉ nằm trên một máy.

**Làm:**
```bash
git push -u origin feature/framework
```
Trước khi đẩy, kiểm repo `cmtri2005/graphrag-legal-thesis` đang ở chế độ riêng tư. Nếu repo công
khai thì cân nhắc trước khi đẩy `data/review/` (nhãn người, phiếu luật sư).

**Xong khi:** `git status -sb` hiện `## feature/framework...origin/feature/framework`.

---

## 2. Chốt hướng dẫn gán nhãn v2.0

**Vì sao:** T6 có 388 dòng ranh giới. Lần đo 07/10, T6 có κ = −0,02, do pool T6 lẫn các khoản
"chuyển chỗ" chứ không thật sự bị bãi bỏ. Pool đã sửa. Nhưng nếu người gán T6 theo v1.2, họ sẽ
lại bất đồng ở đúng chỗ đó.

**Đầu vào:**
- `docs/vilextime-annotation-v2-draft.md`: bản thảo, mới có phần T6 và chuyển chỗ, dựa trên
  phán quyết của cố vấn ngày 05/10;
- `docs/vilextime-annotation.md`: v1.2 đang dùng.

**Làm:**
1. A đọc bản thảo, đối chiếu bốn điểm cố vấn đã chốt (§1 của bản thảo).
2. Bổ sung phần bản thảo còn thiếu:
   - tiêu chí `khong_dat` cho T2 và lát gần giống (T4 cũ): câu hỏi phải chạm đúng cụm đã đổi.
     Đổi cách gọi cùng một văn bản ("Nghị định này" → "Nghị định số …") là `group_mismatch`;
     đổi tên cơ quan là `dat`;
   - T3, T5: nếu không đổi so với v1.2 thì ghi rõ "như v1.2".
3. LS xác nhận phần pháp lý (T6, chuyển chỗ, điều khoản chuyển tiếp).
4. Báo Claude để:
   - gộp bản thảo vào `docs/vilextime-annotation.md`, đổi phiên bản thành 2.0;
   - đổi `GUIDELINE = "2.0"` trong `scripts/review/crosscheck.py`;
   - xuất lại `data/review/crosscheck_{A,B}.xlsx`. Trang "Đọc trước" trong xlsx được sinh từ
     hướng dẫn, nên phải xuất lại thì người gán mới đọc đúng bản mới.

**Xong khi:** `docs/vilextime-annotation.md` ghi "Phiên bản 2.0", có xác nhận của LS (ghi ngày
và tên vào đầu tài liệu), và xlsx đã xuất lại.

> **Chưa ai được gán dòng T6 trong D4 trước khi xong việc này.** Các dòng T2, T3, T5 của D4 thì
> gán được ngay theo v1.2.

---

## 3. Gán bộ kiểm chéo D4

**Vì sao:** đây là con số đồng thuận giữa hai người mà khóa luận và bài báo phải báo.

**Đầu vào:** `data/review/crosscheck_A.xlsx` (của A) và `data/review/crosscheck_B.xlsx` (của B).
Mỗi file có 300 dòng, cùng tập dòng nhưng thứ tự khác nhau.

| | Đã có nhãn từ đợt trước (khóa, không sửa) | Còn phải gán |
|---|---:|---:|
| A | 166 | 134 (T2 42, T6 92) |
| B | 165 | 135 (T2 43, T6 92) |

Cơ cấu 300 dòng: T2 thường 50, T2 gần giống 50, T3 50, T5 38, T6 bãi bỏ qua nút cha 86, T6 bãi
bỏ trực tiếp 26.

**Làm:**
1. Mở xlsx, đọc trang "Đọc trước" và "Mã lý do".
2. Ở trang "Gán nhãn", chỉ điền các ô xanh còn trống:
   - `verdict`: chọn `dat` hoặc `khong_dat` từ danh sách;
   - `reasons`: chỉ điền khi `khong_dat` (ví dụ `group_mismatch`, `gold_wrong`); nhiều mã thì
     cách nhau bằng dấu phẩy;
   - `note`: bắt buộc khi có `gold_wrong` hoặc `other`.
3. Mở `source_url` khi cần đối chiếu văn bản gốc.
4. Lưu file, rồi nạp về TSV:
   ```bash
   python scripts/review/crosscheck_xlsx.py import --who A
   python scripts/review/crosscheck_xlsx.py import --who B
   ```
   Nếu báo lỗi thì không có gì bị ghi. Sửa đúng các dòng được báo rồi chạy lại.
5. Commit `data/review/crosscheck_A.tsv`, `crosscheck_B.tsv` cùng hai file xlsx.

**Xong khi:** cả hai file có đủ 300/300 `verdict` và `import` chạy không lỗi.

**Lưu ý:** 19 dòng trong D4 đã có nhãn từ ngoài D4. Trang "Đọc trước" có ghi các dòng này; biên
bản D5 phải nêu (việc 5).

---

## 4. Nhãn cho 276 dòng T6 chưa có nhãn

**Vì sao:** 138 lineage T6 (câu hỏi mới sinh ngày 07/10 và 11/10, ngoài D4) chưa có nhãn nào.
Theo quy trình §6 của hướng dẫn, model gán trước, người audit sau.

**Làm:**
1. Sau khi xong việc 2, nhắn Claude: "gán nhãn model cho T6 theo hướng dẫn 2.0".
2. Claude gán qua `scripts/review/labels.py add`. Mọi nhãn model gán theo hướng dẫn mới đều tự
   động vào diện audit.
3. Claude xuất phiếu audit T6:
   `python scripts/review/labels.py audit-sheet data/review/audit_T6.xlsx --group T6`.
4. A/B audit như việc 6.

**Xong khi:** 276/276 dòng có nhãn model, và phiếu `audit_T6.xlsx` đã được audit.

---

## 5. Tính đồng thuận, hoà giải (D5) và biên bản

**Làm:**
1. Sau việc 3:
   ```bash
   python scripts/review/crosscheck.py kappa
   ```
   Kết quả ghi vào `data/review/crosscheck_result.json`.
2. Đọc kết quả theo ngưỡng **đã đăng ký trước**:
   - **AC1 ≥ 0,80** (thước đo chính);
   - **p_neg ≥ 0,60**, tức mức đồng thuận trên `khong_dat`, nhãn làm loại dòng;
   - κ chỉ báo kèm. Ở tỷ lệ `dat` khoảng 85%, κ ≥ 0,6 gần như không đạt được (đã đo 07/10).
3. Nếu chưa đạt ngưỡng: xem các dòng lệch theo nhóm, sửa hướng dẫn ở chỗ hay lệch, tăng phiên bản
   hướng dẫn, rồi gán lại phần lệch.
4. **Hoà giải:** A và B ngồi cùng nhau (hoặc nhờ người thứ ba) xét từng dòng lệch, ghi kết quả vào
   cột `adjudicated` của `data/review/crosscheck_A.tsv`. **Không sửa** `verdict` gốc của ai: nhãn
   thô được giữ nguyên và phát hành.
5. Phân xử các cờ hiệu lực thuộc lineage κ trong `data/review/validity_queue.tsv` (cột
   `in_kappa = co`), sau khi hoà giải xong.
6. **Biên bản D5:** tạo `docs/reports/D5_bien_ban.md`, ghi:
   - A là ai, B là ai (bảng ánh xạ chỉ để trong plan, không phát hành);
   - ngày gán, phiên bản hướng dẫn đã dùng;
   - kết quả AC1, p_neg, κ kèm khoảng tin cậy, theo từng nhóm;
   - các dòng không mù: 19 dòng đã có nhãn từ ngoài D4, và 166/165 dòng mang nhãn từ đợt
     07/10 (bản đợt cũ lưu ở `data/review/crosscheck_{A,B}.20261011.tsv`);
   - danh sách dòng lệch và quyết định hoà giải.

**Xong khi:** `crosscheck_result.json` mới; cột `adjudicated` điền đủ cho mọi dòng lệch; có biên
bản; mọi dòng `khong_dat` sau hoà giải đã được báo Claude để loại hoặc thay (việc 13).

---

## 6. Audit nhãn model

**Vì sao:** nhãn model không được báo như nhãn người. Khóa luận báo **tỷ lệ đồng ý khi audit**.

**Đầu vào:** `data/review/audit_T1.xlsx` (55 dòng), `audit_T2.xlsx` (223 dòng), `audit_T3.xlsx`
(107 dòng), và sau việc 4 thêm `audit_T6.xlsx`.

**Làm:**
1. Người audit một dòng phải là người **không gán** dòng đó.
2. Với mỗi dòng, mở lịch sử văn bản (`source_url`, văn bản hợp nhất trên cổng) và kiểm ở **mọi**
   ngày hỏi (cột `also_asked_at`):
   - (a) không có văn bản nào sửa đổi hay bãi bỏ điều khoản trước ngày hỏi mà chuỗi bỏ sót;
   - (b) văn bản chưa hết hiệu lực toàn bộ;
   - (c) không có điều khoản chuyển tiếp giữ quy định cũ cho đúng quan hệ trong câu hỏi. Nếu có
     thì ghi Điều chuyển tiếp.
3. Điền:
   - `audit`: `dong_y` hoặc `khong_dong_y`;
   - `auditor`: `human:<mã>`, ví dụ `human:A`;
   - `audit_note`: bắt buộc khi `khong_dong_y`; ghi cả lỗi ở dòng anh em (kèm ngày, văn bản)
     và đáp án ngắn "đòi thừa".
4. Nạp về:
   ```bash
   python scripts/review/labels.py import-audit data/review/audit_T1.xlsx
   python scripts/review/labels.py report
   ```
5. **Luật leo thang:** nếu trong mẫu 20% `dat` của một nhóm có hơn 5% `khong_dong_y`, phải audit
   toàn bộ `dat` của nhóm đó. `labels.py report` sẽ cảnh báo.

**Xong khi:** `labels.py report` báo `0 / 0` nhãn bắt buộc còn lại trên dòng đang phát hành
(hiện tại: 0 đã làm / 375 bắt buộc), và không nhóm nào còn cảnh báo leo thang.

Mấy dòng model đã ghi chú để người audit xem kỹ:
- 05/2010/TT-BXD Đ13.1 và 75/2021/NĐ-CP Đ13.6: vế trước "không giới hạn". Xem có nên đánh
  `unanswerable_as_asked` không.
- 82/2020/NĐ-CP Đ24.7.a: đổi "Hủy" thành "Buộc hủy bỏ". Xem đây là đổi thật hay chỉ đổi cách gọi.

---

## 7. Luật sư chốt T5 và giấy phép

**Vì sao:** việc một văn bản có thuộc hiệu lực trở về trước theo Điều 152 Luật Ban hành VBQPPL hay
không là phán đoán pháp lý. Đề cương dùng chuẩn "có lợi" là chưa đúng (đã ghi trong datasheet §6).

**Đầu vào:**
- `data/review/t5_documents.tsv`: 8 văn bản (119/2026/NĐ-CP, 65/2025/TT-BQP, 12/2015/NĐ-CP,
  26/2015/TT-BTC, 130/2016/TT-BTC, 96/2002/QĐ-BTC, 123/2003/QĐ-BTC, 2714/QĐ-BTC). Có câu hiệu
  lực trích sẵn và link;
- `data/review/t5_items.tsv`: 34 dòng, từng cặp đáp án cụ thể;
- `data/review/gui_co_van.xlsx`: bản đã gửi cố vấn trước đây.

**Làm:**
1. Gửi hai file TSV (hoặc xuất ra xlsx) cho LS.
2. LS điền:
   - `t5_documents.tsv`: `LUẬT SƯ: thuộc Điều 152? (có/không)` và `LUẬT SƯ: ghi chú`;
   - `t5_items.tsv`: `LUẬT SƯ: đáp án mốc sau đúng? (có/không)` và ghi chú.
   - Riêng 12/2015/NĐ-CP: câu hiệu lực không nêu ngày hồi tố, cần LS cho ý kiến cụ thể.
3. Cùng buổi, xin LS xác nhận nhận định: lời văn pháp luật không thuộc đối tượng bảo hộ quyền tác
   giả (Điều 15 Luật Sở hữu trí tuệ), nên phát hành theo CC BY 4.0 được (`data/vilextime/LICENSE`).
4. Commit hai file đã điền, rồi báo Claude. **Chưa có script nào đọc cột `LUẬT SƯ:`**, nên Claude
   sẽ áp kết quả: văn bản bị loại thì lineage của nó vào `data/vilextime/dropped.jsonl`, T6 tự nhận
   phần thiếu, rồi dựng lại bản phát hành. Nếu T5 đổi, D4 có thể phải dựng lại phần T5/T6. Vì vậy
   nên có kết quả LS **trước khi** gán xong T6 của D4.

**Xong khi:** hai cột `LUẬT SƯ:` điền đủ 8/8 và 34/34; có ghi nhận nhận định giấy phép (ngày, tên
LS) trong datasheet §7.

---

## 8. Hàng đợi chuyển chỗ (T6)

**Vì sao:** cổng `norm_continuity` của pool T6 dùng một tín hiệu gần đúng ("cùng ngày có sửa đổi
khác trong cùng văn bản"), cố ý bắt dư. 20 dòng này đo độ chính xác của tín hiệu đó. Theo hướng dẫn,
chỉ người đọc văn bản đích mới được ghi `moved`.

**Đầu vào:** `data/review/audit_queue_relocation.tsv`, 20 lineage: 18 "chưa kiểm", 2 "đã đối chiếu
văn bản thô 05/10, chờ người xác nhận".

**Làm:** với mỗi dòng, đọc văn bản đích và điền:
- `check_conduct`, `check_subject`, `check_conditions`, `check_structure`: hành vi, đối tượng,
  điều kiện, cấu trúc có giữ nguyên không;
- `norm_continuity`: `none`, `moved` hoặc `unclear`;
- `successor`: chỗ quy định mới (cho phép ghi bằng chữ nếu kho thiếu điều khoản đích);
- `annotator`, `note`.

Kiểm con trỏ của người gán trước với văn bản đích. Ví dụ ghi nhận 05/10: B ghi khoản 2 Điều 3
TT 74/2022, nhưng nội dung nằm ở khoản 3.

**Xong khi:** 20/20 dòng có `norm_continuity` do người ghi; báo Claude để tính độ chính xác của tín
hiệu và ghi vào datasheet.

---

## 9. Cờ "cấp huyện" trong hàng đợi hiệu lực

**Vì sao:** từ 01/07/2025 không còn cấp huyện. Dòng hỏi sau mốc này mà câu hỏi hoặc đáp án còn nói
"cấp huyện" có thể sai. Văn bản chuyển tiếp liên ngành có thể nằm ngoài kho.

**Đầu vào:** `data/review/validity_queue.tsv`. 8 cờ `kind = cap_huyen` (ngoài bộ κ, `active = co`)
còn trống cột `decision`.

**Làm:** xem từng cờ, điền:
- `decision`: `loi`, `co_the_sai`, `bao_dong_gia` hoặc `da_sua`;
- `reviewer`: mã người.

**Xong khi:** 8/8 cờ có `decision`; dòng `loi` được báo Claude để loại hoặc dời ngày (việc 13).

---

## 10. Kiểm ngày ký cho chế độ `truoc_hieu_luc`

**Vì sao:** 153 dòng `truoc_hieu_luc` hỏi 30 ngày trước khi phiên bản sau có hiệu lực, với điều kiện
văn bản sửa đổi **đã ký**. Ngày ký lấy từ cổng, mà cổng từng sai ngày (JUDGE C1).

**Đầu vào:** `data/review/audit_truoc_hieu_luc.tsv`, 30 dòng chọn tất định, đã có link văn bản.

**Làm:** mở link, đối chiếu ngày ký và ngày hiệu lực trong văn bản. Điền:
- `ngay_ky_dung`, `ngay_hieu_luc_dung`: `dung`, hoặc ngày đúng nếu cổng sai;
- `ghi_chu`, `nguoi_kiem`.

**Xong khi:** 30/30 dòng điền đủ. Claude tính tỷ lệ sai (Wilson CI). Nếu có sai, Claude loại các
dòng có ngày ký sau ngày hỏi.

---

## 11. Hỏi khoa

**Vì sao:** đề cương ghi "1.150 câu hỏi" và "κ ≥ 0,6". Bộ dữ liệu có 1.225 **dòng** (câu hỏi, mốc)
nhưng chỉ 653 **câu hỏi** khác nhau. Còn κ thì không đạt được ở tỷ lệ nhãn hiện tại.

**Làm:** gặp GVHD/khoa, hỏi và **báo** (không phải xin phép):
1. "Câu" trong mốc M3 tính theo dòng (1.225) hay theo câu hỏi khác nhau (653)?
2. Thước đo đồng thuận chính là AC1 ≥ 0,80 kèm p_neg ≥ 0,60, đã đăng ký trước. κ vẫn báo kèm.
   Lý do: ở tỷ lệ `dat` khoảng 85%, κ ≥ 0,6 đòi đồng ý trên 89,8%, không phụ thuộc người gán cẩn
   thận đến đâu.

**Xong khi:** có câu trả lời bằng văn bản (email). Ghi vào master plan (mốc M3) và datasheet §6.

---

## 12. Gold độc lập (J7)

**Vì sao:** gold của bộ dữ liệu được dựng từ chính chuỗi phiên bản mà hệ thống đề xuất dùng. Phản
biện mạnh nhất sẽ là "gold và hệ thống cùng sai một chỗ". Tập con có gold do người dựng từ văn bản
thô trả lời phản biện đó. Kết quả được báo hai cột: "gold theo KG" và "gold độc lập".

**Hai quyết định cần chốt trước (A):**
1. **Mù hay không mù.** Đề xuất của Claude: **mù**. Người đọc chỉ thấy câu hỏi, ngày hỏi và văn bản
   thô (đoạn gốc, đoạn sửa đổi, điều khoản chuyển tiếp, do `scripts/review/crosscheck_evidence.py`
   cắt sẵn), rồi tự ghi điều khoản có hiệu lực. Không thấy đáp án KG. Script so sánh sau.
2. **Khi nào rút mẫu.** Đề xuất: rút ngay phần T1–T3 (gold đã ổn định), phần T6 rút sau khi xong
   việc 2.

**Làm sau khi chốt:** báo Claude rút mẫu khoảng 120 dòng (dư dòng `giua_khoang`, ngoài các lineage
của D4) và dựng phiếu. A/B đọc, điền. Claude tính tỷ lệ gold sai kèm Wilson CI; dòng sai thì
chuyển `split = excluded`.

**Xong khi:** có tỷ lệ gold sai trên khoảng 120 dòng kèm khoảng tin cậy, ghi vào datasheet §5 và §8.

---

## 13. Đóng băng v1.0 (Claude làm, A duyệt)

Làm sau khi xong 3–10 và 12. Claude sẽ:
1. Áp mọi kết quả người:
   - dòng `khong_dat` sau hoà giải hoặc audit: viết lại câu hỏi, hoặc loại lineage (vào
     `dropped.jsonl`) và để lineage kế tiếp trong bảng xếp hạng thế chỗ. **Không sửa gold âm
     thầm**: sửa gold là thay đổi MAJOR (ADR 0003 §8);
   - quyết định của LS về T5, hàng đợi chuyển chỗ, cờ cấp huyện, ngày ký.
2. Dựng lại, theo đúng thứ tự:
   ```bash
   python scripts/pipeline/build_vilextime.py
   python scripts/pipeline/sample_vilextime.py --select
   python scripts/pipeline/enrich_vilextime.py
   python scripts/check/check_release.py
   python -m pytest -q
   ```
3. Viết đáp án ngắn cho phiên bản mới (nếu có lineage thay thế), sinh câu hỏi cho lineage thay thế
   nếu thiếu.
4. Cập nhật datasheet lần cuối: số liệu, phễu chọn, bảng lý do loại, tỷ lệ người sửa, kết quả
   AC1/κ, tỷ lệ gold sai, mục "Chưa xong" phải trống.
5. Commit, rồi ghi manifest trên cây sạch:
   ```bash
   python scripts/check/check_release.py --manifest
   ```
6. **Hỏi A trước khi:** gắn tag `vilextime-v1.0` và đẩy bản phát hành lên HF/GCS.

**Xong khi:** tag `vilextime-v1.0` tồn tại, manifest có `uncommitted_changes: false`, datasheet
không còn mục "Chưa xong", bản phát hành đã ở ngoài máy.

---

## 14. (Tùy chọn) Chuẩn công bố cho bài báo

Chỉ cần nếu nộp ARR 01/2027 hoặc ICAIL 2027:
- metadata Croissant và các trường Responsible AI;
- mục kiểm tra nhiễm dữ liệu (contamination) và canary GUID;
- mục Ethics: người gán là tác giả, không được trả công;
- phát hành nhãn thô trước hoà giải;
- cân nhắc mở rộng overlap từ 300 lên 600 dòng.

---

## Phụ lục: việc ngoài bộ dữ liệu nhưng liên quan

- **P5.1:** chọn LLM cụ thể cho cột kết quả chính, **không thuộc họ Claude và không thuộc họ
  DeepSeek** (ADR 0004 §3, chốt 11/10).
- 4 ứng viên ngày hiệu lực còn chờ người trong `data/review/temporal_candidates.jsonl`
  (02/2018/TT-BGTVT, 24/2001/TT-BTC, 113/2011/TT-BTC, 20/2026/TT-BTC). Không chạm bản phát hành
  (kiểm 25/09), chỉ ảnh hưởng đồ thị tri thức.
