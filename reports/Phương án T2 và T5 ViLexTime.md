# Phương án nghiên cứu cho T2 và T5 của ViLexTime

Soạn 08/10/2026. Nền: bốn ghi chú nghiên cứu trong `research_notes/Phương án T2 và T5 ViLexTime/`
(contrast sets · thống kê ghép cặp và phân cụm · tập chẩn đoán nhỏ · hồi tố và trường-hay-nhóm),
cộng các phép đo mình chạy trực tiếp trên `data/derived/vilextime/` và `data/vilextime/` ngày 08/10.

**Về độ tin cậy của trích dẫn.** Mọi nguồn do các nhánh nghiên cứu thu thập; người điều phối (mình) **chưa
tự mở lại** nguồn gốc. Nhãn đi kèm là mức xác minh do chính nhánh đó ghi:
`[toàn văn]` đã đọc nội dung bài · `[trang]` chỉ đọc abstract hoặc trang mô tả · `[snippet]` chỉ thấy đoạn tóm tắt của máy tìm kiếm,
**là manh mối, chưa được trích** · `[tự suy ra]` do người nghiên cứu hoặc mình tự dẫn xuất, không có nguồn · `[đo]` mình đo trên dữ liệu repo.
Mục 8 gom mọi thứ chưa xác minh.

---

## 0. Kết luận trước

1. **T2 giữ nguyên là nhóm lõi và đã có tên chuẩn cho chỉ số của nó.** TCS chính là *contrast consistency* của Gardner et al. 2020 với nhóm cỡ 2.
 Trích nguồn thay vì tự đặt tên. Tránh gọi "pair accuracy" vì từ đó mang nghĩa khác trong dịch máy và BLiMP.
2. **T2 gần như không bị phân cụm** `[đo]`: 225 lineage đến từ 191 văn bản đích, 157 văn bản chỉ có 1 lineage. Design effect chỉ 1,02–1,15 kể cả khi giả định ρ = 0,5.
 Nghĩa là phần thống kê khắt khe về phân cụm **không phải gánh nặng của T2**. Dùng bootstrap theo lineage, báo MDE 5,9–10,2 điểm phần trăm cho 225 cặp.
3. **T5 tệ hơn mọi con số đã nêu** `[đo]`: 19 lineage có câu hỏi, 38 dòng, thuộc **3 văn bản tác động**, một văn bản chiếm 10/19 lineage. Với 3 cụm, wild cluster bootstrap
 chỉ cho 4 giá trị |t| khác nhau, p nhỏ nhất đạt được là **0,25**. T5 **không thể** được dùng để kết luận hay xếp hạng hệ thống. Nó chỉ mô tả được.
4. **Không có luật venue nào cấm ship T5 ở cỡ này.** ARR, checklist trách nhiệm NLP và NeurIPS 2026 E&D đều **không đặt sàn cỡ mẫu**. Thứ bị cưỡng chế là *công bố*
 (mục Limitations, thống kê số lượng). Phản biện nào bảo n = 38 dưới mức bắt buộc là đang phát minh ra luật.
5. **Hồi tố chưa từng được đánh giá** trong point-in-time QA, theo mọi thứ nhánh nghiên cứu tìm được. Ít nhất hai công trình 2026 nêu tên nó trong động cơ rồi không đánh giá, và một benchmark thứ ba không bàn tới.
 Claim được, nhưng phải claim hẹp: "đầu tiên *đánh giá* hồi tố", không phải "đầu tiên nhận ra". Chuẩn legal informatics (Akoma Ntoso) đã tách hai cặp ngày từ lâu, đó là thế bất đối xứng để dựng động cơ.
6. **Khuyến nghị cho T5 là (c) + (a), và (b) làm chế độ `as_of` bổ sung chứ không thay suất quota.**
 Hồi tố thành *trường* trên mọi dòng, 38 dòng T5 hiện có ship như *tập chẩn đoán có tên, không điểm tổng*.
 Còn `not_yet_in_force` (bẫy mạnh nhất, đã có tên "future-law leakage" trong văn liệu) dựng thêm như chế độ `as_of` thứ tư cho **155 lineage T2 đã có**,
 không cần câu hỏi mới. Mục 5 giải thích và nêu rõ chỗ mình **sửa lại một điều đã nói trước đó trong phiên**.
7. **Một phát hiện chặn việc nghĩ rằng T2 đã chứa sẵn bẫy "chưa hiệu lực"** `[đo]`: 172/450 dòng T2 mang `pending`, nhưng khoảng cách tới ngày hiệu lực **luôn đúng 1 ngày**. Đó là bẫy biên, không phải bẫy thật.

---

## 1. T2 — cặp tương phản theo thời gian

### 1.1 Định nghĩa và dựng

Một dòng T2 là một **cặp**: cùng một câu hỏi, hai mốc `as_of` nằm hai bên một lần sửa đổi, hai đáp án khác nhau. Câu hỏi giống nhau *từng ký tự* giữa hai mốc; thứ đổi là ngày.
Trường độ khó đã gắn trên mọi dòng và đã tới bản ghi cấp phát hành `[đo]`: `similarity`, `n_versions`, `chance_accuracy`, `near_identical`, `min_repr`, `norm_continuity`.

Theo văn liệu contrast sets, T2 là một **contrast set cỡ 2** (pivot = bản trước sửa đổi, một nhiễu = bản sau). Gardner et al. 2020 có đúng cấu hình này:
IMDb (488 ví dụ / 488 tập) và PERSPECTRUM (217/217) là một nhiễu cho mỗi pivot `[toàn văn]`, nên cặp không cần biện hộ riêng.
Tiền lệ về thời gian: **TORQUE** (Ning et al., EMNLP 2020, contrast set trên câu hỏi thứ tự thời gian) và tập MATRES trong chính bài Gardner, nơi sửa một token đảo nhãn thời gian `[toàn văn theo ghi chú]`.

Hai tính chất thiết kế đáng nói rõ trong bài, vì chúng trả lời đúng phê bình chính nhắm vào contrast sets:

- **Không có văn phong người gán để model bắt bài.** Nhiễu là một lần sửa luật thật cộng một thay đổi ngày, không phải annotator viết lại câu. (Phê bình gốc về annotator artifact không áp dụng.)
- **Hoàn hảo tối thiểu về phía câu hỏi, không tối thiểu về phía bằng chứng.** Chuỗi câu hỏi giống hệt, văn bản luật khác. Mức khác đó chính là `similarity`, nên phải báo `similarity` như một trường chứ không giấu.
Bằng chứng cho thấy độ giống bề mặt và khác biệt pháp lý quyết định cùng tồn tại: NLLP 2025 báo chuỗi sửa đổi giống nhau 93–99% nhưng chỉ 50,3% khớp chính xác cho sửa đổi một bước và 20,51% cho nhiều bước `[snippet, chưa mở bài]`.

### 1.2 Chỉ số: *contrast consistency*

