# Hướng dẫn gán nhãn ViLexTime

Phiên bản hướng dẫn: **1.2** (29/09/2026). Các thay đổi so với 1.1 đều là hệ quả của
phản biện `docs/reports/JUDGE_DATASET.md`:
- dòng anh em không còn mặc định đúng theo nhãn của dòng ranh giới (§5.1);
- audit có thêm bước kiểm hiệu lực tại mọi ngày hỏi, và các luật audit bắt buộc
  mới (§6);
- có loại dòng mới `sau_het_hieu_luc` (§3);
- người audit phải là người.

So với 1.0: câu dẫn là một phần của đáp án (§1), có mã `transitional_rule` (§2), có
lớp `meta_issues` và quy trình cho nhãn do model gán (§6). `review.guideline_version`
của bản ghi phát hành và `data/review/labels.tsv` (trên từng nhãn) ghi phiên bản
hướng dẫn đã dùng.
Áp dụng cho đợt kiểm chéo D4 (Cohen κ) và mọi lượt kiểm tay sau đó.

## 1. Bạn đang kiểm cái gì

Mỗi dòng là **một câu hỏi được hỏi ở một mốc thời gian** (`as_of`), kèm **đáp án
chuẩn**: nội dung điều khoản có hiệu lực tại mốc đó. Đáp án do máy dựng từ chuỗi
phiên bản, không do LLM viết. Câu hỏi do LLM viết và chưa ai đọc.

Bạn trả lời **một câu duy nhất cho mỗi dòng**:

> Một luật sư đọc câu hỏi, biết ngày `as_of`, và tra đúng văn bản — người đó có
> trả lời **đúng bằng nội dung trong cột đáp án** không, và có trả lời được **chỉ
> một cách** không?

Có → `dat`. Không → `khong_dat` và ghi lý do.

**Câu dẫn là một phần của đáp án** (v1.1). Với mục trong danh sách, luật sư đọc
điểm cùng câu dẫn của nút cha tại `as_of` (cột `lead_in`). Ở nghị định xử phạt,
mức phạt nằm ở câu dẫn của khoản còn điểm chỉ nêu hành vi: câu hỏi "bị phạt bao
nhiêu" với đáp án là một điểm là `dat` nếu câu dẫn nêu mức phạt.

## 2. Nhãn (từ vựng đóng, không thêm mã mới trong đợt kiểm)

| Cột | Giá trị | Ghi chú |
|---|---|---|
| `verdict` | `dat` · `khong_dat` | Cohen κ tính trên cột này |
| `reasons` | một hoặc nhiều mã bên dưới, cách nhau bằng dấu phẩy | Chỉ điền khi `khong_dat` |
| `note` | tự do | Bắt buộc khi có `gold_wrong` hoặc `other` |

Mã lý do:

| Mã | Khi nào dùng |
|---|---|
| `question_ambiguous` | Câu hỏi khớp **nhiều điều khoản** hoặc nhiều mục trong danh sách; đáp án chuẩn chỉ là một trong số đó |
| `question_leaks` | Câu hỏi đã nói ra đáp án, nêu số hiệu/Điều/Khoản, ký hiệu mục ("c)"), hoặc để lộ phiên bản nào |
| `gold_wrong` | Nội dung ở cột đáp án **không đúng** là điều khoản có hiệu lực tại `as_of` (sai phiên bản, vế "trước sửa đổi" thực ra đã là bản sửa, text bị cắt mất phần được hỏi) |
| `group_mismatch` | Câu hỏi không làm được việc của nhóm: T2/T4 không chạm chỗ thay đổi (hai mốc trả lời như nhau); T3 chỉ chạm một lần sửa; T6 hỏi kiểu có/không; T5 hỏi vào phần không đổi |
| `unanswerable_as_asked` | Câu hỏi đúng chủ đề nhưng không thể trả lời bằng đáp án (hỏi "khi nào" mà đáp án không nói thời hạn, hỏi "ai" mà đáp án không nêu chủ thể...) |
| `transitional_rule` | **v1.1.** Điều khoản chuyển tiếp của văn bản sửa đổi giữ quy định cũ cho đúng quan hệ trong câu hỏi (ví dụ hồ sơ nộp trước ngày hiệu lực), nên nội dung ở cột đáp án không phải quy định được áp dụng. Ghi Điều chuyển tiếp ở `note` |
| `other` | Lỗi khác — mô tả ở `note` |

