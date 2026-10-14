# Execution Plan: Embed lớp A bằng `dangvantuan/vietnamese-embedding` trên CPU máy chính

Date: 2026-10-14

## Status

Active. Chờ nhóm duyệt amendment ADR 0004 §4 (bước 0). Phương án thay thế dùng GPU vẫn giữ ở
`embed-gpu.md`.

## Outcome

`data/derived/embed/asis-vietnamese-embedding/` chứa vector của **mọi** đơn vị lớp A trong
`data/derived/corpus/index.sqlite`: 1.503.700 đơn vị, 1.484.106 lời văn khác nhau (đã tính
header). Lệnh `verify_embed.py --layer asis --model dangvantuan/vietnamese-embedding` in `OK`.
Sau đó mới làm W2-12: viết truy xuất dense, chạy thử B3, B4 trên dev.

## Context

- ADR 0004 §4 chọn `AITeamVN/Vietnamese_Embedding`. Trên CPU 4 nhân của máy chính, model này
  chạy 1,1–1,2 lời văn/giây, tức khoảng **15 ngày** cho 1.484.106 lời văn. Ước tính cũ (12,5 ngày)
  tính theo 1,25 triệu lời văn chưa gắn header nên thấp hơn thực tế.
- Máy chính không có GPU. Nhóm chọn ngày 14/10: đổi sang model nhỏ, chạy trên CPU.
- Theo `MASTER_RESEARCH_GUIDE.md` §7.7, K-09 và quyết định B3, bảng chính chỉ dùng truy xuất từ
  vựng (`--no-dense`). Dense chỉ cần cho B3, B4 và một dòng kiểm độ bền. Các hệ này đều đọc lớp
  A, nên **không cần embed lớp B**.
- `src/vilexgraph/framework/retrieve.py` chưa có truy xuất dense (báo `NotImplementedError`).
  Phần này viết ở W2-12, không thuộc plan này.

### Số đo ngày 14/10 trên máy chính

Đo trên mẫu ngẫu nhiên 600 đơn vị lớp A (seed 0); tốc độ đo trên 300 đơn vị.

| Chỉ số | Giá trị |
|---|---|
| Tách từ bằng pyvi | khoảng 1.250 lời văn/giây, không đáng kể so với embed |
| Embed (CPU 4 nhân, `--max-seq-length 256`, batch 16) | 5,5–6,3 lời văn/giây |
| Thời gian ước tính cho 1.484.106 lời văn | **khoảng 65–75 giờ (2,7–3,1 ngày)**, dưới ngưỡng 4 ngày của K-09 |
| Độ dài sau tách từ (token PhoBERT) | trung vị 80, p95 186, p99 310 |
| Lời văn dài hơn 256 token (bị cắt đuôi) | 1,5% |
| Dung lượng vector | 1.484.106 × 768 chiều × fp16, khoảng 2,3 GB |

## Ưu và nhược điểm

So với giữ `AITeamVN/Vietnamese_Embedding` (chạy GPU theo `embed-gpu.md`, hoặc CPU 15 ngày):

**Ưu điểm**

1. **Kịp hạn trên máy sẵn có.** Khoảng 3 ngày; bắt đầu 15/10 thì xong khoảng 18/10, trước hạn
   W2-12 (24/10) và W3-04 (29/10).
2. **Không cần máy khác.** Không phải chép index 3,7 GB đi rồi chép vector về, không phụ thuộc
   Kaggle hay Colab.
3. **Model nhẹ.** 135 triệu tham số, 768 chiều: tốn ít RAM (máy chỉ có 7 GB), vector nhẹ hơn
   (2,3 GB so với khoảng 3 GB), và truy vấn lúc chạy B3, B4 cũng nhanh hơn.
4. **An toàn khi bị ngắt.** Script có checkpoint theo shard; chạy lại đúng lệnh là tiếp tục.
   Đã chạy thử, cosine giữa lần embed lại và vector đã lưu là 1,0000.

**Nhược điểm**

1. **Chất lượng truy xuất có thể thấp hơn rõ.** Model được huấn luyện cho độ giống nhau giữa
   hai câu (NLI, STS), không phải cho cặp câu hỏi và đoạn văn, và tác giả không công bố số nào về
   truy xuất. `AITeamVN` tự công bố Acc@1 0,727 trên Legal Zalo 2021. Chưa đo trên ViLexTime.
