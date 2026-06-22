import base64
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone


class GitHubStoreError(RuntimeError):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


MAX_NAME_LENGTH = 80
MAX_AUTHOR_LENGTH = 80
MAX_DESC_LENGTH = 280
MAX_COMMANDS = 300
MAX_TRIGGER_LENGTH = 120
MAX_ACTION_LENGTH = 4000


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def clean_text(value, max_length=0):
    text = str(value or "").strip()
    if max_length:
        return text[:max_length]
    return text


def slugify(value):
    slug = re.sub(r"[^a-z0-9]+", "-", clean_text(value).lower()).strip("-")
    return slug or "profile"


def normalize_commands(commands):
    if not isinstance(commands, dict):
        raise ValueError("Profile commands must be a JSON object.")

    normalized = {}
    for trigger, action in commands.items():
        trigger_text = clean_text(trigger, MAX_TRIGGER_LENGTH)
        action_text = clean_text(action, MAX_ACTION_LENGTH)
        if trigger_text and action_text:
            normalized[trigger_text] = action_text
        if len(normalized) >= MAX_COMMANDS:
            break

    if not normalized:
        raise ValueError("Profile must include at least one valid command.")
    return normalized


def normalize_profile_payload(payload):
    if not isinstance(payload, dict):
        raise ValueError("Profile payload must be valid JSON.")

    name = clean_text(payload.get("name"), MAX_NAME_LENGTH)
    author = clean_text(payload.get("author"), MAX_AUTHOR_LENGTH)
    desc = clean_text(payload.get("desc"), MAX_DESC_LENGTH)
    commands = normalize_commands(payload.get("commands", {}))

    if not name:
        raise ValueError("Profile name is required.")
    if not author:
        raise ValueError("Author name is required.")

    return {
        "name": name,
        "author": author,
        "desc": desc,
        "commands": commands,
    }


def build_summary(profile):
    slug = profile["slug"]
    return {
        "slug": slug,
        "name": profile["name"],
        "author": profile["author"],
        "desc": profile["desc"],
        "command_count": len(profile["commands"]),
        "created_at": profile["created_at"],
        "updated_at": profile["updated_at"],
        "path": f"profiles/{slug}.json",
    }


class GitHubRepoStore:
    def __init__(self, repo, branch, data_dir, token=""):
        self.repo = repo
        self.branch = branch
        self.data_dir = data_dir.strip("/")
        self.token = token.strip()
        self.index_path = f"{self.data_dir}/index.json"

    def _headers(self):
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "vox-ops-community-backend",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _content_url(self, path):
        encoded_path = "/".join(urllib.parse.quote(part) for part in path.split("/"))
        ref = urllib.parse.quote(self.branch)
        return f"https://api.github.com/repos/{self.repo}/contents/{encoded_path}?ref={ref}"

    def _request_json(self, url, method="GET", payload=None, expected=(200,)):
        data = None
        headers = self._headers()
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"

        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                if response.getcode() not in expected:
                    raise GitHubStoreError(f"GitHub returned unexpected status {response.getcode()}.", response.getcode())
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8")
            except Exception:
                detail = exc.reason
            raise GitHubStoreError(f"GitHub API error {exc.code}: {detail}", exc.code) from exc
        except urllib.error.URLError as exc:
            raise GitHubStoreError(f"Could not reach GitHub: {exc}") from exc

    def _require_token(self):
        if not self.token:
            raise GitHubStoreError("GITHUB_TOKEN is required for community profile uploads.")

    def _read_file(self, path, missing_ok=False):
        try:
            response = self._request_json(self._content_url(path))
        except GitHubStoreError as exc:
            if missing_ok and exc.status_code == 404:
                return None
            raise

        content = response.get("content", "")
        decoded = base64.b64decode(content).decode("utf-8") if content else ""
        return {"sha": response.get("sha"), "content": decoded}

    def _write_file(self, path, content, message):
        self._require_token()
        existing = self._read_file(path, missing_ok=True)
        payload = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
            "branch": self.branch,
        }
        if existing and existing.get("sha"):
            payload["sha"] = existing["sha"]

        self._request_json(
            self._content_url(path),
            method="PUT",
            payload=payload,
            expected=(200, 201),
        )

    def load_index(self):
        index_file = self._read_file(self.index_path, missing_ok=True)
        if not index_file:
            return {"schema_version": 1, "generated_at": "", "profiles": []}

        data = json.loads(index_file["content"])
        if isinstance(data, list):
            data = {"schema_version": 1, "generated_at": "", "profiles": data}

        data.setdefault("profiles", [])
        return data

    def list_profiles(self):
        index = self.load_index()
        profiles = [summary for summary in index.get("profiles", []) if isinstance(summary, dict)]
        return sorted(
            profiles,
            key=lambda summary: (
                summary.get("updated_at", ""),
                summary.get("name", "").lower(),
            ),
            reverse=True,
        )

    def get_profile(self, slug):
        safe_slug = slugify(slug)
        path = f"{self.data_dir}/profiles/{safe_slug}.json"
        profile_file = self._read_file(path, missing_ok=False)
        profile = json.loads(profile_file["content"])
        profile.setdefault("slug", safe_slug)
        profile.setdefault("path", f"profiles/{safe_slug}.json")
        return profile

    def _next_slug(self, name, author, existing_slugs):
        base_slug = slugify(name)
        candidate = base_slug
        suffix = slugify(author)
        counter = 2

        if candidate not in existing_slugs:
            return candidate

        if suffix:
            candidate = f"{base_slug}-{suffix}"
            if candidate not in existing_slugs:
                return candidate

        while candidate in existing_slugs:
            candidate = f"{base_slug}-{counter}"
            counter += 1
        return candidate

    def add_profile(self, payload):
        index = self.load_index()
        existing_slugs = {summary.get("slug") for summary in index.get("profiles", []) if isinstance(summary, dict)}
        slug = self._next_slug(payload["name"], payload["author"], existing_slugs)
        timestamp = utc_now()

        profile = {
            "schema_version": 1,
            "slug": slug,
            "name": payload["name"],
            "author": payload["author"],
            "desc": payload["desc"],
            "commands": payload["commands"],
            "created_at": timestamp,
            "updated_at": timestamp,
            "path": f"profiles/{slug}.json",
        }

        profile_path = f"{self.data_dir}/profiles/{slug}.json"
        self._write_file(
            profile_path,
            json.dumps(profile, indent=2) + "\n",
            f"community: add profile {payload['name']}",
        )

        summary = build_summary(profile)
        profiles = [entry for entry in index.get("profiles", []) if isinstance(entry, dict)]
        profiles.insert(0, summary)
        index["schema_version"] = 1
        index["generated_at"] = timestamp
        index["profiles"] = sorted(
            profiles,
            key=lambda entry: (
                entry.get("updated_at", ""),
                entry.get("name", "").lower(),
            ),
            reverse=True,
        )

        self._write_file(
            self.index_path,
            json.dumps(index, indent=2) + "\n",
            f"community: update profile index ({len(index['profiles'])} profiles)",
        )
        return profile
