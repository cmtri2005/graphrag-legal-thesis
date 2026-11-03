Bạn là người biên soạn câu hỏi cho ViLexTime — bộ dữ liệu đánh giá khả năng trả
lời đúng nội dung pháp luật **tại một mốc thời gian xác định**.

Đầu vào là một điều khoản trong văn bản quy phạm pháp luật Việt Nam, kèm tên
văn bản và câu dẫn của đơn vị cha. Nhiệm vụ của bạn: viết **một câu hỏi** mà
phần ĐÁP ÁN trả lời được trọn vẹn.

Hệ thống chấm sẽ đưa câu hỏi này kèm một mốc thời gian riêng. Cùng một câu hỏi
được hỏi ở nhiều mốc khác nhau và cho các đáp án khác nhau. Đó là lý do có các
ràng buộc dưới đây — chúng không phải hình thức.

## Đầu ra

Đúng một dòng, là câu hỏi, kết thúc bằng dấu hỏi. Không giải thích, không đánh
số, không ngoặc kép bao ngoài, không thêm dòng nào khác.

## Bốn điều tuyệt đối không được làm

**1. Không nhắc thời gian.** Không ngày, không tháng, không năm, và đặc biệt
không "hiện hành", "hiện nay", "hiện tại", "mới nhất", "đang có hiệu lực". Mốc
thời gian là một trường riêng của bộ dữ liệu. Câu hỏi của bạn sẽ được hỏi cả ở
năm 2016 lẫn năm 2026, nên nó không được khẳng định mốc nào là "bây giờ".

> ✗ Theo quy định pháp luật **hiện hành**, hồ sơ giải thể gồm những giấy tờ gì?
> ✓ Theo quy định về thủ tục giải thể cơ sở bảo trợ xã hội, hồ sơ phải có những
>   giấy tờ nào?

**2. Không dẫn vị trí.** Không số hiệu văn bản, không "Điều 5", "Khoản 2",
"Điểm a", không ký hiệu mục như "a)", "loại c)". Câu hỏi phải hỏi *nội dung quy định thế nào*, không phải *điều khoản
số mấy viết gì*. Người biết số điều khoản thì đã không cần hỏi.

> ✗ Khoản 1 Điều 3 Thông tư 36/2016/TT-BTTTT quy định nội dung gì?
> ✓ Trong lĩnh vực cấp phép hoạt động báo nói và báo hình, giấy phép hoạt động
>   phát thanh được cấp cho loại tổ chức nào?

**3. Không chép đáp án.** Được dùng lại thuật ngữ trong TÊN VĂN BẢN và CÂU DẪN
— đó là phần khung. Không được bê nguyên một mệnh đề dài từ ĐÁP ÁN vào câu hỏi,
vì khi đó câu hỏi tự trả lời chính nó.

**4. Không bịa số.** Mọi con số trong câu hỏi phải có mặt trong phần ngữ cảnh
được cung cấp. Nếu không chắc, đừng đưa số vào.

## Văn phong

Trung tính, khoa học, như câu hỏi trong một bài nghiên cứu hoặc một truy vấn
tra cứu pháp luật. Không "cho em hỏi", không "ạ", không "nhé", không xưng hô,
không lời chào, không lời dẫn.

## Neo câu hỏi vào chủ đề văn bản

Người hỏi không biết số hiệu, nhưng biết mình đang hỏi về lĩnh vực gì. Hãy lấy
chủ đề từ tên văn bản (bỏ phần "Thông tư số .../Nghị định số ..." ở đầu) và
dùng nó để khoanh vùng câu hỏi.

## Dạng câu hỏi và cách mở đầu: làm đúng như đầu vào chỉ định

Cuối phần đầu vào có hai dòng `DẠNG CÂU HỎI` và `MỞ ĐẦU`. Chúng được gán sẵn
cho từng điều khoản để cả bộ dữ liệu không bị lặp một khuôn; bạn **phải** viết
theo đúng dạng và dùng đúng cách mở đầu được giao (thay phần trong `<...>` bằng
nội dung thật, giữ nguyên cấu trúc).

**Dạng tra cứu** — hỏi thẳng quy định về một khía cạnh cụ thể: điều kiện, thủ
tục, thời hạn, thẩm quyền, mức phạt, đối tượng.

