# ViLexTime: định nghĩa sáu nhóm, bản chốt đề xuất

**Trạng thái: BẢN THẢO chờ ký, 06/10/2026.** Chưa thay `classify()` trong
`build_question_pool.py`, chưa thay `docs/vilextime-annotation.md` (v1.2), chưa đổi datasheet.
Mục 8 liệt kê những gì cần nhóm hoặc khoa quyết định trước khi đóng băng.

---

## 1. Nguyên tắc chốt: mỗi nhóm cô lập một bậc của thang RQ3

Bảng 1 đề cương trộn ba loại thứ vào một biến phân loại: thuộc tính dữ liệu (số phiên bản ở
T1/T2/T3, độ giống ở T4), hiện tượng pháp lý (hồi tố T5, bãi bỏ một phần T6), và **mục đích đo**
("đo lợi ích của đồ thị" T3, "đo ảo giác trích dẫn" T4). Hai loại đầu là dữ liệu; loại thứ ba là
giả thuyết, không phải nhãn.

Các bộ dữ liệu được nhận ở hội nghị đều chia nhóm theo **năng lực bị kiểm**, không theo thuộc
tính dữ liệu: bộ tiếng Đức chia theo hai chế độ lỗi (post-cutoff staleness, recency bias);
LexKairos chia theo ba năng lực (identification, verification, reasoning); LeKUBE chia theo năm
chiều, trong đó có *locality*. Nguyên tắc đó áp vào ViLexTime có một dạng tự nhiên, vì RQ3 đã
cho sẵn một thang bốn bậc **lồng nhau** (`src/vilexgraph/framework/temporal.py`):

```
𝒰ₜ(propagated) ⊆ 𝒰ₜ(version) ⊆ 𝒰ₜ(document) ⊆ 𝒰ₜ(none)
   none        ρ = text, không ràng buộc thời gian          B2/B3/B4
   document    + ngày của chính văn bản                     B7
   version     + I1, khoảng hiệu lực của chuỗi phiên bản    B7+
   propagated  + I2, khoảng của mọi đơn vị cấp trên, CT (3) hệ thống đề xuất
```

**Nguyên tắc chốt: một nhóm tồn tại khi và chỉ khi nó cô lập được một bậc chuyển của thang này,
hoặc làm đối chứng cho toàn thang.** Mọi thứ khác là *trường cắt ngang* (mục 4), không phải nhóm.

Phép đo trên bản phát hành 29/09 (bậc thấp nhất đủ để loại đáp án sai, bảng chính 1.150 dòng):

| Nhóm | `none` | `document` | `version` | `propagated` |
|---|---:|---:|---:|---:|
| T1 | **251** | 0 | 0 | 0 |
| T2 | 0 | 0 | **400** | 0 |
| T3 | 0 | 0 | **199** | 0 |
| T4 | 0 | 0 | **150** | 0 |
| T5 | 0 | 0 | **38** | 0 |
| T6 | 44 | 0 | 45 | **23** |
| *chế độ `sau_het_hieu_luc`* | — | **181** | — | — |

Ba kết luận, và cả ba đều đổi thiết kế:

1. **T2, T3, T4, T5 nằm trên cùng một bậc (`version`).** Chúng không phải bốn năng lực khác nhau;
   chúng là bốn **tầng độ khó** của cùng một năng lực. Đây là căn cứ kỹ thuật để hạ số phiên bản
   và độ giống xuống thành trường, chứ không phải lý lẽ về mỹ học thiết kế.
2. **T6 vỡ làm ba** (44 / 45 / 23). Bậc `propagated` chỉ được 23 dòng bảng chính chạm tới, và đó
   đúng là H3. T6a và T6b nằm trên **hai bậc khác nhau**, nên tách chúng không phải lựa chọn
   trình bày mà là điều kiện để RQ3 đo được.
3. **Bậc `document` hiện không được đo trên bảng chính.** Chỉ 181 dòng `sau_het_hieu_luc` chạm
   tới, mà datasheet lại lấy `giua_khoang` làm bảng kết quả chính. Khớp JUDGE N2: *"0 dòng thuộc
   loại `document_repealed` hay `not_yet_in_force`, nên siêu dữ liệu cấp văn bản không bao giờ bị
   thử thách trực tiếp"*. Thang RQ3 vì vậy đang **hụt một bậc**, và T5 là chỗ lấp (mục 2.5).

---

## 2. Sáu nhóm

Mỗi nhóm có bảy ô: năng lực bị kiểm · bậc thang cô lập · điều kiện thuộc nhóm · mốc hỏi · đáp án
đúng · chỉ số chính · vì sao không gộp được vào nhóm khác.

### 2.1 T1 — đối chứng tĩnh (locality)

