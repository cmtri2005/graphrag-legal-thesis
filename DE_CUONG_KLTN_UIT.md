| ĐẠI HỌC QUỐC GIA TP. HỒ CHÍ MINH<br>TRƯỜNG ĐẠI HỌC<br>CÔNG NGHỆ THÔNG TIN | CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM<br>Độc Lập - Tự Do - Hạnh Phúc |
| --- | --- |

ĐỀ CƯƠNG CHI TIẾT

| TÊN ĐỀ TÀI TIẾNG VIỆT: TRUY XUẤT TĂNG CƯỜNG DỰA TRÊN ĐỒ THỊ TRI THỨC CÓ NHẬN BIẾT THỜI GIAN CHO HỎI ĐÁP PHÁP LUẬT VIỆT NAM THEO MỐC HIỆU LỰC |
| --- |
| TÊN ĐỀ TÀI TIẾNG ANH: TEMPORAL-AWARE KNOWLEDGE GRAPH RAG FOR POINT-IN-TIME VIETNAMESE LEGAL QUESTION ANSWERING |
| Cán bộ hướng dẫn: ………………………………………, Khoa Hệ thống Thông tin, Trường Đại học Công Nghệ Thông Tin, ĐHQG-TP.HCM |
| Thời gian thực hiện: Từ ngày 01/09/2026 đến ngày 01/02/2027 |
| Sinh viên thực hiện:<br>Cao Minh Trí – 23521635<br>Nguyễn Minh Trí – 23621643 |

Nội dung đề tài:

# Tổng quan đề tài:

Những năm gần đây, việc ứng dụng các Mô hình Ngôn ngữ Lớn (Large Language Models – LLM) kết hợp kỹ thuật Tạo sinh Tăng cường Truy xuất (Retrieval-Augmented Generation – RAG) trong lĩnh vực pháp lý đã thu hút nhiều sự quan tâm nghiên cứu. Mục tiêu chính của các hệ thống hỏi đáp pháp luật là hỗ trợ cá nhân và tổ chức tra cứu quy định hiệu quả mà không đòi hỏi chuyên môn sâu. Tuy nhiên, phần lớn các kiến trúc RAG hiện hành đều dựa trên giả định ngầm rằng cơ sở tri thức pháp luật là tĩnh—nơi mỗi điều khoản chỉ tồn tại dưới một phiên bản duy nhất. Giả định này không phản ánh đúng bản chất động của hệ thống văn bản quy phạm pháp luật, vốn liên tục được sửa đổi, bổ sung, thay thế hoặc bãi bỏ theo thời gian.

Hạn chế mang tính cấu trúc này dẫn đến hiện tượng ảo giác theo thời gian (temporal hallucination): hệ thống truy xuất và trích dẫn chính xác số hiệu điều luật nhưng áp dụng sai phiên bản hiệu lực. Kết quả sinh ra tuy có độ mạch lạc cao và nguồn dẫn rõ ràng nhưng lại căn cứ trên các quy định đã hết hiệu lực thi hành. Trong nghiệp vụ pháp lý, sai lệch này không đơn thuần là lỗi suy diễn mô hình mà có thể gây ra những rủi ro pháp lý nghiêm trọng trong ứng dụng thực tế.

Phát biểu bài toán

Đề tài nghiên cứu bài toán Hỏi đáp pháp luật theo mốc thời gian (Point-in-Time Legal Question Answering) cho pháp luật Việt Nam, được phát biểu như sau:

Đầu vào (Input): Một câu hỏi pháp lý x bằng tiếng Việt, kèm theo một mốc thời gian áp dụng t (thời điểm phát sinh hành vi hoặc quan hệ pháp luật cần tra cứu).

Đầu ra (Output): Một câu trả lời a kèm tập bằng chứng E gồm các đơn vị pháp lý (Điều / Khoản / Điểm) có hiệu lực tại thời điểm t.

Hình 1. Mô tả đầu vào và đầu ra của bài toán.

Một cách hình thức, bài toán được mô tả bởi công thức (1), trong đó U là tập toàn bộ đơn vị pháp lý trong kho văn bản và valid(u, t) là vị từ xác định đơn vị u có hiệu lực tại thời điểm t hay không:

Điểm khác biệt then chốt so với hỏi đáp pháp luật thông thường nằm ở chỗ truy vấn không còn là x mà là cặp (x, t). Cùng một câu hỏi, hai mốc thời gian khác nhau phải cho hai câu trả lời và hai tập bằng chứng khác nhau. Hình 2 minh họa hiện tượng sai lệch thời gian (temporal bias) mà các mô hình ngôn ngữ hiện nay mắc phải: chúng có xu hướng neo vào phiên bản pháp luật xuất hiện nhiều nhất trong dữ liệu huấn luyện.

Hình 2. Minh họa lỗi áp dụng sai phiên bản văn bản theo mốc thời gian.

Tình hình nghiên cứu quốc tế

