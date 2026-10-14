# Execution Plan: Embed lớp A trên máy có GPU

Date: 2026-10-14

## Status

Blocked. Nhóm chọn `embed-phobert-cpu.md` ngày 14/10 vì máy không có GPU. Giữ plan này cho trường hợp sau này có GPU và muốn chạy đúng model của ADR 0004.

## Outcome

`data/derived/embed/asis/` trên máy chính chứa vector của **mọi** đơn vị lớp A trong
`data/derived/corpus/index.sqlite` (1.503.700 đơn vị, 1.484.106 lời văn khác nhau, đã tính header),
dùng đúng model của ADR 0004 §4, và `scripts/eval/verify_embed.py --layer asis` in `OK`.
Sau đó mới làm W2-12 (index dense, chạy thử B3, B4 trên dev).

## Context

- ADR 0004 §4: model dense là `AITeamVN/Vietnamese_Embedding` (họ bge-m3, 1024 chiều).
- `MASTER_RESEARCH_GUIDE.md` §7.7, K-09, việc W1-08: trên CPU 4 nhân của máy chính chỉ đạt
  1,1–1,2 lời văn/giây, tức khoảng 360 giờ (15 ngày) cho 1.484.106 lời văn, vượt ngưỡng 4 ngày. Giảm `max_seq_length` không
  giúp gì, vì 99,8% lời văn ngắn hơn 512 token (`runs/README.md`, dòng 11/10).
- Không được embed tập con mà benchmark chạm tới: tập đó được chọn theo gold, nên làm lộ đáp
  án cho B3, B4 và lệch so với bộ truy xuất từ vựng vốn tìm trên toàn kho (§7.8).
- `scripts/eval/embed_corpus.py`: chạy tiếp được sau khi bị ngắt, chặn nếu đổi cấu hình.
  Từ 14/10 script tự dùng CUDA khi có GPU (trước đó bị ép CPU).
- `scripts/eval/verify_embed.py`: kiểm kết quả mang về: đủ đơn vị, đủ vector, chuẩn hóa,
  đúng index, đúng model (embed lại một mẫu trên CPU, cosine ≥ 0,99).

## Scope

In scope:

- Embed lớp A (`--layer asis`, `--max-seq-length 512`) trên một máy có GPU NVIDIA.
- Mang kết quả về máy chính và kiểm.
- Ghi sổ chạy và chốt lại C1.

Out of scope:

- Lớp B (`--layer version`): B3, B4 chỉ đọc lớp A.
- Dựng Milvus hay index tìm kiếm (W2-12).
- Đổi model (việc đó cần amendment ADR 0004).

## Approach

Ký hiệu: **[Chính]** là máy hiện tại (WSL, không GPU), **[GPU]** là máy chạy.

### Bước 0 [Chính]: đưa code lên GitHub

Hai script và plan này phải có trên nhánh `feature/framework` ở remote:

```bash
git add scripts/eval/embed_corpus.py scripts/eval/verify_embed.py docs/plans/active/embed-gpu.md
git commit -m "feat(embed): chạy được trên GPU, script kiểm kết quả mang về"
git push
```

### Bước 1 [Chính → GPU]: chép index

`data/derived/` nằm trong `.gitignore`, nên index phải chép tay: USB, `scp`, hoặc Google Drive.
Chỉ cần **một file**, 3,7 GB (file `-wal` rỗng, `-shm` không cần):

```
data/derived/corpus/index.sqlite
sha256 b785909d1cdbcc80b48dbef375edd69fd7e18349fb21f45536619b91f7432467
```

Chép xong, trên [GPU] đặt file vào đúng `data/derived/corpus/index.sqlite` trong repo, rồi kiểm:

```bash
sha256sum data/derived/corpus/index.sqlite     # phải ra đúng chuỗi trên
```

### Bước 2 [GPU]: cài đặt

Yêu cầu: GPU NVIDIA từ 8 GB VRAM, khoảng 15 GB đĩa trống (index 3,7 GB, model 2,3 GB, vector
khoảng 2,6 GB), Python ≥ 3.10, có mạng để tải model từ Hugging Face lần đầu.
Máy chính dùng Python 3.12.3, torch 2.14.1, sentence-transformers 6.1.0.

```bash
git clone git@github.com:cmtri2005/graphrag-legal-thesis.git
cd graphrag-legal-thesis
git checkout feature/framework
python -m venv .venv && source .venv/bin/activate
# torch bản CUDA trước, theo lệnh ở https://pytorch.org/get-started/locally/ cho đúng driver
pip install -e ".[embed]"
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

Dòng cuối phải in `True` và tên GPU. Máy Windows: chạy trong WSL2 có CUDA, hoặc dùng PowerShell
với `.venv\Scripts\activate`; các lệnh Python bên dưới giữ nguyên.

### Bước 3 [GPU]: đo tốc độ trên 2.000 đơn vị

```bash
python scripts/eval/embed_corpus.py --layer asis --max-seq-length 512 --batch 64 \
    --limit 2000 --out /tmp/embed-test
```

- Dòng đầu phải là `device cuda:0`. Nếu là `device cpu` thì dừng, quay lại bước 2.
- Đọc `texts/s` ở dòng cuối. Thời gian ước tính = 1.484.106 / tốc độ.
  Ví dụ 100 lời văn/giây thì khoảng 4 giờ.
- Báo lỗi hết bộ nhớ GPU (`CUDA out of memory`): giảm `--batch` xuống 32 hoặc 16.
- Tốc độ dưới 20 lời văn/giây (tức hơn 17 giờ): dừng lại và báo nhóm trước khi chạy cả kho.

Xóa `/tmp/embed-test` sau khi đo. Thư mục này không phải kết quả.

### Bước 4 [GPU]: chạy cả kho

Chạy trong `tmux` hoặc `screen`, hoặc dùng `nohup`, để đóng terminal không làm dừng tiến trình:

```bash
nohup python scripts/eval/embed_corpus.py --layer asis --max-seq-length 512 --batch 64 \
    > embed-asis.log 2>&1 &
