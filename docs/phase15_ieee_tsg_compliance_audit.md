# Phase 15 — IEEE Transactions on Smart Grid Compliance Audit

**Target Venue:** IEEE Transactions on Smart Grid (IEEE TSG)  
**Publication Standard:** 2025–2026 IEEE Power & Energy Society (PES) Guidelines  
**Auditor Mode:** Formal Journal Compliance, Formatting, and Page Constraint Review

---

## 1. Compliance Checklist Matrix

| Requirement | IEEE TSG Mandate | Current Repository State | Compliance Status | Required Remediation |
|---|---|---|:---:|---|
| **Scope Alignment** | Power grid digital twins, distribution systems, smart grid data analytics | IEEE 33-bus OpenDSS feeder + Pecan Street AMI + ML | **COMPLIANT** | None |
| **Initial Page Limit** | **Maximum 10 pages** at first submission (strict desk-return rule) | Estimated 6.5–7.0 pages in `IEEEtran` layout | **COMPLIANT** | Keep within 10 pages when adding revisions |
| **Format & Layout** | Standard double-column `IEEEtran.cls`, `\documentclass[journal]{IEEEtran}` | `main.tex` uses standard `\documentclass[journal]{IEEEtran}` | **COMPLIANT** | None |
| **Figure Standards** | Embedded high-res figures; vector PDF preferred | 8 figures provided in dual 300 DPI PNG and vector PDF | **COMPLIANT** | None |
| **Table Standards** | Booktabs style, caption above table | 6 tables provided in dual CSV and LaTeX `.tex` | **COMPLIANT** | None |
| **Bibliography Integrity** | Complete author names, titles, journals, DOIs | **6 out of 10 references have `[VERIFY]` tags** | **NON-COMPLIANT (P0)** | **Populate real citations in `references.bib`** |
| **Author Block & ORCID** | Placeholder during drafting; required upon submission | Commented-out placeholder in `main.tex` | **ACTION REQUIRED** | Assign official author list and ORCIDs |
| **Abstract & Keywords** | Abstract 150–200 words; up to 10 keywords | Abstract ~195 words; 7 keywords defined | **COMPLIANT** | None |
| **Overlength Charges** | Mandatory \$250/page for pages exceeding 12 pages post-acceptance | Current draft is ~7 pages | **COMPLIANT** | Safe from overlength fees |
| **Supplementary Material**| Allowed via IEEE Xplore for proofs/massive tables | Not yet separated | **RECOMMENDED** | Move secondary ablation tables to supplementary |

---

## 2. Critical Compliance Action Item: `references.bib`

The single fatal compliance blocker in the manuscript package is the unverified citations in `experiments/runs/E13_MANUSCRIPT_SUBMISSION_20261002/manuscript/references.bib`:

```bibtex
@article{ref_dt_survey,
  author = {{VERIFY — DT Survey Author}},
  title = {{Digital Twins in Power Systems: A Comprehensive Survey}},
  journal = {{VERIFY — Journal}}, ...
}
```

### Action Plan
Prior to submission, replace all 6 `[VERIFY]` placeholders with authoritative peer-reviewed literature:
1. `ref_dt_survey` $\to$ Sifat et al. (2023) or Thwe et al. (2025) IEEE TSG review.
2. `ref_ad_survey` $\to$ Gholami et al. (2022) or Liu et al. (2023) IEEE TSG anomaly detection paper.
3. `ref_aoi_theory` $\to$ Sun et al. / Kaul et al. foundational AoI monograph.
4. `ref_lstm_ae` $\to$ Malhotra et al. (2016) / Asghar et al. (2023).
5. `ref_lstm_forecast` $\to$ Kong et al. (2019) IEEE TSG short-term load forecasting.
