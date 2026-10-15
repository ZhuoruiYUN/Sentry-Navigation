#!/usr/bin/env bash

# ROS 2 Humble + Livox MID360 user-local development environment.
if [ -n "${ZSH_VERSION:-}" ]; then
  SENTRY_WS_DIR="$(cd "$(dirname "${(%):-%N}")" && pwd)"
else
  SENTRY_WS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi
export SENTRY_WS_DIR
export PATH="/usr/bin:/bin:/usr/local/bin:$PATH"
# Keep this project isolated from stale ROS 2 processes in the default domain.
export ROS_DOMAIN_ID=42
if [ -n "${ZSH_VERSION:-}" ]; then
  source /opt/ros/humble/setup.zsh
  if [ -f "$SENTRY_WS_DIR/install/setup.zsh" ]; then
    source "$SENTRY_WS_DIR/install/setup.zsh"
  fi
else
  source /opt/ros/humble/setup.bash
  if [ -f "$SENTRY_WS_DIR/install/setup.bash" ]; then
    source "$SENTRY_WS_DIR/install/setup.bash"
  fi
fi
export LD_LIBRARY_PATH="$HOME/third_party/livox-sdk2-install/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