| | |
|---|---|
| **Năng lực** | Thêm khả năng thời gian có **làm hỏng** câu không phụ thuộc thời gian không |
| **Bậc cô lập** | Đối chứng cho toàn thang: không bậc nào giúp, nên mọi chênh lệch là tác hại |
| **Điều kiện** | Đúng 1 phiên bản có ngày; văn bản còn hiệu lực tại mốc hỏi; không mất hiệu lực do đơn vị cấp trên |
| **Mốc hỏi** | Một mốc, trải xác định trong `[bắt đầu + 1, bắt đầu + 30]`, kẹp theo ngày hết hiệu lực của văn bản và ngày chụp corpus |
| **Đáp án đúng** | Phiên bản duy nhất |
| **Chỉ số chính** | **Không phải accuracy tuyệt đối.** Hai số: (a) độ lệch so với baseline không thời gian `none`; (b) tỷ lệ từ chối sai |
| **Không gộp được** | Là nhóm duy nhất mà *mọi* bậc thang phải cho cùng kết quả. Không có nó thì không biết lợi ích ở T2–T6 đến từ khả năng thời gian hay từ truy xuất tốt hơn |

**Căn cứ.** Mọi probe chọn phiên bản đạt 1,000 ở T1. Điểm 1,000 là **đúng với vai trò**, không
phải khuyết điểm: T1 không phân biệt hệ thống chọn phiên bản, nó phân biệt hệ thống *làm hại*.
Tên "locality" mượn khung năm chiều của LeKUBE (ở đó locality đo việc cập nhật một điều luật có
phá kiến thức không liên quan không, kiểm trên 60 điều không sửa). Đây là **mượn khái niệm**:
LeKUBE kiểm sửa tham số model, ViLexTime kiểm hệ thống truy hồi. Các bộ thời gian lớn đều giữ một
nhóm tĩnh: "Static" của SituatedQA, "Unchanged" của TemporalWiki, "never-changing" của FreshQA.

**Đổi so với đề cương.** Nhãn Bảng 1 là "Đối chứng" (giữ). Vai trò mô tả lại thành locality.
Mốc hỏi đã dời khỏi `bắt đầu + 1` (05/10), vì đặt cố định ở đó dạy phân bố biên rằng
`as_of − 1` là ranh giới phiên bản.

### 2.2 T2 — chọn phiên bản, độ khó nền

| | |
|---|---|
| **Năng lực** | Chọn đúng phiên bản khi khoảng hiệu lực của chính đơn vị là thứ phân biệt |
| **Bậc cô lập** | `document` → `version` |
| **Điều kiện** | Đúng 2 phiên bản có ngày; lần chuyển là **thực chất** (không chỉ hoa thường, dấu câu, khoảng trắng); văn bản còn hiệu lực ở cả hai mốc |
| **Mốc hỏi** | Hai mốc, hai phía của lần chuyển. Chế độ `ranh_gioi` dùng `[bắt đầu₂ − 1, bắt đầu₂]`; chế độ `giua_khoang` lấy mốc cách hai đầu ≥ 30 ngày |
| **Đáp án đúng** | Mỗi mốc một phiên bản khác nhau; đáp án ngắn của phiên bản này **không** được nằm trong phiên bản kia |
| **Chỉ số chính** | Accuracy tương phản và **TCS** (cặp phải đúng cả hai mốc) |
| **Không gộp được** | Là nhóm nền của bậc `version`. T3 và T4 định nghĩa *so với* nó |

**Căn cứ.** Đây là nhóm duy nhất mà định nghĩa đề cương, hiện tượng và code khớp nhau. Chữ ký
probe: mới nhất 0,500 · đầu tiên 0,500 · ngày gần nhất 0,772 · rào đón tương phản 0,057.
Quan hệ hai mốc là một **quan hệ biến hình** theo nghĩa LawShift: cùng câu hỏi, đổi mốc, đáp án
**phải** đổi. Nhờ đó TCS kiểm được tính nhất quán mà không cần nhãn vàng bổ sung, và nó bắt đúng
thứ TimeQA đo (chỉ 66% câu đúng giữ nguyên đúng khi đổi mốc).

### 2.3 T3 — chọn phiên bản qua chuỗi nhiều bước

| | |
|---|---|
| **Năng lực** | Chọn đúng phiên bản khi chuỗi có ≥ 3 phiên bản, tức phải phân biệt được nhiều hơn hai trạng thái |
| **Bậc cô lập** | `document` → `version`, ở độ khó cao hơn T2 |
| **Điều kiện cấu trúc** | ≥ 3 phiên bản có ngày; ≥ 2 lần chuyển thực chất |
| **Điều kiện ở tầng câu hỏi (R2, bắt buộc)** | Chuỗi chỉ là T3 khi **chính câu hỏi đó** có đáp án khác nhau ở **mọi** mốc. Chuỗi mà câu hỏi chỉ chạm một lần sửa là T2 với `n_versions ≥ 3`, không phải T3 |
| **Mốc hỏi** | Một mốc trước mỗi lần chuyển, cộng mốc của lần chuyển cuối |
| **Đáp án đúng** | Phiên bản tại mốc; mỗi mốc một đáp án phân biệt |
| **Chỉ số chính** | Accuracy tương phản, **chuẩn hoá theo mức ngẫu nhiên của từng item** |
| **Không gộp được** | Mức ngẫu nhiên khác T2 (1/3 so với 1/2), nên điểm không so thẳng được. Và nó là nhóm duy nhất kiểm được *độ đầy đủ chuỗi* |

