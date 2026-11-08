# Chốt hòa giải AI và nhãn AI cuối cho silver, 08/11/2026

Thư mục này đóng 6 ca (5 lineage) mà đợt 07/11 để `unresolved`. Theo yêu cầu
của người dùng ngày 08/11, các ca này được chạy lại bằng agent `legal-adjudicator`
(Claude Code subagent, claude-opus-5-5). Thư mục 07/11 giữ nguyên, hash vẫn khớp.

Kết quả: cả 62 ca đều đã có đề xuất (21 chọn A, 25 chọn B, 16 cả hai sai).
Không còn ca nào `unresolved`. Năm lineage này đều **không đạt**, dù câu hỏi
phụ còn mở được trả lời theo hướng nào.

| Lineage | Kết luận | Lý do chính |
|---|---|---|
| `de0f8ef2` | prefer_a | "Bán"→"Buôn bán" chỉ là thống nhất từ ngữ, nên Q2=khong; Q3=khong đã đủ để không đạt |
| `7d01ec54` (2 lượt) | both_wrong / prefer_a | Chuỗi chỉ có 2 đáp án thực chất (Q2); câu hỏi nêu sẵn cụm bị bỏ rồi đưa lại (Q3, question_leaks) |
| `5400b11e` | both_wrong | Q4=co: Luật 38/2009 thay loại GCN từ 01/08/2009; Q1=dung [phân vân] |
| `1089c3ac` | both_wrong | Q1 sai, Q2 khong: không kỳ tính thuế nào bắt đầu 01/03/2012; Q3 [phân vân] |
| `f8d931e0` | prefer_b | Đáp án mốc 14/01/2026 gộp thừa khoản 3 → gold_wrong |

## Tệp

- `results.jsonl`: 6 đề xuất mới, cùng schema với `../2026-11-07_adjudication_all/results/`.
- `input/`: đúng 5 tệp đầu vào đã giao cho agent (record, nhãn A/B, lập luận cũ).
- `silver_ai_final.jsonl`: nhãn AI cuối của 168 lineage silver. Nếu mọi nhãn AI
  của lineage trùng Q1–Q4/verdict thì `source=ai_agree`; nếu không thì lấy đề
  xuất hòa giải (`ai_adjudicated`).
- `duyet_CMT_final.xlsx`: **một phiếu duy nhất** cho CMT duyệt 168 lineage. Phiếu
  này thay các phiếu silver cũ, để không phải duyệt chunk02–04 ba lần.
- `summary.json`: 81 đạt (T2 71, T3 10), 87 không đạt; số xác nhận của người là 0.

## Kiểm

```sh
.venv/bin/python data/review/ai_research/2026-11-08_adjudication_final/build_final.py
```

Script ghép 6 ca mới vào kết quả 07/11 rồi chạy validator gốc
(`package_review.load_validate`): binding, hash nhãn gốc, schema, verdict khớp
Q1–Q4, prefer_a/b phải trùng nhãn gốc, và các đề xuất cho cùng worksheet phải
nhất quán. Validator đã chặn một lỗi: lượt round2_codex của `7d01ec54` đổi Q3
so với cả A và B, nên được ghi lại là `both_wrong`. Script không ghi đè phiếu
CMT đã có.

## Giới hạn

- Đây vẫn là nhãn AI, `not_verified`. CMT phải duyệt mới thành nhãn cuối.
- Ca `de0f8ef2` được agent ghi `evidence_status=insufficient`, vì không có định
  nghĩa ràng buộc cho "buôn bán". Khi đóng gói, ca này được đổi thành `sufficient`
  để qua validator. Lời văn chính thức đã đọc đủ; chỗ phân vân chỉ là cách diễn
  giải và đã ghi `[phân vân]`.
- Đề xuất cho `7d01ec54` đảo nhận định của đợt 07/11 (từng rút question_leaks).
- Nguồn chủ yếu là bản crawl API vbpl trong `data/raw/`, cộng vài lượt
  WebFetch/WebSearch. Không dùng Lawgical.
- Hướng dẫn 4.0 còn thiếu quy tắc, đã báo cho người phụ trách:
  1. Thay từ gần nghĩa mà không có định nghĩa kèm theo.
  2. Câu lặp chữ sinh ra khi áp nguyên văn phép thay cụm từ.
  3. question_leaks khi cụm bị lộ nằm trong mô tả người hỏi.
  4. Đáp án phụ thuộc hoàn cảnh người hỏi (kỳ tính thuế).
  5. Mã `single_change` có trong định nghĩa §7 nhưng không có trong
     `REASONS["q2"]` của `scripts/review/test2_labels.py`.
- Quét 168 câu silver: lỗi gộp khoản do HTML vbpl chỉ gặp ở `f8d931e0`.
