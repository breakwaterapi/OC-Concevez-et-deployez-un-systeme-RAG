from dataclasses import dataclass

from api.modules.health.ports import ModelCheckerPort, StoreCheckerPort


@dataclass(frozen=True)
class HealthStatus:
    status: str
    store_ready: bool
    model_ready: bool
    index_size: int


@dataclass
class HealthUseCases:
    store_checker: StoreCheckerPort
    model_checker: ModelCheckerPort

    def check(self) -> HealthStatus:
        store_ready = self.store_checker.is_ready
        model_ready = self.model_checker.is_ready()
        return HealthStatus(
            status="ok" if store_ready and model_ready else "degraded",
            store_ready=store_ready,
            model_ready=model_ready,
            index_size=self.store_checker.n_vectors,
        )
