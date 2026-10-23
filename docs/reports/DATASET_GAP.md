# ViLexTime — khoảng trống chất lượng dữ liệu

Ngày: 23/10/2026. Người phản biện: Claude (claude-opus-5-5), chỉ đọc. Trạng thái được đo: commit
`b5d36de`, bản `data/vilextime_dataset/` (schema 2.0.0, `draft: true`; sha256 của `vilextime.jsonl`
ghi trong `manifest.json`).

**Phạm vi:** tiêu chí *Dataset &amp; Data Quality*, gồm (1) thu thập, gán nhãn, độ tin cậy; (2) cân bằng,
thiên lệch, tính đại diện; (3) datasheet / data card. Không chấm phần viết của khóa luận vì repo chưa
có bản thảo.

**Chuẩn đối chiếu:**

- `docs/vilextime-dinh-nghia.md` (ĐN): §6 điều kiện vào test, §8 kiểm định, §9 cơ cấu;
- `docs/vilextime-annotation.md` (HD 3.0): §5 quy trình kiểm;
- Gebru và cộng sự (2021), *Datasheets for Datasets*; ACL Responsible NLP checklist (mục B, D, E);
NeurIPS Datasets &amp; Benchmarks (metadata Croissant).

**Quy ước:** **[Đo]** là số đo lại ngày 23/10 (cách đo ở Phụ lục). **[Suy luận]** là nhận định chưa
kiểm bằng dữ liệu.

**Giữ mù:** tài liệu không nêu id hay điều khoản nào thuộc lô 0, mẫu gán chéo (`kiem_cheo.txt`) hay
mẫu gold. **B đọc mục G4 sau khi nộp lô 0**, vì mục này nói về nhãn của A ở lô 0.

---

## 1. Kết luận

- **Mức hiện tại: cần sửa lớn (Major revision).** Theo thang ARR: Soundness 2/5, Dataset 3/5.
- Thiết kế bài toán và scorer tốt, cơ cấu nhóm đạt §9. Nhưng **gần như chưa có dòng test nào được
người kiểm**, và hướng dẫn 3.0 chưa có số đồng thuận nào.
- Năm khoảng trống mức Chặn: G1–G4 thuộc dữ liệu, G17 là điều kiện để chạy test. Phải đóng cả năm
trước khi báo số chính thức. Đóng thêm G12 (datasheet) thì bộ dữ liệu lên được 4/5.

## 2. Bảng khoảng trống

Mức: **Chặn** — chưa được báo số chính thức trên test; **Cao** — reviewer chắc chắn bắt;
**TB** — nên sửa trước khi phát hành; **Thấp** — sửa khi đóng băng.


