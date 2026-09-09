#!/usr/bin/env bash

# ROS 2 Humble + Livox MID360 user-local development environment.
export PATH="/usr/bin:/bin:/usr/local/bin:$PATH"
if [ -n "${ZSH_VERSION:-}" ]; then
  source /opt/ros/humble/setup.zsh
  if [ -f "$HOME/Desktop/workspace/sentry-navigation/install/setup.zsh" ]; then
    source "$HOME/Desktop/workspace/sentry-navigation/install/setup.zsh"
  fi
else
  source /opt/ros/humble/setup.bash
  if [ -f "$HOME/Desktop/workspace/sentry-navigation/install/setup.bash" ]; then
    source "$HOME/Desktop/workspace/sentry-navigation/install/setup.bash"
  fi
fi
export LD_LIBRARY_PATH="$HOME/third_party/livox-sdk2-install/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
