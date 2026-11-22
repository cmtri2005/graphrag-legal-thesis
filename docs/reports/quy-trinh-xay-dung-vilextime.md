# Quy trình xây dựng bộ dữ liệu ViLexTime

Tài liệu này dành cho người **không có quyền vào mã nguồn**. Đọc xong, người đọc phải hiểu được ba thứ:

1. Pipeline đi từ văn bản pháp luật thô đến bộ dữ liệu cuối như thế nào.
2. Ở mỗi chỗ dùng LLM hoặc agent, model được giao việc gì, được đưa gì, bị dặn gì (ý tưởng của system prompt), và ai kiểm đầu ra.
3. Vì sao thiết kế như vậy.

Các đoạn system prompt được trích hoặc diễn lại ngay trong bài. Tên file, tên lệnh chỉ nằm ở Phụ lục A để nhóm tra lại.
Số liệu được đếm lại ngày 22/11/2026, hoặc lấy từ tài liệu nội bộ của nhóm.

Đánh giá điểm mạnh, điểm yếu của bộ dữ liệu nằm ở tài liệu riêng (kiểm định 22/11).

---

## 1. Bộ dữ liệu này là gì, và ý tưởng cốt lõi

### 1.1 Bài toán

Luật Việt Nam bị sửa đổi, bãi bỏ liên tục. Cùng một câu hỏi như "thời hạn nộp hồ sơ là bao lâu?" có thể có đáp án khác nhau
ở hai thời điểm. Một hệ hỏi đáp pháp luật (thường là RAG) phải trả lời theo **quy định đang có hiệu lực vào ngày được
hỏi**. ViLexTime đo đúng khả năng đó.

Mỗi dòng của bộ dữ liệu có:

| Trường | Ý nghĩa |
|---|---|
| `question` | Câu hỏi tiếng Việt, **không chứa ngày** |
| `as_of` | Ngày hỏi, ví dụ 15/06/2019 |
| `context` | Toàn văn điều khoản có hiệu lực vào ngày đó (đáp án đầy đủ) |
| `answer` | Đáp án ngắn: đoạn cốt lõi, nguyên văn từ `context`, là phần được chấm |
| `answerable` | Có đáp án không. Nếu điều khoản đã bị bãi bỏ thì đáp án đúng là "không còn hiệu lực" |

**Ví dụ.** Điều khoản về hồ sơ giải thể cơ sở bảo trợ xã hội (Nghị định 68/2008/NĐ-CP) từng đổi một câu:

| | Lời văn |
|---|---|
| Phiên bản cũ | "a) Đơn xin giải thể cơ sở bảo trợ xã hội nêu rõ lý do xin giải thể;" |
| Phiên bản mới | "a) Đơn đề nghị giải thể cơ sở bảo trợ xã hội, trong đó nêu rõ lý do xin giải thể (Mẫu số 4 Phụ lục kèm theo);" |

Câu hỏi (viết một lần, dùng cho mọi ngày): *"Theo quy định về thủ tục giải thể cơ sở bảo trợ xã hội, loại đơn trong hồ sơ
giải thể được gọi tên thế nào và phải kèm theo yêu cầu gì về biểu mẫu?"*

- Hỏi với `as_of` trước ngày sửa → đáp án là bản cũ.
- Hỏi với `as_of` sau ngày sửa → đáp án là bản mới.

Hệ nào trả bản mới cho ngày cũ (hoặc ngược lại) là **trích dẫn đúng điều khoản nhưng sai phiên bản**.

### 1.2 Nguyên tắc thiết kế

> **Đáp án không do LLM đặt ra.** Đáp án, các phiên bản và ngày chuyển phiên bản được **code dẫn xuất** từ một "kho
> phiên bản" dựng từ cơ sở dữ liệu quốc gia vbpl.vn. LLM chỉ viết câu hỏi, cắt đáp án ngắn từ lời văn có sẵn, lọc ứng
> viên và gán nhãn kiểm tra.

Hệ quả thiết kế xuyên suốt:
- Mọi thứ LLM viết ra đều đi qua một **cổng code** hoặc một **người/agent độc lập** trước khi vào bộ dữ liệu.
- Cái gì bị loại thì **ghi lại kèm lý do**, không âm thầm xóa.
- Model, lượt chạy, phiên bản lời dặn đều được ghi lại (provenance).

### 1.3 Từ vựng

- **Điều khoản (provision):** một Điều, Khoản hoặc Điểm của văn bản.
- **Lineage:** một điều khoản cùng toàn bộ các phiên bản của nó theo thời gian. Mỗi lineage có **một** câu hỏi.
- **Phiên bản:** lời văn của điều khoản trong một khoảng hiệu lực.
- **Văn bản tác động:** văn bản sửa đổi, bổ sung, thay thế hoặc bãi bỏ một văn bản khác.
- **Câu dẫn (lead-in):** câu mở đầu của nút cha, ví dụ "Hồ sơ gồm có:". Một Điểm "a) Đơn xin giải thể…" chỉ có nghĩa khi đọc cùng câu dẫn.
- **Gold:** đáp án đúng, do kho phiên bản tính ra.
- **CMT:** tác giả chính của khóa luận, người duyệt nhãn.

### 1.4 Sáu nhóm câu hỏi

| Nhóm (tên công khai) | Mô tả | Thử điều gì |
|---|---|---|
| `control` (T1) | Chỉ một phiên bản, chưa từng sửa | Thêm ngày không được làm hệ kém đi |
| `two_versions` (T2) | Sửa một lần, đáp án đổi theo | Có theo kịp thay đổi không |
| `near_identical` (T4) | Hai phiên bản giống nhau trên 90%, chỉ khác một số hay một cụm | Bẫy "trích đúng điều khoản, sai phiên bản" |
| `multi_versions` (T3) | Từ ba phiên bản trở lên | Lần theo nhiều lần sửa liên tiếp |
| (T5, không vào bản cuối) | Văn bản sửa đổi có hiệu lực trở về trước ngày ký | Hiệu lực hồi tố |
| `repealed` (T6) | Điều khoản bị bãi bỏ nhưng văn bản chứa nó vẫn còn hiệu lực | Sau bãi bỏ, đáp án đúng là "không còn hiệu lực" |

### 1.5 Sơ đồ toàn bộ quy trình

Khung `LLM / AGENT` là chỗ có model AI tham gia.

```
 vbpl.vn (API công khai + sitemap)
   │ ① CÀO: chọn văn bản theo từ khóa → mở rộng theo quan hệ sửa đổi/bãi bỏ → tải toàn văn, lịch sử, cây điều khoản
   ▼
 ~23 nghìn văn bản thô
   │ ② DỰNG KHO PHIÊN BẢN (luật viết tay, không LLM)
   │    đọc câu lệnh "sửa đổi…như sau", "bãi bỏ…" → áp theo thời gian → chuỗi phiên bản từng điều khoản
   │    (hàng chờ ca khó: LLM xem trước, người kiểm)                                 ◄── LLM xem trước
   ▼
 KHO PHIÊN BẢN = nguồn duy nhất của đáp án đúng
   │ ③ CHỌN ỨNG VIÊN theo nhóm T1–T6, xáo bằng seed cố định (code)
   ▼
 11.408 lineage ứng viên
   │ ④ LỌC ứng viên bẫy pháp lý                                                     ◄── LLM / AGENT
   │ ⑤ VIẾT CÂU HỎI (một câu cho mỗi lineage) → bộ kiểm tự động loại câu hỏng       ◄── LLM / AGENT
   │ ⑥ CHỌN ĐÁP ÁN NGẮN (đoạn nguyên văn) → code kiểm "đúng là đoạn của lời văn"    ◄── LLM
   │ ⑦ DỰNG DÒNG: mỗi lineage thành nhiều dòng theo ngày hỏi (code)
   ▼
 PHIẾU GÁN NHÃN
   │ ⑧ HAI AGENT AI gán mù Q1–Q4 → đo đồng thuận → AGENT HÒA GIẢI ca bất đồng → CMT duyệt → AI kiểm lại ca rủi ro
   │                                                                                 ◄── AGENT
   ▼
 Bộ test cuối: 199 lineage, 722 dòng
   │ ⑨ NGƯỜI ĐỌC MÙ độc lập + rà sót sửa đổi → sửa kho                             ◄── NGƯỜI
   ▼
 Bản phát hành 5.1.1 (Data in Brief)
```

### 1.6 Các con số chính

| Con số | Giá trị |
|---|---:|
| Văn bản trong kho thô (ảnh chụp 12/09/2026) | 23.139 |
| Văn bản trong corpus truy xuất (17/09/2026) | 17.333 |
| Câu lệnh sửa đổi/bãi bỏ trích được | 56.624 |
| Trong đó áp được vào kho | 21.892 |
| Phiên bản điều khoản trong kho | 1.477.102 |
| Lineage ứng viên | 11.408 |
| Câu hỏi LLM đã viết ở vòng 1 | 2.246 |
| Lineage đưa vào gán nhãn cho bộ cuối | 374 |
| Lineage được giữ / dòng phát hành | **199 / 722** |

