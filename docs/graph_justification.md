# Phân tích động cơ và lựa chọn biểu diễn đồ thị có phiên bản cho hỏi đáp pháp luật theo mốc thời gian

## Tóm tắt

Trong bài toán hỏi đáp pháp luật theo mốc thời gian, một câu trả lời chỉ đúng khi mọi bằng chứng được trích dẫn có hiệu lực tại thời điểm được hỏi. Mục này lập luận rằng yêu cầu đó quyết định cách biểu diễn tri thức pháp luật. Trước hết, chúng tôi đưa ra một tiêu chí hình thức cho tính *đủ* của một biểu diễn đối với ràng buộc hiệu lực, và chỉ ra rằng hiệu lực của một đơn vị pháp lý phụ thuộc vào ba loại thông tin nằm ngoài nội dung của nó: chuỗi phiên bản, chuỗi đơn vị cấp trên và các văn bản tác động. Tiếp theo, phân tích trên 22.550 văn bản và 1.264.594 đơn vị điều khoản từ Cơ sở dữ liệu quốc gia về văn bản pháp luật cho thấy các biểu diễn đơn giản hơn không đủ ở quy mô đáng kể: 8.210 nhóm điều khoản có nội dung trùng khớp nhưng hiệu lực trái ngược; 27,8% đơn vị điều khoản thuộc văn bản hết hiệu lực một phần; 14.157 đơn vị mất hiệu lực chỉ do đơn vị cấp trên bị bãi bỏ; và chuỗi tác động bắc cầu lên một văn bản có thể gồm tới 2.963 văn bản. Từ đó, chúng tôi lựa chọn đồ thị có kiểu và có phiên bản kết hợp truy xuất lai, đồng thời nêu các giả thuyết có thể bác bỏ bằng thực nghiệm.

---

## 1. Đặt vấn đề

Phần lớn các hệ thống tạo sinh tăng cường truy xuất (RAG) [1] mặc nhiên coi cơ sở tri thức là tĩnh: mỗi đoạn văn bản là một đơn vị độc lập, được xếp hạng theo độ tương đồng từ vựng [2] hoặc ngữ nghĩa [3] với câu hỏi. Các biến thể dựa trên đồ thị như GraphRAG [4] và LightRAG [5] bổ sung cấu trúc và quan hệ, nhưng mỗi thực thể vẫn chỉ tồn tại dưới một phiên bản duy nhất. Với văn bản quy phạm pháp luật, giả định này không đúng: điều khoản liên tục được sửa đổi, bổ sung, thay thế hoặc bãi bỏ. Hệ quả là hiện tượng *ảo giác theo thời gian*: hệ thống trích dẫn đúng số hiệu điều luật nhưng dựa trên phiên bản không còn hiệu lực.

Cách biểu diễn tri thức quyết định những ràng buộc nào hệ thống truy xuất có thể bảo đảm. Nếu biểu diễn không chứa thông tin cần thiết để xác định hiệu lực, thì không bộ xếp hạng hay mô hình sinh nào khôi phục được thông tin đó. Vì vậy, mục này trả lời hai câu hỏi:

- **(Q1)** Về mặt hình thức, một biểu diễn phải chứa những thông tin gì để ràng buộc hiệu lực có thể được kiểm tra?
- **(Q2)** Trên dữ liệu thực, các biểu diễn đơn giản hơn có "gần đủ" hay không, tức các trường hợp thất bại có hiếm đến mức có thể bỏ qua?

Mục 2 phát biểu bài toán. Mục 3 trả lời Q1 bằng một tiêu chí hình thức. Mục 4 trả lời Q2 bằng bốn quan sát trên kho văn bản. Mục 5 đối chiếu với các hướng tiếp cận hiện có. Mục 6 trình bày biểu diễn được lựa chọn. Mục 7 nêu các giả thuyết kiểm chứng, và Mục 8 thảo luận giới hạn.

---

## 2. Phát biểu bài toán

Gọi $\mathcal{D}$ là tập văn bản và $\mathcal{U}$ là tập đơn vị pháp lý (Phần, Chương, Mục, Điều, Khoản, Điểm). Mỗi đơn vị $u \in \mathcal{U}$ thuộc một văn bản $\mathrm{doc}(u) \in \mathcal{D}$ và có một đơn vị cấp trên trực tiếp $\pi(u) \in \mathcal{U} \cup \{\bot\}$ trên cây cấu trúc của văn bản. Mỗi đơn vị có một chuỗi phiên bản $V_u = (v_1, v_2, \ldots)$, trong đó phiên bản $v_i$ có nội dung $\mathrm{text}(v_i)$ và khoảng hiệu lực nửa mở $[s_i, e_i)$.

**Phiên bản tại một thời điểm.** Phiên bản của $u$ có hiệu lực tại thời điểm $t$ là

