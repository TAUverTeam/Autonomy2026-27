# Diagrams

The three diagrams that come **before any new code** (set by the project head; REQ-AUT-ISS-01/02/03).
They are drawn from scratch to match the rover as it is today. Last season's design-review diagrams
are a guide only.

| Diagram | Shows | Requirement | Files | Status |
|---|---|---|---|---|
| Hardware | Every device in Autonomy's part of the rover, what it connects to, and the connection type (USB 3, Ethernet, CAN, power) | REQ-AUT-ISS-01 | `hardware.drawio`, `hardware.png` | Not started |
| Software | Every program, what it does, and what it sends to and receives from other programs and other teams (topic names and message types) | REQ-AUT-ISS-02 | `software.drawio`, `software.png` | Not started |
| Logic | Every situation the rover can meet and what it does in each: normal driving, obstacle ahead, lost radio link, lost wheel data, motor fault, stuck, emergency stop | REQ-AUT-ISS-03 | `logic.drawio`, `logic.png` | Not started |

## How to keep them

- Draw in [draw.io / diagrams.net](https://app.diagrams.net/) (free, works in the browser and offline).
- Commit the editable source (`.drawio`) **and** an exported image (`.png`) so the diagram can be
  seen on GitHub and still be edited later.
- When a change adds, removes or rewires a device, program or topic, update the diagram in the same
  pull request.
- Put the date and the Git tag or commit the diagram matches in a corner of the diagram.