| #   | Khoảng trống                                       | Chuẩn                                                   | Hiện trạng [Đo]                                                                           | Mức                  |
| --- | -------------------------------------------------- | ------------------------------------------------------- | ----------------------------------------------------------------------------------------- | -------------------- |
| G1  | Test chưa được người kiểm                          | ĐN §6, §8: test chỉ gồm dòng người đã kiểm có dẫn chứng | 21/1.120 dòng ranh giới (1,9%); xuất `--final` thì file chính còn 11 lineage              | Chặn                 |
| G2  | Đồng thuận theo HD 3.0 chưa đo; D4 chưa đạt        | ĐN §8: AC1 ≥ 0,80 và p_neg ≥ 0,60                       | HD 3.0: 0 dòng gán đôi. D4: AC1 0,612, p_neg 0,46                                         | Chặn                 |
| G3  | Gold độc lập chưa làm                              | ĐN §8: 120 + 30 dòng gán mù, đạt ≥ 114/120              | `gold_A` 0/75, `gold_B` 0/75                                                              | Chặn (RQ2, RQ3)      |
| G4  | Nhãn HD 3.0 đầu tiên quá nhanh; chưa hiệu chuẩn    | HD 3.0 §5: lô 0 hai người làm, họp luật sư trước lô 1   | Lô 0 của A: trung vị 1 phút/dòng; B chưa gán lô 0                                         | Chặn                 |
| G5  | Hòa giải D4 không độc lập                          | ĐN §8: người thứ ba (luật sư), không dùng AI            | AI soạn; A, một bên của dòng lệch, xác nhận                                               | Cao                  |
| G6  | Gọi AC1 là "đăng ký trước"                         | MRG A3, DL-12: ghi rõ AC1 chọn sau pilot                | D5, HD 3.0, datasheet, `crosscheck_result.json` vẫn ghi "đăng ký trước"                   | Cao                  |
| G7  | Câu hỏi bám lời văn đáp án; chưa có câu người viết | ĐN §8: khoảng 100 câu người viết mù                     | 609/609 câu do LLM viết; trung vị 77% số tiếng của câu hỏi nằm nguyên văn trong gold      | Cao                  |
| G8  | Thay đổi do sắp xếp bộ máy 2025 lọt bộ lọc         | ĐN R1-ii, R4                                            | 16/21 lineage T2/T3 có ranh giới đúng ngày sắp xếp nhắc tới cơ quan hay đơn vị hành chính | Cao                  |
| G9  | Nhóm trùng với model viết câu hỏi                  | ADR 0004 §3                                             | T1, T2 thường, T5a: Claude 100%; T4 87%, T6a 84%, T6b 98%: DeepSeek                       | TB                   |
| G10 | Đại diện hẹp: miền, loại văn bản, thời gian        | Gebru: phạm vi đại diện; ACL B                          | Miền "khác" 66,5%; NĐ 43,8% (kho 20,5%); 33,4% dòng hỏi từ 2025                           | TB                   |
| G11 | Lời văn gold hỏng dấu; scorer so khớp giữ dấu      | ĐN §6, điều kiện 1 và 8                                 | Ít nhất 1 lineage                                                                         | TB                   |
| G12 | Datasheet cũ và thiếu mục                          | Gebru; ACL B, D, E; NeurIPS D&amp;B                     | Mô tả bản 11/10; thiếu mục "không nên dùng", người gán, bảo trì, Croissant                | Cao                  |
| G13 | Corpus truy xuất chưa phát hành                    | Tái lập được                                            | asis 771 MB, versions 834 MB; chưa chốt nơi đăng                                          | TB                   |
| G14 | Dòng giữa khoảng kế thừa nhãn, không xét lại R4    | ĐN R4 xét theo `t` của chính dòng                       | 1 dòng                                                                                    | Thấp                 |
| G15 | Số lineage bị loại theo mã chưa có trong manifest  | Schema phát hành                                        | `dropped_lineages_by_reason` trống                                                        | Thấp                 |
| G16 | Tên nhóm T5b lệch                                  | ĐN §4                                                   | File ghi `group = T2`, `subgroup = T5b`                                                   | Thấp                 |
| G17 | ADR 0005 chưa Accepted                             | ADR 0005: Accepted trước khi chạy test                  | `Proposed`                                                                                | Chặn (khi dùng test) |


## 3. Chi tiết

### 3.1 Thu thập, gán nhãn, độ tin cậy

**G1. Test chưa được người kiểm.** [Đo]

- `manifest.json` ghi `final: false`, `agreement: null`. Dòng ranh giới: 21 `checked`, 1.099
`not_verified`.
- Theo quy tắc lấy nhãn cuối của `docs/vilextime-schema-phat-hanh.md`, nếu xuất `--final` hôm nay
thì file chính chỉ có 11 lineage.
- 609/609 câu hỏi do LLM viết (Claude 367, DeepSeek 241, gpt-oss 1). Cả 945 đáp án ngắn đang dùng
do Claude viết; chưa đáp án nào được người sửa.
- 139 nhãn D4 mang sang (hướng dẫn 1.2 và 2.0) chưa được xác nhận lại theo 3.0, nên chưa tính.

**G2. Đồng thuận.** [Đo]


| Phạm vi                                 | n   | AC1 [KTC 95%]         | p_neg | κ      |
| --------------------------------------- | ---: | --------------------- | -----: | ------: |
| D4 toàn tập (HD 1.2/2.0)                | 300 | 0,612 [0,511; 0,697]  | 0,460 | 0,323  |
| D4, riêng T6                            | 112 | 0,622 [0,461; 0,748]  | 0,000 | −0,018 |
| D4, hai người dùng hai bản HD khác nhau | 65  | 0,053 [−0,190; 0,309] | 0,590 | 0,140  |
| HD 3.0                                  | 0   | —                     | —     | —      |


