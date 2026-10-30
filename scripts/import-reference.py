"""Reproduce the reference resource from Ergora's reviewed public HTML."""

from __future__ import annotations

import base64
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import zipfile


PROJECT = Path(__file__).resolve().parents[1]
HTML = PROJECT / "docs/distribution/multi-agent-development-platform.html"
DATA = PROJECT / "src/ergora/data"
ZIP_SHA256 = "8018be5094623ca0646d28d3671daaf7ac60774280eefc1c5c023bc19dc5c760"


def main() -> None:
    match = re.search(
        r'<script id="artifact-data" type="application/json">(.*?)</script>',
        HTML.read_text(),
        re.S,
    )
    if match is None:
        raise ValueError("Public artifact-data block is missing")
    metadata = json.loads(match.group(1))
    raw = base64.b64decode(metadata["zip"], validate=True)
    if hashlib.sha256(raw).hexdigest() != ZIP_SHA256:
        raise ValueError("Public archive identity changed; review the new source before importing")
    manifest = {
        "version": metadata["version"],
        "source_html_sha256": hashlib.sha256(HTML.read_bytes()).hexdigest(),
        "source_zip_sha256": ZIP_SHA256,
        "files": {},
    }
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if archive.testzip() is not None:
            raise ValueError("Public archive CRC check failed")
        for member in archive.infolist():
            path = PurePosixPath(member.filename)
            if path.is_absolute() or ".." in path.parts or path.parts[0] != "agentflow-platform":
                raise ValueError("Archive member escapes its expected root")
            if member.is_dir():
                continue
            relative = Path(*path.parts[1:])
            target = DATA / "reference" / relative
            content = archive.read(member)
            if target.exists() and target.read_bytes() != content:
                raise ValueError(f"Preserving modified reference file: {relative}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            manifest["files"][relative.as_posix()] = hashlib.sha256(content).hexdigest()
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "reference-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    )
    print(f"Imported {len(manifest['files'])} public files without changing their contents")


if __name__ == "__main__":
    main()
