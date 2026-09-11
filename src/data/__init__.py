"""
data — Data pipeline module

Handles loading, preprocessing, mapping, and splitting of the hybrid simulation
dataset used in Digital Twin synchronization staleness experiments.

NOTE: This module works with a hybrid simulation dataset.
Pecan Street load profiles are mapped to the IEEE 33-bus topology.
The resulting dataset is NOT real field measurements of the IEEE feeder.
"""