**Căn cứ và cảnh báo.** Hai điều phải viết vào datasheet.

**(a) R2 là điều kiện ở tầng câu hỏi, nên máy chỉ sinh được ứng viên.** Người gán loại **24/50
dòng (48%)**, tức 8/16 lineage, với lý do áp đảo là `group_mismatch` (26 lần). Đây là nhóm duy
nhất κ có nghĩa (prevalence 0,12) và nó **đạt**: κ 0,684, p_pos 0,818, p_neg 0,857. Hai người
đồng ý, và họ đồng ý rằng gần một nửa dòng T3 là sai. Phép đo chữ ở tầng chuỗi cho cận trên quá
rộng: trường `substantive_transitions` cho 380/386 đạt ngưỡng ≥ 2, vì nó chỉ bắt hoa thường và
dấu câu, không bắt đổi tên cơ quan (139/790 lần chuyển, 56 trong số đó thuộc đợt sắp xếp bộ máy
2025). **Trữ lượng dùng được ước ≈ 190/386 lineage**, suy từ tỷ lệ người loại.

**(b) Vai trò "đo lợi ích của đồ thị" trong Bảng 1 không phải thuộc tính của nhóm.** Lợi ích của
đồ thị là một phép so sánh giữa các hệ thống, đo được trên mọi nhóm. Giữ nhãn Bảng 1, nhưng
datasheet phải ghi lại vai trò thật: **chọn phiên bản ở chuỗi dài**. Tiền lệ loại "chỉ sửa câu
chữ" là bộ tiếng Đức, nơi "editorial-only" là một trong các lý do loại được ghi lại.

### 2.4 T4 — bẫy gần trùng

| | |
|---|---|
| **Năng lực** | Chọn đúng phiên bản khi **sai cũng trông như đúng**: hai phiên bản khác nhau ở một đoạn ngắn nhưng đoạn đó quyết định đáp án |
| **Bậc cô lập** | `document` → `version`, ở chế độ khó phát hiện |
| **Điều kiện (ĐỀ XUẤT ĐỔI)** | Đúng 2 phiên bản; **đoạn thay đổi ngắn so với điều khoản** (`changed_span_ratio` dưới một ngưỡng đăng ký trước) **và** đoạn đó mang nội dung quyết định đáp án (số tiền, thời hạn, phạm vi, chủ thể) |
| **Điều kiện hiện tại (bị loại bỏ)** | `difflib.SequenceMatcher(...).ratio() ≥ 0,90` trên **toàn văn** |
| **Mốc hỏi** | Như T2 |
| **Đáp án đúng** | Như T2, và đáp án ngắn **phải** phủ đoạn thay đổi |
| **Chỉ số chính** | Accuracy tương phản, cộng **TVER và VCR** (trích dẫn đúng phiên bản) |
| **Không gộp được** | Chỉ ở nhóm này một câu trả lời sai mới *không phát hiện được bằng mắt*. Đó là chế độ lỗi riêng, dù cùng bậc thang với T2 |

**Vì sao đổi định nghĩa.** Bốn lý do, ba đã đo:

1. **Ngưỡng 0,90 là cắt tuỳ ý trên biến liên tục.** Cặp 0,91 thành T4, cặp 0,89 thành T2, hai
   nhóm quota riêng, không so được với nhau.
2. **`difflib` so theo ký tự nên không theo nghĩa.** Một khoản dài đổi một con số đạt trên 0,99;
   một khoản ngắn bị đổi tên cơ quan lại đạt thấp. Việc gán T2 hay T4 có thể **ngược**.
3. **Ngưỡng nằm sát một hiện vật của pipeline.** 2.132/19.192 cặp liền nhau (11,1%) giống hệt
   nhau về chữ và bị loại, **1.947 trong số đó là ứng viên T4**. Chưa rõ nguyên nhân là luật hay
   do cổng đã áp sẵn lời văn mới. T4 hiện sống trong một dải hẹp ngay cạnh lỗi đo đó.
4. **Không phép đo nào hiện tách được T4 khỏi T2.** Chữ ký probe (0,500 · 0,500 · 0,741 · 0,028)
   so với T2 (0,500 · 0,500 · 0,772 · 0,057): khác 3,1 pp với sai số khoảng ±8 pp. *Cảnh báo
   ngược:* các probe này biết trước điều khoản gold và chỉ chọn theo ngày, nên **về bản chất**
   không thể thấy độ giống. Đây là "không có bằng chứng", không phải "bằng chứng không có khác
   biệt". Phép đo đúng cần baseline có truy xuất.