Các công trình nghiên cứu quốc tế về bài toán hỏi đáp pháp luật dựa trên kiến trúc RAG (Retrieval-Augmented Generation) [1] có thể chia thành ba giai đoạn phát triển chính. Ở giai đoạn đầu, các nghiên cứu chủ yếu dựa vào mô hình truy xuất phẳng (flat retrieval), kết hợp BM25 với các bộ biểu diễn ngữ nghĩa (dense retrieval) nhằm tìm kiếm các đoạn văn bản tương đồng rồi đưa trực tiếp vào mô hình ngôn ngữ lớn (LLM). Bước sang giai đoạn thứ hai, sự chú ý chuyển dịch sang việc mô hình hóa cấu trúc phân cấp và ngữ nghĩa; các kỹ thuật như GraphRAG [2], LightRAG [3], cấu trúc phân cấp cây RAPTOR [4] hay mạng nơ-ron đồ thị áp dụng trên đồ thị trích dẫn [5] đã chứng minh được tính hiệu quả vượt trội trong các tác vụ suy luận đa bước (multi-hop reasoning).

Giai đoạn thứ ba—mới hình thành trong giai đoạn 2024–2026—bắt đầu xem xét chiều thời gian (temporal dimension) như một yếu tố quyết định tính đúng đắn của hệ thống. Các công trình gần đây chỉ ra rằng các kiến trúc GraphRAG truyền thống suy giảm hiệu năng nghiêm trọng khi dữ liệu có sự biến động phiên bản, đặc biệt trước các sửa đổi có tính chất ngầm định [6]. Để xử lý vấn đề này, một số nhóm tác giả đề xuất việc phân tách rành mạch giữa thực thể pháp lý trừu tượng và các biểu hiện thực thi theo phiên bản hiệu lực nhằm bảo đảm khả năng kiểm toán của hệ thống [7]. Song song đó, các phân tích chuyên sâu trên tập dữ liệu STARD [8] cũng như những cảnh báo về giới hạn của việc tự động hợp nhất văn bản luật [9] cho thấy mô hình thường hoạt động kém ổn định đối với các quy định nằm ngoài mốc thời gian huấn luyện. Dù vậy, phần lớn các công trình này mới dừng lại ở việc khảo sát trên hệ thống pháp luật Thông luật (Common Law) hoặc Dân luật (Civil Law) phương Tây và sử dụng ngữ liệu tiếng Anh, tiếng Trung.

Tình hình nghiên cứu trong nước

Tại Việt Nam, hướng nghiên cứu Xử lý ngôn ngữ tự nhiên trong lĩnh vực pháp lý (Legal NLP) phát triển chủ yếu thông qua các bộ dữ liệu từ các kỳ đánh giá ALQAC [10] và VLSP [11]. Đây là cơ sở thực nghiệm cho các tác vụ truy xuất điều luật, kiểm chứng suy luận và hỏi đáp pháp luật [12]. Gần đây, nguồn ngữ liệu được mở rộng thêm với các bộ dữ liệu quy mô lớn như VLQA [13] hay benchmark hỏi đáp đa bước ViHERMES [14] trên văn bản pháp quy y tế. Về mặt phương pháp, giai đoạn 2025–2026 ghi nhận sự xuất hiện của các nghiên cứu tích hợp đồ thị tri thức với RAG [15], [16]. Các công trình này tập trung xây dựng đồ thị nhằm bảo toàn cấu trúc pháp điển từ cấp Văn bản đến Điều, Khoản, Điểm và thiết lập các liên kết tham chiếu để hỗ trợ LLM mở rộng ngữ cảnh truy xuất.

Từ tổng quan trên, có thể nhận thấy hướng tiếp cận kết hợp đồ thị tri thức phân cấp với RAG cho văn bản pháp luật tiếng Việt đã có những đóng góp nền tảng. Tuy nhiên, khoảng trống nghiên cứu then chốt hiện nay nằm ở hai điểm:

Chưa có công trình nào trong nước mô hình hóa một cách tường minh chiều thời gian và vòng đời hiệu lực của các văn bản quy phạm pháp luật.

Chưa có bộ dữ liệu chuẩn nào cho phép đánh giá có kiểm soát khả năng truy xuất và suy luận đúng phiên bản quy phạm pháp luật tại thời điểm diễn ra sự việc.

Khoảng trống này càng trở nên rõ nét sau đợt tái sắp xếp tổ chức bộ máy nhà nước theo Nghị quyết số 190/2025/QH15 [17] và các quy định của Luật Ban hành văn bản quy phạm pháp luật [18], dẫn đến việc sửa đổi, thay thế hoặc bãi bỏ đồng loạt hàng loạt văn bản quy phạm pháp luật (tiêu biểu như các nghị định xử phạt vi phạm hành chính [19], [20]). Biến động pháp lý này vừa đặt ra bài toán cấp thiết trong thực tiễn, vừa tạo thành một môi trường kiểm thử tự nhiên phù hợp cho việc đánh giá các mô hình RAG có nhận biết thời gian và phiên bản văn bản.

Khó khăn và thử thách:

