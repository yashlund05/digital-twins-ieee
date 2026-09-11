"""
conftest.py — Shared pytest fixtures

Provides fixtures used across all test categories.
"""

import pytest


@pytest.fixture
def sample_config() -> dict:
    """Return a minimal valid experiment configuration for testing."""
    return {
        "experiment": {
            "id": "TEST",
            "name": "test_experiment",
            "seed": 42,
            "version": "0.0.1",
        },
        "synchronization": {
            "interval_seconds": 60,
            "missed_update_policy": "hold_last_state",
        },
    }


@pytest.fixture
def sample_sync_config() -> dict:
    """Return a minimal synchronization configuration for testing."""
    return {
        "interval_seconds": 60,
        "missed_update_policy": "hold_last_state",
        "logging": {"enabled": False},
    }