Và người gán **không thống nhất được T4 xấu là thế nào**: κ 0,054, p_neg 0,143 — B gắn cờ 11 dòng,
A gắn 3, hai người chỉ đồng ý trên 1 dòng.

**Vai trò "đo ảo giác trích dẫn" trong Bảng 1 là một chỉ số, không phải nhóm.** TVER và VCR áp lên
mọi nhóm. Giữ nhãn, ghi lại vai trò thật trong datasheet.

**Phụ thuộc chưa xong.** `changed_span` hiện chỉ có trên **1.408/2.481 dòng (57%)** và giá trị mẫu
là một từ đơn ("các"), tức token diff chứ không phải đoạn. Trước khi dùng `changed_span_ratio` làm
điều kiện, phải xác định lại nội dung trường này và lấp 43% còn thiếu. **Nếu không làm được thì
giữ ngưỡng `difflib` và khai là giới hạn**, kèm phân bố độ giống để người đọc tự đánh giá —
cách TimelyRAG làm (độ tương đồng 0,61–0,73 so với 0,35–0,36 của CRAG và RealTimeQA).

### 2.5 T5 — ngày ký khác ngày hiệu lực

| | |
|---|---|
| **Năng lực** | Đáp án tại mốc t khi **không suy ra được từ ngày của văn bản**: văn bản đã có nhưng chưa là luật, hoặc đã là luật trước khi ai đọc được |
| **Bậc cô lập** | `none` → `document`, **bậc duy nhất hiện chưa được đo trên bảng chính** |
| **Điều kiện** | Văn bản tác động có `effective_from ≠ issued_on`. Hai chiều:<br>· `retroactive` — `effective_from < issued_on`<br>· `delayed` — `issued_on < effective_from` |
| **Mốc hỏi** | Một mốc **bên trong cửa sổ lệch**, cộng một mốc ngoài cửa sổ để tương phản |
| **Đáp án đúng** | `retroactive`: nội dung mới (đã có hiệu lực dù chưa công bố).<br>`delayed`: nội dung **cũ** — văn bản mới tìm được nhưng chưa là luật |
| **Chỉ số chính** | Accuracy tương phản, tách theo `effect_direction` |
| **Không gộp được** | Là nhóm duy nhất mà bậc `document` làm việc. Bỏ nó thì thang RQ3 chỉ còn ba bậc đo được |

**Hai điều phải đổi so với đề cương, và một đề xuất mở rộng.**

**(a) Bỏ vế "có lợi cho đối tượng áp dụng".** Trong Điều 152, "có lợi" là **điều kiện cho phép**
hồi tố, không phải thuộc tính làm bài toán hỏi đáp khó hơn. Đề cương trộn học thuyết pháp lý với
độ khó tác vụ. Nhóm đã tự bỏ vế này (quyết định Q3, 20/09) và đó là quyết định đúng.

**(b) `retroactive` không đủ làm nhóm, phải là tập chẩn đoán.** Toàn kho có 194 lineage từ 8 văn
bản tác động; sạch còn 148 từ **4 văn bản**; ba văn bản chiếm 151 lineage. Một văn bản có cửa sổ
hồi tố **2 ngày** nên không đặt được mốc giữa khoảng. Ở cỡ ~40 dòng, khoảng tin cậy Wilson rộng
khoảng ±15 pp. Đề xuất: **30–45 lineage, có trần theo văn bản đích, cố vấn ký từng ca, báo theo
cụm văn bản tác động, không tính vào trung bình macro, ghi rõ "minh hoạ"**. Tiền lệ biện hộ là
CALRK-Bench: chỉ 8/100 item về sửa đổi luật, và họ nêu thẳng rằng thay đổi phân loại rõ là hiếm
theo đúng bản chất, kèm tiêu chí loại trừ ("clarity bias").

**(c) Đề xuất mở rộng: thêm chiều `delayed`.** Đây là chỗ mình đề xuất **tăng phạm vi**, nên nói
rõ cả cái được và cái mất.

*Được.* Đo được: **3.856 lần chuyển có cửa sổ "đã ký nhưng chưa có hiệu lực" ≥ 30 ngày, trung vị
46 ngày, tối đa 554**; theo nhóm (≥30 ngày): T2 2.566 · T4 817 · T3 454 · T6 11 · T5 8. Đây là
bẫy khó nhất với RAG: văn bản mới đã nằm trên cổng, truy xuất được, nguyên văn đúng, **và chưa là
luật** — mọi tín hiệu truy xuất đều trỏ vào đáp án sai. Nó cũng là thứ **duy nhất** làm bậc
`document` đo được trên bảng chính. Và nó đối xứng với `retroactive` theo đúng mô hình hai thời
gian của SAT-Graph RAG (`validityInterval` so với `applicabilityInterval`).

