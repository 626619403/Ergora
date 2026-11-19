"""Selected native executor and worker command assembly."""

from __future__ import annotations

from pathlib import Path
import sys

from .._paths import IMPORT_ROOT
from .resources import validate_installation


def executor(installation: Path, home: Path, request: Path | None = None):
    if sys.platform != "linux":
        raise ValueError("The formal reference executor requires Linux; use WSL2 and a trusted Linux container")
    installation = validate_installation(installation)
    sys.path[:0] = [str(installation / "local"), str(installation / "upstream/platform")]
    from ..development.runtime import executor as development_executor
    return development_executor.main(home, request)


def worker_command(installation: Path, *, module: str = 'development.runtime.worker', entrypoint: str = 'main') -> list[str]:
    """Run versioned workers with the selected native SDK and this package's code."""
    bootstrap = (f'import sys;sys.path.insert(0,{str(IMPORT_ROOT)!r});'
                 'import ergora;sys.path.pop(0);'
                 f'from ergora.{module} import {entrypoint};{entrypoint}({str(installation)!r})')
    return [str(installation / '.venv/bin/python'), '-P', '-c', bootstrap]


def training_budget_worker_command(installation: Path) -> list[str]:
    """Budget readers use this application's dependencies and optional Temporal SDK."""
    bootstrap = (f'import sys;sys.path.insert(0,{str(IMPORT_ROOT)!r});'
                 f'from ergora.training.runtime.worker import main;main({str(installation)!r})')
    return [sys.executable, '-P', '-c', bootstrap]


def training_cycle_worker_command(installation: Path) -> list[str]:
    """Cycle readers use the application's SDK in their own service process."""
    bootstrap = (f'import sys;sys.path.insert(0,{str(IMPORT_ROOT)!r});'
                 f'from ergora.training.runtime.worker import cycle_main;cycle_main({str(installation)!r})')
    return [sys.executable, '-P', '-c', bootstrap]