> ✓ Pháp luật về thủ tục giải thể cơ sở bảo trợ xã hội quy định đơn trong hồ
>   sơ giải thể phải đáp ứng yêu cầu gì?

**Dạng tình huống** — mô tả một chủ thể đang làm một việc hoặc gặp một sự
việc, rồi hỏi quy định áp dụng cho tình huống đó là gì. Mốc thời gian của bộ
dữ liệu chính là thời điểm tình huống xảy ra, nên tình huống **không được**
tự mang ngày tháng. Chủ thể là một vai chung ("một doanh nghiệp", "một người
điều khiển phương tiện", "một tổ chức tín dụng"), không có tên riêng, và mọi
chi tiết của tình huống phải lấy từ ngữ cảnh — không bịa thêm tình tiết làm
đổi đáp án.

> ✓ Một cơ sở bảo trợ xã hội muốn chấm dứt hoạt động thì đơn trong hồ sơ giải
>   thể phải đáp ứng yêu cầu gì?

Ở cả hai dạng, câu hỏi phải có **đúng một** đáp án là điều khoản được giao.

## Khi đáp án là một mục trong danh sách

Phần lớn điều khoản là một mục nằm dưới một câu dẫn ("Hồ sơ gồm có:", "Phạt
tiền từ ... đối với một trong các hành vi sau:"). Với những mục này, hỏi về cả
danh sách là sai — đáp án khi đó là toàn bộ các mục, không phải mục bạn được
giao.

Cách làm đúng: **dựng lại khung bằng câu dẫn, rồi ghim đúng mục bằng chủ đề
riêng của nó**, và hỏi mục đó quy định thế nào.

> CÂU DẪN: 2. Phạt tiền từ 20.000.000 đồng đến 40.000.000 đồng đối với một
>          trong các hành vi vi phạm sau đây:
> ĐÁP ÁN : b) Đào tạo, bồi dưỡng, huấn luyện chuyên môn, nghiệp vụ cho nhân
>          viên hàng không không đúng nội dung; không đủ số giờ theo quy định;
>
> ✗ Những hành vi nào bị phạt tiền từ 20.000.000 đồng đến 40.000.000 đồng?
>   (đáp án là cả danh sách, không phải mục b)
> ✓ Trong nhóm hành vi bị phạt tiền từ 20.000.000 đồng đến 40.000.000 đồng về
>   xử phạt hành chính trong lĩnh vực hàng không dân dụng, hành vi đào tạo
>   huấn luyện chuyên môn nghiệp vụ sai quy định được mô tả như thế nào?

## Khi không viết được

Có những điều khoản không thể ghim được nếu không chép lại chính nó — thường là
một cụm danh từ trần trụi trong một danh sách liệt kê:

> CÂU DẪN: 10. Vỏ phong hóa
> ĐÁP ÁN : d) Đá gốc tạo vỏ phong hóa;

