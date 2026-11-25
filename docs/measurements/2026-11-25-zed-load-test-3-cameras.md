# 2026-11-25: Camera load test, 1 to 3 ZED 2i on the bench Jetson

- **Requirement:** REQ-AUT-ISS-06 (measured load on the main computer); input to REQ-AUT-ISS-05
  (second computer) and REQ-AUT-ISS-11 (live map)
- **Done by:** Autonomy team leader, run remotely over SSH
- **Tool:** [tools/zed_load_test](../../tools/zed_load_test/) (`run_matrix.sh`)
- **Raw results:** on the bench Jetson in `~/tauver-tools/zed_load_test/results_2026-11-25/`
  (`results.jsonl`, `results.md`, `system.txt`, one log per run)

## Goal

Last season the team reported that the Jetson could not handle all three cameras, and in the end
only the front camera fed the obstacle map. No measurement was recorded. This test asks the first
half of the question: **can the Jetson run the three cameras and their depth calculation at all,
and how much of the computer does that use?**

## Setup

| | |
|---|---|
| Computer | Bench Jetson: Orin NX 16 GB, Engineering Reference Developer Kit |
| Software | L4T R36.4.7 (JetPack 6), ZED SDK 5.1.1, Python API |
| Power mode | MAXN. `jetson_clocks` not enabled (clocks scale with load) |
| Cameras | 3 × ZED 2i: front 31718458, rear-right 32514439, rear-left 33289078 |
| USB | All three at USB 3 (5000M), all behind the carrier's single internal USB hub (10 Gb/s link) |
| Other load | None: no ROS, no detection, desktop idle |
| Clock | Synchronized to internet time before the test |

Each run: open the cameras, 5 s warm-up, 30 s measuring window, one `tegrastats` sample per second
(30 samples per run). Unless stated otherwise the point cloud was copied to CPU memory after every
frame, as a ROS driver must do to publish it.

## Procedure

```bash
cd ~/tauver-tools/zed_load_test
./run_matrix.sh ~/tauver-tools/zed_load_test/results_2026-11-25
```

The configurations are listed in `run_matrix.sh`. They start from one camera, then vary one setting
at a time against the three-camera baseline (B3).

## Results

| Run | Cams | Resolution | fps | Depth | Copied to CPU | fps achieved (each camera) | Dropped | CPU % mean / max | GPU % mean / max | RAM MB max | Power W mean / max | Temp °C max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B1 front only | 1 | HD720 | 15 | PERFORMANCE | point cloud | 15.0 | 0 | 3.3 / 5.1 | 20.5 / 82 | 1963 | 6.5 / 6.6 | 48.8 |
| B2 two cameras | 2 | HD720 | 15 | PERFORMANCE | point cloud | 15.0 / 15.0 | 0 | 6.8 / 14.1 | 39.4 / 81 | 2133 | 7.3 / 7.4 | 49.5 |
| **B3 baseline** | 3 | HD720 | 15 | PERFORMANCE | point cloud | 15.0 / 15.0 / 15.0 | 0 | 10.1 / 19.6 | 62.2 / 82 | 2315 | 8.0 / 8.1 | 50.4 |
| T1 video only | 3 | HD720 | 15 | NONE | nothing | 15.0 / 15.0 / 15.0 | 0 | 5.5 / 11.2 | 10.1 / 13 | 2276 | 6.5 / 6.7 | 50.3 |
| T2 depth, no copy | 3 | HD720 | 15 | PERFORMANCE | nothing | 15.0 / 15.0 / 15.0 | 0 | 8.3 / 14.1 | 38.1 / 47 | 2292 | 7.1 / 7.2 | 50.6 |
| C1 copy at 5 Hz | 3 | HD720 | 15 | PERFORMANCE | point cloud, 5 Hz | 15.0 / 15.0 / 15.0 | 0 | 8.6 / 17.0 | 48.4 / 80 | 2384 | 7.4 / 7.5 | 50.9 |
| R1 VGA | 3 | VGA | 15 | PERFORMANCE | point cloud | 15.0 / 15.0 / 15.0 | 0 | 6.3 / 17.2 | 41.9 / 64 | 2323 | 7.1 / 7.2 | 51.0 |
| R2 HD1080 | 3 | HD1080 | 15 | PERFORMANCE | point cloud | 14.9 / 14.9 / 14.9 | 0 | 16.7 / 19.9 | 58.4 / 99 | 3002 | 9.7 / 9.9 | 52.4 |
| F1 30 fps | 3 | HD720 | 30 | PERFORMANCE | point cloud | 30.0 / 30.0 / 30.0 | 0 | 19.6 / 29.8 | 67.9 / 99 | 2785 | 10.1 / 10.3 | 53.0 |
| D1 NEURAL_LIGHT | 3 | HD720 | 15 | NEURAL_LIGHT | point cloud | 15.0 / 15.0 / 15.0 | 0 | 12.0 / 21.8 | 57.3 / 99 | 3021 | 10.7 / 10.9 | 54.0 |
| D2 NEURAL | 3 | HD720 | 15 | NEURAL | point cloud | 15.0 / 15.0 / 15.0 | 0 | 11.1 / 18.9 | **96.9** / 99 | 3040 | **20.1** / 20.2 | 61.8 |
| D-QUALITY | 3 | HD720 | 15 | QUALITY | point cloud | 15.0 / 15.0 / 15.0 | 0 | 14.4 / 24.8 | 76.2 / 99 | 3403 | 16.1 / 16.3 | 55.1 |
| D-ULTRA | 3 | HD720 | 15 | ULTRA | point cloud | 15.0 / 15.0 / 15.0 | 0 | 8.3 / 10.4 | 70.8 / 99 | 4209 | 15.6 / 15.8 | 57.5 |
| D-NEURAL_PLUS | 3 | HD720 | 15 | NEURAL_PLUS | point cloud | **4.2 / 4.2 / 4.2** | **982** | 8.7 / 12.8 | **98.3** / 99 | 4652 | **21.1** / 21.4 | 63.8 |