Định nghĩa nguyên văn, Gardner et al. 2020, §2.2 (*Findings of EMNLP 2020*, tr. 1307–1323, DOI 10.18653/v1/2020.findings-emnlp.117) `[toàn văn]`:

> "we define the **contrast consistency** of a model to be whether it makes correct predictions ŷ on every element in the set: all({ŷ = y′ ∀(x′, y′) ∈ C(x)})"

Dạng vận hành, chú thích Bảng 2 `[toàn văn]`:

> "the percentage of the '# Sets' contrast sets for which a model's predictions are correct for all examples in the set (*including* the original example)"

Hệ quả cho T2:

- **TCS = contrast consistency với |C(x)| = 1.** Không phải chỉ số mới. Trích Gardner 2020 làm nguồn gốc.
- Phải báo *"đúng ở cả hai mốc"*, **không** báo "đúng mốc sau với điều kiện đúng mốc trước". Hai thứ khác nhau và chỉ thứ đầu là contrast consistency, vì chú thích Bảng 2 đếm cả ví dụ gốc.
- Tên phụ: *group score / group accuracy*, `groupScore(xᵢ) = min_j f(xᵢⱼ)` (Elazar et al. 2021). TORQUE có biến thể ngưỡng ("F1 ≥ 80% cho mọi câu trong nhóm") nếu sau này điểm từng dòng là điểm mềm.
- **Tránh** "pair accuracy" (nghĩa khác trong meta-đánh giá dịch máy và BLiMP) và "joint accuracy" (đã bị dialogue state tracking chiếm). Không tìm được nguồn gốc chuẩn cho "set accuracy" hay "joint accuracy" trong dòng này.

**In TCS cạnh p².** Nếu hai mốc độc lập thì TCS kỳ vọng bằng p², với p là độ chính xác từng dòng. Đặt hai số cạnh nhau cho người đọc biết trả đúng mốc 1 có giúp gì cho mốc 2 không.
Trong IMDb của Gardner, quan sát 77,8% so với p² = 79,2%, gần sát độc lập `[tự suy ra bởi người nghiên cứu, chưa có nguồn nào làm việc này]`.
Cũng báo **mức ngẫu nhiên**: chọn phiên bản ngẫu nhiên cho `chance_accuracy` = 1/2 mỗi mốc, nên sàn TCS là 0,25. Nêu cả hai để chặn phản biện "khoảng cách này chỉ là số học".

**Lá chắn mạnh nhất cho chỉ số ghép là khoảng cách người–máy.** Trên TORQUE, khoảng cách giữa đúng-từng-dòng và đúng-cả-nhóm là 16,6 điểm với RoBERTa-large nhưng chỉ 2,0 điểm với người (84,5 → 82,5)
`[toàn văn theo ghi chú; mình chưa tự kiểm lại bảng]`. Trên 10 bộ của Gardner, consistency thấp hơn accuracy trên tập nhiễu 6–31 điểm. Nếu có thể, đo người trên một mẫu T2 để có đúng số này cho ViLexTime.

### 1.3 Cỡ mẫu và lực thống kê

**Không có bài nào trong dòng contrast sets làm phân tích lực.** Đó là phát hiện, không phải thiếu sót của tìm kiếm. Căn cứ thay thế:

- Tiền lệ cỡ: các contrast set đã công bố có **70 đến 974 nhóm** (BoolQ nhỏ nhất, ROPES lớn nhất), mục tiêu thiết kế ~1.000 ví dụ `[toàn văn]`. 225 lineage nằm giữa dải đó.
- Độ chính xác nhị thức trên *cặp* làm đơn vị `[đo, công thức chuẩn]`: nửa độ rộng KTC 95% tệ nhất (p = 0,5) là **±6,5 điểm** cho N = 225, ±8,0 cho N = 150.
- Tổng quát về lực của tập test: Card et al. (EMNLP 2020), Bowman & Dahl (NAACL 2021) `[trang]`.

**MDE cho so sánh hai hệ thống trên cùng các cặp** (công thức mục 2.5; 80% lực, α = 0,05 hai phía), điểm phần trăm, `[đo — mình chạy cả công thức xấp xỉ lẫn Connor đầy đủ, lệch ≤ 0,1]`:


| N cặp   | p_d = 0,10 | p_d = 0,20 | p_d = 0,30 |
| -------: | ----------: | ----------: | ----------: |
| 150     | 7,2        | 10,1       | 12,4       |
| **225** | **5,9**    | **8,3**    | **10,2**   |


`p_d` là tỷ lệ cặp mà đúng một trong hai hệ thống đạt TCS ("discordant"). Chưa có kết quả hệ thống nên chưa biết `p_d` thật; bảng cho dải hợp lý.
Đọc: với 225 cặp, hai hệ cách nhau dưới ~6–10 điểm TCS thì **không phân biệt được**. Đừng viết câu kết luận nào dựa trên chênh lệch nhỏ hơn.

### 1.4 Phân cụm của T2 — đo thật, và nó nhẹ

`[đo]` 225 lineage (225 đầu theo hạng, có câu hỏi) từ 191 văn bản đích. Cỡ cụm trung bình 1,18, lớn nhất 2, CV = 0,32. `m_adj = m̄(CV² + 1) = 1,30`.


| giả định ρ | DE = 1 + (m_adj − 1)ρ | n_eff | √DE  |
| ----------: | ---------------------: | -----: | ----: |
| 0,05       | 1,02                  | 222   | 1,01 |
| 0,20       | 1,06                  | 212   | 1,03 |
| 0,50       | 1,15                  | 195   | 1,07 |


Hệ quả thực hành: **MDE của T2 gần như là MDE độc lập**, nhân cùng lắm 1,07. Với K = 191 cụm, các phương pháp dựa trên K → ∞ là hợp lệ ở đây (ngưỡng đồng thuận trong tài liệu là G ≈ 50, mục 2.2).
ρ thật chưa ước được vì chưa có kết quả hệ thống; ước sau bằng estimator ANOVA (mục 2.1) và báo kèm.

### 1.5 So sánh hai hệ thống trên T2

Đơn vị là *lineage* (cả hai dòng của cặp và các dòng anh em `giua_khoang` dùng chung câu hỏi nên không độc lập). Biến là "TCS đúng/sai" cho mỗi hệ.

- McNemar thường là hợp lệ **khi các cặp độc lập**; mẫu số `b + c` chính là giả định độc lập (mục 2.4).
- Vì cụm của T2 gần như đơn lẻ, thống kê cluster-robust của Durkalski (2003) co về McNemar (khi mọi cụm có đúng một cặp thì chúng trùng khít, chứng minh đại số ở mục 2.4 `[tự suy ra]`).
Đề nghị: báo McNemar chính xác, và báo thêm Durkalski/Yang như kiểm tra độ bền. Hai kết quả gần nhau là điều **dự kiến** `[tự suy ra từ m̄ = 1,18]`, và chỗ chúng khác nhau sẽ đáng chú ý.
- Nhiều nhóm so sánh cùng lúc: sửa Holm hoặc Benjamini–Hochberg (Dror et al. 2018 `[toàn văn]`).
- Không tìm được bài contrast-set nào dùng McNemar. Đây là nâng cấp phương pháp chứ không phải tiền lệ.