$$
\mathrm{snapshot}(u, t) =
\begin{cases}
v_i & \text{nếu } \exists\, v_i \in V_u : s_i \le t < e_i,\\
\bot & \text{nếu không tồn tại.}
\end{cases}
\tag{1}
$$

**Nguồn gốc của khoảng hiệu lực.** Các mốc $s_i, e_i$ không phải thuộc tính nội tại của $u$. Chúng được xác định bởi tập thao tác tác động lên $u$:

$$
\mathrm{Act}(u) = \{(a, \mathit{op}) \mid a \in \mathcal{D},\ \mathit{op} \in \{\text{sửa đổi}, \text{bổ sung}, \text{thay thế}, \text{bãi bỏ}\},\ a \xrightarrow{\mathit{op}} u\}.
\tag{2}
$$

Thời điểm có hiệu lực $\tau(a)$ của văn bản tác động $a$ mở một phiên bản mới hoặc đóng phiên bản hiện hành. Văn bản tác động có thể chính nó cũng đã bị sửa đổi hay thay thế, nên $\mathrm{Act}$ cần được xét theo bao đóng bắc cầu.

**Hiệu lực lan truyền trên cây cấu trúc.** Một đơn vị chỉ có hiệu lực khi bản thân nó có phiên bản hiện hành và đơn vị cấp trên của nó cũng có hiệu lực:

$$
\mathrm{valid}(u, t) = \big[\mathrm{snapshot}(u, t) \ne \bot\big] \wedge \big[\pi(u) = \bot \ \vee\ \mathrm{valid}(\pi(u), t)\big].
\tag{3}
$$

**Bài toán.** Cho câu hỏi $x$ và mốc thời gian $t$, hệ thống trả về câu trả lời $a$ và tập bằng chứng $E(x, t)$ thoả mãn

$$
E(x, t) \subseteq \mathcal{U}_t, \qquad \mathcal{U}_t = \{u \in \mathcal{U} \mid \mathrm{valid}(u, t)\}.
\tag{4}
$$

Khác với hỏi đáp pháp luật thông thường, truy vấn ở đây là cặp $(x, t)$: cùng một câu hỏi $x$ với hai mốc $t \ne t'$ có thể có hai tập bằng chứng khác nhau.

---

## 3. Tiêu chí lựa chọn biểu diễn

Gọi *biểu diễn* là một ánh xạ $\rho : \mathcal{U} \to \mathcal{R}$, cho biết hệ thống truy xuất quan sát được gì về mỗi đơn vị.

> **Định nghĩa 1 (Biểu diễn đủ).** Biểu diễn $\rho$ là *đủ* đối với ràng buộc hiệu lực nếu tồn tại hàm $g$ sao cho $\mathrm{valid}(u, t) = g(\rho(u), t)$ với mọi $u \in \mathcal{U}$ và mọi thời điểm $t$.

