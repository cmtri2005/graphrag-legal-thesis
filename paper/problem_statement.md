<!--
Ghi chú cho nhóm tác giả (xoá trước khi nộp).
- Quy ước đánh dấu: [KT] = đã đối chiếu với tệp dữ liệu của repo ngày 02/10/2026;
  [CHƯA KT] = chưa kiểm chứng, không được trích nguyên văn khi chưa kiểm.
- Mọi số liệu truy vết ở bảng cuối mục (Bảng A). Số liệu lấy từ bản chụp vbpl.vn ngày 12/09/2026.
- "§N" giữ chỗ cho tham chiếu chéo tới các mục chưa viết.
-->

# 2. Phát biểu bài toán

## 2.1 Động cơ

Tạo sinh tăng cường truy xuất (RAG) [1] neo câu trả lời của mô hình ngôn ngữ vào các đoạn văn bản được truy xuất từ một kho tài liệu. Trong cách thiết kế thông thường, kho tài liệu được coi là tĩnh: một đoạn văn hoặc liên quan hoặc không liên quan đến câu hỏi, bất kể câu hỏi được đặt vào thời điểm nào [CHƯA KT: nhận định khái quát về RAG chuẩn, cần đối chiếu [1]–[3]]. Văn bản quy phạm pháp luật không thoả giả định này. Điều khoản liên tục được sửa đổi, bổ sung, thay thế và bãi bỏ, nên nội dung có hiệu lực vào ngày này có thể đã bị thay thế, hoặc chưa tồn tại, vào ngày khác.

Hệ quả là một hệ thống có thể trích nguyên văn một điều khoản, dẫn đúng số hiệu, nhưng vẫn trả lời sai, vì phiên bản được dựa vào không có hiệu lực tại ngày người dùng hỏi. Lỗi này được gọi là *ảo giác theo thời gian*. Nó khác với bịa đặt ở chỗ mọi chuỗi được trích đều có trong kho; lỗi nằm ở hiệu lực của bằng chứng tại mốc thời gian được hỏi, điều mà điểm liên quan của bộ truy xuất và độ trôi chảy của mô hình sinh đều không phản ánh được. Trong lĩnh vực pháp luật, một câu trả lời dựa trên quy định đã hết hiệu lực có thể dẫn người dùng đến hành vi trái quy định hiện hành, nên đây là lỗi cần được đo riêng chứ không gộp vào độ chính xác chung.

Lỗi này không phải trường hợp biên trong kho văn bản được nghiên cứu. Trên bản chụp Cơ sở dữ liệu quốc gia về văn bản pháp luật (vbpl.vn) ngày 12/09/2026, 39,2% số văn bản chịu tác động từ văn bản khác bị tác động bởi ít nhất hai văn bản, và 92,2% đơn vị pháp lý nằm ở độ sâu từ hai trở lên trong cây cấu trúc (Bảng A, dòng 1–2). Hiệu lực trong bối cảnh này vì vậy là thuộc tính của toàn bộ lịch sử sửa đổi và toàn bộ hệ thống phân cấp, không phải của một đoạn văn đứng riêng.

## 2.2 Định nghĩa hình thức

Gọi $\mathcal{D}$ là tập văn bản và $\mathcal{U}$ là tập đơn vị pháp lý (Phần, Chương, Mục, Điều, Khoản, Điểm). Mỗi đơn vị $u \in \mathcal{U}$ thuộc một văn bản $\mathrm{doc}(u) \in \mathcal{D}$ và có một đơn vị cấp trên trực tiếp $\pi(u) \in \mathcal{U} \cup \{\bot\}$ trên cây cấu trúc của văn bản. Mỗi đơn vị có một chuỗi phiên bản $V_u = (v_1, v_2, \ldots)$, trong đó phiên bản $v_i$ có nội dung $\mathrm{text}(v_i)$ và khoảng hiệu lực nửa mở $[s_i, e_i)$. Phiên bản của $u$ có hiệu lực tại thời điểm $t$ được xác định bởi

$$
\mathrm{snapshot}(u, t) =
\begin{cases}
v_i & \text{nếu } \exists\, v_i \in V_u : s_i \le t < e_i,\\
\bot & \text{nếu không tồn tại.}
\end{cases}
\tag{1}
$$

