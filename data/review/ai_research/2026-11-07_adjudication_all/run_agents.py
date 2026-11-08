"""Invoke the requested Claude legal-adjudicator on frozen five-case packets."""
import argparse
import concurrent.futures
import datetime
import hashlib
import json
import re
import subprocess
from pathlib import Path

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[3]


def run(packet):
    raw = WORK / "raw" / (packet.stem + ".md")
    if raw.exists():
        return {"batch": packet.stem, "status": "preserved_existing_reply"}
    records = [json.loads(line) for line in packet.read_text().splitlines()]
    prompt = f"""Thực hiện vai trò .claude/agents/legal-adjudicator.md cho đúng {len(records)} ca.
Đọc đúng file agent, hai skill .claude/skills/vn-legal-research/SKILL.md và
.claude/skills/vilextime-ai-labeling/SKILL.md (đọc trực tiếp, không dựa vào preload),
docs/vilextime-dinh-nghia.md và docs/vilextime-annotation.md.
Chỉ đọc thêm packet {packet.relative_to(ROOT)}; không đọc nhãn/lô/kết quả hệ khác.
Packet có nhãn thô đã đóng băng, binding và hash. Trọng tài được xem cả A/B.
Đây là phạm vi Q1–Q4 VÀ mã reason khác nhau, hoặc unresolved cũ cần tra lại.
Không mặc định phiếu dài hơn hoặc đa số là đúng. Tự đối chiếu đủ bốn Q,
giải thích rõ lập luận A/B nào được nguồn chứng minh/bác bỏ, từng mốc.
Mở lại nguồn thật bằng WebFetch/WebSearch; API vbpl có thể lấy với ItemID
từ sources của record. official trong packet là excerpt đã lấy từ nguồn gốc,
không phải kiểm chứng độc lập mới; ghi rõ khi chỉ đọc excerpt. Pilot có thể thiếu
official, cần mở URL gốc. Kiểm nội dung điều hiệu lực, không dùng metadata ngày.
Lawgical không có trong runtime này: ghi rõ, dùng web/API nguồn chính thức.
Ngân sách mềm khoảng 15 lượt web/lô; ưu tiên gộp nguồn chung, nhưng cần thì tra đủ.
Nếu công cụ không mở nguồn hoặc chính sách gán còn thiếu, ghi unresolved thật,
không tự tạo quy tắc và không chọn A/B cho đủ số. Nếu một lỗi độc lập đã chắc
để loại dòng nhưng Q khác còn thiếu nguồn, vẫn ghi thiếu nguồn của nhãn đầy đủ;
không gọi cả phiếu sufficient chỉ vì verdict chắc chắn.

Chỉ trả MỘT khối ```jsonl gồm đúng {len(records)} object theo thứ tự packet,
không viết file. Mỗi object gồm:
case_id,run_id,lineage_id,worksheet_sha256,raw_a_sha256,raw_b_sha256 (chép từ packet),
disputed_fields (chép từ packet), disposition prefer_a|prefer_b|both_wrong|unresolved,
proposed_label null nếu chưa đủ căn cứ, nếu đề xuất đầy đủ thì gồm
q1,q1_reason,q2,q2_reason,q3,q3_reason,q4,q4_reason,verdict,quote,search_log,note,
evidence_status và evidence. Giữ nguyên taxonomy thẻ 4.0 (không sáng tác reason).
verdict dat CHỈ khi dung/co/co/khong. Các câu thuận lợi reason rỗng.
Mỗi evidence có url thực đã mở, source_tier official|worksheet|secondary|snippet,
document_number,provision,as_of,quote nguyên văn ngắn,accessed_at (unknown nếu không biết).
Nếu đã đủ để giải quyết, evidence_status=sufficient; nếu không unresolved,
proposed_label có thể null hoặc phiếu tentative insufficient được đánh dấu rõ.
reasoning: tiếng Việt ngắn gọn nhưng nêu từng điểm tranh chấp, đối chiếu A và B.
evidence: các nguồn quyết định đã mở (không bịa URL), open_questions: danh sách còn thiếu.
labeler=ai-adjudicator,label_origin=ai,verification_status=not_verified,
human_adjudication_required=true. Không giả luật sư hoặc xác nhận CMT.
Sau đó MỘT khối ```json provenance: agent/model thực, input file, web calls,
nguồn lỗi, giới hạn, mốc truy cập; nếu không biết thì unknown. Không chép placeholder.
"""
    (WORK / "prompts").mkdir(exist_ok=True)
    (WORK / "raw").mkdir(exist_ok=True)
    (WORK / "metadata").mkdir(exist_ok=True)
    (WORK / "results").mkdir(exist_ok=True)
    prompt_path = WORK / "prompts" / (packet.stem + ".md")
    prompt_path.write_text(prompt)
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    print("START", packet.stem, started, flush=True)
    command = ["claude", "-p", "--agent", "legal-adjudicator", "--model", "claude-opus-5-5",
               "--output-format", "json", "--no-session-persistence", "--strict-mcp-config",
               "--mcp-config", '{"mcpServers":{}}', "--allowedTools", "Read", "Glob", "Grep",
               "WebSearch", "WebFetch", "ToolSearch"]
    try:
        result = subprocess.run(command, input=prompt, text=True, capture_output=True,
                                cwd=ROOT, timeout=1800)
        data = json.loads(result.stdout)
        reply = data.get("result", "")
        blocks = re.findall(r"```jsonl\s*\n(.*?)```", reply, re.S)
        success = result.returncode == 0 and not data.get("is_error") and len(blocks) == 1
        record = {key: data.get(key) for key in
                  ("session_id", "is_error", "modelUsage", "usage", "total_cost_usd", "duration_ms", "permission_denials")}
        record.update(batch=packet.stem, started_at=started,
                      finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                      input_sha256=hashlib.sha256(packet.read_bytes()).hexdigest(),
                      prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
                      agent_file=".claude/agents/legal-adjudicator.md",
                      status="completed" if success else "failed", returncode=result.returncode)
        if success:
            with raw.open("x") as out:
                out.write(reply)
            parsed = [json.loads(line) for line in blocks[0].splitlines() if line.strip()]
            assert [item["case_id"] for item in parsed] == [item["case_id"] for item in records]
            with (WORK / "results" / (packet.stem + ".jsonl")).open("x") as out:
                out.write("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in parsed))
        else:
            record.update(error=reply, stderr=result.stderr[-2000:])
    except Exception as error:
        record = {"batch": packet.stem, "status": "failed", "error": str(error), "started_at": started}
    metadata = WORK / "metadata" / (packet.stem + ".json")
    attempt = 1
    while metadata.exists():
        attempt += 1
        metadata = WORK / "metadata" / (packet.stem + f".attempt{attempt}.json")
    with metadata.open("x") as out:
        json.dump(record, out, ensure_ascii=False, indent=2)
    print("DONE", packet.stem, record["status"], flush=True)
    return {key: record.get(key) for key in ("batch", "status", "error", "total_cost_usd")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", nargs="*")
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    packets = sorted((WORK / "input").glob("batch*.jsonl"))
    if args.batch:
        packets = [p for p in packets if p.stem in args.batch]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        results = list(executor.map(run, packets))
    print(json.dumps(results, ensure_ascii=False, indent=2), flush=True)
