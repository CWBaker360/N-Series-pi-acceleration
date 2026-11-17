#!/usr/bin/env python3
"""Build the shipped-file SHA-256 manifest for Version 3.0."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXCLUDED_NAMES = {
    "PACKAGE_MANIFEST.json",
    "pi_g_verification_report.aux",
    "pi_g_verification_report.log",
    "pi_g_verification_report.out",
    "pi_g_verification_report.toc",
}
EXCLUDED_SUFFIXES = {".pyc"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def included_files() -> list[Path]:
    paths: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts:
            continue
        if path.name in EXCLUDED_NAMES or path.suffix in EXCLUDED_SUFFIXES:
            continue
        paths.append(path)
    return sorted(paths, key=lambda item: item.relative_to(ROOT).as_posix())


def main() -> None:
    output_manifest = json.loads(
        (ROOT / "output" / "pi_g_verification_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    r9 = output_manifest["r9_certificate"]
    files = []
    for path in included_files():
        files.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )

    manifest = {
        "package": "Baker pi_g certified verification package",
        "version": "3.0",
        "date": "2026-07-30",
        "overall_verdict": output_manifest["overall_verdict"],
        "working_precision_decimal_digits": output_manifest[
            "working_precision_decimal_digits"
        ],
        "level_count": output_manifest["level_count"],
        "r9_total_certified_abs_error_bound": r9[
            "total_certified_abs_error_bound"
        ],
        "r9_certified_absolute_decimal_places": r9[
            "certified_absolute_decimal_places"
        ],
        "claim_boundary": (
            "R9 is a rigorous finite-value enclosure. Cross-domain checks are "
            "supplementary; H6, E7, and R8 are library-level checks."
        ),
        "manifest_self_hash_note": (
            "PACKAGE_MANIFEST.json is necessarily excluded from its own file list."
        ),
        "files": files,
    }
    destination = ROOT / "PACKAGE_MANIFEST.json"
    destination.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote: {destination}")
    print(f"files_hashed: {len(files)}")
    print(f"manifest_sha256: {sha256_file(destination)}")


if __name__ == "__main__":
    main()
