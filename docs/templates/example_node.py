"""Watch one topic and report when its messages stop arriving.

STYLE EXAMPLE. This file shows what a fully documented node looks like under
docs/documentation-standard.md. It is not part of the rover system until the team decides
it is (it would serve REQ-AUT-270: notice when information stops arriving).

How it works: every incoming message resets a timer. A periodic check compares the time since
the last message with a timeout and publishes ``True`` (alive) or ``False`` (silent). The
status is published on every check, not only on changes, so a node that starts late still
learns the current state within one check period.

Run:
    ros2 run <package_name> topic_watchdog --ros-args -p watched_topic:=/zed/front/odom

Interfaces:
    Subscribes: ``<watched_topic>`` (any message type, see ``watched_type``).
    Publishes:  ``~/alive`` (``std_msgs/msg/Bool``), at ``check_rate_hz``.
"""

import importlib

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time
from std_msgs.msg import Bool


def load_message_class(type_name: str):
    """Import a ROS message class from its full name.

    Args:
        type_name: Message type in ROS form, for example ``"nav_msgs/msg/Odometry"``.

    Returns:
        The message class, for example ``nav_msgs.msg.Odometry``.

    Raises:
        ValueError: If ``type_name`` is not in the form ``package/msg/Name``.
        ImportError: If the package is not installed or has no such message.
    """
    parts = type_name.split("/")
    if len(parts) != 3 or parts[1] != "msg":
        raise ValueError(f"Expected 'package/msg/Name', got '{type_name}'")
    package, _, name = parts
    module = importlib.import_module(f"{package}.msg")
    return getattr(module, name)


class TopicWatchdog(Node):
    """ROS 2 node that publishes whether a watched topic is still receiving messages.

    Parameters (all documented in the package README):
        watched_topic (str): Topic to watch. Default ``/odom``.
        watched_type (str): Message type of that topic. Default ``nav_msgs/msg/Odometry``.
        timeout_s (float): Silence longer than this, in seconds, counts as "lost". Default 1.0.
        check_rate_hz (float): How often the status is published, in hertz. Default 5.0.
    """

    def __init__(self) -> None:
        """Declare parameters, subscribe to the watched topic and start the check timer."""
        super().__init__("topic_watchdog")

        self.watched_topic: str = self.declare_parameter("watched_topic", "/odom").value
        watched_type: str = self.declare_parameter(
            "watched_type", "nav_msgs/msg/Odometry"
        ).value
        self.timeout_s: float = self.declare_parameter("timeout_s", 1.0).value
        check_rate_hz: float = self.declare_parameter("check_rate_hz", 5.0).value

        # Time of the most recent message, or None if none has arrived yet.
        self._last_msg_time: Time | None = None
        # Last published state, kept only so we log changes once instead of every check.
        self._was_alive: bool | None = None

        # Sensor-data QoS (best effort) matches how camera drivers usually publish. With the
        # default "reliable" QoS we would receive nothing from a best-effort publisher and
        # wrongly report the topic as silent.
        self.create_subscription(
            load_message_class(watched_type),
            self.watched_topic,
            self._on_message,
            qos_profile_sensor_data,
        )
        self._alive_pub = self.create_publisher(Bool, "~/alive", 10)
        self.create_timer(1.0 / check_rate_hz, self._check)

        self.get_logger().info(
            f"Watching {self.watched_topic} ({watched_type}), timeout {self.timeout_s:.2f} s"
        )

    def _on_message(self, _msg) -> None:
        """Record the arrival time of a message. The content is not used."""
        self._last_msg_time = self.get_clock().now()

    def _check(self) -> None:
        """Publish whether the watched topic is alive, and log when the state changes."""
        alive = self._is_alive(self.get_clock().now())
        self._alive_pub.publish(Bool(data=alive))

        if alive != self._was_alive:
            # Logged with a timestamp so the gap can be found later in the recording
            # (REQ-AUT-270 asks us to record when information stopped arriving).
            if alive:
                self.get_logger().info(f"{self.watched_topic}: messages arriving")
            else:
                self.get_logger().warn(f"{self.watched_topic}: no message for > {self.timeout_s} s")
            self._was_alive = alive

    def _is_alive(self, now: Time) -> bool:
        """Return True if a message arrived within the timeout.

        Args:
            now: Current ROS time.

        Returns:
            False if no message has ever arrived, or the last one is older than ``timeout_s``.
        """
        if self._last_msg_time is None:
            return False
        silence_s = (now - self._last_msg_time).nanoseconds / 1e9
        return silence_s <= self.timeout_s


def main(args=None) -> None:
    """Entry point used by ``ros2 run``."""
    rclpy.init(args=args)
    node = TopicWatchdog()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass  # Ctrl+C is the normal way to stop the node.
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
