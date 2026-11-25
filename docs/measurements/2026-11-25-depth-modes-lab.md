# 2026-11-25: Depth modes compared on a lab recording

- **Requirement:** input to choosing the depth mode for REQ-AUT-020 (obstacles ≥ 20 cm from ≥ 2 m)
  and REQ-AUT-120 (share of the computer)
- **Done by:** Autonomy team leader (recording and analysis run remotely over SSH)
- **Tool:** [tools/zed_depth_compare](../../tools/zed_depth_compare/)
- **Raw data:** on the bench Jetson in `~/recordings/2026-11-25_lab_handheld/` (three SVO files,
  about 1.1 GB in total; comparison pictures and results in `compare/`). The pictures show people
  in the lab, so they are not copied into this repository.

Summary of all of the day's camera tests, with load numbers per mode: [2026-11-25-camera-tests-summary.md](2026-11-25-camera-tests-summary.md).

## Goal

A first look at how the six ZED depth modes differ on real images, and a check that the tools work
end to end. This is **not** the final depth-mode decision: the lab is not like the Mars Yard
(see Limitations).

## Setup

| | |
|---|---|
| Computer | Bench Jetson (Orin NX 16 GB), MAXN, ZED SDK 5.1.1 |
| Cameras | All three ZED 2i on the mast: front 31718458, rear-right 32514439, rear-left 33289078 |
| Recording | 20 s, HD720, 15 fps, `LOSSLESS` compression, about 300 frames per camera |
| Scene | Lab, ceiling lights. Front: room with benches, chair, whiteboard, a person close by. Rear-right: workbench and two seated people at about 2 m. Rear-left: wall with posters and monitors at about 1 m |
| Mast | **Held by hand**, people moving in the room |

## Procedure

```bash
python3 record_svo.py --serials 31718458 32514439 33289078 --duration 20 \
    --out ~/recordings/2026-11-25_lab_handheld --note "lab, mast held by hand, people moving in the room"
python3 depth_compare.py ~/recordings/2026-11-25_lab_handheld/*.svo2 \
    --out ~/recordings/2026-11-25_lab_handheld/compare
```

Each file was replayed once per mode; the first 15 frames were skipped, 287 frames were analysed.

## Results

Fill rate: share of pixels with a valid depth (whole image / lower half).

| Mode | Front | Rear-right | Rear-left | Processing fps (one camera) |
|---|---|---|---|---|
| PERFORMANCE | 92.0 / 91.0 | 93.0 / 92.2 | 94.9 / 93.2 | 21 |
| QUALITY | 91.5 / 91.6 | 92.7 / 92.2 | 95.1 / 93.5 | 15 |
| ULTRA | 89.7 / 90.9 | 92.1 / 90.6 | 95.3 / 93.9 | 15 |
| NEURAL_LIGHT | 99.3 / 99.0 | 99.3 / 98.8 | 99.7 / 99.4 | 17 |
| NEURAL | 99.7 / 99.5 | 99.6 / 99.3 | 99.7 / 99.5 | 15 |
| NEURAL_PLUS | 98.4 / 98.4 | 98.0 / 97.1 | 99.4 / 98.9 | 9 |

The noise figures are **not reported**: the mast was hand-held and people moved, so frame-to-frame
changes are mostly real movement, not depth noise.

Processing fps includes the tool's own analysis in Python, so it is lower than the SDK alone would
reach. Use it only to compare modes with each other. The real load of each mode with three cameras
is in the [load measurement](2026-11-25-zed-load-test-3-cameras.md).

### What the pictures show

- **Classic modes (PERFORMANCE, QUALITY, ULTRA)** leave black holes mainly:
  - along the edges of nearby objects (people, chairs, the workbench), where the background is
    seen by one lens only;
  - on thin objects (light fittings, chair legs, cables);
  - in a band at the left edge of the image, which the right lens does not see.
- **Classic modes sometimes produce false depth**, which is worse than a hole: ULTRA showed a
  patch of "far away" in a dark area under a desk (rear-right), and in an earlier trial
  PERFORMANCE did the same where ceiling light reflected off a cable on the floor.
- **Neural modes** fill almost everything, give clean outlines of people and furniture, and show
  thin objects such as the chair. NEURAL_PLUS has the sharpest edges (individual chair legs) but
  is slowest. NEURAL_LIGHT and NEURAL look nearly the same.

## Conclusions

1. **Neural modes fill 98–100 % of the image against 90–95 % for classic modes**, even in a lab
   full of texture, where classic modes do best. The gap should be larger on plain sand.
2. **Classic modes' holes are mostly at object edges**, and they occasionally invent false
   distances in dark or shiny areas. For obstacle detection a false "far" value is the dangerous
   case, because it can hide an obstacle.
3. **NEURAL_PLUS is too slow** for three cameras on this Jetson (9 fps for one camera in replay).
   **NEURAL fills the GPU** with three cameras (load test). That leaves **PERFORMANCE and
   NEURAL_LIGHT** as the real candidates.
4. **NEURAL_LIGHT looked nearly as good as NEURAL** here, at much lower cost, so it is the leading
   candidate. This is not yet a decision: see below.

## Limitations and next steps

- **The lab is not the Mars Yard.** It has strong texture and even lighting; sand, sky and harsh
  sun are what break classic modes. Record outdoors on sand or gravel, in strong sun and at dusk
  (REQ-AUT-130).
- **Hand-held mast:** repeat with the mast resting on something solid, with nobody moving in view,
  to get valid noise figures.
- **No accuracy check:** fill and noise do not say whether the distances are correct. Put a box
  20 cm high at a taped 2 m (REQ-AUT-020) and check its measured distance and whether it stands out
  from the ground in each mode.
- **Pictures:** for indoor scenes use `--vis-max 5` so that 1–4 m distances get more contrast.
- After those tests, write a decision record for the depth mode.
