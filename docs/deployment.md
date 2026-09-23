# Publish PassiveROI

Current status: code published at https://github.com/AhmedShehata2002/passive-roi-simulator; **live app hosting is not deployed**. No account credentials are bundled.

## Streamlit Community Cloud

1. Create a public GitHub repository named `passive-roi-simulator` under your account.
2. Commit the contents of this project folder at the repository root, including `.streamlit/`, `.github/`, and all six `data/cache/` files. Do not commit local virtual environments or secrets.
3. Confirm the GitHub Actions checks pass.
4. Sign in at https://share.streamlit.io/ with the account that can access the repository.
5. Create an app. Select the repository, branch `main`, entry point `app.py`, and Python 3.12 in advanced settings.
6. Deploy. The cache is bundled and no API keys are required. Record the actual URL.
7. Open that URL in a signed-out/incognito browser. Check all three cities; turn off all interventions (zero savings/cost); enter a project quote; check negative NPV display; download a scenario JSON.
8. Add the actual URL to README and LinkedIn only after the signed-out check succeeds.

Reference: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app

## Optional Docker hosting

The Dockerfile uses port 7860, suitable for a Docker-based Hugging Face Space or other container host:

```bash
docker build -t passiveroi .
docker run --rm -p 7860:7860 passiveroi
```

This container recipe is included but was not built or deployed in this environment. It is not a claim of an existing Space.

## Before presenting investment outputs

Replace illustrative CAPEX with project-specific quotes. Confirm the actual tariff, baseline envelope and use profile. The notebook is a plausibility exercise, not proof of engineering accuracy. The UI and methodology deliberately disclose these limits.