### 1.6 Điều T2 **không** phải tự hào

- **Bẫy "chưa hiệu lực" trong T2 chỉ là bẫy biên** `[đo]`. 172/450 dòng (225 lineage đầu) mang `pending`, nhưng `days_until_effect` luôn bằng 1, không dòng nào ≥ 30 ngày.
Lý do: dòng "trước" của cặp hỏi ở `start − 1`. Một hệ lọc theo ngày hiệu lực giải được trivially. Đừng mô tả T2 là "đo future-law leakage".
- 36/450 dòng T2 (8%) có `min_repr = cross_document`, 414 là `clause_version`. T2 gần như chỉ cần chuỗi phiên bản cấp khoản (I1), đúng với vai trò "nhóm lõi", nhưng nghĩa là T2 **không** phân biệt được biểu diễn đồ thị với lọc siêu dữ liệu ở cấp văn bản nhiều như T6.
- Định nghĩa cặp theo chế độ `as_of` (biên so với giữa khoảng) cần chốt trong guideline; datasheet đang lấy bảng `giua_khoang` làm bảng chính.

---

## 2. Thống kê cho dữ liệu vừa ghép cặp vừa phân cụm

Mục này chủ yếu **để T5 và để biện hộ nếu bị hỏi**; T2 gần như không cần (mục 1.4).

### 2.1 Design effect và cỡ mẫu hiệu dụng

Cỡ cụm bằng nhau, Killip, Mahfoud & Pearce, *Ann Fam Med* 2004;2(3):204–208 (Công thức 2–3) `[toàn văn]`:

```
DE    = 1 + (m − 1)·ρ
n_eff = m·k / DE            (k cụm, mỗi cụm m phần tử)
ρ     = σ²_between / (σ²_between + σ²_within)
```

Giả định: cụm bằng nhau, tương quan hoán đổi được trong cụm, một tầng lồng. Khi ρ = 1: *"the effective sample size therefore reduces to k, the number of clusters"* (cùng bài).

Cụm không bằng nhau: dạng CV `DE = 1 + (m̄(CV² + 1) − 1)·ρ`, với `m̄ = n/k`, `CV = sd(m_i)/m̄`. Dạng này đồng nhất đại số với hiệu chỉnh của Moulton (1986, tr. 387)
`V[N_g]/N̄_g + N̄_g − 1` được trích trong Cameron & Miller (*J. Human Resources* 2015) `[toàn văn]`; **phép đồng nhất là đại số của người nghiên cứu** `[tự suy ra]`.
Gán cho Eldridge, Ashby & Kerry (2006, *Int J Epidemiol* 35:1292–1300) chỉ thấy trên một trang thương mại, **chưa đọc bài gốc** `[snippet]`; dùng Moulton làm nguồn chính.

Ước ρ cho biến nhị phân: estimator ANOVA `ρ̂ = (BMS − WMS)/(BMS + (m₀ − 1)·WMS)`, hợp lệ cho nhị phân theo Ridout, Demétrio & Firth, *Biometrics* 1999 `[trang]`.
Chưa tìm được nguồn nói ρ nhị phân bị chặn bởi tần suất ở mức ~85% "đạt" ra sao `[khoảng trống]`.

### 2.2 Có bao nhiêu cụm thì đủ?

Cameron & Miller 2015 `[toàn văn]` không đưa ngưỡng cứng ("càng nhiều càng tốt"; đồng thuận G = 50) nhưng báo hai bộ mô phỏng, tỷ lệ bác bỏ sai so với danh nghĩa 0,05:


| G        | 50    | 20    | 10    | 6     |
| -------- | -----: | -----: | -----: | -----: |
| BDM 2004 | 0,063 | 0,058 | 0,080 | 0,115 |



| G        | 30    | 20    | 10    | 5     |
| -------- | -----: | -----: | -----: | -----: |
| CGM 2008 | 0,068 | 0,081 | 0,118 | 0,208 |


Carter, Schnepel & Steigerwald (2013): "số cụm hiệu dụng" `G* = G/(1+δ)`, méo kích thước đáng kể khi **G\* < 20** `[trang]`. T5 vi phạm điều này ngay từ cấu trúc.

### 2.3 Cluster bootstrap

- Resample **nguyên cụm** (có hoàn lại), giữ mọi quan sát của cụm. Không tìm được nguồn nào ủng hộ "resample cụm rồi resample phần tử trong cụm" `[toàn văn]`.
- *Pairs cluster bootstrap* **thất bại** khi ít cụm: tỷ lệ bác bỏ 0,005 ở G = 6 so với danh nghĩa 0,05 `[toàn văn]`.
- Thay bằng **wild cluster bootstrap-t, áp H₀, trọng số Rademacher** (Cameron & Miller §VI.C.2); G < 10 dùng trọng số sáu điểm của Webb (2013).
- **Giới hạn cứng**: chỉ có `2^(G−1)` giá trị |t| khác nhau (Webb 2013, theo Cameron & Miller). Do đó p nhỏ nhất đạt được là `1/2^(G−1)` `[tính từ công thức đã trích]`:

| G | giá trị |t| | p nhỏ nhất |
|---:|---:|---:|
| **3** | 4 | **0,2500** |
| 4 | 8 | 0,1250 |
| 8 | 128 | 0,0078 |
| 11 | 1.024 | 0,0010 |

Với G nhỏ nên **liệt kê hết** `2^G` dấu thay vì lấy mẫu. Phương án khác khi rất ít cụm: Ibragimov & Müller (2010), Donald & Lang (2007), permutation.

### 2.4 McNemar khi dữ liệu phân cụm

McNemar `χ² = (b − c)²/(b + c)` coi `b + c` là phương sai của `b − c`, đúng *chỉ khi các cặp độc lập*. Dưới tương quan dương trong cụm, phương sai thật lớn hơn, thống kê bị thổi phồng, kiểm định thiên về bác bỏ sai
`[tự suy ra từ logic design effect]`.

Bốn tổng quát hoá cho dữ liệu ghép cặp có cụm, cài trong gói R `clust.bin.pair` (mặc định là Yang) `[trang]`:
Eliasziw & Donner (1991, *Stat Med* 10:1981–1991) · Obuchowski (1998) · Durkalski, Palesch, Lipsitz & Rust (2003, *Stat Med* 22:2417–2428) · Yang, Sun & Hardin (2010).
Thống kê Durkalski ở H₀ (δ₀ = 0, `d_k = x₁₀ₖ − x₀₁ₖ`): `Z = Σ d_k / √(Σ d_k²)`. Khi mỗi cụm đúng một cặp, `Σ d_k = b − c` và `Σ d_k² = b + c`, nên `Z = (b − c)/√(b + c)`, chính McNemar.
**Phép rút gọn này là đại số của người nghiên cứu** `[tự suy ra]`: họ hỏi một nguồn và nhận câu trả lời phủ định không đáng tin, nên coi chứng minh sơ cấp là bằng chứng, đừng trích ai cho nó.

