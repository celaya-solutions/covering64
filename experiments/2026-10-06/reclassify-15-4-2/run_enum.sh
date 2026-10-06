#!/bin/sh
# Document:    Parallel Enumeration Runner
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-06
# SHA256:      a5b27495e08d0d981814c1f71caf11fc7226f60e639b1d59d30528533d68818b
# Chain:       solana-mainnet
# Tx:          4EW18rDCoabbUzqG4ZcLbU4J7bXiuPjHoMWR98yBAiJPcX6kjcC6nUdJnvarJaxCMrtN8M3pzL1CZTmULsi2KAQD
# License:     CC BY 4.0 / Celaya Solutions

# Build enum_par and run K workers of one branching mode in parallel.
# usage: ./run_enum.sh MODE K SPLIT_LEVEL OUT_DIR
#   ./run_enum.sh 1 14 2 out/dfs1   lowest-index pair, the faster order
#   ./run_enum.sh 0 16 3 out/dfs0   most-constrained pair
# Each worker k writes OUT_DIR/s<k>.bin (19 uint16 masks per solution) and
# OUT_DIR/log<k>.txt. The summed solution count is printed at the end.
set -eu
cd "$(dirname "$0")"
mode=${1:-1}
k=${2:-14}
split=${3:-2}
outdir=${4:-out/dfs$mode}
cc -O2 -o enum_par enum_par.c
mkdir -p "$outdir"
rm -f "$outdir"/s*.bin "$outdir"/log*.txt
i=0
while [ "$i" -lt "$k" ]; do
    ./enum_par "$outdir/s$i.bin" "$mode" "$k" "$i" "$split" > "$outdir/log$i.txt" &
    i=$((i + 1))
done
wait
cat "$outdir"/log*.txt
awk '{for (f = 1; f <= NF; f++) {split($f, kv, "=");
        if (kv[1] == "solutions") s += kv[2];
        if (kv[1] == "nodes") n += kv[2];
        if (kv[1] == "time") {t = kv[2] + 0; c += t; if (t > m) m = t}}}
     END {printf "workers=%d solutions=%d nodes=%d cpu_seconds=%.1f slowest_worker=%.1fs\n",
          NR, s, n, c, m}' "$outdir"/log*.txt