---

## 2. Nguồn dữ liệu và cách cào (không dùng LLM)

### 2.1 Nguồn

Nguồn duy nhất là cơ sở dữ liệu quốc gia về văn bản pháp luật **vbpl.vn** của Bộ Tư pháp. Nhóm chỉ lấy **văn bản quy
phạm pháp luật cấp trung ương** (luật, nghị định, thông tư, nghị quyết, quyết định…). Nhóm lấy cả văn bản đã hết hiệu
lực và **không bao giờ lọc theo trạng thái hiệu lực**, vì bài toán cần lịch sử.

Giao diện web của vbpl.vn gần như không chứa dữ liệu. Dữ liệu thật lấy qua API của cổng biên tập, mỗi văn bản có:
- **Chi tiết:** số hiệu, tiêu đề, ngày ban hành, ngày bắt đầu/hết hiệu lực, trạng thái, toàn văn HTML, danh sách quan hệ với văn bản khác (sửa đổi, thay thế, bãi bỏ, hướng dẫn, căn cứ…).
- **Lịch sử hiệu lực:** ban hành, có hiệu lực, hết hiệu lực, hết hiệu lực một phần (kèm danh sách điều khoản hết hiệu lực).
- **Lược đồ quan hệ, cả chiều vào:** ai sửa, ai bãi bỏ văn bản này.
- **Cây điều khoản:** Phần/Chương/Mục/Điều/Khoản/Điểm, mỗi nút có mã định danh ổn định.

Không cần đăng nhập, chỉ cần header giống trình duyệt. Nhóm cào tuần tự, cách nhau tối thiểu 0,3 giây, thử lại tối đa 3
lần với lỗi mạng và 5xx. Lỗi 4xx không bao giờ thử lại vì đó là văn bản đã bị gỡ. Các mã loại quan hệ không có nhãn chữ
trong API, nên nhóm tự đối chiếu 13 mã với giao diện trình duyệt ngày 24/08/2026. Gặp mã lạ thì chương trình dừng và báo
lỗi, không tự gán.

### 2.2 Các bước cào

1. **Chọn seed.** Lọc danh sách văn bản theo từ khóa trong tên (slug) của 4 lĩnh vực: đất đai, thuế, doanh nghiệp–đầu tư, giao thông. Được 9.329 seed, thêm 8 từ khóa còn thiếu thì thành 9.806.
2. **Mở rộng xuôi.** Từ seed, đi theo các cạnh **phả hệ** (sửa đổi, thay thế, bãi bỏ, đính chính, hợp nhất, hướng dẫn). Cạnh trích dẫn và căn cứ ban hành được ghi lại nhưng không đi tiếp, để không lan sang lĩnh vực khác. Corpus lên 13.863 văn bản.
3. **Mở rộng ngược.** Quan hệ chỉ ghi một chiều: nếu B sửa A thì cạnh nằm ở B. Nên phải dùng lược đồ quan hệ chiều vào để tìm các văn bản *tác động lên* corpus, tải về, lặp đến khi hội tụ. Thêm 2.335 văn bản; corpus lên 20.491 văn bản, 147.413 cạnh. 97,7% văn bản "hết hiệu lực một phần" có đủ văn bản tác động trong corpus.
4. **Tải lịch sử hiệu lực** cho mọi văn bản.
5. **Rà lĩnh vực.** Máy chỉ *gợi ý* văn bản nghi lạc lĩnh vực; **người quyết định**. Văn bản bị loại không bị xóa, chỉ bị bỏ qua khi đọc.
6. **Lấy cây điều khoản và ghép lời văn.** Ghép đoạn HTML vào đúng nút của cây. Cây và lời văn mâu thuẫn thì đưa vào hàng chờ, không tự chọn.
7. **Cập nhật định kỳ.** So thời điểm sửa của sitemap, kiểm lại văn bản "còn hiệu lực" mà ngày hết hiệu lực đã qua.

Độ phủ so với toàn bộ văn bản trung ương: khoảng trống thật ước 0,4–1,6%. Khoảng 5,4% văn bản không có lời văn trên cổng (chỉ
có PDF bị chặn); nhóm không OCR.

Một số bẫy đã gặp: ngày "createdDate" trong lịch sử chỉ là ngày pháp lý khi do hệ thống tự tạo; cờ "có nội dung" có thể sai;
văn bản cũ dùng HTML không có id.

---

## 3. Dựng kho phiên bản (không dùng LLM để quyết định)

Đây là phần **quyết định đáp án đúng**. Nó chạy hoàn toàn offline, bằng luật viết tay.

### 3.1 Ý tưởng

Một điều khoản không có sẵn "lịch sử phiên bản" trên cổng. Phải tự suy ra bằng cách đọc chính văn bản tác động. Ví dụ
Nghị định B có câu "Điều 5 được sửa đổi, bổ sung như sau: …" có hiệu lực từ ngày X. Từ đó suy ra Điều 5 của nghị định A
có phiên bản mới kể từ X, với lời văn mới là phần sau dấu hai chấm.

### 3.2 Các bước

1. **Dựng chỉ mục** văn bản, điều khoản, khoảng hiệu lực cấp văn bản.
2. **Ánh xạ danh sách "điều khoản hết hiệu lực" của cổng** ("Khoản 3, Điều 9…") vào nút trong cây điều khoản.
3. **Trích sự kiện.** Đọc lời văn của văn bản tác động, tìm các mẫu như "Bãi bỏ khoản 2 Điều 11 Nghị định số X" hay "Sửa đổi khoản 2 Điều 5 như sau: …". Phân giải số hiệu văn bản và vị trí điều khoản, lấy lời văn mới. Mỗi câu lệnh thành một **sự kiện** có trạng thái.
4. **Áp bãi bỏ cả văn bản.** Văn bản bị bãi bỏ toàn bộ mà cổng không ghi ngày hết hiệu lực: lấy ngày từ câu lệnh bãi bỏ.
5. **Áp sự kiện theo thứ tự thời gian** thành chuỗi phiên bản cho từng điều khoản. Mỗi phiên bản có khoảng hiệu lực. Sự kiện bị từ chối được ghi lại kèm lý do.

### 3.3 Kết quả và giới hạn

| Trạng thái sự kiện | Số lượng | Nghĩa |
|---|---:|---|
| `verified` | 3.260 | Khớp danh sách hết hiệu lực của cổng |
| `auto_accepted` | 19.564 | Phân giải được vị trí, có ngày và lời văn |
| `needs_review` | 33.800 | Chưa tự quyết được |

Lý do chính của nhóm `needs_review`: không tìm thấy vị trí (11.165), thiếu lời văn mới (6.279), tác động cả văn bản
(5.777), cấu trúc lệch (5.161). Tổng: **21.892 sự kiện áp được, 34.732 bị từ chối**.

**Đây là giới hạn đã biết của kho:** một lần sửa đổi không áp được nghĩa là kho có thể giữ một phiên bản quá hạn. Đó
đúng là loại lỗi mà các đợt đọc mù về sau tìm ra (§10).

### 3.4 Chỗ có LLM ở tầng kho

LLM **không quyết định** phiên bản. Với hai hàng chờ mà code không tự giải được (sự kiện bị từ chối, và ngày hiệu lực
chưa xác định), một LLM đọc câu nguồn và **đề xuất** vị trí hoặc ngày, đánh dấu `llm_reviewed`. Người kiểm sau đó. Quyết
định cuối cùng được đọc lại nguyên trạng ở mỗi lần dựng kho, nên dựng lại cho ra cùng kết quả.

### 3.5 Corpus truy xuất

Từ kho, nhóm dựng corpus mà mọi hệ trong thực nghiệm phải tìm kiếm. Corpus chỉ gồm văn bản đủ điều kiện (trung ương,
có mốc thời gian, có lời văn): **17.333 văn bản**. Có ba lớp đơn vị:

| Lớp | Đơn vị | Số lượng | Ai dùng |
|---|---|---:|---|
| "Như đã ban hành" | Điều khoản ở bản ban hành đầu, và từng câu lệnh sửa đổi/bãi bỏ | 1.455.372 + 53.991 | Baseline RAG phẳng |
| "Theo phiên bản" | Một phiên bản của một điều khoản, kèm khoảng hiệu lực | 1.477.102 | Hệ đề xuất, baseline lọc theo phiên bản |
| Văn bản | Văn bản kèm ngày của chính nó | 17.333 | Bộ lọc cấp văn bản |

---

## 4. Chọn ứng viên câu hỏi (không dùng LLM)

1. **Phân nhóm.** Mỗi điều khoản vào **đúng một** nhóm, theo thứ tự hiếm trước: T5 → T6 (bãi bỏ qua nút cha) → T3 → T6 (bãi bỏ trực tiếp) → T4 → T2 → T1. Mỗi ngày hỏi có gold là phiên bản có hiệu lực ngày đó. Cặp phiên bản có lời văn giống hệt nhau (11,1%) bị loại.
2. **Xáo và xếp hạng một lần bằng seed cố định**, giới hạn số lineage mỗi văn bản (để không có một văn bản chiếm hết).
3. **Chọn theo thứ hạng.** Sau khi có câu hỏi, đi theo đúng thứ hạng đó và lấy lineage đầu tiên qua mọi cổng kiểm, đến khi đủ chỉ tiêu. Ai được chọn do seed và bộ kiểm quyết định, không do người chọn.