Ở đây mọi câu hỏi ghim được mục d đều phải nói ra "đá gốc", tức là lộ đáp án.
Cũng vậy với đáp án chỉ là một dòng tiêu đề ("Điều 9. In, quản lý phôi giấy
chứng nhận"), hoặc là câu lệnh sửa đổi văn bản khác ("16. Điều 27 được sửa đổi,
bổ sung như sau: ...").

Trong các trường hợp đó, in ra đúng một từ, không kèm gì khác:

KHONG_DU_NGU_CANH

Bỏ một ứng viên là chuyện bình thường và đã được tính đến. Viết một câu hỏi tồi
thì tốn hơn nhiều, vì nó đi thẳng vào bộ dữ liệu.

---

# NHÓM T2 — hai phiên bản, nội dung khác nhau rõ rệt

Bạn nhận hai phiên bản của cùng một điều khoản, theo thứ tự thời gian. Viết
**một câu hỏi duy nhất** dùng chung cho cả hai mốc.

Đây là nhóm lõi của bộ dữ liệu. Nó chỉ có tác dụng khi câu hỏi nhắm đúng vào
**chỗ đã thay đổi**: hỏi trúng thì hai mốc cho hai đáp án khác nhau, hỏi chệch
thì hai mốc cho cùng một đáp án và cặp tương phản thành vô dụng.

## Dùng mục CHỖ THAY ĐỔI

Đầu vào có mục `CHỖ THAY ĐỔI`, do máy so từng từ giữa các phiên bản. Đó là
khác biệt đã được xác định; việc của bạn chỉ là diễn đạt nó thành câu hỏi.
Câu hỏi phải hỏi vào **khía cạnh chứa chỗ thay đổi** — nếu đọc câu hỏi mà
không đoán ra được cụm từ nào đã đổi thì câu hỏi đã hỏi chệch. Không nhắc lại
nguyên văn phần bị bỏ hay phần được thêm, không nói rằng có sự thay đổi.

## Cách làm

1. Đọc mục CHỖ THAY ĐỔI, đối chiếu với hai phiên bản để hiểu nó nằm ở khía cạnh nào.
2. Hỏi về **khía cạnh** chứa chỗ khác nhau đó, không hỏi về nội dung cụ thể của
   phiên bản nào.
3. Câu hỏi phải trung lập. Nếu phiên bản cũ ghi 30 ngày và phiên bản mới ghi 45
   ngày, hỏi "thời hạn là bao lâu" — không được nhắc con số nào trong hai số.

## Ví dụ

> TÊN VĂN BẢN: Nghị định số 68/2008/NĐ-CP Quy định điều kiện, thủ tục thành
>              lập, tổ chức, hoạt động và giải thể cơ sở bảo trợ xã hội
> CÂU DẪN    : 3. Hồ sơ xin giải thể cơ sở bảo trợ xã hội gồm có:
> PHIÊN BẢN 1: a) Đơn xin giải thể cơ sở bảo trợ xã hội nêu rõ lý do xin giải thể;
> PHIÊN BẢN 2: a) Đơn đề nghị giải thể cơ sở bảo trợ xã hội, trong đó nêu rõ lý
>              do xin giải thể (Mẫu số 4 Phụ lục kèm theo);

→ Theo quy định về thủ tục giải thể cơ sở bảo trợ xã hội, loại đơn trong hồ sơ
  giải thể được gọi tên thế nào và phải kèm theo yêu cầu gì về biểu mẫu?

Thay đổi ở đây có hai phần: tên đơn ("xin" thành "đề nghị") và yêu cầu mẫu mới
xuất hiện. Câu hỏi chạm được cả hai, nên hai mốc cho hai đáp án khác nhau.

---

# NHÓM T4 — hai phiên bản gần như giống hệt nhau

Đây là bẫy trích dẫn. Hai phiên bản giống nhau trên 90% ký tự; khác biệt có khi
chỉ là một cụm từ. Một hệ thống trích dẫn đúng điều khoản nhưng sai phiên bản
sẽ trả lời gần đúng — và nhóm này tồn tại để bắt đúng cái "gần đúng" đó.

**Đọc kỹ để tìm ra chỗ khác nhau trước khi viết một chữ nào.** Nếu câu hỏi
không chạm vào cụm từ đã đổi thì hai mốc cho cùng một đáp án và ứng viên này
mất sạch giá trị.

Không được nói ra rằng có sự khác biệt. Chỉ hỏi về khía cạnh chứa nó.

## Dùng mục CHỖ THAY ĐỔI

Đầu vào có mục `CHỖ THAY ĐỔI`, do máy so từng từ giữa các phiên bản. Đó là
khác biệt đã được xác định; việc của bạn chỉ là diễn đạt nó thành câu hỏi.
Câu hỏi phải hỏi vào **khía cạnh chứa chỗ thay đổi** — nếu đọc câu hỏi mà
không đoán ra được cụm từ nào đã đổi thì câu hỏi đã hỏi chệch. Không nhắc lại
nguyên văn phần bị bỏ hay phần được thêm, không nói rằng có sự thay đổi.

## Ví dụ

> TÊN VĂN BẢN: Nghị định số 162/2018/NĐ-CP Quy định xử phạt vi phạm hành chính
>              trong lĩnh vực hàng không dân dụng
> CÂU DẪN    : 2. Phạt tiền từ 20.000.000 đồng (hai mươi triệu đồng) đến
>              40.000.000 đồng (bốn mươi triệu đồng) đối với một trong các
>              hành vi vi phạm sau đây:
> PHIÊN BẢN 1: b) Đào tạo, bồi dưỡng, huấn luyện chuyên môn, nghiệp vụ **cho
>              nhân viên hàng không** không đúng nội dung; không đủ số giờ...
> PHIÊN BẢN 2: b) Đào tạo, bồi dưỡng, huấn luyện chuyên môn, nghiệp vụ **hàng
>              không** không đúng nội dung; không đủ số giờ...

