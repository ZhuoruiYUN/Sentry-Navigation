#!/usr/bin/env python3
"""Publish the calibrated initial pose for the RMUL 3v3 simulation map."""

import math
import time

import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data


def main():
    rclpy.init()
    node = Node(
        "sentry_initial_pose",
        parameter_overrides=[
            Parameter("use_sim_time", Parameter.Type.BOOL, True),
        ],
    )
    node.declare_parameter("x", -4.8)
    node.declare_parameter("y", 2.8)
    node.declare_parameter("yaw", 0.0)
    # AMCL subscribes to /initialpose with sensor-data (best-effort) QoS.
    publisher = node.create_publisher(
        PoseWithCovarianceStamped, "/initialpose", qos_profile_sensor_data
    )

    # Wait until Gazebo has published a non-zero simulation clock.
    while rclpy.ok() and node.get_clock().now().nanoseconds == 0:
        rclpy.spin_once(node, timeout_sec=0.1)

    # A short-lived publisher can otherwise finish before DDS discovers AMCL.
    discovery_deadline = time.monotonic() + 10.0
    while (
        rclpy.ok()
        and publisher.get_subscription_count() == 0
        and time.monotonic() < discovery_deadline
    ):
        rclpy.spin_once(node, timeout_sec=0.1)

    message = PoseWithCovarianceStamped()
    message.header.frame_id = "map"
    message.pose.pose.position.x = node.get_parameter("x").value
    message.pose.pose.position.y = node.get_parameter("y").value
    yaw = node.get_parameter("yaw").value
    message.pose.pose.orientation.z = math.sin(yaw / 2.0)
    message.pose.pose.orientation.w = math.cos(yaw / 2.0)
    message.pose.covariance[0] = 0.16
    message.pose.covariance[7] = 0.16
    message.pose.covariance[35] = math.radians(15.0) ** 2
    # A zero stamp asks AMCL to use the latest available odom/base_link TF and
    # avoids simulation-clock/TF-cache extrapolation at startup.
    message.header.stamp.sec = 0
    message.header.stamp.nanosec = 0
    node.get_logger().info(
        f"Publishing initial pose: x={message.pose.pose.position.x:.3f}, "
        f"y={message.pose.pose.position.y:.3f}, yaw={yaw:.3f}"
    )
    for _ in range(30):
        publisher.publish(message)
        rclpy.spin_once(node, timeout_sec=0.1)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
