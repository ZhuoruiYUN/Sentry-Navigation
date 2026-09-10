#!/usr/bin/env python3
"""Continuously sweep the simulated yaw gimbal to move MID360 blind sectors."""

import math

import rclpy
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionClient
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectoryPoint


class GimbalScanSweep(Node):
    def __init__(self):
        super().__init__("gimbal_scan_sweep")
        self.limit = self.declare_parameter("limit", 1.50).value
        self.speed = self.declare_parameter("speed", 1.20).value
        self.client = ActionClient(
            self,
            FollowJointTrajectory,
            "/gimbal_yaw_controller/follow_joint_trajectory",
        )
        self.target_sign = 1.0
        self.first_move = True
        self.busy = False
        self.create_timer(0.2, self.tick)

    def tick(self):
        if self.busy or not self.client.server_is_ready():
            return

        target = self.target_sign * self.limit
        distance = self.limit if self.first_move else 2.0 * self.limit
        duration = max(0.5, distance / self.speed)

        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = ["gimbal_yaw_joint"]
        point = JointTrajectoryPoint()
        point.positions = [target]
        point.time_from_start.sec = int(duration)
        point.time_from_start.nanosec = int((duration % 1.0) * 1_000_000_000)
        goal.trajectory.points = [point]

        self.busy = True
        self.first_move = False
        self.get_logger().info(
            f"Sweeping gimbal to {math.degrees(target):.1f} deg in {duration:.2f} s"
        )
        self.client.send_goal_async(goal).add_done_callback(self.goal_response)

    def goal_response(self, future):
        handle = future.result()
        if not handle.accepted:
            self.get_logger().warn("Gimbal sweep goal was rejected")
            self.busy = False
            return
        handle.get_result_async().add_done_callback(self.goal_result)

    def goal_result(self, future):
        wrapped = future.result()
        if wrapped.result.error_code != 0:
            self.get_logger().warn(
                f"Gimbal sweep failed: {wrapped.result.error_string}"
            )
        else:
            self.target_sign *= -1.0
        self.busy = False


def main():
    rclpy.init()
    node = GimbalScanSweep()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
