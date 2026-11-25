# 2026-11-25: Summary of the camera tests

Everything measured on the cameras on 25 November 2026, in one place: what each depth mode does,
how much of the Jetson it uses, and how good its depth looked. The detailed reports are:

- [Camera load test](2026-11-25-zed-load-test-3-cameras.md): CPU, GPU, memory and power for
  different camera settings (tool: [zed_load_test](../../tools/zed_load_test/)).
- [Depth modes on a lab recording](2026-11-25-depth-modes-lab.md): how complete each mode's depth
  is on the same images (tool: [zed_depth_compare](../../tools/zed_depth_compare/)).

---

## Contents

1. [Setup](#1-setup)
2. [How the ZED measures depth](#2-how-the-zed-measures-depth)
3. [The depth modes explained](#3-the-depth-modes-explained)
4. [All modes side by side](#4-all-modes-side-by-side)
5. [Other settings: cameras, resolution, frame rate, copying](#5-other-settings)
6. [Depth quality per camera](#6-depth-quality-per-camera)
7. [Trials, recording and file sizes](#7-trials-recording-and-file-sizes)
8. [Conclusions](#8-conclusions)
9. [What these tests do not cover](#9-what-these-tests-do-not-cover)
10. [Where the raw data is](#10-where-the-raw-data-is)

---

## 1. Setup

| | |
|---|---|
| Computer | Bench Jetson: Orin NX 16 GB, Engineering Reference Developer Kit (8 CPU cores) |
| Software | L4T R36.4.7 (JetPack 6), ZED SDK 5.1.1 with its Python API |
| Power mode | MAXN. `jetson_clocks` off, so clocks rise and fall with load |
| Cameras | 3 × ZED 2i: front 31718458, rear-right 32514439, rear-left 33289078 |
| USB | All three at USB 3 (5000M), behind the carrier's single internal hub (10 Gb/s link) |
| Other software running | None (no ROS, no object detection) |

**The Jetson at rest** (sampled at 09:59 before any test): CPU about 0–1 %, GPU 0 %, memory
1,693 MB used, board power 5.5–5.7 W, hottest temperature 47.7 °C. The numbers below include this
base.

**How to read the load numbers:**

- **CPU %** is the average over all 8 cores. 12.5 % equals one core fully busy.
- **GPU %** is the GPU's load as reported by `tegrastats`. Because `jetson_clocks` was off, the GPU
  slows its clock when lightly loaded, which makes low percentages look higher than they are.
  Short peaks to 80–99 % appear even in light runs. Treat GPU % as rough.
- **Power** is the whole board's input (VDD_IN). It is the most reliable way to compare how hard
  the Jetson works.
- **fps achieved** is frames per second actually delivered per camera, against a target of 15.
- **Dropped** is frames the camera sent but the SDK skipped because it could not keep up.

Each load run: cameras opened, 5 s warm-up, 30 s measured, one reading per second (30 readings).
The point cloud was copied to CPU memory after every frame, as a ROS driver does to publish it.

---

## 2. How the ZED measures depth

A ZED 2i has two lenses 12 cm apart (the *baseline*). A nearby object appears shifted between the
left and right images; a far one barely moves. That shift, in pixels, is called *disparity*.
Depth follows from it:

```
depth = focal length × baseline / disparity
```

So the whole problem is **matching**: for each pixel in the left image, find the same point in the
right image. Two consequences matter for us:

- **Error grows with distance.** Far objects have small disparities, so a one-pixel matching error
  is a large depth error. Stereo error grows roughly with the square of the distance.
- **Some pixels cannot be matched at all:**
  - *occlusion*: background next to a nearby object is seen by one lens only;
  - *no texture*: plain sand, sky, blank walls look the same everywhere, so any shift matches;
  - *repeating patterns*: several shifts match equally well;
  - *reflections and glare*: the two lenses see different bright spots.

The depth modes are different ways of doing the matching and of deciding what to do where it fails.

---

## 3. The depth modes explained

Stereolabs does not publish exactly how each mode works inside. The descriptions below combine
their documentation with what we saw today.

### Classic modes: a fixed matching algorithm

For each pixel, the algorithm compares a small patch around it with patches along the same row of
the other image and picks the shift where they look most alike. It then checks the match (for
example matching right-to-left too) and **throws away matches it is not sure of**, which leaves
holes. Finally it smooths and filters the result. The three classic modes differ in how much
checking and refinement they do.

| Mode | What Stereolabs says it is for | What we saw |
|---|---|---|
| **PERFORMANCE** | Fastest; designed for speed | Cheapest real depth mode by far. 92–95 % of the image filled indoors. Holes at object edges and on thin objects. In one trial it invented a "far away" patch where light reflected off a cable. |
| **QUALITY** | Better on difficult, low-texture surfaces | Fill about the same as PERFORMANCE indoors (the lab has plenty of texture), at **double the power**. |
| **ULTRA** | Favours sharp edges and detail; needs more GPU memory and computing | Fill about the same, power like QUALITY, and **the most memory of any classic mode** (2.5 GB above rest). Invented a "far away" patch in a dark area under a desk. |

### Neural modes: a trained network

A neural network, trained by Stereolabs on large numbers of stereo image pairs, takes both images
and outputs a disparity for every pixel. Because it looks at the whole scene rather than small
patches, it can **fill in** areas the classic algorithm cannot match (plain surfaces, object edges)
with a value that fits the surroundings. The risk is the opposite of a hole: a filled value can be
plausible but wrong, which is why an accuracy test with a known target is still needed. The three
modes are smaller to larger versions of the network.

| Mode | What Stereolabs says it is for | What we saw |
|---|---|---|
| **NEURAL_LIGHT** | Lightest network, for real time and several cameras | 99–100 % filled, clean outlines of people and furniture. All three cameras at full rate for 10.7 W: **cheaper than QUALITY or ULTRA**. |
| **NEURAL** | The standard neural mode; balance of quality and speed | Pictures nearly the same as NEURAL_LIGHT. Three cameras still at full rate, but the **GPU is full (97 %) and power doubles to 20 W**: nothing left for object detection. |
| **NEURAL_PLUS** | Largest network; most accurate and robust, slowest | Sharpest edges (single chair legs visible). **Cannot run three cameras**: 4.2 fps per camera, 982 frames dropped in 30 s. |

### NONE

No depth at all: the cameras only send video. Useful as the baseline cost of the cameras themselves.

---

## 4. All modes side by side

Three cameras, HD720, 15 fps, point cloud copied after every frame. Live load from the load test;
fill rate from the lab recording (average of the three cameras).

| Mode | fps achieved (each camera) | Dropped (30 s, all cams) | CPU % mean / max | GPU % mean / max | Memory used, MB max (above rest) | Power W mean / max | Temp °C max | Fill % (whole / lower half) | Replay fps, one camera |
|---|---|---|---|---|---|---|---|---|---|
| NONE (video only) | 15.0 | 0 | 5.5 / 11.2 | 10.1 / 13 | 2,276 (+0.6 GB) | 6.5 / 6.7 | 50.3 | – | – |
| **PERFORMANCE** | 15.0 | 0 | 10.1 / 19.6 | 62.2 / 82 | 2,315 (+0.6 GB) | **8.0** / 8.1 | 50.4 | 93.3 / 92.1 | 21.2 |
| QUALITY | 15.0 | 0 | 14.4 / 24.8 | 76.2 / 99 | 3,403 (+1.7 GB) | 16.1 / 16.3 | 55.1 | 93.1 / 92.4 | 15.1 |
| ULTRA | 15.0 | 0 | 8.3 / 10.4 | 70.8 / 99 | 4,209 (+2.5 GB) | 15.6 / 15.8 | 57.5 | 92.4 / 91.8 | 15.3 |
| **NEURAL_LIGHT** | 15.0 | 0 | 12.0 / 21.8 | 57.3 / 99 | 3,021 (+1.3 GB) | **10.7** / 10.9 | 54.0 | **99.4 / 99.1** | 16.7 |
| NEURAL | 15.0 | 0 | 11.1 / 18.9 | **96.9** / 99 | 3,040 (+1.3 GB) | **20.1** / 20.2 | 61.8 | 99.7 / 99.4 | 15.1 |
| NEURAL_PLUS | **4.2** | **982** | 8.7 / 12.8 | **98.3** / 99 | 4,652 (+3.0 GB) | **21.1** / 21.4 | 63.8 | 98.6 / 98.1 | 9.1 |

Notes:

- QUALITY, ULTRA and NEURAL_PLUS were load-tested at 11:26–11:28, the others at 10:03–10:10, with
  the same settings and tool.
- *Replay fps* is how fast one recording was processed flat out, including the comparison tool's
  own Python analysis. It only compares modes with each other; it is not the SDK's top speed.
- *Grab cycle time*: 66.6–66.7 ms on average for every camera in every mode except NEURAL_PLUS,
  matching 15 fps exactly. NEURAL_PLUS took 241 ms per frame (about 4 fps).
- **CPU use is low in every mode** (at most a quarter of the CPU). Depth runs on the GPU. The
  differences between modes are in GPU, power and memory.

### Ranking by cost (power, three cameras)

```
NONE          6.5 W  ████
PERFORMANCE   8.0 W  █████
NEURAL_LIGHT 10.7 W  ███████
ULTRA        15.6 W  ██████████
QUALITY      16.1 W  ███████████
NEURAL       20.1 W  █████████████
NEURAL_PLUS  21.1 W  ██████████████   (fails: 4.2 fps)
```

---

## 5. Other settings

All with PERFORMANCE depth unless stated. Same columns as above.

### Number of cameras (HD720, 15 fps)

| Run | Cameras | fps achieved | Dropped | CPU % mean / max | GPU % mean / max | Memory MB max | Power W mean / max | Temp °C max |
|---|---|---|---|---|---|---|---|---|
| B1 | front | 15.0 | 0 | 3.3 / 5.1 | 20.5 / 82 | 1,963 | 6.5 / 6.6 | 48.8 |
| B2 | front + rear-right | 15.0 / 15.0 | 0 | 6.8 / 14.1 | 39.4 / 81 | 2,133 | 7.3 / 7.4 | 49.5 |
| B3 | all three | 15.0 / 15.0 / 15.0 | 0 | 10.1 / 19.6 | 62.2 / 82 | 2,315 | 8.0 / 8.1 | 50.4 |

Each extra camera adds about 3.4 points of CPU, 20 points of GPU, 170 MB and 0.75 W. The cost
grows steadily; there is no sudden limit at three cameras.

### What part of the work costs what (three cameras, HD720, 15 fps)

| Run | What runs | CPU % mean / max | GPU % mean / max | Power W mean |
|---|---|---|---|---|
| T1 | Video only, no depth | 5.5 / 11.2 | 10.1 / 13 | 6.5 |
| T2 | Depth computed, kept on the GPU | 8.3 / 14.1 | 38.1 / 47 | 7.1 |
| C1 | Depth + point cloud copied to CPU at 5 Hz | 8.6 / 17.0 | 48.4 / 80 | 7.4 |
| B3 | Depth + point cloud copied every frame (15 Hz) | 10.1 / 19.6 | 62.2 / 82 | 8.0 |

Making the point cloud and copying it to the CPU costs about as much GPU as computing the depth.
Copying at 5 Hz instead of 15 Hz saves part of it, and the copy at 5 Hz made a few cycles slower
(95th percentile 79–80 ms against 67–68 ms), without losing frames.

### Resolution and frame rate (three cameras)

| Run | Setting | fps achieved | Dropped | CPU % mean / max | GPU % mean / max | Memory MB max | Power W mean / max | Temp °C max |
|---|---|---|---|---|---|---|---|---|
| R1 | VGA, 15 fps | 15.0 / 15.0 / 15.0 | 0 | 6.3 / 17.2 | 41.9 / 64 | 2,323 | 7.1 / 7.2 | 51.0 |
| B3 | HD720, 15 fps | 15.0 / 15.0 / 15.0 | 0 | 10.1 / 19.6 | 62.2 / 82 | 2,315 | 8.0 / 8.1 | 50.4 |
| R2 | HD1080, 15 fps | 14.9 / 14.9 / 14.9 | 0 | 16.7 / 19.9 | 58.4 / 99 | 3,002 | 9.7 / 9.9 | 52.4 |
| F1 | HD720, 30 fps | 30.0 / 30.0 / 30.0 | 0 | 19.6 / 29.8 | 67.9 / 99 | 2,785 | 10.1 / 10.3 | 53.0 |

All held their target rate. HD1080 had slightly longer slow cycles (95th percentile 75–78 ms) but
no dropped frames. Doubling the frame rate roughly doubles the CPU and adds about 2 W.

---

## 6. Depth quality per camera

From the lab recording (mast held by hand, people moving). 287 frames per camera analysed.

### Fill rate (% of pixels with a valid depth: whole image / lower half)

| Mode | Front | Rear-right | Rear-left |
|---|---|---|---|
| PERFORMANCE | 92.0 / 91.0 | 93.0 / 92.2 | 94.9 / 93.2 |
| QUALITY | 91.5 / 91.6 | 92.7 / 92.2 | 95.1 / 93.5 |
| ULTRA | 89.7 / 90.9 | 92.1 / 90.6 | 95.3 / 93.9 |
| NEURAL_LIGHT | 99.3 / 99.0 | 99.3 / 98.8 | 99.7 / 99.4 |
| NEURAL | 99.7 / 99.5 | 99.6 / 99.3 | 99.7 / 99.5 |
| NEURAL_PLUS | 98.4 / 98.4 | 98.0 / 97.1 | 99.4 / 98.9 |

The scenes: front looked across the room (benches, chair, whiteboard, a person close by);
rear-right at a workbench with two seated people at about 2 m; rear-left at a wall with posters
and monitors about 1 m away. The rear-left view was the simplest (one flat wall), so all modes did
best there.

### Replay speed (frames per second, one camera, including the tool's analysis)

| Mode | Front | Rear-right | Rear-left |
|---|---|---|---|
| PERFORMANCE | 21.4 | 21.0 | 21.1 |
| QUALITY | 15.0 | 15.2 | 15.2 |
| ULTRA | 15.4 | 15.1 | 15.3 |
| NEURAL_LIGHT | 16.5 | 17.0 | 16.7 |
| NEURAL | 15.0 | 15.0 | 15.2 |
| NEURAL_PLUS | 8.9 | 9.3 | 9.0 |

### Frame-to-frame variation (recorded, but NOT valid as noise)

The tool also measured how much each pixel's depth changed between frames (median, as % of its
distance). **Because the mast was hand-held and people moved, these numbers mostly show real
movement, not depth noise.** They are listed only for completeness; do not use them to compare
modes.

| Mode | Front (at 2.2–2.4 m) | Rear-right (at 2.1 m) | Rear-left (at 1.15 m) |
|---|---|---|---|
| PERFORMANCE | 2.29 % | 1.55 % | 1.95 % |
| QUALITY | 1.81 % | 1.21 % | 1.58 % |
| ULTRA | 2.18 % | 1.54 % | 1.62 % |
| NEURAL_LIGHT | 2.71 % | 1.55 % | 1.59 % |
| NEURAL | 2.47 % | 1.58 % | 1.56 % |
| NEURAL_PLUS | 2.32 % | 1.68 % | 1.60 % |

### What the comparison pictures showed

- Classic modes: holes along the edges of people and furniture, on thin objects (light fittings,
  chair legs, cables), and in a strip at the left edge of the image, which the right lens does not
  see. ULTRA showed a false "far away" patch in a dark area under a desk.
- Neural modes: almost no holes, clean outlines; NEURAL_PLUS has the sharpest edges; NEURAL_LIGHT
  and NEURAL look nearly the same.

---

## 7. Trials, recording and file sizes

### First load trial (front camera only, 8 s, PERFORMANCE, HD720, 15 fps)

121 frames, 15.12 fps, 0 dropped, 66.7 ms per cycle (95th percentile 67.6 ms). CPU 3.5 % mean /
4.4 % max, GPU 19.5 % / 60 %, memory 1,953 MB, power 6.8 W mean / 7.2 W max, 48.2 °C.

### First depth trial (front camera lying near the floor, about 0.6 m from laminate, a cable and chair legs; 4 s)

| Mode | Frames | Fill % (whole / lower half) | Variation % (at m) | Replay fps |
|---|---|---|---|---|
| PERFORMANCE | 57 | 76.2 / 71.3 | 0.17 (0.6) | 30.7 |
| NEURAL_LIGHT | 57 | 87.2 / 81.2 | 0.06 (0.57) | 21.3 |

PERFORMANCE invented a "far away" patch, with a hole around it, where ceiling light reflected off
the cable. NEURAL_LIGHT showed the cable and chair legs correctly.

### Recording compression (front camera, 4 s, 62 frames, HD720)

| Compression | File size | Per minute (estimate) |
|---|---|---|
| H265_LOSSLESS | 2 MB | ≈ 30 MB |
| LOSSLESS | 75 MB | ≈ 1.1 GB |

A 37-fold difference means H265_LOSSLESS is probably not truly lossless on this Jetson, so
`LOSSLESS` became the tool's default for depth comparisons.

### Lab recording (10:57, 20 s, HD720, 15 fps, LOSSLESS)

| Camera | Frames | Size |
|---|---|---|
| Front 31718458 | 302 | 363 MB |
| Rear-right 32514439 | 302 | 364 MB |
| Rear-left 33289078 | 302 | 338 MB |

All three recorded at the same time without losing frames: 302 frames in 20 s is the full 15 fps.

---

## 8. Conclusions

1. **The Jetson can run all three cameras with depth.** Every mode except NEURAL_PLUS delivered the
   full 15 fps on all three cameras with zero dropped frames. USB and the shared hub were never the
   limit. Last season's problem was probably what ran on top (detection, ROS, RTAB-Map), not the
   cameras.
2. **CPU is not the constraint for depth**; at most a quarter of the CPU was used. GPU, power and
   memory are what differ between modes.
3. **QUALITY and ULTRA are not worth it.** They cost about twice the power of PERFORMANCE (and more
   than NEURAL_LIGHT) without filling more of the image indoors.
4. **NEURAL is too expensive** while object detection must also use the GPU (97 % GPU, 20 W), and
   **NEURAL_PLUS cannot run three cameras** at all on this Jetson.
5. **The real choice is PERFORMANCE (8 W) or NEURAL_LIGHT (10.7 W).** NEURAL_LIGHT fills about
   99 % of the image against about 93 %, gives cleaner shapes and avoided the false distances the
   classic modes produced, for 2.7 W and about 0.7 GB more. **NEURAL_LIGHT is the leading
   candidate.** The team chose it: [decision 0003](../decisions/0003-depth-mode-neural-light.md).

## 9. What these tests do not cover

- **Object detection and ROS** were not running. A full system adds both; detection competes with
  depth for the GPU.
- **The lab is not the Mars Yard.** Plain sand, sky and harsh sun are where classic modes fail
  most. Outdoor recordings in sun and at dusk are needed (REQ-AUT-130).
- **Accuracy was not measured.** Fill rate says how much of the image has a depth, not whether it
  is right. A 20 cm box at a taped 2 m is needed (REQ-AUT-020).
- **Noise was not measured validly** (hand-held mast, people moving).
- **Heat over time:** runs lasted 35 s. A 60-minute task (REQ-OPS-140) in the rover's enclosure
  may heat the Jetson until it slows down.
- **The rover's Jetson** was not tested; these results are from the bench Jetson.

## 10. Where the raw data is

All on the bench Jetson:

| Data | Location |
|---|---|
| Load test, 11 runs (10:01–10:10) | `~/tauver-tools/zed_load_test/results_2026-11-25/` (`results.jsonl`, `results.md`, `system.txt`, `log_*.txt`) |
| Load test, QUALITY / ULTRA / NEURAL_PLUS (11:26–11:28) | `~/tauver-tools/zed_load_test/results_2026-11-25_extra/` |
| Lab recording (3 SVO files, 1.1 GB) | `~/recordings/2026-11-25_lab_handheld/` |
| Depth comparison (table, raw results, pictures) | `~/recordings/2026-11-25_lab_handheld/compare/` |

The trial files (first load and depth trials, compression test) were temporary and have been
deleted; their numbers are recorded above. The comparison pictures show people in the lab, so they
are not copied into this repository.
