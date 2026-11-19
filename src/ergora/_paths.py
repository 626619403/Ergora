"""Physical roots shared by resource reads, process entrypoints and source identity."""

from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent
IMPORT_ROOT = PACKAGE_ROOT.parent
DATA_ROOT = PACKAGE_ROOT / "data"
