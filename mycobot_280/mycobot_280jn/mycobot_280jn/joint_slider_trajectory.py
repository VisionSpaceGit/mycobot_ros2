import math
from typing import Dict, List, Optional

import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

class JointSliderTrajectoryBridge(Node):
    """Bridge joint_state slider updates into JointTrajectory commands."""

    def __init__(self) -> None:
        super().__init__("joint_slider_trajectory_bridge")
        self.joint_names: List[str] = self.declare_parameter(
            "joint_names",
            [
                "joint1_to_joint2",
                "joint2_to_joint3",
                "joint3_to_joint4",
                "joint4_to_joint5",
                "joint5_to_joint6",
                "joint6_to_joint6output",
            ],
        ).value
        self.joint_state_topic: str = (
            self.declare_parameter("joint_state_topic", "/joint_targets").value
        )
        self.trajectory_topic: str = (
            self.declare_parameter("trajectory_topic", "/arm_controller/joint_trajectory").value
        )
        self.goal_time: float = float(
            self.declare_parameter("goal_time", 0.5).value
        )
        self.min_delta: float = float(
            self.declare_parameter("min_position_delta", 1e-3).value
        )
        self.min_period = Duration(
            seconds=float(self.declare_parameter("min_publish_period", 0.05).value)
        )

        self._publisher = self.create_publisher(
            JointTrajectory, self.trajectory_topic, 10
        )
        self._subscription = self.create_subscription(
            JointState, self.joint_state_topic, self._joint_state_cb, 10
        )

        self._joint_index_map: Optional[Dict[str, int]] = None
        self._last_positions: Optional[List[float]] = None
        self._last_publish_time = self.get_clock().now()

        self.get_logger().info(
            f"Bridging joint states from '{self.joint_state_topic}' "
            f"to JointTrajectory on '{self.trajectory_topic}'"
        )

    def _joint_state_cb(self, msg: JointState) -> None:
        if not msg.name:
            self.get_logger().debug("Received JointState without joint names, skipping.")
            return

        if self._joint_index_map is None:
            self._joint_index_map = self._build_index_map(msg)
            if self._joint_index_map is None:
                return

        positions = [0.0] * len(self.joint_names)
        for idx, joint_name in enumerate(self.joint_names):
            joint_pos = msg.position[self._joint_index_map[joint_name]]
            positions[idx] = joint_pos

        if self._should_skip_publish(positions):
            return

        traj = JointTrajectory()
        now = self.get_clock().now()
        traj.header.stamp = now.to_msg()
        traj.joint_names = self.joint_names

        point = JointTrajectoryPoint()
        point.positions = positions
        point.time_from_start = Duration(seconds=self.goal_time).to_msg()

        traj.points.append(point)
        self._publisher.publish(traj)

        self._last_positions = positions
        self._last_publish_time = now

    def _build_index_map(self, msg: JointState) -> Optional[Dict[str, int]]:
        index_map: Dict[str, int] = {}
        for joint_name in self.joint_names:
            try:
                index_map[joint_name] = msg.name.index(joint_name)
            except ValueError:
                self.get_logger().warning(
                    f"Joint '{joint_name}' not found in JointState message. "
                    "Waiting for matching names."
                )
                return None
        return index_map

    def _should_skip_publish(self, positions: List[float]) -> bool:
        if self._last_positions is None:
            return False

        now = self.get_clock().now()
        elapsed = now - self._last_publish_time
        if elapsed.nanoseconds < self.min_period.nanoseconds:
            # Within deadband window; skip to avoid flooding commands
            return True

        for prev, current in zip(self._last_positions, positions):
            if math.fabs(prev - current) >= self.min_delta:
                return False

        # All joint deltas are within tolerance; no new command needed
        return True


def main(args=None) -> None:
    rclpy.init(args=args)
    node = JointSliderTrajectoryBridge()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
