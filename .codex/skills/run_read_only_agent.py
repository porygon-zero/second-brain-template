#!/usr/bin/env python3
"""Launch a Second Brain read-only Codex role and verify repository immutability."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path


VAULT = Path(__file__).resolve().parents[2]
MACOS_CODEX = Path("/Applications/ChatGPT.app/Contents/Resources/codex")
ROLE_SKILLS = {
    "expert": "second-brain-expert",
    "interlocutor": "second-brain-interlocutor",
}


def git_output(vault: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ["git", *arguments],
        cwd=vault,
        check=True,
        capture_output=True,
    ).stdout


def repository_snapshot(vault: Path) -> str:
    """Hash HEAD, tracked changes, and untracked file contents."""
    digest = hashlib.sha256()
    digest.update(git_output(vault, "rev-parse", "HEAD"))
    digest.update(git_output(vault, "diff", "--binary", "HEAD", "--"))
    untracked = git_output(
        vault, "ls-files", "--others", "--exclude-standard", "-z"
    ).split(b"\0")
    for encoded_path in sorted(path for path in untracked if path):
        relative = encoded_path.decode("utf-8", errors="surrogateescape")
        path = vault / relative
        digest.update(encoded_path)
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()


def resolve_codex() -> str:
    executable = shutil.which("codex")
    if executable:
        return executable
    if MACOS_CODEX.is_file():
        return str(MACOS_CODEX)
    raise FileNotFoundError("Codex CLI was not found on PATH or in the macOS app bundle")


def codex_command(vault: Path, role: str, request: str) -> list[str]:
    skill = ROLE_SKILLS[role]
    prompt = f"Use ${skill} to handle this request:\n\n{request}"
    return [
        resolve_codex(),
        "--sandbox",
        "read-only",
        "--ask-for-approval",
        "never",
        "exec",
        "--ephemeral",
        "--cd",
        str(vault),
        prompt,
    ]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a read-only Second Brain role under the Codex sandbox."
    )
    parser.add_argument("role", choices=sorted(ROLE_SKILLS))
    parser.add_argument("request", help="user request passed to the selected role")
    parser.add_argument("--vault", type=Path, default=VAULT, help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    vault = args.vault.resolve()
    try:
        before = repository_snapshot(vault)
        completed = subprocess.run(codex_command(vault, args.role, args.request))
        after = repository_snapshot(vault)
    except (FileNotFoundError, OSError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    if before != after:
        print(
            "ERROR: repository state changed during a read-only consultation",
            file=sys.stderr,
        )
        return 3
    print("Read-only verification passed: repository state is unchanged.")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
