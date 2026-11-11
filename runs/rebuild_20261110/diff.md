# H6 diff sau khi dựng lại (NHÁP, chưa kiểm độc lập)

Sinh bởi `runs/rebuild_20261110/h6_diff.py`; số liệu đầy đủ ở `diff.json`.

## Đồ thị

- Phiên bản: {'old': 1598648, 'new': 1598662, 'only_old': 1, 'only_new': 15, 'text_changed': 50293, 'window_changed': 16224}
- Sự kiện: số dòng 56624 -> 56624; chỉ có ở bản cũ 0, chỉ có ở bản mới 0
- Chuyển trạng thái sự kiện (cùng id):

  - needs_review/document_scope -> auto_accepted/None: 278
  - auto_accepted/None -> needs_review/partial_repeal: 23
  - needs_review/phrase_not_found -> auto_accepted/None: 14
  - needs_review/document_scope -> needs_review/partial_repeal: 10
  - same status, text_updates changed: 7
  - verified/None -> needs_review/partial_repeal: 3
  - needs_review/phrase_not_found -> verified/None: 2
  - verified/None -> needs_review/phrase_not_found: 1

## Theo tập (dòng đã dựng lại, so theo id)

| Tập | dòng cũ | dòng mới | excluded:partial_repeal | excluded:superseded_by_other_norm | lead_in_only_changed | missing_from_new | new_only | same | version_text_changed |
|---|---|---|---|---|---|---|---|---|---|
| dev | 328 | 328 | 0 | 0 | 11 | 1 | 1 | 312 | 4 |
| v1.0_test | 441 | 439 | 1 | 1 | 10 | 1 | 1 | 428 | 0 |
| silver_old859 | 859 | 879 | 0 | 0 | 20 | 0 | 20 | 837 | 2 |

Chế độ `giua_khoang` (dòng được chấm ở tiêu đề):

- dev: lead_in_only_changed=5, missing_from_new=1, same=143, version_text_changed=2
- v1.0_test: excluded:partial_repeal=1, excluded:superseded_by_other_norm=1, lead_in_only_changed=5, missing_from_new=1, same=203
- silver_old859: lead_in_only_changed=10, same=378, version_text_changed=1

## Theo tập (tính lại từ versions.jsonl mới, không dựng lại file)

- lo1_silver (369 dòng): same=369
- lo2 (258 dòng): same=258
- lo0 (65 dòng): same=65
- test2 (492 dòng): same=492

## release.jsonl dẫn xuất (2383 -> 2383 dòng, so theo id)

- dev/giua_khoang/changed: 2
- dev/giua_khoang/only_new: 1
- dev/giua_khoang/only_old: 1
- dev/ranh_gioi/changed: 2
- test/giua_khoang/changed: 1
- test/giua_khoang/only_new: 12
- test/giua_khoang/only_old: 12
- test/ranh_gioi/changed: 1
- test/ranh_gioi/only_new: 10
- test/ranh_gioi/only_old: 10
- lineage rời release only_old/test/T1: 1
- lineage rời release only_old/dev/T2: 1
- lineage rời release only_old/test/T2: 1
- lineage rời release only_old/test/T6: 5
- lineage vào release only_new/test/T1: 1
- lineage vào release only_new/dev/T2: 1
- lineage vào release only_new/test/T2: 1
- lineage vào release only_new/test/T6: 5

## Gold mù (150 dòng)

excluded:superseded_by_other_norm=1, lead_in_only_changed=4, same=145

## Id dòng dev đổi (mọi chế độ)

- version_text_changed (4): vilextime:T1:provision:5003ac4e-eb7e-11f0-a0a3-c9aae40c2eb7:2004-07-13; vilextime:T1:provision:5003ac4e-eb7e-11f0-a0a3-c9aae40c2eb7:2010-08-12; vilextime:T3:provision:d427a720-2d53-11f1-a1cc-67f2013d5aa0:2016-06-30; vilextime:T3:provision:d427a720-2d53-11f1-a1cc-67f2013d5aa0:2014-07-12
- lead_in_only_changed (11): vilextime:T1:provision:376b89bc-ec3d-11f0-9575-3f5b1452526c#k3:2016-09-03; vilextime:T1:provision:376b89bc-ec3d-11f0-9575-3f5b1452526c#k3:2018-05-18; vilextime:T2:provision:1a9e95e0-eb7f-11f0-9f77-311425e86753#k9:2020-01-02; vilextime:T2:provision:1a9e95e0-eb7f-11f0-9f77-311425e86753#k9:2018-03-04; vilextime:T2:provision:1a9e95e0-eb7f-11f0-9f77-311425e86753#k9:2019-12-04; vilextime:T2:provision:1a9e95e0-eb7f-11f0-9f77-311425e86753#k9:2020-01-03; vilextime:T2:provision:1a9e95e0-eb7f-11f0-9f77-311425e86753#k9:2021-03-23; vilextime:T3:provision:d427a720-2d53-11f1-a1cc-67f2013d5aa0:2018-01-31; vilextime:T3:provision:d427a720-2d53-11f1-a1cc-67f2013d5aa0:2016-11-12; vilextime:T3:provision:d427a720-2d53-11f1-a1cc-67f2013d5aa0:2018-02-01; vilextime:T3:provision:d427a720-2d53-11f1-a1cc-67f2013d5aa0:2021-08-01
- missing_from_new (1): vilextime:T2:provision:f69ce10e-eb76-11f0-a3ad-7b197f745334:2018-10-02
- new_only (1): vilextime:T2:provision:f69ce10e-eb76-11f0-a3ad-7b197f745334:2018-08-09

## Giải thích thay đổi thành phần (bổ sung của executor tiếp quản, 10/11, NHÁP chưa kiểm độc lập)

- `selected.jsonl` cũ so với mới: 5 lineage T6 rời, 5 lineage T6 vào (selected.jsonl chỉ đổi ở T6; T1 1 và T2 1 trong bảng release ở trên CHƯA được giải thích riêng, cần kiểm thêm).
- Nguyên nhân T6: sau sửa L2 (văn bản hết hiệu lực), cửa sổ của phiên bản cuối đổi. Ví dụ `provision:75e9b4f6-eb8a-11f0-93ee-ed6a8e367972`: trước `[2018-02-01, 2026-04-29)`, nay `[2018-02-01, null)`. Dòng "sau khi hết hiệu lực" (đáp án None, T6) không còn tồn tại nên lineage không còn trong `T6.jsonl`; `sample_vilextime.py --select` (không đổi quy tắc) lấy lineage xếp hạng kế tiếp. Kiểm: 5 lineage rời đều vắng trong T6.jsonl mới và không bị R6 chặn (R6 chặn 0/5), tức đổi thành phần là do cửa sổ phiên bản, không do bị loại thủ công. Phần lớn dòng test T6 trong `ranh_gioi` đổi theo.
- Dev `f69ce10e…:2018-10-02` -> `2018-08-09` (giua_khoang, T2): phiên bản 2 trước `[2018-06-22, null)`, nay `[2018-06-22, 2021-01-11)` (cửa sổ đóng do L2); điểm giữa khoảng dời theo cửa sổ.
- Không sửa code để giữ thành phần test; chỉ báo.
