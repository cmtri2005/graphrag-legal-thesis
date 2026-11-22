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
- [x] Repo dữ liệu riêng `../vilextime_uit` → github.com/cmtri2005/vilextime_uit (main, commit a5b9d52, 19/11):
  data 3.0.0, README/SCHEMA tiếng Anh, `scripts/check_dataset.py`, CC BY 4.0 + MIT, CITATION.cff (thiếu tên tác giả).
  Cập nhật repo này khi dữ liệu đổi: chạy `build_dib_release.py`, chép 3 file sang `vilextime_uit/data/`.
- [x] Corpus đầy đủ nén xz (146 MB) trong `vilextime_uit/corpus/`; 360 evidence + 338 version đều có.
- [x] `annotation/`: hướng dẫn VI + EN (thêm mục tra cứu cho người không học luật), định nghĩa, nhãn thô 398, hòa giải 17, H7/R2 26, phiếu đọc mù, prompt + agent. Ngữ cảnh cho Claude: `vilextime_uit/CLAUDE.md`, `paper/` (PAPER_PLAN, RELATED_WORK, DIB_RULES).
- [ ] Cập nhật đề cương/khóa luận chỗ ghi "AI-A Claude, AI-B Codex": 28 lineage có cặp cùng họ (silver01 Claude–Claude, round2_codex Codex–Codex).
- [x] Bảng thống kê tự động: `vilextime_uit/scripts/check_dataset.py`.
- [ ] Viết bài theo template DiB (khung trong hội thoại 19/11): Methods + kiểm chất lượng trước.
- [ ] Nâng chất lượng trước khi nộp (đọc mù toàn bộ, chấm câu hỏi, đối chiếu nguồn ngoài vbpl): `docs/plans/active/2026-11-22-dib-qa-v6.md`.
- [ ] Evidence-gate mọi con số trước khi nộp.
- [ ] Đăng Mendeley Data (để chế độ chưa publish trong lúc review).

## Số đồng thuận dùng trong bài (nguồn)
- Gold mù đợt 2: luật sư–NMT 29/30, κ 0,932 (`data/review/gold_final/DONG_THUAN_B_20261116.md`); NMT–kho 80/81.
- Gold mù đợt 1 (người A/B, 24 lineage bộ cuối): khớp thô 148/150; 119/120 sau phân xử AI đề xuất (ADR 0006 §7).
- AI–AI trước hòa giải, 314 lineage: Q1–Q4 AC1 0,87–0,95; verdict 0,608 (`docs/reports/g2-co-mau-dong-thuan-20261109.md`).