- D4 không đạt ngưỡng. Số này chỉ nói về hướng dẫn cũ, không nói gì về HD 3.0.
- Mẫu gán chéo của HD 3.0 (`kiem_cheo.txt`, 106 dòng ở lô 1–9) chưa ai gán. 106 dòng bằng khoảng
9,5% của 1.120 dòng, thấp hơn mức 25% ở §8. Quyết định này đã chốt ngày 21/10, nhưng phải ghi vào
bảng lệch.
- [Suy luận] Với khoảng 106 dòng, KTC của AC1 rộng chừng ±0,15 (ở D4, T2 có n = 100 cho
[0,548; 0,809]). Đủ để báo số chung, không đủ để báo theo từng nhóm.

**G4. Nhãn HD 3.0 đầu tiên (lô 0).** [Đo] **B đọc mục này sau khi nộp lô 0.**

- 21 dòng lô 0 của A: cả 21 dòng `dat`, trung vị 1 phút/dòng, tổng 25 phút. Kế hoạch ước 100–120
giờ người cho bước 5–7, tức vài phút mỗi dòng.
- Lô 0 được thiết kế nghiêng về ca khó (T6, T2 gần giống). Tôi mở 2 cặp T2 gần giống (4 dòng). Cả hai
cặp có lỗi mà nhãn không ghi:
  - cặp thứ nhất: lời văn gold có chữ hỏng dấu, và phần tô đỏ (chỗ khác giữa hai phiên bản) chính
  là các chữ hỏng đó (xem G11);
  - cặp thứ hai: lần đổi duy nhất là đổi tên đơn vị hành chính ngày 01/07/2025, thuộc loại R1-ii/R4
  mà ít nhất phải hỏi luật sư; và câu hỏi ghi sẵn đáp án của mốc trước (`question_leaks`, HD §3).
- Bối cảnh từ D4: A cho `dat` 85,0% số dòng, B 68,7%. Trong 75 dòng lệch, 62 dòng là A `dat`, B
`khong_dat`. Kết luận hòa giải trùng nhãn của B ở 70/75 dòng. Từ 21/10, A là người kiểm duy nhất.
- B chưa gán lô 0, nên buổi hiệu chuẩn chưa diễn ra; mục 7 "Hỏi đáp" của HD chưa có mục nào.
- [Suy luận] Tốc độ 1 phút có thể do đang thử trang gán nhãn mới. Nên đo lại cột `phut` sau lô 1 rồi
mới kết luận.
- Id cụ thể của các dòng trên được đưa vào buổi hiệu chuẩn, sau khi B nộp lô 0.

**G5. Hòa giải D4 không độc lập.** [Đo, theo D5 §4]

- Bản nháp do trợ lý AI viết; `claude-opus-5-5` đối chiếu văn bản; A xác nhận. Cột `adjudicator`
ghi đúng như vậy.
- Cách làm này trái ĐN §8 và HD 3.0 §5 ("người thứ ba, không dùng AI"). Kết quả không nghiêng về A,
nhưng khóa luận vẫn phải ghi đúng quy trình.
- Việc cần làm: đợt HD 3.0 do luật sư hòa giải, như đã chốt ngày 21/10. Khóa luận ghi D4 là "hòa
giải có AI hỗ trợ, một người gán xác nhận", và không dùng D4 làm số đồng thuận chính.

**G6. "Đăng ký trước".** [Đo]

- `MASTER_RESEARCH_GUIDE.md:145` (A3) và `MASTER_RESEARCH_GUIDE.md:2072` (DL-12) ghi rằng AC1 được
chọn sau lượt pilot.
- Nhưng D5 §2, HD 3.0 §5 bước 4, datasheet §6 và `crosscheck_result.json` (khóa `preregistered`)
vẫn gọi là "đăng ký trước".
- Cách sửa: viết "chọn sau pilot ngày 07/10/2026, vì nghịch lý prevalence"; vẫn báo κ cạnh AC1.

### 3.2 Cân bằng, thiên lệch, tính đại diện

**Cơ cấu đạt §9, nhưng chưa được kiểm.** [Đo] Số đếm trên dòng ranh giới:


| Nhóm            | Lineage | Dòng      | Có đáp án       | dev / test    | Mục tiêu §9   |
| --------------- | -------: | ---------: | ---------------: | ------------- | ------------- |
| T1              | 150     | 150       | 150             | 20 / 130      | 150           |
| T2 thường       | 150     | 300       | 300             | 64 / 236      | 300           |
| T4 (lát của T2) | 75      | 150       | 150             | 18 / 132      | 150           |
| T3              | 49      | 150       | 150             | 28 / 122      | 150 (sàn 120) |
| T5a             | 10      | 20        | 20              | 0 / 20        | khoảng 34     |
| T6a             | 50      | 100       | 50              | 14 / 86       | sàn 100       |
| T6b             | 125     | 250       | 125             | 42 / 208      | 250 (sàn 200) |
| **Tổng**        | **609** | **1.120** | **945 (84,4%)** | **186 / 934** | 1.100–1.150   |


