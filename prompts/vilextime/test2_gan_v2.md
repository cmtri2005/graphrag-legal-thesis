# Gán nhãn câu hỏi ViLexTime bộ test 2 — lời dặn cho LLM, bản 2

Bạn là một người gán độc lập và là model, không phải người hay luật sư. Nhãn của bạn được ghi rõ là nhãn LLM.
Chỉ đọc `HUONG_DAN.md` và `tasks.jsonl` trong thư mục này. Không đọc thư mục khác, không tra web, không trao đổi
với phiên khác. Lời dặn này tự đủ: mọi quy tắc cần dùng đều nằm ở đây.

Bộ dữ liệu đo một hệ hỏi đáp pháp luật có biết chọn đúng phiên bản điều khoản tại một ngày hay không. Bạn quyết một
câu hỏi có đủ tốt để chấm điểm hệ thống hay không. Không có mục tiêu về tỷ lệ đạt. Đừng thiên về đạt, cũng đừng thiên
về không đạt: chọn "xấu" khi có căn cứ, chọn "tốt" sau khi đã đối chiếu xong.

## Mỗi dòng của tasks.jsonl

| Trường | Nghĩa |
|---|---|
| `group`, `loai` | Nhóm: T2, T3, T6. `loai` nói thêm: "T2 gần giống", "T6 đích danh", "T6 cấp trên" |
| `question` | Câu hỏi, cùng một câu cho mọi mốc |
| `rows` | Các mốc. `as_of`: ngày hỏi. `answer`: lời văn đáp án tại mốc, `null` nghĩa là đáp án đúng là "không còn quy định". `short_answer`: đoạn ngắn dùng để chấm, trích từ `answer`; dấu `…` nối các đoạn. `cau_dan`: câu dẫn của nút cha |
| `cac_phien_ban` | Chuỗi phiên bản: khoảng hiệu lực, văn bản mở từng bản, và `chỗ đổi` giữa hai bản liền nhau do máy tính |
| `goi_y_cho_moi` | T6: máy tìm trong kho văn bản những chỗ nội dung có thể đã chuyển tới. Chỉ là chỗ cần nhìn, có thể sai |
| `quy_dinh_tuong_tu` | T2, T3: máy tìm trong kho những quy định giống nhất đang có hiệu lực ở mốc cuối. Chỉ là chỗ cần nhìn, có thể sai |
| `sources.base` | Đoạn văn bản gốc |
| `sources.actors` | Văn bản tác động: `passage` (đoạn sửa đổi hoặc bãi bỏ), `transitional` (điều khoản chuyển tiếp), `in_force` (điều hiệu lực) |

## Điều kiện từng nhóm

- **T2:** hỏi ở hai mốc phải ra **đúng hai** đáp án pháp lý khác nhau. "Gần giống": hai bản giống nhau trên 90%, chỗ đổi
  thường chỉ là một con số hay một cụm từ, và câu hỏi phải hỏi vào đúng chỗ đó.
- **T3:** qua các mốc phải ra **ít nhất ba** đáp án pháp lý khác nhau. Lần đổi chỉ về tên hay hình thức không tính là
  trạng thái mới.
- **T6:** mốc trước có đáp án; mốc sau điều khoản đã bị bãi bỏ, đích danh hoặc theo điều khoản cấp trên, nên đáp án đúng là
  "không còn quy định".

## Ba quy tắc nền

1. **`as_of` là ngày tính hiệu lực pháp lý.** Đáp án là phiên bản có hiệu lực tại `as_of` theo khoảng hiệu lực do chính các
   văn bản quy định, kể cả hiệu lực trở về trước. Sự việc coi như phát sinh tại `as_of`.
2. **Câu hỏi hỏi nội dung, không hỏi vị trí.** Đáp án là quy phạm đang điều chỉnh nội dung được hỏi tại `as_of`. Chỉ đổi mức
   phạt thì vẫn là cùng một quy phạm.
3. **Câu dẫn là một phần của đáp án.** Mục trong danh sách phải đọc cùng `cau_dan`. Ở nghị định xử phạt, mức phạt nằm ở câu
   dẫn của khoản.

## Bốn câu hỏi

Trả lời đủ bốn câu, theo thứ tự. Nhãn cuối do máy suy ra: đạt khi Q1 `dung`, Q2 `co`, Q3 `co`, Q4 `khong`.

### Q1. Đáp án ở mỗi mốc có đúng văn bản không?

Đọc `sources.actors` và `cac_phien_ban`, đối chiếu cả `answer` lẫn `short_answer` ở từng mốc.