*Mất.* Cần **mốc `as_of` thứ tư**, tức sửa `enrich_vilextime.py`, nhánh phân loại của
`check_release.py`, và ADR 0003 (đổi tập chế độ `as_of` là thay đổi MAJOR). Nó cũng đổi số dòng
mỗi lineage, nên phá phép tính tổng con (subset-sum) trong `sample_vilextime.select()` và các số
đã tinh chỉnh `RELEASE.update(T1=251, T3=199)`.

*Trạng thái hiện tại.* Giá trị `not_yet_in_force` đã có trong schema nhưng **0 dòng dùng**. Trường
`pending` vừa thêm (05/10) ghi nhận 4.840 dòng có phiên bản đã ký chưa hiệu lực, nhưng **cả 4.840
dòng đều có `days_until_effect = 1`** vì không mốc hỏi nào nằm sâu trong cửa sổ. Facet đúng, nhưng
suy biến: nó ghi nhận dạng yếu đã tồn tại, không tạo ra phép thử.

### 2.6 T6a — hết hiệu lực một phần, bãi bỏ trực tiếp

| | |
|---|---|
| **Năng lực** | Biết một khoản/điểm **đã hết hiệu lực** trong khi văn bản còn sống, khi có câu lệnh bãi bỏ đích danh |
| **Bậc cô lập** | `document` → `version`, ở chế độ **chấm dứt** (khác T2–T4 là chế độ **thay thế**) |
| **Điều kiện** | Cấp Khoản hoặc Điểm; phiên bản cuối có `effective_to` **và** `ended_by_event_id`; văn bản đích còn hiệu lực tại mốc hỏi |
| **Mốc hỏi** | `[kết thúc − 1, kết thúc]` |
| **Đáp án đúng** | Phụ thuộc `norm_continuity` (mục 3) |
| **Chỉ số chính** | Recall và precision của việc **từ chối**; điểm +1/0/−1 kiểu CRAG để phạt nặng việc tự tin trích văn bản đã bãi bỏ |
| **Không gộp được** | T2–T4 kiểm *đổi nội dung*; T6a kiểm *không còn nội dung*. Loại đáp án đúng khác nhau (một phiên bản cụ thể so với từ chối trả lời), nên gộp sẽ phá construct validity của cả hai |

### 2.7 T6b — hết hiệu lực lan truyền từ đơn vị cấp trên (H3)

| | |
|---|---|
| **Năng lực** | Biết một khoản/điểm đã hết hiệu lực **dù không ai nhắc tới nó**, vì Điều/Khoản/Mục/Chương chứa nó bị bãi bỏ |
| **Bậc cô lập** | `version` → `propagated`. **Chỉ bậc 4 bắt được.** Đây là H3 |
| **Điều kiện** | Cấp Khoản hoặc Điểm; phiên bản cuối có `effective_to` nhưng `ended_by_event_id` **rỗng** và `valid_to` rỗng; tồn tại đơn vị cấp trên bị bãi bỏ đúng ngày đó (`repealed_by` giải được) |
| **Mốc hỏi** | Như T6a |
| **Đáp án đúng** | Như T6a |
| **Chỉ số chính** | Như T6a, cộng **TV-Recall@1** trên đường dẫn bằng chứng của đơn vị cấp trên |
| **Không gộp được** | **Bậc thang khác T6a.** Gộp hai cơ chế thì khi báo "T6 đạt 70%" không ai biết 70% đến từ đâu, và nếu hệ thống giỏi T6a mà dở T6b thì che mất đúng kết quả quan trọng nhất của bài báo |

**Căn cứ cho việc tách.** Kho có **14.157 đơn vị mất hiệu lực chỉ vì đơn vị cấp trên bị bãi bỏ, so
với 6.001 bị bãi bỏ trực tiếp (2,4 lần)**. Bảng ở mục 1 cho thấy T6 vỡ làm ba và chỉ **23 dòng**
bảng chính cần bậc `propagated`. Bản phát hành cũ chỉ có **12 lineage** H3, sai số khoảng ±25 pp,
nên H3 chỉ ở mức minh hoạ. Sau khi sửa thứ tự ghi và bỏ trần (05/10): **10.053 lineage đủ điều
kiện, pool giữ 2.000 trên 365 văn bản**, tầng xếp hạng cấp được **200 lineage trên 150 văn bản**.
Ở 200 lineage, MDE ghép cặp vào khoảng 8–9 pp, tức H3 chuyển từ minh hoạ thành **giả thuyết kiểm
được**.

**Cảnh báo khi báo cáo.** Chữ ký probe riêng của T6 (ngày gần nhất chỉ 0,500 trong khi các nhóm
khác 0,7+) **một phần là hiện vật**: `ask_dates` cho T6 mốc `[kết thúc − 1, kết thúc]`, nên đúng
một nửa số dòng không có đáp án. Phải nói điều này trong datasheet.

---

## 3. Quy tắc đáp án cho T6a và T6b: chuyển chỗ nội dung

Cố vấn luật chốt ngày 05/10. Mọi câu hỏi ViLexTime là câu hỏi **nội dung**, vì
`prompts/vilextime/base.md` cấm dẫn Điều/Khoản. Nên:

