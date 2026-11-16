# NHÁP — Amendment gộp cho ADR 0006 (PLAN_PAPER_GAP mục 7)

**16/11: CMT bỏ reranker** (hết quota, tập trung việc chính). Mọi chỗ về reranker đã gỡ khỏi nháp; xem mục 10.

Trạng thái: **NHÁP 16/11/2026, chưa duyệt.** Chưa chép vào `docs/decisions/0006-*.md`. Chỉ chép sau khi CMT duyệt (dự kiến M1 22/11) và **trước** khi Qwen chạm bộ cuối. Chỗ `[CMT]` là quyết định còn mở; chỗ `[ĐIỀN]` điền bằng số đo thật trước khi duyệt, không điền sau khi đã thấy bộ cuối.

---

## Amendment 2026-11-__: generator mở (Qwen) và các phép thăm dò khác trên bộ cuối, sau khi đã thấy kết quả bộ cuối

Accepted __/11/2026, [CMT] duyệt trong hội thoại / commit, **trước** khi bất kỳ hệ nào dưới đây chạy trên bộ cuối. NMT chưa có xác nhận riêng trong repo [kiểm lại]. Không sửa phần nào ở trên.

### 1. Đã thấy gì
- Toàn bộ G4 (hai lần chạy), hậu nghiệm 13/11 (`runs/posthoc_g4_20261113/`), `bvnone`, `bvdate`, `lightrag` bằng GPT-4o mini trên bộ cuối.
- Gold mù người của 81 lineage (NMT, 15/11) và F1–F7 trên 103 lineage có gold người (`runs/gold_final_subset_20261115/`). NMT đọc xong sau khi bộ cuối đã được chạy.
- Dev: Qwen3.8-27B, 15 hệ × 2 lần (`runs/qwen_gen_20261115/dev/`, evidence-gate PASS 16/11).
- **Chưa thấy:** mọi dự đoán Qwen trên bộ cuối.

### 2. Hệ thêm
- **Qwen:** `Qwen/Qwen3.8-27B` rev `37561816e66b5b9153b1b64c10968c18c1e6f4a0`, vLLM 0.33.0, nhiệt độ 0, `max_tokens` 1024, `seed` 20261109, không thinking, hai lần chạy. Chạy lại **đúng prompt đã khóa** của 15 hệ (`b1`…`b7pp`, `oracle`, `oracle_now`, `proposed2`, `bvnone`, `bvdate`, `lightrag`; prompt khớp sha256 với lần GPT). Không đổi prompt hay cấu hình hệ.
- **B3 (chọn một trong hai đáp án):** `[CMT]` giữ hoặc bỏ; nếu giữ, chạy trên dev trước, model GPT-4o mini và Qwen, không dùng họ Claude hay DeepSeek (ADR 0004 §3).
- **`ranh_gioi`:** truy xuất cả thang (miễn phí); sinh bằng Qwen; bảng phụ.
- **Lát câu hỏi do người viết (C2):** [CMT chốt có làm không và ai viết; nếu không làm thì bỏ dòng này].

### 3. Phạm vi
Tất cả là **thăm dò, ngoài Holm, không có phán quyết**. Không đổi P (`proposed2`), F1–F7, phán quyết đã báo, scorer, gold, prompt của các hệ đã khóa.

### 4. Phép so (báo cả hai lần chạy)
- Qwen: F1–F5 như ADR §3 (hiệu ghép cặp, KTC bootstrap theo cụm lineage, B = 10.000); `b7plus − bvdate`; `proposed2 − lightrag`; cặp oracle.
- Chỉ số: Accuracy, `wrong_version`, TCS, MRR, TV-R@1.
- Hai lần chạy Qwen cho hai KTC gần như trùng; báo cả hai, không coi là hai mẫu độc lập (trùng nguyên văn 97,1% trên dev).

### 5. Cách đọc đã khai trước

| Thí nghiệm | Nếu | Thì viết |
|---|---|---|
| Qwen, F1–F5 | Cùng dấu, KTC loại 0 ở cả hai lần | "Kết luận không phụ thuộc generator" |
| Qwen, F1–F5 | Có hiệu đổi dấu hoặc KTC chứa 0 | Nêu đúng hiệu đó; khẳng định tương ứng chỉ còn cho GPT-4o mini |
| Qwen, `b7plus − bvdate` | KTC chứa 0 ở cả hai lần | "Với model lớn không thấy khác biệt lớn hơn độ rộng KTC giữa lọc cứng và để model tự chọn theo ngày." Sửa số chính thứ ba của abstract (0,245 là của GPT-4o mini) |
| Qwen, `b7plus − bvdate` | Loại 0 về phía dương ở cả hai lần | "Lọc cứng còn giá trị riêng với model lớn" |
| Qwen, `proposed2 − lightrag` | Loại 0 dương ở cả hai lần | Như amendment 15/11 |
| Gold mù | Dưới ngưỡng B6 | Báo tỷ lệ lỗi; chấm lại phần đó theo gold người; thu hẹp khẳng định. Không sửa kho trước hạn nộp |

