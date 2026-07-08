from dataclasses import dataclass

from mistralai import Mistral

from api.modules.health.ports import ModelCheckerPort


@dataclass
class MistralModelChecker(ModelCheckerPort):
    api_key: str

    def is_ready(self) -> bool:
        if not self.api_key:
            return False
        try:
            Mistral(api_key=self.api_key).models.list()
            return True
        except Exception:
            return False