> **Mệnh đề 1.** Nếu tồn tại $u, u' \in \mathcal{U}$ và thời điểm $t$ sao cho $\rho(u) = \rho(u')$ nhưng $\mathrm{valid}(u, t) \ne \mathrm{valid}(u', t)$, thì $\rho$ không đủ.
>
> *Chứng minh.* Giả sử tồn tại $g$ thoả Định nghĩa 1. Khi đó $\mathrm{valid}(u, t) = g(\rho(u), t) = g(\rho(u'), t) = \mathrm{valid}(u', t)$, mâu thuẫn với giả thiết. $\square$

Hệ quả của Mệnh đề 1 là: nếu biểu diễn không đủ, thì mọi bộ lọc hay bộ xếp hạng xây dựng trên biểu diễn đó đều có trường hợp vi phạm (4). Nguyên nhân nằm ở biểu diễn, không nằm ở năng lực của mô hình truy xuất hay mô hình sinh.

Từ (1)–(3), $\mathrm{valid}(u, t)$ phụ thuộc vào ba loại thông tin:

- **(I1) Chuỗi phiên bản và khoảng hiệu lực** $V_u$ — theo (1).
- **(I2) Chuỗi đơn vị cấp trên** $\pi(u), \pi(\pi(u)), \ldots$ — theo vế đệ quy của (3).
- **(I3) Các văn bản tác động và bao đóng bắc cầu của chúng** — theo (2).

I1 là thuộc tính gắn với từng đơn vị, còn I2 và I3 là *quan hệ* giữa các đơn vị và văn bản. Một biểu diễn chứa đồng thời I1–I3 gồm các nút mang khoảng thời gian, cạnh phân cấp và cạnh có kiểu giữa các văn bản; về bản chất đó là một đồ thị có kiểu và có phiên bản. Lập luận này ở mức mô hình dữ liệu và không phụ thuộc vào cách mã hoá vật lý của đồ thị.

Tuy nhiên, tiêu chí trên chỉ cho biết một biểu diễn đơn giản hơn *có thể* thất bại. Nếu các trường hợp thất bại hiếm trên dữ liệu thực, một biểu diễn đơn giản hơn vẫn có thể là lựa chọn hợp lý. Mục 4 định lượng điều này.

---

## 4. Phân tích trên kho văn bản

### 4.1. Dữ liệu

Chúng tôi phân tích bản chụp Cơ sở dữ liệu quốc gia về văn bản pháp luật (vbpl.vn) ngày 12/09/2026. Mỗi văn bản được phân tích thành cây cấu trúc; quan hệ giữa các văn bản được lấy từ siêu dữ liệu do cổng công bố. Các quan hệ trùng lặp theo bộ (văn bản nguồn, văn bản đích, loại quan hệ) được hợp nhất. Bảng 1 tóm tắt đặc trưng cấu trúc của kho văn bản.

**Bảng 1.** Đặc trưng cấu trúc của kho văn bản.

| Đại lượng | Giá trị |
|---|---:|
| Số văn bản | 22.550 |
| Số đơn vị điều khoản | 1.264.594 |
| Số quan hệ cấp trên – cấp dưới | 1.165.528 |
| Số quan hệ giữa các văn bản (13 loại) | 128.289 |
| Trong đó: quan hệ tác động (sửa đổi, bổ sung, thay thế, bãi bỏ, …) | 42.303 |
| Tỉ lệ đơn vị nằm ở độ sâu từ 2 trở lên | 92,2% |
| Số văn bản chịu tác động từ văn bản khác | 15.394 |
| Tỉ lệ văn bản chịu tác động từ ít nhất 2 văn bản | 39,2% |

Cấu trúc phân cấp và các quan hệ tác động đan xen là đặc trưng phổ biến của dữ liệu chứ không phải trường hợp biên. Các quan sát dưới đây đối chiếu từng biểu diễn đơn giản hơn với Định nghĩa 1.

### 4.2. Quan sát 1: Nội dung không xác định được hiệu lực

Xét biểu diễn chỉ gồm nội dung, $\rho_{\text{text}}(u) = \mathrm{text}(\mathrm{snapshot}(u, \cdot))$. Đây là biểu diễn của truy xuất phẳng dựa trên BM25 [2] hoặc bộ mã hoá dày [3]. Theo Mệnh đề 1, chỉ cần hai đơn vị có nội dung trùng khớp nhưng hiệu lực khác nhau là $\rho_{\text{text}}$ không đủ.

**Ví dụ 1.** Điều 1 của Nghị định số 41/2025/NĐ-CP (có hiệu lực từ 01/03/2025 đến 24/07/2026) và Điều 1 của Nghị định số 297/2026/NĐ-CP (thay thế văn bản trước, có hiệu lực từ 24/07/2026) có cùng nội dung: *"Bộ Dân tộc và Tôn giáo là cơ quan của Chính phủ thực hiện chức năng quản lý nhà nước về các ngành, lĩnh vực: Công tác dân tộc; tín ngưỡng, tôn giáo […]"*. Tại $t$ = 12/09/2026, chỉ điều khoản thứ hai có hiệu lực. Bộ mã hoá là hàm tất định của nội dung, nên hai điều khoản nhận cùng một điểm tương đồng với mọi câu hỏi; không hàm xếp hạng nào dựa trên nội dung ưu tiên được điều khoản còn hiệu lực.

**Phương pháp đo.** Chúng tôi gom các phiên bản có độ dài từ 100 ký tự trở lên theo nội dung đã chuẩn hoá (gộp khoảng trắng, không phân biệt hoa thường), và giữ các nhóm xuất hiện ở ít nhất hai văn bản (31.136 nhóm, 69.930 phiên bản). Gọi $\mathcal{C}_t$ là tập nhóm có đồng thời phiên bản còn và hết hiệu lực tại $t$. Nếu hệ thống chọn ngẫu nhiên đều một phiên bản trong nhóm, tỉ lệ sai kỳ vọng là

$$
\varepsilon(t) = \frac{\sum_{g \in \mathcal{C}_t} \big|\{v \in g : \neg\,\mathrm{valid}(v, t)\}\big|}{\sum_{g \in \mathcal{C}_t} |g|}.
\tag{5}
$$

**Bảng 2.** Nhóm điều khoản trùng nội dung nhưng hiệu lực trái ngược.

| Mốc $t$ | $\lvert\mathcal{C}_t\rvert$ | Số phiên bản trong $\mathcal{C}_t$ | $\varepsilon(t)$ | Nhóm có văn bản hợp nhất |
|---|---:|---:|---:|---:|
| 12/09/2026 | 8.210 | 19.154 | 47,5% | 271 |
| 01/01/2020 | 5.404 | 13.155 | 50,6% | 209 |

Chỉ 271 trong 8.210 nhóm có văn bản hợp nhất. Như vậy, hiện tượng này chủ yếu không do quá trình hợp nhất văn bản sinh ra, mà do nội dung được kế thừa nguyên văn giữa văn bản gốc, văn bản sửa đổi và văn bản thay thế. Tỉ lệ sai xấp xỉ 50% cho thấy, trong các nhóm này, nội dung gần như không mang tín hiệu nào về hiệu lực.

**Phạm vi.** Quan sát 1 bác bỏ các biểu diễn chỉ gồm nội dung. Nó *không* bác bỏ việc lọc theo siêu dữ liệu cấp văn bản: trong Ví dụ 1, ngày hiệu lực của hai nghị định đủ để phân biệt hai điều khoản. Giới hạn của cách lọc này được xét ở Quan sát 2.

### 4.3. Quan sát 2: Siêu dữ liệu cấp văn bản không xác định được hiệu lực của điều khoản

Xét biểu diễn bổ sung siêu dữ liệu hiệu lực của văn bản chứa đơn vị, $\rho_{\text{doc}}(u) = \big(\mathrm{text}(u), \mathrm{meta}(\mathrm{doc}(u))\big)$, trong đó quyết định hiệu lực chỉ dựa trên $\mathrm{meta}(\mathrm{doc}(u))$. Mọi đơn vị trong cùng một văn bản do đó nhận cùng một quyết định. Biểu diễn này không đủ khi một văn bản chứa đồng thời đơn vị còn và hết hiệu lực.

**Bảng 3.** Phân bố đơn vị đã xác định là hết hiệu lực theo trạng thái của văn bản chứa chúng (tại 12/09/2026).

| Trạng thái văn bản | Số văn bản | Số đơn vị trong các văn bản này | Số đơn vị đã xác định hết hiệu lực |
|---|---:|---:|---:|
| Hết hiệu lực một phần | 2.051 | 351.813 (27,8%) | 12.331 |
| Còn hiệu lực | 7.745 | — | 1.911 |
| Hết hiệu lực toàn bộ | 12.206 | — | 5.916 |

*Ghi chú:* "đơn vị đã xác định hết hiệu lực" gồm các đơn vị bị bãi bỏ trực tiếp đã định vị được trên cây và toàn bộ đơn vị cấp dưới của chúng (20.158 đơn vị; xem Quan sát 3).

Bảng 3 đặt bộ lọc cấp văn bản trước một thế lưỡng nan với 2.051 văn bản hết hiệu lực một phần. Nếu giữ lại các văn bản này, bộ lọc chấp nhận ít nhất 12.331 đơn vị đã hết hiệu lực. Nếu loại bỏ, nó loại 339.482 đơn vị không có căn cứ nào cho thấy đã hết hiệu lực. Ngoài ra, 1.911 đơn vị đã hết hiệu lực nằm trong văn bản có trạng thái "còn hiệu lực" và bị chấp nhận trong cả hai lựa chọn. Như vậy, 27,8% đơn vị trong kho văn bản nằm trong vùng mà siêu dữ liệu cấp văn bản không quyết định được hiệu lực.

### 4.4. Quan sát 3: Hiệu lực phụ thuộc vào đơn vị cấp trên

Xét biểu diễn lưu trạng thái hiệu lực riêng của từng đơn vị, $\rho_{\text{local}}(u)$, không kèm quan hệ cấp trên – cấp dưới. Theo (3), biểu diễn này không đủ nếu có đơn vị mất hiệu lực chỉ do đơn vị cấp trên bị bãi bỏ.

Cổng dữ liệu công bố 31.175 ghi nhận hết hiệu lực ở cấp dưới văn bản. Trong đó, 22.992 ghi nhận (73,8%) được định vị chính xác trên cây cấu trúc, ứng với 6.001 đơn vị phân biệt (Bảng 4).

**Bảng 4.** Đơn vị bị bãi bỏ trực tiếp, theo cấp.

| Cấp | Điều | Khoản | Điểm | Chương | Mục | Phần | Tiểu mục | Tổng |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Số đơn vị | 2.835 | 2.198 | 843 | 82 | 37 | 5 | 1 | 6.001 |

Dưới 6.001 đơn vị này có **14.157 đơn vị** không được nêu tên trong bất kỳ ghi nhận bãi bỏ nào, nhưng hết hiệu lực vì một đơn vị cấp trên đã bị bãi bỏ. Số đơn vị mất hiệu lực gián tiếp gấp 2,4 lần số đơn vị bị bãi bỏ trực tiếp. Một biểu diễn đánh giá hiệu lực độc lập cho từng đơn vị sẽ coi toàn bộ 14.157 đơn vị này là còn hiệu lực.

### 4.5. Quan sát 4: Tác động giữa các văn bản có tính bắc cầu

Xét biểu diễn chỉ lưu quan hệ tác động trực tiếp hoặc không lưu quan hệ. Theo (2), biểu diễn này không đủ khi văn bản tác động bản thân nó cũng chịu tác động từ văn bản khác.

Trong 15.394 văn bản chịu tác động, số văn bản tác động trực tiếp lên mỗi văn bản có trung vị 1, phân vị 99 là 26 và lớn nhất là 259. Trên mẫu ngẫu nhiên 1.000 văn bản chịu tác động, bao đóng bắc cầu theo quan hệ tác động có kích thước trung vị 4, phân vị 90 là 68 và lớn nhất là 2.963 văn bản.

**Phạm vi.** Quan sát 4 cho thấy chuỗi tác động nhiều bước tồn tại và có quy mô không tầm thường. Nó chưa cho thấy mỗi bước trong chuỗi đều làm thay đổi đáp án; mức ảnh hưởng thực tế được kiểm chứng bằng thực nghiệm ở Mục 7.

### 4.6. Tổng hợp

**Bảng 5.** Tổng hợp các quan sát.

| Quan sát | Biểu diễn không đủ | Quy mô trên kho văn bản | Thiết lập đối chứng tương ứng |
|---|---|---|---|
| 1 | Chỉ nội dung | 8.210 nhóm; $\varepsilon$ = 47,5% | B2–B4 |
| 2 | Nội dung + siêu dữ liệu cấp văn bản | 351.813 đơn vị (27,8%) không quyết định được | B7 |
| 3 | Trạng thái riêng từng đơn vị | 14.157 đơn vị mất hiệu lực gián tiếp | A4 |
| 4 | Không có quan hệ bắc cầu | Bao đóng tới 2.963 văn bản | B5, A2 |

---

## 5. Đối chiếu với các hướng tiếp cận hiện có

**Truy xuất phẳng.** Kiến trúc RAG tiêu chuẩn [1] chia văn bản thành các đoạn độc lập và xếp hạng theo BM25 [2], biểu diễn dày [3], hoặc kết hợp cả hai. Cách tiếp cận này mạnh về đối sánh ngữ nghĩa nhưng thuộc loại $\rho_{\text{text}}$, nên chịu Quan sát 1. Việc gắn thêm ngày hiệu lực của văn bản vào mỗi đoạn là thực hành phổ biến; nó thuộc loại $\rho_{\text{doc}}$ và chịu Quan sát 2.

**Truy xuất phân cấp theo ngữ nghĩa.** RAPTOR [6] gom cụm và tóm tắt đệ quy các đoạn văn bản thành cây nhiều mức. Cây này được xây dựng theo độ tương đồng ngữ nghĩa chứ không theo cấu trúc pháp điển, nên không cung cấp quan hệ $\pi$ trong (3), cũng như không có quan hệ tác động hay khoảng hiệu lực.

**Đồ thị tri thức phi thời gian.** Đồ thị tri thức biểu diễn thực thể thành nút và quan hệ có kiểu thành cạnh [7]. GraphRAG [4] và LightRAG [5] dựng đồ thị bằng trích xuất thực thể – quan hệ và truy xuất theo cộng đồng hoặc láng giềng. Trong miền pháp lý, đồ thị trích dẫn giữa các điều luật đã được dùng để cải thiện truy xuất [8]. Tại Việt Nam, các công trình [9], [10] xây dựng đồ thị bảo toàn cấu trúc Văn bản – Điều – Khoản – Điểm và liên kết tham chiếu. Nhóm này đáp ứng I2 và một phần I3. Tuy nhiên, mỗi đơn vị chỉ có một phiên bản duy nhất, nên thiếu I1 và vẫn chịu Quan sát 1.

**Biểu diễn có nhận biết thời gian và phiên bản.** Trong tin học pháp lý, chuẩn Akoma Ntoso [11] mã hoá cấu trúc văn bản cùng các mốc trong vòng đời hiệu lực, và mô hình FRBR [12] phân biệt tác phẩm trừu tượng với các biểu hiện cụ thể của nó. Nghiên cứu hỏi đáp thời gian trên đồ thị tri thức [13] cho thấy ràng buộc thời gian cần được biểu diễn tường minh để suy luận đúng. Gần nhất với chúng tôi, SAT-Graph RAG [14] tách thực thể pháp lý trừu tượng khỏi các biểu hiện theo thời gian trong một đồ thị có cấu trúc phân cấp, còn VersionRAG [15] mô hình hoá tài liệu tiến hoá qua các phiên bản. Nghiên cứu [16] đồng thời cảnh báo rủi ro của việc hợp nhất văn bản luật tự động, cho thấy chuỗi phiên bản cần được xây dựng có kiểm soát và kiểm toán được.

**Bảng 6.** Mức đáp ứng các loại thông tin I1–I3 và đối sánh ngữ nghĩa (✓ đáp ứng · ◐ đáp ứng một phần · ✗ không đáp ứng).

| Hướng tiếp cận | I1 Phiên bản | I2 Cấu trúc pháp điển | I3 Tác động bắc cầu | Đối sánh ngữ nghĩa | Thiết lập đối chứng |
|---|:-:|:-:|:-:|:-:|---|
| Truy xuất phẳng [1]–[3] | ✗ | ✗ | ✗ | ✓ | B2–B4 |
| Truy xuất phẳng + lọc cấp văn bản | ◐ | ✗ | ✗ | ✓ | B7 |
| Cây ngữ nghĩa [6] | ✗ | ✗ | ✗ | ✓ | — |
| Đồ thị tri thức phi thời gian [4], [5], [9], [10] | ✗ | ✓ | ◐ | ✓ | B5, B6 |
| **Đề xuất** | ✓ | ✓ | ✓ | ✓ | — |

So với [14] và [15], đóng góp của chúng tôi nằm ở ba điểm: (i) áp dụng cho hệ thống pháp luật Việt Nam, với khung thời gian của đồ thị được xây dựng bán tự động từ siêu dữ liệu công khai; (ii) lan truyền hiệu lực theo cây pháp điển được tách thành một thành phần riêng và đánh giá độc lập, xuất phát từ Quan sát 3; (iii) thiết kế thực nghiệm tách lợi ích của biểu diễn đồ thị khỏi lợi ích của việc lọc theo siêu dữ liệu thời gian (Mục 7).

---

## 6. Biểu diễn được lựa chọn

> **Định nghĩa 2 (Đồ thị pháp luật có phiên bản).** Đồ thị $\mathcal{G} = (\mathcal{N}, \mathcal{E})$ có tập nút $\mathcal{N} = \mathcal{D} \cup \mathcal{U} \cup \mathcal{V}$ gồm nút văn bản, nút đơn vị và nút phiên bản, với tập cạnh $\mathcal{E} = \mathcal{E}_{\text{part}} \cup \mathcal{E}_{\text{ver}} \cup \mathcal{E}_{\text{rel}}$, trong đó:
> - $\mathcal{E}_{\text{part}}$ gồm cạnh cấp trên – cấp dưới, mã hoá $\pi$ (I2);
> - $\mathcal{E}_{\text{ver}}$ gồm cạnh từ đơn vị đến phiên bản; mỗi nút phiên bản mang khoảng $[s_i, e_i)$ (I1);
> - $\mathcal{E}_{\text{rel}}$ gồm cạnh có kiểu giữa các văn bản, với kiểu thuộc tập 13 loại quan hệ do nguồn dữ liệu công bố như sửa đổi bổ sung, thay thế, bãi bỏ, căn cứ ban hành, dẫn chiếu (I3).
>
> Nút văn bản mang thêm các thuộc tính cơ quan ban hành, loại văn bản, ngày ban hành và ngày có hiệu lực.

Theo Mục 3, $\mathcal{G}$ chứa đủ I1–I3, nên $\mathrm{valid}(u, t)$ tính được một cách tất định từ $\mathcal{G}$ qua (1)–(3). Trong phương pháp, đồ thị đảm nhận ba vai trò tách biệt. Mỗi vai trò xuất phát từ một quan sát và có một thiết lập loại bỏ tương ứng:

1. **Lọc hiệu lực.** Không gian tìm kiếm được thu hẹp về $\mathcal{U}_t$ theo (4) trước khi xếp hạng. Vai trò này xuất phát từ Quan sát 1 và 2, và được kiểm chứng bằng thiết lập bỏ ràng buộc thời gian (A1) cùng so sánh với B7.
2. **Lan truyền hiệu lực.** Vế đệ quy của (3) được đánh giá trên $\mathcal{E}_{\text{part}}$. Vai trò này xuất phát từ Quan sát 3 và được kiểm chứng bằng A4.
3. **Mở rộng theo láng giềng.** Ngữ cảnh bằng chứng được mở rộng theo cạnh tác động và dẫn chiếu trong $\mathcal{E}_{\text{rel}}$. Vai trò này xuất phát từ Quan sát 4 và được kiểm chứng bằng thiết lập bỏ mở rộng đồ thị (A2) cùng so sánh với B5.

Đồ thị không tự cung cấp độ tương đồng ngữ nghĩa giữa câu hỏi và điều khoản. Vì vậy, bên trong $\mathcal{U}_t$, ứng viên vẫn được xếp hạng bằng tổ hợp tín hiệu từ vựng và ngữ nghĩa. Phương pháp đề xuất do đó là *lai*: đồ thị bảo đảm tính hợp lệ theo thời gian, còn truy xuất văn bản bảo đảm tính liên quan.

---

## 7. Giả thuyết kiểm chứng

Các quan sát ở Mục 4 là bằng chứng về *điều kiện cần*: thông tin quyết định hiệu lực tồn tại trong dữ liệu và bị các biểu diễn đơn giản hơn đánh mất. Chúng chưa chứng minh rằng hệ thống dựa trên $\mathcal{G}$ trả lời đúng hơn ở mức đầu – cuối, vì kết quả còn phụ thuộc vào chất lượng trích xuất thao tác sửa đổi, chất lượng truy xuất và mô hình sinh. Để biến lập luận thành các khẳng định có thể bác bỏ, chúng tôi xác định trước các giả thuyết trong Bảng 7.

Các thiết lập đối chứng gồm: B2 (BM25), B3 (truy xuất dày), B4 (truy xuất lai kèm bộ xếp hạng lại), B5 (GraphRAG phi thời gian), B6 (đồ thị tri thức phân cấp cho pháp luật Việt Nam) và B7 (truy xuất kèm lọc theo siêu dữ liệu hiệu lực cấp văn bản, không dùng đồ thị). Các nhóm câu hỏi liên quan gồm: T1 (tra cứu một phiên bản, không mơ hồ về thời gian), T2 (cặp câu hỏi tương phản theo thời gian), T3 (truy vết chuỗi sửa đổi nhiều bước), T4 (phiên bản cũ còn trong kho và rất giống về nội dung) và T6 (hết hiệu lực một phần ở cấp khoản, điểm). Các chỉ số gồm TVER (tỉ lệ câu trả lời có trích dẫn không còn hiệu lực), VCR (tỉ lệ trích đúng đơn vị nhưng sai phiên bản) và TCS (tỉ lệ trả lời đúng ở cả hai mốc của một cặp tương phản).

**Bảng 7.** Giả thuyết, dự đoán và điều kiện bác bỏ.

| Giả thuyết | Xuất phát từ | Dự đoán | Bị bác bỏ nếu |
|---|---|---|---|
| H1 | Quan sát 1 | VCR của B2–B4 trên T4 cao hơn đáng kể so với trên T1 | VCR của B2–B4 trên T4 không cao hơn trên T1 |
| H2 | Quan sát 2 | Khoảng cách giữa phương pháp đề xuất và B7 lớn nhất trên T6 | B7 đạt kết quả tương đương phương pháp đề xuất trên T6 |
| H3 | Quan sát 3 | Loại bỏ lan truyền làm tăng TVER, tập trung ở câu hỏi mà bằng chứng nằm dưới một đơn vị bị bãi bỏ | TVER không thay đổi đáng kể trên tập con này |
| H4 | Quan sát 4 | A2 làm giảm độ chính xác nhiều nhất trên T3; B5 có TCS thấp hơn phương pháp đề xuất trên T2 | A2 không làm giảm độ chính xác trên T3 |

H2 là phép thử quyết định đối với lựa chọn biểu diễn. Nếu việc lọc theo siêu dữ liệu cấp văn bản đạt gần mức của phương pháp đề xuất, thì lợi ích của biểu diễn đồ thị không được xác lập, và đóng góp của các thành phần xây dựng đồ thị phải được đánh giá lại.

---

## 8. Giới hạn

**Các số liệu là cận dưới.** Quan sát 1 chỉ tính các nhóm có nội dung trùng khớp tuyệt đối sau chuẩn hoá; các cặp gần giống, chẳng hạn chỉ khác vài từ do sửa đổi, không được tính. Quan sát 2 và 3 chỉ tính 73,8% ghi nhận bãi bỏ định vị được chính xác trên cây; phần còn lại chưa định vị được do cây cấu trúc từ nguồn không khai báo tới cấp tương ứng.

**Khoảng hiệu lực kế thừa từ văn bản.** Do kho dữ liệu chỉ lưu văn bản ở trạng thái hiện hành, khoảng hiệu lực của mỗi phiên bản trong phân tích được kế thừa từ văn bản chứa nó. Vì vậy, Quan sát 1 phản ánh xung đột giữa các văn bản khác nhau, chưa phản ánh xung đột giữa các phiên bản của cùng một đơn vị. Loại xung đột thứ hai chỉ đo được sau khi trích xuất thao tác sửa đổi ở cấp khoản, điểm.

**Trạng thái tại một thời điểm.** Trạng thái hiệu lực của văn bản và các ghi nhận bãi bỏ được lấy tại ngày chụp dữ liệu. Thời điểm cụ thể một đơn vị bị bãi bỏ không phải lúc nào cũng có trong siêu dữ liệu, nên Quan sát 2 và 3 được đo tại ngày chụp chứ không tại mọi thời điểm $t$.

**Phạm vi dữ liệu.** Phân tích dựa trên một nguồn dữ liệu và một hệ thống pháp luật. Khả năng khái quát sang miền hoặc nguồn khác cần được kiểm chứng riêng.

---

## Tài liệu tham khảo

[1] P. Lewis, E. Perez, A. Piktus, F. Petroni, V. Karpukhin, N. Goyal, H. Küttler, M. Lewis, W. Yih, T. Rocktäschel, S. Riedel, and D. Kiela, "Retrieval-augmented generation for knowledge-intensive NLP tasks," in *Proc. NeurIPS*, 2020.

[2] S. Robertson and H. Zaragoza, "The probabilistic relevance framework: BM25 and beyond," *Foundations and Trends in Information Retrieval*, vol. 3, no. 4, pp. 333–389, 2009.

[3] V. Karpukhin, B. Oğuz, S. Min, P. Lewis, L. Wu, S. Edunov, D. Chen, and W. Yih, "Dense passage retrieval for open-domain question answering," in *Proc. EMNLP*, 2020.

[4] D. Edge, H. Trinh, N. Cheng, J. Bradley, A. Chao, A. Mody, S. Truitt, and J. Larson, "From local to global: A graph RAG approach to query-focused summarization," arXiv:2404.16130, 2024.

[5] Z. Guo, L. Xia, Y. Yu, T. Ao, and C. Huang, "LightRAG: Simple and fast retrieval-augmented generation," in *Findings of EMNLP*, 2025.

[6] P. Sarthi, S. Abdullah, A. Tuli, S. Khanna, A. Goldie, and C. D. Manning, "RAPTOR: Recursive abstractive processing for tree-organized retrieval," in *Proc. ICLR*, 2024.

[7] A. Hogan, E. Blomqvist, M. Cochez, C. d'Amato, G. de Melo, C. Gutierrez, et al., "Knowledge graphs," *ACM Computing Surveys*, vol. 54, no. 4, pp. 1–37, 2021.

[8] A. Louis, G. van Dijck, and G. Spanakis, "Finding the law: Enhancing statutory article retrieval via graph neural networks," in *Proc. EACL*, 2023.

[9] V. T. Pham and M. Phan, "Integrating knowledge graph with retrieval-augmented generation for Vietnamese legal question answering," *DS Journal of Digital Science and Technology*, vol. 5, no. 1, 2026.

[10] M. P. Huynh, T. V. Nguyen-Thi, H. T. N. Trang, and A. C. Le, "Applying Graph RAG: Enhancing retrieval and synthesis of Vietnamese legal text information," in *Proc. ICCIES*, Springer CCIS, vol. 2585, 2026.

[11] M. Palmirani and F. Vitali, "Akoma-Ntoso for legal documents," in *Legislative XML for the Semantic Web*, Springer, 2011.

[12] IFLA Study Group on the Functional Requirements for Bibliographic Records, *Functional Requirements for Bibliographic Records: Final Report*. München: K. G. Saur, 1998.

[13] Z. Jia, S. Pramanik, R. Saha Roy, and G. Weikum, "Complex temporal question answering on knowledge graphs," in *Proc. CIKM*, 2021.

[14] H. de Martim, "An ontology-driven graph RAG for legal norms: A hierarchical, temporal, and deterministic approach," in *Legal Knowledge and Information Systems (JURIX)*, IOS Press, 2025.

[15] D. Huwiler, K. Stockinger, and J. Fürst, "VersionRAG: Version-aware retrieval-augmented generation for evolving documents," arXiv:2510.08109, 2025.

[16] M. Prior, A. Hof, N. Wais, and M. Grabmair, "Risks and limits of automatic consolidation of statutes," in *Proc. Natural Legal Language Processing Workshop*, 2025.

---

<!--
GHI CHÚ CHO NGƯỜI VIẾT — xoá khi đưa vào bài.

1. Số liệu: tái lập bằng `python scripts/explore/compare_representations.py`
   -> data/representation_benchmark.json (M1, M2a, M2b, M2c, M3.lineage_size).
   Ví dụ 1 được lấy trực tiếp từ data/temporal.sqlite (bản chụp 12/09/2026).
2. Công thức (1)–(4) đánh số riêng cho mục này; đề cương đánh số (1)–(3) khác.
   Công thức (3) ở đây gộp "bãi bỏ riêng" vào việc đóng khoảng hiệu lực trong (2).
   Cần thống nhất ký hiệu với chương Phương pháp.
3. H1–H4 KHÔNG có trong đề cương; cần nhóm thống nhất trước khi chạy thực nghiệm.
   H3 cần một biến thể "bỏ vế đệ quy của (3)" — A4 trong đề cương chỉ là proxy.
4. Chưa kiểm tra thông tin xuất bản (danh sách tác giả, trang, venue): [2], [3], [7], [11], [12], [13];
   danh sách tác giả đầy đủ của [1], [3], [4], [6] được bổ sung từ trí nhớ, cần đối chiếu.
   Hai mục KHÁC đề cương, cần kiểm tra và sửa đồng bộ cả đề cương nếu đúng:
   - [6] đề cương ghi "S. Sarthi"; tên đúng nhiều khả năng là "P. Sarthi" (Parth Sarthi).
   - [8] đề cương ghi "A. Louis, N. Thakur, I. Gurevych, Enhancing Statutory Article Retrieval via
     Graph Neural Networks over Legal Citation Graphs"; bài EACL 2023 nhiều khả năng là
     "A. Louis, G. van Dijck, G. Spanakis, Finding the Law: Enhancing Statutory Article Retrieval
     via Graph Neural Networks".
   Mô tả SAT-Graph RAG [14] và VersionRAG [15] ở Mục 5 cần đối chiếu với bài gốc.
-->
