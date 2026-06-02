from josie_agents.memory.base import BaseMemory, MemoryConfig


class EpisodicMemory:

    def __init__(self, config: MemoryConfig, storage_backend=None):
        super().__init__(config, storage_backend)