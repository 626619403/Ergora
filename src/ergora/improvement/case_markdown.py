"""Bounded shared-case Markdown decoding for publication and frozen readers."""

from pathlib import PureWindowsPath
import re

from ergora.training.materials import decode_record


MAX_MARKDOWN_BYTES = 65_536
MAX_REVISION = 999_999_999
CASE_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_MAX_METADATA_BYTES = 8_192


def validate_id(value) -> str:
    if (not isinstance(value, str) or len(value) > 64 or CASE_ID.fullmatch(value) is None
            or PureWindowsPath(value).is_reserved()):
        raise ValueError("Shared case ID requires a portable lowercase letter, digit and hyphen slug")
    return value


def decode_markdown(raw: bytes) -> tuple[dict, str, str]:
    """Read the original identity and body without consulting a library or host state."""
    if len(raw) > MAX_MARKDOWN_BYTES:
        raise ValueError(f"Shared case Markdown exceeds {MAX_MARKDOWN_BYTES} UTF-8 bytes")
    markdown = raw.decode("utf-8")
    text = markdown.removeprefix("\ufeff").replace("\r\n", "\n")
    if not text.startswith("---\n"):
        raise ValueError("Shared case Markdown requires JSON front matter between --- delimiters")
    header, delimiter, body = text[4:].partition("\n---\n")
    if not delimiter or len(header.encode("utf-8")) > _MAX_METADATA_BYTES or not body.strip():
        raise ValueError("Shared case requires front matter of at most 8192 bytes and a nonempty Markdown body")
    try:
        record = decode_record(header.encode("utf-8"))
    except ValueError as error:
        raise ValueError(f"Invalid shared case front matter: {error}") from error
    validate_id(record.get("id"))
    revision = record.get("revision")
    if type(revision) is not int or not 1 <= revision <= MAX_REVISION:
        raise ValueError(f"Shared case revision requires an integer from 1 to {MAX_REVISION}")
    return record, markdown, body
