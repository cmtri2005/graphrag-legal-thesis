# Đăng ký trước: bộ test ViLexTime 7.0 (24/11/2026)

Commit **trước khi rút mẫu**. Sau mốc này mọi thay đổi ghi ở §8 (Sai lệch), kèm ngày và lý do; bài báo cáo cả luật cũ
lẫn luật mới. Plan: `docs/plans/active/2026-11-24-vilextime-v7-rebuild.md`.

## 0. Người và độ mù

| Vai | Ai | Được làm | Không được làm |
|---|---|---|---|
| A, B | CMT, NMT (hai tác giả) | Gán mọi dòng | Mở đáp án kho, nhãn của người kia, hay file nào trong `data/vilextime_v7/` ngoài phiếu của mình trước khi cả hai khóa |
| Luật sư | Luật sư cộng tác | Chốt mọi xung đột có nội dung pháp lý; xác nhận T5 | — |
| Claude | Agent | Rút mẫu, sinh câu hỏi, dựng phiếu, so máy, gợi ý tra cứu cho luật sư sau khi khóa | Đứng tên nhãn, chấm thay người |

- Chỉ rút lineage **chưa từng xuất hiện** trong `data/review/` hay bản phát hành cũ (§1), nên cả A và B đều chưa thấy
  đáp án kho của mẫu. Trước lô đầu, A và B ký `data/vilextime_v7/attestation.md`.
- Bài ghi: hai người gán đều là tác giả.

## 1. Khung mẫu

- Kho ứng viên `data/derived/vilextime_pool.jsonl` (11.408 lineage; sha256 ghi trong `data/vilextime_v7/frame.json`).
- Loại: mọi lineage xuất hiện trong `data/review/**` hoặc trong `data/vilextime_dataset*`, `data/vilextime_final`,
  `data/vilextime_dib`, `data/vilextime/test2_release*.jsonl`. Danh sách `data/vilextime_v7/frame_excluded.txt`.
- Giữ luật cũ của `sample_vilextime.py`: bỏ lineage có `flags`, bỏ T5 loại `correction`/`guidance_in_sync`, bỏ lineage
  có sự kiện chưa áp (R6), tối đa 2 lineage mỗi văn bản, không cắt một lineage giữa các ngày.
- Seed `20261124`. Hệ số rút dư như cũ (T1, T2, T5, T6 ×2; T3 ×3). Quota bản phát hành theo định nghĩa §9:
  T1 150, T2 450 (trong đó T4 150), T3 150 (sàn 120), T5a mọi ca luật sư xác nhận, T6 350 (T6a 100, T6b 250).
- Thiếu thì rút tiếp theo thứ hạng; không đạt sàn thì giảm quota, không nới điều kiện (§9).

## 2. Câu hỏi

`generate_questions.py` như các bản trước (một câu hỏi mỗi lineage, qua `validate()`). Câu hỏi đã sinh cho lineage
trong khung được dùng lại. Đáp án ngắn do người gán viết ở giai đoạn 1, không do LLM.

## 3. Gán nhãn hai giai đoạn, mỗi dòng

**Giai đoạn 1, mù đáp án kho.** Phiếu có: câu hỏi, ngày hỏi, văn bản đích và đường dẫn văn bản gốc. Không có lời văn
kho, không có nhóm, không có ngày chuyển. Người gán tự tra nguồn (văn bản gốc, văn bản sửa đổi, VBHN, Công báo) và
điền:
- `hieu_luc` (còn / hết) tại ngày hỏi;
- `noi_dung`: lời văn đang áp dụng, dán nguyên văn;
- `dap_an_ngan`: câu trả lời ngắn cho câu hỏi, trích từ `noi_dung`;
- `van_ban_ap_dung`: số hiệu văn bản đã tạo ra lời văn đó (văn bản gốc hoặc văn bản sửa đổi);
- `phut`.

Khóa giai đoạn 1 (sha256) rồi mới mở giai đoạn 2.

**Giai đoạn 2, có lời văn mọi phiên bản của kho.** Điền:
- Q2 `hoi_vao_cho_doi`: có / không / không chắc / không áp dụng (một phiên bản);
- Q3 `tra_loi_duy_nhat`: có / không / không chắc; `lo_dap_an`: có / không;
- mã lý do §7 nếu "không".

**Nhãn suy ra (máy):**
- Q1 = máy so giai đoạn 1 với kho: `hieu_luc` bằng nhau; dòng còn hiệu lực thì `noi_dung` sau chuẩn hóa nằm trong lời văn
  kho (`machine_agrees`).
- Q4 = `van_ban_ap_dung` khớp văn bản tạo phiên bản kho, và người gán không ghi quy định khác thay thế.
- `dat` khi Q1 khớp, Q2 có (hoặc không áp dụng với T1), Q3 có và không lộ, Q4 khớp.

## 4. Hòa giải

- Xung đột: A khác B ở bất kỳ câu nào; hoặc cả hai khác kho.
- Luật sư chốt mọi xung đột có nội dung pháp lý; Claude được tra và trình trích dẫn, không quyết.
- Lỗi dán chữ hay dán nhầm điểm: người gán tự sửa sau khi mở, ghi lại bản trước và bản sau.
- Lỗi kho đã xác nhận: sửa ở tầng kho, đánh cờ `store_corrected`, dòng vẫn được giữ nếu đạt sau sửa.

## 5. Chỉ số

- Đồng thuận A–B **trước hòa giải**, từng câu Q1–Q4 và nhãn suy ra: tỷ lệ khớp thô, Gwet AC1, Cohen κ (ghi "không xác
  định" khi một bên chỉ có một hạng). Theo nhóm.
- Tỷ lệ lỗi kho theo nhóm (Wilson 95%), sau hòa giải.
- Phút trung vị mỗi dòng, theo người và theo giai đoạn.
- Phễu: rút → có câu hỏi → đạt → bản phát hành, theo nhóm, kèm mã loại.

## 6. Bản phát hành và thực nghiệm

- 7.0 chỉ gồm dòng `dat` sau hòa giải. `check_release.py` đạt.
- G4 trên 7.0: cùng 12 hệ và cấu hình ADR 0006, chạy một lần (hai lần gọi API như cũ). Cần amendment ADR 0006 được CMT
  duyệt trước khi chạy.

## 7. Giới hạn biết trước

- Hai người gán là tác giả.
- Kho chỉ áp 38,7% lệnh sửa đổi; lỗi sót sửa đổi chỉ bắt được qua tra nguồn ở giai đoạn 1.
- T3 chỉ còn 183 lineage trong khung.

## 8. Sai lệch so với đăng ký

Chưa có.
