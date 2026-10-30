import os
from temporalio.client import Client


async def connect():
    address = os.environ["TEMPORAL_ADDRESS"]
    namespace = os.environ["TEMPORAL_NAMESPACE"]
    if os.environ.get("TEMPORAL_LOCAL_DEV") == "1":
        if address not in {"localhost:7233", "127.0.0.1:7233"}:
            raise ValueError("Insecure test mode is restricted to loopback")
        return await Client.connect(address, namespace=namespace)
    key = os.environ["TEMPORAL_API_KEY"]
    if not key: raise ValueError("TEMPORAL_API_KEY cannot be empty")
    return await Client.connect(address, namespace=namespace, api_key=key, tls=True)


def task_queue(): return os.environ.get("DEV_TASK_QUEUE", "development-tasks")
