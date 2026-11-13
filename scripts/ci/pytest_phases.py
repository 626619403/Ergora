"""Pytest observations without replacing its multiprocessing-safe entry point."""

import hashlib
import json
from pathlib import Path
import sys
import time

import pytest


def pytest_addoption(parser):
    parser.addoption('--ci-results', default='ci-results', help='Fresh CI observation directory')
    parser.addoption('--ci-group', type=int, default=None, help='Linux group index; omitted means full selection')
    parser.addoption('--ci-groups', default=str(Path(__file__).with_name('linux-groups.json')), help='Explicit Linux file groups')


def pytest_configure(config):
    observer = PhaseLog(Path(config.getoption('--ci-results')), config.getoption('--ci-group'), Path(config.getoption('--ci-groups')))
    config.pluginmanager.register(observer, 'ergora-ci-phase-log')


class PhaseLog:
    def __init__(self, directory, group, groups_file):
        directory.mkdir(parents=True, exist_ok=True)
        self.directory = directory
        self.group = group
        self.groups_file = groups_file
        self.started = time.monotonic()
        self.stream = (directory / 'phases.jsonl').open('x', encoding='utf-8', buffering=1)
        self.emit('identity', python=sys.version, executable=sys.executable, group=group,
                  plugin_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())

    def emit(self, event, **fields):
        self.stream.write(json.dumps({'elapsed': time.monotonic() - self.started,
                                      'event': event, **fields}) + '\n')

    def pytest_collection_modifyitems(self, session, config, items):
        self.emit('coverage', all_nodeids=[item.nodeid for item in items])
        if self.group is None:
            return
        raw = self.groups_file.read_bytes()
        groups = json.loads(raw)['linux_groups']
        (self.directory / 'linux-groups.json').write_bytes(raw)
        self.emit('partition', groups_sha256=hashlib.sha256(raw).hexdigest(), group_count=len(groups))
        if not 0 <= self.group < len(groups):
            raise pytest.UsageError(f'CI group {self.group} outside configured range')
        names = [name for group in groups for name in group]
        if len(names) != len(set(names)):
            raise pytest.UsageError('CI groups assign a file more than once')
        missing = [name for name in names if not (config.rootpath / name).is_file()]
        if missing:
            raise pytest.UsageError(f'CI groups reference missing files: {missing}')
        assignments = {name: index for index, group in enumerate(groups) for name in group}
        paths = {item.path.relative_to(config.rootpath).as_posix() for item in items}
        unknown = paths - assignments.keys()
        if unknown:
            raise pytest.UsageError(f'Add collected files to CI groups: {sorted(unknown)}')
        selected, deselected = [], []
        for item in items:
            index = assignments[item.path.relative_to(config.rootpath).as_posix()]
            (selected if index == self.group else deselected).append(item)
        if not selected:
            raise pytest.UsageError(f'CI group {self.group} selected no tests')
        items[:] = selected
        config.hook.pytest_deselected(items=deselected)

    def pytest_collectreport(self, report):
        if report.failed or report.skipped:
            self.emit('collection', nodeid=report.nodeid, outcome=report.outcome, detail=report.longreprtext)

    def pytest_collection_finish(self, session):
        self.emit('collected', nodeids=[item.nodeid for item in session.items])

    def pytest_runtest_logstart(self, nodeid, location):
        self.emit('start', nodeid=nodeid)

    @pytest.hookimpl(wrapper=True, tryfirst=True)
    def pytest_runtest_setup(self, item):
        self.emit('phase-start', nodeid=item.nodeid, when='setup')
        return (yield)

    @pytest.hookimpl(wrapper=True, tryfirst=True)
    def pytest_runtest_call(self, item):
        self.emit('phase-start', nodeid=item.nodeid, when='call')
        return (yield)

    @pytest.hookimpl(wrapper=True, tryfirst=True)
    def pytest_runtest_teardown(self, item):
        self.emit('phase-start', nodeid=item.nodeid, when='teardown')
        return (yield)

    def pytest_runtest_logreport(self, report):
        self.emit('phase', nodeid=report.nodeid, when=report.when,
                  report_type=f'{type(report).__module__}.{type(report).__qualname__}',
                  outcome=report.outcome, seconds=report.duration,
                  failure=report.longreprtext if report.failed else None)

    def pytest_sessionfinish(self, session, exitstatus):
        self.emit('finish', exitstatus=int(exitstatus))

    def pytest_unconfigure(self, config):
        self.stream.close()
