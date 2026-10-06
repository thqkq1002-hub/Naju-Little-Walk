"""Inventory this project for a backup without reading secrets or following links."""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REPARSE = 0x400
GENERATED_DIRS = {
    "node_modules", ".git", "__pycache__", ".next", ".vinext",
    ".wrangler", ".pytest_cache", ".mypy_cache", ".ruff_cache",
}
PRIVATE_DIRS = {".openai", ".vercel", ".aws", ".ssh", ".gnupg"}
PRIVATE_NAMES = {"credentials", "credentials.json", "id_rsa", "id_ed25519"}
SECRET_PATTERNS = {
    "meshy_api_key": re.compile(rb"\bmsy_[A-Za-z0-9]{20,}\b"),
    "openai_api_key": re.compile(rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}\b"),
    "github_token": re.compile(rb"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,})\b"),
    "aws_access_key": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}
SECRET_MARKERS = {
    "meshy_api_key": (b"msy_",),
    "openai_api_key": (b"sk-",),
    "github_token": (b"ghp_", b"gho_", b"ghu_", b"ghs_", b"ghr_", b"github_pat_"),
    "aws_access_key": (b"AKIA", b"ASIA"),
    "private_key": (b"PRIVATE KEY-----",),
}


def inspect_stream(stream) -> tuple[str, set[str]]:
    digest = hashlib.sha256()
    findings: set[str] = set()
    tail = b""
    while block := stream.read(4 * 1024 ** 2):
        digest.update(block)
        joined = tail + block
        findings.update(
            name for name, pattern in SECRET_PATTERNS.items()
            if any(marker in joined for marker in SECRET_MARKERS[name]) and pattern.search(joined)
        )
        tail = joined[-4096:]
    return digest.hexdigest(), findings


def inspect_archive(path: Path) -> list[dict]:
    """Only return paths and finding types; never print matched credential text."""
    issues = []
    archive_suffix = path.name.lower()
    if archive_suffix.endswith((".tar", ".tar.gz", ".tgz")):
        with tarfile.open(path, "r|*") as archive:
            for member in archive:
                if not member.isfile():
                    continue
                category, _ = classification(member.name.removeprefix("./"))
                if category == "private_configuration":
                    issues.append({"member": member.name, "type": "private_configuration"})
                stream = archive.extractfile(member)
                if stream:
                    with stream:
                        _, findings = inspect_stream(stream)
                    issues.extend({"member": member.name, "type": finding} for finding in sorted(findings))
    elif archive_suffix.endswith(".zip"):
        with zipfile.ZipFile(path) as archive:
            for member in archive.infolist():
                if member.is_dir():
                    continue
                category, _ = classification(member.filename.removeprefix("./"))
                if category == "private_configuration":
                    issues.append({"member": member.filename, "type": "private_configuration"})
                with archive.open(member) as stream:
                    _, findings = inspect_stream(stream)
                issues.extend({"member": member.filename, "type": finding} for finding in sorted(findings))
    return issues


def prepare_manifest(inventory_path: Path) -> dict:
    result = json.loads(inventory_path.read_text(encoding="utf-8"))
    files = [row for row in result["files"] if row["category"] not in {"regenerable", "private_configuration", "backup_output"}]
    objects: dict[str, dict] = {}
    issues = []
    accepted = []
    for index, row in enumerate(files, 1):
        path = ROOT / row["path"]
        before = path.stat()
        if (before.st_size, before.st_mtime_ns) != (row["bytes"], row["mtime_ns"]):
            raise RuntimeError(f"File changed since inventory: {row['path']}")
        with path.open("rb") as stream:
            digest, findings = inspect_stream(stream)
        archive_issues = inspect_archive(path)
        if findings or archive_issues:
            issues.append({"path": row["path"], "finding_types": sorted(findings), "archive_findings": archive_issues})
        else:
            after = path.stat()
            if (after.st_size, after.st_mtime_ns) != (before.st_size, before.st_mtime_ns):
                raise RuntimeError(f"File changed while reading: {row['path']}")
            accepted.append({"path": row["path"], "bytes": row["bytes"], "mtime_ns": row["mtime_ns"], "sha256": digest, "category": row["category"]})
            if digest not in objects:
                objects[digest] = {"sha256": digest, "bytes": row["bytes"], "source": row["path"], "paths": []}
            objects[digest]["paths"].append(row["path"])
        if index % 500 == 0:
            print(f"Hashed and inspected {index}/{len(files)} files", flush=True)
    return {
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "root": str(ROOT), "scope": "current_project_only",
        "source_bytes": sum(row["bytes"] for row in accepted),
        "unique_bytes": sum(row["bytes"] for row in objects.values()),
        "file_count": len(accepted), "object_count": len(objects),
        "secret_scan": "provider key signatures and nested tar/zip payload inspection; not a guarantee against all secret formats",
        "excluded_direct_files": [row for row in result["files"] if row["category"] in {"regenerable", "private_configuration"}],
        "blocked_files": issues, "skipped_links": result["links"],
        "files": accepted, "objects": list(objects.values()),
    }


