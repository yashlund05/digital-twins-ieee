"""
synchronization — Synchronization Engine

The authoritative source of all synchronization logic in this repository.
Implements configurable synchronization intervals, Age of Information (AoI)
tracking, missed-update detection, and synchronization logging.

RESEARCH NOTE: This module implements the independent variable of the
experimental study. Synchronization interval is the controlled variable
being swept in Experiment E5.

NO other module may implement synchronization timing or staleness logic.
"""
