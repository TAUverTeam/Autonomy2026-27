# Hardware

Facts about the computers and sensors Autonomy uses. The wiring between them is shown in the hardware
diagram ([diagrams/](diagrams/), REQ-AUT-ISS-01). Update this page whenever hardware changes.

Last checked: 18 November 2026.

## Computers

| | Rover Jetson | Bench Jetson |
|---|---|---|
| Where | On the rover | In the lab, not on the rover |
| Model | Jetson Orin NX 16 GB **(check)** | Jetson Orin NX 16 GB, Engineering Reference Developer Kit |
| Storage | **(check)** | 512 GB NVMe SSD |
| Software | **(check)** | JetPack 6 (L4T R36.4.7), Ubuntu 22.04.5, ROS 2 Humble, ZED SDK 5.1.1, CUDA 12.6 |
| Power | From the rover's power system, through a converter (power team) | 19 V barrel jack |
| Network | Ethernet to the rover access point | Fixed address `192.168.1.10` on Ethernet |
| Login user | `tauver` | `tauver` |
| Notes | Powering it requires a power-team member | Holds last season's recordings and project book; candidate second computer (REQ-AUT-ISS-05) and test bench for the load test (REQ-AUT-ISS-06). Clock not synced (no internet). |

Passwords are not written in this repository. Ask the team leader.

Ports on the dev-kit carrier: DisplayPort (no HDMI), 4 × USB-A, 1 × USB-C, Gigabit Ethernet, DC jack.

## Cameras

Three Stereolabs **ZED 2i** stereo cameras, numbered with tape labels.

| Label | Serial | Position on the mast | Yaw (last season's config) |
|---|---|---|---|
| 2 | 31718458 | Front | 0 rad |
| 1 | 32514439 | Rear-right | −2.094 rad (−120°) |
| 3 | 33289078 | Rear-left | +2.094 rad (+120°) |

- Each camera has two USB functions: the video stream (USB 3 SuperSpeed) and an internal USB 2 hub
  carrying its motion and environment sensors (HID). **The real serial number is on the HID part**;
  the video part reports the placeholder `OV0001`.
- All three cameras and their cables were tested at USB 3 on a laptop (USBView, 17 November 2026).
- The cables are blue; the cable for camera 1 is about twice as long as the others.
- The camera mast was off the rover in November 2026. Mounting angles above are from last season's
  configuration and have not been measured **(check)**.

**Depth mode: NEURAL_LIGHT** for all three cameras ([decision 0003](decisions/0003-depth-mode-neural-light.md)).

There is also a ZED camera on the robotic arm (Arm team's). It is not part of Autonomy's system.