def classification(relative: str) -> tuple[str, str]:
    parts = Path(relative).parts
    lower = tuple(p.lower() for p in parts)
    name = lower[-1]
    if any(p in PRIVATE_DIRS for p in lower) or name.startswith(".env"):
        return "private_configuration", "인증·개인 설정: 별도 안전 보관 필요"
    if name in PRIVATE_NAMES or Path(name).suffix in {".pem", ".key", ".p12", ".pfx"}:
        return "private_configuration", "인증 파일 가능성: 공개/일반 압축 백업 제외"
    if any(p in GENERATED_DIRS for p in lower):
        return "regenerable", "Git 메타데이터 또는 재설치 가능한 라이브러리·캐시"
    if lower[0] == "dist" or name.endswith((".tsbuildinfo", ".pyc")):
        return "regenerable", "다시 생성 가능한 빌드 결과"
    if lower[:2] == ("work", "github-backup-20261004"):
        return "backup_output", "이번 백업 산출물: 재귀 포함 방지"
    if lower[:2] == ("work", "tools") or lower[:2] == ("work", "python-geo"):
        return "regenerable", "Blender/지리 처리 실행 환경"
    if lower[0] in {"assets", "outputs"}:
        return "authoring", "캐릭터·Blender 제작 원본 및 작업 산출물"
    if lower[0] == "public":
        return "app_assets", "앱 실행 모델·이미지·지도 데이터"
    if lower[0] in {"work", "temp"}:
        return "working_reference", "작업 자료: 개별 검토 후 비공개 보관"
    return "source_documentation", "앱 소스·문서·스크립트"


def git_paths() -> set[str]:
    result = subprocess.run(
        ["git", "-c", "core.quotepath=false", "ls-files", "-z"], cwd=ROOT,
        capture_output=True, check=True,
    )
    return set(result.stdout.decode("utf-8").split("\0")) - {""}


def inventory() -> dict:
    tracked = git_paths()
    files, links, errors = [], [], []
    stack = [ROOT]
    while stack:
        directory = stack.pop()
        try:
            entries = list(os.scandir(directory))
        except OSError as exc:
            errors.append({"path": directory.relative_to(ROOT).as_posix(), "error": type(exc).__name__})
            continue
        for entry in entries:
            relative = Path(entry.path).relative_to(ROOT).as_posix()
            try:
                info = entry.stat(follow_symlinks=False)
                if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & REPARSE:
                    links.append({"path": relative, "followed": False})
                    continue
                if entry.is_dir(follow_symlinks=False):
                    stack.append(Path(entry.path))
                    continue
                if not entry.is_file(follow_symlinks=False):
                    continue
                category, reason = classification(relative)
                files.append({
                    "path": relative, "bytes": info.st_size,
                    "mtime_ns": info.st_mtime_ns, "category": category,
                    "tracked": relative in tracked, "reason": reason,
                })
            except OSError as exc:
                errors.append({"path": relative, "error": type(exc).__name__})
    files.sort(key=lambda row: row["path"])
    top, second, categories, extensions = (collections.defaultdict(lambda: {"bytes": 0, "files": 0}) for _ in range(4))
    for row in files:
        parts = row["path"].split("/")
        for summary, key in [
            (top, parts[0] if len(parts) > 1 else "(root)"),
            (second, "/".join(parts[:2]) if len(parts) > 2 else parts[0]),
            (categories, row["category"]),
            (extensions, Path(row["path"]).suffix.lower() or "(none)"),
        ]:
            summary[key]["bytes"] += row["bytes"]
            summary[key]["files"] += 1
    candidates = [row for row in files if row["category"] not in {"regenerable", "private_configuration", "backup_output"}]
    return {
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "root": str(ROOT), "total_bytes": sum(row["bytes"] for row in files),
        "file_count": len(files), "tracked_file_count": sum(row["tracked"] for row in files),
        "candidate_bytes": sum(row["bytes"] for row in candidates), "candidate_count": len(candidates),
        "top_level": dict(top), "second_level": dict(second), "categories": dict(categories),
        "extensions": dict(extensions),
        "large_candidates": [row for row in sorted(candidates, key=lambda row: row["bytes"], reverse=True) if row["bytes"] >= 100 * 1024 ** 2],
        "links": links, "errors": errors, "files": files,
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="work/github-backup-20261004/inventory.json")
    parser.add_argument("--prepare-manifest", action="store_true")
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    if not output.is_relative_to(ROOT):
        raise SystemExit("Output must stay inside this project")
    if args.prepare_manifest:
        result = prepare_manifest(output)
        destination = output.with_name("manifest-draft.json")
        destination.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({key: result[key] for key in ["source_bytes", "unique_bytes", "file_count", "object_count", "blocked_files", "skipped_links"]}, ensure_ascii=False, indent=2))
        return
    result = inventory()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    brief = {key: result[key] for key in [
        "total_bytes", "file_count", "tracked_file_count", "candidate_bytes", "candidate_count",
        "top_level", "categories", "large_candidates", "links", "errors",
    ]}
    brief["largest_second_level"] = sorted(result["second_level"].items(), key=lambda pair: pair[1]["bytes"], reverse=True)[:35]
    print(json.dumps(brief, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
