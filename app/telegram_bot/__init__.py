"""Telegram adapter for VietDub Studio.

This package is intentionally separate from the web UI and pipeline code.  It
creates normal jobs and receives completion notifications, but the core
processing stages do not depend on Telegram.
"""