Mọi phép thử này được biện minh bằng K → ∞ ("a large number of clusters is pivotal to obtain accurate Type 1 error rate"). **Không phép nào đáng tin ở K = 8, càng không ở K = 3.**

### 2.5 MDE cho nhị phân ghép cặp

Ký hiệu theo SAS/STAT PROC POWER, `PAIREDFREQ` `[trang]`: `N` số cặp; `p₀₁`, `p₁₀` tỷ lệ cặp lệch mỗi chiều; `p_d = p₀₁ + p₁₀`; `δ = p₀₁ − p₁₀`.

Connor (1987), cỡ mẫu hai phía xấp xỉ chuẩn:

```
N = { z_{1−α/2}·√p_d + z_{1−β}·√(p_d − δ²) }²  /  δ²
```

(Dạng một phía dùng `z_{1−α}`.) Nghịch đảo cho quy tắc nhanh, **mình đã kiểm so với Connor đầy đủ, lệch ≤ 0,1 điểm** `[đo]`:

```
δ_MDE ≈ (z_{1−α/2} + z_{1−β}) · √(p_d / N)        với 80% lực, α = 0,05:  z-tổng = 2,8016
```

SAS ghi: Miettinen hơi phản bảo thủ, Connor hơi bảo thủ. Cả hai nguồn Connor (1987) và Miettinen (1968) **bị chặn truy cập**, công thức lấy từ trình bày lại của tài liệu SAS.

Có phân cụm: `δ_MDE,cụm ≈ δ_MDE,độc lập · √DE`, trong đó DE tính theo *số cặp lệch trên mỗi cụm*, không phải số phần tử trên cụm. **Đây là phép ghép hai kết quả đã trích do người nghiên cứu làm; chưa có công thức MDE chung cho cặp ghép có cụm** `[tự suy ra]`.

### 2.6 Hướng dẫn riêng của NLP — và khoảng trống

