#!/bin/bash
set -e
R=/home/trica/UIT_Thesis/graphrag-legal-thesis; W=/home/trica/vilextime_loc/gan_t1; P=$R/.venv/bin/python; Q=questions_ext
export PYTHONDONTWRITEBYTECODE=1
A=()
for r in 1 2 3; do
  if [ $r != 1 ]; then
    $P $W/claude_task.py --kind q --guide $W/$Q/HUONG_DAN.md --input $W/$Q/viet_lai.r$((r-1)).jsonl --out $W/$Q/answers_$r.jsonl --log-dir $W/logs/qext$r --model haiku | tail -1
  fi
  A+=($W/$Q/answers_$r.jsonl)
  (cd $R && $P scripts/review/test2_packs.py qcheck --data data --out $W/$Q/packs --provider claude-code --model claude-haiku-5-5 --dest $W/$Q/chot_r$r.jsonl "${A[@]}") | tee $W/qcheck_ext$r.log
  cp $W/$Q/viet_lai.jsonl $W/$Q/viet_lai.r$r.jsonl
done
