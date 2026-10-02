# Discrepancy Resolution Log — Phase 14 Audit

## Summary of Tracked Discrepancies
- Total Tracked: 3
- Resolved: 2
- Accepted Differences: 1
- Critical Unresolved: 0

## Detailed Resolutions
1. **DISC-001-C13-AOI (Case B)**:
   - Automated threshold in table_04 yields 0.0 s (CI: [0.0, 2.5] s) for micro noise departure.
   - Descriptive macro cliff in narrative and figures yields ~5.0 s (CI: [3.5, 7.5] s) for in-bin F1 collapse.
   - Demarcated into Claim C13 (micro) and Claim C14 (macro). Status: **RESOLVED**.
2. **DISC-002-METRIC-SCALE**:
   - Bounded F1 [0, 1] vs unbounded MAPE favors steeper LE slopes under log-linear normalization.
   - Fully disclosed in manuscript Section V-B. Status: **RESOLVED**.
3. **DISC-003-LATEX-COMPILER**:
   - pdflatex not present in host PATH.
   - Structural LaTeX syntax, inputs, citations, and labels verified clean. Status: **ACCEPTED_DIFFERENCE**.