Kết quả: pool 11.408 lineage (T2 5.428, T6 2.806, T1 2.497, T3 476, T5 201); mẫu xếp hạng 1.794 lineage.

---

## 5. Cách nhóm dùng LLM: tổng quan

| # | Việc | Model / agent | Cổng kiểm sau đó |
|---|---|---|---|
| A | Xem trước hàng chờ ca khó của kho | LLM | Người kiểm |
| B | **Lọc ứng viên** có bẫy pháp lý | Codex, subagent Claude Code | Một số mục có kết luận người sẵn để chấm lại agent |
| C | **Viết câu hỏi** | claude-opus-5-5, deepseek-flash, claude-haiku-5-5, Codex, claude-sonnet-5-5 | Bộ kiểm tự động (10 luật) + gán nhãn |
| D | **Chọn đáp án ngắn** | claude-opus-5-5, claude-haiku-5-5, Codex | Code kiểm "là đoạn nguyên văn" + gán nhãn |
| E | **Gán nhãn Q1–Q4** (hai agent độc lập) | AI-A: Claude Code. AI-B: Codex CLI | Đo đồng thuận bằng code + CMT duyệt |
| F | **Hòa giải** ca bất đồng | Agent hòa giải (claude-opus-5-5) | Hash hai nhãn gốc + CMT quyết ca còn lại |
| G | **Kiểm lại** ca rủi ro (bãi bỏ, ca CMT nghi) | Agent phân xử | CMT |

Năm nguyên tắc dùng chung:
1. LLM không tạo gold.
2. Mọi đầu ra LLM đi qua một cổng code hoặc một người độc lập.
3. Hai agent gán nhãn **không thấy nhãn của nhau**. Agent hòa giải **không thấy kết quả của hệ được đo**. Agent **không có quyền ghi file**.
4. Cái bị loại được giữ lại kèm lý do.
5. Ghi lại model, lượt chạy và dấu vân tay của lời dặn. Chỗ nào không ghi được thì nói thẳng là "không ghi".

---

## 6. Bước B: Lọc ứng viên bằng LLM

### 6.1 Vì sao cần

Sau vòng đầu, nhóm thấy nhiều ứng viên T2, T3, T6 có **bẫy pháp lý** mà câu hỏi không cứu được: điều khoản chỉ dẫn chiếu
sang chỗ khác, bị luật cấp cao hơn đè, bị sắp xếp bộ máy 2025 làm lỗi thời, hoặc nội dung bị bãi bỏ thật ra đã được **chuyển
sang chỗ khác**. Nên *trước khi viết câu hỏi*, một agent đọc từng ứng viên và quyết giữ hay loại.

### 6.2 Agent được giao gì

- **Ai làm:** agent Codex và subagent Claude Code.
- **Đầu vào mỗi mục:** một điều khoản cùng chuỗi phiên bản, lời văn từng phiên bản và khoảng hiệu lực, đoạn văn bản gốc, đoạn văn bản tác động (sửa đổi/bãi bỏ, điều chuyển tiếp, điều hiệu lực), câu dẫn của nút cha. Với T6 có thêm *gợi ý của máy* về chỗ nội dung có thể đã chuyển tới. Lời dặn nhấn mạnh gợi ý này **chỉ cho biết chỗ cần nhìn, không phải kết luận**.
- **Quyền hạn:** chỉ đọc gói công việc và tra văn bản pháp luật gốc trên web. Không mở thư mục nào khác.
- **Kiểm chéo ngầm:** một số mục đã có kết luận của người và dùng để chấm lại agent. Agent *không biết mục nào*, và được dặn đừng đoán.

### 6.3 Ý tưởng của lời dặn: "không chắc thì loại"

> Giữ chỉ khi đủ cả các điều dưới đây. Thiếu một điều thì loại với đúng một mã. **Không chắc thì loại**: kho ứng viên còn
> nhiều, câu hỏi tốt quan trọng hơn số lượng.

| Điều | Agent kiểm gì | Mã loại |
|---|---|---|
| 1 | Lời văn là nội dung pháp lý, không phải chỉ dẫn chiếu ("thực hiện theo Chương IV…") | `reference_only` |
| 2 | Chuỗi phiên bản khớp văn bản tác động: ngày hiệu lực của lần sửa, kể cả hiệu lực tách phần ("trừ khoản 2…"); lời văn không hỏng dấu do trích xuất | `gold_wrong` |
| 3 | Không bị quy phạm khác đè: văn bản cấp cao hơn, hoặc cùng cơ quan ban hành sau, quy định khác về cùng vấn đề mà không sửa điều khoản này. Luật và văn bản dưới luật khác nhau thì theo Luật | `superseded_by_other_norm` |
| 4 | Không vướng sắp xếp bộ máy 2025 (mốc sau 01/03/2025 hoặc 01/07/2025 mà lời văn còn tên cơ quan, cấp, địa danh cũ) | `restructuring_2025` |
| 5 | Không có điều khoản chuyển tiếp buộc việc *mới phát sinh* sau ngày hiệu lực phải theo bản cũ | `transitional_rule` |
| 6 (T2, T3) | Mỗi lần chuyển là thay đổi **thực chất**, không chỉ đổi hoa thường/dấu câu/đánh số, không chỉ đổi tên cơ quan kế thừa nhiệm vụ, không chỉ cập nhật dẫn chiếu tự áp | `cosmetic_only`, `rename_only`, `auto_reference_update` |
| 7 (T3) | Có ít nhất ba trạng thái pháp lý khác nhau sau khi bỏ các lần chuyển không thực chất | `single_change` |
| 8 (T2, T3) | Phần đổi hỏi được thành một câu hỏi rõ (mức tiền, thời hạn, chủ thể, điều kiện…) | `other` |
| 9 (T6) | Văn bản bãi bỏ còn hiệu lực và không giữ lại điều khoản ("trừ điểm a") | `gold_wrong` |
| 10 (T6) | **Nội dung không chuyển sang chỗ khác** (xem dưới) | `relocated`, `relocation_unclear` |

Điều 5 có một chi tiết tinh tế mà lời dặn nêu rõ. Câu hỏi hỏi "pháp luật quy định gì tại mốc", tức coi sự việc phát sinh
tại mốc. Điều khoản chuyển tiếp chỉ giữ bản cũ cho việc phát sinh **trước** ngày bản mới có hiệu lực (hồ sơ đã nhận, giấy
phép đã cấp, hợp đồng đã ký) thì **không** làm hỏng ứng viên. Chỉ loại khi chuyển tiếp kéo dài bản cũ cho cả việc *mới*
phát sinh, ví dụ "được tiếp tục cấp theo mẫu cũ đến hết 31/10/2022" mà mốc hỏi là 16/07/2022.

**Điều 10, kiểm "nội dung đã chuyển chỗ chưa" cho T6.** Đây là rủi ro lớn nhất của nhóm repealed: nếu điều khoản bị bãi
bỏ nhưng nội dung được viết lại ở chỗ khác, thì "không còn hiệu lực" là đáp án *sai*. Agent phải tìm theo thứ tự:
1. Cùng văn bản bãi bỏ (có "Bổ sung…" hay "Sửa đổi Điều… như sau" cùng đợt không).
2. Khoản cha, khoản anh em.
3. Văn bản khác có hiệu lực cùng ngày hoặc được dẫn tới.
4. Văn bản cấp cao hơn.

Rồi so quy định cũ với chỗ mới theo **bảy yếu tố**: hành vi; đối tượng, chủ thể; điều kiện áp dụng; cấu trúc (chỉ đổi vị
trí, thời hạn); loại chế tài, hậu quả (mức phạt được đổi); thẩm quyền và hiệu lực kế thừa; dấu vết nối hai quy định. Đủ
bảy thì `relocated` kèm chỗ mới. Không chắc ở yếu tố nào thì `relocation_unclear` kèm chỗ nghi. Rõ là không có quy định
kế thừa thì ứng viên đạt.

### 6.4 Đầu ra

Một bảng TSV, đúng một dòng cho mỗi mục: `item`, `quyet_dinh` (`giu`/`loai`), `ma` (một mã trong danh sách đóng), `can_cu`,
`ghi_chu`.
- `can_cu` bắt buộc là **một câu nguyên văn** từ văn bản tác động (hoặc văn bản khác) làm căn cứ. Với T6 giữ lại, ghi đã tìm chỗ chuyển ở đâu.
- `ghi_chu` bắt buộc khi loại.
- Agent tự kiểm số mục và mục trùng sau mỗi gói, và không được đổi hướng dẫn giữa chừng.

---

## 7. Bước C: Viết câu hỏi bằng LLM

Đây là bước LLM tạo nhiều nội dung nhất.

