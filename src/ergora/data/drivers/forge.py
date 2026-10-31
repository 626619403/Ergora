"""Fixed-version ForgeKernel API bridge; execute in its own Python environment."""

from contextlib import redirect_stdout
import hashlib
import json
from pathlib import Path
import sys

from forgekernel.launch import _check_providers, describe, drive
from forgekernel.localenv import load_machine
from forgekernel.paths import repo_root
from forgekernel.runs import new_run, open_run
from forgekernel.task import load_task
from forgekernel import taskcard


def main():
    request = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    if repo_root().resolve() != Path(request["checkout"]).resolve():
        raise ValueError("The selected Python must import ForgeKernel from the configured checkout")
    expected = request.get("global_config_sha256")
    if not expected or any(hashlib.sha256((repo_root() / "global_config" / name).read_bytes()).hexdigest() != digest
                           for name, digest in expected.items()):
        raise ValueError("Forge global_config differs from the frozen campaign identity; restore it before continuing")
    machine = load_machine()
    if machine.delivery != "local":
        raise ValueError("The Ergora ForgeKernel adapter currently supports local delivery only")
    action = request["action"]
    campaign = request.get("campaign")
    result = {"action": action, "campaign": campaign}
    with redirect_stdout(sys.stderr):
        if action in ("plan", "prepare"):
            task = load_task(request["task"])
            _check_providers(task, machine)
            result["plan"] = describe(task, machine)
            if action == "prepare":
                run = new_run(task, root=Path(request["native_root"]), machine=machine)
                result.update(campaign=str(run.dir), native_record=run.record())
        else:
            if not campaign:
                candidates = list(Path(request["native_root"]).glob("*/run.json"))
                if len(candidates) != 1:
                    raise ValueError("Cannot reconcile a unique native campaign; inspect native_root without resubmitting")
                campaign = str(candidates[0].parent)
            run = open_run(campaign)
            result["campaign"] = str(run.dir)
            if action == "run":
                code = drive(run, machine, resuming=run.record().get("status") != "created")
                result["native_returncode"] = code
            result["native_record"] = run.record()
            result["artifacts"] = {}
            task = load_task(run.task_dir, name=run.task_name)
            candidate = "best/" + Path(taskcard.kernel_file(task)).name
            for relative in ("report.md", candidate):
                file = run.dir / relative
                if file.is_file():
                    result["artifacts"][relative] = {"path": str(file), "sha256": hashlib.sha256(file.read_bytes()).hexdigest()}
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
