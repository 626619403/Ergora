from temporalio import workflow


@workflow.defn
class InstallationProbe:
    @workflow.run
    async def run(self, value: str) -> str:
        await workflow.sleep(3)
        return value