2. **Rủi ro bị phản biện là baseline yếu.** B3, B4 là baseline để so với hệ đề xuất. Hội đồng có
   thể nói hệ đề xuất chỉ thắng một baseline dense yếu. Khóa luận phải nêu đây là giới hạn và lý
   do chọn (phần cứng, thời hạn).
3. **Lệch ADR 0004 §4.** Phải ghi amendment và commit **trước** mọi lần chạy trên test (ADR 0005).
4. **Cắt ở 256 token.** PhoBERT chỉ có 258 vị trí, nên 1,5% lời văn mất phần đuôi. Model của ADR
   cho phép tới 2.048 token.
5. **Phải tách từ ở cả hai phía.** Câu hỏi lúc truy vấn cũng phải qua `pyvi`, đúng như lời văn
   lúc embed (`embed_corpus.prepare`). Quên bước này thì B3, B4 sai mà không báo lỗi.
6. **Máy chính bận khoảng 3 ngày.** Embed dùng cả 4 nhân. Trong thời gian đó, các việc nặng CPU
   (E1 trên test, dựng lại kho) sẽ chậm. Các việc gọi API LLM (W1-09, W1-15) và việc gán nhãn
   không bị ảnh hưởng.

## Scope

In scope:

- Embed lớp A (`--layer asis`, `--max-seq-length 256`) bằng `dangvantuan/vietnamese-embedding`
  trên máy chính.
- Kiểm kết quả, ghi sổ chạy, ghi amendment ADR 0004 §4.

Out of scope:

- Lớp B (`--layer version`).
- Code truy xuất dense, Milvus, chạy B3, B4 (W2-12).
- Embed bằng `AITeamVN` (giữ ở `embed-gpu.md` nếu sau này có GPU).

## Approach

### Bước 0: amendment ADR 0004 §4 (nhóm duyệt)

Thêm cuối `docs/decisions/0004-framework-truy-xuat-va-sinh.md`:

> **Amendment 2026-10-14 (§4):** model dense đổi sang `dangvantuan/vietnamese-embedding`
> (PhoBERT-base, 768 chiều), đầu vào tách từ bằng `pyvi` ở cả lời văn và câu hỏi,
> `max_seq_length` 256. Lý do: máy duy nhất của nhóm là CPU 4 nhân; model cũ cần khoảng 15 ngày,
> model mới khoảng 3 ngày (đo 14/10, `runs/README.md`). Hệ quả: B3, B4 là baseline dense yếu hơn
> mức có thể đạt; bảng chính không đổi vì chỉ dùng truy xuất từ vựng.

### Bước 1: cài đặt

```bash
.venv/bin/pip install -e ".[embed]"     # đã thêm pyvi vào nhóm embed
```

Máy chính đã cài và đã có model trong cache (`~/.cache/huggingface/hub`). Đĩa còn trống khoảng
820 GB.

### Bước 2: giữ máy thức trong khoảng 3 ngày

Máy chạy WSL2 trên Windows:

- Windows Settings → Power: **Sleep = Never** khi cắm sạc.
- Tạm dừng Windows Update trong 1 tuần.
- Chạy trong `tmux`, và để một cửa sổ terminal WSL luôn mở để WSL không tự tắt.

### Bước 3: chạy

```bash
tmux new -s embed
cd ~/UIT_Thesis/graphrag-legal-thesis
nice -n 10 .venv/bin/python scripts/eval/embed_corpus.py --layer asis --max-seq-length 256 \
    --model dangvantuan/vietnamese-embedding 2>&1 | tee -a embed-phobert.log
# thoát tmux mà tiến trình vẫn chạy: Ctrl-b rồi d; vào lại: tmux attach -t embed
```

- `nice -n 10` để máy vẫn dùng được cho việc khác, dù embed sẽ chậm đi một chút.
- Mỗi shard 20.000 lời văn mất khoảng 1 giờ. Log in một dòng sau mỗi shard.
- Bị ngắt: chạy lại **đúng lệnh trên**. Script tiếp tục từ shard cuối đã ghi.
- Đổi `--max-seq-length`, `--model` hay `--layer` giữa chừng thì script từ chối. Đó là cố ý.