Lớp thứ hai, **chỉ ở `data/review/labels.tsv`**, không vào κ: `meta_issues` ghi lỗi
siêu dữ liệu của đồ thị mà không làm sai đáp án tại `as_of` (T1 hỏi ngày hôm sau
ngày hiệu lực nên `valid_to` sai không đổi đáp án). Mã: `valid_to_wrong` ·
`valid_from_wrong` · `group_wrong` · `citation_path_wrong` · `doc_number_wrong` ·
`lead_in_wrong` · `other`. Một dòng có thể `dat` và vẫn mang `meta_issues`.

## 3. Cách kiểm từng nhóm

Đọc **câu hỏi → mốc → đáp án**, rồi mở link văn bản (cột `source_url`, là văn bản
bị sửa) khi cần kiểm cột đáp án. Cột `note_for_annotator` ghi ngày ký và ngày hiệu
lực của văn bản sửa đổi ở dòng T5.

- **T1** (một phiên bản): kiểm chủ yếu `question_ambiguous` — với mục trong danh
  sách, câu hỏi phải ghim được đúng mục, không phải cả danh sách.
- **T2** (hai phiên bản khác rõ): hai dòng cùng câu hỏi, khác mốc. Câu hỏi phải
  chạm vào chỗ đã đổi; nếu đọc câu hỏi mà hai đáp án đều trả lời được như nhau →
  `group_mismatch`. Kiểm **vế trước** (mốc sớm) với văn bản gốc: nếu văn bản gốc
  trên cổng đã là lời văn sau sửa đổi → `gold_wrong`.
- **T3** (chuỗi ≥ 3 phiên bản): câu hỏi phải tách được mọi mốc, không chỉ mốc đầu
  và cuối.
- **T4** (hai phiên bản gần giống): chỗ đổi thường chỉ là một cụm từ (tên cơ
  quan, số ngày). Câu hỏi phải hỏi đúng vào cụm đó; hỏi chung chung là
  `group_mismatch`. Vế trước kiểm như T2.
- **T5** (hồi tố): mốc sau nằm **trong khoảng hồi tố** — sau ngày có hiệu lực,
  trước ngày ký. Đáp án chuẩn ở mốc đó là **nội dung mới**. Chỉ đánh `gold_wrong`
  nếu văn bản sửa đổi không thật sự có hiệu lực từ ngày đó; việc văn bản có thuộc
  Điều 152 hay không là việc của luật sư (`data/review/t5_documents.tsv`), không
  phải của đợt gán nhãn.
- **T6** (hết hiệu lực một phần): mốc sau có đáp án rỗng và
  `no_answer_reason = provision_repealed`. Đúng khi điều khoản đã bị bãi bỏ trong
  khi văn bản vẫn còn hiệu lực. Câu hỏi không được giả định quy định đang tồn tại.
  `repeal_mode = ancestor` (24 dòng, từ 28/09): điều khoản không bị bãi bỏ đích
  danh mà mất hiệu lực vì Điều/Khoản/Mục/Chương chứa nó bị bãi bỏ (`repealed_by`
  ghi nút cha và event). Kiểm như T6 thường; nếu câu bãi bỏ của nút cha thật ra
  giữ lại điều khoản này (ví dụ "trừ điểm a") thì đánh `gold_wrong`.
- **`sau_het_hieu_luc`** (v1.2): cùng câu hỏi với lineage, nhưng hỏi **sau ngày văn
  bản đích hết hiệu lực**. Đáp án chuẩn là không có đáp án
  (`no_answer_reason = document_repealed`). `accepted_evidence` là câu của văn bản
  chấm dứt ("... hết hiệu lực kể từ ...", "Thông tư này thay thế Thông tư số ...").
  Kiểm câu đó có thật sự chấm dứt **cả** văn bản và đúng ngày không. Nếu chỉ chấm
  dứt một phần, hoặc có điều khoản chuyển tiếp giữ nguyên quy định được hỏi, thì
  đánh `gold_wrong`.

