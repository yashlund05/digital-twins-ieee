"""
tests/unit/test_aoi.py — Unit tests for Age of Information (AoI) calculation engine.
"""

import pytest

from src.synchronization.aoi import AoITracker


def test_aoi_initial_state():
    """Verify initial tracker state before any updates."""
    tracker = AoITracker()
    assert tracker.current_aoi == 0.0
    assert tracker.peak_aoi == 0.0
    assert tracker.average_aoi == 0.0
    assert tracker.sync_age == 0.0


def test_aoi_single_update_zero_latency():
    """Verify AoI immediately following update with zero latency."""
    tracker = AoITracker()
    aoi = tracker.record_update(current_time=100.0, generation_time=100.0)
    assert aoi == 0.0
    assert tracker.current_aoi == 0.0
    assert tracker.sync_age == 0.0


def test_aoi_single_update_with_latency():
    """Verify AoI with transmission/sensor delay (gen_time < current_time)."""
    tracker = AoITracker()
    # Generated at t=95, received at t=100 -> latency 5s
    aoi = tracker.record_update(current_time=100.0, generation_time=95.0)
    assert aoi == 5.0
    assert tracker.current_aoi == 5.0
    assert tracker.sync_age == 0.0


def test_aoi_linear_growth_between_updates():
    """Verify AoI increases linearly with slope 1 between sync events."""
    tracker = AoITracker()
    tracker.record_update(current_time=100.0, generation_time=100.0)

    # Evaluate at t = 115 s (15s after update)
    aoi_15 = tracker.evaluate_at(current_time=115.0)
    assert aoi_15 == 15.0
    assert tracker.sync_age == 15.0

    # Evaluate at t = 160 s (60s after update)
    aoi_60 = tracker.evaluate_at(current_time=160.0)
    assert aoi_60 == 60.0
    assert tracker.sync_age == 60.0


def test_aoi_sawtooth_profile():
    """Verify the characteristic sawtooth pattern of AoI over consecutive updates."""
    tracker = AoITracker()

    # Step 1: Update at t=0
    tracker.record_update(current_time=0.0, generation_time=0.0)
    assert tracker.current_aoi == 0.0

    # Step 2: Time advances to t=30
    aoi_30 = tracker.evaluate_at(current_time=30.0)
    assert aoi_30 == 30.0

    # Step 3: Next update arrives at t=30 with gen_time=30 -> resets to 0
    new_aoi = tracker.record_update(current_time=30.0, generation_time=30.0)
    assert new_aoi == 0.0
    assert tracker.peak_aoi == 30.0

    # Step 4: Time advances to t=50
    aoi_50 = tracker.evaluate_at(current_time=50.0)
    assert aoi_50 == 20.0
    assert tracker.peak_aoi == 30.0  # Peak is still 30.0


def test_aoi_average_calculation():
    """Verify time-average AoI matches analytic trapezoidal integral."""
    tracker = AoITracker()

    # In a periodic update with interval T=10 and zero latency:
    # Sawtooth from 0 to 10. Average AoI over [0, 10] is 0.5 * 10 = 5.0.
    tracker.record_update(current_time=0.0, generation_time=0.0)
    tracker.evaluate_at(current_time=10.0)

    assert pytest.approx(tracker.average_aoi, rel=1e-3) == 5.0


def test_aoi_max_cap():
    """Verify maximum AoI ceiling constraint if configured."""
    tracker = AoITracker(max_aoi_seconds=45.0)
    tracker.record_update(current_time=0.0, generation_time=0.0)

    # At t=100, unbounded AoI would be 100, but capped at 45
    capped_aoi = tracker.evaluate_at(current_time=100.0)
    assert capped_aoi == 45.0


def test_aoi_invalid_evaluation_time():
    """Verify error when evaluation time precedes packet generation time."""
    tracker = AoITracker()
    tracker.record_update(current_time=100.0, generation_time=100.0)
    with pytest.raises(ValueError):
        tracker.evaluate_at(current_time=50.0)
