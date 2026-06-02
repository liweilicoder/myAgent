from josie_agents.memory.base import BaseMemory, MemoryConfig


class PerceptualMemory:

    def __init__(self, config: MemoryConfig, storage_backend=None):
        super().__init__(config, storage_backend)