## 4. Ví dụ

| Câu hỏi | Nhãn | Vì sao |
|---|---|---|
| "Một doanh nghiệp tái xuất hàng hoá thì phải làm thủ tục hải quan tại đâu?" (đáp án: "tại cửa khẩu nhập hoặc cửa khẩu tái xuất") | `dat` | Một cách hiểu, đáp án trả lời trọn |
| "Trong lĩnh vực xử phạt chứng khoán, hình thức xử phạt chính loại c) được quy định như thế nào?" | `khong_dat`: `question_leaks` | Ký hiệu mục "c)" là vị trí, không phải nội dung |
| "Những hành vi nào bị phạt tiền từ 20.000.000 đồng đến 40.000.000 đồng?" (đáp án: một mục b) | `khong_dat`: `question_ambiguous` | Đáp án đúng là cả danh sách |
| T2 — "Chế độ bảo hiểm xã hội đối với dân quân thường trực được xác định ra sao?" với hai đáp án khác nhau về căn cứ áp dụng | `dat` | Chạm đúng khía cạnh đã đổi |
| T4 — câu hỏi về "cơ quan nào" khi chỗ đổi là "Bộ Tài nguyên và Môi trường" → "Bộ Nông nghiệp và Môi trường" | `dat` | Hỏi đúng cụm đã đổi |
| Hỏi "được xác định ra sao" khi đáp án chỉ là tiêu đề Điều ("Điều 12. Các chỉ số…") | `khong_dat`: `gold_wrong` | Nội dung nằm ở nút con; lẽ ra đã bị cờ `answer_in_children` |

## 5. Quy trình

1. Hai người gán nhãn **độc lập**, mỗi người một file (`data/review/crosscheck_A.tsv`,
   `crosscheck_B.tsv`), không trao đổi trong lúc làm. Tên thật không ghi vào
   file; dùng mã `A` / `B` (28/09: A = CMT, B = NMT; bảng ánh xạ chỉ nằm ở plan,
   không phát hành). Chỉ gán dòng `ranh_gioi`. Dòng anh em `giua_khoang` cùng câu hỏi
   và cùng phiên bản đáp án, nên **câu hỏi** dùng chung nhãn. **Gold thì không** (v1.2).
   Dòng anh em hỏi ở ngày muộn hơn, nên mọi lần sửa đổi hay bãi bỏ mà chuỗi phiên bản
   bỏ sót trong khoảng giữa hai ngày đều làm gold sai. Phản biện 29/09 tìm được 10/11
   lỗi gold ở dòng anh em.

   Các lỗi này do `scripts/check/check_validity.py` dò. Hàng đợi ở
   `data/review/validity_queue.tsv`: dòng thuộc bộ κ mang `sau_D4` và chỉ được
   phân xử sau hoà giải (bước 4). Dòng ngoài bộ κ được phân xử ngay, với
   `decision` là `loi` · `co_the_sai` · `bao_dong_gia` · `da_sua`.
2. Không sửa câu hỏi hay đáp án trong file — chỉ điền `verdict`, `reasons`, `note`.
3. Xong cả hai, chạy `python scripts/review/crosscheck.py kappa` để tính κ
   (mục tiêu ≥ 0,6). Nếu thấp hơn: viết lại hướng dẫn ở các điểm hay lệch, tăng
   phiên bản hướng dẫn, kiểm lại (plan, Gói D).
4. Dòng hai người lệch nhau được người thứ ba (hoặc hai người cùng ngồi) hoà giải;
   kết quả ghi ở cột `adjudicated` của file A. **Nhãn thô của từng người được
   giữ nguyên** và phát hành cùng bộ dữ liệu (ADR 0003 §9).
5. Dòng `khong_dat` sau hoà giải: câu hỏi viết lại hoặc dòng bị loại, không lặng lẽ
   sửa đáp án chuẩn — sửa gold là thay đổi MAJOR (ADR 0003 §8).

