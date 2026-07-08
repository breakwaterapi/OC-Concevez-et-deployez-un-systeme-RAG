from dataclasses import dataclass, field

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_mistralai import ChatMistralAI


@dataclass
class MistralLLM:
    api_key: str
    model: str = "mistral-small-latest"
    temperature: float = 0.3
    chat: ChatMistralAI = field(init=False, repr=False)

    def __post_init__(self):
        self.chat = ChatMistralAI(
            model=self.model,  # pyright: ignore[reportCallIssue]
            mistral_api_key=self.api_key,  # pyright: ignore[reportCallIssue]
            temperature=self.temperature,
        )

    def invoke(self, system_prompt: str, user_message: str) -> str:
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
        response = self.chat.invoke(messages)
        return str(response.content)
