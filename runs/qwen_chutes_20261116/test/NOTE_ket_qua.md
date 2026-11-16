# Qwen3.8-27B (Chutes, TEE, fp8) trên bộ cuối, 16/11/2026
ADR 0006 amendment 16/11 (b). Thăm dò, hậu nghiệm, ngoài Holm. 15 hệ × 2 lần × 361 dòng; chấm trên 318 dòng của lát `all`. Chạy: `run_test.sh` (có thử lại khi Chutes timeout 90 s: r1 6 lần, r2 5 lần; dòng đã xong không gọi lại). Chưa qua evidence-gate lúc ghi.

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
- proposed2 − b4 (F1, F3): Accuracy +0,324 [+0,272; +0,376]; sai phiên bản −0,306 [−0,353; −0,258].
- proposed2 − b5 (F2): Accuracy +0,333 [+0,281; +0,385].
- proposed2 − b7pp (F7, T6): T6 Accuracy +0,043 [0; 0,109] (cả hai lần); toàn `all` +0,009 [−0,013; +0,035].
- b7plus − bvdate: Accuracy +0,085 [+0,041; +0,132]; sai phiên bản −0,038 [−0,064; −0,015]; TCS +0,126 [+0,062; +0,194] (r2 tương tự).
- proposed2 − lightrag: Accuracy +0,119 [+0,050; +0,187]; sai phiên bản −0,279; TCS +0,299.
F4–F6 chỉ truy xuất, không phụ thuộc generator, giữ nguyên số G4.
Lệch với dev: trên dev `b7plus − bvdate` chứa 0; trên bộ cuối loại 0. Dev chỉ 151 dòng.
