# Phễu lọc lô mới (A4), 05/11/2026

Bộ lọc LLM chạy trước khi đưa câu cho người, theo lời dặn `prompts/vilextime/test2_loc.md` (nguyên byte). Đây là bước xếp loại, **không phải nhãn kiểm định**. Kết quả trên T6 và T2 của bộ test cuối là **có điều kiện theo bộ lọc này** (ADR 0006, phản biện N3).

- 51 gói, 2.032 mục: 1.964 ứng viên và 68 câu hiệu chuẩn có nhãn người độc lập (40 tốt, 28 xấu), trộn ngẫu nhiên; bên lọc không biết câu nào là hiệu chuẩn.
- Model: 2 gói Claude Sonnet (`claude -p`, không công cụ), 49 gói Codex (`codex exec`, chỉ đọc, không mạng; model trong cấu hình `gpt-6.1-sol`, log không xác nhận). Lý do đổi: hạn mức Claude dùng chung với phiên điều phối.
- Chạy lại: chỉ gói dừng vì hạn mức, hoặc lỗi định dạng (mỗi gói tối đa một lần vì định dạng: pack_06, pack_18, pack_20, pack_38, pack_50). Không chạy lại gói nào đã có quyết định hợp lệ.
- Hồ sơ đầy đủ (gói, phản hồi nguyên văn, khóa) ở `~/vilextime_loc/gan5/`, ngoài repo. sha256 `result.tsv`: `d6a6db16398b77451f01afd10c1ed6544d66b2d9c9ac0961c9b58ec19ad3aacd`.

## Hiệu chuẩn (68 câu có nhãn người)

| Tầng | Câu xấu | Loại đúng | Câu tốt | Loại nhầm |
|---|---:|---:|---:|---:|
| Toàn tập | 28 | 1,00 | 40 | 0,28 |
| T2 | 0 | — | 25 | 0,08 |
| T2 gần giống | 2 | 1,00 | 3 | 1,00 |
| T3 | 1 | 1,00 | 4 | 0,50 |
| T6 cấp trên | 17 | 1,00 | 8 | 0,50 |
| T6 đích danh | 8 | 1,00 | 0 | — |

Ngưỡng khai trước: loại đúng ≥ 0,80, loại nhầm ≤ 0,30, đo trên toàn tập: **đạt, sát ngưỡng** (thêm một câu tốt bị loại là trượt). Theo tầng, mẫu quá nhỏ để kết luận; T6 cấp trên loại nhầm 4/8. Người sẽ kiểm 20 câu T6 bị loại, rút ngẫu nhiên, để ước lượng tỷ lệ loại nhầm trên ứng viên thật.

## Phễu theo tầng (chỉ ứng viên)

| Tầng | Ứng viên | Giữ | Loại | Tỷ lệ giữ |
|---|---:|---:|---:|---:|
| T2 | 280 | 157 | 123 | 0,561 |
| T2 gần giống | 140 | 63 | 77 | 0,45 |
| T6 cấp trên | 1217 | 48 | 1169 | 0,039 |
| T6 đích danh | 327 | 50 | 277 | 0,153 |

## Mã lý do của câu bị loại

| Tầng | Mã (số câu) |
|---|---|
| T2 | `gold_wrong` 48, `other` 22, `reference_only` 15, `restructuring_2025` 12, `cosmetic_only` 11, `rename_only` 8, `auto_reference_update` 4, `transitional_rule` 2, `superseded_by_other_norm` 1 |
| T2 gần giống | `cosmetic_only` 23, `gold_wrong` 19, `rename_only` 14, `restructuring_2025` 9, `other` 5, `reference_only` 4, `transitional_rule` 2, `auto_reference_update` 1 |
| T6 cấp trên | `relocation_unclear` 600, `gold_wrong` 162, `relocated` 146, `other` 95, `reference_only` 69, `superseded_by_other_norm` 47, `restructuring_2025` 28, `transitional_rule` 22 |
| T6 đích danh | `relocation_unclear` 117, `gold_wrong` 53, `reference_only` 38, `relocated` 33, `other` 25, `restructuring_2025` 8, `superseded_by_other_norm` 3 |
