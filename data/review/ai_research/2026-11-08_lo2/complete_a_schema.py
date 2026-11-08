"""Ask Claude to complete omitted Q fields, preserving its original replies.

No B labels and no additional web budget. Outputs are separate patches bound
to the original A reply and packet; this is annotation completion, not inference
by the schema adapter. Run only after all twelve A replies exist.
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[3]


def main():
    cases = []
    for inp in sorted((RUN / "input").glob("chunk*.jsonl")):
        raw = RUN / "raw" / f"a_{inp.stem}.md"
        packets = {p["worksheet_sha256"]: p for p in map(json.loads, inp.read_text().splitlines())}
        block = re.findall(r"```jsonl\s*\n(.*?)```", raw.read_text(), re.S)
        assert len(block) == 1
        for label in map(json.loads, filter(str.strip, block[0].splitlines())):
            missing = [q for q in ("q1", "q2", "q3", "q4") if q not in label]
            if missing and "rows" not in label:
                cases.append({"missing": missing, "own_label": label,
                              "packet": packets[label["worksheet_sha256"]],
                              "original_raw": raw.name,
                              "original_raw_sha256": hashlib.sha256(raw.read_bytes()).hexdigest()})
    assert cases, "No omitted Q fields requiring Claude completion"
    dest = RUN / "schema_completion"
    dest.mkdir(exist_ok=False)
    (dest / "cases.json").write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n")
    prompt = """Bạn là AI-A Claude, hoàn tất các trường Q bị bỏ sót trong chính nhãn của AI-A.
Đây không phải hòa giải: không nhận hoặc đọc nhãn AI-B, dự đoán hệ hay hồ sơ khác.
Chỉ đọc docs/vilextime-dinh-nghia.md, docs/vilextime-annotation.md,
.claude/skills/vilextime-ai-labeling/SKILL.md và .claude/skills/vn-legal-research/SKILL.md.
Phải đọc các file skill này rõ ràng, không giả định chúng đã preload.
Nguồn của từng ca được cung cấp đầy đủ bên dưới, đúng packet của lượt gán gốc.
Lượt gốc đã dùng hết 6 lượt web. Không tra web hay mở thêm bất kỳ nguồn/file nào.
Chỉ hoàn tất Q bị thiếu bằng đánh giá độc lập của chính bạn; không đổi Q đã có.
Không đủ căn cứ: vẫn chọn mức tốt nhất theo thẻ, ghi [phân vân] trong note_append;
không bịa nguồn hoặc biến không truy cập được thành kết luận pháp lý chắc chắn.
Trả một khối jsonl, mỗi ca một object: lineage_id, worksheet_sha256, các Q bị thiếu
và Q_reason tương ứng, note_append (rỗng nếu không cần thêm), evidence_status.
Không ghi Q đã có. evidence_status chỉ được giữ hoặc hạ so với nhãn gốc;
nếu Q mới chưa đủ căn cứ, ghi insufficient, không giữ sufficient của phần cũ.
Q4 = khong / co / khong_chac. Reason khong rỗng; co dùng
superseded_by_other_norm|restructuring_2025|transitional_rule|relocated;
khong_chac dùng relocation_unclear và phải nêu điểm chưa rõ trong note_append.
Sau đó một khối json provenance: model thực tế, blinding, additional_web_calls=0,
nguồn đã đọc và hạn chế. Chỉ hai khối này; không viết file.
Ca đầu vào (own_label là chính nhãn gốc của bạn, không phải nhãn đối phương):
""" + json.dumps(cases, ensure_ascii=False)
    (dest / "prompt.md").write_text(prompt)
    cmd = ["claude", "-p", "--agent", "legal-annotator-a", "--model", "claude-opus-5-5",
           "--output-format", "json", "--no-session-persistence", "--strict-mcp-config",
           "--mcp-config", '{"mcpServers":{}}', "--allowedTools", "Read", "Glob", "Grep"]
    result = subprocess.run(cmd, input=prompt, text=True, capture_output=True, cwd=ROOT, timeout=1200)
    meta = json.loads(result.stdout)
    (dest / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
    assert result.returncode == 0 and not meta.get("is_error"), meta.get("result")
    text = meta["result"]
    (dest / "reply.md").write_text(text)
    blocks = re.findall(r"```jsonl\s*\n(.*?)```", text, re.S)
    assert len(blocks) == 1
    patches = [json.loads(line) for line in blocks[0].splitlines() if line.strip()]
    assert len(patches) == len(cases)
    expected = {c["packet"]["record"]["lineage_id"]: c for c in cases}
    assert {r["lineage_id"] for r in patches} == set(expected)
    for patch in patches:
        case = expected[patch["lineage_id"]]
        assert patch["worksheet_sha256"] == case["own_label"]["worksheet_sha256"]
        allowed = {"lineage_id", "worksheet_sha256", "note_append", "evidence_status"}
        rank = {"unavailable": 0, "insufficient": 1, "sufficient": 2}
        assert rank[patch["evidence_status"]] <= rank[case["own_label"]["evidence_status"]]
        for q in case["missing"]:
            assert q in patch and q + "_reason" in patch
            allowed.update((q, q + "_reason"))
        assert set(patch) <= allowed
        patch.update(original_raw=case["original_raw"], original_raw_sha256=case["original_raw_sha256"])
    (dest / "patches.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in patches))
    print(json.dumps({"completed_cases": len(patches), "additional_web_calls": 0}))


if __name__ == "__main__":
    main()
