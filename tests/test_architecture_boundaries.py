"""Static import contracts for the installed, first-party control plane."""

import ast
from graphlib import TopologicalSorter
from importlib.util import resolve_name
from pathlib import Path
import sys

import pytest

import ergora


@pytest.fixture(scope="module")
def module_paths():
    root = Path(ergora.__file__).parent
    modules = {}
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root)
        if relative.parts[0] == "data":
            continue
        parts = relative.with_suffix("").parts
        if parts[-1] == "__init__":
            parts = parts[:-1]
        modules[".".join(("ergora", *parts))] = path
    return modules


@pytest.fixture(scope="module")
def module_imports(module_paths):
    imports = {}
    for module, path in module_paths.items():
        package = module if path.name == "__init__.py" else module.rpartition(".")[0]
        names = set()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"), filename=str(path))):
            if isinstance(node, ast.Import):
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                source = resolve_name("." * node.level + (node.module or ""), package)
                names.add(source)
                names.update(f"{source}.{alias.name}" for alias in node.names)
        imports[module] = names
    return imports


@pytest.fixture(scope="module")
def local_dependencies(module_imports):
    return {
        module: names & module_imports.keys()
        for module, names in module_imports.items()
    }


def test_responsibility_packages_have_no_initialization_side_effects(module_paths):
    for module, path in module_paths.items():
        if module != "ergora" and path.name == "__init__.py":
            assert not ast.parse(path.read_text(encoding="utf-8"), filename=str(path)).body, module


def test_control_plane_import_graph_is_acyclic(local_dependencies):
    tuple(TopologicalSorter(local_dependencies).static_order())


@pytest.mark.parametrize("module,allowed", [
    ("ergora._paths", set()),
    ("ergora.configuration.catalog", {"ergora._paths"}),
    ("ergora.configuration.validation", {"ergora._paths"}),
    ("ergora.storage.state", set()), ("ergora.storage.git", set()),
    ("ergora.storage.assets", set()),
    ("ergora.training.materials", {"ergora.storage.assets"}),
    ("ergora.development.route_errors", set()),
    ("ergora.development.dags", {"ergora.development.route_errors"}), ("ergora.issues.identity", set()),
    ("ergora.runtime.budget_clock", set()),
    ("ergora.development.budget", {
        "ergora.runtime", "ergora.runtime.budget_clock", "ergora.development.dags",
    }),
    ("ergora.development.six_stage", {"ergora.development.route_errors"}),
    ("ergora.development.envelopes", {
        "ergora.configuration.catalog", "ergora.development.dags", "ergora.issues.identity",
        "ergora.development.budget", "ergora.development.six_stage", "ergora.development.route_errors",
        "ergora.development", "ergora.development.verification", "ergora.training.materials",
    }),
    ("ergora.development.handoff", {
        "ergora._paths", "ergora.configuration", "ergora.configuration.validation",
        "ergora.development.envelopes", "ergora.issues.identity",
    }),
    ("ergora.runtime.windows_job", set()),
    ("ergora.runtime.processes", {"ergora.runtime.windows_job"}),
    ("ergora.development.verification", {
        "ergora.storage.assets", "ergora.storage.git", "ergora.training.materials",
    }),
])
def test_foundations_do_not_depend_on_application_modules(local_dependencies, module_imports, module, allowed):
    assert local_dependencies[module] <= allowed, (module, local_dependencies[module] - allowed)
    if module in {
        "ergora._paths", "ergora.configuration.catalog", "ergora.development.dags",
        "ergora.development.envelopes", "ergora.development.route_errors", "ergora.issues.identity", "ergora.runtime.budget_clock",
        "ergora.development.budget", "ergora.development.six_stage", "ergora.storage.git",
        "ergora.development.verification", "ergora.training.materials", "ergora.storage.assets",
    }:
        external_roots = {name.split(".")[0] for name in module_imports[module]
                          if name.split(".")[0] != "ergora"}
        assert external_roots <= sys.stdlib_module_names


def test_application_modules_do_not_import_entry_points(local_dependencies):
    entry_points = {
        module for module in local_dependencies
        if module == "ergora.__main__" or module == "ergora.interfaces"
        or module.startswith("ergora.interfaces.")
    }
    for module, dependencies in local_dependencies.items():
        if module not in entry_points:
            assert not dependencies & entry_points, (module, dependencies & entry_points)


def test_reference_internals_are_imported_only_at_the_boundary(module_imports):
    internal_roots = ("agent_platform", "dev_platform", "perf_temporal", "ergora.data.reference")
    native_owners = {
        "ergora.development.native", "ergora.development.inputs", "ergora.training.native",
        "ergora.training.execution_protocol",
    }
    native_packages = ("ergora.native", "ergora.development.runtime", "ergora.training.runtime")
    for module, names in module_imports.items():
        if module not in native_owners and not any(
            module == owner or module.startswith(owner + ".") for owner in native_packages
        ):
            internals = {name for name in names
                         if any(name == root or name.startswith(root + ".") for root in internal_roots)}
            assert not internals, (module, internals)
