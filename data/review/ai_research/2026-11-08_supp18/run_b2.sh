#!/usr/bin/env bash
# AI-B = Codex, blind to AI-A: read-only sandbox, ephemeral, only the B prompt + agent spec.
set -u
D=data/review/ai_research/2026-11-08_supp18
mkdir -p $D/codex_logs
for n in ${CHUNKS:-01 02}; do
  out=$D/raw/b_chunk$n.md; [ -e "$out" ] && continue
  { echo "Thực hiện vai trò .claude/agents/legal-annotator-b.md (đọc đúng file này, và đọc trực tiếp hai skill .claude/skills/vn-legal-research/SKILL.md, .claude/skills/vilextime-ai-labeling/SKILL.md cùng docs/vilextime-dinh-nghia.md, docs/vilextime-annotation.md). Không đọc bất kỳ file a_*, nhãn AI-A, hay thư mục khác ngoài input được nêu. Không viết file; trả lời theo đúng định dạng yêu cầu dưới đây."; echo; cat $D/prompts/chunk${n}_ai-b.md; } |
  codex exec -m gpt-6-luna -s read-only --ephemeral -c web_search=live -o "$out.tmp" - > $D/codex_logs/b_chunk$n.log 2>&1 &
done
wait
for n in ${CHUNKS:-01 02}; do [ -s $D/raw/b_chunk$n.md.tmp ] && grep -A1 '```jsonl' $D/raw/b_chunk$n.md.tmp | grep -q lineage_id && grep -q '```jsonl' $D/raw/b_chunk$n.md.tmp && mv $D/raw/b_chunk$n.md.tmp $D/raw/b_chunk$n.md; done
ls -la $D/raw
