#!/usr/bin/env python3
"""Keyboard teleoperation window for the kinematic sentry simulator."""

import tkinter as tk
from tkinter import ttk

import rclpy
from geometry_msgs.msg import Twist


class SentryTeleop:
    def __init__(self):
        rclpy.init()
        self.node = rclpy.create_node("sentry_teleop_gui")
        self.pub = self.node.create_publisher(Twist, "/cmd_vel", 10)
        self.keys = set()
        self.was_driving = False
        # Conservative speeds for producing a clean occupancy map.
        self.linear_speed = 0.15
        self.angular_speed = 0.40

        self.root = tk.Tk()
        self.root.title("Sentry Manual Drive")
        self.root.resizable(False, False)
        panel = ttk.Frame(self.root, padding=18)
        panel.grid()
        ttk.Label(panel, text="Click this window before driving", font=("Sans", 12, "bold")).grid(row=0, column=0)
        ttk.Label(panel, text="W / S   forward / reverse\nA / D   left / right strafe\nQ / E   rotate left / right\nSpace   emergency stop\nRelease all keys to stop").grid(row=1, column=0, pady=12)
        self.status = tk.StringVar(value="Stopped")
        ttk.Label(panel, textvariable=self.status, anchor="center").grid(row=2, column=0)
        ttk.Button(panel, text="STOP", command=self.stop).grid(row=3, column=0, pady=(12, 0), sticky="ew")
        self.root.bind("<KeyPress>", self.key_press)
        self.root.bind("<KeyRelease>", self.key_release)
        self.root.bind("<FocusOut>", lambda _: self.stop())
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(50, self.publish)
        self.root.after(100, self.root.focus_force)

    def key_press(self, event):
        key = event.keysym.lower()
        if key == "space":
            self.stop()
        elif key in {"w", "a", "s", "d", "q", "e"}:
            self.keys.add(key)

    def key_release(self, event):
        self.keys.discard(event.keysym.lower())

    def stop(self):
        self.keys.clear()
        self.pub.publish(Twist())
        self.was_driving = False
        self.status.set("Stopped")

    def publish(self):
        msg = Twist()
        msg.linear.x = self.linear_speed * (("w" in self.keys) - ("s" in self.keys))
        msg.linear.y = self.linear_speed * (("a" in self.keys) - ("d" in self.keys))
        msg.angular.z = self.angular_speed * (("q" in self.keys) - ("e" in self.keys))
        if self.keys:
            self.pub.publish(msg)
            self.was_driving = True
            self.status.set(f"Driving: {' '.join(sorted(self.keys)).upper()}")
        elif self.was_driving:
            self.pub.publish(Twist())
            self.was_driving = False
            self.status.set("Stopped")
        self.root.after(50, self.publish)

    def close(self):
        self.stop()
        self.node.destroy_node()
        rclpy.shutdown()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    SentryTeleop().run()