T5b gồm 143 dòng `truoc_hieu_luc` (dev 27, test 116), báo riêng. Cả bộ có 2.383 dòng, trong 502 văn
bản đích.

**G7. Câu hỏi do model viết.** [Đo]

- Trung vị 77% số tiếng có nghĩa của câu hỏi xuất hiện nguyên văn trong lời văn gold; 43,3% số câu
vượt mức 80%.
- 5 cụm mở đầu chiếm 19,0% số câu; riêng "theo quy định về" có 76/609 câu.
- Điểm tốt: 0/609 câu nêu Điều, Khoản hay số hiệu; không có câu trùng.
- [Suy luận] Câu hỏi "chép từ đáp án" giúp truy xuất theo từ khóa (BM25) có lợi, và không giống câu
hỏi người dùng thật. Khoảng 100 câu người viết mù (§8) dùng để đo độ lệch này; hiện chưa có câu nào.

**G9. Nhóm trùng với model viết câu hỏi.** [Đo] Số lineage:


| Nhóm      | Claude | DeepSeek | gpt-oss |
| --------- | ------: | --------: | -------: |
| T1        | 150    | 0        | 0       |
| T2 thường | 150    | 0        | 0       |
| T4        | 10     | 65       | 0       |
| T3        | 37     | 11       | 1       |
| T5a       | 10     | 0        | 0       |
| T6a       | 8      | 42       | 0       |
| T6b       | 2      | 123      | 0       |


- Chênh lệch giữa các nhóm vì vậy lẫn với văn phong của hai model. ADR 0004 §3 (giám khảo và cột kết
quả chính ngoài hai họ model) chỉ xử lý thiên vị tự chấm, không gỡ được nhiễu này.
- Việc cần làm: báo kết quả tách theo `question_source`, và ghi điều này vào phần giới hạn.

**G10. Tính đại diện.** [Đo]


| Loại văn bản   | Bộ dữ liệu (theo lineage) | Kho văn bản (theo văn bản) |
| -------------- | -------------------------: | --------------------------: |
| Thông tư       | 45,6%                     | 42,8%                      |
| Nghị định      | 43,8%                     | 20,5%                      |
| Quyết định     | 2,1%                      | 25,6%                      |
| Luật + Bộ luật | 5,1%                      | 3,3%                       |


- **Miền** (theo lineage; một lineage có thể mang nhiều nhãn): "khác" 66,5%, giao thông 13,1%,
doanh nghiệp – đầu tư 11,3%, thuế 7,6%, đất đai 2,8%. Có 14,3% lineage mang nhãn miền "không rõ
nguồn". Bốn miền của đề cương chỉ chiếm khoảng một phần ba.
- **Hiện tượng:** chỉ có sửa đổi và bãi bỏ. T5a có 10 lineage, nên chỉ đủ để minh họa.
- **Thời gian:** 33,4% dòng ranh giới hỏi từ năm 2025 trở đi.
- [Suy luận] Model trả lời sai ở câu năm 2025–2026 có thể vì chưa từng thấy luật mới (vượt hạn dữ
liệu huấn luyện), chứ chưa chắc vì kém suy luận thời gian. Việc cần làm: báo kết quả tách theo mốc
hỏi trước và sau hạn dữ liệu của từng model.
- [Suy luận] Mẫu được chọn ngẫu nhiên theo seed, đây là điểm tốt. Nhưng mẫu đi qua ba lần lọc: model
viết được câu hỏi, không có cờ cấu trúc, không bị loại sau khi kiểm. Bộ còn lại vì vậy nghiêng về
điều khoản dễ diễn đạt và những ca đồ thị làm đúng (xem G3).

**G3. Gold dẫn xuất từ chính đồ thị của hệ đề xuất.** [Đo, theo datasheet N1]

