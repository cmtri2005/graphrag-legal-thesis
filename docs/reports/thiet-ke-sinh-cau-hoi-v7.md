# Thiết kế pipeline viết câu hỏi cho ViLexTime 7.0 (24/11/2026)

Đề xuất, chưa chạy. Căn cứ: các tài liệu liên quan (mục 1), bối cảnh ViLexTime (mục 2), kết quả chạy thử vòng 1
(`data/vilextime_v7/pilot/pilot_cham_filled.xlsx`, CMT chấm 58 câu).

## 1. Các bài liên quan làm thế nào

| Công trình | Sinh câu hỏi | Lọc tự động | Người duyệt |
|---|---|---|---|
| Prior, Schultz, Grabmair, *Asking For An Old Friend* (arXiv 2605.23497; prompt ở github.com/TUMLegalTech/temporal_bias). Luật Đức theo phiên bản, gần ViLexTime nhất | Gemini 3 Pro. **Bước 1**: với từng cặp phiên bản liền nhau, LLM phân loại thay đổi thực chất hay chỉ biên tập, và có dựng được câu hỏi mà "ít nhất một tình huống điển hình" cho kết quả khác không. **Bước 2**: chỉ cặp đạt bước 1 mới được sinh câu hỏi tình huống, đầu ra JSON gồm câu hỏi, đáp án, lập luận, căn cứ | Chỉ có bước phân loại thay đổi | 2 sinh viên luật + 1 luật sư duyệt mọi cặp: 697 sinh ra, giữ 312 (45%). Lý do loại: thay đổi chỉ biên tập; câu ghép nhiều câu hỏi con; hệ quả pháp lý giống nhau ở hai phiên bản; đáp án sai |
| KoBLEX (arXiv 2509.01324), luật Hàn | GPT-4o sinh nháp, mở rộng dần số bước suy luận | GPT-4o kiểm 2 bước: *Partial Check* (một phần điều khoản đã đủ trả lời thì loại) và *Full Check* (nhất quán, đáp án đúng, suy ra được từ điều khoản). Qua cả hai: 27% | Người học luật sửa từng mục; 3 chuyên gia chấm; còn 226 |
| YourBench (arXiv 2504.01833) | Nhiều LLM cùng sinh, gộp ứng viên | Đối chiếu trích dẫn với văn bản (fuzzy match), bỏ trùng bằng embedding | 20 người chấm 2.000 câu: khoảng 85% hợp lệ, AC1 0,71 |
| Alberti et al., ACL 2019 (*Roundtrip consistency*) | Sinh câu hỏi từ đoạn văn | Cho model trả lời lại câu hỏi; giữ câu mà đáp án khớp. Câu khớp đúng 39%, câu bị bỏ chỉ đúng 16% | — |
| TimeQA (Chen et al., 2021) | Khai thác sự kiện thay đổi theo thời gian trước, rồi mới sinh câu hỏi | Kiểm và hiệu chỉnh sự kiện trước khi sinh | — |

Điểm chung: **chọn đúng thay đổi trước, rồi mới viết câu hỏi; sau đó máy kiểm chứng câu hỏi; người duyệt sau cùng.**
Bài gần nhất (luật Đức) còn giữ được dưới một nửa số câu sinh ra, dù có luật sư duyệt.

## 2. Bối cảnh ViLexTime khác ở đâu

- **Một câu hỏi dùng chung cho mọi mốc.** Ngày hỏi nằm ở trường `as_of`, không nằm trong câu (bài Đức nhúng ngày
  vào câu). Vì vậy câu hỏi vừa phải trúng chỗ đổi, vừa phải có nghĩa ở mọi phiên bản.
- **Đáp án lấy từ kho, không do LLM viết.** Bỏ được lý do loại "đáp án sai" của bài Đức. LLM chỉ viết câu hỏi.
- **Kho không lọc thay đổi chỉ biên tập.** Trong chạy thử, vài lineage chỉ đổi chữ (L26 bỏ chữ "đơn vị", L29 đổi tên
  giấy chứng nhận). Với các lineage này, không câu hỏi nào hỏi trúng chỗ đổi được. Lỗi nằm ở ứng viên, không nằm ở
  câu hỏi. Định nghĩa đã có mã `cosmetic_only`, `rename_only`, `auto_reference_update`, nhưng chỉ người gán dùng.
- **Lỗi chính đã đo được** (vòng 1): câu hỏi khớp cả mục anh em; câu hỏi dùng nội dung chỉ một phiên bản có; câu hỏi
  hỏi vào phần không đổi.
- **Người gán cuối cùng** là 2 sinh viên luật + luật sư, đúng như bài Đức. Mọi bước LLM chỉ để tăng tỷ lệ câu dùng
  được, không thay người.
- T3 (159 lineage) và T5 (23 lineage) không có dự phòng, nên mỗi câu hỏng là mất hẳn một ca.

## 3. Pipeline đề xuất

