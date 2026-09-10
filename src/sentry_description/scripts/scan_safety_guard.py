#!/usr/bin/env python3
"""Fail-closed lidar guard for the kinematic planar simulator."""

import math

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan


class ScanSafetyGuard(Node):
    def __init__(self):
        super().__init__("scan_safety_guard")
        self.stop_distance = self.declare_parameter("stop_distance", 0.55).value
        self.rotation_stop_distance = self.declare_parameter(
            "rotation_stop_distance", 0.50
        ).value
        self.scan_timeout = self.declare_parameter("scan_timeout", 0.30).value
        self.command_timeout = self.declare_parameter("command_timeout", 0.25).value
        self.motion_half_angle = math.radians(
            self.declare_parameter("motion_half_angle_deg", 60.0).value
        )
        self.scan = None
        self.scan_received_at = None
        self.command = Twist()
        self.command_received_at = None
        self.last_warning_at = None
        self.create_subscription(
            LaserScan, "/scan", self.on_scan, qos_profile_sensor_data
        )
        self.create_subscription(Twist, "/cmd_vel", self.on_command, 10)
        self.publisher = self.create_publisher(Twist, "/cmd_vel_safe", 10)
        self.create_timer(0.05, self.publish_safe_command)

    def on_scan(self, scan):
        self.scan = scan
        self.scan_received_at = self.get_clock().now()

    def on_command(self, command):
        self.command = command
        self.command_received_at = self.get_clock().now()

    def age(self, received_at):
        if received_at is None:
            return math.inf
        return (self.get_clock().now() - received_at).nanoseconds * 1e-9

    def warn_throttled(self, message):
        now = self.get_clock().now()
        if self.last_warning_at is None or (now - self.last_warning_at).nanoseconds > 1_000_000_000:
            self.get_logger().warn(message)
            self.last_warning_at = now

    def valid_ranges(self):
        if self.scan is None:
            return
        for index, distance in enumerate(self.scan.ranges):
            if not math.isfinite(distance):
                continue
            if distance < self.scan.range_min or distance > self.scan.range_max:
                continue
            angle = self.scan.angle_min + index * self.scan.angle_increment
            yield angle, distance

    def obstacle_in_motion_direction(self, vx, vy):
        heading = math.atan2(vy, vx)
        for angle, distance in self.valid_ranges():
            delta = math.atan2(math.sin(angle - heading), math.cos(angle - heading))
            if abs(delta) <= self.motion_half_angle and distance < self.stop_distance:
                return True
        return False

    def obstacle_too_close_to_rotate(self):
        return any(
            distance < self.rotation_stop_distance
            for _, distance in self.valid_ranges()
        )

    def publish_safe_command(self):
        safe = Twist()
        if self.age(self.command_received_at) > self.command_timeout:
            self.publisher.publish(safe)
            return
        if self.age(self.scan_received_at) > self.scan_timeout:
            self.warn_throttled("Blocked motion: /scan is missing or stale")
            self.publisher.publish(safe)
            return

        command = self.command
        speed = math.hypot(command.linear.x, command.linear.y)
        if speed > 1e-4 and not self.obstacle_in_motion_direction(
            command.linear.x, command.linear.y
        ):
            safe.linear = command.linear
        elif speed > 1e-4:
            self.warn_throttled(
                f"Blocked translation: obstacle within {self.stop_distance:.2f} m"
            )

        if abs(command.angular.z) > 1e-4:
            if self.obstacle_too_close_to_rotate():
                self.warn_throttled(
                    "Blocked rotation: obstacle too close to the robot envelope"
                )
            else:
                safe.angular = command.angular
        self.publisher.publish(safe)


def main():
    rclpy.init()
    node = ScanSafetyGuard()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