- Gold lấy từ chuỗi phiên bản mà hệ đề xuất cũng dùng. Bước trích sự kiện L2 chỉ bắt được 62,2%
số lần sửa đổi.
- Dòng nào đồ thị làm sai thì bị loại và thay bằng lineage kế tiếp. Vì vậy bộ còn lại là những ca đồ
thị làm đúng, có lợi cho hệ dùng KG, đúng ở chỗ RQ2 và RQ3 cần chứng minh.
- Gold độc lập là cách phòng duy nhất, nhưng hiện mới điền 0/75 dòng ở mỗi phiếu.

**G8. Sắp xếp bộ máy 2025.** [Đo]

- Có 21 lineage T2/T3 mang ranh giới vào 28/02–01/03/2025 hoặc 30/06–01/07/2025. Trong đó, 16
lineage có `changed_span` nhắc tới cơ quan hay đơn vị hành chính (cấp huyện, thị trấn, Sở, Cục,
Phòng…). Con số này đếm bằng từ khóa, chưa phải kết luận.
- Trong số đó có ca là thay đổi thật (chuyển thẩm quyền sang một cơ quan có chức năng khác), cũng có
ca chỉ đổi tên (R1-ii).
- 66/1.120 dòng ranh giới (5,9%) hỏi đúng ngày 30/06 hoặc 01/07/2025.
- Việc cần làm: đưa 16 lineage này cho luật sư phân loại theo R1-ii/R4 trước khi người gán nhãn
làm tới.

**G11. Lời văn gold hỏng dấu.** [Đo]

- Có ít nhất 1 lineage mà đáp án ngắn chứa chữ hỏng dấu. Tôi mới quét theo vài mẫu chữ, chưa quét
toàn bộ.
- Scorer chuẩn hóa nhưng giữ dấu (`norm()` trong `scripts/eval/score_vilextime.py`), nên câu trả lời
viết đúng chính tả bị chấm sai; chỉ câu trả lời chép nguyên văn kho mới được chấm đúng. Lỗi này có
lợi cho hệ RAG chép văn bản.
- Việc cần làm: quét toàn bộ đáp án ngắn tìm âm tiết không có trong tiếng Việt. Dòng hỏng thì gán
`khong_dat` (`gold_wrong`) theo quy tắc hiện có, không sửa tay lời văn luật.

**G14. Nhãn kế thừa.** [Đo] Có 1 dòng `giua_khoang` (T2) hỏi sau 01/07/2025 mà đáp án vẫn nêu "cấp
huyện", trong khi dòng ranh giới mà nó lấy nhãn (`label_of`) được kiểm ở mốc trước ngày đó. R4 phải
xét theo `as_of` của chính từng dòng.

### 3.3 Datasheet / Data Card (G12)

`docs/vilextime-datasheet.md` theo đúng khung Gebru, nhưng nội dung đã cũ:


| Datasheet ghi                                                      | Thực tế ngày 23/10                                                            |
| ------------------------------------------------------------------ | ----------------------------------------------------------------------------- |
| `release.jsonl` schema 1.4.0; 2.730 dòng, 653 lineage, 503 văn bản | `data/vilextime_dataset/`, schema 2.0.0; 2.383 dòng, 609 lineage, 502 văn bản |
| Có chế độ `sau_het_hieu_luc`                                       | Đã bỏ từ 20/10                                                                |
| T5 một nhóm, T6 một nhóm                                           | T5a/T5b, T6a/T6b                                                              |
| Bộ kiểm chéo "chỉ người, gán mù"                                   | D5: 19 dòng không mù; bản hòa giải do AI soạn                                 |
| Nhãn model, người audit theo mẫu                                   | HD 3.0 §6: nhãn model không được tính                                         |
| Mục 7 "Chưa xong" theo HD 2.0                                      | Việc còn lại nay theo `docs/plans/active/vilextime-dinh-nghia-chot.md`        |


Còn thiếu so với chuẩn:


