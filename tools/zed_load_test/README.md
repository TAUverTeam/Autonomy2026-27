# zed_load_test

Measures how much of the Jetson the ZED cameras use (CPU, GPU, memory, power, temperature) and
whether each camera still delivers its full frame rate, with 1, 2 or 3 cameras running at once.

**Owner:** Autonomy team leader · **Status:** used on the bench Jetson, 2026-11-25
· **Requirements:** REQ-AUT-ISS-06 (measured load), input to REQ-AUT-ISS-05, REQ-AUT-ISS-11, REQ-AUT-120

This is a **measurement tool, not part of the rover software**. It uses the ZED SDK directly,
without ROS, so it measures the cameras' own cost. A full system adds ROS, object detection and
the planner on top, so treat its numbers as a lower bound.

## Where it fits

```
3 × ZED 2i ──USB 3──► zed_load_test.py ──► results.jsonl ──► summarize ──► results.md
                           ▲
                      tegrastats (CPU, GPU, RAM, power, temperature, once per second)
```

Results are written up in [docs/measurements/](../../docs/measurements/).

## Files

| File | What it is |
|---|---|
| `zed_load_test.py` | Runs one configuration (`run`) or prints a table of results (`summarize`) |
| `run_matrix.sh` | Runs a fixed list of configurations, one after another, and saves everything |

## What one run does

1. Opens each camera by **serial number** (never by USB order, which changes between boots).
2. Starts one thread per camera that grabs frames as fast as the camera delivers them. After each
   frame it can copy data to CPU memory (`--retrieve`): `none`, `image`, `depth` or `pointcloud`.
   A ROS driver must copy the point cloud to publish it, so `pointcloud` is the realistic case.
3. Waits a warm-up time (default 5 s), then measures for a fixed window (default 30 s).
4. Reports per camera: frames per second achieved, frames dropped, time per grab cycle; and for the
   Jetson: CPU and GPU load, memory, total power, hottest temperature (mean and maximum).
5. Appends one JSON line to the results file.

## Options (`zed_load_test.py run`)

| Option | Default | Unit | Meaning |
|---|---|---|---|
| `--serials` | (required) | | Serial numbers of the cameras to open, see [docs/hardware.md](../../docs/hardware.md) |
| `--resolution` | `HD720` | | ZED resolution: `VGA`, `HD720`, `HD1080`, `HD2K`, … |
| `--fps` | `15` | frames/s | Requested camera frame rate |
| `--depth-mode` | `PERFORMANCE` | | `NONE`, `PERFORMANCE`, `QUALITY`, `ULTRA`, `NEURAL_LIGHT`, `NEURAL`, `NEURAL_PLUS` |
| `--retrieve` | `pointcloud` | | What to copy to CPU memory after each frame |
| `--retrieve-hz` | `0` | Hz | Copy at most this often; `0` means every frame |
| `--warmup` | `5` | s | Time before measuring starts |
| `--duration` | `30` | s | Length of the measuring window |
| `--label` | | | Name of the run in the table |
| `--output` | `results.jsonl` | | File the result is appended to |

## How to run

On the Jetson, with the cameras plugged in and nothing else using them (no ROS driver, no
`ZED_Explorer`):

```bash
# One configuration:
python3 zed_load_test.py run --serials 31718458 32514439 33289078 --label "my test"

# The full list (about 10 minutes; longer the first time a NEURAL mode is used):
./run_matrix.sh results_$(date +%F)

# Table of any results file:
python3 zed_load_test.py summarize results_2026-11-25/results.jsonl
```

Check the power mode first with `nvpmodel -q`; results are only comparable in the same mode.

## How to check it works

A quick run with one camera should show about 15 fps and 0 dropped frames:

```bash
python3 zed_load_test.py run --serials 31718458 --duration 8 --output /tmp/check.jsonl
```

## Reading the results

- **fps per camera** below the target means that camera cannot keep up in that configuration.
- **Dropped** frames are frames the camera sent but the SDK skipped because it was too slow.
- **CPU %** is the mean over all 8 cores, so 12.5 % equals one core fully busy.
- **GPU %** near 100 % means the GPU is the limit; object detection also needs the GPU.
- **Power** is the whole board's input (VDD_IN), useful for the power budget (REQ-OPS-140).

## Known limitations

- No ROS, no detection, no planner: real load will be higher.
- `tegrastats` samples once per second; very short peaks are missed.
- On another JetPack version the `tegrastats` format may differ; lines that cannot be parsed are
  skipped, and the system columns then show `-`.
