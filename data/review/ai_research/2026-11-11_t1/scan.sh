#!/bin/bash
# Quét mọi nhắc tới provision:<uuid> trong các nơi phải loại (chỉ đọc). Ghi exclusion_tokens.txt
R=/home/trica/UIT_Thesis/graphrag-legal-thesis; W=/home/trica/vilextime_loc/gan_t1
cd $R
{
 grep -rhaoE 'provision:[0-9a-f-]{36}' runs data/review data/vilextime data/vilextime_dataset data/vilextime_dataset_h6 data/derived/vilextime_test2 data/derived/vilextime/selected.jsonl 2>/dev/null
 find data/review runs -name '*.xlsx' -print0 | xargs -0 -I{} sh -c 'unzip -p "{}" 2>/dev/null | grep -aoE "provision:[0-9a-f-]{36}"'
} | sort -u > $W/exclusion_tokens.txt
wc -l $W/exclusion_tokens.txt