Các mốc $s_i, e_i$ không phải thuộc tính nội tại của $u$; chúng được quyết định bởi các văn bản tác động,

$$
\mathrm{Act}(u) = \{(a, \mathit{op}) \mid a \in \mathcal{D},\ \mathit{op} \in \{\text{sửa đổi}, \text{bổ sung}, \text{thay thế}, \text{bãi bỏ}\},\ a \xrightarrow{\mathit{op}} u\},
\tag{2}
$$

trong đó thời điểm có hiệu lực $\tau(a)$ của mỗi văn bản tác động $a$ mở một phiên bản mới hoặc đóng phiên bản hiện hành. Vì văn bản tác động có thể chính nó bị sửa đổi hay thay thế, $\mathrm{Act}$ phải được xét theo bao đóng bắc cầu. Hiệu lực còn được lan truyền xuống cây cấu trúc: một đơn vị chỉ có hiệu lực khi nó có phiên bản hiện hành và đơn vị cấp trên của nó cũng có hiệu lực,

$$
\mathrm{valid}(u, t) = \big[\mathrm{snapshot}(u, t) \ne \bot\big] \wedge \big[\pi(u) = \bot \ \vee\ \mathrm{valid}(\pi(u), t)\big].
\tag{3}
$$

**Đầu vào và đầu ra.** Đầu vào là cặp $(x, t)$, trong đó $x$ là câu hỏi bằng ngôn ngữ tự nhiên và $t$ là thời điểm truy vấn. Đầu ra là câu trả lời $a$ cùng tập đơn vị bằng chứng $E(x, t)$.

**Ràng buộc.** Bằng chứng phải thoả

$$
E(x, t) \subseteq \mathcal{U}_t, \qquad \mathcal{U}_t = \{u \in \mathcal{U} \mid \mathrm{valid}(u, t)\},
\tag{4}
$$

và $a$ phải được chống đỡ bởi các phiên bản $\mathrm{snapshot}(u, t)$ của những đơn vị trong $E(x, t)$. Truy vấn là cặp $(x, t)$ chứ không phải riêng $x$: cùng một câu hỏi tại hai thời điểm $t \ne t'$ có thể có tập bằng chứng và câu trả lời khác nhau. Khi không có đơn vị nào trong $\mathcal{U}_t$ trả lời được $x$, chẳng hạn vì điều khoản điều chỉnh đã bị bãi bỏ, đầu ra đúng là nêu rõ điều khoản không còn hiệu lực, không phải một câu trả lời lấy từ nội dung đã bị thay thế.

**Các loại lỗi.** Ràng buộc (4) tách hai cách thất bại, được đo riêng từng loại. Một trích dẫn là *hết hiệu lực* nếu nó nêu một đơn vị $u \notin \mathcal{U}_t$. Một trích dẫn là *sai phiên bản* nếu nó nêu một đơn vị $u \in \mathcal{U}_t$ nhưng trích một phiên bản $v \ne \mathrm{snapshot}(u, t)$. Loại thứ nhất phát hiện được chỉ từ các khoảng hiệu lực; loại thứ hai đòi hỏi hệ thống xác định được phiên bản, không chỉ đơn vị.

## 2.3 Vì sao bài toán khó

Khó khăn trước hết nằm ở biểu diễn, sau đó mới đến xếp hạng. Gọi biểu diễn là ánh xạ $\rho : \mathcal{U} \to \mathcal{R}$ quyết định hệ thống truy xuất quan sát được gì về mỗi đơn vị.

> **Định nghĩa 1 (Biểu diễn đủ).** Biểu diễn $\rho$ là *đủ* đối với ràng buộc hiệu lực nếu tồn tại hàm $g$ sao cho $\mathrm{valid}(u, t) = g(\rho(u), t)$ với mọi $u \in \mathcal{U}$ và mọi thời điểm $t$.

