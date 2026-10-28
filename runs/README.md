# Sổ chạy thực nghiệm

Mỗi thí nghiệm có một thư mục `runs/<mã thí nghiệm>/<split>/` (mã theo MASTER_RESEARCH_GUIDE §8.2).
Mỗi hệ để lại ba file:

| File | Ai viết | Nội dung |
|---|---|---|
| `<hệ>.jsonl` | `scripts/eval/run_vilextime.py` | Dự đoán, mỗi dòng release một dòng. Đây là bằng chứng và đắt để sinh lại, nên không sửa tay |
| `<hệ>.run.json` | runner, tự động | Mỗi lần gọi một bản ghi: spec, tham số, commit, hash của diff chưa commit, sha256 của release, manifest và prompt, model đã trả lời, số dòng. Chạy tiếp thì nối thêm bản ghi, chạy lại từ đầu thì bắt đầu danh sách mới |
| `<tên>.score.json` | `scripts/eval/score_vilextime.py --out` | Báo cáo theo chế độ `as_of` và nhóm. Với `--ci`, có thêm khoảng tin cậy và hiệu ghép cặp |

Quy tắc:

1. Mọi lựa chọn (cấu hình, prompt, model, `k`) chỉ được quyết trên `dev`.
2. Không chạy hệ nào trên `test` trước khi ADR 0005 được Accepted và commit. Mỗi cấu hình chạy trên
   `test` một lần, và mỗi lần đó có một dòng trong bảng dưới, ghi lý do.
3. Luôn truyền `--split`. Không dùng `--fast-retrieval` cho số được báo.
4. Chấm nhiều hệ trong một lệnh: scorer chỉ đọc `derived/versions.jsonl` (khoảng 1 GB) một lần, và
   với `--ci` thì so mỗi file với file đứng trước nó (ghép cặp theo lineage).

Ví dụ, E1 trên `dev`:

```bash
for s in b2ctx b7 b7v b7plus b7pp; do
  python scripts/eval/run_vilextime.py --system $s --no-dense --retrieval-only \
      --split dev --out runs/E1_ladder/dev/$s.jsonl
done
python scripts/eval/score_vilextime.py runs/E1_ladder/dev/{b2ctx,b7,b7v,b7plus,b7pp}.jsonl \
    --split dev --ci 2000 --out runs/E1_ladder/dev/ladder.score.json
```

## Nhật ký

