# 0003. Use the NEURAL_LIGHT depth mode for the ZED cameras

- **Status:** Accepted
- **Date:** 2026-11-25
- **Decided by:** Autonomy team, 2026/27
- **Requirements:** REQ-AUT-020 (obstacles ≥ 20 cm from ≥ 2 m), REQ-AUT-120 (share of the computer),
  REQ-AUT-ISS-06 (measured load), REQ-AUT-130 (low light and strong sun)

## Problem

The ZED SDK offers seven depth modes, from no depth to large neural networks. The mode decides how
much of the image gets a depth value, how often that depth is wrong, and how much of the Jetson the
three cameras use, which in turn decides how much is left for object detection, ROS and planning.
Every autonomy package that uses depth depends on this choice, so we make it once, here.

## Options considered

All measured on 2026-11-25 on the bench Jetson, three ZED 2i cameras, HD720, 15 fps
([summary of the tests](../measurements/2026-11-25-camera-tests-summary.md)).

| Mode | Kind | Three cameras at full rate? | GPU % mean | Power | Image filled (lab) |
|---|---|---|---|---|---|
| PERFORMANCE | Classic | Yes | 62 | 8.0 W | 93 % |
| QUALITY | Classic | Yes | 76 | 16.1 W | 93 % |
| ULTRA | Classic | Yes | 71 | 15.6 W | 92 % |
| **NEURAL_LIGHT** | Neural | Yes | 57 | **10.7 W** | **99 %** |
| NEURAL | Neural | Yes | 97 | 20.1 W | 100 % |
| NEURAL_PLUS | Neural | **No** (4.2 fps, frames dropped) | 98 | 21.1 W | 99 % |

1. **PERFORMANCE**: cheapest, but leaves holes at object edges and on thin objects, and twice
   invented false "far away" distances (glare on a cable, a dark area under a desk).
2. **QUALITY / ULTRA**: twice the power of PERFORMANCE with no better fill indoors.
3. **NEURAL_LIGHT**: nearly complete depth with clean object outlines, for 2.7 W and about 0.7 GB
   more than PERFORMANCE.
4. **NEURAL**: pictures nearly the same as NEURAL_LIGHT, but fills the GPU (97 %) and doubles the
   power, leaving nothing for object detection.
5. **NEURAL_PLUS**: cannot keep up with three cameras on this Jetson.

## Decision

All three cameras use **NEURAL_LIGHT** depth.

## Why

- **Fewer holes and fewer false distances** than every classic mode. For obstacle detection a
  false "far away" value is the dangerous error, because it can hide an obstacle, and the classic
  modes produced it in our tests.
- **It leaves room for the rest of the system.** GPU use was about the same as PERFORMANCE and far
  below NEURAL, and CPU use stayed around 12 %, so object detection and ROS still have resources.
- **Its cost is small and known**: about 10.7 W for the three cameras, 1.3 GB of memory above idle.
- Plain sand, the main surface at ERC, is where classic modes are known to fail most, which
  favours a neural mode further.

## Consequences

- Every package and launch file that opens the cameras sets `NEURAL_LIGHT`. A different mode needs a
  new decision record.
- The power budget (REQ-OPS-140) counts about 10.7 W for the three cameras with depth, before
  detection.
- The first time NEURAL_LIGHT runs on a new Jetson (for example the rover's), the SDK optimises the
  network for it, which takes several minutes. Do this once before a test day, not in the field.

**We revisit this decision if any of these checks fails:**

1. **Accuracy:** a 20 cm box at a taped 2 m is measured at the right distance and stands out from
   the ground (REQ-AUT-020). A neural network can fill a gap with a plausible but wrong value; this
   is the check that catches it.
2. **Outdoors:** recordings on sand or gravel in strong sun and at dusk (REQ-AUT-130) still show
   NEURAL_LIGHT ahead of PERFORMANCE.
3. **Full load:** with object detection and ROS running, all three cameras still deliver their
   frame rate (REQ-AUT-ISS-06, REQ-AUT-120). If not, PERFORMANCE is the fallback.
4. **Heat:** a 60-minute run in the rover's enclosure does not make the Jetson slow down.
5. **The rover's Jetson** gives the same results as the bench Jetson.
