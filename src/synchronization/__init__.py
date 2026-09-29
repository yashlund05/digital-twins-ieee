"""
src/synchronization — Synchronization Engine module.

The authoritative source of all synchronization logic in this repository.
Implements configurable synchronization intervals, Age of Information (AoI)
tracking, missed-update detection, divergence tracking, and synchronization logging.

RESEARCH NOTE: This module implements the independent variable of the
experimental study. Synchronization interval is the controlled variable
being swept in Experiment E5.

NO other module may implement synchronization timing or staleness logic.
"""

from src.synchronization.aoi import AoITracker
from src.synchronization.engine import SynchronizationEngine, SynchronizationResult
from src.synchronization.logger import SyncEventLogger, SyncLogRecord
from src.synchronization.policies import (
    HoldLastStatePolicy,
    LinearExtrapolationPolicy,
    MissedUpdatePolicy,
    ZeroInputPolicy,
    get_policy,
)
from src.synchronization.scheduler import UpdateScheduler
from src.synchronization.state_tracker import DivergenceMetrics, StateDivergenceTracker

__all__ = [
    "AoITracker",
    "DivergenceMetrics",
    "HoldLastStatePolicy",
    "LinearExtrapolationPolicy",
    "MissedUpdatePolicy",
    "StateDivergenceTracker",
    "SyncEventLogger",
    "SyncLogRecord",
    "SynchronizationEngine",
    "SynchronizationResult",
    "UpdateScheduler",
    "ZeroInputPolicy",
    "get_policy",
]
