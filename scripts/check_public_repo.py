"""Scan publishable files without printing matched values. Uses only the standard library.

Default: tracked and non-ignored files in the working tree.
--staged: exact added/modified index blobs, suitable for a pre-commit check.
--history: unique historical text blobs, checking credential patterns only.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SECRET_RULES = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "provider-key": re.compile(r"(?<![\w-])(?:sk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|hf_[A-Za-z0-9]{24,})"),
    "signed-jwt": re.compile(r"\beyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{20,}\b"),
    "cloud-secret": re.compile(r"(?i)(?:aws_secret_access_key|access_key_secret|api_key)\s*[:=]\s*['\"][A-Za-z0-9/+_-]{32,}['\"]"),
}
PRIVACY_RULES = {
    "personal-email": re.compile(r"\b[\w.+-]+@(?:gmail|qq|163|126|outlook|hotmail)\.com\b", re.I),
    "phone-number": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "identity-number": re.compile(r"(?<!\d)[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)"),
    "personal-local-path": re.compile(r"(?i)[c-z]:[\\/](?:Users|Programming)[\\/]"),
}
BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".pdf", ".model"}
FORBIDDEN_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".jks", ".keystore", ".sql", ".dump", ".safetensors", ".pt", ".pth", ".ckpt", ".onnx", ".zip", ".7z"}


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def forbidden_path(name: str) -> bool:
    path = Path(name)
    return (
        path.suffix.lower() in FORBIDDEN_SUFFIXES
        or any(part in {".git", "node_modules", "secrets", ".venv"} for part in path.parts)
        or (path.name.startswith(".env") and path.name != ".env.example")
        or path.name.lower() in {"credentials.json", "service-account.json", "dev_token.txt"}
    )


def scan_text(name: str, payload: bytes, privacy: bool = True) -> list[tuple[str, int, str]]:
    if b"\0" in payload[:8192]:
        return []
    try:
        content = payload.decode("utf-8-sig")
    except UnicodeDecodeError:
        return []
    findings = []
    rules = {**SECRET_RULES, **(PRIVACY_RULES if privacy else {})}
    for rule, pattern in rules.items():
        for match in pattern.finditer(content):
            findings.append((name, content.count("\n", 0, match.start()) + 1, rule))
    return findings


def working_files(staged: bool):
    args = ("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z") if staged else ("ls-files", "--cached", "--others", "--exclude-standard", "-z")
    names = set(git(*args).decode("utf-8").split("\0"))
    for name in sorted(names - {""}):
        if forbidden_path(name):
            yield name, None
        elif Path(name).suffix.lower() not in BINARY_SUFFIXES:
            if staged:
                yield name, git("show", f":{name}")
            else:
                path = ROOT / name
                if path.is_file():
                    if not path.resolve().is_relative_to(ROOT):
                        yield name, None
                    else:
                        yield name, path.read_bytes()


def history_files():
    # git log names only; commit metadata and local .git/config are never exported.
    records = git("rev-list", "--objects", "--all").decode("utf-8").splitlines()
    for record in records:
        object_id, separator, name = record.partition(" ")
        if not separator or Path(name).suffix.lower() in BINARY_SUFFIXES:
            continue
        if git("cat-file", "-t", object_id).strip() == b"blob":
            yield f"{object_id[:12]}:{name}", git("cat-file", "blob", object_id)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--staged", action="store_true")
    scope.add_argument("--history", action="store_true")
    args = parser.parse_args()
    findings = []
    checked = 0
    for name, payload in history_files() if args.history else working_files(args.staged):
        checked += 1
        findings.extend([(name, 0, "private-file")] if payload is None else scan_text(name, payload, privacy=not args.history))
    for name, line, rule in findings[:100]:
        print(f"{name}:{line}: {rule} (value hidden)")
    if findings:
        print(f"FAIL: {len(findings)} findings; rules: {dict(Counter(item[2] for item in findings))}")
        return 1
    print(f"PASS: {checked} publishable text files checked ({'credential history' if args.history else 'staged blobs' if args.staged else 'working tree'}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