| `norm_continuity` | Điều kiện | Đáp án đúng | Dòng còn là phép thử từ chối? |
|---|---|---|---|
| `none` | Không tìm thấy quy phạm kế thừa | Rỗng, `no_answer_reason = provision_repealed` | Có |
| `moved` | Hành vi, đối tượng, điều kiện giữ nguyên **về bản chất**; chỉ đổi vị trí, có thể kèm đổi mức phạt hoặc thời hạn | Quy định tại `successor` | **Không** |
| `unclear` | Không chắc | Tạm loại khỏi bảng chính, giữ ở tập phụ | — |

Bốn điểm cố vấn đã chốt: (1) hỏi theo cấu trúc thì trả "đã bãi bỏ", hỏi theo nội dung thì trả quy
phạm đang điều chỉnh; (2) khoản bị bãi bỏ vẫn là đã bãi bỏ dù cơ chế tương tự còn ở khoản khác;
(3) **đổi mức phạt không tự thân thành quy phạm mới, và không đặt ngưỡng "tăng bao nhiêu"** — phải
đối chiếu hành vi, đối tượng, điều kiện, cấu trúc; (4) chuyển sang văn bản khác vẫn là chuyển chỗ
nếu quy định mới thực sự tiếp tục điều chỉnh nội dung cũ.

`substantive_change` **không gán tay**, suy từ so sánh văn bản khi phân tích.

**Trạng thái.** 25 dòng / **20 lineage** nghi chuyển chỗ, trong đó **2 đã đối chiếu văn bản thô**,
18 chưa kiểm (`data/inter-annotator-agreement/audit_queue_relocation.tsv`). Con số 25 là lọc từ
khoá trên ghi chú của người gán B, chưa kiểm từng dòng, và hàng audit chỉ phủ 61/112 dòng T6 nên
**số thật có thể cao hơn**. Hệ quả: số dòng T6 "xoá hẳn thật" có thể thấp hơn 112 nhiều, và phép
thử từ chối của T6 yếu đi tương ứng.

---

## 4. Trường cắt ngang

Các biến này **không** sinh nhóm. Mọi dòng mang chúng, và mọi phân tích là một lát cắt.

| Trường | Giá trị | Nguồn | Vì sao không là nhóm |
|---|---|---|---|
| `n_versions` | số nguyên | máy | Biến rời rạc; T1/T2/T3 là ba lát của nó |
| `similarity`, `similarities` | 0–1 mỗi lần chuyển | máy | Biến liên tục; T4 là một lát |
| `changed_span_ratio` | 0–1 | máy (**chờ lấp 43%**) | Điều kiện đề xuất cho T4 |
| `substantive_transitions` | số nguyên | máy | Cận trên ở tầng chữ cho R2 |
| `norm_continuity`, `successor` | none / moved / unclear | **người** | Quyết định đáp án, không quyết định nhóm |
| `answer_direction` | gold là bản mới nhất / bản cũ hơn | máy | Trục cắt ngang **bắt buộc** (xem dưới) |
| `value_in_current` | bool | máy | Cờ rò, không phải nhóm |
| `effect_direction` | aligned / retroactive / delayed | máy | T5 là hai lát của nó |
| `op_type` | amend / supplement / replace | máy | Hiện 100% là `amend` |
| `as_of_mode` | ranh_gioi / giua_khoang / sau_het_hieu_luc (+ chế độ thứ tư nếu mục 2.5c được chấp nhận) | máy | Chế độ, không phải nhóm |
| `question_source` | human / llm_edited / llm_unedited | máy | Cho ablation theo nguồn câu hỏi |

**`answer_direction` là trục bắt buộc, không phải tuỳ chọn.** Tỷ lệ dòng có gold chính là bản mới
nhất: T1 251/251 (100%) · T6 56/56 (100%) · T2 200/400 (50%) · T4 75/150 (50%) · T5 19/38 (50%) ·
T3 65/199 (33%). Một hệ thống thiên về bản mới nhất được 100% ở T1 và T6, 50% ở T2. Nên **so điểm
giữa các nhóm mà không tách theo trục này là so sai**: nó lẫn "nhóm khó hơn" với "nhóm dễ ăn điểm
nhờ thiên vị bản mới". Đơn vị phân tích là **nhóm × `answer_direction`**. Tiền lệ: TALD tách án
theo luật cũ (0,014–0,237) và luật mới (0,70–0,843), và 69–94% lỗi là áp luật mới cho tình huống
thuộc luật cũ.

---

## 5. Cổng hợp lệ: ràng buộc chặt

Mọi dòng vào bản phát hành phải qua tám cổng. Cổng nào trượt thì dòng bị loại hoặc gắn cờ, **và
đếm lại trong datasheet** (phễu có số lượng ở mọi bước là hình bắt buộc của các bộ được nhận).

