# Phương án ViLexTime 1.500 câu (bản tóm tắt)

## Đề xuất một câu

Dùng **T1, T2, T3, T4, T6 làm năm nhóm chính**, hạ **T5 thành tập nhỏ báo cáo riêng**, và dồn phần thiếu sang T6.

## Vì sao không chia đều 300 câu mỗi nhóm

Dữ liệu thật không đủ cho hai nhóm:

- **T5 (hồi tố):** chỉ có 194 lineage, đến từ 8 văn bản; sạch chỉ 148, từ 4 văn bản. Độn cho đủ 300 sẽ chỉ ra các bản gần trùng nhau.
- **T3 (sửa nhiều lần):** có 386 chuỗi, nhưng chỉ 130–249 chuỗi có ít nhất hai lần sửa thực chất. Khoảng 1/5 lần "sửa" chỉ là đổi tên cơ quan.
- **T6 (mất hiệu lực vì đơn vị cấp trên bị bãi bỏ):** dữ liệu dồi dào (10.055 ứng viên) và đúng giả thuyết H3 của bài báo, vốn hiện chỉ có 24 dòng. Vì vậy T6 nhận phần thiếu.

## Phân bổ


| Nhóm           | Số lineage     | Ghi chú                                                                       |
| -------------- | --------------: | ----------------------------------------------------------------------------- |
| T1 (đối chứng) | 300            | Rẻ nhất, cần để biết lợi ích đến từ "hiểu thời gian" hay chỉ từ truy xuất tốt |
| T2             | 300            | Nhóm cốt lõi, không cắt                                                       |
| T3             | ~200 (sàn 130) | Chỉ tính khi có ≥3 phiên bản cho đáp án khác nhau với chính câu hỏi đó        |
| T4             | 300            |                                                                               |
| T6             | ~400           | ~200 trực tiếp + ~200 do đơn vị cấp trên bị bãi bỏ                            |
| **Tổng**       | **1.500**      | ≈ 3.000 dòng ranh giới                                                        |
| T5 (chẩn đoán) | 30–45          | Cố vấn luật ký từng câu, không tính vào trung bình                            |


## Cách làm nhãn

1. LLM soạn câu hỏi từ đoạn thay đổi; máy lọc lỗi; người duyệt từng câu. Khoảng 10% do người viết từ đầu để kiểm tra thiên vị của model.
2. Mỗi lineage một sinh viên gán; khoảng **600 dòng gán đôi mù** để đo độ đồng thuận.
3. Dòng bị gắn cờ hoặc "không chắc" được rà lại lần hai.
4. Cố vấn luật chỉ xử lý phần pháp lý (12–20 giờ).
5. Không cho người gán thấy nhãn của model ở lượt đầu, và lưu **nhãn thô trước khi hoà giải**. Sau đó không bù lại được.

## Vấn đề lớn nhất: không đủ giờ công

- Cần **250–465 giờ** sinh viên, nhưng hai người chỉ có khoảng **175–325 giờ**, tuỳ M2 (26/10) chiếm bao nhiêu.
- **Cổng go/no-go ngày 18/10:** đo số phút trung vị cho mỗi dòng ở pilot 2.
  - ≤3 phút: giữ 1.500.
  - 3–4 phút: giữ 1.500 chỉ khi đã gác bớt M2.
  - Trên 4 phút: cắt theo thứ tự T1 → T4 → T3. Không cắt T2, T6-ancestor (dưới 150) và phần gán đôi.
- Nếu phải chọn: **~1.200 câu có độ đồng thuận giữa người với người** tốt hơn 1.500 câu chỉ kiểm một lượt.

## Lưu ý về đo đồng thuận

- κ dễ bị kéo thấp khi tỷ lệ "đạt" quanh 90%, nên báo cáo thêm **AC1** và **p_neg** (đăng ký ngưỡng trước, ví dụ AC1 ≥ 0,80).
- Nếu người gán A của D4 là hội đồng LLM thì κ(A, B) là độ khớp model–người, **không được gọi là IAA** giữa người.

## Hội nghị và định vị

- NeurIPS 2026 đã đóng; ARR 12/10 rơi trước ngày đóng băng dữ liệu. Đích thực tế: **ARR tháng 1/2027, ICAIL 2027 (28/01/2027) hoặc NeurIPS 2027**.
- **Không** viết "benchmark pháp luật theo thời gian đầu tiên" (đã có ít nhất sáu bộ). **Nên viết:** benchmark point-in-time đầu tiên cho luật Việt Nam, ở cấp khoản/điểm, có bãi bỏ một phần, hiệu lực lan truyền từ đơn vị cấp trên, và có độ đồng thuận giữa người với người.

## Việc cần chốt ngay (hạn 04/10)

1. "Câu" tính theo lineage hay theo dòng? (1.500 lineage ≈ 3.000 dòng, vượt khung 1.100–1.300 của đề cương; cần hỏi khoa.)
2. Chọn phương án năm nhóm ở trên.
3. Người gán A là sinh viên hay hội đồng LLM.
4. Gác bớt M2 hay chấp nhận bản v1.0 lõi ~1.150–1.200 câu.
5. Rebuild dữ liệu trước khi gán bất kỳ nhãn mù nào.

## Lộ trình


| Mốc         | Việc chính                                                     |
| ----------- | -------------------------------------------------------------- |
| 05–11/10    | Đổi quota sang lineage, viết guideline, LLM soạn nháp, pilot 1 |
| 12–18/10    | Pilot 2, buổi cố vấn 1, **cổng go/no-go 18/10**                |
| 19/10–08/11 | Gán nhãn theo lô; M2 ngày 26/10; buổi cố vấn 2                 |
| 09–15/11    | Hoà giải, audit lỗi, **đóng băng v1.0 ngày 13–14/11**          |
| 16/11       | Nộp mốc M3                                                     |


> Bản đầy đủ (kèm số liệu, nguồn trích dẫn và so sánh benchmark) đã được lược bỏ khỏi file này.

