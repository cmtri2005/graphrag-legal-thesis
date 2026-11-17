# Evidence-gate: điền khóa luận 17/11/2026

Phạm vi: `git diff fecae0b..3a16e5c -- docs/thesis`; phân tích `51123d4` (`runs/gap_analysis_20261117/`, `docs/paper/NGUYEN_NHAN_3_VAN_DE.md`); A1 `2df3340`, `94953d1`. Agent `evidence-gate` (AI, không phải duyệt của người). Phiên chính ghi lại bản tóm tắt này, vì agent không được ghi file.

## Lượt 1: FAIL

- 70 mục số: 67 PASS, 3 FAIL. Cả 3 FAIL cùng một gốc: số 92 ở §6.6.3 là hiệu ròng (304 − 212). Số dòng `oracle` đúng mà `proposed2` sai là 96 ở lần 1 và 98 ở lần 2.
- Tái lập trùng từng byte:
  - `funnel.py` r1/r2;
  - `version_recheck_score.py` (9/9 [0,7008; 1,0]; 2/24 [0,0232; 0,2585]);
  - 4 file điểm LightRAG; 6 file cặp Qwen;
  - `confirm_vilextime` trên tập con 105 lineage có gold đã sửa (r1);
  - κ 0,932 và AC1 0,935 của luật sư; NMT 80/81.
- Số LightRAG và Qwen nay đã qua gate.

### Lỗi lớn
- **F1:** 92 → 96 (98 ở lần 2). Các nhóm là 41 + 37 + 15 + 3.
- **F2:** hai phiếu chấm khác nhau ở 6/33 dòng, không phải 5 (thêm dòng 100 `b4` từ đúng sang sai phiên bản). Nếu thay 33 nhãn mới thì độ khớp là 92/100. Dòng `proposed2` từng ghi "cờ nhầm" thì phiếu mới chấm là sai phiên bản.

### Lỗi vừa
- **F3:** câu "LightRAG xấp xỉ RAG phẳng" sai, vì lần 2 KTC loại 0.
- **F4:** câu "Model lớn hơn thu hẹp" quy nguyên nhân cho kích thước model.
- **F5:** "đúng 5/12 vì…": nguyên nhân chưa đo.
- **F6:** "chủ yếu là bài toán tìm đúng điều khoản": sai, vì 37/96 dòng có gold trong prompt.

### Lỗi nhỏ
- m1: thêm phép đếm điều/khoản cha vào artifact; mẫu số đúng là 3/41.
- m2: 15 dòng T6, không phải 16.
- m3: báo thêm r2 cho phép so Qwen với LightRAG.
- m4: báo `lightrag − b5`, `b7plus − lightrag`.
- m5: mức lệch Chutes–vLLM ghi theo từng hệ.
- m6: chênh trần 0,07–0,08.
- m7: "hiệu quan sát".
- m8: ghi "đợt chạy G4 hai lần" thay "lần chạy duy nhất".
- m9: thêm kết quả kiểm lại +2/21 ngày 12/11.
- m10: sửa 5 câu lỗi thời ở chương 1, 7.
- m11: thêm comment nguồn.
- m12: Qwen không có file gate riêng.
- m13: M2 → "A2 dùng thay một phần".
- m14: ghi tên người chấm và việc họ đã thấy độ khớp.
- m15: LightRAG khác embedding, truy vấn có ngày, lần 2 bị dừng giữa chừng.
- NGUYEN_NHAN mục 4: bỏ câu "thấp hơn 0–4 điểm".

### Rò rỉ và overfitting
- Mọi phép so mới đều có nhãn thăm dò hoặc hậu nghiệm.
- Các amendment đều được commit trước khi sinh câu trả lời trên bộ cuối.
- Không trộn số dev với số bộ cuối, không trộn số GPT với số Qwen.

## Đã sửa (phiên chính, 17/11)

- **Đã sửa:** F1–F6; m1 (`funnel.py` thêm `+co_cha`, chạy lại r1/r2: 3/41 ở cả hai lần); m2–m11, m13–m15; NGUYEN_NHAN §1.
- **Chưa làm:** m12, vì không có file gate cũ để thêm.
- Chờ gate chạy lại trên phần đã sửa.
