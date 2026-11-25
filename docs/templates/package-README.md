<!--
  Package README template.
  Copy this file to src/<your_package>/README.md and replace every part in <angle brackets>.
  Delete sections that truly do not apply, and say why in one line instead of leaving them empty.
  Rules: docs/documentation-standard.md
-->

# <package_name>

<One paragraph in plain words: what this package does and why the rover needs it.>

**Owner:** <name> · **Status:** <experimental / tested on bench / tested on rover (tag vYYYY.MM.DD)>
· **Requirements:** <REQ-AUT-xxx, REQ-AUT-yyy>

## Where it fits

<Which programs feed this package and which programs use its output. Link the software diagram.>

```
<upstream node> --/topic_a--> [this node] --/topic_b--> <downstream node>
```

See the [software diagram](../../docs/diagrams/).

## Nodes

### `<node_name>`

<What this node does, in two or three sentences.>

#### Subscribed topics

| Topic | Type | Rate | Meaning |
|---|---|---|---|
| `/example/in` | `sensor_msgs/msg/PointCloud2` | 5 Hz | <What it contains. Frame: `<frame>`. Units: <units>.> |

#### Published topics

| Topic | Type | Rate | Meaning |
|---|---|---|---|
| `/example/out` | `nav_msgs/msg/OccupancyGrid` | 1 Hz | <What it contains. Frame: `<frame>`. Units: <units>.> |

#### Services and actions

<None, or a table like the ones above.>

#### Parameters

| Name | Type | Default | Unit | What it changes |
|---|---|---|---|---|
| `rate_hz` | double | 5.0 | Hz | <How often the node publishes. Why this default.> |

#### TF frames

<Frames this node reads (lookups) and frames it publishes, or "None".>

## How to build

```bash
colcon build --packages-select <package_name> --symlink-install
source install/setup.bash
```

## How to run

```bash
ros2 launch <package_name> <file>.launch.py
```

<What you should see when it works: log lines, topics appearing, `ros2 topic hz` values.>

## How to test

```bash
colcon test --packages-select <package_name>
colcon test-result --verbose
```

<Manual tests too: which recording to play, what to look at in RViz, what result counts as a pass.>

## Known limitations

- <What does not work yet, or works only in some conditions.>

## Further reading

- <Decision records, measurements, papers or library docs this package relies on.>