Siêu dữ liệu cấp văn bản không phản ánh đúng hiệu lực cấp điều khoản: trạng thái “Còn hiệu lực” của một văn bản không bảo đảm mọi khoản trong đó đều còn hiệu lực. Trạng thái “Hết hiệu lực một phần” rất phổ biến và là nguồn gốc chủ yếu của lỗi truy xuất.

Thao tác sửa đổi có cấu trúc phức tạp: các mệnh đề như “bổ sung điểm đ vào sau điểm d khoản 3 Điều 6” hay “thay thế cụm từ … tại các Điều 5, 7, 12” không chỉ là thay đổi nội dung mà còn là phép biến đổi có vị trí và phạm vi. Việc bãi bỏ cả một Chương kéo theo vô hiệu hóa toàn bộ cây con.

Dẫn chiếu động: các cụm “theo quy định tại khoản 2 Điều 5 của Luật này” hay “Điều X của Luật Y đã được sửa đổi, bổ sung” chỉ có thể giải quyết được khi đã biết mốc thời gian.

Thiếu dữ liệu gán nhãn: không tồn tại bộ dữ liệu tiếng Việt nào gắn nhãn mốc thời gian áp dụng cùng bằng chứng ở cấp khoản.

Nguy cơ sai lệch pháp lý: nguyên tắc chung là áp dụng văn bản có hiệu lực tại thời điểm phát sinh hành vi, nhưng pháp luật cũng quy định về hiệu lực trở về trước trong một số trường hợp có lợi hơn cho đối tượng bị áp dụng. Việc xác định đáp án đúng do đó cần được kiểm chứng bởi người có chuyên môn luật.

Mục tiêu của đề tài:

Đề tài hướng tới trả lời ba câu hỏi nghiên cứu sau:

RQ1. Các mô hình ngôn ngữ lớn và các hệ thống RAG hiện có mắc lỗi áp dụng sai phiên bản quy phạm ở mức độ nào trên pháp luật Việt Nam?

RQ2. Việc biểu diễn văn bản pháp luật dưới dạng đồ thị theo phiên bản có làm giảm tỷ lệ lỗi này so với RAG phẳng và GraphRAG phi thời gian hay không?

RQ3. Lợi ích thu được đến từ biểu diễn đồ thị, hay chỉ đơn thuần đến từ việc lọc theo siêu dữ liệu thời gian?

Giả thuyết nghiên cứu: việc mô hình hóa tường minh chuỗi phiên bản và lan truyền hiệu lực trên cây cấu trúc sẽ mang lại cải thiện có ý nghĩa so với việc chỉ lọc theo ngày hiệu lực ở cấp văn bản, và mức cải thiện sẽ lớn nhất ở nhóm câu hỏi đòi hỏi truy vết chuỗi sửa đổi nhiều bước.

Trên cơ sở đó, đề tài đặt ra bốn mục tiêu cụ thể:

Xây dựng bộ dữ liệu ViLexTime – bộ dữ liệu đầu tiên cho bài toán hỏi đáp pháp luật theo mốc thời gian trong tiếng Việt, quy mô khoảng 1.100–1.300 câu hỏi, có cặp câu hỏi tương phản theo thời gian và bằng chứng ở cấp Điều / Khoản / Điểm.

Xây dựng Đồ thị tri thức pháp luật có nhận biết thời gian (Temporal Legal Knowledge Graph) cho pháp luật Việt Nam, với quy trình xây dựng bán tự động khai thác siêu dữ liệu công khai.

Đề xuất kiến trúc truy xuất có ràng buộc thời gian kết hợp lọc hiệu lực, truy xuất lai ghép và mở rộng theo đồ thị, cùng cơ chế kiểm chứng trích dẫn.

Đề xuất bộ chỉ số đánh giá độ tin cậy thời gian (TVER, VCR, TCS) và tiến hành đánh giá so sánh có hệ thống với bảy đường cơ sở.

Phương pháp thực hiện:

Về mặt kỹ thuật, hệ thống đề xuất được tổ chức thành sáu tầng như mô tả trong Hình 3. Các tầng L0–L3 được thực hiện ngoại tuyến và sinh ra một sản phẩm trung gian tĩnh, có thể kiểm toán; các tầng L4–L5 hoạt động trực tuyến theo từng truy vấn.

Hình 3. Kiến trúc tổng thể của hệ thống đề xuất.

Tầng L0–L1: Phân tích cấu trúc và cạnh từ siêu dữ liệu

Văn bản được thu thập từ Cơ sở dữ liệu quốc gia về văn bản quy phạm pháp luật (vbpl.vn) [21] và phân tích thành cây phân cấp Văn bản → Chương → Mục → Điều → Khoản → Điểm. Điểm thuận lợi quan trọng là phần khung thời gian của đồ thị có thể lấy trực tiếp từ siêu dữ liệu sẵn có: ngày ban hành, ngày có hiệu lực, trạng thái hiệu lực, cùng các liên kết “văn bản được sửa đổi, bổ sung”, “văn bản bị thay thế”, “văn bản dẫn chiếu”. Nhờ đó, chi phí gán nhãn thủ công giảm đáng kể so với các bài toán tương tự.

Hình 4. Lược đồ đồ thị tri thức pháp luật có nhận biết thời gian.

