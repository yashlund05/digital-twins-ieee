# Human Actions Required Before Journal Submission

This document lists the mandatory non-automatable actions that the human authors must perform before finalizing submission to **IEEE Transactions on Smart Grid**.

## Mandatory Author Fields
The following fields must be supplied manually:

| Field | Author 1 (Ayush Vishwakarma) | Author 2 (Vipul Bhamare) | Author 3 (Yash Lund) |
|---|---|---|---|
| **Department** | `REQUIRED` | `REQUIRED` | `REQUIRED` |
| **Institutional Email** | `REQUIRED` | `REQUIRED` | `REQUIRED` |
| **IEEE Membership Grade** | `REQUIRED` | `REQUIRED` | `REQUIRED` |
| **Corresponding Author** | [ ] Yes / [ ] No | [ ] Yes / [ ] No | [ ] Yes / [ ] No |
| **ORCID ID (Optional)** | `OPTIONAL` | `OPTIONAL` | `OPTIONAL` |

## Mandatory Administrative & Grant Fields
1. **Grant Funding Statement:**
   - If funded: State funding agency and grant numbers (e.g., "This work was supported in part by ... under Grant ...").
   - If unfunded: Confirm no external funding to declare.
2. **Zenodo Replication Archive DOI:**
   - Visit https://zenodo.org, create a new upload, reserve a DOI.
   - Package source code and historical data manifests.
   - Update `configs/publication/author_metadata.yaml` with the assigned DOI.
3. **LaTeX PDF Compilation:**
   - Compile `manuscript/main.tex` and `manuscript/references.bib` using TeX Live, MacTeX, or Overleaf.
   - Confirm PDF produces clean 2-column IEEEtran layout without errors.
