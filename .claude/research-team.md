# Nhóm agent nghiên cứu khóa luận

Cấu hình dự án ở `.claude/agents/`, dùng với Claude Code. Ba skill dùng chung ở
`.claude/skills/`; không phụ thuộc skill chỉ có trong Codex hoặc đường dẫn máy
cá nhân. Kiểm tra CLI tại lúc setup: Claude Code 2.1.319 (06/11/2026).

| Agent | Vai trò | Khả năng ghi |
|---|---|---|
| `research-lead` | Phiên chính điều phối và lưu artifact | Có |
| `legal-annotator-a` | AI-A tự kiểm Q1–Q4 | Không có Bash/Write/Edit |
| `legal-annotator-b` | AI-B, cùng skill/công cụ/model cấu hình với A | Không có Bash/Write/Edit |
| `legal-adjudicator` | Tra lại nguồn, đề xuất hòa giải sau đo đồng thuận thô | Không có Bash/Write/Edit |
| `experiment-executor` | Code, môi trường, scripts eval, chạy được phép | Có |
| `evidence-gate` | Truy nguồn từng số, chấm lại offline, rà leak/câu chữ | Không có Write/Edit; Bash theo phạm vi audit |
| `vn-law-verifier` | Tra hiệu lực/nội dung luật, dòng lệch gold, ca VBHN | Chỉ đọc |
| `thesis-critic`, `lit-scout` | Phản biện như hội đồng; tìm và kiểm tài liệu | Chỉ đọc |
| `data-clerk` | Việc cơ học: dựng phiếu, import/reveal, audit, đếm | Có; cấm điền nhãn/gold/`dong_y` |

Model (cập nhật 10/11/2026, đặt ở frontmatter): lead, `legal-adjudicator`, `evidence-gate`
= `claude-opus-5-5`; annotator A, verifier, executor, critic, scout = `claude-sonnet-5-5`;
`data-clerk` = `claude-haiku-5-5`; AI-B vẫn chạy Codex CLI. Cặp làm–kiểm khác model
(executor sonnet → gate opus). Lead đổi model từng lượt bằng tham số `model`.

Hai agent nhãn và agent thẩm phán cùng preload `vn-legal-research` và
`vilextime-ai-labeling`. Executor/gate cùng preload `experiment-evidence`, nhưng
khác quyền và ngữ cảnh. Ghi model thực tế mỗi lượt,
không suy rằng tên vai trò tạo nhiều model độc lập. Từ silver phần 5 (CMT 06/11),
AI-B chạy bằng Codex CLI để hai bên khác model; xem `research-lead.md` bước 3.

## Bắt đầu

Từ gốc repo:

```bash
claude --agent research-lead
```

Giao việc, ví dụ (thay placeholder bằng input/lô được phép dùng):

> Chuẩn bị lượt nhãn AI riêng cho worksheet `<file>`, ID `<danh sách>`. Kiểm
> quyền truy cập Lawgical/web của cả hai annotator, băm input, giao hai phiên mù
> mới cùng dữ liệu, khóa a.jsonl/b.jsonl. Đo AC1/p_neg/κ từng Q và verdict trước
> khi dùng legal-adjudicator; giữ nguyên nhãn người và release.

> Dùng experiment-executor triển khai `<thay đổi>` và kiểm trên dev. Sau khi có
> artifact, dùng một phiên evidence-gate mới kiểm mọi số trong `<báo cáo>`, tái
> chấm predictions đã lưu trên mẫu dev, trả bảng claim → nguồn và verdict. Chưa
> chạy bộ test cuối khi cổng ADR áp dụng chưa đủ.

Có thể gọi trực tiếp một vai bằng `claude --agent evidence-gate` hoặc nhờ phiên
chính dùng agent theo tên. Coordinator phải chạy ở phiên chính để dùng allowlist
`Agent(...)`. Một lượt chỉ cần vai liên quan, không phải luôn gọi cả nhóm.

## MCP và plugin

Ba agent pháp luật có cùng danh sách tool Lawgical (tìm/đọc và xem quota). Không cài plugin marketplace không rõ nguồn, không bịa
RegAI/Pháp Luật Tra Cứu server khi chưa xác minh endpoint và công cụ. Các plugin
tài khoản đã có (như academic-research-skills/research-integrity) không phải phụ
thuộc bắt buộc: hai annotator dùng cùng bộ skill được commit trong repo.