| Ngày | Thí nghiệm | Split | Hệ | Commit | Mục đích | Kết quả tóm tắt | Ghi chú |
|---|---|---|---|---|---|---|---|
| 11/10/2026 | E0 | dev | probe (`--probes --ci 1000`) | `2213f44` + diff chưa commit | Kiểm scorer trước khi tin số | `giua_khoang`: oracle đạt trần mọi nhóm (Acc 1,000; TVER, VCR, `wrong_version` 0); `hedge` Acc 0,031 ở T2 nhưng Acc lỏng 1,000; `nearest` 0,708 ở T2 | `E0/probes_dev.score.json`. Probe trên test chạy lại ở W3-01 |
| 11/10/2026 | E0 | — | `build_versions.py --verify-pairs 200` trên 135 văn bản đích của T6 | như trên | Tier `propagated` so với `ValidityService` | 485 cặp (nút, ngày) khớp, kể cả mốc của nút cha. Dựng lại ra trùng 27.978/27.978 phiên bản đã công bố | `E0/build_versions_verify.txt`; đầu ra dựng lại để ở thư mục tạm, không ghi đè `data/derived` |
| 11/10/2026 | E0 | cả release | `scripts/check/check_tier_windows.py` | như trên | Cửa sổ trong index so với nguồn; tier để lại gì của gold | 1.033 phiên bản, 0 lệch. Dòng có đáp án ở T2, T3, T5: tier `document` còn để phiên bản khác lọt qua ở 100% dòng, tier `version` và `propagated` thì 0%. Dòng không có đáp án ở T6: `document` lộ việc bãi bỏ ở 0%, `version` 22,4% (bãi bỏ trực tiếp), `propagated` 100% | `E0/index_windows.json`. Cửa sổ là của KG, nên đây là kiểm index và bộ lọc, không kiểm KG |
| 11/10/2026 | E1 | dev | `b2ctx`, `b7`, `b7v`, `b7plus`, `b7pp` (từ vựng, chỉ truy xuất) | như trên | Kiểm thang 5 nấc trước khi khóa cấu hình | `giua_khoang`, 193 dòng có đáp án (119 lineage), TV-R@1: `b2ctx` 0,254 → `b7` 0,389 → `b7v` 0,321 → `b7plus` 0,513 → `b7pp` 0,513. Hiệu ghép cặp (KTC 95%): `b7` − `b2ctx` +0,135 [0,091; 0,182]; `b7plus` − `b7` +0,124 [0,067; 0,179]; `b7v` − `b7` âm. 38 dòng đã bị bãi bỏ: điều khoản đã hết hiệu lực còn lọt vào top-20 ở `b2ctx` 78,9%, `b7` 81,6%, `b7plus` 63,2%, `b7pp` 0% | `E1_ladder/dev/ladder.score.json` (cả 4 chế độ, `--ci 2000`), `confirm_dev.json` (XN1, XN3, XN4 chạy thử). Dev chỉ để kiểm đường ống, không dùng để kết luận. R@1 tính cả phiên bản đã hết hiệu lực, nên ở dòng đã bị bãi bỏ nó thưởng cho việc lấy phải điều khoản chết; đọc R@1 trên dòng có đáp án |
| 11/10/2026 | W1-08 | — | `AITeamVN/Vietnamese_Embedding` trên CPU 4 nhân (máy rảnh) | như trên | Đo tốc độ embed trước khi chạy cả corpus | 1.000 lời văn lớp A có header: trung vị 110 token, p99 350, chỉ 0,2% dài hơn 512. Tốc độ 1,1 đoạn/giây với `max_seq_length` 256, 1,2 với 512, tức khoảng 300 giờ (12,5 ngày) cho 1.247.953 lời văn. `dangvantuan/vietnamese-embedding` (PhoBERT-base): 3,5 đoạn/giây, khoảng 100 giờ | Vượt ngưỡng 4 ngày của K-09, nên cần nhóm chọn lại phương án (GPU một lần, model nhỏ, hoặc bỏ B3, B4). Script `scripts/eval/embed_corpus.py` đã chạy thử: tiếp tục được sau khi dừng, chặn khi đổi cấu hình |
| 19/10/2026 | W2-12 | dev | `b3` (dense, `dangvantuan/vietnamese-embedding`, chỉ truy xuất) so với `b2ctx` | `564b741` + diff chưa commit | Chạy thử truy xuất dày trước khi dùng cho B3, B4 | `giua_khoang`: R@1 `b3` 0,260 so với `b2ctx` 0,420; TV-R@1 0,126 so với 0,212; hiệu ghép cặp R@1 −0,160 [−0,25; −0,06]. Dense đơn lẻ kém BM25 rõ rệt | `W2-12_dense/dev/b3_vs_b2ctx.score.json`. Khoảng 7 giây/câu (quét hết 1,48 triệu vector). Dev chỉ để kiểm đường ống |
| 20/10/2026 | W2-12 (chạy lại) | dev | `b2ctx`, `b3` (chỉ truy xuất) | `2140f68` | Chạy lại sau khi dựng lại corpus và release ở bước 5 | `giua_khoang`, 186 dòng có đáp án: R@1 `b3` 0,253 so với `b2ctx` 0,409; TV-R@1 0,124 so với 0,215; hiệu ghép cặp R@1 −0,156 [−0,26; −0,05]. Kết luận như lần trước: dense đơn lẻ kém BM25 rõ | `W2-12_rerun/dev/b3_vs_b2ctx.score.json`. 21 mã không phân giải được đều là đơn vị câu lệnh sửa đổi (`asis:event:…`), không phải điều khoản. B3 1,8 câu/giây (lần trước khoảng 7 giây/câu). Số E1 ở trên vẫn là corpus cũ |
| 28/10/2026 | B2 | dev | `b1`, `b2ctx`, `b7`, `b7v`, `b7plus`, `b7pp`, `proposed` (từ vựng; sinh bằng `Qwen/Qwen3-4B-Instruct-2507` rev `cdbee75`, NF4, greedy, 512 token, Colab 2×T4) | `996f148` + diff chưa commit | Chạy thử sinh câu trả lời trên dev, bắt lỗi đường ống, đo thời gian | `giua_khoang`, 151 dòng/81 lineage. Acc: `b1` 0,000 (141/151 câu "không rõ") → `b2ctx` 0,351 → `b7` 0,583 → `b7v` 0,450 → `b7plus` 0,649 → `b7pp` 0,629 → `proposed` 0,656. TVER: `b2ctx` 0,622, `b7` 0,233, `b7plus` 0,073, `b7pp` 0,000, `proposed` 0,014. Đúng định dạng 97,4–100%, cắt cụt 0–3 câu/hệ. Khoảng 12–13,5 s/câu có truy xuất, 3,1 s/câu `b1`; tổng 3,3 giờ GPU | `B2_dev/dev/b2.score.json` (`--ci 2000`), `confirm.json` (8/9 XN, thiếu XN8 vì chưa có `b5`). Raw Colab ở `B2_dev/raw/`. Sửa hai lỗi đường ống trước khi chấm: Verifier chấm nút lệnh theo tier thay vì theo văn bản như bước mở rộng (`proposed` không nhập được); `confirm_vilextime.py` đọc release nội bộ 186 dòng thay vì bản công bố 151 dòng (thêm `--release`). 19 mã `asis:event` scorer không biết, 5 lần bị trích. Dev không dùng để kết luận |
