# zed_depth_compare

Records the ZED cameras once, then compares the depth modes (PERFORMANCE, QUALITY, ULTRA,
NEURAL_LIGHT, NEURAL, NEURAL_PLUS) on exactly the same images: how much of the image gets a depth
value, how steady that depth is, and how fast the Jetson computes it.

**Owner:** Autonomy team leader · **Status:** tested on the bench Jetson, 2026-11-25
· **Requirements:** helps choose the depth mode for REQ-AUT-020 (obstacles ≥ 20 cm from ≥ 2 m),
REQ-AUT-130 (low light and strong sun), REQ-AUT-120 (share of the computer)

This is a **measurement tool, not part of the rover software**. The load each mode puts on the
Jetson is measured separately by [zed_load_test](../zed_load_test/).

## Why

The ZED computes depth by matching the left and right images. The classic modes (PERFORMANCE,
QUALITY, ULTRA) use a fixed algorithm that leaves holes where there is nothing distinctive to
match: plain sand, sky, blank walls, glare. The neural modes use a trained network that fills more
of the image, but costs much more GPU (see
[the load measurement](../../docs/measurements/2026-11-25-zed-load-test-3-cameras.md)). We want
the cheapest mode that is good enough on Mars Yard-like ground.

## Where it fits

```
ZED cameras ──► record_svo.py ──► *.svo2 (raw stereo video) ──► depth_compare.py ──► results.md
                                                                                  └─► *_compare.png
```

## Files

| File | What it does |
|---|---|
| `record_svo.py` | Records several cameras at once to SVO files (images only, depth off) |
| `depth_compare.py` | Replays SVO files once per depth mode and measures each mode |

## How to run

On the Jetson, with nothing else using the cameras:

```bash
# 1. Record 20 s from all three cameras. Keep the cameras still for the noise figure.
python3 record_svo.py --serials 31718458 32514439 33289078 --duration 20 \
    --out ~/recordings/2026-11-25_lab --note "lab, box 20 cm high at 2 m in front"

# 2. Compare all depth modes on those files (several minutes; NEURAL_PLUS is slow).
python3 depth_compare.py ~/recordings/2026-11-25_lab/*.svo2 --out ~/recordings/2026-11-25_lab/compare
```

The first time a neural mode is used on a Jetson, the SDK optimises its network for that
Jetson, which can take several minutes. Later runs start immediately.

### `record_svo.py` options

| Option | Default | Unit | Meaning |
|---|---|---|---|
| `--serials` | (required) | | Cameras to record, see [docs/hardware.md](../../docs/hardware.md) |
| `--duration` | `30` | s | Recording length |
| `--resolution` | `HD720` | | ZED resolution |
| `--fps` | `15` | frames/s | Frame rate |
| `--compression` | `LOSSLESS` | | `LOSSLESS` keeps pixels exact (≈ 1.1 GB per camera per minute at HD720). `H265_LOSSLESS` was 37× smaller on the Jetson, so it is probably not truly lossless there |
| `--out` | (required) | | Output folder; refuses to overwrite existing files |
| `--note` | | | Description of the scene, saved in `info.txt` |

### `depth_compare.py` options

| Option | Default | Unit | Meaning |
|---|---|---|---|
| `svo` | (required) | | SVO files to compare |
| `--modes` | all six | | Depth modes to try |
| `--out` | (required) | | Output folder |
| `--min-depth` / `--max-depth` | `0.3` / `20` | m | Range of accepted depth; outside it counts as no depth |
| `--vis-max` | `10` | m | Furthest distance coloured in the pictures |
| `--max-frames` | `0` (all) | frames | Limit per file, for quick tests |
| `--skip` | `15` | frames | Frames skipped at the start (some modes smooth over time and need to settle) |

## Reading the results

| Column | Meaning | Better is |
|---|---|---|
| Fill % | Share of pixels with a valid depth, averaged over frames | Higher |
| Fill % lower half | The same for the lower half of the image (the ground ahead) | Higher |
| Noise % (at m) | Median frame-to-frame jump of a pixel's depth, as % of its distance, and the median distance of those pixels. **Only valid if the camera did not move** | Lower |
| Processing fps | Frames per second computed when replaying flat out | Higher; must stay above the camera's frame rate with everything else running |

In the pictures, red is near, blue is far, and black is no depth. Look for holes on the ground,
false objects (patches with a very different colour from their surroundings), and whether a
small obstacle shows as a clear shape.

Fill rate alone can mislead: a mode can fill a hole with a wrong guess. Always look at the
pictures too, and for REQ-AUT-020 check that the obstacle stands out from the ground.

## How to check it works

```bash
python3 record_svo.py --serials 31718458 --duration 4 --out /tmp/svo_check
python3 depth_compare.py /tmp/svo_check/*.svo2 --modes PERFORMANCE NEURAL_LIGHT --out /tmp/cmp_check --skip 5
```

Two table rows and a picture `front_31718458_compare.png` should appear in `/tmp/cmp_check`.

## Known limitations

- The noise figure assumes a still camera. Recordings made while driving give fill rates and
  pictures, but their noise figures mean nothing.
- Fill and noise say how complete and steady the depth is, not how **accurate** it is. Accuracy
  needs a target at a measured distance (for example a box at a taped-out 2 m).
- Processing speed is measured with one camera at a time and nothing else running.
