---
name: experiment-evidence
description: Hợp đồng artifact thực nghiệm KLTN — code/data/model/prompt hash, log và nguồn từng số; tái chấm offline, cổng test và thống kê theo ADR của ViLexTime.
---

## Tìm authority trước khi thực thi/kiểm

Đọc `runs/README.md`, ADR của đúng bộ dữ liệu, phần liên quan trong master plan,
CLI/code và test của thao tác. ADR 0005 và amendments mô tả v1.0/test 2; không
tự áp ADR 0006 khi nó chưa Accepted, được duyệt và commit đủ đầu vào. Ngày sửa
file không chứng minh phê duyệt có trước lượt chạy; kiểm lịch sử commit.

Dev dùng phát triển. Test cần khóa release/split/config/prompt, cổng phê duyệt
và scope được giao. Không gọi runner thấp để né `scripts/eval/final_run.py`.
`test 2` là nhãn LLM; số Accuracy hợp lệ ở `runs/E3_test2/rescore/`. Không gộp
v1.0, test 2 và bộ cuối thành một tập xác nhận, không thay vai trò lịch sử.

## Hợp đồng bằng chứng

Mỗi run lưu cùng output, theo cấu trúc hiện có của `runs/`:

- ID run và thời gian UTC, lệnh đầy đủ, cwd, exit code, stdout/stderr/log, seed,
  máy/GPU/backend và phiên bản dependencies thực tế. Ghi failed/resume/rerun.
- `git rev-parse HEAD`, trạng thái dirty, patch/code snapshot hoặc digest từng
  file ảnh hưởng nếu chưa commit. Chỉ HEAD là thiếu khi working tree khác HEAD.
- Release/manifest/split và ID/lineage, corpus/index, config, prompt, predictions
  và score: đường dẫn, SHA256 của byte đã dùng. Ghi hash trước và sau để phát
  hiện nguồn đang đổi. Không ghi nội dung credentials hoặc toàn bộ environment.
- Model/revision/tokenizer/quantization, generation settings; training run có
  checkpoint path + hash và quy tắc chọn checkpoint. Hosted model không có
  checkpoint thì ghi N/A cùng model ID thực tế, không bịa.
- Một dòng truy vết cho từng số trong report: vị trí claim, đại lượng/đơn vị,
  split/lát, n/mẫu số, input/output có hash, JSON key/dòng, công thức và làm tròn,
  lệnh tái tính, commit + patch. Số dẫn xuất có thể dẫn nhiều nguồn rõ ràng.

Không sửa log/score gốc để làm khớp báo cáo. Thay input/gold/scorer sau quan sát
phải giữ bản cũ, ghi amendment/phê duyệt và phạm vi chấm lại; không giả đó là
một thiết kế đã đăng ký trước.

## Chấm và tái lập

Dùng scorer `scripts/eval/score_vilextime.py`, kiểm định
`scripts/eval/confirm_vilextime.py`, báo cáo `scripts/eval/report_results.py`;
xem `--help` trước khi tạo lệnh, không bịa cờ. Mẫu kiểm dùng `--ids`, đúng release
và split dev được chỉ định; chấm lại cùng predictions đã lưu. Ghi ID mẫu/seed,
hash, lệnh và exit code. Không tự sinh đầu ra LLM mới để “tái lập scorer”.

Kiểm đủ ID, trùng ID, thiếu dự đoán, đáp án ngắn rỗng, mẫu số answerable và
unanswerable, câu dẫn, parser và accepted evidence. Bootstrap theo cụm lineage,
so sánh ghép cặp, CI và Holm theo **ADR đang áp dụng**; không đổi B/seed/family
sau thấy kết quả. CI mẫu nhỏ hoặc smoke test không chứng minh toàn bộ số test.

Executor tạo/sửa artifact; gate kiểm trên phiên mới và chỉ ghi output ở thư mục
tạm. Kết luận nêu rõ phần đã tái chạy, phần chỉ đọc và phần chưa kiểm được.
`PASS` trong lời đáp là review của AI, không tự cài hook/CI hoặc phê duyệt người.
