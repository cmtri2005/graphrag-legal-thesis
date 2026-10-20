# Execution Plan: Dựng lại ViLexTime theo định nghĩa chốt

Date: 2026-10-20

## Status

Active. Chờ luật sư ký phiếu `data/review/gui_luat_su_dinh_nghia.xlsx` (bước 1); các bước máy
(2–5) làm song song được.

## Outcome

Bản phát hành ViLexTime mà **mọi dòng của tập test** đạt 8 điều kiện ở mục 6 của
`docs/vilextime-dinh-nghia.md`, đã được người kiểm có dẫn chứng; dòng bị loại mang một mã ở mục 7;
cơ cấu đạt sàn ở mục 9; `check_release.py` OK; datasheet không còn mục "chưa xong".

## Context

- Định nghĩa: `docs/vilextime-dinh-nghia.md` (chốt 20/10/2026, CMT).
- Lý do làm lại: D4 sau hòa giải hỏng 22–64% theo lát; nhãn model chỉ gắn `khong_dat` 2–19%, khớp
  người 7/13 dòng (memory, đo 19/10); 7 loại lỗi đồ thị ở `docs/reports/D5_bien_ban.md` §5.
- Mốc: chạy xong đồ án trước 31/10/2026 (A1). Bản dựng lại này phục vụ khóa luận nếu kịp, và chắc
  chắn phục vụ bài báo. Nhóm chọn mốc cho bước 6–8.

## Scope

In scope:

- Hướng dẫn gán nhãn 3.0, bộ lọc máy, sửa lỗi đồ thị, dựng lại, phiếu kiểm, kiểm định người,
  gold độc lập, đóng băng.

Out of scope:

- Thao tác "bổ sung" điều khoản mới; lát "T6 chuyển chỗ" có chấm điểm; chế độ `sau_het_hieu_luc`.

## Approach

1. **Luật sư ký** 7 quy tắc pháp lý (CMT gửi). Không đồng ý điểm nào thì sửa đúng điểm đó trong
   định nghĩa trước bước 6.
2. **Hướng dẫn gán nhãn 3.0** viết lại theo định nghĩa: 8 ô kiểm bắt buộc, mã loại đóng, ví dụ mục
   10; phiếu có cấu trúc (ô "đã kiểm văn bản tác động nào", "nội dung còn ở đâu", "chạm lần sửa nào").
3. **Bộ lọc máy:** R1-i (đã có `cosmetic_change`), R1-ii (danh sách đổi tên cơ quan, đơn vị do sắp
   xếp 2025), R1-iii (điều khoản tự cập nhật dẫn chiếu), R4 (mở rộng bộ dò `cap_huyen` sang bộ, tỉnh),
   R5 (đáp án chỉ là dẫn chiếu), R6 (`pending_events.py`), R7 (đã có); T3 chỉ giữ ứng viên có ≥ 2
   lần chuyển thực chất sau R1; tách T5a/T5b, T6a/T6b; bỏ `sau_het_hieu_luc` khỏi phần chấm.
4. **Sửa lỗi đồ thị** còn lại ở D5 §5 (mục 1 đã sửa ở `5877a5a`): thay toàn bộ điều, khoản bị bỏ sót;
   đích bãi bỏ sai; `valid_to` sai; quy phạm cấp cao thay nội dung (chỉ dò để loại theo R3).
5. **Dựng lại một lần**, giữ nhãn người cũ khi câu hỏi và đáp án không đổi; xuất phiếu kiểm kèm
   đoạn trích văn bản gốc (`crosscheck_evidence.py --ids`).
6. **Người kiểm 100% tập test**; 25% gán đôi; người thứ ba hòa giải; ~100 câu người viết lại.
7. **Gold độc lập** 120 + 30 (đang làm, B6).
8. **Đóng băng:** manifest, tag, datasheet, phụ lục chỗ chuyển đến, silver.

## Risks And Recovery

- T3, T6 thiếu dòng sau khi lọc chặt → lấy từ kho ứng viên (T3 386, T6 2.812), không đạt sàn thì giảm
  quota (đã chốt), không nới điều kiện.
- Giờ người ở bước 6 lớn (ước 100–120 giờ người cho cả bước 5–7) → làm theo lô 30–50 dòng, đo phút
  mỗi dòng sau lô đầu để lập lại kế hoạch.
- Dựng lại làm mất nhãn → `crosscheck.py build` đã lưu bản cũ `*.YYYYMMDD.tsv` và chỉ chuyển nhãn khi
  câu hỏi, đáp án không đổi; giữ nguyên quy tắc đó.

## Progress

- [x] Định nghĩa chốt, ADR 0003 Follow-Up, phiếu luật sư — 20/10
- [ ] Bước 1: luật sư ký
- [ ] Bước 2: hướng dẫn 3.0
- [ ] Bước 3: bộ lọc máy
- [ ] Bước 4: sửa lỗi đồ thị
- [ ] Bước 5: dựng lại, xuất phiếu
- [ ] Bước 6: kiểm định người
- [ ] Bước 7: gold độc lập
- [ ] Bước 8: đóng băng

## Decisions

- 2026-10-20: một bản định nghĩa duy nhất, không chia phiên bản v1.0/v1.1 (CMT).
- 2026-10-20: thêm R6 (dòng có sự kiện chưa áp chưa vào test); CMT chưa trả lời riêng điểm này, đưa vào
  theo tinh thần "ưu tiên chất lượng", bỏ nếu CMT không đồng ý.

## Validation

- Focused proof: test cho từng bộ lọc (một ca dương, một ca âm lấy từ ví dụ mục 10 của định nghĩa).
- Integration: `check_release.py` OK; bảng cơ cấu so với mục 9; đếm dòng theo mã loại.
- Repository-required checks: `pytest` toàn bộ.

## Result

(Điền khi xong.)
