# sourced by the step scripts; dev rehearsal of the G4 command (README data/vilextime_final, "Chạy G4")
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
export PYTHONPATH=src HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
PY=.venv/bin/python; O=runs/final_rehearsal_g3_20261112; R=data/vilextime_dataset_h6/vilextime.jsonl; D=data
M=gpt-4o-mini-2024-07-18
FR="$PY scripts/eval/final_run.py --split dev --release $R --data $D --raw $O/raw --retrieval $O/retrieval"
