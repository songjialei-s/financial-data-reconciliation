# GitHub publish checklist / 发布前检查

- [ ] Confirm the repository root is `financial-data-reconciliation`, not a confidential source folder.
- [ ] Confirm `git status` contains no `.env`, database credential, private IP address, or local user path.
- [ ] Confirm no real order, settlement, customer, account, SKU, or transaction data is present.
- [ ] Confirm `.venv`, `node_modules`, SQLite files, QA previews, and inspection dumps are ignored.
- [ ] Run `pytest` and record the actual result.
- [ ] Run the end-to-end CLI with the documented seed.
- [ ] Open the README images and Excel report.
- [ ] Review the repository in GitHub Desktop before the first commit.
- [ ] Create a new remote repository only after the local review.

