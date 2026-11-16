# Sửa gold theo ADR 0006 §7 — 16/11/2026
CMT duyệt trong hội thoại ("sửa luôn", rồi "oke" cho hai lineage còn lại). Ba lineage kho sai do người đọc mù phát hiện, 4 dòng bộ cuối (chi tiết, căn cứ trong `make_release.py`):
- **F019** (luật sư 16/11), `…4cee6a60…:2026-08-06` → không có đáp án: TT 36/2026/TT-BXD Điều 16 khoản 2 bãi bỏ TT 11/2021/TT-BXD từ 01/07/2026 (đã đọc văn bản gốc).
- **F060** (NMT 15/11), `…a16089ba…:2017-04-29` và `:2019-02-28` → trỏ phiên bản 2 (lời văn trùng), hiệu lực từ 01/03/2017 theo khoản 2 Điều 1 TT 32/2016/TT-NHNN (theo ghi chú NMT; chưa đọc lại văn bản gốc).
- **F016** (NMT 15/11), `…7ba9e014…:2020-04-04` → đáp án ngắn "Phối hợp với Văn phòng Chính phủ", lời văn theo khoản 9 Điều 2 NĐ 92/2017/NĐ-CP từ 25/09/2017 (theo ghi chú NMT). Kho không có phiên bản này; `version_id` trỏ phiên bản 1 (cùng đáp án ngắn, lời văn khác), nên TV-Recall dòng này vẫn theo kho.
Bản release đã sửa ở thư mục này; **không sửa** `data/vilextime_final`. Chỉ chấm lại dự đoán đã lưu (`run.sh`), không gọi model.

**Kết quả:** phán quyết F1–F7 không đổi ở GPT-4o mini và Qwen, cả hai lần. GPT: |Δ ước lượng| ≤ 0,0033 (F3 r1 −0,283 → −0,286; F5 +0,115 → +0,116; F1, F2, F7 không đổi). Qwen F3 −0,309 (r1, r2). Oracle GPT r1 0,956 → 0,953.
Phần có gold mù người, nay **105 lineage / 215 dòng** (`subset/`, gồm cả 2 lineage trước bị loại): F1 +0,284 [+0,208; +0,359] / +0,316; F3 −0,245 / −0,258; F5 +0,073 [+0,032; +0,119]; F1–F6 ủng hộ, F7 không đủ bằng chứng, cả hai lần.
Paper giữ số chính theo gold đã phát hành và nêu kết quả gold đã sửa ở đoạn gold mù. Chưa làm: phát hành bản ViLexTime sửa lỗi (errata), cần CMT quyết.
