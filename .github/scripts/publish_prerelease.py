"""Publish the current, verified Windows build without replacing released versions."""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tomllib
from urllib.request import Request, urlopen


def github_release(repository, tag):
    # The list endpoint includes drafts for the authenticated writer; tag lookup is for published releases.
    page = 1
    while True:
        request = Request(f"https://api.github.com/repos/{repository}/releases?per_page=100&page={page}", headers={
            "Authorization": f"Bearer {os.environ['GH_TOKEN']}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10",
        })
        with urlopen(request, timeout=30) as response:
            releases = json.load(response)
        for release in releases:
            if release["tag_name"] == tag:
                return release
        if len(releases) < 100:
            return None
        page += 1


def current_version(root):
    version = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("Use a numeric x.y.z app version; releases are marked as pre-release separately")
    tree = ast.parse((root / "citrus_drop/__init__.py").read_text(encoding="utf-8"))
    app_version = next(ast.literal_eval(node.value) for node in tree.body
                       if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__version__" for t in node.targets))
    if app_version != version:
        raise ValueError("App and pyproject versions do not match")
    return version


def gh(*arguments):
    subprocess.run(["gh", *arguments], check=True)


def publish(root, repository, commit):
    tag = "v" + current_version(root)
    existing = github_release(repository, tag)
    if existing and not existing["draft"]:
        notes = root / f"docs/releases/{tag}.md"
        if notes.is_file() and existing.get("body", "").replace("\r\n", "\n").strip() != notes.read_text(encoding="utf-8").strip():
            gh("release", "edit", tag, "--repo", repository, "--notes-file", str(notes))
            print(f"Updated {tag} release notes.")
        print(f"{tag} is already published; its tag, assets and pre-release status are unchanged.")
        return
    if existing and existing["target_commitish"] != commit:
        raise ValueError("An existing draft belongs to another commit; refusing to change it")
    executable = root / "dist/CitrusDrop.exe"
    with executable.open("rb") as source:
        if source.read(2) != b"MZ":
            raise ValueError("The verified Windows executable is missing or invalid")
    notes = root / f"docs/releases/{tag}.md"
    if not notes.is_file():
        raise FileNotFoundError(f"Write release notes before publishing: {notes}")
    checksum = root / "dist/SHA256SUMS.txt"
    digest = hashlib.sha256(executable.read_bytes()).hexdigest()
    checksum.write_text(f"{digest}  CitrusDrop.exe\n", encoding="utf-8", newline="\n")
    if not existing:
        gh("release", "create", tag, "--repo", repository, "--target", commit,
           "--title", f"Citrus Drop {tag} (Pre-release)", "--notes-file", str(notes),
           "--draft", "--prerelease", "--latest=false")
    # A retry may resume this commit's unpublished draft; public assets are never replaced.
    gh("release", "upload", tag, str(executable), str(checksum), "--repo", repository, "--clobber")
    draft = github_release(repository, tag)
    expected = {"CitrusDrop.exe": executable.stat().st_size, "SHA256SUMS.txt": checksum.stat().st_size}
    if not draft or not draft["draft"] or not draft["prerelease"]:
        raise RuntimeError("The prepared release is not a pre-release draft")
    assets = {item["name"]: item for item in draft["assets"]}
    if set(assets) != set(expected):
        raise RuntimeError("Release asset names do not match the prepared package")
    for name, size in expected.items():
        if assets[name]["state"] != "uploaded" or assets[name]["size"] != size:
            raise RuntimeError(f"Release asset upload is incomplete: {name}")
    if assets["CitrusDrop.exe"].get("digest") != f"sha256:{digest}":
        raise RuntimeError("Uploaded EXE digest does not match the verified build")
    gh("release", "edit", tag, "--repo", repository, "--draft=false", "--prerelease", "--latest=false")
    published = github_release(repository, tag)
    if not published or published["draft"] or not published["prerelease"]:
        raise RuntimeError("The release was not published as a pre-release")
    print(published["html_url"])


if __name__ == "__main__":
    publish(Path(__file__).resolve().parents[2], os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_SHA"])
