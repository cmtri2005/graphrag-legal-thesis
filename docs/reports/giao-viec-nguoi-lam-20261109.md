# Giao việc cho người làm: chốt G2 ViLexTime (soạn 09/11/2026)

Mục tiêu: có đủ nhãn do người xác nhận và gold mù để khóa bộ dữ liệu (G2). Hạn mục tiêu của master plan: **12/11**.
Chưa đạt ngưỡng thì ghi đúng số thật, không hạ tiêu chuẩn.

Tình trạng hiện tại (Codex báo, đã chạy lại kiểm 09/11):
- Nhãn do người xác nhận sau khi đọc: **81**. Cần ≥ **130** → thiếu **49**.
- Gold mù: **0/75** dòng đã điền (cần 120 dòng riêng, thêm 30 dòng T6/T1).

## Nguyên tắc chung (đọc trước khi làm)
1. **Tự đọc điều khoản gốc, đừng chỉ tin nhãn AI.** Nhãn trong phiếu là nhãn AI, chưa kiểm.
2. Đo thời gian mỗi dòng. **Trung vị dưới 90 giây/dòng thì dừng lại, xem kỹ hơn.** Vòng trước A gán ~5 giây/dòng nên số đo bị loại.
3. Không sửa cột xám. Không ai điền thay người khác.
4. Hướng dẫn nhãn: `docs/vilextime-annotation.md` (thẻ 4.0) và định nghĩa: `docs/vilextime-dinh-nghia.md`.
5. Nguồn luật: văn bản gốc trên vbpl.vn hoặc Lawgical. Không dùng trí nhớ.

---

## Việc 1. Luật sư: chốt 5 khoảng trống quy tắc
- **Gửi:** `data/review/ai_research/2026-11-08_adjudication_final/README.md`, mục "Giới hạn" (5 mục) + `docs/vilextime-annotation.md`.
- **Làm:** với mỗi mục trả lời "tính / không tính" và cách mã hóa:
  1. Thay từ gần nghĩa mà không có định nghĩa kèm theo.
  2. Câu lặp chữ sinh ra khi áp nguyên văn phép thay cụm từ.
  3. `question_leaks` khi cụm bị lộ nằm trong mô tả người hỏi.
  4. Đáp án phụ thuộc hoàn cảnh người hỏi (ví dụ kỳ tính thuế).
  5. Mã `single_change`: có ở §7 định nghĩa nhưng thiếu ở `REASONS["q2"]` trong `scripts/review/test2_labels.py`.
- **Kết quả:** 5 câu trả lời bằng văn bản (email hoặc ghi chú ngắn), mỗi câu có ví dụ. CMT chép vào hướng dẫn.
- **Nên xong trước:** việc 1 và 2 phụ thuộc vào kết quả này (đặc biệt 3 và 4).

## Việc 2. Luật sư (hoặc người có thẩm quyền): chốt 20 lineage lo2 còn mở
- **Gửi:**
  - `data/review/ai_research/2026-11-08_lo2/duyet_CMT_after_adjudication.xlsx`, sheet **"Duyệt"** (128 dòng; chỉ làm **20 dòng** có lineage trong danh sách dưới đây).
  - Danh sách 20 lineage: `data/review/ai_research/2026-11-08_lo2/cmt_acceptance.json`, khóa `scope.unresolved_lineage_ids`.
  - Lập luận và câu hỏi còn mở: `data/review/ai_research/2026-11-08_lo2/open_cases_for_CMT.jsonl` (23 ca, theo `lineage_id`). Sheet "Hòa giải" trong xlsx có cùng nội dung.
- **Làm:** với mỗi lineage, đọc câu hỏi, điều khoản gốc và văn bản tác động. Trả lời câu hỏi còn mở (chủ yếu **Q4**, 14/23 ca: văn bản nào đã sửa/thay thế điều khoản này?). Điền cột `chot_q1`…`chot_q4_reason`, `xac_nhan`, `ghi_chu_cmt`.
- **Kết quả:** 20 dòng có đủ nhãn cuối. Lo2 thành 128/128 có nhãn cuối. File xlsx trả lại, không đổi tên và không sửa cột xám.

