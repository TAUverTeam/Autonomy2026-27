# Documentation standard

This page defines how every piece of Autonomy code is documented. It exists because the team changes
every year: the people who wrote the code will be gone, and the next team must be able to understand,
run and change it from the repository alone.

**The rule: a change is not finished until its documentation is written.** Reviewers reject pull
requests that add or change code without the matching documentation (see the checklist at the end).

---

## Who we write for

Write for a new team member who:

- knows basic Python and has heard of ROS 2,
- has never seen this rover or this code,
- will read your work a year from now, with nobody to ask.

If they would have to ask you a question to use or change your code, the answer belongs in the docs.

## The four levels of documentation

| Level | Where | Answers |
|---|---|---|
| 1. Project | `README.md`, `docs/` | What is this system, how do the parts fit, how do I start? |
| 2. Package | `src/<package>/README.md` | What does this package do, what does it send and receive, how do I run and test it? |
| 3. Code | Docstrings and comments in the source files | What does this file, class or function do, and why is it written this way? |
| 4. Decisions | `docs/decisions/NNNN-title.md` | Why did we choose this option over the others? |

Each level is described below.

---

## Level 1: project documentation

- The root [README.md](../README.md) gives the overview and the reading order for newcomers.
- [docs/README.md](README.md) lists every document.
- The three diagrams in [docs/diagrams/](diagrams/) (hardware, software, logic) are kept up to date.
  **If your change adds, removes or rewires a program, a topic or a device, update the diagram in the
  same pull request.**

## Level 2: package README

Every package in `src/` has a `README.md` copied from
[templates/package-README.md](templates/package-README.md). It must contain:

1. **Purpose**: one paragraph, in plain words.
2. **Where it fits**: which programs feed it and which programs use its output, with a link to the
   software diagram.
3. **Nodes**: one section per node.
4. **Interfaces**: for every topic, service and action, a table row with name, message type,
   direction (in/out), rate and meaning, including **units** and **coordinate frame**.
5. **Parameters**: name, type, default, unit and what it changes.
6. **How to run**: the exact commands.
7. **How to test**: the exact commands, and what a correct result looks like.
8. **Known limitations**: what does not work yet, or works only in some conditions.
9. **Requirements**: the requirement IDs this package helps meet (for example `REQ-AUT-020`).

## Level 3: code

### Language and style

- Python follows [PEP 8](https://peps.python.org/pep-0008/); docstrings use the
  [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).
- C++ (only where speed requires it; see the decisions folder) follows the
  [ROS 2 code style](https://docs.ros.org/en/humble/The-ROS2-Project/Contributing/Code-Style-Language-Versions.html),
  with [Doxygen](https://www.doxygen.nl/) comments (`/** ... */`).
- Code, comments and documentation are written in **English**.

### File header

Every source file starts with a docstring that says what the file is for and where it fits.

```python
"""Watch a topic and report when its messages stop arriving.

Part of the ``autonomy_health`` package. Other nodes use the status this node publishes
to decide what to do when a sensor goes silent (see REQ-AUT-270 and the logic diagram).
"""
```

### Docstrings

Every module, class, public function and method has a docstring. It says:

- what it does (one line, then details if needed),
- each argument, with its **unit**,
- what it returns, with its unit,
- what it raises, if anything.

```python
def heading_error_deg(current_yaw_rad: float, target_yaw_rad: float) -> float:
    """Return the smallest signed angle from the current heading to the target heading.

    The result is wrapped to [-180, 180) so the rover always turns the short way.

    Args:
        current_yaw_rad: Current heading in the ``map`` frame, in radians (0 = +x, counterclockwise positive).
        target_yaw_rad: Desired heading in the same frame, in radians.

    Returns:
        Heading error in degrees. Positive means turn left (counterclockwise).
    """
```

### Comments: explain *why*, not *what*

The code already says what it does. Comments say why it does it that way, especially when the reason
is not obvious: a hardware quirk, a measured value, a workaround, a requirement.

```python
# Bad: says what the code already says.
rate_hz = 5.0  # set rate to 5

# Good: says why.
# 5 Hz is the highest point-cloud rate the Jetson sustained with all three cameras
# and detection running (load test 2026-12-02, docs/measurements/load-test-1.md).
rate_hz = 5.0
```

Every workaround gets a comment that says what problem it works around and when it can be removed.

### Units and frames

Units cause more bugs on robots than anything else. Therefore:

- Use SI units inside the code (metres, radians, seconds), as ROS does
  ([REP 103](https://www.ros.org/reps/rep-0103.html)).
- When a value is not SI, put the unit in its name: `angle_deg`, `timeout_ms`.
- Every pose, point or velocity says which coordinate frame it is in (`map`, `odom`, `base_link`,
  a camera frame). Frame names follow [REP 105](https://www.ros.org/reps/rep-0105.html).

### Magic numbers

No unexplained numbers in the code. A number is either a named constant with a comment, or a ROS
parameter documented in the package README and the config file.

### Configuration files

Every parameter in a YAML config file has a comment with its unit and what it changes. If a value was
chosen by measurement or tuning, say where the measurement is.

```yaml
costmap:
  # Distance from the rover centre to its furthest edge, in metres.
  # Measured on the rover on 2026-11-25 (rover with arm folded).
  robot_radius: 0.45
```

### Custom messages

Every field in a `.msg`, `.srv` or `.action` file has a comment with its meaning and unit.

```
# Mission progress sent to the control station (REQ-AUT-140).
uint8 waypoints_reached     # Number of waypoints reached so far, 0 to 4.
float32 distance_to_next_m  # Straight-line distance to the next waypoint, in metres.
```

## Level 4: decision records

When the team makes a choice that a future member might question, write a short decision record in
[docs/decisions/](decisions/), copied from the template there. Examples: choosing Python or C++,
choosing a path planner, dropping a live map, changing the camera resolution.

A decision record says what the problem was, which options were considered, what was chosen and why.
It is never deleted: if the decision changes, write a new record that replaces the old one and mark the
old one as replaced.

## Measurements

Numbers that drive decisions (computing load, accuracy, detection range) are recorded in
`docs/measurements/`, one file per test, with the date, the setup, the exact commands, the raw results
and the conclusion. Code comments and decision records link to these files.

## Commit messages

```
<package or area>: <what changed, in the imperative>

<why it changed, if not obvious. Link the requirement or issue.>
```

Example: `path_planner: inflate obstacles by the rover radius`

---

## Reviewer checklist

Copy this into every pull request. The reviewer ticks each item or explains why it does not apply.

- [ ] Every new or changed file has a header docstring.
- [ ] Every new or changed class and function has a docstring with units.
- [ ] Non-obvious code and every workaround has a comment explaining why.
- [ ] No unexplained numbers; parameters are documented in the README and the config file.
- [ ] The package README is updated (interfaces, parameters, how to run and test).
- [ ] The diagrams are updated if programs, topics or devices changed.
- [ ] A decision record is written if a significant choice was made.
- [ ] Measurements that support a number are saved in `docs/measurements/`.
- [ ] A new team member could run and test this from the README alone.