Thuộc tính trên mỗi nút phiên bản: eff_from, eff_to, issuer, rank => Cho phép truy vấn snapshot(u,t) một cách tất định.

Tầng L2: Trích xuất thao tác sửa đổi

Nội dung sửa đổi ở cấp khoản, điểm được trích xuất thành bộ bốn (utarget , op, textnew, teff), trong đó op thuộc tập {SỬA ĐỔI, BỔ SUNG, BÃI BỎ, THAY THẾ}. Chiến lược kết hợp được sử dụng: biểu thức chính quy xử lý các mẫu chuẩn, mô hình ngôn ngữ chỉ được gọi cho các trường hợp phức tạp. Độ chính xác của bước này được đo trên 200 mẫu kiểm chứng thủ công và báo cáo tường minh trong khóa luận.

Tầng L3: Hợp nhất phiên bản và lan truyền hiệu lực

Mỗi đơn vị pháp lý u được gắn một chuỗi phiên bản Vu = {v1, v2, …}, mỗi phiên bản có một khoảng hiệu lực nửa mở. Hàm truy vấn cốt lõi của hệ thống được định nghĩa như công thức (2):

|  | (2) |
| --- | --- |

Hiệu lực không phải là một thuộc tính phẳng của văn bản mà là một hàm được lan truyền trên cây cấu trúc. Một khoản chỉ hợp lệ khi Điều cha của nó hợp lệ và bản thân nó chưa bị bãi bỏ riêng, như mô tả trong công thức (3):

|  | (3) |
| --- | --- |

Hình 5 minh họa hai trường hợp lan truyền khác nhau. Trường hợp (a): bãi bỏ cả Chương làm vô hiệu toàn bộ cây con. Trường hợp (b): bãi bỏ riêng một khoản không làm Điều cha vô hiệu. Trong cả hai trường hợp, siêu dữ liệu ở cấp văn bản đều không đủ để phân biệt.

Hình 5. Lan truyền hiệu lực trên cây cấu trúc văn bản.

Mở rộng (không bắt buộc): trong trường hợp còn thời gian, đề tài xem xét bổ sung bước giải xung đột quy phạm theo công thức (4), trong đó C(u, t) là tập quy phạm cùng có hiệu lực và cùng điều chỉnh một quan hệ, còn quan hệ u′ ≻ u được xác định theo thứ bậc hiệu lực pháp lý và tính chuyên ngành:

|  | (4) |
| --- | --- |

Tầng L4: Truy xuất có ràng buộc thời gian

Không gian tìm kiếm trước hết được thu hẹp về tập các đơn vị hợp lệ tại thời điểm truy vấn theo công thức (5):

|  |  |
| --- | --- |

Trên tập đã lọc, điểm số của mỗi ứng viên được tính bằng tổ hợp giữa tín hiệu từ vựng, tín hiệu ngữ nghĩa và tín hiệu lan truyền từ các nút láng giềng trên đồ thị (công thức (6)), trong đó NG(u) là tập láng giềng của u theo các cạnh AMENDS và REFERS_TO, còn λ, μ là các siêu tham số được tinh chỉnh trên tập phát triển:

|  | (6) |
| --- | --- |

Tầng L5: Sinh câu trả lời và kiểm chứng trích dẫn

Mô hình sinh được ràng buộc phải trích dẫn ở cấp Điều / Khoản / Điểm. Sau đó, một mô-đun kiểm chứng (Temporal Verifier) rà soát toàn bộ trích dẫn trong câu trả lời và loại bỏ hoặc cảnh báo những trích dẫn không hợp lệ tại thời điểm truy vấn. Hệ thống chỉ sử dụng đúng hai vai tác tử – bộ suy luận mốc thời gian và bộ kiểm chứng trích dẫn – nhằm giữ cho thiết kế thực nghiệm còn khả năng phân tách đóng góp của từng thành phần.

Các nội dung chính và giới hạn của đề tài

- Nội dung thực hiện:

Nội dung 1: Khảo sát và phân tích tài liệu liên quan

Khảo sát các phương pháp RAG và GraphRAG tiêu biểu (GraphRAG, LightRAG, RAPTOR, IRCoT).

Khảo sát dòng nghiên cứu về RAG nhận biết thời gian và phiên bản (VersionRAG, SAT-Graph RAG) và các nghiên cứu về hợp nhất văn bản luật.

Phân tích các công trình Legal NLP tiếng Việt: ALQAC, VLSP, ViBidLQA, VLQA, ViHERMES và các hệ thống KG + RAG cho pháp luật Việt Nam.

Xác định chính xác khoảng trống nghiên cứu và định vị đóng góp của đề tài.

Nội dung 2: Thu thập và phân tích cấu trúc kho văn bản

Thu thập văn bản từ vbpl.vn, lưu trữ bản gốc để bảo đảm khả năng tái lập; ghi rõ nguồn và phương pháp thu thập.

Xây dựng bộ phân tích cấu trúc, tách chính xác các cấp Chương / Mục / Điều / Khoản / Điểm.