tail -f embed-asis.log
```

- Kết quả nằm ở `data/derived/embed/asis/`: file `texts.sqlite` và các file
  `shard-00000.npy`, `shard-00001.npy`, ..., mỗi shard 20.000 lời văn.
- Bị ngắt (mất điện, hết phiên): chạy lại **đúng lệnh trên**. Script tiếp tục từ shard cuối
  đã ghi; phần dở của shard đang chạy được tính lại, không quá 20.000 lời văn.
- Đổi `--max-seq-length` hay `--layer` giữa chừng thì script từ chối chạy. Đó là cố ý.
- Xong khi log in một dòng JSON có `"units": ...`, `"distinct_texts": ...`.

### Bước 5 [GPU]: kiểm nhanh trước khi chép về

```bash
python scripts/eval/verify_embed.py --layer asis --sample 0
```

Phải in `OK`. `--sample 0` bỏ qua bước embed lại trên CPU; bước đó làm ở máy chính.

### Bước 6 [GPU → Chính]: chép kết quả về

Chép **cả thư mục** `data/derived/embed/asis/` (khoảng 3 GB, gồm khoảng 75 shard) về đúng đường dẫn đó trên máy chính.
Kèm danh sách checksum để kiểm khi chép xong:

```bash
# [GPU]
cd data/derived/embed/asis && sha256sum * > ../asis.sha256
# [Chính], sau khi chép cả asis/ và asis.sha256
cd data/derived/embed/asis && sha256sum -c ../asis.sha256
```

### Bước 7 [Chính]: kiểm đầy đủ

```bash
.venv/bin/python scripts/eval/verify_embed.py --layer asis
```

Embed lại 100 đơn vị trên CPU (khoảng 2 phút) và so với vector mang về. Phải in `OK`.

### Bước 8 [Chính]: ghi lại

- Thêm một dòng vào sổ chạy `runs/README.md`: máy, GPU, `--batch`, tốc độ, tổng thời gian,
  số shard, kết quả `verify_embed.py`.
- Cập nhật C1 trong `MASTER_RESEARCH_GUIDE.md` §7.7 và tiến độ W1-08.
- Chuyển plan này sang `docs/plans/completed/`, rồi làm W2-12.

## Risks And Recovery

- **Hết phiên hoặc mất điện giữa chừng:** chạy lại đúng lệnh ở bước 4 (script có checkpoint).
- **Hết bộ nhớ GPU:** giảm `--batch`. Không cần xóa kết quả cũ, vì `--batch` không nằm trong
  cấu hình bị khóa và không đổi vector.
- **Chép nhầm index hoặc index đã đổi:** bước 1 kiểm sha256, và `verify_embed.py` báo
  `text here differs` nếu lời văn không khớp.
- **Kho được dựng lại ở W2-09.** Event đổi ngày 13/10 (`29b0886`) và `manifest.json` của kho
  phụ thuộc `provision_events.jsonl`, nên một số đơn vị lớp A có thể đổi. Vector được khóa theo
  sha256 của lời văn, nên phần lớn dùng lại được. Nhưng `embed_corpus.py` hiện chỉ chạy tiếp
  theo `rowid` trên **cùng** index, chưa có chế độ "chỉ embed lời văn còn thiếu" trên index mới.
  Khi dựng lại kho: chạy `verify_embed.py` với index mới để đếm phần thiếu, rồi thêm chế độ đó.
  Vài nghìn lời văn chạy trên CPU máy chính cũng được (1,1 lời văn/giây).
- **Hỏng hẳn:** xóa `data/derived/embed/asis/` trên [GPU] rồi chạy lại từ bước 4. Index và
  code không bị đụng tới.

## Progress

- [x] Sửa `embed_corpus.py` để tự dùng CUDA; viết `verify_embed.py`; chạy thử cả hai trên
      50 đơn vị ở máy chính (cosine CPU so với vector đã lưu: 1,0000) — 14/10
- [ ] Bước 0: commit, push
- [ ] Bước 1–2: chép index, cài đặt trên [GPU]
- [ ] Bước 3: đo tốc độ trên [GPU]
- [ ] Bước 4–5: chạy cả kho, kiểm nhanh
- [ ] Bước 6–7: chép về, kiểm đầy đủ
- [ ] Bước 8: sổ chạy, C1, W1-08

## Decisions

- 2026-10-14: C1 chốt lại: giữ model của ADR 0004, chạy một lần trên máy có GPU thay vì CPU
  máy chính. Không cần amendment ADR 0004, vì model và văn bản embed không đổi; chỉ đổi phần cứng.
- 2026-10-14: không embed tập con theo benchmark (lộ gold, §7.8).

## Validation

- Focused proof: `verify_embed.py --layer asis` in `OK` trên máy chính, gồm đủ 1.503.700 đơn
  vị và cosine ≥ 0,99 trên 100 mẫu embed lại bằng CPU.
- Integration or end-to-end proof: B3, B4 chạy được trên dev (W2-12).
- Repository-required checks: `pytest` không đổi kết quả.

## Result

(điền sau khi xong)
