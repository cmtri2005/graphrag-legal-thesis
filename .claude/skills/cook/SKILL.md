---
name: cook
description: Chạy nhóm nghiên cứu nhiều agent cho khóa luận — chia việc cho vn-law-verifier, lit-scout, thesis-critic chạy song song rồi gộp kết quả có nhãn bằng chứng. Gọi bằng /cook <việc cần làm>.
argument-hint: <câu hỏi hoặc việc, ví dụ "kiểm 20 dòng T6 đầu tiên của data/review/kiem_A.tsv">
---

Việc: $ARGUMENTS

1. Đọc đủ repo để hiểu việc (master plan, MASTER_RESEARCH_GUIDE §0, file liên quan).
   Nếu việc chỉ cần một agent thì chỉ gọi một agent; không gọi cho đủ bộ.
2. Chia thành các phần độc lập và gọi các agent **trong cùng một lượt** để chạy song song:
   - `vn-law-verifier`: mọi khẳng định pháp lý (số hiệu, Điều/Khoản, hiệu lực tại ngày t).
     Lawgical chỉ 20 lượt/ngày: gom khẳng định, mỗi agent một lô không trùng nhau.
   - `lit-scout`: tài liệu, tính mới, baseline, phương pháp thống kê.
   - `thesis-critic`: phản biện thiết kế, bằng chứng, thống kê.
   Mỗi prompt phải tự đủ: đường dẫn file, phạm vi dòng, định dạng đầu ra, ngày hôm nay.
   Việc lớn (vd. 100 truy vấn M2) thì chia lô cho nhiều `vn-law-verifier` song song.
3. Gộp kết quả: đối chiếu chéo, nêu chỗ các agent mâu thuẫn, gắn nhãn
   [Đã kiểm] / [Repo] / [Web] / [Giả định] như MASTER_RESEARCH_GUIDE.
4. Báo người dùng: kết quả trước, câu ngắn, ít thuật ngữ. Chỉ ghi file khi người dùng
   yêu cầu hoặc khi việc vốn là sửa file; không commit.
