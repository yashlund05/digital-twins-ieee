# Draft IEEE Transactions on Smart Grid Cover Letter

**NOTE:** DRAFT ONLY — For Human Author Review and Submission

To:  
Editor-in-Chief  
IEEE Transactions on Smart Grid  

Dear Editor-in-Chief,

We are pleased to submit our original research manuscript titled:

**"Quantifying the Effect of Digital Twin Synchronization Staleness on Joint Short-Term Load Estimation and Unsupervised Anomaly Detection in a Distribution-Feeder Digital Twin"**

for consideration for publication in the *IEEE Transactions on Smart Grid*.

### Research Overview & Contribution
Distribution-feeder digital twins are increasingly deployed to enhance grid observability and enable edge machine-learning analytics. However, the physical state divergence introduced by synchronization staleness (telemetry latency and communication packet drops) has remained un-quantified.

In this work, we present a controlled co-simulation framework coupling OpenDSS distribution models with an Age-of-Information (AoI) synchronization engine driven by real high-resolution smart meter telemetry from Pecan Street Dataport. Across extensive multi-seed factorial experiments ($N=10$ independent random seeds) and three IEEE benchmark distribution feeders (IEEE 13, 33, and 123-bus), we show that:
1. Fresh physics-based residuals provide superior anomaly detection ($F_1 = 0.978$ vs. $0.539$ for raw telemetry).
2. Beyond an operational transition envelope ($2.4$--$4.1$~s scaling with feeder electrical impedance depth), residuals suffer representation inversion, where stale physics models actively harm detection.
3. The pre-specified hypothesis (H3) that anomaly detection degrades more rapidly than load estimation is falsified ($\Deltaeta = -1.224$, $p=1.000$) across all tested seeds and eight distinct error formulations, revealing that autoregressive load forecasting degrades more steeply under delayed inputs.
4. Physics residual arithmetic and adaptive thresholding execute in sub-microsecond latency ($0.41\,\mu$s and $1.28\,\mu$s), confirming edge feasibility.

This manuscript is original work and is not under consideration for publication elsewhere. All authors have approved the manuscript for submission. A complete reproducibility package with open-source code and data manifests accompanies this paper.

Sincerely,

[The Authors]