### 7.1 Câu hỏi phải thỏa gì, và vì sao

Câu hỏi sẽ được hỏi ở **mọi ngày** của lineage, nên phải trung lập thời gian. System prompt dùng chung nói với model, đại ý:

> Bạn là người biên soạn câu hỏi cho ViLexTime, bộ dữ liệu đánh giá khả năng trả lời đúng nội dung pháp luật **tại một
> mốc thời gian xác định**. Đầu vào là một điều khoản kèm tên văn bản và câu dẫn của đơn vị cha. Viết **một câu hỏi** mà
> phần ĐÁP ÁN trả lời được trọn vẹn. Hệ thống chấm sẽ đưa câu hỏi này kèm một mốc thời gian riêng; cùng câu hỏi được hỏi
> ở nhiều mốc và cho các đáp án khác nhau. Đó là lý do có các ràng buộc dưới đây: chúng không phải hình thức.

**Đầu ra:** đúng một dòng, kết thúc bằng dấu hỏi. Không giải thích, không đánh số, không ngoặc kép.

**Bốn điều tuyệt đối không được làm** (kèm ví dụ sai/đúng trong prompt):

| Cấm | Ví dụ sai → đúng (trích từ prompt) |
|---|---|
| **1. Nhắc thời gian**: ngày, tháng, năm, "hiện hành", "hiện nay", "mới nhất", "đang có hiệu lực". Câu hỏi sẽ được hỏi cả ở 2016 lẫn 2026 | ✗ "Theo quy định pháp luật **hiện hành**, hồ sơ giải thể gồm những giấy tờ gì?" ✓ "Theo quy định về thủ tục giải thể cơ sở bảo trợ xã hội, hồ sơ phải có những giấy tờ nào?" |
| **2. Dẫn vị trí**: số hiệu văn bản, "Điều 5", "Khoản 2", "Điểm a", "a)". Câu hỏi hỏi *nội dung quy định thế nào*, không hỏi *điều số mấy viết gì*; "người biết số điều khoản thì đã không cần hỏi" | ✗ "Khoản 1 Điều 3 Thông tư 36/2016/TT-BTTTT quy định nội dung gì?" ✓ "Trong lĩnh vực cấp phép hoạt động báo nói và báo hình, giấy phép hoạt động phát thanh được cấp cho loại tổ chức nào?" |
| **3. Chép đáp án**: được dùng lại thuật ngữ trong tên văn bản và câu dẫn (đó là khung), nhưng không bê nguyên một mệnh đề dài từ đáp án, vì khi đó câu hỏi tự trả lời | — |
| **4. Bịa số**: mọi con số trong câu hỏi phải có trong ngữ cảnh đã đưa | — |

**Văn phong:** trung tính, như truy vấn tra cứu pháp luật. Không "cho em hỏi", "ạ", "nhé", không xưng hô, không lời chào.

**Neo vào chủ đề văn bản:** người hỏi không biết số hiệu nhưng biết lĩnh vực. Model lấy chủ đề từ tên văn bản (bỏ phần
"Thông tư số…" ở đầu) để khoanh vùng câu hỏi.

### 7.2 Hai dạng câu hỏi, và mở đầu được gán sẵn

Mỗi lineage được **gán trước** một dạng câu hỏi và một kiểu mở đầu; model **phải** theo.

| Dạng | Cách hỏi | Ví dụ mở đầu |
|---|---|---|
| **Tra cứu** | Hỏi thẳng quy định về một khía cạnh: điều kiện, thủ tục, thời hạn, thẩm quyền, mức phạt, đối tượng | "Theo quy định về <chủ đề>, …?" · "Pháp luật về <chủ đề> quy định … như thế nào?" · "Trong lĩnh vực <chủ đề>, …?" |
| **Tình huống** | Mô tả một chủ thể đang làm một việc rồi hỏi quy định áp dụng. Chủ thể là vai chung ("một doanh nghiệp", "một người điều khiển phương tiện"), không tên riêng; **không mang ngày**; không bịa tình tiết | "Một <chủ thể> <làm gì> thì …?" · "Khi <sự việc xảy ra>, <chủ thể> phải / được …?" · "Nếu <chủ thể> <hành vi>, …?" |

**Vì sao gán sẵn?** Lúc đầu để model tự chọn, nó mở **31/31** câu bằng "Trong …", vì mỗi lần gọi nó chỉ thấy một câu và
không biết các câu khác đã mở thế nào. Giờ code gán bằng hàm băm cố định từ mã lineage: một nửa "tra cứu", một nửa "tình
huống", mỗi dạng có 4 kiểu mở đầu. Cả bộ vì thế không lặp một khuôn.

### 7.3 Khi đáp án là một mục trong danh sách

Phần lớn điều khoản là một mục nằm dưới câu dẫn ("Phạt tiền từ … đối với một trong các hành vi sau đây:"). Hỏi về cả danh
sách là sai, vì đáp án khi đó là mọi mục, không phải mục được giao. Prompt dạy model **dựng lại khung bằng câu dẫn, rồi
ghim đúng mục bằng chủ đề riêng của nó**:

> CÂU DẪN: 2. Phạt tiền từ 20.000.000 đồng đến 40.000.000 đồng đối với một trong các hành vi vi phạm sau đây:
> ĐÁP ÁN: b) Đào tạo, bồi dưỡng, huấn luyện chuyên môn, nghiệp vụ cho nhân viên hàng không không đúng nội dung; không đủ số giờ…
>
> ✗ "Những hành vi nào bị phạt tiền từ 20.000.000 đồng đến 40.000.000 đồng?" (đáp án là cả danh sách)
> ✓ "Trong nhóm hành vi bị phạt tiền từ 20.000.000 đồng đến 40.000.000 đồng về xử phạt hành chính trong lĩnh vực hàng không dân dụng, hành vi đào tạo huấn luyện chuyên môn nghiệp vụ sai quy định được mô tả như thế nào?"

### 7.4 Cho phép từ chối

Có điều khoản không thể ghim mà không lộ đáp án: một cụm danh từ trần trong danh sách ("d) Đá gốc tạo vỏ phong hóa;"), một
dòng tiêu đề Điều, hay một câu lệnh sửa đổi văn bản khác. Khi đó model phải in đúng một từ:

`KHONG_DU_NGU_CANH`

Prompt nói rõ lý do: *bỏ một ứng viên là chuyện bình thường và đã được tính đến; viết một câu hỏi tồi tốn hơn nhiều vì nó
đi thẳng vào bộ dữ liệu.* Ở vòng 1, 333 trên 387 câu bị loại là kiểu từ chối này.

### 7.5 Phần riêng từng nhóm

Mỗi nhóm có thêm một đoạn lời dặn, ghép vào sau lời dặn chung:

| Nhóm | Ý tưởng của lời dặn riêng |
|---|---|
| **T1** (một phiên bản) | Đây là nhóm đối chứng, đo xem hệ có tra đúng điều khoản khi không có gì gây nhiễu. Câu hỏi phải rõ, một cách hiểu. Hỏi theo đúng loại của câu dẫn: định nghĩa thì hỏi định nghĩa, điều kiện thì hỏi điều kiện, mức phạt thì hỏi mức phạt |
| **T2** (hai phiên bản) | Nhóm lõi. **Hỏi trúng chỗ đã đổi thì hai mốc ra hai đáp án; hỏi chệch thì hai mốc ra cùng đáp án và cặp tương phản thành vô dụng.** Hỏi vào *khía cạnh* chứa chỗ đổi, không hỏi nội dung cụ thể của phiên bản nào. Phải trung lập: bản cũ 30 ngày, bản mới 45 ngày thì hỏi "thời hạn là bao lâu", không nhắc số nào. Kiểm tra tự thân: nếu đọc câu hỏi mà không đoán được cụm nào đã đổi thì câu hỏi đã chệch |
| **T3** (từ ba phiên bản) | Nhóm mỏng và khó nhất, đo khả năng lần qua nhiều lần sửa liên tiếp. Chọn khía cạnh **đổi xuyên suốt chuỗi**, nhiều phiên bản nhất. Cấm nhắc điều khoản từng được sửa |
| **T4** (gần giống hệt) | "Bẫy trích dẫn". Hai bản giống nhau trên 90%, khác có khi chỉ một cụm. **Đọc kỹ chỗ khác nhau trước khi viết một chữ nào.** Ví dụ trong prompt: bản cũ "đào tạo … *cho nhân viên hàng không*", bản mới "đào tạo … *hàng không*"; khác biệt là phạm vi đối tượng, nên câu hỏi hỏi thẳng vào phạm vi |
| **T5** (hồi tố) | Như T2. Nhưng câu hỏi sẽ được hỏi cả ở ngày *nằm trong khoảng hồi tố*, lúc văn bản sửa đổi chưa được ký nhưng về pháp lý nội dung mới đã áp dụng. Cấm nhắc hồi tố hay ngày ký |
| **T6** (bãi bỏ) | Model chỉ thấy nội dung lúc còn hiệu lực. Câu hỏi phải đứng vững ở cả hai mốc (còn hiệu lực / đã bãi bỏ). Cấm "hiện hành, đang áp dụng". **Cấm câu có/không** ("Hành vi X có bị phạt không?"), vì sau khi bãi bỏ, "không" vừa đúng vừa sai theo hai nghĩa khác nhau. Hỏi dạng mở về nội dung |