Xem tiến độ bất kỳ lúc nào:

```bash
sqlite3 data/derived/embed/asis-vietnamese-embedding/texts.sqlite \
  "SELECT COUNT(*), ROUND(100.0*COUNT(*)/1484106, 1) || '%' FROM text"
```

### Bước 4: kiểm

```bash
.venv/bin/python scripts/eval/verify_embed.py --layer asis --model dangvantuan/vietnamese-embedding
```

Phải in `OK`. Lệnh này kiểm: đủ 1.503.700 đơn vị, mọi đơn vị có vector, vector chuẩn hóa và
không có NaN, đúng index, và 100 mẫu embed lại có cosine ≥ 0,99.

### Bước 5: ghi lại

- Thêm một dòng vào `runs/README.md`: model, `max_seq_length`, tốc độ, tổng thời gian, số shard,
  kết quả `verify_embed.py`.
- Cập nhật C1 trong `MASTER_RESEARCH_GUIDE.md` §7.7 (và bảng §0.6, §13.3 nếu có ghi C1), cùng
  tiến độ W1-08.
- Chuyển plan này sang `docs/plans/completed/`; ghi `embed-gpu.md` là không dùng.

## Risks And Recovery

- **Mất điện, Windows tự khởi động lại, WSL tắt:** chạy lại bước 3. Mất tối đa một shard
  (khoảng 1 giờ).
- **Chạy chậm hơn ước tính** (máy bận việc khác): đến 20/10 mà chưa xong thì xem lại. Ngưỡng cứng
  là 23/10, để còn W2-12 trước 24/10.
- **Kho được dựng lại ở W2-09:** event đổi ngày 13/10 (`29b0886`), nên một số đơn vị lớp A có thể
  đổi lời văn. Vector được khóa theo sha256 của lời văn, nên phần lớn dùng lại được. Nhưng
  `embed_corpus.py` chỉ chạy tiếp theo `rowid` trên **cùng** index, chưa có chế độ "chỉ embed lời
  văn còn thiếu" trên index mới. Khi dựng lại kho: chạy `verify_embed.py` với index mới để đếm phần
  thiếu, rồi thêm chế độ đó. Vài nghìn lời văn chỉ mất khoảng một giờ trên CPU.
- **Kết quả B3, B4 quá yếu** (ví dụ thua BM25 rõ trên dev ở W2-12): ghi là giới hạn. Nếu kịp và có
  GPU thì chạy thêm `embed-gpu.md`; hai thư mục vector tách riêng, không ghi đè nhau.
- **Hỏng hẳn:** xóa `data/derived/embed/asis-vietnamese-embedding/` rồi chạy lại bước 3. Index
  và code không bị đụng tới.

## Progress

- [x] Thêm `--model` vào `embed_corpus.py` (tách từ `pyvi`, chặn `max_seq_length` > 256, mỗi
      model một thư mục riêng); `verify_embed.py` đọc model từ meta; thêm `pyvi` vào nhóm `embed`.
      Chạy thử 300 đơn vị: 6,3 lời văn/giây, cosine 1,0000; 513 test qua — 14/10
- [x] Đo tốc độ, độ dài, tỷ lệ bị cắt; đếm 1.484.106 lời văn khác nhau — 14/10
- [ ] Bước 0: nhóm duyệt amendment ADR 0004 §4
- [ ] Bước 1–3: cài đặt, giữ máy thức, chạy cả kho
- [ ] Bước 4: `verify_embed.py` in `OK`
- [ ] Bước 5: sổ chạy, C1, W1-08

## Decisions

- 2026-10-14: dùng `dangvantuan/vietnamese-embedding` trên CPU máy chính thay cho `AITeamVN` (nhóm
  chọn sau khi xem ưu và nhược điểm). Cần amendment ADR 0004 §4.
- 2026-10-14: `max_seq_length` 256, mức tối đa của PhoBERT.
- 2026-10-14: không embed tập con theo benchmark (lộ gold, §7.8); không embed lớp B.

## Validation

- Focused proof: `verify_embed.py --layer asis --model dangvantuan/vietnamese-embedding` in `OK`.
- Integration or end-to-end proof: B3, B4 chạy được trên dev (W2-12).
- Repository-required checks: `pytest` qua.

## Result

(điền sau khi xong)
