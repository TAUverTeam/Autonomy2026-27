# 0002. Python by default, C++ only where speed is measured to matter

- **Status:** Proposed (to confirm at a team meeting)
- **Date:** 2026-11-18
- **Decided by:** _to fill in_
- **Requirements:** REQ-AUT-ISS-04, REQ-AUT-120

## Problem

ROS 2 nodes can be written in Python or C++. We need one default so that the code base stays readable
for a team that changes every year.

## Options considered

1. **Python everywhere.** Pros: easiest to read and change, most members know it, fastest to write.
   Cons: slower; heavy per-point work (for example looping over a point cloud) can load the CPU.
2. **C++ everywhere.** Pros: fastest, lowest CPU use. Cons: slower to write and review; fewer members
   know it; harder for next year's team.
3. **Python by default, C++ for measured hot spots.**

## Decision

Option 3. Write nodes in Python. Rewrite a node in C++ only when a measurement shows it uses too much
of the Jetson (REQ-AUT-120), and record that measurement and the rewrite in a decision record.

## Why

- Readability for future members is a top goal (REQ-AUT-ISS-04).
- The heaviest work on the rover (camera depth, object detection) runs inside the ZED SDK and on the
  GPU, not in our Python code. Most of our own nodes handle small messages at low rates.
- Heavy array work in Python can use NumPy, which runs in compiled code.

## Consequences

- The load test (REQ-AUT-ISS-06) must show the CPU use per node, so hot spots are found by measurement.
- C++ packages follow the same documentation standard (Doxygen comments instead of docstrings).
