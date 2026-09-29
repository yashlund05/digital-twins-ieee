"""
src/synchronization/scheduler.py — Interval-based update scheduling.

Controls synchronization timing and determines when physical grid measurements
should be propagated to the Digital Twin. Implements the experimental independent
variable (Delta t_sync in [0, 1800] s) and optional stochastic packet drop (Experiment E7).
"""

import numpy as np

from src.utils.logging import get_logger

logger = get_logger("synchronization.scheduler")


class UpdateScheduler:
    """Schedules synchronization events according to configured intervals and stochastic loss."""

    def __init__(
        self,
        interval_seconds: int = 60,
        missed_update_rate: float = 0.0,
        seed: int | None = 42,
    ) -> None:
        """Initialize the update scheduler.

        Args:
            interval_seconds: Synchronization interval (Delta t_sync). 0 = perfect sync.
            missed_update_rate: Probability [0.0, 1.0] of an update failing to transmit (Exp E7).
            seed: Random seed for reproducible stochastic packet loss.
        """
        if interval_seconds < 0:
            raise ValueError(f"Interval seconds must be non-negative, got {interval_seconds}")
        if not (0.0 <= missed_update_rate <= 1.0):
            raise ValueError(f"missed_update_rate must be in [0.0, 1.0], got {missed_update_rate}")

        self.interval_seconds = interval_seconds
        self.missed_update_rate = missed_update_rate
        self.rng = np.random.default_rng(seed)

    def is_update_due(
        self,
        current_time: float,
        last_sync_time: float | None = None,
    ) -> bool:
        """Check whether an update is scheduled at the given time.

        Args:
            current_time: Current simulation or wall-clock epoch time in seconds.
            last_sync_time: Epoch time of the previous successful synchronization.

        Returns:
            True if an update should be performed at current_time, False otherwise.
        """
        if last_sync_time is None:
            # First observation always attempts synchronization
            return True

        if self.interval_seconds == 0:
            # Level 0 (perfect synchronization): update every step
            return True

        elapsed = current_time - last_sync_time
        # Use a small numerical epsilon (1e-6) to guard against floating-point imprecision
        return elapsed >= (self.interval_seconds - 1e-6)

    def check_update(
        self,
        current_time: float,
        last_sync_time: float | None = None,
    ) -> tuple[bool, bool]:
        """Evaluate if an update is due and whether it succeeds.

        Args:
            current_time: Current simulation timestamp in seconds.
            last_sync_time: Epoch timestamp of last successful sync.

        Returns:
            Tuple of (is_due, is_successful).
            - is_due: Whether the schedule warrants an update attempt now.
            - is_successful: True if due AND not dropped by communication failure.
        """
        is_due = self.is_update_due(current_time, last_sync_time)
        if not is_due:
            return False, False

        # If due, check stochastic packet drop
        if self.missed_update_rate > 0.0:
            dropped = float(self.rng.random()) < self.missed_update_rate
            if dropped:
                logger.debug(
                    f"Update at t={current_time:.2f}s dropped due to simulated packet loss."
                )
                return True, False

        return True, True

    def reset(self, seed: int | None = 42) -> None:
        """Reset the random number generator for reproducible runs."""
        self.rng = np.random.default_rng(seed)