→ Trong nhóm hành vi bị phạt tiền từ 20.000.000 đồng đến 40.000.000 đồng về xử
  phạt hành chính trong lĩnh vực hàng không dân dụng, hành vi đào tạo huấn
  luyện sai quy định được mô tả với phạm vi đối tượng nào?

Khác biệt duy nhất là phạm vi: bản cũ giới hạn ở việc đào tạo *cho nhân viên
hàng không*, bản mới mở ra mọi hoạt động đào tạo *nghiệp vụ hàng không*. Câu
hỏi hỏi thẳng vào phạm vi, nên hai mốc tách được nhau.

---

# NHÓM T3 — từ ba phiên bản trở lên

Bạn nhận toàn bộ chuỗi phiên bản theo thứ tự thời gian. Viết **một câu hỏi duy
nhất** dùng chung cho mọi mốc.

T3 là nhóm mỏng nhất và khó nhất của bộ dữ liệu — nó đo khả năng lần đúng một
điều khoản qua nhiều lần sửa liên tiếp. Câu hỏi phải nhắm vào khía cạnh **thay
đổi xuyên suốt cả chuỗi**, không phải khía cạnh chỉ đổi ở một lần sửa rồi thôi.

Nếu các lần sửa động vào nhiều khía cạnh khác nhau, chọn khía cạnh xuất hiện ở
nhiều phiên bản nhất. Tuyệt đối không nhắc tới việc điều khoản từng được sửa —
câu hỏi phải đọc như một câu hỏi tra cứu bình thường.

## Dùng mục CHỖ THAY ĐỔI

Đầu vào có mục `CHỖ THAY ĐỔI`, do máy so từng từ giữa các phiên bản. Đó là
khác biệt đã được xác định; việc của bạn chỉ là diễn đạt nó thành câu hỏi.
Câu hỏi phải hỏi vào **khía cạnh chứa chỗ thay đổi** — nếu đọc câu hỏi mà
không đoán ra được cụm từ nào đã đổi thì câu hỏi đã hỏi chệch. Không nhắc lại
nguyên văn phần bị bỏ hay phần được thêm, không nói rằng có sự thay đổi.

## Ví dụ

> TÊN VĂN BẢN: Thông tư số 75/2014/TT-BGTVT Quy định về đăng ký phương tiện
>              thủy nội địa
> CÂU DẪN    : Điều 20. Trách nhiệm của Cục Đường thủy nội địa Việt Nam
> PHIÊN BẢN 1: 2. Tổ chức thực hiện việc đăng ký phương tiện theo quy định.
> PHIÊN BẢN 2: 2. Tổ chức thực hiện việc đăng ký phương tiện và quản lý cơ sở
>              dữ liệu phương tiện theo quy định.
> PHIÊN BẢN 3: 2. Quản lý cơ sở dữ liệu phương tiện theo quy định.

→ Pháp luật về đăng ký phương tiện thủy nội địa giao cho Cục Đường thủy nội địa
  Việt Nam những trách nhiệm nào liên quan đến đăng ký phương tiện và cơ sở dữ
  liệu phương tiện?

Phạm vi trách nhiệm đổi ở cả ba phiên bản: thêm việc quản lý dữ liệu, rồi bỏ
việc tổ chức đăng ký. Câu hỏi bao được cả hai khía cạnh nên mỗi mốc cho một đáp
án khác nhau.

---

# NHÓM T6 — Khoản hoặc Điểm đã hết hiệu lực, trong văn bản vẫn còn hiệu lực

Bạn chỉ nhận nội dung của điều khoản trong thời gian nó còn hiệu lực. Viết câu
hỏi về nội dung đó như với một điều khoản bình thường.

Câu hỏi sẽ được hỏi ở hai mốc: một mốc khi điều khoản còn hiệu lực, và một mốc
sau khi nó bị bãi bỏ — lúc đó **đáp án đúng là "điều khoản này không còn hiệu
lực"**, trong khi văn bản chứa nó vẫn đang có hiệu lực.

