"""Exercise the original local release owner without a Temporal service."""

import asyncio
from dataclasses import asdict
import getpass
import json
import os
import sys
import time

from agent_platform import training as owner
from perf_temporal.models import Binding, Experiment, ReleaseContext, ReleaseRequest


async def main():
    ident = sys.argv[1] if len(sys.argv) > 1 else 'alpha'
    spec = json.loads((owner.TRAINING / 'specs' / (ident + '.json')).read_bytes())
    experiment = Experiment(**{**spec, 'binding': Binding(**spec['binding'])})
    adapter = owner.create_adapter()
    job = await adapter.lookup_job(experiment)
    gate = await adapter.collect_and_gate(job)
    receipt_id = 'owner-native-fence-order-' + ident
    receipt = owner.TRAINING / 'approvals' / (receipt_id + '.json')
    if not receipt.exists():
        owner.write(receipt, {'binding': asdict(job.binding), 'evidence_sha256': gate.evidence_sha,
                             'decision': 'approve', 'role': 'owner', 'actor_id': f'unix:{os.getuid()}:{getpass.getuser()}',
                             'revoked': False, 'expires_at': time.time() + 300})
        receipt.chmod(0o600)
    context = ReleaseContext(experiment, gate, ReleaseRequest(job.binding, gate.evidence_sha, receipt_id))
    ticket = await adapter.authorize_release_and_create_task(context)
    print(json.dumps(asdict(ticket)))


if __name__ == '__main__':
    asyncio.run(main())