## 6. Nhãn do model gán và audit cuốn chiếu (v1.1, bổ sung v1.2)

Chốt 28/09 (CMT): để kịp tiến độ, model (`claude-opus-5-5`) gán nhãn trước, nhóm
audit theo từng đợt. Bốn ràng buộc giữ cho số liệu còn bảo vệ được:

1. **Bộ kiểm chéo D4 chỉ gồm người, và gán mù.** Model không gán dòng nào của
   `crosscheck_A/B.tsv` cho tới khi cả A và B đã gán dòng đó; `labels.py add`
   từ chối. Cohen κ luôn là κ giữa hai người. Sau D4, nhãn của model trên 300
   dòng này có thể dùng làm phân tích phụ (độ đồng thuận model–người), không
   thay A hay B.
2. **Nhãn nào cũng ghi người gán.** `labeler` là `claude-opus-5-5`, hoặc
   `human:<mã>` cho người. Nhãn của model không bao giờ ghi đè nhãn của người;
   mỗi (dòng, người gán) là một dòng riêng trong `labels.tsv`.
3. **Audit bắt buộc** (cột `audit_required`) gồm:
   - mọi `khong_dat` và mọi `meta_issues` của model;
   - một mẫu cố định 20% các `dat` (`sha1(id) % 5 == 0`).

   Từ **v1.2**, bắt buộc thêm:
   - dòng mà văn bản sửa đổi có điều khoản chuyển tiếp (`actor_has_transitional`);
   - dòng hỏi sau 01/07/2025 mà câu hỏi hoặc đáp án còn nói "cấp huyện";
   - mọi nhãn model gán theo v1.2, tức nhãn của các lineage thay thế.

   Áp luật mới cho nhãn đã có bằng `labels.py mark-audit`.

   Người audit điền `audit` (`dong_y` · `khong_dong_y`), `auditor` và `audit_note`.
   `auditor` phải là `human:<mã>`; `import-audit` từ chối model. Nếu tỷ lệ
   `khong_dong_y` trong mẫu `dat` của một nhóm vượt 5%, audit toàn bộ `dat` của nhóm
   đó. `python scripts/review/labels.py report` báo các tỷ lệ này.

   **Audit không chỉ đọc cột gold** (v1.2). Phiếu audit có các cột:
   - `also_asked_at`: các ngày cùng câu hỏi được hỏi lại (dòng anh em, dòng
     `sau_het_hieu_luc`);
   - `amended_by`: các văn bản tác động;
   - `legal_markers`, `validity_flags`: dấu hiệu từ `validity_queue.tsv`.

   Người audit mở lịch sử văn bản (lược đồ, văn bản hợp nhất trên cổng) để kiểm ba
   điều ở **mọi** ngày đó:
   - (a) không có văn bản nào sửa đổi hay bãi bỏ điều khoản trước ngày hỏi;
   - (b) văn bản chưa hết hiệu lực toàn bộ;
   - (c) điều khoản chuyển tiếp không giữ quy định cũ cho đúng quan hệ trong câu
     hỏi. Nếu có, đánh `transitional_rule` và ghi Điều.

   Lỗi ở dòng anh em ghi vào `audit_note` kèm ngày và văn bản.

   Đáp án ngắn "đòi thừa" so với câu hỏi được đề xuất sửa trong `audit_note`. Nhóm
   sửa trong `data/vilextime/short_answers.jsonl` với `by: human:<mã>`.
4. **Model viết câu hỏi thì không tự chấm được lỗi của chính mình một cách khách
   quan.** Câu hỏi do `claude-opus-5-5` viết, nên tỷ lệ `dat` của model là cận
   trên. Khoá luận báo tỷ lệ đồng ý khi audit, không báo nhãn model như nhãn người.

Phán đoán pháp lý (T5 theo Điều 152, điều khoản chuyển tiếp) do model **đề xuất
kèm trích dẫn câu chữ**, ở cột riêng; quyết định vẫn là của cố vấn luật ở các cột
`LUẬT SƯ:` của `data/review/t5_documents.tsv`, `t5_items.tsv`.