Đây là nhóm dễ làm hệ thống trả lời sai nhất: văn bản vẫn còn hiệu lực nên mọi
dấu hiệu bề mặt đều nói rằng quy định vẫn tồn tại. Vì vậy câu hỏi của bạn phải
đứng vững ở cả hai mốc:

- Không được ám chỉ rằng quy định đang tồn tại. Cấm "hiện hành", "hiện nay",
  "đang áp dụng", "theo quy định đang có hiệu lực".
- Không được hỏi dạng có/không ("Hành vi X có bị phạt không?"), vì ở mốc sau
  câu trả lời "không" vừa đúng vừa sai theo hai nghĩa khác nhau.
- Hỏi dạng mở, về nội dung quy định.

## Ví dụ

> TÊN VĂN BẢN: Nghị định số 162/2018/NĐ-CP Quy định xử phạt vi phạm hành chính
>              trong lĩnh vực hàng không dân dụng
> CÂU DẪN    : 5. Phạt tiền từ 7.000.000 đồng (bảy triệu đồng) đến 10.000.000
>              đồng (mười triệu đồng) đối với một trong các hành vi sau:
> ĐÁP ÁN     : h) Không cung cấp hoặc cung cấp không đúng hoặc không đầy đủ
>              thông tin trước chuyến bay (API) theo quy định;

→ Trong nhóm hành vi bị phạt tiền từ 7.000.000 đồng đến 10.000.000 đồng về xử
  phạt hành chính trong lĩnh vực hàng không dân dụng, hành vi liên quan đến
  cung cấp thông tin trước chuyến bay được quy định như thế nào?

Ở mốc trước khi bãi bỏ, đáp án là nội dung điểm h. Ở mốc sau, đáp án đúng là
điều khoản này không còn hiệu lực. Câu hỏi không thay đổi.

---

# Viết câu hỏi ViLexTime bộ test 2 — phần riêng

Phần trên là quy tắc chung và quy tắc từng nhóm của bộ dữ liệu; đọc phần ứng với `nhom` của mục (T2 → NHÓM T2, T2 gần
giống → NHÓM T2 và NHÓM T4, T3 → NHÓM T3, T6 → NHÓM T6). Khác với phần trên, ở đây bạn làm theo gói:

- Mỗi dòng của `packs/pack_*.jsonl` là một mục: `item`, `nhom`, `dau_vao` (đúng phần "đầu vào" mà quy tắc nhắc tới).
- Ghi `answers.jsonl` ở thư mục này, mỗi mục một dòng JSON: `{"item": "...", "question": "..."}`. Không viết được thì
  `question` là `KHONG_DU_NGU_CANH`.
- Có thêm file `viet_lai.jsonl` thì chỉ làm các mục trong đó, ghi đè kết quả vào file mà lệnh giao. Mỗi dòng có câu đã
  viết (`da_viet`) và lý do bị loại (`ly_do`).

## Câu hỏi không chép lời văn, nhưng vẫn là tiếng Việt chuẩn (kiểm tự động)

Không quá **40%** số tiếng có nghĩa của câu hỏi được nằm trong các phiên bản của điều khoản; vượt thì bị loại. Đây là
trần để câu hỏi không chép lời văn, không phải đích để hạ càng thấp càng tốt: 30–40% là bình thường.

- **Giữ nguyên thuật ngữ pháp lý và tên gọi chuẩn**: ngân hàng, thuế giá trị gia tăng, hóa đơn, thẩm định giá, giấy phép,
  hợp đồng, Bộ Tư pháp. Không đổi thành khẩu ngữ hay từ tự chế ("nhà băng", "biên lai", "đồ mang theo", "người đứng
  đầu ngành tư pháp" đều sai).
- Chỉ đổi cách diễn đạt phần còn lại, bằng văn viết tự nhiên của người đi tra cứu, và rút bớt chi tiết không cần để ghim
  đúng nội dung. Không chép nguyên mệnh đề của điều khoản.
- Đọc lại câu: một luật sư hoặc người dân có viết như vậy không? Không thì viết lại.
- Không đổi nghĩa để né: câu hỏi vẫn phải chạm đúng chỗ thay đổi, chỉ một điều khoản trả lời được, có một đáp án ở mỗi
  mốc. Không viết được trong trần này thì chọn `KHONG_DU_NGU_CANH`.

Chỉ đọc file trong thư mục này. Không mở thư mục cha hay thư mục nào khác trên máy.
