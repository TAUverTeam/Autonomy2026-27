# Getting started

From a new laptop to running code on the Jetson. If any step here is wrong or missing, fix this page
in your first pull request: that is the best way to learn the workflow.

## 1. Accounts and access

- A GitHub account, added to the **TAUverTeam** organisation (ask the team leader).
- Lab access, and the Jetson password (ask the team leader; it is never written in the repository).
- Powering the rover requires a member of the power team. The bench Jetson can be powered alone.

## 2. Tools on your laptop

| Tool | What for |
|---|---|
| [Git](https://git-scm.com/) | Getting and sharing code |
| [VS Code](https://code.visualstudio.com/) with the *Remote - SSH* extension | Editing code directly on the Jetson |
| An SSH client (built into Windows 10+, macOS and Linux) | Logging in to the Jetson |
| [draw.io](https://app.diagrams.net/) | Editing the diagrams |

Optional: Ubuntu 22.04 with ROS 2 Humble (native, dual boot or WSL 2) to build and run nodes on your
laptop without the Jetson. The ZED cameras need an NVIDIA GPU and the ZED SDK, so camera nodes run
on the Jetson.

## 3. Connect to a Jetson

Both Jetsons use the user name `tauver`.

**Over the USB-C cable** (simplest): connect your laptop to the Jetson's USB-C port. The Jetson
appears as a network device at a fixed address:

```bash
ssh tauver@192.168.55.1
```

**Over an Ethernet cable** directly between laptop and Jetson: the bench Jetson has the fixed address
`192.168.1.10`. Give your laptop a fixed address on the same network (for example `192.168.1.20`,
mask `255.255.255.0`), then:

```bash
ssh tauver@192.168.1.10
```

**With a monitor**: the dev-kit carrier has DisplayPort only. Use a DisplayPort monitor or a
DisplayPort-to-HDMI cable. A laptop cannot be used as the screen.

### Log in without typing the password every time

Create a key on your laptop once, then copy it to the Jetson:

```bash
ssh-keygen -t ed25519
```

On Linux or macOS:

```bash
ssh-copy-id tauver@192.168.55.1
```

On Windows (PowerShell has no `ssh-copy-id`): open `C:\Users\<you>\.ssh\id_ed25519.pub` in Notepad,
copy the single line, log in to the Jetson, and append it with `nano ~/.ssh/authorized_keys`.
Pasting it with a PowerShell pipe can add invisible characters that break the key.

## 4. Get the code and build it

On the Jetson (or your Ubuntu laptop):

```bash
git clone https://github.com/TAUverTeam/Exodus2026.27_Autonomy.git ~/Exodus2026.27_Autonomy
cd ~/Exodus2026.27_Autonomy
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -y
colcon build --symlink-install
source install/setup.bash
```

`--symlink-install` means changes to Python files take effect without rebuilding.

## 5. Useful commands on the Jetson

| Command | Shows |
|---|---|
| `tegrastats` | CPU, GPU, memory, temperature and power, once per second |
| `jtop` | The same, as an interactive screen (if `jetson-stats` is installed) |
| `ros2 node list` | Running ROS nodes |
| `ros2 topic list` / `ros2 topic hz <topic>` | Topics, and how often a topic publishes |
| `ZED_Explorer` | View a ZED camera directly, without ROS |
| `lsusb -t` | USB devices and the speed each one connected at (`5000M` = USB 3) |

## 6. Next

Read [documentation-standard.md](documentation-standard.md) and [../CONTRIBUTING.md](../CONTRIBUTING.md)
before your first pull request.