| Cổng | Nội dung | Trạng thái |
|---|---|---|
| **G-A** | Mọi phiên bản có ngày hiệu lực | ✅ đã có trong `classify` |
| **G-B** | Đáp án **khác nhau** ở các mốc của dòng | ✅ đã có (1.947 ca T4 và 72 ca T3 bị loại) |
| **G-C** | Không mốc nào sau ngày chụp corpus | ✅ sửa 05/10 (40 → 0 dòng) |
| **G-D** | Lần chuyển không chỉ là hoa thường, dấu câu, khoảng trắng | ✅ `substantive_transitions`, `cosmetic_change` |
| **G-E** | Đáp án vàng **không** xuất hiện nguyên văn trong phiên bản hiện hành | ⬜ **chưa có.** Đo được: 33 dòng (3,0%) bị rò. Theo FiscalQA, nhưng **gắn cờ chứ không xoá**, và báo bảng chính cả khi có lẫn không có |
| **G-F** | Mốc hỏi không bị ghim vào một độ lệch cố định quanh ranh giới | ✅ T3 dời 29/09, T1 dời 05/10 |
| **G-G** | Câu hỏi qua `validate()`: không nhắc thời gian, không dẫn vị trí, không chép đáp án, không bịa số | ✅ 10 cổng, tỷ lệ giữ 81,1% |
| **G-H** | Người gán cho `dat`, sau khi đạt **cổng hiệu chỉnh ≥ 85% trên 50 mẫu pilot** | ⬜ **chưa có cổng hiệu chỉnh.** Đây là chỗ κ pilot trượt |

**Hai cổng còn thiếu là hai chỗ yếu nhất.** G-E là bộ lọc rẻ (regex) mà FiscalQA dùng để bảo đảm
mọi câu đều **không** trả lời được bằng bản hiện hành. Ngoài 33 dòng rò, còn một con số lớn hơn:
**666/1.094 dòng bảng chính (61%) có gold chính là bản mới nhất**, nên một hệ thống chỉ biết bản
hiện hành đã đúng ở chừng đó dòng. Vì vậy datasheet phải báo thêm **bảng con "nhạy thời gian"**:
dòng có gold khác bản mới nhất và không rò, khoảng **395 dòng**. Đây mới là bảng so được với con
số 2,7% của RAG tĩnh ở FiscalQA.

G-H là lý do κ pilot chỉ đạt p_o 0,700 / κ 0,236. VLegal-Bench đạt 92,39% và κ 0,89 **không** vì
người gán giỏi hơn, mà vì có tập huấn 2 ngày, 50 mẫu pilot có phản hồi tức thời, và cổng ≥85%
trước khi gán chính thức. Pilot của ViLexTime là lượt gán đầu **không có cổng đó**.

---

## 6. Ánh xạ về Bảng 1 đề cương

Bản UIT đã nộp không sửa được, nên **giữ nguyên sáu nhãn T ở tầng trình bày**. Bảng lệch trong
datasheet phải có các dòng sau.

| Bảng 1 | Định nghĩa chốt | Loại lệch |
|---|---|---|
| T1 "Đối chứng", 250 | Đối chứng tĩnh, vai trò **locality**; mốc hỏi đã dời; đề xuất 150 | Vai trò mô tả lại; quota |
| T2 "Nhóm cốt lõi", 400 | Chọn phiên bản, độ khó nền | Không lệch |
| T3 "Đo lợi ích của đồ thị", 200 | Chọn phiên bản ở chuỗi dài, **R2 ở tầng câu hỏi**; trữ lượng dùng được ≈190 | Vai trò mô tả lại; trữ lượng |
| T4 "Đo ảo giác trích dẫn", 150 | Bẫy gần trùng, **định nghĩa trên đoạn thay đổi** thay cho ngưỡng độ giống toàn văn | Vai trò mô tả lại; điều kiện |
| T5 "Trường hợp khó", 50 | Ngày ký khác ngày hiệu lực; bỏ vế "có lợi"; `retroactive` 30–45 là **chẩn đoán**; đề xuất thêm chiều `delayed` | Định nghĩa; quy mô; mở rộng |
| T6 "Hiệu lực cấp điều khoản", 100 | **Tách T6a trực tiếp và T6b lan truyền**; đáp án theo `norm_continuity` | Tách nhóm; quy tắc đáp án |

---

## 7. Ánh xạ về các bộ đã công bố

Để phản biện thấy thiết kế không phải tuỳ ý. (Mình đọc phần lớn các bài này qua công cụ tóm tắt
tự động, nên **kiểm lại con số với bài gốc trước khi trích vào bài báo**.)