The last three runs (D-QUALITY, D-ULTRA, D-NEURAL_PLUS) were added at 11:26–11:28 the same day, with the
same tool and settings; raw results in `~/tauver-tools/zed_load_test/results_2026-11-25_extra/`.

How to read it: CPU % is the mean over 8 cores (12.5 % = one core fully busy). RAM is the whole
system (about 1.7 GB is used with nothing running). Power is the whole board's input. Time per grab
cycle was 66.7 ms at 15 fps (33.3 ms at 30 fps) in every run, so no camera ever waited longer than
its frame period. No errors or grab failures in any run.

**Caution about GPU %:** without `jetson_clocks` the GPU slows its clock when lightly loaded, and
`tegrastats` reports load relative to the current clock. Low GPU percentages are therefore inflated
and short peaks (82 % with one camera) are noise. Power is the more reliable way to compare runs.

## Conclusions

1. **The Jetson runs all three cameras with depth at full frame rate.** In every configuration all
   three cameras delivered their full rate with zero dropped frames. The USB connection and the
   shared hub are not a bottleneck at HD720 or HD1080.
2. **The cameras alone use a small part of the computer** in the configuration last season used
   (PERFORMANCE depth): about 10 % CPU, 0.6 GB of memory above idle and 8 W.
3. **NEURAL depth fills the GPU** (97 % GPU, power doubles to 20 W). It would leave nothing for
   object detection. NEURAL_LIGHT costs about a third more power than PERFORMANCE and is the most we
   should consider while detection also runs. **NEURAL_PLUS cannot run three cameras**: 4.2 fps per
   camera and 982 dropped frames in 30 s. QUALITY and ULTRA cost about twice the power of PERFORMANCE
   (16 W), more than NEURAL_LIGHT.
4. **Copying point clouds to the CPU costs GPU time** (T2 → B3). Copying them less often (C1, 5 Hz)
   recovers part of it; this is a cheap setting to use if needed.
5. **So last season's limit was probably not the cameras themselves,** but what ran on top of them:
   the ROS driver publishing large point clouds, YOLO on three video streams, and RTAB-Map, whose
   output was not used. This is a hypothesis; the next tests check it.

## Not covered (next tests)

- **Object detection alongside the cameras** (YOLO or similar on three streams, on the GPU). This is
  the most likely real limit.
- **The ROS 2 driver** publishing three point clouds, with CPU use per process.
- **The rover Jetson.** Confirm it is the same model and repeat B3 and D1 there.
- **Sustained heat.** Each run lasted 35 s; a 60-minute run (REQ-OPS-140) in the rover's enclosure
  may heat the board enough to slow it.
- Steadier GPU readings with `jetson_clocks` enabled, which changes a system setting.