## Việc 3. CMT + NMT: duyệt phiếu silver 168 lineage
- **Gửi:** `data/review/ai_research/2026-11-08_adjudication_final/duyet_CMT_final.xlsx`, sheet **"Duyệt"** (168 dòng). Sheet "Đọc trước" có hướng dẫn.
- **Làm (đề xuất chia đôi 84/84; CMT chốt cách chia):**
  - Thứ tự ưu tiên: (a) dòng AI hòa giải hoặc có `[phân vân]` / cột `cau_hoi_mo` có chữ; (b) dòng **đạt** (vào bộ test, xem kỹ); (c) dòng **không đạt** mà hai AI đồng ý (xem lướt lý do).
  - Cột `cmt_dong_y`: ghi `x` nếu đồng ý toàn bộ nhãn. Nếu sửa: ghi Q cần sửa và lý do ở `cmt_sua`. Ghi chú ở `cmt_ghi_chu`.
- **Kết quả:** 168 dòng đều có quyết định. Sau đó chạy lại script kiểm để tính lại số lineage do người xác nhận. Cần thêm ≥ 49 để lên 130 (mục tiêu ~180).
- **Lưu ý:** người nào trước đó đã gán một dòng silver nào đó (A gán 131/168 ở vòng 25/10 và đã thấy đáp án đồ thị) phải khai trong khóa luận.

## Việc 4. Gold mù (cần người độc lập với đồ thị)
- **Gửi:**
  - Người A: `data/review/gold_A.xlsx` (hoặc `.tsv`), 75 dòng.
  - Người B: `data/review/gold_B.xlsx` (hoặc `.tsv`), 75 dòng.
  - Hai file có **30 câu chung** (mã khóa G001…), còn lại riêng: tổng **120 câu khác nhau**.
  - **Không gửi** `gold_sample.tsv` (0/120, đã cũ) và không gửi thư mục `the4/gold1/`.
- **Làm (A và B làm tách biệt, không trao đổi, không mở đồ thị hệ hay nhãn AI):** với mỗi dòng, đọc văn bản gốc hoặc VBHN tại `ngay_hoi` rồi điền:
  - `hieu_luc`: văn bản/điều khoản còn hiệu lực hay không tại ngày hỏi;
  - `noi_dung`: nội dung quy định đúng tại ngày đó (đáp án);
  - `van_ban_ap_dung`: văn bản và Điều/Khoản/Điểm áp dụng;
  - `phut`: số phút làm dòng này; `ghi_chu`: nếu nghi vấn.
- **Kết quả:** hai file đủ 75/75 dòng. CMT đối chiếu với đáp án đồ thị. Đạt khi **≥ 114/120 khớp** (B6); 100 dòng trong đó dùng làm M2. Dưới 95/100 thì sửa đồ thị và người kiểm lại phần bị ảnh hưởng, không loại dòng.
- **Chỗ còn thiếu (đợt 2):** master plan yêu cầu thêm ≥ 30 dòng **T6 và T1** (hiện phiếu chưa có). Tạo thêm phiếu sau khi đợt 1 xong; chưa gửi vội.
- **Không giao cho AI.** AI không tham gia gold mù.

## Việc 5. Ca VBHN cần phân xử (luật sư hoặc CMT)
- **Gửi:** `docs/reports/doi-chieu-vbhn.md`.
- **Làm:** 9 ca cần phân xử + 2 tín hiệu lệch bãi bỏ. Ghi: đúng/sai và lý do.
- **Kết quả:** mỗi ca một kết luận. Dòng lệch do người phân xử, VBHN **không** thay nhãn người.

---

## Gợi ý lịch (hôm nay 09/11, mục tiêu 12/11)
| Ngày | Ai | Việc |
|---|---|---|
| 09–10/11 | CMT | Gửi luật sư việc 1, 2, 5. Bắt đầu việc 3 (dòng ưu tiên a). |
| 09–11/11 | NMT | Việc 3 (nửa còn lại). |
| 09–11/11 | A và B (hai người độc lập) | Việc 4 đợt 1. |
| 11–12/11 | CMT | Thu file, chạy script kiểm, tính lại số lineage người kiểm so với 130. |

## Trả file thế nào
Mỗi người trả lại **đúng file đã nhận** (xlsx hoặc tsv), cùng tên, kèm tên người làm và tổng thời gian. CMT gộp vào repo và chạy:
- `.venv/bin/python scripts/check/audit_g2_statistics.py` để tính lại cỡ mẫu và đồng thuận;
- `.venv/bin/pytest -q -p no:cacheprovider` để kiểm không hỏng dữ liệu.

## Chưa chắc (cần CMT chốt)
- Cách chia 168 dòng silver giữa CMT và NMT.
- Ai là người A và B của gold mù (phải độc lập với đồ thị và với nhãn AI).
- Có tính "CMT duyệt hàng loạt" 81 silver là người kiểm hay không (nếu không tính thì số thiếu là 49).