Chuẩn hóa và trích xuất siêu dữ liệu hiệu lực cùng các liên kết giữa văn bản.

Quy mô kho văn bản dự kiến được trình bày trong Bảng 1.

Bảng 1. Phạm vi kho văn bản của đề tài.

| Miền pháp luật | Vai trò | Trục thời gian chính | Số VB dự kiến |
| --- | --- | --- | --- |
| Xử phạt vi phạm hành chính<br>về giao thông đường bộ | Miền chính<br>(phát triển & tinh chỉnh) | NĐ 100/2019 → NĐ 168/2024;<br>Luật GTĐB 2008 → Luật TTATGTĐB 2024 | 80 – 110 |
| Bảo hiểm xã hội | Miền kiểm chứng<br>(không tinh chỉnh) | Luật BHXH 2014 → Luật BHXH 2024<br>(hiệu lực 01/7/2025) | 40 – 60 |

Nội dung 3: Xây dựng Đồ thị tri thức pháp luật có nhận biết thời gian

Sinh cạnh cấu trúc và cạnh siêu dữ liệu (L0–L1).

Trích xuất thao tác sửa đổi ở cấp khoản, điểm bằng phương pháp lai giữa luật hình thức và mô hình ngôn ngữ (L2); đo và báo cáo độ chính xác trên tập kiểm chứng.

Cài đặt cơ chế hợp nhất phiên bản và lan truyền hiệu lực; kiểm chứng hàm snapshot trên 100 truy vấn đối chiếu thủ công (L3).

Xây dựng mô-đun giải dẫn chiếu chéo có nhận biết thời gian.

Nội dung 4: Xây dựng bộ dữ liệu ViLexTime

Việc xây dựng nhãn vàng cho bộ dữ liệu tuân theo nguyên tắc driff-driven (dẫn xuất từ khác biệt văn bản), nhằm tách bạch giữa nguồn gốc của đáp án và công đoạn diễn đạt ngôn ngữ tự nhiên. Cách tiếp cận này khác với việc sử dụng mô hình ngôn ngữ lớn để sinh đồng thời cả câu trả lời lẫn đáp án - vốn tiềm ẩn rủi ro ảo giác (hallucination) về số liệu, điều khoản hoặc mốc hiệu lực không có thật trong văn bản gốc.

Với mỗi đơn vị pháp lý u tồn tại từ hai phiên bản trở lên, nhãn vàng được xác định thông qua phép so sánh trực tiếp giữa snapshot(u, t1) và snapshot(u, t2), cho ra bộ ba (nội dung trước sửa đổi, nội dung sau sửa đổi, mốc thời gian chuyển đổi hiệu lực) gắn với đơn vị pháp lý tương ứng. Nhãn vàng do đó xác định hoàn toàn bằng đối chiếu văn bản, có thể truy vết ngược về nguồn, và không phụ thuộc vào khả năng suy luận của mô hình ngôn ngữ.

Mô hình ngôn ngữ chỉ được sử dụng ở bước cuối quy trình, với vai trò giới hạn là diễn đạt khác biệt đã được xác định thành câu hỏi tiếng Việt tự nhiên. Việc phân tách vai trò này đảm bảo tính đúng đắn của đáp án không bị ảnh hưởng bởi chất lượng sinh ngôn ngữ cuarm ô hình; các lỗi diễn đạt (nếu có) được xử lý ở bước kiểm định thủ công mà không làm thay đổi nhãn vàng. Quy trình bốn bước - so khớp phiên bản, trích xuất khác biệt, sinh câu hỏi, và kiểm định thủ công - được mình họa trong Hình 6.

Hình 6. Quy trình xây dựng bộ dữ liệu theo hướng diff-driven.

Cấu trúc bộ dữ liệu gồm bảy nhóm câu hỏi, trình bày trong Bảng 2.

Bảng 2. Cấu trúc bộ dữ liệu ViLexTime.

| Nhóm | Mô tả | Vai trò trong đánh giá | Số câu |
| --- | --- | --- | --- |
| T1 | Tra cứu một phiên bản, không mơ hồ về thời gian | Đối chứng | 250 |
| T2 | Cặp tương phản: cùng câu hỏi, khác mốc thời gian, khác đáp án | Nhóm cốt lõi | 400<br>(200 cặp) |
| T3 | Truy vết chuỗi sửa đổi nhiều bước (A → B → C) | Đo lợi ích của đồ thị | 200 |
| T4 | Bẫy thời gian: phiên bản cũ vẫn nằm trong kho, rất giống về ngữ nghĩa | Đo ảo giác trích dẫn | 150 |
| T5 | Hiệu lực trở về trước có lợi cho đối tượng áp dụng | Trường hợp khó | 50 |
| T6 | Xung đột quy phạm giữa các văn bản cùng hiệu lực | Mở rộng (tùy chọn) | 80 |
| T7 | Hết hiệu lực một phần ở cấp khoản, điểm | Phá vỡ đường cơ sở B7 | 100 |
|  | Tổng cộng |  | 1.230 |

