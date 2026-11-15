# Sửa paper theo PAPER_GAP, không thực nghiệm mới

Date: 2026-11-15

## Status
Blocked — chỉ còn commit, Git metadata ngoài vùng ghi

## Outcome and authority
Yêu cầu người dùng, PAPER_GAP mục 6–8: IEEE P0-1, W1–W6, W8; ACM ẩn danh sigconf <=10 trang. Không API/thực nghiệm/sửa runs, data, src, scripts/eval.

## Progress
- [x] Đọc workflow, paper, numbers; đối chiếu điểm G4 và ca release.
- [x] Sửa IEEE và ghi nguồn.
- [x] IEEE build thành công, 8 trang; abstract cuối 178 từ; không ??/unresolved refs/citations/overfull. Commit A đã thử và bị sandbox chặn.
- [x] ACM sigconf anonymous review, 7 trang gồm tham khảo; giữ nội dung khoa học và AI disclosure; TODO kho ẩn danh. Build/kiểm xong; commit B bị cùng giới hạn Git metadata.

## Decisions
W3 giữ đúng lineage, ghi rõ minh họa vì dự đoán không khớp lỗi trong hình. W5 đổi tên Gen-TV-R@1 để tách mẫu số/danh sách retrieval. Không tự điền thông tin tác giả/funding chưa biết.

## Risks and recovery
Khôi phục từng commit; không chạm thực nghiệm. Link anonymous còn TODO.

## Validation
latexmk -xelatex main.tex mỗi thư mục; kiểm ??, unresolved refs/citations, số trang, ACM ẩn danh, đối chiếu nội dung.

## Result
IEEE P0-1, W1–W6, W8 đã sửa. W3 dùng phương án được cho phép: giữ minh họa, nêu rõ không phải dự đoán đã lưu. Hai bản giữ nguyên mức khẳng định; 20 bản ghi metric/KTC so trực tiếp điểm G4 r1/r2; ca rank 6 và bãi bỏ qua cha so trực tiếp release/dự đoán. Nội dung khoa học và bibliography hai bản khớp, chỉ khác lớp tài liệu, ngắt dòng/co hình, metadata và khai báo nhận diện.

Không sửa runs/data/src/scripts/eval; không API, sinh lại, truy xuất lại hoặc chấm lại. TODO: anonymous repo XXXX; IEEE advisor email, CRediT, funding giữ nguyên vì thiếu dữ kiện. P0 khác và W7/W9–W12 ngoài phạm vi sửa này.

Git hiện là nhánh paper-codex-1115. Git add/commit thất bại vì không tạo được /home/trica/UIT_Thesis/graphrag-legal-thesis/.git/worktrees/graphrag-paper-codex/index.lock (read-only filesystem). Không có commit mới, không push/merge. Cần môi trường được ghi metadata worktree để commit hai phần với trailer người dùng yêu cầu.

Friction tái sử dụng: quyền ghi source worktree không bao gồm metadata Git được trỏ qua file .git. Chỉ báo lại, không sửa harness hoặc cấu hình Git. Python executable là python3, không có alias python.

