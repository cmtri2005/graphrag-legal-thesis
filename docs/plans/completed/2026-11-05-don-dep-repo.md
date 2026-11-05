# Execution Plan: C2 — Dọn repo theo danh sách đã duyệt

Date: 2026-11-05

## Status

Completed trong phạm vi đã duyệt; ngoại lệ tham chiếu docstring được ghi dưới đây.

## Outcome

Chuyển 32 file; xóa 216 file, tổng 205.532 MB (1 MB = 1.000.000 byte).
Đây là dung lượng các file bị xóa, chưa trừ phần tài liệu viết thêm; không đo dung lượng `.git`.
Chỉ còn `README.md` và `master-plan.md` trong `docs/plans/active/`.

## Context

Hợp đồng C2 do Claude (lead) chốt ngày 05/11, theo yêu cầu dọn repo của CMT, thay cột action của inventory. CMT chưa duyệt từng mục; CMT xem diff trước khi commit.
Claude kiểm lại độc lập: 735 hash file giữ nguyên (khác đúng 1 file, chỉ đổi comment nguồn), 27 file chuyển khớp hash, 611 test qua (615 trừ 4 test của hai script agent đã xóa), nhập lại `b1` trùng 211/211 câu trả lời, chấm lại `b7pp` ra đúng số cũ ở cả hai bộ. Trong `runs/README.md`, Codex sửa thêm một số đường dẫn cho đúng cây mới, ngoài danh sách; số liệu không đổi.
Authority: `docs/plans/active/master-plan.md` mục 2, 8, 9; `docs/WORKFLOW.md`.
Có sẵn thay đổi chưa commit trước phiên. Không commit, stage hay dùng thao tác Git làm đổi trạng thái.

## Scope

Chỉ chuyển, xóa và sửa tài liệu/tham chiếu trong danh sách C2.
Không đọc `.env`, không mạng, không sinh bằng LLM hay chạy lại hệ thí nghiệm.
Không sửa harness, master plan, ADR, code `src/`, dự đoán được giữ hoặc nhãn người.

## Approach

Kiểm inventory và sha256 → `mv` giữ byte → kiểm prompt → `rm` → sửa tham chiếu, README → kiểm chứng.

Đã chuyển:

| Nguồn | Đích | File |
|---|---|---:|
| colab_upload/v1/ và test2/: JSONL, export JSON | runs/E3_v1/prompts/, runs/E3_test2/prompts/ | 24 |
| colab_upload/README_COLAB.md | notebooks/README.md; sửa đường dẫn, ghi hủy round2 | 1 |
| raw_ac8357cc9f36.jsonl | data/vilextime/test2_generation/ | 1 |
| Workbook gán nhãn ở gốc và docs/hoa_giai_lo0_chot.xlsx | data/review/; sửa 2 đường dẫn đã chỉ định | 2 |
| related_work_paper/FiscalQA.md và reports/*.md | related_paper/notes/; sửa comment nguồn chương 2 | 2 |
| lai-ghep-va-vbhn.md, rerank-va-do-thi-t6.md | completed/2026-11-05-lai-ghep-va-vbhn.md, 2026-11-05-do-thi-t6.md | 2 |

Hai plan chưa track giữ toàn bộ nội dung ngoài Status/Result; hai mục ghi đúng câu đóng đã yêu cầu.
27 file không phải Markdown giữ nguyên sha256; FiscalQA và báo cáo cũng giữ nguyên byte.

Đã xóa (nhóm ứng với các đường dẫn được liệt kê trong hợp đồng C2):

| Nhóm | File | MB | Lý do | Bản thay thế / nơi đọc lại |
|---|---:|---:|---|---|
| root | 11 | 12.841 | Đầu ra rời, bản tạm, hướng dẫn cũ | Raw khớp trong runs/; master plan; 51f36c7 |
| duplicates | 38 | 3.063 | Trùng byte | runs/B2_dev/raw/, runs/E3_v1/raw/, runs/E3_test2/raw/ |
| old-packages | 56 | 68.112 | Gói upload cũ, round2 đã hủy, thư mục đã chuyển hết tài liệu cần giữ | runs/E3_*/prompts/, notebooks/README.md, related_paper/notes/ |
| old-plans | 11 | 0.293 | Plan đã thay thế; kể cả vilextime-test2.md có diff chưa commit | master-plan.md; 51f36c7 và backup diff |
| old-docs | 6 | 0.191 | Tài liệu, hình và báo cáo cũ trong danh sách đã duyệt | README.md mới, master plan, báo cáo E3/E7/D5/VBHN được giữ; 51f36c7 |
| old-runs | 73 | 117.789 | Lượt cũ và gói xuất đã được duyệt bỏ | runs/E1/, runs/W2-12_rerun/, data/vilextime_dataset/, E3 prompts; 51f36c7 |
| old-scripts | 7 | 0.022 | Script khảo sát/agent và 2 file test riêng; không có import ngoài | 51f36c7; giữ các công cụ review còn dùng |
| review-temporary | 11 | 3.123 | Phiếu và thống kê tạm đã duyệt bỏ | Nhãn đã chốt trong data/review/ giữ nguyên; 51f36c7 |
| data-trial | 3 | 0.098 | Bản thử đã duyệt bỏ | questions_test2.jsonl, short_answers_test2.jsonl và bản phát hành; 51f36c7 |