> **Mệnh đề 1.** Nếu tồn tại $u, u' \in \mathcal{U}$ và thời điểm $t$ sao cho $\rho(u) = \rho(u')$ nhưng $\mathrm{valid}(u, t) \ne \mathrm{valid}(u', t)$, thì $\rho$ không đủ.
>
> *Chứng minh.* Nếu tồn tại $g$ như vậy thì $\mathrm{valid}(u, t) = g(\rho(u), t) = g(\rho(u'), t) = \mathrm{valid}(u', t)$, mâu thuẫn. $\square$

Do đó, nếu biểu diễn không đủ, mọi bộ lọc hay bộ xếp hạng xây trên nó đều có trường hợp vi phạm (4), bất kể chất lượng của bộ truy xuất hay mô hình sinh. Từ (1)–(3), hiệu lực phụ thuộc vào ba loại thông tin nằm ngoài nội dung của đơn vị: **(I1)** chuỗi phiên bản và các khoảng hiệu lực, **(I2)** chuỗi đơn vị cấp trên, và **(I3)** các văn bản tác động cùng bao đóng bắc cầu của chúng. Biểu diễn thiếu bất kỳ loại nào đều chịu Mệnh đề 1.

Điều này không chỉ là khả năng lý thuyết. Phân tích ở cấp văn bản và đơn vị trên bản chụp ngày 12/09/2026 cho thấy:

- **Chỉ dùng nội dung thì không đủ (I1).** Có 8.210 nhóm điều khoản có nội dung chuẩn hoá trùng khớp, thuộc ít nhất hai văn bản, trong đó vừa có phiên bản còn hiệu lực vừa có phiên bản hết hiệu lực. Chọn ngẫu nhiên đều trong nhóm sai 47,5% số lần, nên với các nhóm này nội dung hầu như không mang tín hiệu nào về hiệu lực (Bảng A, dòng 3–4). *Cận dưới*: chỉ các bản trùng tuyệt đối sau chuẩn hoá được tính, các bản gần giống bị bỏ qua. Chỉ 271 trong 8.210 nhóm liên quan văn bản hợp nhất (Bảng A, dòng 5).
- **Siêu dữ liệu cấp văn bản không đủ (I1, I2).** Có 2.051 văn bản hết hiệu lực một phần, chứa 351.813 đơn vị (27,8% kho văn bản). Bộ lọc cấp văn bản hoặc phải nhận ít nhất 12.331 đơn vị đã biết là hết hiệu lực, hoặc phải loại 339.482 đơn vị không có căn cứ nào cho thấy đã hết hiệu lực (Bảng A, dòng 6–8). *Cận dưới* cho số đơn vị hết hiệu lực, vì chỉ các đơn vị đã xác định được trên cây cấu trúc mới được đếm.
- **Trạng thái riêng từng đơn vị không đủ (I2).** Có 14.157 đơn vị hết hiệu lực chỉ vì một đơn vị cấp trên bị bãi bỏ; không đơn vị nào trong số đó được nêu tên trong một ghi nhận bãi bỏ. Số này gấp khoảng 2,4 lần 6.001 đơn vị bị bãi bỏ trực tiếp (Bảng A, dòng 9–10). *Cận dưới*: chỉ 73,8% ghi nhận bãi bỏ ở cấp dưới văn bản được định vị chính xác trên cây (Bảng A, dòng 11, [CHƯA KT]).
- **Chỉ dùng quan hệ trực tiếp không đủ (I3).** Trên 1.000 văn bản chịu tác động được lấy mẫu, bao đóng bắc cầu của các văn bản tác động có kích thước trung vị 4, phân vị 90 là 68 và lớn nhất là 2.963 (Bảng A, dòng 12). Đây là *thống kê trên mẫu*; nó cho thấy chuỗi tác động nhiều bước tồn tại, chưa cho thấy mỗi bước đều làm đổi đáp án.

Các hướng tiếp cận hiện có xử lý được từng phần của bài toán. Truy xuất phẳng [1]–[3] chỉ dùng nội dung. RAG dựa trên đồ thị [4], [5] bổ sung quan hệ nhưng, theo mô tả của các công trình đó, gán cho mỗi thực thể một phiên bản duy nhất. Các phương pháp nhận biết phiên bản [14], [15] mô hình hoá sự tiến hoá của tài liệu, và theo hiểu biết của chúng tôi chưa đánh giá riêng phép lan truyền trong (3) như một thành phần độc lập [CHƯA KT: các mô tả về [4], [5], [14], [15] cần đối chiếu với bài gốc]. §N đối chiếu các hướng này với I1–I3.

## 2.4 Câu hỏi nghiên cứu

Bài toán được nghiên cứu qua ba câu hỏi, mỗi câu gắn với một đại lượng đo được. TVER là tỉ lệ câu trả lời có trích dẫn hết hiệu lực; VCR là tỉ lệ trích dẫn đúng đơn vị nhưng sai phiên bản; TCS là tỉ lệ trả lời đúng ở cả hai mốc của một cặp tương phản. Định nghĩa đầy đủ ở §N và trong `scripts/eval/score_vilextime.py`.

- **RQ1.** Mô hình ngôn ngữ lớn và các quy trình RAG chuẩn dựa vào phiên bản không có hiệu lực tại mốc được hỏi thường xuyên đến mức nào? *Đo bằng* TVER và VCR của mô hình sinh không truy xuất, và của truy xuất phẳng thưa, dày và lai. [CHƯA KT: báo cáo phản biện 29/09/2026 (`docs/reports/JUDGE_DATASET.md`, mục C3) ghi TVER của mô hình không truy xuất chưa tính được khi trích dẫn ở dạng chữ; chỉ số này phải được sửa trước khi dùng để trả lời RQ1.]
- **RQ2.** Đồ thị pháp luật có kiểu và có phiên bản có giảm lỗi này so với truy xuất phẳng và so với truy xuất đồ thị bỏ qua thời gian không? *Đo bằng* mức chênh của TVER, VCR và TCS giữa các hệ thống, kèm khoảng tin cậy bootstrap theo chuỗi điều khoản.
- **RQ3.** Nếu có giảm lỗi, mức giảm đến từ chính đồ thị hay chỉ do lọc theo thời gian? Trả lời cần các đối chứng dùng cùng bộ truy xuất, mô hình sinh và lời nhắc, chỉ thay đổi điều mà biểu diễn ghi lại: không gì cả, ngày của văn bản, khoảng hiệu lực riêng của đơn vị, và khoảng được lan truyền qua mọi đơn vị cấp trên theo (3). *Đo bằng* TVER, VCR và TV-Recall@1 trên bốn mức biểu diễn đó.

Các giả thuyết có thể bác bỏ, suy ra từ những quan sát ở mục 2.3, được nêu ở §N.

## 2.5 Phạm vi, giả định và những điều nằm ngoài bài toán

Bài toán được giới hạn như sau để các khẳng định kiểm chứng được.

1. **Kho văn bản.** Văn bản quy phạm pháp luật cấp trung ương của Việt Nam, lấy từ một bản chụp duy nhất của vbpl.vn (12/09/2026). Câu hỏi bằng tiếng Việt. Khả năng khái quát sang hệ thống pháp luật hay nguồn dữ liệu khác không được khẳng định.
2. **Hiệu lực hình thức.** Hiệu lực được đánh giá theo nghĩa *de jure*, suy ra từ ngày có hiệu lực, sửa đổi và bãi bỏ đã công bố. Diễn giải pháp lý nằm ngoài bài toán: điều khoản chuyển tiếp giữ quy định cũ cho một số quan hệ, xung đột giữa các văn bản khác cấp, và việc áp dụng hồi tố vượt ra ngoài ngày có hiệu lực do văn bản tác động nêu đều không được mô hình hoá.
3. **Đáp án chuẩn.** Đáp án chuẩn là nội dung của $\mathrm{snapshot}(u, t)$, tính từ chính các chuỗi phiên bản mà hệ thống dựa trên đồ thị sử dụng. Lỗi khi dựng chuỗi do đó không hiện ra trên bộ đánh giá, và kết quả phải được đọc cùng một đợt kiểm định độc lập (§N). Đây là một giới hạn đã biết của thiết kế (`docs/reports/JUDGE_DATASET.md`, mục N1).
4. **Trạng thái tại một thời điểm.** Trạng thái hiệu lực của văn bản và các ghi nhận bãi bỏ được lấy tại ngày chụp dữ liệu; thời điểm cụ thể một đơn vị bị bãi bỏ không phải lúc nào cũng có trong siêu dữ liệu.
5. **Không phải tư vấn pháp lý.** Hệ thống trả về nội dung điều khoản và trích dẫn; nó không đánh giá điều khoản được áp dụng thế nào cho một vụ việc cụ thể.

Với các giả định này, bài toán là thiết kế và đánh giá một quy trình truy xuất và sinh có bằng chứng thoả (4) với mọi truy vấn $(x, t)$, và xác định, bằng so sánh có kiểm soát, thành phần nào của biểu diễn chịu trách nhiệm cho mức thay đổi quan sát được.

---

**Bảng A. Truy vết số liệu.** Tất cả số liệu lấy từ bản chụp vbpl.vn ngày 12/09/2026. "Tệp" là `data/representation_benchmark.json` trừ khi ghi khác; tái lập bằng `python scripts/explore/compare_representations.py`.

| # | Số liệu | Khoá trong tệp | Trạng thái |
|---|---|---|---|
| 1 | 39,2% văn bản chịu tác động bị ≥ 2 văn bản tác động (trên 15.394 văn bản) | `M1.amenders_per_document.share_with_2_or_more` = 0,3921; `M1.amended_documents` | [KT] |
| 2 | 92,2% đơn vị ở độ sâu ≥ 2 | `M1.tree_depth_distribution`: 1 − 99.066 / 1.264.594 = 0,9217 (tính lại từ phân bố) | [KT] |
| 3 | 8.210 nhóm trùng nội dung, hiệu lực trái ngược; 19.154 phiên bản | `M2a.2026-09-12.conflicting_groups`, `dated_versions_in_them` | [KT] |
| 4 | Sai kỳ vọng 47,5% khi chọn đều | `M2a.2026-09-12.expected_error_if_flat_picks_uniformly` = 0,4749 | [KT] |
| 5 | 271 nhóm liên quan văn bản hợp nhất | `M2a.2026-09-12.conflicting_groups_involving_consolidated_doc` | [KT] |
| 6 | 2.051 văn bản hết hiệu lực một phần; 351.813 đơn vị; 27,8% | `M2c.partially_expired_documents`, `provisions_inside_them`, `share_of_all_provisions` = 0,2782 | [KT] |
| 7 | 12.331 đơn vị đã hết hiệu lực trong các văn bản đó | `M2c.repealed_units_by_document_status.HHL1P` | [KT] |
| 8 | 339.482 đơn vị không có căn cứ hết hiệu lực | 351.813 − 12.331 (suy ra) | [KT] |
| 9 | 14.157 đơn vị mất hiệu lực chỉ do đơn vị cấp trên | `M2b.descendants_invalid_only_via_ancestor` | [KT] |
| 10 | 6.001 đơn vị bị bãi bỏ trực tiếp; tỉ số 2,4 | `M2b.distinct_repealed_nodes`; 14.157 / 6.001 = 2,36 | [KT] |
| 11 | 73,8% ghi nhận bãi bỏ định vị chính xác (22.992 / 31.175) | `docs/graph_justification.md` §4.4; không có trong tệp JSON | [CHƯA KT] |
| 12 | Bao đóng bắc cầu: trung vị 4, p90 68, lớn nhất 2.963 (n = 1.000) | `M3.Q3_transitive_amendment_lineage.lineage_size` | [KT] |

## Tài liệu tham khảo

[1] P. Lewis et al., "Retrieval-augmented generation for knowledge-intensive NLP tasks," in *Proc. NeurIPS*, 2020.

[2] S. Robertson and H. Zaragoza, "The probabilistic relevance framework: BM25 and beyond," *Foundations and Trends in Information Retrieval*, vol. 3, no. 4, pp. 333–389, 2009.

[3] V. Karpukhin et al., "Dense passage retrieval for open-domain question answering," in *Proc. EMNLP*, 2020.

[4] D. Edge et al., "From local to global: A graph RAG approach to query-focused summarization," arXiv:2404.16130, 2024.

[5] Z. Guo et al., "LightRAG: Simple and fast retrieval-augmented generation," in *Findings of EMNLP*, 2025.

[14] H. de Martim, "An ontology-driven graph RAG for legal norms: A hierarchical, temporal, and deterministic approach," in *Legal Knowledge and Information Systems (JURIX)*, IOS Press, 2025.

[15] D. Huwiler, K. Stockinger, and J. Fürst, "VersionRAG: Version-aware retrieval-augmented generation for evolving documents," arXiv:2510.08109, 2025.

[CHƯA KT: thông tin xuất bản và danh sách tác giả của cả bảy mục trên được sao từ `docs/graph_justification.md`, trong đó ghi chú rằng một số mục được viết theo trí nhớ. Cần đối chiếu với nguồn gốc trước khi nộp.]
