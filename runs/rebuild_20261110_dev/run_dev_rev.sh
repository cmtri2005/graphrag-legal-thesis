#!/usr/bin/env bash
# Luồng phụ: chạy các hệ từ cuối danh sách ngược lên, song song với run_dev.sh; cùng lệnh và tham số.
# Prompt ghi ra file tạm rồi mv (nguyên tử) để luồng chính thấy file đủ thì bỏ qua export;
# api_generate bỏ qua câu đã có trả lời. Dừng khi luồng chính còn cách hệ kế tiếp dưới 2 hệ.
set -u
O=runs/rebuild_20261110_dev; R=data/vilextime_dataset_h6/vilextime.jsonl; M=gpt-4o-mini-2024-07-18; PY=.venv/bin/python
read -ra ALL <<< "$(PYTHONPATH=src $PY -c "from vilexgraph.framework import systems as s; print(*s.FINAL_GENERATION, *s.DEV_ONLY)")"
main_pos() { local last; last=$(grep '^=== ' $O/run_dev.log | tail -1 | awk '{print $2}'); for i in "${!ALL[@]}"; do [ "${ALL[$i]}" = "$last" ] && echo $i; done; }
mkdir -p $O/prompts_tmp
for (( i=${#ALL[@]}-1; i>=0; i-- )); do
  s=${ALL[$i]}; m=$(main_pos)
  [ $(( i - m )) -ge 2 ] || { echo "STOP at $s (main at ${ALL[$m]})"; break; }
  echo "=== $s $(date +%T)"
  if [ ! -f "$O/prompts/$s.jsonl" ]; then
    $PY scripts/eval/colab_b1.py export --release "$R" --system "$s" --split dev --as-of-strategy giua_khoang \
        --limit 0 --b2 --hybrid --out "$O/prompts_tmp/$s.jsonl" && mv "$O/prompts_tmp/$s.jsonl" "$O/prompts/$s.jsonl" \
        || { echo "FAIL export $s"; continue; }
  fi
  sha=$(sha256sum "$O/prompts/$s.jsonl" | cut -c1-12)
  $PY scripts/eval/api_generate.py --prompts "$O/prompts/$s.jsonl" --provider openai --model "$M" --out-dir "$O/raw" || { echo "FAIL api $s"; continue; }
  $PY scripts/eval/colab_b1.py import --prompts "$O/prompts/$s.jsonl" --raw "$O/raw/${s}__${M}__${sha}.jsonl" --out "$O/dev/$s.jsonl" || echo "FAIL import $s"
done
echo "REV DONE $(date +%T)"