Về kiểm định chất lượng: 300 câu (toàn bộ T3, T4, T5 và mẫu ngẫu nhiên từ T2) được hai người kiểm chéo độc lập, báo cáo hệ số đồng thuận Cohen κ. Nếu κ < 0,6 thì hướng dẫn gán nhãn sẽ được viết lại và quá trình kiểm định được thực hiện lại. Riêng nhóm T5 và T6 cần được xác nhận bởi người có chuyên môn về luật.

Nội dung 5: Xây dựng hệ thống truy xuất và sinh câu trả lời

Cài đặt truy xuất có ràng buộc thời gian theo công thức (5) và (6).

Cài đặt mở rộng ngữ cảnh theo đồ thị với số bước và trọng số cạnh được tinh chỉnh trên tập phát triển.

Cài đặt sinh câu trả lời có ràng buộc trích dẫn và mô-đun Temporal Verifier.

Xây dựng giao diện minh họa cho phép người dùng chọn mốc thời gian và xem đường dẫn bằng chứng.

Nội dung 6: Thực nghiệm, đánh giá và phân tích

Đề tài triển khai bảy đường cơ sở để bảo đảm kết luận có sức thuyết phục, trình bày trong Bảng 3.

Bảng 3. Các đường cơ sở dùng để so sánh.

| Mã | Đường cơ sở | Câu hỏi mà nó trả lời |
| --- | --- | --- |
| B1 | Mô hình ngôn ngữ không truy xuất | Mức độ sai lệch thời gian nội tại của mô hình |
| B2 | BM25 + mô hình sinh | Tín hiệu từ vựng đã đủ chưa? |
| B3 | Dense retrieval + mô hình sinh | Tín hiệu ngữ nghĩa đã đủ chưa? |
| B4 | Truy xuất lai ghép + reranker | Truy xuất mạnh đã đủ chưa? |
| B5 | GraphRAG phi thời gian (LightRAG) | Đồ thị không có thời gian thì sao? |
| B6 | KG phân cấp cho pháp luật Việt Nam | Có vượt được các công trình trong nước không? |
| B7 | Chỉ lọc theo siêu dữ liệu hiệu lực,<br>không dùng đồ thị | Đồ thị có thực sự cần thiết không? |

Đường cơ sở B7 là phép thử quan trọng nhất và sẽ được thực hiện sớm: nếu việc lọc theo ngày hiệu lực ở cấp văn bản đã đạt gần mức trần, thì đóng góp của các tầng L2–L4 sẽ phải được đánh giá lại. Đề tài xác định trước một điểm quyết định ở giữa giai đoạn thực nghiệm để lựa chọn giữa hướng đóng góp về phương pháp và hướng đóng góp về tài nguyên – phân tích.

Khung đánh giá và thiết kế ablation

Hệ thống được đánh giá theo ba nhóm tiêu chí:

Khả năng truy xuất: sử dụng Recall@k, MRR và Temporally-Valid Recall@k. Kết quả chỉ được xem là đúng khi đơn vị pháp lý vừa phù hợp với câu hỏi, vừa còn hiệu lực tại thời điểm truy vấn.

Chất lượng câu trả lời: sử dụng Accuracy, EM/F1 và LLM-as-judge được hiệu chuẩn trên 100 mẫu.

Độ tin cậy thời gian: được đánh giá trên các câu trả lời có trích dẫn, gồm: TVER, VCR, TCS

Ngoài các chỉ số chuẩn (Recall@k, MRR, Accuracy, EM/F1), đề tài đề xuất ba chỉ số đo độ tin cậy thời gian. Tỷ lệ lỗi hiệu lực thời gian (Temporal Validity Error Rate – TVER) đo tỷ lệ câu trả lời có chứa ít nhất một trích dẫn không còn hiệu lực tại thời điểm truy vấn (công thức (7)):

|  | (7) |
| --- | --- |

Tỷ lệ nhầm phiên bản (Version Confusion Rate – VCR) tách riêng trường hợp hệ thống trích đúng đơn vị pháp lý nhưng sai phiên bản – loại lỗi nguy hiểm nhất vì khó phát hiện bằng mắt thường (công thức (8)):

|  | (8) |
| --- | --- |

Điểm nhất quán thời gian (Temporal Consistency Score – TCS) được tính trên tập cặp tương phản P của nhóm T2, yêu cầu hệ thống trả lời đúng ở cả hai mốc thời gian của cùng một câu hỏi (công thức (9)):

|  | (9) |
| --- | --- |

Cuối cùng, chỉ số truy xuất được điều chỉnh để chỉ tính là truy xuất đúng khi đơn vị vừa nằm trong tập bằng chứng vàng vừa hợp lệ tại thời điểm truy vấn (công thức (10)):

|  | (10) |
| --- | --- |

Đề tài thực hiện bảy thí nghiệm ablation:

A1: Bỏ ràng buộc thời gian.

A2: Bỏ cơ chế mở rộng đồ thị.

A3: Bỏ Temporal Verifier.

A4: Bỏ bước trích xuất ở cấp khoản.

A5: Thay đổi độ chi tiết của đơn vị truy xuất.

A6: Thay đổi quy mô mô hình.

A7: Chuyển hệ thống sang miền BHXH.