### 7.6 Đầu vào mỗi lần gọi model

| Mục | Nội dung |
|---|---|
| TÊN VĂN BẢN | Tên văn bản chứa điều khoản |
| CÂU DẪN | Câu dẫn của nút cha |
| ĐÁP ÁN, hoặc PHIÊN BẢN 1…n | Lời văn các phiên bản. Một câu hỏi phục vụ mọi ngày, nên model thấy **mọi** phiên bản |
| CHỖ THAY ĐỔI (T2–T5) | Khác biệt **từng từ** giữa các phiên bản, **do code tính** |
| DẠNG CÂU HỎI, MỞ ĐẦU | Hai dòng gán sẵn như §7.2 |

**Điểm thiết kế quan trọng: code tìm chỗ khác nhau, model chỉ diễn đạt.** Lúc đầu nhóm đưa hai bản thô và để model tự tìm
chỗ đổi; không có gì kiểm model có tìm đúng không. Giờ chỗ đổi do code tính và đưa sẵn; việc của model chỉ là diễn đạt nó
thành câu hỏi, và không được nhắc nguyên văn phần bị bỏ hay phần được thêm, không được nói là "có sửa đổi".

### 7.7 Tham số gọi model

- `temperature = 0` (đầu ra ổn định).
- Mức suy luận thấp (viết một câu hỏi không cần suy luận sâu; mức cao thậm chí bị cắt giữa chừng).
- Trần 4.096 token cho một câu trả lời; nếu bị cắt thì thử lại một lần với gấp đôi.
- Mọi nhà cung cấp dùng chung dạng giao tiếp kiểu OpenAI; nhà cung cấp và model được chốt cứng để một khóa API thừa không âm thầm đổi nơi sinh câu hỏi.
- Mỗi câu hỏi lưu kèm: model, nhà cung cấp, nhiệt độ, ngày sinh, và **dấu vân tay 12 ký tự của system prompt**, để biết câu nào viết theo lời dặn nào.

### 7.8 Bộ kiểm tự động: "nothing the model writes is trusted"

Mọi câu model viết đều qua bộ kiểm. Câu bị loại được **ghi lại kèm lý do**, không bị âm thầm viết lại cho đến khi qua.

| Mã loại | Điều kiện |
|---|---|
| `not_one_line` | Không đúng một dòng |
| `insufficient_context` | Model tự từ chối (`KHONG_DU_NGU_CANH`) |
| `not_a_question` | Không kết thúc bằng dấu hỏi |
| `conversational_filler` | Có "ạ", "nhé", "cho em hỏi", lời chào |
| `presumes_the_present` | Có "hiện hành", "hiện nay", "mới nhất"… |
| `cites_a_provision` | Có số hiệu văn bản, hoặc "Điều/Khoản/Điểm/Chương/Mục + số", kể cả "a)" |
| `mentions_a_date` | Có ngày, tháng, năm (kiểm sau luật dẫn vị trí vì số hiệu văn bản chứa năm, như "36/2016/TT-…") |
| `unsourced_number` | Có con số không xuất hiện trong ngữ cảnh đã đưa |
| `copies_the_answer` | Có đoạn dài trùng đáp án mà không nằm trong khung (tên văn bản, câu dẫn). Tái dùng cụm có trong tên văn bản là luật neo chủ đề hoạt động đúng, không phải chép |
| `too_short` | Ít hơn 5 tiếng |

**Thử lại có điều kiện.** Câu bị loại được thử lại tối đa **2 lần**, và **gửi kèm lý do loại bằng lời mà model sửa được**.
Ví dụ với `cites_a_provision`: "Bỏ mọi số hiệu văn bản và mọi 'Điều/Khoản/Điểm/Chương/Mục' kèm số, kể cả ký hiệu mục như
'a)'. Hỏi nội dung quy định, không hỏi vị trí." Lý do phải gửi kèm: `temperature = 0` nên gửi lại y nguyên sẽ ra y nguyên
câu cũ. Riêng `insufficient_context` **không bao giờ thử lại**, vì đó là model từ chối đúng; hỏi lại là cãi lại một phán
đoán đúng.

**Chấm lại không tốn tiền.** Câu model viết được lưu nguyên. Khi đổi luật kiểm, nhóm chấm lại toàn bộ câu đã lưu mà không
gọi model.

**Nhận câu viết ngoài.** Một phiên Claude Code hay Codex có thể viết câu theo đúng lời dặn rồi nộp vào; câu đó được chấm y
như câu của nhà cung cấp, và bắt buộc ghi tên người viết.

### 7.9 Vòng bộ test 2 và lô bổ sung: viết theo gói, thêm một trần chống chép

Vào tháng 11, nhóm cho agent Codex và subagent Claude Code viết câu hỏi **theo gói** (mỗi gói nhiều mục; mỗi mục có nhóm
và đầu vào đúng như §7.6; kết quả là danh sách `{mục, câu hỏi}`; không viết được thì ghi `KHONG_DU_NGU_CANH`). Có thêm
cơ chế "viết lại": giao lại các mục bị loại kèm câu cũ và lý do loại.

Thêm một **trần tự động**: không quá **40%** số tiếng có nghĩa của câu hỏi nằm trong lời văn các phiên bản; vượt thì loại.
Lời dặn nói rõ đây là trần chống chép, không phải đích để hạ thấp: 30–40% là bình thường. Ba điều kèm theo:
- **Giữ nguyên thuật ngữ pháp lý chuẩn**: ngân hàng, thuế giá trị gia tăng, hóa đơn, thẩm định giá, giấy phép… Không đổi thành khẩu ngữ hay từ tự chế ("nhà băng", "biên lai" đều sai).
- **Phép thử người thật:** đọc lại câu, "một luật sư hoặc người dân có viết như vậy không? Không thì viết lại."
- **Cách ly:** agent chỉ đọc file trong thư mục gói, không mở thư mục khác.

### 7.10 Kết quả: model nào viết bao nhiêu

**Vòng 1** (tháng 9–10): 2.246 câu.

| Model | Số câu |
|---|---:|
| claude-opus-5-5 | 1.339 |
| deepseek-flash (DeepSeek) | 894 (+12 không ghi model) |
| openai/gpt-oss-120b (Groq) | 1 |

387 câu bị loại: `insufficient_context` 333, `copies_the_answer` 40, `not_one_line` 12, và 2 câu lý do khác.

Nhóm T1 của bộ cuối do **claude-haiku-5-5** viết cả câu hỏi lẫn đáp án ngắn.

**Nguồn câu hỏi trong bản phát hành, theo dòng:**

| Model | Dòng |
|---|---:|
| Codex gpt-6.1-sol | 288 (model do tác giả kể lại, log không ghi) |
| claude-opus-5-5 | 240 |
| claude-haiku-5-5 | 86 |
| deepseek-flash | 72 |
| claude-sonnet-5-5 | 36 |

---

## 8. Bước D: Chọn đáp án ngắn bằng LLM

**Vì sao cần.** Đáp án đầy đủ là cả lời văn của phiên bản, thường dài cả đoạn. Chấm "model trả lời có đúng không" trên cả
đoạn quá dễ lệch. Nên bộ dữ liệu có thêm **đáp án ngắn**: phần cốt lõi mà câu hỏi thật sự hỏi.

**Quy tắc cứng.** Đáp án ngắn **phải là một đoạn nguyên văn** của lời văn (hoặc câu dẫn). LLM chỉ được *cắt*, không được
*viết lại*. Nhiều đoạn thì nối bằng " … ".

| Giai đoạn | Ai chọn |
|---|---|
| Vòng 1 | claude-opus-5-5 |
| Bộ test 2 | LLM trong lượt viết gói |
| Bộ cuối | claude-haiku-5-5 hoặc Codex (ghi theo từng dòng) |

**Cổng kiểm sau LLM (code).**
- Đáp án ngắn không còn là đoạn của lời văn (hoặc câu dẫn) sau khi dựng lại thì bị loại.
- Dòng có đáp án thì **bắt buộc** có đáp án ngắn hợp lệ; dòng "không còn hiệu lực" thì **không được** có.

**Lưu ý trung thực.** Lời dặn riêng cho bước chọn đáp án ngắn **không được lưu thành một văn bản chuẩn**; nó nằm trong các
lượt chạy. Đây là điểm yếu về tái lập.

**Hai lần sửa sau khi có kết quả:**
- 19/11: 82/86 đáp án T1 còn dính ký hiệu liệt kê ở đầu đoạn ("a)", "2."). Lỗi lộ ra sau khi chạy các hệ. Sửa bằng **code** (gỡ đúng một ký hiệu ở đầu mỗi đoạn), không dùng LLM.
- 21/11: hoàn thiện 8 đáp án bị cắt "…" giữa câu.

