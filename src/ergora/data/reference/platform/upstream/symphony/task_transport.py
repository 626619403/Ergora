"""Route task types without cloning the durable bridge or tracker integration."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'platform'))
from temporal_transport import Transport, NotFound
from dev_platform.runtime import DevelopmentTransport as SharedDevelopmentTransport, RuntimeNotFound


class DevelopmentTransport(SharedDevelopmentTransport):
    """Compatibility facade: preserve the bridge's historical NotFound type."""
    async def lookup(self, spec, run_id=None):
        try:
            return await super().lookup(spec, run_id)
        except RuntimeNotFound as error:
            raise NotFound from error

class TaskTransport:
    def __init__(self,client,training_queue,development_queue):
        self.training=Transport(client,training_queue)
        self.development=DevelopmentTransport(client,development_queue)
    def route(self,spec):
        return self.development if 'request' in spec else self.training
    async def start(self,spec):return await self.route(spec).start(spec)
    async def lookup(self,spec,run_id=None):return await self.route(spec).lookup(spec,run_id)
    async def poll(self,spec,run_id):return await self.route(spec).poll(spec,run_id)