| Thành phần ViLexTime | Tiền lệ |
|---|---|
| Nhóm tĩnh làm đối chứng | SituatedQA "Static", TemporalWiki "Unchanged", FreshQA "never-changing" |
| Vai trò locality cho T1 | LeKUBE, chiều *locality* trên 60 điều không sửa |
| Chia nhóm theo năng lực | LexKairos (identification / verification / reasoning), bộ tiếng Đức (hai chế độ lỗi) |
| Quan hệ biến hình của T2, TCS | LawShift (metamorphic testing, không cần nhãn vàng), TimeQA (nhất quán khi đổi mốc: 66%) |
| Loại "chỉ sửa câu chữ" ở T3 | Bộ tiếng Đức, lý do loại "editorial-only" |
| Độ giống giữa phiên bản là thống kê của bộ dữ liệu | TimelyRAG (0,61–0,73 so với 0,35–0,36) |
| Hai thời gian ở T5 | SAT-Graph RAG (`validityInterval` so với `applicabilityInterval`) |
| Biện hộ nhóm nhỏ cho T5 | CALRK-Bench (8/100 item, nêu rõ tiêu chí loại trừ) |
| Cổng G-E | FiscalQA (giá trị vàng không nằm trong bản hiện hành) |
| Trục `answer_direction` | TALD (án luật cũ 0,014–0,237 so với luật mới 0,70–0,843) |
| Cổng hiệu chỉnh G-H | VLegal-Bench (2 ngày, 50 mẫu, ≥85%) |
| Tách T6a/T6b | Không bộ nào làm ở cấp khoản/điểm — **đây là chỗ đóng góp** |

**Định vị đứng được:** benchmark point-in-time **đầu tiên cho luật Việt Nam**, ở **cấp khoản/điểm**,
có **bãi bỏ một phần** và **hiệu lực lan truyền từ đơn vị cấp trên**, có **độ đồng thuận giữa người
với người**. Không viết "đầu tiên" hay "lớn nhất" nói chung: LexKairos có 3.796 item, TALD có
26.000 bản án, VLegal-Bench đã có đồ thị theo dõi sửa đổi.

---

## 8. Quota đề xuất và những gì cần ký

### 8.1 Quota

Lấy MDE ghép cặp (α = 0,05, power 0,8) làm căn cứ: n = 150 cho ~10,1 pp · n = 200 cho ~8–9 pp ·
n = 300 cho ~7,2 pp.

| Nhóm | Đề xuất (lineage) | Lý do |
|---|---:|---|
| T1 | **150** | ±7,9 pp đủ cho vai trò locality; 100 lineage tiết kiệm chuyển sang T6b |
| T2 | **300** | Nhóm nền, không cắt |
| T3 | **~190, sàn 130** | Trữ lượng thật sau khi người lọc; pool đã lấy hết |
| T4 | **150** | Giữ như đề cương, chờ `changed_span_ratio` |
| T5 `retroactive` | **30–45** | Chẩn đoán, cố vấn ký, không tính macro |
| T5 `delayed` | **100–150** *(nếu mục 2.5c được chấp nhận)* | Làm bậc `document` đo được |
| T6a | **200** | Chế độ chấm dứt trực tiếp |
| T6b | **200** | H3 kiểm được ở MDE 8–9 pp |

### 8.2 Năm điều cần ký trước khi đóng băng

| # | Quyết định | Đề xuất của mình | Ai quyết |
|---|---|---|---|
| 1 | "Câu" là lineage hay dòng QA | Đếm theo lineage cho bài báo, báo cả hai số | **Khoa** |
| 2 | Tách T6 thành T6a/T6b trong schema | Có — hai bậc thang khác nhau | Nhóm |
| 3 | Đổi điều kiện T4 sang `changed_span_ratio`, hay giữ ngưỡng `difflib` và khai giới hạn | Đổi **nếu** lấp được 43% `changed_span`; nếu không thì giữ và khai | Nhóm |
| 4 | Thêm chiều `delayed` cho T5 (mốc `as_of` thứ tư, ADR 0003 MAJOR) | Có, vì nó là bậc thang duy nhất còn hụt — nhưng đây là **mở rộng phạm vi** và tốn công rõ rệt | Nhóm |
| 5 | Tiêu chí `khong_dat` cho T2, T3, T4 | Chưa có — **còn chờ cố vấn** | **Cố vấn** |

Sau khi ký, đổi định nghĩa một nhóm là thay đổi **MAJOR** theo ADR 0003 (đổi gold hoặc chuyển
dòng giữa các split) và buộc gán lại nhãn. Vì vậy ba điều kiện đóng băng là: guideline v2.0 có
tiêu chí `khong_dat` cho đủ bốn nhóm và cố vấn ký · quyết định 1 và quota được khoa chấp nhận ·
đạt cổng hiệu chỉnh G-H trên 50 mẫu pilot.

### 8.3 Không thuộc phạm vi

Để khỏi mở rộng: câu hỏi nhiều điều khoản (bộ tiếng Đức có, ViLexTime chưa có hiện tượng — khai
trong Limitations) · `supplement` và `replace` (5.095 và 2.211 event trong kho, 0 dòng trong bản
phát hành — khai trong Limitations) · track tác vụ siêu dữ liệu kiểu LexKairos (bổ sung cho bài
báo, không tính vào M3) · văn bản địa phương.