---

## 9. Dựng dòng và chọn ngày hỏi (không dùng LLM)

Mỗi lineage được trải thành nhiều dòng, mỗi dòng một ngày hỏi.

| Chiến lược ngày | Cách chọn | Mục đích |
|---|---|---|
| `boundary` (ranh giới) | Sát mỗi lần chuyển phiên bản, ví dụ 31/12/2021 và 01/01/2022 | Thử đúng điểm chuyển |
| `mid_interval` (giữa khoảng) | Cùng câu hỏi, cùng phiên bản gold, ở ngày cách hai đầu khoảng hiệu lực ít nhất 30 ngày; chọn bằng seed. Gold được tính lại từ chuỗi phiên bản và phải trùng dòng ranh giới | **Bảng kết quả chính** |

Vì sao giữa khoảng là bảng chính: ngày ranh giới gần như để lộ văn bản đáp án, vì chỉ có trung vị 7 văn bản bắt đầu có
hiệu lực vào hôm trước.

Mỗi dòng còn mang trường bằng chứng: phiên bản gold, các phiên bản liên quan, **những đơn vị trong corpus được tính là
bằng chứng đúng** (điều khoản gốc hoặc câu lệnh sửa đổi đã viết ra lời văn gold), tập bằng chứng (gold + câu dẫn + điều
được dẫn chiếu), và vùng chữ thay đổi.

**Tách dev/test:** theo **văn bản đích** (khoảng 20% dev, 80% test), bằng hàm băm có seed. Một lineage hay một văn bản không
bao giờ nằm ở cả hai tập.

---

## 10. Bước E–G: Gán nhãn bằng agent AI

### 10.1 Vì sao chuyển sang AI gán

Đây là chỗ hội đồng dễ hỏi nhất, nên kể thẳng:

| Giai đoạn | Cách làm | Kết quả |
|---|---|---|
| Tháng 10 | Hai sinh viên gán mù 300 dòng kiểm chéo | AC1 giữa hai người 0,377 trên 246 dòng, **không đạt** ngưỡng 0,80. Nhãn của một người trung bình khoảng 5 giây/dòng và có 288 ghi chú nháp do Claude viết, nên không dùng được |
| 29/10 – 04/11 | Nhãn agent/LLM có cổng hiệu chuẩn so với người | Lời dặn phiên bản 2: AC1 0,530 so với người, **không đạt**, dừng |
| Từ 06/11 (bộ cuối) | **Hai agent AI gán độc lập** theo hướng dẫn 4.0, hòa giải, CMT duyệt từng phiếu | Bộ cuối 199 lineage |