### 6. Kết quả dev lúc duyệt (đã thấy)
Qwen, `all`, dev 151 dòng, r1 / r2 (KTC ghép cặp 95%, 10.000 lần):

| Hệ | Accuracy | Sai phiên bản | TCS |
|---|---|---|---|
| `bvnone` | 0,437 / 0,430 | 0,388 / 0,376 | 0,167 |
| `bvdate` | 0,715 / 0,709 | 0,047 | 0,611 |
| `b7plus` | 0,715 | 0,012 | 0,750 |
| `proposed2` | 0,762 | 0,012 | 0,722 |
| `lightrag` | 0,583 | 0,388 | 0,278 |

| Hiệu (Qwen, dev) | Accuracy | Sai phiên bản | TCS |
|---|---|---|---|
| `b7plus − bvdate` r1 | 0,000 [−0,087; 0,089] | −0,035 [−0,096; 0,015] | +0,139 [−0,033; 0,314] |
| `b7plus − bvdate` r2 | +0,007 [−0,080; 0,094] | −0,035 [−0,096; 0,015] | +0,139 [−0,033; 0,314] |
| `proposed2 − lightrag` (cả hai lần) | +0,179 [0,074; 0,280] | −0,376 [−0,476; −0,275] | +0,444 [0,243; 0,641] |

Đọc: trên dev, Qwen với `bvdate` **ngang** `b7plus` ở cả ba chỉ số (KTC chứa 0), khác GPT-4o mini (+0,272 / +0,245, loại 0). Nên có khả năng cao dòng 3 của bảng §5 sẽ rơi vào nhánh "chứa 0".

### 7. Giới hạn phải khai kèm
- Qwen được định nghĩa **sau** khi đã thấy G4: phân tích hậu nghiệm, không phải kiểm định khai trước.
- `bvnone`, `bvdate` Qwen chạy trong một phiên vLLM khác 13 hệ kia (cấu hình giống; r1 và r2 vẫn lệch 1 dòng ở dev).
- Dev là tập con 151 dòng; bộ cuối khác kích thước. Không suy từ dev ra bộ cuối.
- Ba chỗ không ngang hàng của LightRAG (amendment 15/11) vẫn áp dụng, kèm Qwen.
- `bvnone − bvdate`, `bvdate − b7pp`, `lightrag − bvnone` trong `all.score.json` là cặp ghép tự động, không phải phép so đã thiết kế; không trích.

### 8. Đường chạy
`runs/qwen_gen_20261115/` (tạo `run_test.sh` cạnh `run_dev.sh`; cần cờ `--allow-test` hoặc `final_run.py`, chỉ sau commit duyệt). Chi phí: 0 USD API (Colab A100).

### 9. Việc cho CMT chốt trước khi chép vào ADR
1. Bộ cuối Qwen: chạy `bvdate`, `bvnone`, `lightrag` luôn (đề xuất: có, vì cùng prompt đã khóa).
3. Giữ hay bỏ B3, và C2.
4. Khóa luận đã đọc `b7plus − bvdate` = 0,245 như số chính; cần ghi rõ "GPT-4o mini" cạnh số đó.

### 10. Reranker: bỏ (CMT, 16/11/2026)
Không đưa reranker lên bộ cuối. Lý do: hết quota, ưu tiên các việc chính. Đã có trên dev, **chỉ truy xuất** (chưa sinh): `AITeamVN/Vietnamese_Reranker` nâng MRR `b4` 0,536 → 0,696; TV-R@1 `b7plus − b4` 0,199 → 0,265 (`runs/rerank_pool_dev_20261115/`). Phần Qwen dev cho 4 ô đã dựng sẵn nhưng chưa chạy (`runs/qwen_gen_rr_20261116/`). Paper phải ghi trong giới hạn: "chưa so sánh với retriever có reranker trên bộ cuối; trên dev, khoảng cách truy xuất giữa lọc và không lọc không co lại khi thêm reranker".
