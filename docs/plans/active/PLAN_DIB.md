# Plan: bài dữ liệu ViLexTime cho Data in Brief

Mở 19/11/2026. CMT chốt: nộp Data in Brief (không chờ ICAIL); công bố bộ chính + nhãn thô AI + prompt + gold mù + hướng dẫn gán nhãn; giấy phép CC BY 4.0.

## Quyết định đã chốt (CMT, 19/11)
- Không đưa TV-RAG, G4, F1–F7 vào bài. Bài chỉ mô tả dữ liệu.
- Tác giả (CMT) duyệt từng lineage; ghi rõ duyệt sau khi thấy nhãn AI (không mù).
- Model Codex: `gpt-6.1-sol`, ghi là tác giả khai (log Codex không ghi model).
- Bỏ cột `domain` (500/722 dòng là `khac`); thay bằng `issuer_code` lấy từ số ký hiệu.
- F019 sửa gold theo ADR 0006 §7.
- Chỉ báo các số đồng thuận đo trên dữ liệu phát hành; số của v1.0/hướng dẫn cũ chỉ nhắc một câu.

## Việc
- [x] Dựng bản phát hành DiB: `scripts/pipeline/build_dib_release.py` → `data/vilextime_dib/`
  (722 dòng, 199 lineage, 675 có đáp án; ai_agree 183, ai_adjudicated 12, tác giả quyết 4; 105 lineage có gold mù).
- [ ] Dịch hướng dẫn gán nhãn 4.0 sang tiếng Anh, thêm phần "tra cứu từng bước" cho người không học luật (GVHD yêu cầu).
- [ ] README tiếng Anh + datasheet cho repo dữ liệu; gom nhãn thô AI-A/AI-B, prompt, nguồn đã tra vào `annotation/`.
- [ ] Bảng thống kê tự động từ `data/vilextime_dib/`.
- [ ] Viết bài theo template DiB (khung trong hội thoại 19/11): Methods + kiểm chất lượng trước.
- [ ] Evidence-gate mọi con số trước khi nộp.
- [ ] Đăng Mendeley Data (để chế độ chưa publish trong lúc review).

## Số đồng thuận dùng trong bài (nguồn)
- Gold mù đợt 2: luật sư–NMT 29/30, κ 0,932 (`data/review/gold_final/DONG_THUAN_B_20261116.md`); NMT–kho 80/81.
- Gold mù đợt 1 (người A/B, 24 lineage bộ cuối): khớp thô 148/150; 119/120 sau phân xử AI đề xuất (ADR 0006 §7).
- AI–AI trước hòa giải, 314 lineage: Q1–Q4 AC1 0,87–0,95; verdict 0,608 (`docs/reports/g2-co-mau-dong-thuan-20261109.md`).
