# TAUver Autonomy

Autonomy software for **Exodus**, the Tel Aviv University Mars rover (team TAUver), built for the
**European Rover Challenge (ERC)**.

This repository holds the code that lets the rover drive by itself: it sees the terrain through its
cameras, knows where it is, plans a safe path to each waypoint and tells the drive system how to move.

> **Status (November 2026): fresh start.** The 2026/27 team is building a new code base from scratch.
> Last season's work is used as a source of knowledge, not as code. See
> [docs/previous-season.md](docs/previous-season.md) for what we learned from it and
> [docs/decisions/0001-new-code-base.md](docs/decisions/0001-new-code-base.md) for why we restarted.
>
> Before any rover code is written, the team draws three diagrams (hardware, software, logic).
> See [docs/diagrams/](docs/diagrams/).

---

## Contents

- [What the autonomy system must do](#what-the-autonomy-system-must-do)
- [The system at a glance](#the-system-at-a-glance)
- [Repository layout](#repository-layout)
- [Getting started](#getting-started)
- [Documentation](#documentation)
- [How we work](#how-we-work)
- [Versions](#versions)
- [Team](#team)

---

## What the autonomy system must do

At ERC the rover must complete a traverse without anyone touching the controls:

1. The operators give the rover the coordinates of **four waypoints and a finish point** before the run.
2. The rover drives to all of them, in any order, within the task time, from a randomly drawn start.
3. On the way it must **avoid obstacles** (rocks, trenches, other rovers, people) and must not tip over
   or get stuck.
4. It must **detect the ERC landmarks** (numbered square markers), read their numbers and work out where
   they are relative to the rover.
5. During the run it sends the control station only its position and mission status, no camera images.
6. Right after the run the team shows the judges proof that the traverse was autonomous.

The full list, with the status of each item, is in [docs/requirements.md](docs/requirements.md).
The source of truth is the team requirements spreadsheet (`TAUver Requirements 2026_2027 - SRR`).

## The system at a glance

| Part | What we use (as of November 2026) |
|---|---|
| Main computer | NVIDIA Jetson Orin NX 16 GB, JetPack 6 (L4T R36.4.7), Ubuntu 22.04 |
| Robot framework | ROS 2 Humble |
| Cameras | 3 × Stereolabs ZED 2i on USB 3 (front, rear-left, rear-right), ZED SDK 5.1.1 |
| GPU libraries | CUDA 12.6 |
| Drive system | Owned by the C&C team; Autonomy sends it driving commands |

This table describes the hardware we inherited. The real wiring is documented in the hardware
diagram ([docs/diagrams/](docs/diagrams/)) once it is drawn, and details are in
[docs/hardware.md](docs/hardware.md).

## Repository layout

```
Exodus2026.27_Autonomy/
├── README.md              ← you are here
├── CONTRIBUTING.md        ← how to add code (branches, reviews, checklists)
├── CHANGELOG.md           ← tested versions and their results
├── docs/
│   ├── README.md          ← map of all documentation
│   ├── documentation-standard.md   ← the rules every piece of code follows
│   ├── getting-started.md ← set up your laptop, connect to the Jetson, build
│   ├── hardware.md        ← computers, cameras, cables, serial numbers
│   ├── requirements.md    ← our ERC requirements and their status
│   ├── previous-season.md ← what we learned from the 2025/26 team
│   ├── diagrams/          ← hardware, software and logic diagrams
│   ├── decisions/         ← why we chose what we chose (one file per decision)
│   ├── measurements/      ← test results behind every number we rely on
│   └── templates/         ← copy these when you start a new package
├── tools/                 ← test and measurement tools, not part of the rover software
│   ├── zed_load_test/     ← measures camera load on the Jetson (REQ-AUT-ISS-06)
│   └── zed_depth_compare/ ← records the cameras and compares depth modes
└── src/                   ← ROS 2 packages (one folder per package)
```

This is a standard ROS 2 workspace: `src/` holds the packages, and `colcon build` creates
`build/`, `install/` and `log/` next to it. Those three folders are **never** committed.

## Getting started

New to the team? Read these in order:

1. This README.
2. [docs/getting-started.md](docs/getting-started.md): install the tools, connect to the Jetson, build.
3. [docs/documentation-standard.md](docs/documentation-standard.md): how we write and document code.
4. [CONTRIBUTING.md](CONTRIBUTING.md): how to get your code into the repository.
5. The diagrams in [docs/diagrams/](docs/diagrams/), to see how the parts fit together.

Quick build (on a machine with ROS 2 Humble installed):

```bash
git clone https://github.com/TAUverTeam/Exodus2026.27_Autonomy.git
cd Exodus2026.27_Autonomy
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

## Documentation

All documentation lives in this repository, next to the code it describes, so that it is updated in
the same change as the code. Start at [docs/README.md](docs/README.md).

Every package in `src/` has its own `README.md` explaining what it does, what it sends and receives,
its parameters, and how to run and test it.

## How we work

- **No code without documentation.** A change is finished only when its documentation is written.
  The rules are in [docs/documentation-standard.md](docs/documentation-standard.md).
- **Every change goes through a pull request** and is reviewed by another team member before it
  reaches `main`. See [CONTRIBUTING.md](CONTRIBUTING.md).
- **Important choices are written down** as short decision records in
  [docs/decisions/](docs/decisions/), so future members know *why*, not only *what*.
- **Measure, then decide.** Computing load, camera settings and accuracy claims are backed by
  recorded measurements, not guesses.

## Versions

Versions that were tested on the rover are marked with a Git tag, for example `v2027.03.14`
(the test date), and listed in [CHANGELOG.md](CHANGELOG.md) with what was tested and the result.
If you need code that is known to work, check out the latest tag, not `main`.

## Team

Autonomy team, 2026/27 season:

| Name | Role | Contact |
|---|---|---|
| _to fill in_ | Team leader | |
| | | |

This repository: [TAUverTeam/Exodus2026.27_Autonomy](https://github.com/TAUverTeam/Exodus2026.27_Autonomy).

Previous season: the 2025/26 Autonomy team. Their code is in the
[TAUverIL/Exodus_Autonomy](https://github.com/TAUverIL/Exodus_Autonomy) repository (branch `testing`).