README mới 69 dòng, bảng nguồn sự thật chép nguyên mục 2; chi tiết vận hành cũ chuyển cuối `docs/crawling-plan.md`.
Sửa 34 comment nguồn trong các chương; giữ câu văn. Template paper sửa hai chỗ đợt 2 rồi dựng lại bằng script.
`runs/README.md` ghi xóa lượt cũ, kết quả lai ghép và proposed2; `.gitignore` chỉ nối khối đã yêu cầu.

## Risks And Recovery

- File đã track: đọc lại từ commit `51f36c7` (ví dụ `git show 51f36c7:<đường-dẫn>`); không dùng checkout/reset trong phiên này.
- Bản sao lưu trước dọn: `/home/trica/UIT_Thesis/backup-pre-cleanup-20261105/` có `tracked.diff`, `untracked.tar.gz`, `SHA256SUMS`.
- Để giữ cả thay đổi chưa commit: khôi phục bản commit trong thư mục tạm, áp diff và lấy file chưa track từ backup; đối chiếu hash trước khi đưa lại repo. Hai plan chưa commit hiện đã chuyển an toàn sang completed/.

## Progress

- [x] Kiểm 43/43 file Qwen/b1/b2ctx và vilextime_* trùng sha256 bản được giữ trong runs/.
- [x] Kiểm 12/12 prompt (6 mỗi bộ) khớp prompt_file_sha256 của test/*.run.json trước khi xóa test_prompts/.
- [x] Rà import trên toàn bộ Python trong src/, scripts/, tests/: không có import các script xóa ngoài test riêng.
- [x] Chuyển, xóa, sửa tài liệu và chạy các kiểm tra bên dưới.

## Decisions

- 2026-11-05: Không mở rộng danh sách. `scripts/pipeline/enrich_vilextime.py:230` chỉ nhắc `reports/Phương án T2 và T5` trong docstring; tài liệu này không có trong inventory. Dừng sửa tham chiếu này theo lệnh giữ comment/docstring của code; không có chuỗi đường dẫn thực thi cần đổi.
- Không thiếu file nguồn hoặc lệch hash trong danh sách chuyển/xóa. `dev_graph2/` chưa có score JSON; tính lại từ dự đoán bằng scorer, chỉ ghi log/điểm mới ngoài repo.

## Validation

| Lệnh / phép kiểm thực chạy | Kết quả |
|---|---|
| `HF_HUB_OFFLINE=1 .venv/bin/python -m pytest -q` | Exit 0; 611 passed in 82.74s; 4 test thuộc 2 file agent đã xóa |
| `git diff --check` | Exit 0 |
| `.venv/bin/python scripts/paper/paper_build.py` | Exit 0; 7.001 từ, 11 tài liệu |
| `.venv/bin/python scripts/paper/paper_check.py` | Exit 0; sai lệch 0, bắt 3/3 lỗi cấy |
| `HF_HUB_OFFLINE=1 .venv/bin/python scripts/eval/score_vilextime.py runs/B2_dev/dev/b1.jsonl --split dev --release data/vilextime_dataset/vilextime.jsonl` | Exit 0; lệnh chấm README chạy được, chỉ đọc dự đoán có sẵn |
| `HF_HUB_OFFLINE=1 .venv/bin/python scripts/eval/colab_b1.py import --prompts runs/E3_v1/prompts/b1.jsonl --raw runs/E3_v1/raw/b1__Qwen__Qwen3-4B-Instruct-2507__1eae3c6c8b43.jsonl --out /tmp/c2-cleanup/reimport/b1.jsonl` | Exit 0; 211/211 dòng, ID đúng cả thứ tự, nội dung dự đoán trùng toàn bộ |
| `.venv/bin/python /tmp/c2_verify.py` | Exit 0; 117 đường dẫn cụ thể trong 3 README tồn tại; mẫu đường dẫn, model/Drive và các lượt đã ghi xóa được phân biệt rõ; 564 hash bảo vệ không đổi; 2 plan giữ nguyên phần còn lại |
| `HF_HUB_OFFLINE=1 .venv/bin/python /tmp/c2_score.py` | Exit 0; dùng load_rows, units_of, score của scorer, không gọi retriever/generator |

Điểm tính lại: dev → dev_graph2 R@30 **122/151 = 0,807947 → 137/151 = 0,907285**;
T6 không đáp án **0/21 → 15/21**; R@1 **62/151**, R@10 **111/151**, cả hai không đổi.
Lượt lai ghép cũ lấy từ `runs/hybrid_20261105/dev/retrieval.score.json`: R@1 0,424 → 0,411, R@10 0,722 → 0,735; chỉ truy xuất.
Log và inventory chi tiết (đường dẫn, byte, sha256, bản trùng) ở `/tmp/c2-cleanup/`; các script kiểm một lần ở `/tmp/c2_*.py`.

## Result

Đã hoàn thành dọn theo danh sách, giữ ngoại lệ docstring ở trên để lead rà lại. Không tự sửa logic để qua test.
Văn chương còn nhắc tài liệu/thư mục đã xóa, được giữ đúng yêu cầu:

- `docs/thesis/chuong-2-co-so-ly-thuyet.md:26`: `reports/` (báo cáo đã chuyển sang related_paper/notes/).
- `docs/thesis/chuong-6-thuc-nghiem.md:293`: `MASTER_RESEARCH_GUIDE §8.6`.
