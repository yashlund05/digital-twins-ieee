# Human Author Actions Required Prior to IEEE Submission

The scientific, numerical, and software aspects of this project are complete. To finalize submission to IEEE Transactions on Smart Grid, the human authors must perform the following actions:

## Checklist
- [ ] **1. Author Metadata in Manuscript:**
  - Open `experiments/runs/E20_FINAL_SUBMISSION_RELEASE_20261007/manuscript/main.tex`
  - Uncomment lines 27–29 and insert author names, IEEE membership grades, institutional affiliations, and emails.
- [ ] **2. Funding & Grant Information:**
  - In `main.tex`, insert official research grant numbers and funding agency details in `\section*{Acknowledgment}`.
- [ ] **3. Zenodo Archive & DOI:**
  - Create an archival release snapshot on Zenodo following `ZENODO_RELEASE_INSTRUCTIONS.md`.
  - Replace `ZENODO_DOI_REQUIRED` with the issued DOI in `configs/publication/author_metadata.yaml`.
- [ ] **4. Final PDF Compilation Check:**
  - Build the final PDF using local pdflatex or Overleaf and inspect visual layout.
- [ ] **5. GitHub Push Authorization:**
  - Push the local commits to GitHub upon final approval.
- [ ] **6. ScholarOne Portal Submission:**
  - Upload manuscript PDF, supplementary PDF/zip, and draft cover letter to IEEE Transactions on Smart Grid submission portal.