Hai lần gán bằng người không đạt, nhóm lại thiếu giờ người, nên bộ cuối chuyển sang mô hình *"AI gán, tác giả duyệt, người
đọc mù để kiểm"*. Nhãn của bộ cuối luôn là **nhãn AI**: mỗi nhãn mang `label_origin = ai` và `verification_status =
not_verified` cho đến khi CMT xác nhận. Không có chỗ nào ghi nhãn AI thành nhãn người.

### 10.2 Bốn câu hỏi Q1–Q4 (hướng dẫn gán nhãn 4.0)

Agent chấm **một câu hỏi** (cả lineage, mọi ngày) bằng cách trả lời bốn câu:

| Câu | Hỏi gì | Giá trị | Đạt khi |
|---|---|---|---|
| **Q1** | Đáp án ở mỗi ngày có **đúng** theo văn bản không? (đọc câu lệnh sửa đổi/bãi bỏ và điều về hiệu lực) | `dung` / `sai` | `dung` |
| **Q2** | Câu hỏi có nhắm đúng **chỗ thay đổi** không? | `co` / `khong` | `co` |
| **Q3** | Câu hỏi có **rõ** không? (một điều khoản, một đáp án; không lộ ngày, số hiệu; không chứa đáp án) | `co` / `khong` | `co` |
| **Q4** | Có **quy định khác đang thay thế** đáp án này không? (văn bản cấp cao hơn, sắp xếp bộ máy 2025, điều khoản chuyển tiếp; với T6: nội dung đã chuyển chỗ chưa) | `khong` / `co` / `khong_chac` | `khong` |

- Kết luận `dat` chỉ khi cả bốn đạt (Q1=`dung`, Q2=`co`, Q3=`co`, Q4=`khong`). Còn lại là `khong_dat`.
- Mỗi câu bất lợi phải chọn **một mã lý do** trong danh sách đóng, ví dụ `gold_wrong`, `question_leaks`, `superseded_by_other_norm`, `relocated`, `restructuring_2025`.
- Bắt buộc dán **một câu nguyên văn** từ văn bản tác động làm bằng chứng.
- Phân vân vẫn phải chọn một nhãn, ghi `[phân vân]` vào ghi chú; riêng Q4 có sẵn mức `khong_chac`.
- Với T6, trả lời "không có quy định thay thế" bắt buộc kèm **nhật ký tìm kiếm** (đã tìm chỗ chuyển ở đâu).
- Không được bịa trích dẫn để cho đủ phiếu. Trạng thái chứng cứ (`sufficient`/`insufficient`/`unavailable`) được tách khỏi nhãn: có nhãn không chứng minh đã đủ nguồn.

Một số quy tắc nền mà mọi agent đều được dặn:
1. `as_of` là ngày tính **hiệu lực pháp lý**, kể cả hiệu lực trở về trước. Coi sự việc phát sinh tại `as_of`; điều chuyển tiếp chỉ giữ bản cũ cho việc đang làm, không tự đổi đáp án.
2. Câu hỏi hỏi **nội dung**, không hỏi vị trí. Đổi mức phạt vẫn có thể là cùng một quy phạm.
3. Câu dẫn là một phần của đáp án mục con; đọc cùng câu dẫn của nút cha tại `as_of`.
4. Với T6, **trước ngày bãi bỏ** đáp án đúng lúc đó vẫn đạt dù về sau nội dung chuyển chỗ; chuyển chỗ xét ở mốc sau.
5. Luật và văn bản dưới luật khác nhau về cùng vấn đề: theo Luật.

### 10.3 Hai agent gán: AI-A và AI-B

Hai agent được định nghĩa gần như giống hệt nhau, chỉ khác tên và câu "không đọc nhãn của bên kia".

| | AI-A | AI-B |
|---|---|---|
| Nền | Claude Code | **Codex CLI** (khác họ model) |
| Model | claude-opus-5-5 (một lượt T1 dùng claude-sonnet-5-5) | gpt-6.1-sol, gpt-6-luna; có lượt không ghi model |
| Quyền | Chỉ đọc (đọc file, tìm web, mở trang web, tra cơ sở dữ liệu luật Lawgical) | Như AI-A, nhưng công cụ web thay bằng truy vấn trực tiếp API cổng biên tập |
| Cấm | Chạy lệnh shell, ghi/sửa file, gọi agent khác | Tương tự |

**System prompt của agent (ý chính):**

> Bạn là AI-A (định danh nhãn `ai-a`). Chỉ đọc hướng dẫn, phiếu và nguồn thuộc lô được giao. **Không đọc nhãn hay gợi ý của
> AI-B, luật sư, người gán, hay dự đoán/kết quả của hệ.** Nếu đầu vào đã lộ nhãn khác, báo `blinding_compromised`, không
> tự nhận đây là lượt mù. Tự đối chiếu từng câu Q1–Q4, từng mốc với lời văn nguồn. **Mục tiêu là quyết định đúng căn cứ và
> bộc lộ điểm chưa chắc, không phải đoán ý bên kia hay nâng tỷ lệ đồng thuận.**

Agent được nạp sẵn hai bộ kỹ năng:
- **Tra nguồn pháp luật Việt Nam:** xác minh đúng văn bản và hiệu lực ở từng `as_of` qua cơ sở dữ liệu luật và cổng văn bản gốc; **không phán từ trí nhớ**.
- **Gán và đối soát nhãn:** lược đồ nhãn, cách giữ nhãn thô độc lập, cách đo đồng thuận, cách không giả nhãn người.

**Vì sao AI-B chạy bằng Codex.** Để hai nhãn đến từ **hai họ model khác nhau**, tránh hai bên cùng sai một kiểu. Lời bọc cho
Codex đại ý: đọc vai trò của AI-B và hai bộ kỹ năng như Claude; thay công cụ mở web bằng truy vấn trực tiếp API cổng văn
bản; mỗi truy vấn hay lần tìm web **tính vào ngân sách tra cứu**; chỉ đọc, không tạo/sửa/xóa file nào; không đọc file nhãn
của bên kia hay lịch sử git; tin nhắn cuối chỉ gồm hai khối, nhãn (JSONL) và provenance.

**Lời giao việc mỗi lượt** (khuôn chung):
- Danh sách file được đọc kèm dấu vân tay: định nghĩa bộ dữ liệu, hướng dẫn gán 4.0, và một gói đầu vào. **Không mở file nào khác.**
- Mỗi dòng gói gồm: phiếu; **các đoạn văn bản chính thức đã được lấy sẵn** từ cơ sở dữ liệu quốc gia (điều được hỏi ở bản ban hành, điều hiệu lực, điều chuyển tiếp, toàn văn văn bản tác động); danh sách đoạn không lấy được; và một mã ràng buộc nhãn với đúng phiếu.
- **Ngân sách tra ngoài:** tối đa N lượt tìm web cho cả phiên, chỉ dùng cho Q4 (quy phạm khác đè, chuyển chỗ, sắp xếp bộ máy) hoặc khi đoạn chính thức thiếu. "Gộp nhiều lệnh tra vào một lượt khi được."
- **Ngày hiệu lực lấy từ lời văn của điều quy định hiệu lực**, không lấy từ trường ngày trong phiếu.

**Mỗi nhãn là một bản ghi** gồm: mã lineage; định danh agent; `label_origin: ai`; `verification_status: not_verified`;
phiên bản hướng dẫn; mã ràng buộc phiếu; Q1–Q4 kèm lý do; kết luận; **một trích dẫn nguyên văn**; nhật ký tìm kiếm; ghi
chú; trạng thái chứng cứ; danh sách chứng cứ (địa chỉ đã mở, hạng nguồn `official | worksheet | secondary | snippet`, số
hiệu, điều khoản, ngày, đoạn chứng minh, giờ truy cập). Kèm một khối **provenance** riêng: model thật, phiên, dấu vân tay
đầu vào, công cụ đã dùng, lỗi truy cập, quota, mức mù. Không biết thì ghi `unknown`, không đoán.

**Các lượt đã chạy:**

| Lượt | Lineage | AI-A | AI-B |
|---|---:|---|---|
| silver (vòng 1) | 47 | Claude Code, claude-opus-5-5 | Codex CLI, gpt-6.1-sol |
| lô 2 | 70 | Claude Code, claude-opus-5-5 | Codex, model không ghi |
| lô bổ sung | 11 | Claude Code, claude-opus-5-5 | Codex CLI, gpt-6-luna |
| T1 control | 43 | Claude Code, claude-sonnet-5-5 | Codex CLI, gpt-6-luna |
| gán lại 19/11 | 19 | Claude Code, claude-opus-5-5 (mới) | Codex native subagent (giữ từ trước) |
| gán lại 19/11 | 9 | Claude Code, claude-opus-5-5 (giữ) | Codex CLI, gpt-6-luna (mới) |

Ngày 19/11, 28 lineage trước đó do hai agent **cùng họ** gán (Claude–Claude hoặc Codex–Codex) được gán lại ở phía còn
thiếu, để lineage nào cũng có một nhãn Claude và một nhãn Codex. Nhãn cũ giữ lại với trạng thái "bị thay thế". Tổng cộng:
398 nhãn đang dùng + 56 nhãn bị thay.

### 10.4 Đo đồng thuận (code, không phải cảm giác)

Sau khi **khóa** cả hai file nhãn thô, điều phối viên tính đồng thuận bằng code (AC1 của Gwet, κ của Cohen, đồng thuận đặc
hiệu), không ước lượng bằng mắt.
- Tính riêng cho Q1, Q2, Q3, Q4 và kết luận: AC1, tỷ lệ đồng thuận ở nhãn bất lợi (p_neg), κ, ma trận nhầm lẫn, số mẫu; thêm theo nhóm.
- Ngưỡng: AC1 ≥ 0,80 và p_neg ≥ 0,60; κ báo kèm. Không có mẫu âm hoặc chỉ số không xác định thì ghi `not_evaluable`, **không ghi đạt**.
- Đo **trước hòa giải**. Không lọc các ca lệch để đạt ngưỡng. Lô hiệu chuẩn đầu (30 dòng) không tính vào số đo chính.
- Phải ghi rõ đây là đồng thuận **AI–AI**, ghi model từng bên. Hai model có sai số tương quan; khác họ model giảm nhưng không loại. Nó không thay đồng thuận người–người và không chứng minh đúng pháp lý.

### 10.5 Hòa giải ca bất đồng bằng agent

Hai AI đồng ý ở 184 lineage. Có **15 ca bất đồng**: agent hòa giải đề xuất cho 11 ca, CMT tự quyết 4 ca.

**System prompt của agent hòa giải (ý chính):**

> Bạn là người hòa giải AI cho nghiên cứu, **không phải luật sư hay tòa án**. Chỉ nhận phiếu, hai nhãn thô đã khóa kèm dấu
> vân tay, danh sách trường bất đồng, và nguồn. **Không nhận kết quả của hệ** để quyết một câu có được giữ trong benchmark
> hay không. Với mỗi bất đồng, **mở lại nguồn cả hai bên dẫn** và tự kiểm mốc hiệu lực, phạm vi Điều/Khoản/Điểm, chuyển
> tiếp, quy phạm thay thế. Nêu luận điểm nào của mỗi bên được chứng minh hoặc bị bác bỏ. **Không mặc định A, B, đa số, hay
> bản trả lời dài hơn là đúng.** Có thể kết luận cả hai sai hoặc chưa đủ căn cứ. Không biến "không truy cập được nguồn"
> thành một phán quyết pháp lý.

**Đầu ra mỗi lineage:** dấu vân tay hai nhãn gốc; các trường bất đồng; nhãn đề xuất; `disposition` ∈ {`prefer_a`, `prefer_b`,
`both_wrong`, `unresolved`}; lập luận; chứng cứ; câu hỏi còn mở; `human_adjudication_required: true`. Agent **không ghi đè
hai nhãn gốc** và không ghi mình vào cột của luật sư. Thấy quy tắc thiếu hoặc mâu thuẫn thì báo người phụ trách, **không tự
tạo quy tắc mới**, và không được tuyên bố đã đạt đồng thuận nhờ hòa giải.

### 10.6 CMT duyệt và AI kiểm lại

1. **CMT duyệt** từng phiếu (kèm nhãn AI). Bước này xác nhận ngày 10/11 (silver và lô 2) và 11/11 (T1). Thời gian từng dòng không đo và CMT đã thấy nhãn AI, nên đây **không phải kiểm mù**.
2. **H7 — kiểm lại ca CMT nghi:** agent phân xử xem lại các dòng CMT đánh dấu không chắc.
3. **R2 — kiểm lại chuyển chỗ:** với **mọi ca bãi bỏ**, agent kiểm xem nội dung đã chuyển sang văn bản khác chưa. 23/23 kết luận giữ.

### 10.7 Phễu của bộ cuối

| Nguồn | Đưa vào gán | Giữ |
|---|---:|---:|
| silver (câu hỏi vòng 1) | 168 | 75 |
| lô 2 (ứng viên mới) | 128 | 70 |
| lô bổ sung | 18 | 11 |
| T1 control | 60 | 43 |
| **Tổng** | **374** | **199** |

Nhóm repealed bị thu hẹp mạnh: hơn một trăm lineage bị loại vì không chắc nội dung đã chuyển chỗ hay chưa.

---

## 11. Bước cuối: Người đọc mù, rà sót, và sửa kho

Đây là lớp kiểm **độc lập với AI**.

### 11.1 Đọc mù của người

- Người đọc chỉ thấy câu hỏi, ngày, văn bản và đường dẫn. Họ **không thấy đáp án của kho và không thấy nhãn AI**.
- Họ tự tra và ghi: còn hay hết hiệu lực, nội dung, văn bản áp dụng.
- Công cụ nhập phiếu từ chối file nếu cột khóa bị sửa; khi mở khóa, nó khóa câu trả lời của người bằng dấu vân tay rồi mới đặt đáp án của kho bên cạnh. Nhờ vậy không ai sửa đáp án sau khi đã thấy đáp án kho.

| Đợt | Người đọc | Lineage | Khớp kho | Lỗi kho tìm ra |
|---|---|---:|---:|---|
| 1 | Hai người gán | 30 | 30/30 | 0 |
| 2 | Đồng tác giả | 81 | 78/81 | 2 (sót sửa đổi), 1 lần người đọc sai |
| 2 | Luật sư (chỉ xét hiệu lực) | 30 | 29/30 | 1 (một thông tư bị bãi bỏ từ 01/07/2026) |
| Ngẫu nhiên 30 dòng (21/11) | 2 người | 30 | **chưa nhận phiếu** | — |

105 lineage đã đọc **không phải mẫu ngẫu nhiên**: phủ cả 23 lineage repealed, 5/6 multi_versions, 77/127 two_versions, 0/43
control. Đợt ngẫu nhiên lấy từ 94 lineage chưa ai đọc, để ước lượng tỷ lệ lỗi cho cả bộ.

### 11.2 Rà sót sửa đổi (21/11)

Một chương trình đối chiếu **mọi điều khoản đã phát hành** với danh sách văn bản mà vbpl ghi là sửa đổi, bãi bỏ hay thay
thế văn bản chứa nó; từng ứng viên được đọc trong văn bản chính thức. Tìm thêm 3 lỗi kho; cùng 2 lỗi do đọc mù, tổng cộng
**5 điều khoản được sửa** ở bản 5.0.0. 7 dòng được dời ngày vào giữa khoảng hiệu lực thật nên đáp án không đổi.

### 11.3 Gán tăng cường nhóm rủi ro cao (21/11)

Mỗi lineage repealed (23) và multi_versions (6) lấy một dòng. Hai agent AI gán mù dòng đó, rồi CMT kiểm bằng văn bản gốc.
Cả 29 dòng xác nhận hiệu lực theo kho; một đáp án ngắn bị cắt được hoàn thiện. **Bước này không có luật sư.**

### 11.4 Chạy các hệ lần đầu

Sau khi chốt bộ test cuối, nhóm chạy các hệ (gọi là G4) **một lần** ngày 12–13/11. Kết quả được chấm trên bộ nội bộ
**trước** các đợt sửa ngày 19 và 21/11, nên cần chấm lại trên bản 5.1.1 trước khi trích.

---

## 12. Phát hành cho Data in Brief

Bản phát hành dựng lại từ bộ test cuối bằng chương trình, **không sửa tay dòng nào**. Thay đổi so với bộ nội bộ:
- Sửa đáp án T1; sửa một dòng theo đọc mù của luật sư.
- Viết lại trường nguồn gốc kiểm của từng lineage cho đúng thực tế.
- Đổi tên nhóm sang tên mô tả (bỏ mã T1…T6 ở bản công khai).
- Bỏ trường lĩnh vực (69% rơi vào "khác").
- Sửa 5 lỗi kho.
- Công bố toàn bộ tài liệu gán nhãn: hướng dẫn, phiếu, nhãn AI thô, biên bản hòa giải, kiểm lại, đọc mù, system prompt nguyên văn của các agent.

**Các phần của bản phát hành:**
- Dữ liệu chính (13 cột: id, tập, nhóm, chiến lược ngày, câu hỏi, ngày, ngữ cảnh, đáp án, có đáp án không, trích dẫn, mã lineage, mã phiên bản, bằng chứng chấp nhận) và một file thông tin bổ sung nối theo id (văn bản đích, khoảng hiệu lực, chuỗi chuyển, nguồn câu hỏi, nguồn đáp án ngắn, nguồn gốc kiểm).
- Corpus truy xuất (§3.5).
- Bộ chấm: accuracy (đáp án phải chứa mọi đoạn gold và không chứa đoạn chỉ có ở phiên bản khác), tỷ lệ trả sai phiên bản, từ chối, F1, nhất quán theo cặp, recall@k, MRR, bootstrap theo lineage.
- Datasheet theo mẫu của Gebru và cộng sự (2021).
- Giấy phép: dữ liệu CC BY 4.0, code MIT.

## 13. Các mốc theo thời gian

| Ngày | Mốc |
|---|---|
| 24/08 – 04/09/2026 | Cào lần đầu: 13.863 → 20.491 văn bản sau mở rộng ngược |
| 12/09 | Ảnh chụp kho: 23.139 văn bản |
| 17/09 | Corpus: 17.333 văn bản đủ điều kiện |
| Tháng 9–10 | Bản nội bộ 1.x–2.0: 769 dòng chính (dev 328, test 441) và 859 dòng silver; nhãn người không đạt |
| 29/10, 04/11 | Hai vòng thử (test v1.0, test 2 với nhãn LLM) |
| 11–13/11 | Bộ test cuối (199 lineage, 722 dòng) và chạy các hệ lần đầu |
| 19/11 | Phát hành 3.0.0 → 4.0.0: sửa T1, một dòng, tên nhóm mô tả |
| 21/11 | 5.0.0 → 5.1.1: sửa 5 lỗi kho, bộ chấm công khai, datasheet |

## 14. Hạn chế cần biết khi đọc kết quả

1. Gold là "lời văn theo kho tại ngày chụp", **không phải sự thật pháp lý đã có người kiểm toàn bộ**. Kho có thể sót sửa đổi. Cả 6 lỗi đã biết đều do đọc mù hoặc rà sót tìm ra, **không** do bước gán AI.
2. 94/199 lineage, gồm toàn bộ control, chưa có người đọc mù. Đợt 30 dòng ngẫu nhiên đang chờ phiếu.
3. Nhãn là nhãn AI. Tác giả duyệt nhưng đã thấy nhãn AI, và không đo thời gian từng dòng. Đồng thuận giữa hai agent là AI–AI, không thay cho đồng thuận người.
4. Câu hỏi do LLM viết, cùng họ model với một số hệ được đo; câu hỏi còn bám chữ của điều khoản.
5. Hệ đề xuất dùng chính kho phiên bản tạo ra gold, nên một phần lợi thế là do cách dựng bộ dữ liệu.
6. Kết quả các hệ chấm trên bộ trước các đợt sửa; cần chấm lại trên 5.1.1.
7. Nhóm multi_versions chỉ có 6 lineage, repealed 23 lineage; kết quả theo hai nhóm này chỉ để mô tả.
8. **Tái lập các bước LLM chỉ ở mức "đọc lại kết quả đã lưu", không phải "chạy lại ra y hệt"**: câu hỏi, đáp án ngắn, nhãn AI và quyết định của người đều được lưu chứ không sinh lại. Lời dặn chọn đáp án ngắn không được lưu thành văn bản chuẩn; model của một số lượt (Codex ở phần câu hỏi, Codex ở lô 2) do tác giả kể lại, log không ghi.

---

## Phụ lục A. Đối chiếu với repo (dành cho nhóm)

Đường dẫn tính từ gốc repo khóa luận; `vilextime_uit/` là repo phát hành.

| Mục | Vị trí |
|---|---|
| Cào | `src/vilexgraph/`, `scripts/pipeline/{collect_seeds,build_graph,expand_reverse,fetch_histories,fetch_provision_trees,attach_provision_text,delta_crawl}.py`; kế hoạch và bẫy: `docs/crawling-plan.md` |
| Kho phiên bản | `scripts/pipeline/{build_store,resolve_expiry_targets,extract_provision_events,apply_document_scope,build_versions}.py` → `data/derived/` |
| Hàng chờ LLM xem trước | `data/review/provision_events.jsonl`, `validity_queue.tsv`, `temporal_candidates.jsonl` |
| Corpus | `scripts/pipeline/build_corpus.py`, `build_eligibility.py` → `vilextime_uit/corpus/` |
| Ứng viên | `build_question_pool.py`, `sample_vilextime.py` → `data/derived/vilextime_pool.jsonl`, `data/vilextime/sample.jsonl` |
| Viết câu hỏi | `scripts/pipeline/generate_questions.py`, `src/vilexgraph/llm.py`; system prompt: `prompts/vilextime/base.md` + `T1.md`…`T6.md`; bộ test 2: `test2_cau_hoi.md`; kết quả: `data/vilextime/questions.jsonl` |
| Lọc ứng viên | `prompts/vilextime/test2_loc.md`; thư mục làm việc ngoài repo `~/vilextime_loc/`; phiếu: `data/review/the4/`, `data/vilextime_final/inputs/` |
| Đáp án ngắn | `data/vilextime/short_answers*.jsonl`; kiểm: `enrich_vilextime.py`; sửa: `scripts/eval/fix_t1_short_answers.py`, `scripts/review/test2_fill_shorts.py` |
| Dựng dòng | `build_vilextime.py`, `enrich_vilextime.py` |
| Agent gán, hòa giải | `.claude/agents/{legal-annotator-a,legal-annotator-b,legal-adjudicator}.md`; kỹ năng: `.claude/skills/{vn-legal-research,vilextime-ai-labeling}/`; bản nguyên văn đã phát hành: `vilextime_uit/annotation/prompts/` |
| Lời giao việc và Codex | `data/review/ai_research/{prompt_v2.md,codex_b_wrapper.md}`; từng lượt: `data/review/ai_research/<ngày>_<lượt>/` |
| Hướng dẫn gán | `docs/vilextime-annotation.md` (tiếng Việt), `vilextime_uit/annotation/guidelines/annotation_guideline_v4.0.md`; định nghĩa: `docs/vilextime-dinh-nghia.md` |
| Đo đồng thuận, mã lý do | `scripts/review/crosscheck.py`, `scripts/review/test2_labels.py` |
| Phễu bộ cuối | `data/review/ai_research/2026-11-11_final_count/count_final.py` |
| Đọc mù | `scripts/review/independent_gold.py`; phiếu `data/review/gold_final/`, `data/review/gold_random30/`; bản phát hành `vilextime_uit/annotation/blind_reading/` |
| Rà sót sửa đổi | `scripts/check/audit_missed_amendments.py`, `runs/audit_missed_amendments/` |
| Bộ cuối và phát hành | `scripts/pipeline/build_final_release.py` → `data/vilextime_final/`; `build_dib_release.py` → `vilextime_uit/` |
| Kiểm và tái lập | `scripts/check/verify_pipeline.py`; `vilextime_uit/scripts/{check_dataset,evaluate}.py` |
| Nhãn thô và hòa giải đã phát hành | `vilextime_uit/annotation/labels/{ai_labels_raw,adjudication,post_review_ai_checks}.jsonl` |
