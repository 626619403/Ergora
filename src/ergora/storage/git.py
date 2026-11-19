"""Offline, bounded Git objects shared by formal and advisory source readers."""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Callable


def text_blob(content: bytes) -> dict:
    if b"\0" in content:
        raise ValueError("Complete review source contains binary content")
    if content.startswith((b"version https://git-lfs.github.com/spec/v1\n",
                           b"version https://git-lfs.github.com/spec/v1\r\n")):
        raise ValueError("Complete review source requires LFS content, not a pointer")
    return {"sha256": hashlib.sha256(content).hexdigest(), "text": content.decode("utf-8")}


class GitMaterials:
    """Read exact objects, never the worktree, filters or an implicit fetch."""

    def __init__(self, repository: Path, *, git: str = "git", scratch: Path | None = None,
                 max_bytes: int = 1_000_000):
        self.repository = repository
        self.git = git
        self.scratch = scratch
        self.max_bytes = max_bytes
        self._checked = False

    def _run(self, arguments: tuple[str, ...], limit: int, input_data: bytes | None) -> bytes:
        env = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}
        env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0",
                   GIT_NO_LAZY_FETCH="1", GIT_OPTIONAL_LOCKS="0")
        command = [self.git, "--no-replace-objects", "--literal-pathspecs", "-c", f"core.hooksPath={os.devnull}",
                   "-c", "protocol.allow=never", "-C", str(self.repository), *arguments]
        # File stdin avoids a batch read/write pipe deadlock. Two drainers work
        # on Windows pipes too; neither output nor diagnostic capture is unbounded.
        with tempfile.TemporaryFile(dir=self.scratch) as source:
            source.write(input_data or b"")
            source.seek(0)
            with subprocess.Popen(command, env=env, stdin=source, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
                def drain(stream, budget, *, complete):
                    content = bytearray()
                    while chunk := stream.read(65536):
                        if complete and len(content) + len(chunk) > budget:
                            process.kill()
                            raise ValueError("Complete candidate material exceeds the input byte limit")
                        content.extend(chunk[:max(0, budget - len(content))])
                    return bytes(content)

                with ThreadPoolExecutor(max_workers=2) as readers:
                    output = readers.submit(drain, process.stdout, limit, complete=True)
                    errors = readers.submit(drain, process.stderr, 1500, complete=False)
                    try:
                        process.wait(timeout=60)
                        raw, detail = output.result(), errors.result()
                        if process.returncode:
                            raise ValueError("Git material read failed: " + detail.decode("utf-8", errors="replace"))
                        return raw
                    finally:
                        if process.poll() is None:
                            process.kill()
                        process.wait()

    def read(self, *arguments: str, limit: int | None = None, input_data: bytes | None = None) -> bytes:
        if not self._checked:
            version = self._run(("--version",), 1500, None).decode("ascii").strip()
            match = re.fullmatch(r"git version (\d+)\.(\d+)[^\n]*", version)
            if match is None or tuple(map(int, match.groups())) < (2, 43):
                raise ValueError("Offline material reading requires Git 2.43 or later with GIT_NO_LAZY_FETCH support")
            self._checked = True
        return self._run(arguments, self.max_bytes if limit is None else limit, input_data)

    def repository_sources(self, commits: dict[str, str], paths: list[str], *,
                           authorize: Callable[[str], bool] | None = None) -> dict:
        """Read each full blob once after a batched size check; preserve CRLF."""
        repository, objects = {}, set()
        for label, commit in commits.items():
            files = {}
            tree = self.read("ls-tree", "-r", "-z", commit, "--", *paths)
            for entry in tree.split(b"\0"):
                if not entry:
                    continue
                metadata, name = entry.split(b"\t", 1)
                mode, kind, oid = metadata.decode("ascii").split()
                path = name.decode("utf-8")
                if kind != "blob" or mode not in ("100644", "100755"):
                    raise ValueError("Review source must be an ordinary Git file: " + path)
                if authorize is not None and not authorize(path):
                    raise ValueError("Review source exceeds the leaf read scope: " + path)
                files[path] = {"git_object": oid, "mode": mode}
                objects.add(oid)
            repository[label] = {"commit": commit, "files": files}
        ordered = sorted(objects)
        requests = "".join(oid + "\n" for oid in ordered).encode("ascii")
        sizes = self.read("cat-file", "--batch-check", input_data=requests).splitlines()
        if len(sizes) != len(ordered):
            raise ValueError("Incomplete Git object size response")
        expected, total = {}, 0
        for oid, header in zip(ordered, sizes):
            fields = header.decode("ascii").split()
            if len(fields) != 3 or fields[:2] != [oid, "blob"]:
                raise ValueError("Review object is not the requested local Git blob: " + oid)
            expected[oid] = int(fields[2])
            total += int(fields[2]) + len(header) + 2
        if total > self.max_bytes:
            raise ValueError("Complete candidate material exceeds the input byte limit")
        raw = self.read("cat-file", "--batch", input_data=requests)
        offset, blobs = 0, {}
        for oid in ordered:
            end = raw.index(b"\n", offset)
            if raw[offset:end] != f"{oid} blob {expected[oid]}".encode("ascii"):
                raise ValueError("Git blob header changed")
            start, finish = end + 1, end + 1 + expected[oid]
            content = raw[start:finish]
            if len(content) != expected[oid] or raw[finish:finish + 1] != b"\n":
                raise ValueError("Incomplete Git blob response")
            blobs[oid] = text_blob(content)
            offset = finish + 1
        if offset != len(raw):
            raise ValueError("Unexpected trailing Git blob response")
        repository["blobs"] = blobs
        repository["scope"] = paths
        return repository
