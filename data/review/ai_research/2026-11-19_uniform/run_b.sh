#!/usr/bin/env bash
# AI-B = Codex CLI, blind to AI-A; same flags as supp18/run_b.sh (gpt-6.1-sol is refused for ChatGPT accounts).
set -u
D=data/review/ai_research/2026-11-19_uniform
mkdir -p $D/codex_logs $D/raw
for p in $D/prompts/*_ai-b.md; do
  n=$(basename $p); out=$D/raw/$n; [ -e "$out" ] && continue
  { echo "Thực hiện vai trò .claude/agents/legal-annotator-b.md (đọc đúng file này và các skill nó nêu). Không đọc bất kỳ file a_*, nhãn AI-A, hay thư mục khác ngoài input được nêu. Không viết file; trả lời theo đúng định dạng yêu cầu dưới đây."; echo; cat $p; } |
  codex exec -m gpt-6-luna -s read-only --ephemeral -c web_search=live -o "$out.tmp" - > $D/codex_logs/${n%.md}.log 2>&1
  [ -s "$out.tmp" ] && grep -q '```jsonl' "$out.tmp" && mv "$out.tmp" "$out"
done
ls -la $D/raw