- `gold_wrong`: sai phiên bản, sai ngày; lời văn thiếu hay thừa so với văn bản; chữ hỏng dấu do trích xuất ("sản xuât",
  "giây phép"). Văn bản tác động có hiệu lực tách phần ("trừ quy định tại khoản 2, 3 Điều này", "các quy định về … có hiệu lực
  kể từ ngày ký"): nếu lần sửa thuộc phần ngoại lệ thì là `gold_wrong`, ghi ngày đúng. Câu "áp dụng từ năm ngân sách X" là
  hiệu lực trở về trước, tính từ 01/01/X. T6: văn bản bãi bỏ phải còn hiệu lực; T6 cấp trên mà câu bãi bỏ giữ lại điều khoản
  này ("trừ điểm a") thì là `gold_wrong`.
- `reference_only`: đáp án chỉ dẫn chiếu ("thực hiện theo quy định tại Chương IV Thông tư này"), kể cả khi khớp lời văn.
- `other`: `short_answer` sai, hoặc thiếu ý mà câu hỏi hỏi. Ghi ý thiếu ở `note`, trích đoạn đúng từ `answer`.

**Thiếu đoạn nguồn không phải bằng chứng là sai.** Nếu không có `passage` nói về lần sửa này, đối chiếu bằng `cac_phien_ban`;
không thấy mâu thuẫn thì chọn `dung` và ghi `[phân vân] thiếu đoạn nguồn: …` ở `note`.

T6, mốc trước ngày bãi bỏ mà đáp án đúng tại mốc thì Q1 vẫn `dung`, kể cả khi nội dung sau đó chuyển sang chỗ khác. Chuyển chỗ
xét ở Q4.

### Q2. Câu hỏi có hỏi vào đúng chỗ đổi không?

Che đáp án, đọc câu hỏi, rồi nhìn `chỗ đổi`: hỏi ở các mốc, người trả lời có phải nói những điều khác nhau không? So câu hỏi với
**chỗ đổi**, không so với cả điều khoản.

- `group_mismatch`: các mốc trả lời như nhau; T3 chỉ ra hai đáp án, hoặc chỉ một lần đổi chạm câu hỏi; T6 câu hỏi **chỉ** hỏi
  có/không (câu ghép có vế hỏi nội dung thì chấm theo vế đó).
- `cosmetic_only`: chỗ đổi chỉ là hình thức: hoa thường, dấu câu, khoảng trắng, đánh số.
- `rename_only`: chỉ đổi tên cơ quan, đơn vị do sắp xếp bộ máy, nhiệm vụ giữ nguyên (Bộ Giao thông vận tải → Bộ Xây dựng; Bộ Tài
  nguyên và Môi trường → Bộ Nông nghiệp và Môi trường). Căn cứ khoản 1 Điều 3 Nghị quyết 190/2025/QH15: tên đã chuyển từ ngày
  sắp xếp, nên hai mốc cùng một đáp án pháp lý.
- `auto_reference_update`: chỉ cập nhật dẫn chiếu sang văn bản mới, khi chính văn bản đã quy định tự áp văn bản thay thế.

**Vẫn là thay đổi thật:** chuyển sang cơ quan khác về chức năng, không phải cơ quan kế thừa; thay danh sách đơn vị hành chính
không tương ứng một-một, ví dụ "xã, phường, thị trấn" → "xã, phường, đặc khu".

### Q3. Câu hỏi có rõ không?

Một luật sư đọc câu hỏi, biết ngày, tra đúng văn bản: có trả lời đúng bằng đáp án này, và chỉ trả lời được **một cách** không?

- `question_ambiguous`: nhiều điều khoản cùng trả lời được; hoặc câu hỏi rộng hơn đáp án. Ví dụ hỏi "những hành vi nào bị phạt từ
  20 đến 40 triệu đồng" mà đáp án chỉ là một mục b, trong khi đáp án đúng là cả danh sách. Với mục trong danh sách, câu hỏi phải
  ghim đúng mục.
- `unanswerable_as_asked`: đáp án không trả lời được đúng điều câu hỏi hỏi: hỏi "khi nào" mà đáp án không có thời hạn, hỏi
  "ai" mà đáp án không nêu chủ thể.
- `question_leaks`: câu hỏi nêu ngày, số hiệu văn bản, Điều, Khoản, ký hiệu mục ("loại c)"); chép sẵn đáp án; hoặc nêu sẵn cụm của
  bản cũ mà bản mới đã đổi.

### Ranh giới giữa Q1, Q2, Q3

Một lỗi chỉ ghi ở một câu, theo chỗ lỗi nằm:

| Lỗi | Ghi ở |
|---|---|
| Lời văn, ngày, phiên bản, hay đoạn ngắn sai so với văn bản; đoạn ngắn thiếu ý trong khi cả `answer` đủ ý | Q1 |
| Câu hỏi rõ nhưng hỏi vào phần không đổi | Q2 |
| Câu hỏi không ghim được một đáp án, kể cả khi câu hỏi rộng hơn cả `answer` | Q3 |

### Q4. Có quy định nào khác đang thay cho đáp án này không?

Chọn `khong`, `co` kèm mã, hoặc `khong_chac` kèm `relocation_unclear` (chỉ dùng cho T6).

- `superseded_by_other_norm`: văn bản cấp cao hơn, hoặc văn bản cùng cơ quan ban hành sau, quy định khác về cùng vấn đề mà không
  sửa điều khoản này. Luật và văn bản dưới luật khác nhau thì đáp án theo Luật. Văn bản mới quy định khác mà không nói thay thế
  không làm văn bản cũ hết hiệu lực; đó là xung đột, và ghi mã này.
- `restructuring_2025`: mốc từ 01/03/2025 (hợp nhất bộ) hoặc từ 01/07/2025 (bỏ cấp huyện, sáp nhập tỉnh) mà đáp án vẫn nêu cơ quan,
  cấp, địa danh cũ chưa được sửa lời văn.
- `transitional_rule`: chỉ khi điều khoản chuyển tiếp kéo dài bản cũ cho cả việc **mới phát sinh** sau ngày hiệu lực và mốc rơi vào
  khoảng đó (ví dụ "được tiếp tục cấp theo mẫu cũ đến hết 31/10/2022" với mốc 16/07/2022), hoặc giữ bản cũ cho đúng quan hệ mà
  câu hỏi tự nêu. Chuyển tiếp chỉ giữ việc phát sinh **trước** ngày bản mới có hiệu lực (hồ sơ đã tiếp nhận, giấy phép đã cấp, hợp
  đồng đã ký, hành vi đã xảy ra, dự án đã phê duyệt, định mức đã ban hành, nhiệm kỳ đang dở) thì **không** vướng.
- `relocated`: T6, nội dung bị bãi bỏ đã chuyển chỗ, đạt đủ bảy yếu tố dưới đây. Ghi chỗ mới ở `note`.

**T6: luôn tìm chỗ chuyển.** Tìm theo thứ tự, trong `goi_y_cho_moi` và `sources`: (a) cùng văn bản bãi bỏ, ở các cụm "Bổ sung…",
"Sửa đổi Điều… như sau" cùng đợt; (b) khoản cha, khoản anh em của cùng điều; (c) văn bản khác có hiệu lực cùng ngày hoặc được dẫn
tới; (d) văn bản cấp cao hơn quy định cùng vấn đề, khi đó dùng `superseded_by_other_norm`.

So quy định cũ với chỗ mới theo bảy yếu tố. Chỉ xét **phần câu hỏi hỏi**: chỗ mới đổi phần câu hỏi không hỏi thì không làm hỏng yếu tố.

| # | Yếu tố | Đạt khi |
|---|---|---|
| 1 | Hành vi | giữ nguyên về bản chất |
| 2 | Đối tượng, chủ thể | giữ nguyên; địa danh chỉ đổi tên do sáp nhập, phạm vi giữ nguyên, vẫn đạt |
| 3 | Điều kiện áp dụng | giữ nguyên |
| 4 | Cấu trúc quy định | chỉ đổi vị trí, thời hạn |
| 5 | Chế tài, hậu quả pháp lý | cùng loại chế tài; mức được đổi. Đổi loại chế tài hay thêm hình thức phạt bổ sung thì không đạt |
| 6 | Thẩm quyền, hiệu lực kế thừa | cùng cơ quan ban hành hoặc cơ quan kế thừa, hiệu lực pháp lý không thấp hơn |
| 7 | Dấu vết chuyển tiếp | có dấu vết nối hai quy định: cùng đợt "Bãi bỏ… Bổ sung…", câu "thay thế", điều khoản chuyển tiếp |

- Đạt đủ bảy → `co`, `relocated`.
- Không chắc ở yếu tố nào, hoặc yếu tố 7 không có dấu vết → `khong_chac`, `relocation_unclear`, ghi chỗ nghi ở `note`.
- Không có quy định kế thừa, hoặc yếu tố 1–6 rõ ràng không đạt → `khong`.
- Khoảng trống: khoản cũ hết hiệu lực từ ngày A, chỗ mới có hiệu lực từ ngày B sau A. Hỏi giữa A và B thì đáp án rỗng là đúng.

**Giới hạn của Q4:** bạn chỉ thấy phần máy đưa, không phải cả hệ thống pháp luật. `khong` nghĩa là "không thấy trong phần được
đưa", và `search_log` phải ghi đúng điều đó. Không dùng trí nhớ để khẳng định có một văn bản ngoài nguồn. Nếu nhớ có, ghi
`[phân vân] nhớ có: …` ở `note`.

## Ví dụ

| Nhóm | Câu hỏi và chỗ đổi | Nhãn | Vì sao |
|---|---|---|---|
| T2 | "Phải lưu trữ những bài sát hạch và biên bản nào". Bản sau thêm "bài sát hạch lái xe trên phần mềm mô phỏng…" | Đạt | Câu hỏi chạm đúng phần đổi |
| T2 | "Giấy chứng nhận loại tàu bay được công nhận theo bộ quy chế do bộ nào ban hành". Chỉ thay "Bộ Giao thông vận tải" bằng "Bộ Xây dựng" | Q2 `rename_only` | Tên đã chuyển từ 01/03/2025, hai mốc cùng một đáp án pháp lý |
| T2 gần giống | "Được cấp dầu gội đầu với định lượng bao nhiêu mỗi năm". 800 ml → 1.000 ml | Đạt | Chỗ đổi là con số được hỏi |
| T3 | "Giấy phép lái xe hợp lệ khi đáp ứng điều kiện gì về cơ quan cấp và thông tin trên giấy phép". Ba trạng thái qua hai lần sửa | Đạt | Ba đáp án khác nhau |
| T6 | Trình độ cán bộ quản lý vận hành cơ sở hỏa táng. Khoản cha bị bãi bỏ, không có quy định kế thừa | Đạt | Q4 `khong` |
| T6 | Điều kiện phòng cháy khi khai thác cảng biển. Cùng văn bản bãi bỏ viết lại điều khác và đưa vào "Đáp ứng các điều kiện về an toàn, vệ sinh lao động, phòng, chống cháy, nổ…" | Q4 `relocated` | Nội dung chuyển sang chỗ mới cùng đợt |
| T6 | Hồ sơ giấy thông hành sang Lào theo thông tư. Nghị định ban hành sau quy định tờ khai khác thay mẫu cũ | Q4 `superseded_by_other_norm` | Văn bản cấp cao hơn quy định khác về cùng vấn đề |
| — | "…hình thức xử phạt chính loại c) được quy định như thế nào?" | Q3 `question_leaks` | Ký hiệu mục là vị trí, không phải nội dung |

## Ba lỗi hay gặp

- Chọn tốt khi mới nhìn qua, chưa đối chiếu nguồn.
- Bỏ bước tìm chỗ chuyển ở T6.
- So câu hỏi với cả điều khoản thay vì với chỗ đổi.

## Đầu ra

Ghi `labels.jsonl` trong thư mục này, đúng một dòng JSON cho mỗi dòng của `tasks.jsonl`:

```json
{"lineage_id": "...", "q1": "", "q1_reason": "", "q2": "", "q2_reason": "", "q3": "", "q3_reason": "", "q4": "", "q4_reason": "", "quote": "", "search_log": "", "note": ""}
```

- Giá trị: `q1` là `dung` hoặc `sai`; `q2`, `q3` là `co` hoặc `khong`; `q4` là `khong`, `co` hoặc `khong_chac`.
- Mã lý do chỉ ghi khi chọn câu trả lời xấu, đúng một mã của câu đó trong các danh sách trên; câu tốt để chuỗi rỗng.
- `quote`: bắt buộc, một câu trích **nguyên văn** từ `sources.actors`; không có thì từ `sources.base`. Chép đúng từng chữ.
- `search_log`: bắt buộc mọi dòng, một câu ghi đã xem những gì cho Q4.
- `note`: bắt buộc khi chọn `other`, `relocated`, `relocation_unclear`, `superseded_by_other_norm`, `gold_wrong`. Nói ngắn lý do.
- Phân vân thì vẫn chọn một đáp án, ghi `[phân vân] …` ở `note`.

Làm từng dòng theo thứ tự, không bỏ dòng nào. Xong thì kiểm số dòng của `labels.jsonl` bằng số dòng của `tasks.jsonl`.
Không đổi lời dặn, không thêm trường.
