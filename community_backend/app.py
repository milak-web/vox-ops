import os

from flask import Flask, jsonify, request

from github_store import GitHubRepoStore, GitHubStoreError, build_summary, normalize_profile_payload


def create_app():
    app = Flask(__name__)
    store = GitHubRepoStore(
        repo=os.getenv("COMMUNITY_REPO", "milak-web/vox-ops"),
        branch=os.getenv("COMMUNITY_BRANCH", "main"),
        data_dir=os.getenv("COMMUNITY_DATA_DIR", "community"),
        token=os.getenv("GITHUB_TOKEN", ""),
    )

    @app.get("/health")
    def health():
        return jsonify(
            {
                "ok": True,
                "repo": store.repo,
                "branch": store.branch,
                "data_dir": store.data_dir,
                "upload_enabled": bool(store.token),
            }
        )

    @app.get("/profiles")
    def list_profiles():
        try:
            return jsonify(store.list_profiles())
        except GitHubStoreError as exc:
            return jsonify({"error": str(exc)}), 502

    @app.get("/profiles/<slug>")
    def get_profile(slug):
        try:
            profile = store.get_profile(slug)
        except GitHubStoreError as exc:
            status_code = 404 if exc.status_code == 404 else 502
            return jsonify({"error": str(exc)}), status_code
        return jsonify(profile)

    @app.post("/profiles")
    def publish_profile():
        if request.content_length and request.content_length > 256_000:
            return jsonify({"error": "Payload is too large."}), 413

        payload = request.get_json(silent=True)
        try:
            normalized = normalize_profile_payload(payload)
            profile = store.add_profile(normalized)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except GitHubStoreError as exc:
            return jsonify({"error": str(exc)}), 502

        summary = build_summary(profile)
        return jsonify({"ok": True, "profile": summary}), 201

    @app.post("/upload")
    def legacy_upload():
        return publish_profile()

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=False)
