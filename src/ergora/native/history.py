"""Match complete operation signals in the original fixed-run history."""

from datetime import timedelta


async def find_signal_event(handle, converter, signal_name: str, payload: dict) -> int | None:
    """Stream the original run's history and match the complete signal payload."""
    from dev_platform.contracts import canonical_sha

    async for event in handle.fetch_history_events(page_size=100, rpc_timeout=timedelta(seconds=20)):
        if not event.HasField('workflow_execution_signaled_event_attributes'):
            continue
        signal = event.workflow_execution_signaled_event_attributes
        if signal.signal_name != signal_name or len(signal.input.payloads) != 1:
            continue
        values = await converter.decode(signal.input.payloads, [dict])
        if canonical_sha(values) == canonical_sha([payload]):
            return event.event_id
    return None
