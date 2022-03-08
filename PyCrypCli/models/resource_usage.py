from .model import Model


class ResourceUsage(Model):
    usage_cpu: float
    usage_ram: float
    usage_gpu: float
    usage_disk: float
    usage_network: float
    performance_cpu: float
    performance_ram: float
    performance_gpu: float
    performance_disk: float
    performance_network: float

    @property
    def cpu(self) -> float:
        return min(self.usage_cpu / self.performance_cpu, 1)

    @property
    def ram(self) -> float:
        return min(self.usage_ram / self.performance_ram, 1)

    @property
    def gpu(self) -> float:
        return min(self.usage_gpu / self.performance_gpu, 1)

    @property
    def disk(self) -> float:
        return min(self.usage_disk / self.performance_disk, 1)

    @property
    def network(self) -> float:
        return min(self.usage_network / self.performance_network, 1)
