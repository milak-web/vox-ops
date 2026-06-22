# VOX OPS Community Backend

This service exposes the community profile API used by the desktop app and stores shared profiles directly in this repository under `community/`.

## Endpoints

- `GET /health`
- `GET /profiles`
- `GET /profiles/<slug>`
- `POST /profiles`
- `POST /upload` (legacy alias)

## Environment

- `GITHUB_TOKEN`: token with contents write access to the repository
- `COMMUNITY_REPO`: defaults to `milak-web/vox-ops`
- `COMMUNITY_BRANCH`: defaults to `main`
- `COMMUNITY_DATA_DIR`: defaults to `community`
- `PORT`: defaults to `8000`

## Run locally

```bash
pip install -r community_backend/requirements.txt
python community_backend/app.py
```

The desktop app can browse community profiles directly from GitHub, but publishing uploads requires this API to be deployed with a valid `GITHUB_TOKEN`.
