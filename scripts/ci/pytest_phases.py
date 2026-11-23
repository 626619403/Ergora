"""Pytest observations without replacing its multiprocessing-safe entry point."""

import hashlib
import json
import os
from pathlib import Path
import sys
import time

import pytest


def pytest_addoption(parser):
    parser.addoption('--ci-results', default='ci-results', help='Fresh CI observation directory')
    parser.addoption('--ci-group', type=int, default=None, help='Linux group index; omitted means full selection')
    parser.addoption('--ci-groups', default=str(Path(__file__).with_name('linux-groups.json')), help='Explicit Linux file and node-shard groups')


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
        self.emit('identity', python=sys.version, executable=sys.executable, pid=os.getpid(), group=group,
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
        assignments = {}
        for index, group in enumerate(groups):
            for entry in group:
                if isinstance(entry, str):
                    name, shard, count, whole = entry, 0, 1, True
                elif isinstance(entry, dict) and set(entry) == {'file', 'shard', 'shards'}:
                    name, shard, count, whole = entry['file'], entry['shard'], entry['shards'], False
                    if (not isinstance(name, str) or type(shard) is not int or type(count) is not int
                            or count < 1 or not 0 <= shard < count):
                        raise pytest.UsageError(f'Invalid CI file shard: {entry}')
                else:
                    raise pytest.UsageError(f'Invalid CI group entry: {entry}')
                previous = assignments.get(name)
                if previous is None:
                    previous = assignments[name] = {'whole': whole, 'count': count, 'groups': {}}
                elif previous['whole'] or whole:
                    raise pytest.UsageError(f'CI groups assign a whole file more than once: {name}')
                if previous['count'] != count or shard in previous['groups']:
                    raise pytest.UsageError(f'CI file shards disagree or repeat: {name}')
                previous['groups'][shard] = index
        for name, assignment in assignments.items():
            if set(assignment['groups']) != set(range(assignment['count'])):
                raise pytest.UsageError(f'CI file shards are incomplete: {name}')
        missing = [name for name in assignments if not (config.rootpath / name).is_file()]
        if missing:
            raise pytest.UsageError(f'CI groups reference missing files: {missing}')
        paths = {item.path.relative_to(config.rootpath).as_posix() for item in items}
        unknown = paths - assignments.keys()
        if unknown:
            raise pytest.UsageError(f'Add collected files to CI groups: {sorted(unknown)}')
        uncollected = assignments.keys() - paths
        if uncollected:
            raise pytest.UsageError(f'CI groups reference files without collected tests: {sorted(uncollected)}')
        nodeids = [item.nodeid for item in items]
        if len(nodeids) != len(set(nodeids)):
            raise pytest.UsageError('CI collection repeats test node IDs')
        selected, deselected = [], []
        group_counts = [0] * len(groups)
        shard_counts = {name: dict.fromkeys(assignment['groups'], 0) for name, assignment in assignments.items()}
        for item in items:
            name = item.path.relative_to(config.rootpath).as_posix()
            assignment = assignments[name]
            shard = int.from_bytes(hashlib.sha256(item.nodeid.encode('utf-8')).digest(), 'big') % assignment['count']
            index = assignment['groups'][shard]
            shard_counts[name][shard] += 1
            group_counts[index] += 1
            (selected if index == self.group else deselected).append(item)
        empty = [(name, shard) for name, counts in shard_counts.items() for shard, count in counts.items() if count == 0]
        if empty:
            raise pytest.UsageError(f'CI file shards contain no tests: {empty}')
        empty_groups = [index for index, count in enumerate(group_counts) if count == 0]
        if empty_groups:
            raise pytest.UsageError(f'CI groups contain no tests: {empty_groups}')
        self.emit('shards', counts=shard_counts, group_counts=group_counts)
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