```
Bước 0  máy:  diff giữa các phiên bản, mục anh em                                   (đã có)
Bước 1  LLM:  phân tích thay đổi  →  bỏ lineage chỉ đổi hình thức, ghi mã §R1
Bước 2  LLM:  sinh 3 câu hỏi từ phân tích, kèm đáp án dự kiến ở từng phiên bản
Bước 3  máy:  bộ lọc hình thức (validate, names_one_version)                        (đã có)
Bước 4  LLM:  kiểm chứng khứ hồi, độc lập với bước 1–2  →  chọn câu tốt nhất
Bước 5  người: 2 sinh viên luật gán Q1–Q4, luật sư hòa giải                         (theo đăng ký trước)
```

**Bước 1. Phân tích thay đổi** (theo bước 1 của bài Đức, chỉnh cho ViLexTime). Bật chế độ suy nghĩ của Qwen. Đầu
vào: các phiên bản, chỗ thay đổi, câu dẫn. Đầu ra JSON, cho từng lần chuyển:
- `thuc_chat`: có / không. "Không" thì ghi mã `cosmetic_only`, `rename_only` hay `auto_reference_update` (định
  nghĩa §R1).
- `khia_canh_doi`: khía cạnh pháp lý đã đổi (chủ thể, thời hạn, mức tiền, điều kiện, phạm vi…).
- `phan_chung`: phần giống nhau ở mọi phiên bản, dùng để khoanh vùng câu hỏi.
- `tinh_huong_khac_ket_qua`: một tình huống điển hình mà mỗi phiên bản cho kết quả khác.

Lineage không có lần chuyển thực chất nào thì dừng ở đây, ghi lý do. Người gán xác nhận lại ở giai đoạn 2; bước
này chỉ giúp không tốn công viết câu hỏi cho ứng viên hỏng. Không áp dụng cho T1. Với T6, chỉ cần khía cạnh nội dung.

**Bước 2. Sinh 3 câu hỏi.** Đầu vào: prompt hiện tại + kết quả bước 1 + 2–3 ví dụ đạt lấy từ phiếu CMT đã chấm
(lineage ngoài mẫu 7.0). Đầu ra JSON cho mỗi câu: `cau_hoi`, `dap_an_du_kien` cho từng phiên bản (trích ngắn từ lời
văn), `vi_sao_muc_anh_em_khong_tra_loi`. Bắt model ghi đáp án dự kiến cho từng bản buộc nó kiểm xem đáp án có khác
nhau không.

**Bước 4. Kiểm chứng khứ hồi** (Alberti 2019; *Partial Check* của KoBLEX). Gọi riêng từng lượt, không cho xem bước
1–2. Với mỗi câu hỏi, model trả lời:
- chỉ dựa vào lời văn **từng phiên bản**. Đạt khi các đáp án khác nhau (T3: ít nhất 3 đáp án khác nhau);
- chỉ dựa vào **từng mục anh em** (tối đa 3 mục gần nhất). Đạt khi mục anh em không trả lời được;
- **không có đoạn văn**. Đạt khi model không tự trả lời được, tức câu hỏi không lộ đáp án.

So khớp đáp án bằng một lượt LLM chấm riêng. Chọn câu đầu tiên đạt cả ba (kiểm lần lượt, dừng khi có câu đạt). Không
câu nào đạt thì lineage được ghi `qg_failed` kèm lý do, không vào phiếu gán.

**Hiệu chuẩn trước khi tin bước 4.** Chạy bước 4 trên 58 câu CMT đã chấm ở vòng 1, báo độ chính xác và độ phủ của
từng phép kiểm so với nhãn người. Bước 4 chỉ được dùng để loại nếu khớp nhãn người đủ tốt; nếu không, chỉ dùng để
xếp hạng ba ứng viên.

## 4. Chi phí và cách kiểm

- Mỗi lineage: 1 lượt phân tích, 1 lượt sinh, khoảng 5–8 lượt kiểm chứng ngắn cho mỗi câu được kiểm (trung bình
  1,5 câu). Ước khoảng 15–30 USD cho 1.782 lineage với Qwen3.8-27B trên Chutes; con số chính xác đo ở chạy thử.
- Chạy thử trên 30 lineage cũ: CMT chấm mù, so với vòng 1 (Qwen 8/28 đạt cả 3 tiêu chí, Opus 10/17).
- Ghi lại mọi lượt gọi: prompt sha, model thật, seed, đầu ra từng bước. Báo phễu: bị bỏ ở bước 1, bước 3, bước 4.

## 5. Giới hạn

- Bước 1 và 4 dùng cùng một model với bước 2, nên có thể thiên vị câu của chính nó. Kiểm chứng ở bước 4 gọi tách
  biệt và được hiệu chuẩn bằng nhãn người.
- Lineage bị bỏ ở bước 1 hay 4 làm bộ dữ liệu nghiêng về các thay đổi dễ hỏi. Phễu được báo theo nhóm.
- Nguồn tài liệu: phần lớn đọc qua bản HTML trên arXiv, một số mục chỉ có bản tóm tắt (ghi trong phiên làm việc).
  Cần đọc lại bản gốc trước khi trích trong khóa luận.
