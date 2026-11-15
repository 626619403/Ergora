"""Keep real detached budget owners/helpers; reuse the existing SDK service double."""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
import training_submission_client as base
import training_cancellation_client

from ergora.reference_training_worker import budget_main
from ergora import reference_training_budget as budget
import os
import time

fault = os.environ.get('ERGORA_TEST_TRAINING_BUDGET')
if fault == 'monitor-blocked' and base.payload['mode'] == 'monitor':
    async def blocked(_self):
        time.sleep(60)
    budget.BudgetedStart.completion = blocked
if fault in ('fence-flush-failed', 'fence-flush-blocked') and base.payload['mode'] == 'fence':
    original = budget.training_cycles._sync_directory
    def flush(directory):
        if directory.name == 'fences':
            if fault == 'fence-flush-blocked':
                time.sleep(60)
            raise OSError('Controlled fence directory fsync failure')
        return original(directory)
    budget.training_cycles._sync_directory = flush
if fault in ('final-file-blocked', 'final-directory-blocked') and base.payload['mode'] in ('owner', 'publish'):
    original = budget.os.fsync
    def fsync(descriptor):
        path = Path('/proc/self/fd/' + str(descriptor)).resolve()
        if (fault == 'final-file-blocked' and path.name.startswith('.pending-')
                and path.parent.name == 'alpha.budget' and 'executor_stop_confirmed' in json.loads(path.read_bytes())
                or fault == 'final-directory-blocked' and path.name == 'alpha.budget' and (path / 'final.json').exists()):
            base.storage.with_suffix('.final-blocked').write_text(fault)
            time.sleep(60)
        return original(descriptor)
    budget.os.fsync = fsync

base.payload['request_id'] = 'budget-' + base.payload['intent_sha256'][:32]
sys.stdin = base.io.StringIO(json.dumps(base.payload))
base.install_budget_fixture()
budget_main()
