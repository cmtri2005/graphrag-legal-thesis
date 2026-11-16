# Qwen3.8-27B (Chutes, TEE, fp8) trên bộ cuối, 16/11/2026
ADR 0006 amendment 16/11 (b). Thăm dò, hậu nghiệm, ngoài Holm. 15 hệ × 2 lần × 361 dòng; chấm trên 318 dòng của lát `all`. Chạy: `run_test.sh`. Mỗi lần chạy bị dừng một lần lúc khoảng 14:05 vì Chutes timeout 90 s (r1 ở `b5`, r2 ở `b6`); khởi động lại 14:09 bằng script đã thêm vòng thử lại (commit sau, trong ec5da75), sau đó thử lại thêm r1 6 lần, r2 5 lần; dòng đã xong không gọi lại. `head.txt`, `started_utc.txt` ghi theo lần khởi động lại. Log `*.log` bị gitignore. Chỉ `b1` có câu bị cắt (`finish_reason` length): 9 dòng r1, 6 dòng r2. Evidence-gate 16/11: số khớp từng byte; lỗi nhãn F7 đã sửa dưới đây.

Accuracy / sai phiên bản / TCS, `all`, r1 | r2:
| Hệ | Accuracy | Sai phiên bản | TCS |
|---|---|---|---|
| b4 | 0,355 / 0,358 | 0,313 / 0,309 | 0,102 |
| b5 | 0,346 / 0,349 | 0,321 / 0,313 | 0,094 / 0,102 |
| b7 | 0,635 | 0,072 / 0,068 | 0,575 / 0,567 |
| b7plus | 0,676 / 0,679 | 0,004 | 0,661 |
| b7pp | 0,670 / 0,673 | 0,004 | 0,654 / 0,669 |
| bvnone | 0,327 / 0,321 | 0,340 / 0,351 | 0,079 |
| bvdate | 0,591 / 0,597 | 0,042 / 0,034 | 0,535 |
| lightrag | 0,560 | 0,287 / 0,283 | 0,339 |
| proposed2 | 0,679 / 0,689 | 0,008 / 0,004 | 0,638 / 0,654 |
| oracle | 0,884 / 0,877 | 0 | 0,874 / 0,858 |
| oracle_now | 0,418 / 0,421 | 0,449 / 0,457 | 0 |

Hiệu ghép cặp (r1; r2 gần như trùng), thư mục `pairs/`:
- r2 của ba cặp còn lại: proposed2 − b4 +0,330, proposed2 − b5 +0,340, proposed2 − lightrag +0,129 (Accuracy).
- proposed2 − b4 (F1, F3): Accuracy +0,324 [+0,272; +0,376]; sai phiên bản −0,306 [−0,353; −0,258].
- proposed2 − b5 (F2): Accuracy +0,333 [+0,281; +0,385].
- proposed2 − b7pp, **F7 đúng lát `t6_unanswerable`** (23 dòng; `confirm_vilextime.py --family final`, evidence-gate): Accuracy +0,087 [0; 0,217], p = 0,238 cả hai lần: không đủ bằng chứng, như GPT-4o mini. T6 gộp (46 dòng, 23 có đáp án): +0,043 [0; 0,109]. Toàn `all`: +0,009 [−0,013; +0,035].
- b7plus − bvdate: Accuracy +0,085 [+0,041; +0,132]; sai phiên bản −0,038 [−0,064; −0,015]; TCS +0,126 [+0,062; +0,194] ; r2: Accuracy +0,082 [+0,041; +0,127], sai phiên bản −0,030 [−0,055; −0,011], TCS +0,126 [+0,067; +0,190].
- proposed2 − lightrag: Accuracy +0,119 [+0,050; +0,187]; sai phiên bản −0,279; TCS +0,299.
F4–F6 chỉ truy xuất, không phụ thuộc generator, giữ nguyên số G4.
Lệch với dev: trên dev `b7plus − bvdate` chứa 0; trên bộ cuối loại 0. Dev chỉ 151 dòng.

Giới hạn phải khai kèm mọi số Qwen (amendment 16/11 (b)): Chutes phục vụ bản FP8, **không ghim revision, không bảo đảm seed**; dev vLLM chạy BF16, revision `37561816`. Mức lệch Chutes–vLLM (≤ 0,02 Accuracy) đo trên dev, `b4` và `b7plus`, r1, 151 dòng, không đo trên bộ cuối. Trùng nguyên văn giữa r1 và r2: 90–98% với mọi hệ trừ `b1` (124/361); dev vLLM 97,1%. Câu "dev chứa 0" nói về dev vLLM BF16.
Cách viết (evidence-gate): "với hai generator đã thử"; F1–F3 loại 0 ở cả hai lần và cùng dấu với GPT-4o mini; F4–F6 không dùng generator; F7 không đủ bằng chứng ở cả hai. `b7plus − bvdate` cận dưới +0,041 vượt mức lệch 0,02: viết là phân tích hậu nghiệm, ngoài Holm. Chưa báo ở đây: MRR, TV-R@1, cặp oracle, `ranh_gioi`.

Bổ sung 16/11 (sau gate):
- MRR, TV-R@1: chỉ phụ thuộc truy xuất. Prompt dùng lại của G4 nên trùng G4: `b4` MRR 0,445 / TV-R@1 0,164; `b7` 0,493 / 0,242; `b7plus` 0,456 / 0,336; `proposed2` 0,453 / 0,336; `bvnone`, `bvdate` 0,447 / 0,173.
- Cặp oracle (Qwen): `oracle` 0,884 / 0,877, `oracle_now` 0,418 / 0,421 (GPT-4o mini: 0,956, 0,456). Trần của Qwen thấp hơn GPT-4o mini khoảng 0,07.
- `ranh_gioi`: prompt bộ cuối chỉ gồm dòng `giua_khoang` (như G4); lát `ranh_gioi` có 0 dòng. Không có số Qwen cho `ranh_gioi` (B5 chưa chạy).
