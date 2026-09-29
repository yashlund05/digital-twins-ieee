"""
src/synchronization/aoi.py — Age of Information (AoI) calculation engine.

Implements the formal Age of Information metric per Guo et al. (2026) and Shu et al. (2022):
    AoI(t) = t_physical - t_generation(last_received_packet)
Tracks instantaneous AoI, average AoI, and peak AoI over experimental horizons.
"""

from src.utils.logging import get_logger

logger = get_logger("synchronization.aoi")


class AoITracker:
    """Tracks and calculates Age of Information (AoI) and synchronization age metrics."""

    def __init__(self, max_aoi_seconds: float | None = None) -> None:
        """Initialize the AoI tracker.

        Args:
            max_aoi_seconds: Optional cap on maximum AoI (divergence limit).
        """
        self.max_aoi_seconds = max_aoi_seconds
        self._last_successful_sync_time: float | None = None
        self._last_update_generation_time: float | None = None
        self._current_aoi: float = 0.0
        self._peak_aoi: float = 0.0
        self._cumulative_aoi_area: float = 0.0
        self._last_evaluated_time: float | None = None
        self._num_evaluations: int = 0

    def record_update(self, current_time: float, generation_time: float | None = None) -> float:
        """Record the arrival of a successful synchronization update into the Digital Twin.

        Upon arrival, the instantaneous AoI drops to the transmission/computation latency:
            AoI(t_arrival) = t_arrival - t_generation

        Args:
            current_time: Epoch seconds or simulated wall-clock time of reception.
            generation_time: Epoch seconds when the measurement was captured at the sensor.
                             If None, assumes negligible measurement latency (generation_time = current_time).

        Returns:
            The new instantaneous AoI in seconds.
        """
        gen_time = generation_time if generation_time is not None else current_time
        latency = max(0.0, current_time - gen_time)

        # Update cumulative area using trapezoidal integration if time has advanced
        if self._last_evaluated_time is not None and current_time > self._last_evaluated_time:
            dt = current_time - self._last_evaluated_time
            # Area under the sawtooth AoI curve
            self._cumulative_aoi_area += 0.5 * (self._current_aoi + latency) * dt

        self._last_successful_sync_time = current_time
        self._last_update_generation_time = gen_time
        self._current_aoi = latency
        self._last_evaluated_time = current_time
        self._num_evaluations += 1

        return self._current_aoi

    def evaluate_at(self, current_time: float) -> float:
        """Calculate the instantaneous AoI at an arbitrary evaluation timestamp.

        Between updates, AoI grows linearly with slope 1:
            AoI(t) = t - t_generation

        Args:
            current_time: Timestamp to evaluate.

        Returns:
            Current Age of Information in seconds.
        """
        if self._last_update_generation_time is None:
            # No update received yet; AoI is 0.0
            return 0.0

        if current_time < self._last_update_generation_time:
            raise ValueError(
                f"Evaluation time ({current_time}) cannot precede last generation time ({self._last_update_generation_time})"
            )

        raw_aoi = current_time - self._last_update_generation_time
        aoi = min(raw_aoi, self.max_aoi_seconds) if self.max_aoi_seconds is not None else raw_aoi

        # Track peak AoI observed
        if aoi > self._peak_aoi:
            self._peak_aoi = aoi

        # Update integration
        if self._last_evaluated_time is not None and current_time > self._last_evaluated_time:
            dt = current_time - self._last_evaluated_time
            self._cumulative_aoi_area += 0.5 * (self._current_aoi + aoi) * dt

        self._current_aoi = aoi
        self._last_evaluated_time = current_time
        self._num_evaluations += 1

        return self._current_aoi

    @property
    def current_aoi(self) -> float:
        """Current instantaneous AoI in seconds."""
        return self._current_aoi

    @property
    def peak_aoi(self) -> float:
        """Maximum peak AoI observed over the tracking period in seconds."""
        return self._peak_aoi

    @property
    def average_aoi(self) -> float:
        """Time-average Age of Information: (1/T) * integral(AoI(t) dt)."""
        if self._last_evaluated_time is None or self._last_successful_sync_time is None:
            return 0.0
        total_time = self._last_evaluated_time - self._last_successful_sync_time
        if total_time <= 0.0:
            return self._current_aoi
        return self._cumulative_aoi_area / total_time

    @property
    def sync_age(self) -> float:
        """Time elapsed since last successful synchronization in seconds."""
        if self._last_successful_sync_time is None:
            return 0.0
        current = (
            self._last_evaluated_time
            if self._last_evaluated_time is not None
            else self._last_successful_sync_time
        )
        return max(0.0, current - self._last_successful_sync_time)

    def reset(self) -> None:
        """Reset all AoI tracking accumulators."""
        self._last_successful_sync_time = None
        self._last_update_generation_time = None
        self._current_aoi = 0.0
        self._peak_aoi = 0.0
        self._cumulative_aoi_area = 0.0
        self._last_evaluated_time = None
        self._num_evaluations = 0
