"""Static import contracts for the installed, first-party control plane."""

import ast
from graphlib import TopologicalSorter
from importlib.util import resolve_name
from pathlib import Path

import pytest

import ergora


@pytest.fixture(scope="module")
def module_imports():
    imports = {}
    for path in Path(ergora.__file__).parent.glob("*.py"):
        names = set()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"), filename=str(path))):
            if isinstance(node, ast.Import):
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                source = resolve_name("." * node.level + (node.module or ""), "ergora")
                names.add(source)
                names.update(f"{source}.{alias.name}" for alias in node.names)
        imports[path.stem] = names
    return imports


@pytest.fixture(scope="module")
def local_dependencies(module_imports):
    return {
        module: {name.split(".")[1] for name in names if name.startswith("ergora.")
                 and name.split(".")[1] in module_imports}
        for module, names in module_imports.items()
    }


def test_control_plane_import_graph_is_acyclic(local_dependencies):
    tuple(TopologicalSorter(local_dependencies).static_order())


@pytest.mark.parametrize("module,allowed", [
    ("components", set()), ("contracts", set()), ("state", set()),
    ("windows_job", set()), ("processes", {"windows_job"}),
])
def test_foundations_do_not_depend_on_application_modules(local_dependencies, module, allowed):
    assert local_dependencies[module] <= allowed


def test_application_modules_do_not_import_entry_points(local_dependencies):
    entry_points = {"__main__", "cli", "web"}
    for module, dependencies in local_dependencies.items():
        if module not in entry_points:
            assert not dependencies & entry_points, (module, dependencies & entry_points)


def test_reference_internals_are_imported_only_at_the_boundary(module_imports):
    internal_roots = ("agent_platform", "dev_platform", "ergora.data.reference")
    for module, names in module_imports.items():
        if module not in {"reference", "reference_executor", "reference_task_creation", "reference_task_runtime", "reference_task_submission", "reference_task_approval"}:
            internals = {name for name in names
                         if any(name == root or name.startswith(root + ".") for root in internal_roots)}
            assert not internals, (module, internals)
