"""Bounded ordinary-file trees with the original Agent Skills content identity."""

import hashlib
import json
from pathlib import Path
import stat


def manifest_digest(files: dict) -> str:
    """Original Skill identity, shared by on-disk and proposed file manifests."""
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()


def is_link(path: Path) -> bool:
    details = path.lstat()
    return stat.S_ISLNK(details.st_mode) or bool(
        getattr(details, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def inventory_tree(directory: Path, *, label: str = "Skill", max_directories: int | None = None,
                   max_depth: int | None = None) -> tuple[str, dict, list[str]]:
    if is_link(directory) or not directory.is_dir():
        raise ValueError(f"{label} bundles require a real directory without symlinks or reparse points")
    files, total, directories = {}, 0, []
    pending = [(directory, 0)]
    while pending:
        parent, depth = pending.pop()
        for path in parent.iterdir():
            if is_link(path) or path.name == ".git":
                raise ValueError(f"{label} bundles cannot contain symlinks, reparse points or .git")
            details = path.stat()
            if stat.S_ISDIR(details.st_mode):
                directories.append(path.relative_to(directory).as_posix())
                if ((max_directories is not None and len(directories) > max_directories) or
                        (max_depth is not None and depth >= max_depth)):
                    raise ValueError(f"{label} bundle exceeds directory count or depth limit")
                pending.append((path, depth + 1))
            elif stat.S_ISREG(details.st_mode):
                total += details.st_size
                if total > 10_000_000 or len(files) >= 500:
                    raise ValueError(f"{label} bundle exceeds 10 MB / 500 files")
                with path.open("rb") as stream:
                    digest = hashlib.file_digest(stream, "sha256").hexdigest()
                files[path.relative_to(directory).as_posix()] = {
                    "sha256": digest, "executable_bits": stat.S_IMODE(details.st_mode) & 0o111}
            else:
                raise ValueError(f"{label} bundles cannot contain special files: {path.name}")
    files = dict(sorted(files.items()))
    digest = manifest_digest(files)
    return digest, files, sorted(directories)


def digest_tree(directory: Path) -> tuple[str, dict]:
    """Keep the established Skill interface, identity and directory acceptance."""
    digest, files, _ = inventory_tree(directory)
    return digest, files