Ba agent pháp luật dùng **connector Lawgical của tài khoản claude.ai** (tool
`mcp__claude_ai_Lawgical_vn__*`), không dùng MCP inline nữa. Ngày 06/11/2026, MCP
inline `legal.lawgical.vn/mcp` không nạp được trong subagent (ToolSearch không ra
tool), còn connector tài khoản trả `get_account_status` bình thường. Connector chỉ
có khi đăng nhập đúng tài khoản claude.ai đã gắn Lawgical; hạn mức khoảng 20
lượt/ngày dùng chung với phiên chính.

Toàn văn chính thức đọc qua API JSON của CSDL quốc gia về pháp luật
(`vbpl-bientap-gateway.moj.gov.vn/api/qtdc/public/doc/<ItemID>`), không tốn lượt
Lawgical; chi tiết trong skill `vn-legal-research`.

Trước mỗi lượt, điều phối gọi `get_account_status`, chia ngân sách lượt Lawgical
đều cho A và B, ghi vào lời giao việc. Nếu một bên không có tool thì bên kia cũng
không dùng; ghi lệch vào provenance.

Kết nối và quota có thể dùng chung tài khoản; không coi mỗi agent có quota riêng.
Việc xác thực không được thực hiện tự động bởi các file cấu hình này.

## Nhãn, độc lập và cổng kết luận

Từ 06/11/2026 (CMT; định nghĩa §6 và hướng dẫn §5 sửa 06/11): bộ test cuối do
AI-A, AI-B gán mù độc lập, `legal-adjudicator` đề xuất cho dòng lệch, CMT duyệt
mọi dòng có xem nhãn AI và chốt; dòng CMT ghi `[phân vân]` do luật sư chốt. Gold mù
vẫn do người gán, không xem gợi ý AI; câu gold của một người không đưa người đó
duyệt trước khi họ nộp gold.

Nhận nhãn qua lời đáp; chỉ lead lưu ở `data/review/ai_research/<run_id>/` gồm
`a.jsonl`, `b.jsonl`, provenance, số đo và đề xuất hòa giải riêng. Không tạo dữ
liệu giả để sẵn trong thư mục này. Hash nhãn gốc trước hòa giải; không ghi vào
phiếu A/B hay release chính thức. Các trường AI giữ `not_verified`.

AC1 ≥ 0,80, p_neg ≥ 0,60, κ báo kèm theo hướng dẫn; tính từng Q1–Q4 và nhãn suy
ra, theo nhóm/phiên bản và đủ mẫu âm. Không có đảm bảo sẽ đạt. Chưa đạt thì báo
thất bại, hiệu chuẩn trên câu mới; không sửa nhãn cũ hay lọc ca lệch để đạt cổng.
Đồng thuận AI–AI cao vẫn chưa chứng minh độ đúng hoặc thay được người–người.

MCP/tool allowlist là cấu hình runtime; giới hạn đường đọc và chống lộ nhãn là
chỉ dẫn hành vi. `Read` vẫn có thể mở file khác trong workspace, Bash của gate
vẫn có khả năng ghi. Chưa có sandbox/hook cưỡng chế cách ly file hay CI gate.
Muốn cách ly cứng cần môi trường chỉ chứa input được phép, quyền OS/container
riêng và lần kiểm chứng độc lập; không tự nhận cấu hình prompt đã làm được điều đó.

Evidence Gate trả PASS/FAIL/BLOCKED theo phạm vi đã kiểm, có bảng truy vết và
lệnh tái lập. Không cho phép né cổng test, không hứa phát hiện hết contamination
hoặc overfitting. Thiếu artifact thì số đó chưa đủ bằng chứng.

## Kiểm tra lúc setup (06/11/2026)

Đã parse YAML của sáu agent và ba skill, đối chiếu A/B có cùng cấu hình năng
lực, kiểm đường dẫn tham chiếu và tên agent không trùng. Kiểm tra code được
các vai tái sử dụng bằng lệnh offline sau: **64 passed**.

```bash
.venv/bin/python -m pytest -q tests/test_crosscheck.py tests/test_score_vilextime.py tests/test_confirm_vilextime.py tests/test_final_run.py
```

Đây là kiểm tra cấu hình tĩnh và các primitive sẵn có; chưa kiểm runtime nạp
agent/preload skill, chưa xác thực hoặc gọi MCP, chưa có lượt nhãn AI mới và
chưa chạy gate trên báo cáo thực tế. Chỉ sau preflight và một lượt pilot được
giao mới có bằng chứng về công cụ khả dụng và đồng thuận thực đo.