Toàn bộ bảy thí nghiệm ablation (A1–A7) được xác định trước khi chạy thực nghiệm nhằm tránh việc diễn giải kết quả một cách tùy tiện. Trong đó, A2 (bỏ mở rộng đồ thị) và A4 (bỏ trích xuất ở cấp khoản) là hai phép thử quyết định đối với đóng góp kỹ thuật của đề tài. Thí nghiệm A7 chuyển toàn bộ hệ thống sang miền Bảo hiểm xã hội mà không tinh chỉnh lại, nhằm kiểm tra khả năng khái quát hóa.

Đóng góp dự kiến của đề tài

ViLexTime – bộ dữ liệu đánh giá đầu tiên cho bài toán hỏi đáp pháp luật theo mốc thời gian trong tiếng Việt, có cặp câu hỏi tương phản theo thời gian.

Đồ thị tri thức pháp luật có nhận biết thời gian cho pháp luật Việt Nam cùng quy trình xây dựng bán tự động từ dữ liệu công khai.

Kiến trúc truy xuất có ràng buộc thời gian và cơ chế kiểm chứng trích dẫn, hoạt động không cần huấn luyện lại.

Bộ chỉ số TVER, VCR, TCS cùng phân tích thực nghiệm về sai lệch thời gian của các mô hình ngôn ngữ trên pháp luật Việt Nam.

- Giới hạn của đề tài:

Đề tài chỉ tập trung vào hiệu lực theo thời gian; hiệu lực theo không gian (lãnh thổ) và theo đối tượng áp dụng chưa được xử lý đầy đủ. Bước giải xung đột quy phạm chỉ được triển khai ở mức mở rộng tùy chọn.

Kho văn bản giới hạn ở hai miền pháp luật với quy mô khoảng 120–170 văn bản, chưa bao phủ toàn bộ hệ thống pháp luật Việt Nam.

Đề tài chỉ xử lý văn bản quy phạm pháp luật cấp trung ương; chưa xem xét văn bản do chính quyền địa phương ban hành, vốn chịu tác động mạnh của đợt sắp xếp đơn vị hành chính từ năm 2025.

Hệ thống chỉ hỗ trợ văn bản dạng chữ, không xử lý bảng biểu, phụ lục dạng ảnh hoặc dữ liệu đa phương thức.

Việc hợp nhất văn bản được thực hiện tự động và có thể chứa sai sót; kết quả không có giá trị pháp lý và không thay thế tư vấn pháp luật chuyên nghiệp.

Đề tài không huấn luyện lại mô hình ngôn ngữ; các cải tiến đến từ khâu biểu diễn tri thức và truy xuất.

Tài liệu tham khảo


P. Lewis, E. Perez, A. Piktus, et al., “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,” NeurIPS, 2020.

D. Edge, H. Trinh, N. Cheng, et al., “From Local to Global: A Graph RAG Approach to Query-Focused Summarization,” arXiv:2404.16130, 2024.

Z. Guo, L. Xia, Y. Yu, et al., “LightRAG: Simple and Fast Retrieval-Augmented Generation,” Findings of EMNLP, 2025.

S. Sarthi, S. Abdullah, A. Tuli, et al., “RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval,” ICLR, 2024.

A. Louis, N. Thakur, and I. Gurevych, “Enhancing Statutory Article Retrieval via Graph Neural Networks over Legal Citation Graphs,” EACL, 2023.

Daniel Huwiler, Kurt Stockinger, Jonathan Fürst, “VersionRAG: Version-Aware Retrieval-Augmented Generation for Evolving Documents,” arXiv:2510.08109, 2025.

Hudson de Martim, “An Ontology-Driven Graph RAG for Legal Norms: A Hierarchical, Temporal, and Deterministic Approach (SAT-Graph RAG),” Legal Knowledge and Information Systems (JURIX), IOS Press, 2025.

H. Su et al., “STARD: A Chinese Statute Retrieval Dataset with Real Queries Issued by Non-professionals,” arXiv:2406.15313, 2024.

M. Prior, A. Hof, N. Wais, and M. Grabmair, “Risks and Limits of Automatic Consolidation of Statutes,” Natural Legal Language Processing Workshop, 2025.

D. T. Do, S. T. Luu, T. Pham, et al., “A Summary of the ALQAC 2024 Competition,” KSE, 2024.

S. T. Luu et al., “VLSP 2025 MLQA-TSR Challenge: Vietnamese Multimodal Legal Question Answering on Traffic Sign Regulation,” VLSP, 2025.

N. T. Ha, T. P. Nguyen, K. T. Trung, et al., “Vietnamese Legal Question Answering: An Experimental Study,” KSE, 2024.

T.-M. Nguyen et al., “VLQA: The First Comprehensive, Large, and High-Quality Vietnamese Dataset for Legal Question Answering,” arXiv:2507.19995, 2025.

L. S. T. Nguyen, Q. M. Bui, T. T. Ngo, et al., “ViHERMES: A Graph-Grounded Multihop Question Answering Benchmark and System for Vietnamese Healthcare Regulations,” ACIIDS, 2026.

