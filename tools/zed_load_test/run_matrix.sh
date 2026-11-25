#!/usr/bin/env bash
# Run zed_load_test.py over a fixed list of camera configurations and save all results.
#
# Part of tools/zed_load_test (see README.md). Each line in CONFIGS below is one run of
# about 45 s (opening the cameras + 5 s warm-up + 30 s measuring). The whole list takes
# about 10 minutes, longer the first time a NEURAL depth mode is used (the SDK optimises
# its neural network for this Jetson once, which can take several minutes).
#
# Usage (on the Jetson, with the cameras plugged in):
#   ./run_matrix.sh [output_dir]
# Output: <output_dir>/results.jsonl, results.md (table) and system.txt (setup details).

set -euo pipefail

OUT_DIR="${1:-results_$(date +%Y-%m-%d_%H%M)}"
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$OUT_DIR"

# Camera serials and positions, from docs/hardware.md.
FRONT=31718458
REAR_RIGHT=32514439
REAR_LEFT=33289078
ALL="$FRONT $REAR_RIGHT $REAR_LEFT"

# Record the setup, so the results can be compared with later tests.
{
  echo "date: $(date -Is)"
  echo "model: $(tr -d '\0' < /proc/device-tree/model)"
  echo "l4t: $(head -1 /etc/nv_tegra_release)"
  nvpmodel -q 2>/dev/null | head -1
  python3 -c "import pyzed.sl as sl; print('zed sdk:', sl.Camera.get_sdk_version())"
  lsusb -t | grep -i video
} > "$OUT_DIR/system.txt"

# Each entry: label | serials | resolution | fps | depth mode | retrieve | retrieve Hz
# Order: start small, then vary one setting at a time against the 3-camera baseline (B3).
CONFIGS=(
  "B1 front only|$FRONT|HD720|15|PERFORMANCE|pointcloud|0"
  "B2 front+rear-right|$FRONT $REAR_RIGHT|HD720|15|PERFORMANCE|pointcloud|0"
  "B3 baseline, 3 cams|$ALL|HD720|15|PERFORMANCE|pointcloud|0"
  "T1 transport only, no depth|$ALL|HD720|15|NONE|none|0"
  "T2 depth on GPU, no copy|$ALL|HD720|15|PERFORMANCE|none|0"
  "C1 cloud copied at 5 Hz|$ALL|HD720|15|PERFORMANCE|pointcloud|5"
  "R1 VGA|$ALL|VGA|15|PERFORMANCE|pointcloud|0"
  "R2 HD1080|$ALL|HD1080|15|PERFORMANCE|pointcloud|0"
  "F1 30 fps|$ALL|HD720|30|PERFORMANCE|pointcloud|0"
  "D1 NEURAL_LIGHT|$ALL|HD720|15|NEURAL_LIGHT|pointcloud|0"
  "D2 NEURAL|$ALL|HD720|15|NEURAL|pointcloud|0"
)

for cfg in "${CONFIGS[@]}"; do
  IFS='|' read -r label serials res fps depth retrieve rhz <<< "$cfg"
  echo "=== $label ==="
  # shellcheck disable=SC2086  # $serials is intentionally split into several arguments.
  python3 "$HERE/zed_load_test.py" run --label "$label" --serials $serials \
    --resolution "$res" --fps "$fps" --depth-mode "$depth" \
    --retrieve "$retrieve" --retrieve-hz "$rhz" \
    --output "$OUT_DIR/results.jsonl" > "$OUT_DIR/log_${label%% *}.txt" 2>&1 \
    || echo "  (run reported a problem, see log_${label%% *}.txt)"
  # Let the cameras and the Jetson settle between runs.
  sleep 5
done

python3 "$HERE/zed_load_test.py" summarize "$OUT_DIR/results.jsonl" | tee "$OUT_DIR/results.md"
echo "Saved in $OUT_DIR"
