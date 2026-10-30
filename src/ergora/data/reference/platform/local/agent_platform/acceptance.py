from __future__ import annotations

import asyncio
import json
from pathlib import Path
import re
import subprocess
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import uuid

from temporalio.client import Client
from temporalio.worker import Worker

from .core import CONFIG, ROOT, STATE, environment, read, require, write
from .probes import InstallationProbe


async def services(*, restart_temporal: bool = False) -> dict:
    output = STATE / 'acceptance'
    output.mkdir(parents=True, exist_ok=True)
    value = 'install-' + uuid.uuid4().hex
    client = await Client.connect('127.0.0.1:7233')
    async with Worker(client, task_queue='installation-probes', workflows=[InstallationProbe]):
        handle = await client.start_workflow(InstallationProbe.run, value, id=value, task_queue='installation-probes')
        if restart_temporal:
            await asyncio.sleep(.5)
            process = await asyncio.create_subprocess_exec(str(ROOT / '.venv/bin/supervisorctl'), '-c',
                str(CONFIG / 'supervisord.ini'), 'restart', 'temporal', stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE, env=environment())
            stdout, stderr = await process.communicate()
            require(process.returncode == 0, 'Temporal restart failed: ' + stderr.decode()[-1000:])
        actual = await asyncio.wait_for(handle.result(), timeout=60)
        require(actual == value, 'Temporal durable workflow result mismatch')
    with urlopen('http://127.0.0.1:8765/.well-known/agent-card.json', timeout=10) as response:
        require(response.status == 200, 'A2A agent card is unavailable')
    try:
        urlopen('http://127.0.0.1:8765/a2a', timeout=10)
        raise RuntimeError('A2A accepted a request without a bearer token')
    except HTTPError as error:
        require(error.code == 401, 'Unexpected A2A unauthorized response')
    token = environment()['A2A_LOCAL_TOKEN']
    request = Request('http://127.0.0.1:8765/a2a', method='POST',
        headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json', 'A2A-Version': '1.0'},
        data=json.dumps({'jsonrpc': '2.0', 'id': 'install', 'method': 'installationProbe', 'params': {}}).encode())
    with urlopen(request, timeout=10) as response:
        body = json.load(response)
        require(body['error']['code'] == -32601, 'A2A authenticated JSON-RPC path failed')
    from mlflow import MlflowClient
    tracking = MlflowClient(tracking_uri='http://127.0.0.1:5000')
    experiment = tracking.get_experiment_by_name('agentflow-installation')
    exp_id = experiment.experiment_id if experiment else tracking.create_experiment('agentflow-installation')
    run = tracking.create_run(exp_id, tags={'purpose': 'installation-smoke', 'temporal_workflow_id': value})
    tracking.log_metric(run.info.run_id, 'temporal_probe_success', 1)
    log = ROOT / 'native-tests.log'
    if log.exists():
        text = log.read_text()
        count = re.search(r'Ran (\d+) tests', text)
        require(count is not None and text.rstrip().endswith('OK'), 'Native runner tests did not pass')
        tracking.log_metric(run.info.run_id, 'native_tests_passed', int(count.group(1)))
        tracking.log_artifact(run.info.run_id, str(log))
    marker = output / 'codex-native-r1/acceptance.json'
    if marker.exists():
        data = read(marker)
        require(data['returncode'] == 0 and data['marker_verified'], 'Real Codex tool smoke did not pass')
        tracking.log_metric(run.info.run_id, 'codex_tool_probe_success', 1)
        tracking.log_artifact(run.info.run_id, str(marker))
    tracking.set_terminated(run.info.run_id, status='FINISHED')
    result = {'temporal_workflow_id': value, 'temporal_durable_result_verified': True,
              'temporal_restarted_during_probe': restart_temporal, 'a2a_public_card': True,
              'a2a_unauthenticated_request_rejected': True, 'a2a_authenticated_jsonrpc_verified': True,
              'mlflow_run_id': run.info.run_id, 'training_performance_claims': None}
    write(output / 'services.json', result, replace=True)
    return result
