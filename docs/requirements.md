# Requirements

Autonomy's requirements for 2026/27 and where each one stands. The source of truth is the team
spreadsheet `TAUver Requirements 2026_2027 - SRR (Telecom, Autonomy, C&C)` (v73 at the time of
writing), sheet `09_Autonomy`. This page tracks **progress**; if a requirement's wording changes,
change it in the spreadsheet first.

Update the Status and Where columns in the same pull request that makes progress on a requirement.

**Status values:** Not started · In progress · Done (with link to proof) · Decided not to do (with
link to decision record).
**Priority:** M = Mandatory, G = Design goal, O = Optional.

## Issues to resolve first (from last season)

| ID | Title | Pri. | Status | Where |
|---|---|---|---|---|
| REQ-AUT-ISS-01 | Hardware diagram, drawn from scratch | M | Not started | [diagrams/](diagrams/) |
| REQ-AUT-ISS-02 | Software diagram, drawn from scratch | M | Not started | [diagrams/](diagrams/) |
| REQ-AUT-ISS-03 | Logic diagram: every situation and the rover's response | M | Not started | [diagrams/](diagrams/) |
| REQ-AUT-ISS-04 | One clean, documented code base a new member can build, tested version marked | M | In progress | This repository; [decision 0001](decisions/0001-new-code-base.md) |
| REQ-AUT-ISS-05 | Enough on-board computing power (second computer?) | M | Not started | Bench Jetson is a candidate ([hardware.md](hardware.md)) |
| REQ-AUT-ISS-06 | Measured load on the main computer | M | In progress | Cameras alone measured: [2026-11-25](measurements/2026-11-25-zed-load-test-3-cameras.md). Detection and ROS still to test |
| REQ-AUT-ISS-07 | One common driving command with C&C and the joystick/GUI | M | Not started | Interface document with C&C |
| REQ-AUT-ISS-08 | Recognise ERC objects and read landmark markers, on the rover | M | Not started | |
| REQ-AUT-ISS-09 | Four waypoints and the finish in one run, at ERC distances | M | Not started | |
| REQ-AUT-ISS-10 | Navigation configured for the rover, not the test cart | M | Not started | |
| REQ-AUT-ISS-11 | Decide whether a live map is needed, from the measured load | M | Not started | `decisions/` |

## Design, interfaces and computing

| ID | Title | Pri. | Status | Where |
|---|---|---|---|---|
| REQ-AUT-170 | Organised code base on GitHub with README and marked versions | M | In progress | This repository |
| REQ-AUT-180 | Enough on-board computing power for cameras and detection | M | Not started | See ISS-05 |
| REQ-AUT-120 | Autonomy runs within its share of the main computer | G | Not started | |
| REQ-AUT-110 | Information exchanged with C&C, per the interface document | M | Not started | |
| REQ-AUT-270 | Notice and handle information that stops arriving | M | Not started | Logic diagram |
| REQ-OPS-140 | Power allowance for a 60-minute task (Autonomy's part) | M | Not started | With the power team |

## Perception

| ID | Title | Pri. | Status | Where |
|---|---|---|---|---|
| REQ-AUT-130 | Cameras and detection work in low light and strong sun | M | Not started | |
| REQ-AUT-020 | Detect obstacles ≥ 20 cm high from ≥ 2 m away | M | Not started | |
| REQ-AUT-200 | Recognise ERC objects (landmarks, rocks, trenches, rovers, people, task objects) | M | Not started | |
| REQ-AUT-080 | Detect landmarks, read their numbers, locate them relative to the rover | M | Not started | |

## Navigation

| ID | Title | Pri. | Status | Where |
|---|---|---|---|---|
| REQ-AUT-240 | Position within 0.2 m and heading within 5° at all times | M | Not started | |
| REQ-AUT-250 | Build a live map and align it with the ERC map (if ISS-11 says so) | G | Not started | |
| REQ-AUT-220 | Follow the path within 0.3 m sideways and 5° heading, four-wheel steering | M | Not started | |
| REQ-FUN-240 | Avoid collision with other rovers and obstacles | M | Not started | |
| REQ-AUT-090 | Do not tip over or get stuck | M | Not started | |

## The autonomous task

| ID | Title | Pri. | Status | Where |
|---|---|---|---|---|
| REQ-AUT-040 | Reach the 4 waypoints in any order, then the finish, within the task time | M | Not started | |
| REQ-OPS-050 | Hands off the controls during the task | M | Not started | |
| REQ-AUT-140 | Send the station only position and mission status, no images | M | Not started | |
| REQ-AUT-050 | Show the judges proof of autonomy right after the run | M | Not started | |
| REQ-AUT-100 | Find position again and continue after being moved back | O | Not started | |
| REQ-AUT-150 | Decide which parts of other tasks to automate | G | Not started | `decisions/` |

## ERC rules and documents

| ID | Title | Pri. | Status | Where |
|---|---|---|---|---|
| REQ-AUT-060 | Document all navigation sensors and modes; competition setup matches the approved one | M | Not started | [hardware.md](hardware.md) |
| REQ-AUT-070 | No landmarks or beacons of our own outside the start area | M | Not started | |
| REQ-AUT-280 | Autonomy's part of the ERC reports, video and requirements table | M | Not started | |