V. T. Pham and M. Phan, “Integrating Knowledge Graph with Retrieval-Augmented Generation for Vietnamese Legal Question Answering,” DS Journal of Digital Science and Technology, vol. 5, no. 1, 2026.

M. P. Huynh, T. V. Nguyen-Thi, H. T. N. Trang, and A. C. Le, “Applying Graph RAG: Enhancing Retrieval and Synthesis of Vietnamese Legal Text Information,” ICCIES, Springer CCIS vol. 2585, 2026.

Quốc hội nước CHXHCN Việt Nam, Nghị quyết số 190/2025/QH15 quy định về xử lý một số vấn đề liên quan đến sắp xếp tổ chức bộ máy nhà nước, 2025.

Quốc hội nước CHXHCN Việt Nam, Luật Ban hành văn bản quy phạm pháp luật (quy định về hiệu lực và nguyên tắc áp dụng văn bản quy phạm pháp luật).

Chính phủ nước CHXHCN Việt Nam, Nghị định số 100/2019/NĐ-CP quy định xử phạt vi phạm hành chính trong lĩnh vực giao thông đường bộ và đường sắt, 2019.

Chính phủ nước CHXHCN Việt Nam, Nghị định số 168/2024/NĐ-CP quy định xử phạt vi phạm hành chính về trật tự, an toàn giao thông trong lĩnh vực giao thông đường bộ; trừ điểm, phục hồi điểm giấy phép lái xe, 2024.

Bộ Tư pháp, Cơ sở dữ liệu quốc gia về văn bản quy phạm pháp luật, https://vbpl.vn.


Kế hoạch thực hiện:

| Giai đoạn | Thời gian | Cao Minh Trí | Nguyễn Minh Trí |
| --- | --- | --- | --- |
| 1. Hoàn thiện đề cương | 01/09 – 14/09/2026 | Rà soát lại phạm vi, câu hỏi nghiên cứu; khảo sát tài liệu về RAG, GraphRAG | Rà soát lại phạm vi, câu hỏi nghiên cứu; khảo sát tài liệu về RAG nhận biết thời gian, Legal NLP tiếng Việt |
| 2. Thu thập & xử lý dữ liệu | 15/09 – 05/10/2026 | Thu thập, lưu trữ bản gốc văn bản từ vbpl.vn; ghi rõ nguồn và phương pháp thu thập | Xây dựng và kiểm thử bộ phân tích cấu trúc (Chương/Mục/Điều/Khoản/Điểm) |
| 3. Xây dựng đồ thị tri thức | 06/10 – 26/10/2026 | Sinh cạnh cấu trúc và cạnh siêu dữ liệu (L0–L1); trích xuất thao tác sửa đổi (L2) | Cài đặt hợp nhất phiên bản, lan truyền hiệu lực (L3); kiểm chứng hàm snapshot trên 100 truy vấn |
| 4. Xây dựng bộ dữ liệu ViLexTime | 27/10 – 16/11/2026 | Kiểm định chéo 300 câu, tính hệ số đồng thuận Cohen κ; phối hợp cố vấn chuyên môn luật (T5, T6) | Chủ trì quy trình diff-driven: so khớp phiên bản, trích xuất khác biệt, sinh câu hỏi |
| 5. Cài đặt & đánh giá đường cơ sở | 17/11 – 30/11/2026 | Cài đặt và chạy B1–B4 (mô hình không truy xuất, BM25, dense retrieval, hybrid + reranker) | Cài đặt và chạy B5–B7 (GraphRAG phi thời gian, KG phân cấp, lọc siêu dữ liệu); tổng hợp điểm quyết định |
| 6. Xây dựng hệ thống đề xuất | 01/12 – 21/12/2026 | Cài đặt truy xuất có ràng buộc thời gian, mở rộng theo đồ thị (L4) | Cài đặt sinh câu trả lời có ràng buộc trích dẫn, Temporal Verifier, giao diện minh họa (L5) |
| 7. Thực nghiệm & phân tích | 22/12/2026 – 04/01/2027 | Thực hiện ablation A1–A4; phân tích lỗi trên miền chính (giao thông đường bộ) | Thực hiện ablation A5–A7; thí nghiệm chuyển miền sang Bảo hiểm xã hội |
| 8. Viết bài báo khoa học | 05/01 – 11/01/2027 | Viết phần phương pháp và thực nghiệm; chuẩn bị nộp hội nghị | Viết phần tổng quan, kết quả và thảo luận; chuẩn bị nộp hội nghị |
| 9. Hoàn thiện khóa luận | 12/01 – 01/02/2027 | Hoàn thiện chương trình demo phần hệ thống; viết chương liên quan; chuẩn bị bảo vệ | Hoàn thiện chương trình demo phần dữ liệu/đánh giá; viết chương liên quan; chuẩn bị bảo vệ |

| Xác nhận của CBHD<br>(Ký tên và ghi rõ họ tên) | TP. HCM, ngày …… tháng …… năm 2026<br>Sinh viên<br>(Ký tên và ghi rõ họ tên) |
| --- | --- |