| Mục (Gebru / ACL / NeurIPS)     | Hiện có                      | Cần thêm                                                                |
| ------------------------------- | ---------------------------- | ----------------------------------------------------------------------- |
| Động cơ, người làm, tài trợ     | Có; thiếu tài trợ            | Ghi "không có tài trợ", hoặc ghi nguồn                                  |
| Thành phần, thống kê, split     | Có, nhưng số cũ              | Lấy từ `manifest.json` của bản `--final`                                |
| Nhiễu nhãn                      | Thiếu                        | Tỷ lệ lỗi còn sót (luật sư kiểm một mẫu dòng `dat`)                     |
| Quy trình thu thập              | Một phần                     | Khung thời gian, công cụ, ngày chụp corpus                              |
| Người gán nhãn (ACL D)          | Thiếu                        | Chuyên môn, cách tuyển, thù lao, thời gian, toàn văn hướng dẫn          |
| Dùng AI khi làm dữ liệu (ACL E) | Một phần                     | Ghi thêm việc AI soạn bản hòa giải D4                                   |
| Mục đích dùng và không nên dùng | Chỉ có cách báo kết quả      | Không phải tư vấn pháp lý; không đại diện câu hỏi thật; rủi ro dùng sai |
| Phân phối, giấy phép            | CC BY 4.0, có ý kiến luật sư | Nơi đăng, ngày đăng, DOI, cách phát hành corpus                         |
| Bảo trì                         | Chỉ có quy tắc phiên bản     | Người giữ, liên hệ, cách báo lỗi, giữ bản cũ                            |
| Bản máy đọc                     | Thiếu                        | Croissant hoặc card Hugging Face; bản tiếng Anh                         |


## 4. Đã đạt (giữ nguyên)

- Định nghĩa chặt, có căn cứ luật, luật sư đã đồng ý (21/10). Chỉ có một bản định nghĩa duy nhất.
- Gold truy vết được tới văn bản tác động và câu lệnh sửa đổi.
- Scorer tương phản khó lách. [Đo] Lấy nguyên văn phiên bản sai làm câu trả lời cho 600 dòng T2/T3:
không dòng nào được chấm đúng.
- Chống rò rỉ: split chia theo văn bản; một lineage không nằm ở hai split; không câu hỏi nào nêu
Điều, Khoản, số hiệu; không có câu trùng.
- Mẫu chọn theo seed cố định, người không chọn tay. Cơ cấu nhóm đạt §9.
- Tái lập được: sha256 nằm trong `manifest.json`; `export_release.py --final` từ chối xuất khi còn
dòng chưa có nhãn cuối.
- Báo cáo trung thực: D5 ghi đúng việc chưa đạt ngưỡng và cách hòa giải đã làm.
- Giấy phép rõ: CC BY 4.0; luật sư xác nhận lời văn luật không thuộc đối tượng được bảo hộ.

## 5. Câu hội đồng sẽ hỏi

1. Bao nhiêu dòng test được người kiểm có dẫn chứng? Ai kiểm, mấy phút một dòng?
2. Đồng thuận theo HD 3.0 là bao nhiêu? Vì sao đổi từ κ sang AC1, và đổi lúc nào?
3. Ai hòa giải, và người đó có độc lập không?
4. Ở chỗ KG sai, làm sao biết gold đúng? Kết quả trên gold độc lập ra sao?
5. Nếu câu hỏi do người viết, BM25 còn thắng không?
6. Model sai ở câu năm 2025–2026 vì kém suy luận thời gian, hay vì chưa biết luật mới?

## 6. Lộ trình đóng khoảng trống trước 31/10

Ý chính: **kiểm kỹ một lõi test thay vì kiểm vội cả 1.099 dòng.** Các lô của phiếu đã rải đều theo
nhóm: lô 0–6 có 398 dòng (T1 52, T2 110, T3 42, T4 48, T5a 6, T6a 46, T6b 94), lô 0–9 có 587 dòng.
Mẫu gán chéo 106 dòng nằm trọn trong lô 1–9. Phần chưa kiểm phát hành dạng silver. Lõi này thấp hơn
mức sàn ở §9; định nghĩa cho phép điều đó ("không đạt sàn thì giảm quota, không nới điều kiện"),
nhưng phải ghi vào bảng lệch.

[Suy luận] Lõi cần bao nhiêu dòng: kiểm định McNemar với tỷ lệ dòng mà hai hệ kết quả khác nhau
ψ = 0,25, chênh lệch δ = 0,10, α = 0,05/9 (bước đầu của Holm), power 0,8, cần khoảng 320 câu độc lập.
Nhân hệ số cụm 1,5 (mỗi lineage có 2–3 dòng) thì cần khoảng 480 dòng. Lô 0–9 đủ để thấy chênh 10
điểm; lô 0–6 chỉ đủ để thấy chênh khoảng 12 điểm.


