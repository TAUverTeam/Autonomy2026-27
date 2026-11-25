# What we learned from the 2025/26 season

The 2025/26 Autonomy team built a working obstacle-avoidance demo on a camera test cart and tested it
in experiments in July–August 2026. We do not reuse their code
([decision 0001](decisions/0001-new-code-base.md)), but their results, settings and mistakes save us
a lot of time. This page collects them.

Collected in November 2026 from their repository, their handover documents and inspection of the
hardware. Items marked **(check)** are not yet confirmed by the 2026/27 team.

---

## Where their material is

| What | Where |
|---|---|
| Code | [TAUverIL/Exodus_Autonomy](https://github.com/TAUverIL/Exodus_Autonomy), branch `testing`, last commit `53454f0` (2 September 2026). Autonomy code is under `mobility_ctrl/src/`. |
| Handover documents in the repository | `mobility_ctrl/JETSON_DEPLOYMENT.md`, `SESSION_LOG.md`, `TEAM_TASKS.md`, `NAVIGATION_SETUP.md` |
| Project book, final presentation, figures, analysis scripts | **Only on the bench Jetson** (the second Jetson, not on the rover), in `~/Exodus2025/`. Not in Git. |
| Experiment recordings (107 `trial_*` folders, including the runs used in their final report) | **Only on the bench Jetson**, in `~/bags`, `~/Exodus2025` and `~/Exodus2025/mobility_ctrl`. |

> **Action:** the project book and recordings exist in one place only. Back them up to the team's
> shared storage before anything else happens to that Jetson.

## What their system did

Their pipeline, from cameras to driving command:

```
3 × ZED 2i ──► ZED ROS 2 driver (multi-camera)
                 │
                 ├─ front camera point cloud ──► relay ──► Nav2 costmap (obstacle grid)
                 │                                             │
                 ├─ front camera odometry ──► relay ──► TF (odom → base_link)
                 │                                             ▼
                 │                                     A* path planner
                 │                                             ▼
                 │                          waypoint → steering angle + distance
                 │
                 ├─ all 3 cameras ──► YOLO detector ──► grid mapper ──► separate occupancy grid
                 └─ all 3 cameras ──► RTAB-Map (live 3D map; started but its output not used)
```

Useful ideas to keep in mind (not code to copy):

- **Nav2's costmap** turned point clouds into an obstacle grid without custom code.
- **A\*** on that grid was enough for the obstacle courses they tested.
- They planned at a low rate (0.5 Hz) with waypoints spaced 0.2 m apart.

## The three-camera problem

The team reported that the Jetson could not handle all three cameras at once, so in the end
**only the front camera fed the obstacle map**; the side cameras were left out of the costmap.

What we know so far:

- At the same time they ran: three cameras computing depth, YOLO object detection on all three
  cameras, and RTAB-Map. **RTAB-Map's output was not used**, so part of the load was wasted.
- Camera settings in their final config: depth mode `PERFORMANCE`, point clouds at 5 Hz,
  grab rate 15 fps, a reduced camera resolution.
- In November 2026 we confirmed **the cameras and their cables all connect at USB 3 (SuperSpeed)**,
  so the cables are not the bottleneck. On the Jetson dev-kit carrier the USB-A ports share one
  internal hub, which is still worth checking under load **(check)**.
- There is **no recorded measurement** of what the Jetson can run at once. That is why REQ-AUT-ISS-06
  asks us to measure it before deciding on camera settings or a second computer.

## Things that caught them out

These are traps to avoid in our design:

- **Camera identity.** Each ZED's video device reports a placeholder serial (`OV0001`); the real serial
  is on its sensor (HID) device. Cameras must be told apart by real serial, never by USB port order.
  Their config also had a stale comment naming the wrong camera as front.
- **The ZED driver needed local patches** to run three cameras (documented in their
  `zed_overrides/README.md`). Any patch we need must be documented and kept outside the driver's code.
- **Position came from the front camera alone**, through a relay started by hand. There was no wheel
  odometry and no fusion of sources, and REQ-AUT-240 asks for 0.2 m and 5° at all times.
- **Stand-ins were left in place**: a node faked the "autonomous" rover mode. C&C never sent the
  rover mode, the emergency stop or wheel odometry.
- **The driving command did not match C&C's.** Autonomy published a steering angle and a distance,
  while C&C's drive software listens to `/cmd_vel` (speed and turn rate). REQ-AUT-ISS-07 asks for one
  common command agreed with C&C.
- **Set up for the cart, not the rover**: robot radius 0.35 m, camera positions of the cart
  (REQ-AUT-ISS-10).
- **YOLO positions** were hard-coded to straight ahead (x = 0, y = 0) in their January task list;
  whether this was fixed later is unknown **(check)**.
- **Repository hygiene**: build output (`build/`, `install/`, `log/`) was committed, several teams
  shared one repository, and recordings and the project book were never pushed anywhere.
- **The bench Jetson's clock** was two weeks off (it has no internet), which makes recordings and logs
  hard to line up. Set the time before recording.

## Hardware they left us

See [hardware.md](hardware.md) for details: two Jetson Orin NX 16 GB (one on the rover, one on the
bench), three ZED 2i cameras with known serials and mounting positions, and the software versions
installed on them.