- Dror et al., ACL 2018 (*Hitchhiker's Guide*) `[toàn văn]`: cây quyết định chọn kiểm định; bootstrap "ít hiệu quả với tập test nhỏ". Với tập test phụ thuộc, họ khuyến nghị *replicability analysis* với ước lượng `K_Bonferroni` (Dror et al., TACL 2017).
- Søgaard et al., CoNLL 2014: p-value "rất nhạy với cỡ mẫu"; đề xuất α ≈ 0,0025 `[trang]`.
- **Không có bài ACL-venue nào xử lý phân cụm theo văn bản của item benchmark** `[khoảng trống thật, đã tìm]`. Truyền thống bootstrap NLP (Koehn 2004; Berg-Kirkpatrick 2012) resample item độc lập, chính là thủ tục sai ở đây. Đó cũng là cơ hội: báo *đúng* sẽ tốt hơn mặt bằng.

### 2.7 Báo cáo nhóm có n_eff rất nhỏ

NLP không có quy ước. Y tế công cộng và khảo sát có: báo **số đếm** thay vì phần trăm khi n < ~20 ("hợp lý nhưng tuỳ ý" theo chính nguồn), NCI "small numbers" khi tử số < 20 hoặc mẫu số < 100, AHRQ MEPS tối thiểu 60 quan sát chưa trọng số mới công bố `[snippet–trang]`.
Áp dụng: T5 báo bằng số đếm và bảng theo văn bản tác động, không phần trăm tổng hợp.

---

## 3. T5 — nhóm nhỏ không thể lấp

### 3.1 Cấu trúc thật `[đo]`


| Đo                            | Giá trị                                                   |
| ----------------------------- | ---------------------------------------------------------: |
| Ứng viên toàn kho             | 194 lineage / 8 văn bản tác động                          |
| Sạch                          | 148 lineage / 4 văn bản                                   |
| Xếp hạng được                 | 21 lineage / 42 dòng                                      |
| **Có câu hỏi**                | **19 lineage / 38 dòng**                                  |
| Cụm theo **văn bản tác động** | **3**                                                     |
| Phân bố                       | 65/2025/TT-BQP: 10 · 12/2015/NĐ-CP: 7 · 119/2026/NĐ-CP: 2 |
| Cụm theo văn bản đích         | 10 (lớn nhất 2)                                           |
| Loại hồi tố                   | 19/19 `stated_retroactive`, 0 `guidance_in_sync`          |
| `min_repr`                    | 28 `clause_version`, 10 `cross_document`                  |


Cụm đúng về mặt pháp lý là **văn bản tác động** (một hồi tố thường áp cho nhiều điều khoản cùng lúc, cùng chung cửa sổ hồi tố), không phải văn bản đích. Con số "8 văn bản" và "4 văn bản" trong các báo cáo trước là của *kho*; sau xếp hạng và sinh câu hỏi còn **3**.
Hơn một nửa lineage đến từ một văn bản. Datasheet đã ghi 12/2015/NĐ-CP không nêu ngày hồi tố trong câu hiệu lực và 65/2025/TT-BQP có cửa sổ hồi tố chỉ 2 ngày nên không đặt được câu giữa khoảng.

### 3.2 Hệ quả thống kê, nói thẳng

- n_eff tiến về **3**, không phải 19, nếu lineage cùng văn bản tác động tương quan mạnh (mục 2.1).
- Wild cluster bootstrap: 4 giá trị |t| → **p nhỏ nhất 0,25**. Không có phép kiểm nào về mặt nguyên tắc cho ra p < 0,05 trên T5.
- KTC nhị thức ngây thơ (bỏ qua cụm) đã rộng: ±15,9 điểm cho n = 38, ±22,5 cho n = 19 `[đo]`; và nó *thấp hơn* sự thật vì bỏ qua phân cụm.

**T5 không cho phép:** xếp hạng hệ thống · so sánh hai hệ bằng kiểm định · báo phần trăm tổng hợp · đưa vào trung bình macro · kết luận về "hệ thống tốt/xấu ở hồi tố".
**T5 vẫn cho phép:** báo số đếm từng văn bản tác động · phân tích lỗi định tính · minh hoạ cơ chế lỗi (hệ thống chọn bản nào, vì sao) · làm tập chẩn đoán cho cố vấn luật ký từng ca.

### 3.3 Venue nói gì — và không nói gì

`[trang]` đối với ARR CFP, checklist, hướng dẫn tác giả và NeurIPS 2026 E&D (nhánh đã đọc nguyên văn):

- **Không có sàn cỡ mẫu hay yêu cầu lực thống kê** ở bất kỳ đâu. Hai sàn số duy nhất tự đặt bởi từng benchmark: BIG-bench "tối thiểu 32 cặp input–output mỗi tác vụ", LegalBench "mọi tác vụ có ít nhất 50 instance". **38 dòng nằm giữa hai mốc.** Không mốc nào có hiệu lực venue.
- **Bắt buộc, có desk-reject**: mục Limitations ("Papers without a limitations section will be desk rejected"); checklist trách nhiệm mục B6 yêu cầu báo số lượng ví dụ và chi tiết split. Census 194/148/21/19/3 vì vậy *phải* xuất hiện trong bài.
- Câu của chính checklist, dùng được để **trích chứ không phải tranh luận**: *"small differences in accuracy on large test sets may be significant, while on small test sets they may not be."*
- NeurIPS 2026 E&D bắt buộc metadata Croissant kèm trường Responsible AI; quy tắc kích thước duy nhất chạy theo chiều ngược (bộ dữ liệu > 4GB phải kèm mẫu cho reviewer).

Bất đối xứng đáng nhớ: **công bố là nghĩa vụ bị cưỡng chế; loại một nhóm khỏi trung bình macro chỉ là lựa chọn thiết kế không ai quy định.**

### 3.4 Tiền lệ đóng khung

Truyền thống có bốn vai, mạnh dần về mức khẳng định: *case study* (không chỉ số) → *slice* → *diagnostic set* (cột riêng, so mô hình–với–mô hình trong một hạng mục) → *benchmark task* (xếp hạng, gộp). 38 dòng hợp với **diagnostic set** hoặc **slice**. Gọi là *task* mời phản biện "dưới 50 của LegalBench"; gọi là *case study* thì bỏ đi nhiều hơn cần thiết.

- **GLUE diagnostic** `[trang]`: *"provided not as a benchmark, but as an analysis tool for error analysis, qualitative model comparison, and development of adversarial examples."* Quy tắc đọc kết quả chuyển được nguyên sang T5: so điểm **nhiều model trên cùng một hạng mục**, không so cùng một model giữa các hạng mục. 1.104 ví dụ chia 4 nhóm thô và 21+ nhóm mịn, nên từng ô mịn của GLUE cũng cỡ chục.
- **SuperGLUE (Winogender)** `[trang]`: AX-g 356 và AX-b 1.104, đặt cột riêng ngoài "Avg". Câu caveat tái dùng được gần nguyên văn: *"It offers only positive predictive value: A poor bias score is clear evidence that a model exhibits gender bias, but a good score does not mean that the model is unbiased."*
- **LegalBench** (NeurIPS 2023 D&B, gần miền nhất) `[trang]`: lát cắt nhỏ *"are small—and thus not intended for rigorous statistical analysis"*; mẫu câu khai tập trung nguồn: *"Because 16/17 of our issue-spotting tasks are drawn from one source... average issue performance is skewed by properties of the Learned Hands data distribution."* Đúng tình huống 3 văn bản của T5.
- **HELM** `[trang]`: từ chối điểm tổng một số, và coi việc *nêu tên ô còn thiếu* là sản phẩm: *"provide a top-down taxonomy and make explicit all the major scenarios and metrics that are missing."* Là lập luận *cho* việc ship T5 thay vì bỏ.
- **Datasheets for Datasets** (Gebru et al.): câu hỏi *"Does the dataset contain all possible instances or is it a sample ... of instances from a larger set?"* Câu trả lời trung thực cho T5 là "tất cả instance còn lại sau các bộ lọc đã nêu", biến n nhỏ từ điểm yếu lấy mẫu thành tuyên bố đầy đủ. Và *"Are there tasks for which the dataset should not be used?"* là chỗ ghi "không dùng để xếp hạng hệ thống trên T5". Data Statements v3 có phần LIMITATIONS riêng.
- **CALRK-Bench (2026)** (đã có trong báo cáo khảo sát §2.7): chỉ 8 mẫu về sửa đổi luật, khai "clarity bias" và tiêu chí loại.

**Hai khoảng trống thật thà** (nhánh nghiên cứu ghi): không tìm được một tập con dưới 50 item *độc lập, có tên, kèm câu biện hộ nguyên văn* trong bài ACL/EMNLP/NAACL/NeurIPS-D&B nào — tiền lệ kiểm chứng được chỉ là *lát cắt* dưới 100 item bên trong benchmark lớn. Và không gom được kho câu Limitations "hiếm vốn có" nguyên văn đáng tin (kết quả trả về chủ yếu là preprint y học 2025–26 chỉ thấy dạng snippet).
**Nghĩa là về cỡ mẫu bạn đang tạo tiền lệ; về cách đóng khung thì bạn đi theo tiền lệ. Dựa vào cái thứ hai.**

---

## 4. Hồi tố có tiền lệ trong point-in-time QA không?

**Không, và đây là phủ định có bằng chứng — nhưng claim phải hẹp.** Tìm bằng tiếng Anh; chưa phủ các venue tiếng Việt.

- Khảo sát temporal QA 2025–26 (arXiv 2505.20243) liệt kê 30+ bộ (TimeQA, SituatedQA, StreamingQA, ArchivalQA, RealTimeQA, ComplexTempQA, ChroniclingAmericaQA…) và **không nhắc hồi tố, commencement hay hiệu lực lùi ở đâu**; coi thời điểm tạo văn bản và thời điểm sự kiện là hai mốc trùng nhau `[toàn văn của nhánh]`.
- Các công trình 2026 có kho theo phiên bản trong tay: **LexKairos** (arXiv 2608.09106) nêu retroactivity trong động cơ nhưng viết là "acknowledged but not systematically benchmarked" · **"When Do LLMs Apply the Wrong Law?"** (2608.14610) coi không hồi tố là nguyên tắc nền, hồi tố chỉ là ngoại lệ ở phụ lục, không thành một loại · **"Asking For An Old Friend"** (2605.23497) không bàn tới hồi tố.
Ngoài benchmark, de Martim (2606.09724) là đặc tả kiến trúc, có nêu hồi tố nhưng **không đánh giá định lượng**. LegalBench chỉ có `cuad_effective_date`, một tác vụ phát hiện điều khoản hợp đồng.
- Cách viết đứng được: *"đầu tiên **đánh giá** hồi tố trong point-in-time legal QA"*. Không viết "đầu tiên nhận ra". Việc nhiều công trình độc lập đều không dựng nhóm này cũng là một tín hiệu cần cân: nó có thể là hiện tượng rất hiếm hoặc khó đóng gói thành tác vụ, và **chính T5 với 3 cụm là bằng chứng nội tại cho điều đó**.

**Chuẩn legal informatics đã hình thức hoá phân biệt này từ lâu.** Akoma Ntoso / OASIS LegalDocML (nháp 2006; chuẩn OASIS 29/08/2018) cho mỗi mảnh văn bản **hai cặp ngày độc lập**:
`@start`/`@end` (hiệu lực/ban hành — *validity/enactment*) và `@startEfficacy`/`@endEfficacy` (*efficacy*), kèm `@status`, `lifecycle`, `eventRef`, `temporalData`, `efficacyMod`/`forceMod`;
loại sự kiện gồm `entryIntoForce` và `entryIntoEfficacy` `[trang; từ vựng AKN Part 1 ~246k ký tự, chỉ đọc 100k đầu nên danh sách sự kiện chưa xác nhận đủ]`.
Câu rõ nhất tìm được (arXiv 2506.07853, LRMoo/ELI): việc vào trật tự pháp lý khác với việc áp dụng *"because the two diverge under vacatio legis (deferred onset), retroactive (ex tunc) effect, and tax-anteriority or lex mitior rules"*, kèm ví dụ luật thuế và lex mitior, và yêu cầu hai trục thời gian valid-time/transaction-time `[toàn văn]`.
de Martim (2606.09724, Thượng viện Liên bang Brazil, 2026) viết các chuẩn biểu diễn ngày có hiệu lực và ngày áp dụng như hai thuộc tính riêng `[toàn văn]`.

**Thế bất đối xứng để dựng động cơ:** chín muồi trong chuẩn, vắng mặt trong đánh giá NLP.
Điểm có lợi cho phương án (c): Akoma Ntoso mã hoá hồi tố là **hai thuộc tính trên một mảnh văn bản**, không phải một lớp tài liệu. Làm trường vì vậy là *bám chuẩn*, không phải hạ cấp.

---

## 5. Quyết định cho T5

### 5.1 Ba lựa chọn, đặt cạnh nhau


|                          | (a) Giữ T5, chẩn đoán 30–45                                 | (b) `not_yet_in_force`                                                                                                                       | (c) Hồi tố thành trường                                                         |
| ------------------------ | ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| **Cái gì**               | 19 lineage / 38 dòng hiện có, có tên, không điểm tổng       | Hỏi ở ≥30 ngày trước ngày hiệu lực, khi bản mới đã ký mà bản cũ mới đúng                                                                     | `retroactive` trên mọi dòng của mọi nhóm                                        |
| **Tiền lệ**              | GLUE diagnostic, SuperGLUE AX-g, LegalBench slice (mục 3.4) | **"future-law leakage"** (French tax, arXiv 2608.09393): *"remains unexercised in the scored benchmark, reserved for future work"* `[trang]` | Robustness Gym, CheckList, HELM, TimelyQABench `[trang]`; Akoma Ntoso `[trang]` |
| **Lực thống kê**         | **3 cụm. Không suy luận được**                              | **155 lineage / 129 văn bản tác động** `[đo]`, DE ≈ 1,0x                                                                                     | Phụ thuộc phủ của trường; cho phép nói về *độ phổ biến* chứ không về độ khó     |
| **Chi phí**              | Gần 0 (đã có)                                               | ~1 chế độ `as_of` mới, **không cần câu hỏi mới**, gold tất định                                                                              | Gần 0                                                                           |
| **Rủi ro chính**         | Phản biện "nhóm quá nhỏ"                                    | Cần kiểm kho "như công bố" có chứa văn bản đã ký chưa hiệu lực không (mục 8)                                                                 | Mất "nhóm" để vẽ vào Bảng 1                                                     |
| **Đứng trước phản biện** | Chỉ khi khai thẳng là chẩn đoán                             | **Mạnh nhất**                                                                                                                                | Sạch nhất                                                                       |


Điểm cộng thêm của (b) (nhánh nghiên cứu): chiến lược mặc định của lĩnh vực cho xung đột thời gian là *xếp theo độ mới*, nên kho có văn bản chưa hiệu lực là **đối kháng với heuristic mặc định** ngay từ thiết kế. Trong văn liệu, hướng lỗi được nghiên cứu nhiều là hướng ngược lại — *current-law substitution* / *recency bias* / *newest-law bias* (chênh lệch đo được 0,70–0,84 ở ca bản mới so với dưới 0,25 ở ca bản cũ) `[snippet]`.

### 5.2 Khuyến nghị

**(c) + (a) ngay bây giờ, và (b) như một chế độ `as_of` bổ sung cho T2.**

1. **(c)**: thêm trường `retroactive` (đã có sẵn trên bản ghi T5, cần mở rộng ra mọi dòng) — tính từ cặp (ngày ký, ngày hiệu lực) của văn bản tác động. Rẻ, bám chuẩn, và cho phép một phát hiện cấp kho mà 19 lineage không bao giờ cho được (độ phổ biến của hồi tố).
2. **(a)**: 38 dòng T5 ship như **tập chẩn đoán có tên, cột riêng, không điểm tổng, không vào macro**, báo bằng số đếm theo văn bản tác động. T6 hấp thu 12 dòng thiếu đã có trong thiết kế (`quota += RELEASE["T5"] − got["T5"]`).
3. **(b)**: một chế độ `as_of` mới, đặt tên theo khuôn của `sau_het_hieu_luc` (ví dụ `truoc_hieu_luc`), dựng bằng `twin_of` từ dòng "trước" của cặp T2: hỏi ở `effective_from − 30` ngày với lineage có `signed_on ≤` mốc đó.
  - **Đo `[đo]`**: trong 233 lineage T2 có câu hỏi, **155 đủ điều kiện**; khoảng ký→hiệu lực trung vị 48 ngày, nhỏ nhất 36, lớn nhất 554. Trên toàn pool T2: 3.373/4.149 dòng có `pending` đủ điều kiện (81,3%).
  - **Cụm `[đo]`**: 129 văn bản tác động, 104 cụm chỉ một lineage, `m̄ = 1,20`, `CV = 0,35`. Phân cụm nhẹ, nên khác T5 ở chỗ có thể suy luận thống kê bình thường. Nửa độ rộng KTC 95% tệ nhất cho n = 155 là ±7,9 điểm.
  - **Không cần câu hỏi mới và không cần gán nhãn câu hỏi mới**: câu hỏi và phiên bản đáp án (bản cũ) giữ nguyên, ngày đổi. Như dòng anh em `giua_khoang`, theo cách datasheet đang đếm nó **không tính vào hạn ngạch dòng ranh giới** `[tự suy ra từ datasheet]`.

### 5.3 Chỗ mình sửa lại một điều đã nói trong phiên

Trước đó mình nói `not_yet_in_force` phải đợi v1.1 vì "cần mốc `as_of` thứ tư và đổi schema sau đóng băng". Phép đo hôm nay cho thấy kết luận đó quá nặng tay: repo **đã có chế độ thứ ba** (`sau_het_hieu_luc`, dựng qua `twin_of`),
nên chế độ thứ tư là bổ sung cùng khuôn, không phải đổi cấu trúc. Chi phí thật là một chế độ trong `enrich_vilextime.py`, test, và một mục datasheet.

Mình cũng **lệch khỏi kết luận của nhánh nghiên cứu** ở một điểm: họ khuyến nghị (b) *thay suất quota* của T5. Mình khuyến nghị (b) là *chế độ bổ sung*, không thay quota, vì nó không phải một nhóm câu hỏi riêng mà là một cách hỏi lại các câu hỏi T2 đã có. Họ chưa biết T2 sẵn có 155 ứng viên và rằng `pending` hiện chỉ là bẫy 1 ngày.

### 5.4 Nó tốn gì và có thể sai ở đâu

- **Cần quyết định nhân lực**: thêm chế độ này không tốn giờ gán nhãn câu hỏi, nhưng gold cần kiểm mẫu bởi người (gold tất định nhưng dựa vào `signed_on`, đã từng có lỗi metadata ở JUDGE C1). Giờ công đang thiếu (250–465 giờ cần so với 175–325 có); cổng G3 ngày 18/10 là lúc quyết.
- **Rủi ro lớn nhất, chưa kiểm**: bẫy chỉ có ý nghĩa nếu kho truy xuất "như công bố" *thực sự chứa* văn bản sửa đổi đã ký nhưng chưa hiệu lực. Nếu lớp corpus đó chỉ có văn bản đã hiệu lực thì hệ thống không thể bị lừa và nhóm này đo không ra gì. Đây là việc kiểm đầu tiên (mục 8).
- **Hướng đơn**: (b) chỉ đo future-law leakage, không đo hướng ngược (current-law substitution), hướng mà văn liệu thấy mạnh hơn. Nên nêu rõ trong Limitations.
- **Không có baseline công bố để hiệu chuẩn**: chưa bộ nào chấm điểm một nhóm như vậy, nên không có con số độ khó nào để đối chiếu. Con số 0% của static RAG trong văn liệu là cho hướng *bản cũ đúng*, không phải hướng *bản tương lai* `[trang]`.

---

## 6. Câu cho Limitations (bản nháp tiếng Việt)

**Về T5** — ghép từ bốn nước đi, mỗi nước dựa trên câu đã trích ở trên:

> *Nhóm hồi tố (T5) là một **tập chẩn đoán**, không phải một tác vụ xếp hạng. Nhóm nhỏ vì hiện tượng hiếm đúng như bản chất của nó, không phải vì thiếu công sức: toàn kho có 194 chuỗi sửa đổi hồi tố từ 8 văn bản tác động, 148 chuỗi từ 4 văn bản sau khi lọc,
> và bản phát hành giữ 19 chuỗi (38 dòng) từ 3 văn bản tác động, trong đó một văn bản đóng góp 10 chuỗi. Đây là toàn bộ các ca còn lại sau các bộ lọc đã nêu ở Mục X, không phải một mẫu. Với chỉ 3 cụm, kiểm định bootstrap theo cụm không thể cho p < 0,25 về mặt nguyên tắc,
> và cỡ mẫu hiệu dụng tiệm cận số văn bản chứ không phải số chuỗi. Vì vậy chúng tôi báo cáo T5 bằng số đếm theo từng văn bản tác động, không tính vào trung bình macro, và không khuyến nghị dùng nó để xếp hạng hệ thống.
> Theo tinh thần của các tập chẩn đoán trước đó (Wang et al., 2019; Wang et al., 2019b), nó "không phải một benchmark, mà là công cụ phân tích": một kết quả xấu là bằng chứng rõ ràng về một chế độ lỗi, còn một kết quả tốt không chứng minh hệ thống xử lý đúng hồi tố nói chung.
> Hiện tượng hồi tố được ghi nhận như một trường trên mọi dòng của bộ dữ liệu để phục vụ phân tích độ phổ biến. Chúng tôi cố ý loại các ca mơ hồ hoặc dần dần (clarity bias), theo tiêu chí ở Mục X.*

(GLUE: Wang et al. 2019a; SuperGLUE: Wang et al. 2019b — kiểm lại thông tin thư mục trước khi in.)

**Về T2** — ba câu, mỗi câu ứng với một phê bình đã biết:

> *Mỗi cặp T2 là một contrast set cỡ hai theo Gardner et al. (2020); chúng tôi báo contrast consistency (đúng ở cả hai mốc) kèm hai mốc tham chiếu: bình phương độ chính xác từng dòng và mức ngẫu nhiên 0,25. Nhiễu ở đây là một lần sửa luật thật cộng một thay đổi ngày, không phải do người gán viết,
> nên không có hiện vật văn phong của người gán; đổi lại, cặp tối thiểu về phía câu hỏi nhưng không tối thiểu về phía bằng chứng, mức khác biệt được báo qua `version_similarity`. Với 225 cặp, hai hệ thống chênh lệch dưới 6–10 điểm TCS (tuỳ tỷ lệ cặp lệch) không phân biệt được ở mức lực 80%.*

---

## 7. Điều kiện để dựng bảng kết quả T2 và T5 đúng

Checklist rút ra từ trên, theo thứ tự:

1. **T2**: báo contrast consistency + p² + sàn 0,25; MDE 5,9–10,2 điểm; bootstrap theo lineage; McNemar chính xác kèm Durkalski làm kiểm tra độ bền; ước ρ bằng ANOVA sau khi có kết quả và báo kèm.
2. **T2**: tách bảng theo `similarity` (tư phân vị) và theo `near_identical` (lát cắt T4 cũ, để Bảng 1 còn hàng T4).
3. **T5**: số đếm theo văn bản tác động; không %, không kiểm định, không macro; câu Limitations ở trên; khai census 194/148/21/19/3.
4. **Mọi nhóm**: ghi `retroactive` thành trường; báo `chance_accuracy`.
5. **(b)**: chỉ làm sau khi kiểm mục 8.1.

---

## 8. Chưa xác minh — kiểm trước khi luận văn trích

**Phải kiểm bằng dữ liệu của mình (chặn (b)):**

1. Lớp corpus "như công bố" có chứa các văn bản sửa đổi đã ký chưa hiệu lực không? Nếu không, bẫy không tồn tại với hệ thống và (b) vô nghĩa.
2. Có lỗi metadata `signed_on`/`effective_from` trong 155 ứng viên không (kiểm mẫu bằng người, theo tiền lệ JUDGE C1).
3. Hồi tố: kiểm chéo 19 lineage T5 với cố vấn luật (phiếu T5 chờ từ 20/09), đặc biệt 12/2015/NĐ-CP không nêu ngày hồi tố.

**Nguồn chưa tự xác minh (theo ghi chú nghiên cứu):**

- Câu trích về "corpus normatively stable ... corrigenda/republications" xuất hiện trong một snippet nhưng **không tìm lại được** trong de Martim 2606.09724 (ứng viên khác: 2609.18769 hoặc 2608.09106). **Không trích** cho đến khi định vị được.
- Lý do thiết kế của **LawShift** (tách chiều sửa đổi khỏi item): chỉ xác nhận phần cấu trúc (Template/Amendment Dimensions, 31 loại, metamorphic) qua metadata NeurIPS và mlanthology; trang OpenReview bị chặn bởi xác thực trình duyệt, nên "và nói vì sao" **chưa xác nhận**. Dùng Robustness Gym và CheckList cho luận điểm kiến trúc.
- **Bị chặn hoặc chỉ có abstract**: Durkalski (2003), Yang (2010), Connor (1987), Miettinen (1968), Kish (1965), Donner & Klar (2000), Eldridge (2006), Ridout (1999). Công thức lấy từ trình bày lại có thẩm quyền (SAS, PMC2717020, CRAN); **xác nhận thông tin thư mục trước khi trích**.
- Các lead năm 2025–26 chỉ ở mức snippet, **mở ra trước khi trích**: LexFlip 2609.05296, evolveQA 2510.19172, TeCFaP (EMNLP 2024), Temporal Wiki 2506.07270, TimelyQABench 2609.11572, "Temporal Referential Consistency" 2510.15513, NLLP 2025 "Risks and Limits of Automatic Consolidation of Statutes". Vài ID arXiv rất gần đây chưa được mở, cần xác nhận chúng tồn tại.
- **Các phần do người nghiên cứu hoặc mình tự dẫn xuất, không có nguồn**: p² như baseline độc lập · phép rút gọn Durkalski → McNemar · phép đồng nhất Moulton = dạng CV · MDE có cụm `√DE` · bảng độ phân giải p của wild bootstrap (áp công thức Webb đã trích) · việc dòng anh em không tính vào hạn ngạch dòng ranh giới.
- **Khoảng trống thật** (không phải thiếu tìm kiếm): không có benchmark nào áp contrast consistency lên QA pháp luật theo mốc thời gian (tìm tiếng Anh, chưa phủ venue Việt) · không có phân tích lực trong văn liệu contrast sets · không có xử lý phân cụm theo văn bản ở venue ACL · không có kho câu Limitations "hiếm vốn có" nguyên văn đáng tin · không có nguồn nói ρ nhị phân bị chặn thế nào ở tần suất ~85% · không có nguồn nào phát biểu *chuẩn tắc* quy tắc "trường hay nhóm" (phải ráp từ kiến trúc lát cắt, tiêu chí khả thi của HELM và tài liệu về lực; ngưỡng ~20–50 của BenchScope 2603.29357 là xấp xỉ, không cứng).
- **Chưa kiểm**: CaseHOLD, SCALE, BSARD, TempQuestions, TempLAMA, TAQA, FreshQA, CRAG (chỉ phủ ở mức khảo sát); HoH (không có kết quả liên quan); CALRK-Bench và TW-LegalBench về xử lý ngày hiệu lực; LegalRuleML; BIG-bench/DynaBench/GEM về cách xử lý facet.

---

## 9. Trích dẫn chính (kiểm thông tin thư mục trước khi in)

**Contrast sets**

- Gardner, M. et al. 2020. *Evaluating Models' Local Decision Boundaries via Contrast Sets.* Findings of EMNLP 2020, tr. 1307–1323. [https://aclanthology.org/2020.findings-emnlp.117/](https://aclanthology.org/2020.findings-emnlp.117/) · arXiv:2004.02709 `[toàn văn]`
- Ning, Q. et al. 2020. TORQUE. EMNLP 2020. [https://aclanthology.org/2020.emnlp-main.88/](https://aclanthology.org/2020.emnlp-main.88/) `[theo ghi chú: Bảng 4 chép nguyên văn]`
- Kaushik, D., Hovy, E., Lipton, Z. 2020. Counterfactually-augmented data. · Ribeiro, M. T. et al. 2020. CheckList. ACL 2020. [https://aclanthology.org/2020.acl-main.442/](https://aclanthology.org/2020.acl-main.442/) `[trang]`
- Elazar, Y. et al. 2021. Consistency of factual knowledge in pre-trained language models. `[snippet]`
- Card, D. et al. 2020 (EMNLP) · Bowman, S., Dahl, G. 2021 (NAACL) — lực của tập test. `[trang]`

**Thống kê**

- Killip, S., Mahfoud, Z., Pearce, K. 2004. *Ann Fam Med* 2(3):204–208. [https://pmc.ncbi.nlm.nih.gov/articles/PMC1466680/](https://pmc.ncbi.nlm.nih.gov/articles/PMC1466680/) `[toàn văn]`
- Cameron, A. C., Miller, D. L. 2015. A practitioner's guide to cluster-robust inference. *J. Human Resources.* [http://cameron.econ.ucdavis.edu/research/Cameron_Miller_JHR_2015_February.pdf](http://cameron.econ.ucdavis.edu/research/Cameron_Miller_JHR_2015_February.pdf) `[toàn văn]`
- Dror, R. et al. 2018. The Hitchhiker's Guide to Testing Statistical Significance in NLP. ACL 2018. [https://aclanthology.org/P18-1128/](https://aclanthology.org/P18-1128/) `[toàn văn]`
- Eliasziw & Donner 1991 · Obuchowski 1998 · Durkalski et al. 2003 (*Stat Med* 22:2417–2428, DOI 10.1002/sim.1438) · Yang, Sun & Hardin 2010 · gói R `clust.bin.pair` (CRAN) `[trang]`
- Connor, R. J. 1987 · Miettinen, O. 1968 · SAS/STAT PROC POWER, PAIREDFREQ. [https://support.sas.com/documentation/cdl/en/statug/65328/HTML/default/statug_power_details55.htm](https://support.sas.com/documentation/cdl/en/statug/65328/HTML/default/statug_power_details55.htm) `[trang]`
- Søgaard, A. et al. 2014. CoNLL. [https://aclanthology.org/W14-1601/](https://aclanthology.org/W14-1601/) `[trang]`

**Tập chẩn đoán và venue**

- Wang, A. et al. 2019. GLUE · SuperGLUE (arXiv:1804.07461, arXiv:1905.00537) `[trang]`
- Guha, N. et al. 2023. LegalBench. NeurIPS D&B. arXiv:2308.11462 `[trang]`
- Liang, P. et al. 2022. HELM. arXiv:2211.09110 `[trang]`
- Gebru, T. et al. Datasheets for Datasets · Bender, E., Friedman, B. Data Statements `[trang]`
- ARR: [https://aclrollingreview.org/cfp](https://aclrollingreview.org/cfp) · [https://aclrollingreview.org/responsibleNLPresearch/](https://aclrollingreview.org/responsibleNLPresearch/) · [https://aclrollingreview.org/authors](https://aclrollingreview.org/authors) `[trang]`

**Hồi tố và trường-hay-nhóm**

- Khảo sát temporal QA. arXiv:2505.20243 `[toàn văn của nhánh]`
- LexKairos. arXiv:2608.09106 · "When Do LLMs Apply the Wrong Law?" arXiv:2608.14610 · "Asking For An Old Friend". arXiv:2605.23497 `[toàn văn của nhánh]`
- Temporal misgrounding trong luật thuế Pháp. arXiv:2608.09393 `[trang]`
- OASIS LegalDocML / Akoma Ntoso v1.0 Part 1 vocabulary. [https://docs.oasis-open.org/legaldocml/akn-core/v1.0/akn-core-v1.0-part1-vocabulary.html](https://docs.oasis-open.org/legaldocml/akn-core/v1.0/akn-core-v1.0-part1-vocabulary.html) `[trang, đọc 100k đầu]`
- LRMoo/ELI diachronic norms. arXiv:2506.07853 `[toàn văn]` · de Martim. arXiv:2606.09724 `[toàn văn]`
- Robustness Gym. arXiv:2101.04840 · BenchScope. arXiv:2603.29357 · TimelyQABench. arXiv:2609.11572 `[trang]`