| Bước | Việc                                                                                          | Đóng             | Ai                                  | Ước tính [Suy luận]            |
| ---- | --------------------------------------------------------------------------------------------- | ---------------- | ----------------------------------- | ------------------------------ |
| 1    | B gán lô 0; họp với luật sư; ghi kết luận vào HD §7                                           | G4               | B, luật sư, nhóm                    | 2–3 giờ                        |
| 2    | Luật sư phân loại 16 lineage dính sắp xếp 2025; quét chữ hỏng dấu                             | G8, G11          | Claude lập danh sách; luật sư quyết | khoảng 2 giờ                   |
| 3    | A kiểm lô 1–6 (377 dòng còn lại), điền đủ 4 ô; nếu kịp thì làm tiếp tới lô 9 (566 dòng)       | G1               | A                                   | 25–47 giờ, ở mức 4–5 phút/dòng |
| 4    | B gán 106 dòng `kiem_cheo`; luật sư hòa giải; báo AC1, κ, p_pos, p_neg                        | G2, G5           | B, luật sư                          | 8–10 giờ                       |
| 5    | Luật sư kiểm ngẫu nhiên 30–50 dòng mà cả hai cùng `dat`                                       | G12 (nhiễu nhãn) | luật sư                             | 3–4 giờ                        |
| 6    | Gold độc lập: tối thiểu 60 dòng mù                                                            | G3               | A, B                                | 5–8 giờ                        |
| 7    | Sửa chữ "đăng ký trước"; viết lại datasheet theo bản `--final`; chuyển ADR 0005 sang Accepted | G6, G12, G17     | nhóm, Claude                        | 3–4 giờ                        |
| 8    | Báo kết quả tách theo `question_source` và theo mốc so với hạn dữ liệu của model              | G9, G10          | nhóm                                | khi chạy thực nghiệm           |


## Phụ lục. Cách đo lại


| Số                                     | Nguồn                                                                           | Cách tính                                                                                                                                                                             |
| -------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Dòng đã kiểm                           | `data/vilextime_dataset/manifest.json`                                          | khóa `boundary_rows`, `lineages`                                                                                                                                                      |
| Nhãn HD 3.0, số phút                   | `data/review/kiem_{A,B}.tsv`                                                    | đọc bằng `csv.DictReader`, tách bằng tab; lọc `guideline_version == "3.0"`; lấy trung vị cột `phut`                                                                                   |
| Mẫu gán chéo                           | `data/review/kiem_cheo.txt`, `kiem_B.tsv`                                       | đếm id có `verdict`                                                                                                                                                                   |
| D4                                     | `data/review/crosscheck_result.json`, `crosscheck_{A,B}.tsv`, `hoa_giai_D4.tsv` | tỷ lệ `dat` của từng người trên 300 dòng; bảng chéo; đếm số lần nhãn hòa giải trùng nhãn A hay B                                                                                      |
| Gold độc lập                           | `data/review/gold_{A,B}.tsv`                                                    | dòng có ô `noi_dung` hoặc `van_ban_ap_dung` khác rỗng                                                                                                                                 |
| Cơ cấu, model viết, miền, loại văn bản | `vilextime.jsonl` nối `vilextime_meta.jsonl` theo `id`                          | đếm theo lineage ở dòng `ranh_gioi`; kho văn bản: `data/derived/corpus/documents.jsonl`, trường `rank`                                                                                |
| Độ bám lời văn                         | như trên                                                                        | chuẩn hóa bằng `norm()` của scorer, bỏ khoảng 40 hư từ; tính tỷ lệ âm tiết của câu hỏi có trong `context`; lấy trung vị theo lineage                                                  |
| Scorer tương phản                      | như trên                                                                        | với mỗi dòng T2/T3 có đáp án, lấy `context` của phiên bản khác làm câu trả lời; chấm bằng `correct()`; distractor tính như `distractors()`                                            |
| Sắp xếp 2025                           | như trên                                                                        | dòng `ranh_gioi` T2/T3 có `as_of` là 28/02, 01/03, 30/06 hoặc 01/07/2025; `changed_span` khớp từ khóa thị trấn, đặc khu, huyện, tỉnh, Bộ, Sở, Ủy ban, Cục, Chi cục, Phòng, xã, phường |
| Chữ hỏng dấu                           | cột `answer`                                                                    | khớp mẫu `xuât`, `giây (phép|tờ|chứng)`                                                                                                                                               |
| Lô                                     | cột `lo` của `kiem_A.tsv`                                                       | đếm theo lô và nhóm con                                                                                                                                                               |


