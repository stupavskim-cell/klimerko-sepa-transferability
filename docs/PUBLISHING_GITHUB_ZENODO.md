# First-time GitHub + Zenodo publishing instructions

## A. Before uploading

1. Open `README.md`, `CITATION.cff`, and the manuscript Data and Code Availability section.
2. Do not replace DOI placeholders yet.
3. Confirm the source-data redistribution terms. If they do not explicitly permit redistribution, keep the original raw workbooks outside the public repository and publish only the code and permitted processed/derived files.
4. Run the verification commands locally.

## B. GitHub

1. Sign in to GitHub and create a new **public** repository, suggested name: `klimerko-sepa-transferability`.
2. Do not initialise it with a second README or licence if you plan to upload this folder as-is.
3. Upload the contents of this package.
4. Replace `REPLACE_WITH_GITHUB_REPOSITORY_URL` in `CITATION.cff` with the real repository URL.
5. Commit the change.

## C. Zenodo

1. Sign in to Zenodo.
2. Link your GitHub account in Zenodo.
3. In the Zenodo GitHub integration, synchronise repositories and enable this repository.
4. Back on GitHub, create a release with tag `v1.0.0`.
5. Wait for Zenodo to archive the release.
6. Open the Zenodo record and verify title, authors, licence and files.
7. Copy the **version-specific DOI** for the v1.0.0 record.

Zenodo also supports reserving a DOI before publication. If you choose that route, reserve it in Zenodo first and insert only the DOI actually shown by Zenodo.

## D. Final manuscript update

Replace:
- `[GITHUB_REPOSITORY_URL]` with the actual GitHub repository address.
- `[ZENODO_VERSION_DOI]` with the verified version-specific Zenodo DOI.

Use the version-specific DOI in the article so that the cited code corresponds exactly to the submitted analysis.

## E. Final check

Download the GitHub release ZIP into a clean folder/environment and run:

```bash
pip install -r requirements.txt
python src/run_analysis.py
python src/verify_results.py
```

Only after this clean-room check should the DOI-bearing manuscript be submitted.
