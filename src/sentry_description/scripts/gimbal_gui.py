#!/usr/bin/env python3
"""Small desktop controller for the simulated sentry gimbal yaw joint."""

import math
import tkinter as tk
from tkinter import ttk

import rclpy
from rclpy.action import ActionClient
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint


class GimbalGui:
    def __init__(self):
        rclpy.init()
        self.node = rclpy.create_node("sentry_gimbal_gui")
        self.client = ActionClient(
            self.node,
            FollowJointTrajectory,
            "/gimbal_yaw_controller/follow_joint_trajectory",
        )

        self.root = tk.Tk()
        self.root.title("Sentry Gimbal Yaw")
        self.root.resizable(False, False)
        panel = ttk.Frame(self.root, padding=16)
        panel.grid()

        self.angle = tk.DoubleVar(value=0.0)
        self.duration = tk.DoubleVar(value=1.0)
        self.status = tk.StringVar(value="Waiting for controller...")
        self.value = tk.StringVar()

        ttk.Label(panel, text="Yaw target").grid(row=0, column=0, columnspan=3)
        self.slider = ttk.Scale(
            panel, from_=-180, to=180, variable=self.angle,
            command=self._show_angle,
        )
        self.slider.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(6, 0))
        self.slider.bind("<ButtonRelease-1>", lambda _: self.send_goal())
        ttk.Label(panel, textvariable=self.value, anchor="center").grid(
            row=2, column=0, columnspan=3, pady=(2, 10)
        )

        ttk.Button(panel, text="−90°", command=lambda: self.set_and_send(-90)).grid(row=3, column=0, padx=3)
        ttk.Button(panel, text="Center", command=lambda: self.set_and_send(0)).grid(row=3, column=1, padx=3)
        ttk.Button(panel, text="+90°", command=lambda: self.set_and_send(90)).grid(row=3, column=2, padx=3)

        ttk.Label(panel, text="Motion time (s)").grid(row=4, column=0, columnspan=2, pady=(12, 0), sticky="e")
        ttk.Spinbox(panel, from_=0.1, to=10.0, increment=0.1, textvariable=self.duration, width=6).grid(
            row=4, column=2, pady=(12, 0)
        )
        ttk.Label(panel, textvariable=self.status, anchor="center").grid(
            row=5, column=0, columnspan=3, pady=(12, 0)
        )
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self._show_angle()
        self.spin()

    def _show_angle(self, *_):
        self.value.set(f"{self.angle.get():.1f}°")

    def set_and_send(self, degrees):
        self.angle.set(degrees)
        self._show_angle()
        self.send_goal()

    def send_goal(self):
        if not self.client.server_is_ready():
            self.status.set("Controller is not ready. Start Gazebo first.")
            return
        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = ["gimbal_yaw_joint"]
        point = JointTrajectoryPoint()
        point.positions = [math.radians(self.angle.get())]
        seconds = max(0.1, self.duration.get())
        point.time_from_start.sec = int(seconds)
        point.time_from_start.nanosec = int((seconds % 1) * 1_000_000_000)
        goal.trajectory.points = [point]
        self.status.set("Moving...")
        self.client.send_goal_async(goal).add_done_callback(self.goal_response)

    def goal_response(self, future):
        handle = future.result()
        if not handle.accepted:
            self.status.set("Goal rejected")
            return
        handle.get_result_async().add_done_callback(self.goal_result)

    def goal_result(self, future):
        result = future.result().result
        self.status.set("Reached target" if result.error_code == 0 else f"Controller error: {result.error_string}")

    def spin(self):
        rclpy.spin_once(self.node, timeout_sec=0.0)
        self.root.after(20, self.spin)

    def close(self):
        self.node.destroy_node()
        rclpy.shutdown()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    GimbalGui().run()
