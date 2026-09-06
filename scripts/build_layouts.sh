#!/usr/bin/env bash
set -euo pipefail
for s in 32 64 128 256; do
  echo "Build ${s} MiB layout with SAME row-group, order, codec, schema, partitioning."
done
