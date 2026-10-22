"""Release guards: keep public binaries unchanged and publish only complete verified assets."""
import hashlib
import importlib.util
from pathlib import Path
from urllib.error import HTTPError

import pytest


@pytest.fixture
def publisher(tmp_path):
    spec = importlib.util.spec_from_file_location("publish_prerelease", Path(__file__).resolve().parents[1] / ".github/scripts/publish_prerelease.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "0.3.3"\n', encoding="utf-8")
    (tmp_path / "citrus_drop").mkdir()
    (tmp_path / "citrus_drop/__init__.py").write_text('__version__ = "0.3.3"\n', encoding="utf-8")
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist/CitrusDrop.exe").write_bytes(b"MZverified-test-build")
    (tmp_path / "docs/releases").mkdir(parents=True)
    (tmp_path / "docs/releases/v0.3.3.md").write_text("Pre-release", encoding="utf-8")
    return module


def test_published_assets_are_never_replaced(publisher, tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(publisher, "github_release", lambda *_: {"draft": False, "body": "Pre-release"})
    monkeypatch.setattr(publisher, "gh", lambda *args: calls.append(args))
    publisher.publish(tmp_path, "owner/repo", "commit")
    assert not calls
    assert not (tmp_path / "dist/SHA256SUMS.txt").exists()


def test_existing_release_updates_only_changed_notes(publisher, tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(publisher, "github_release", lambda *_: {"draft": False, "body": "Old instructions"})
    monkeypatch.setattr(publisher, "gh", lambda *args: calls.append(args))
    # Updating documentation must not need a new binary or touch the release assets.
    (tmp_path / "dist/CitrusDrop.exe").unlink()
    publisher.publish(tmp_path, "owner/repo", "new-docs-commit")
    assert calls == [("release", "edit", "v0.3.3", "--repo", "owner/repo", "--notes-file", str(tmp_path / "docs/releases/v0.3.3.md"))]
    assert not (tmp_path / "dist/SHA256SUMS.txt").exists()


def test_invalid_executable_is_not_uploaded(publisher, tmp_path, monkeypatch):
    (tmp_path / "dist/CitrusDrop.exe").write_bytes(b"invalid")
    calls = []
    monkeypatch.setattr(publisher, "github_release", lambda *_: None)
    monkeypatch.setattr(publisher, "gh", lambda *args: calls.append(args))
    with pytest.raises(ValueError, match="invalid"):
        publisher.publish(tmp_path, "owner/repo", "commit")
    assert not calls


@pytest.mark.parametrize("matching_digest", [False, True])
def test_only_complete_matching_assets_are_published(publisher, tmp_path, monkeypatch, matching_digest):
    content = (tmp_path / "dist/CitrusDrop.exe").read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    draft = {"draft": True, "prerelease": True, "assets": [
        {"name": "CitrusDrop.exe", "state": "uploaded", "size": len(content), "digest": "sha256:" + (digest if matching_digest else "wrong")},
        {"name": "SHA256SUMS.txt", "state": "uploaded", "size": len(f"{digest}  CitrusDrop.exe\n".encode())},
    ]}
    responses = iter([None, draft, {"draft": False, "prerelease": True, "html_url": "https://github.com/owner/repo/releases/tag/v0.3.3"}])
    calls = []
    monkeypatch.setattr(publisher, "github_release", lambda *_: next(responses))
    monkeypatch.setattr(publisher, "gh", lambda *args: calls.append(args))
    if matching_digest:
        publisher.publish(tmp_path, "owner/repo", "commit")
        assert calls[-1][:2] == ("release", "edit")
        assert "--draft=false" in calls[-1] and "--prerelease" in calls[-1]
        assert (tmp_path / "dist/SHA256SUMS.txt").read_text().split()[0] == digest
    else:
        with pytest.raises(RuntimeError, match="digest"):
            publisher.publish(tmp_path, "owner/repo", "commit")
        assert not any(args[1] == "edit" for args in calls)


def test_api_permission_error_is_not_treated_as_missing_release(publisher, monkeypatch):
    monkeypatch.setenv("GH_TOKEN", "test-only")
    def reject(*args, **kwargs):
        raise HTTPError("https://api.github.com", 403, "Forbidden", {}, None)
    monkeypatch.setattr(publisher, "urlopen", reject)
    with pytest.raises(HTTPError):
        publisher.github_release("owner/repo", "v0.3.3")
