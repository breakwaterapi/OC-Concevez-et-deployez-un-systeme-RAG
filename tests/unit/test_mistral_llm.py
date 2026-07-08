from typing import cast
from unittest.mock import MagicMock

from langchain_core.messages import HumanMessage, SystemMessage

from api.infra.mistral.llm import MistralLLM


def _llm() -> MistralLLM:
    llm = MistralLLM(api_key="test-key")
    llm.chat = MagicMock()
    return llm


def test_invoke_returns_response_content_as_string():
    llm = _llm()
    mock_chat = cast(MagicMock, llm.chat)
    mock_chat.invoke.return_value = MagicMock(content="Voici la réponse.")

    result = llm.invoke("system", "question")

    assert result == "Voici la réponse."


def test_invoke_builds_system_and_human_messages():
    llm = _llm()
    mock_chat = cast(MagicMock, llm.chat)
    mock_chat.invoke.return_value = MagicMock(content="ok")

    llm.invoke("system prompt", "user question")

    mock_chat.invoke.assert_called_once_with(
        [SystemMessage(content="system prompt"), HumanMessage(content="user question")]
    )


def test_invoke_casts_non_string_content_to_string():
    llm = _llm()
    mock_chat = cast(MagicMock, llm.chat)
    mock_chat.invoke.return_value = MagicMock(content=42)

    result = llm.invoke("system", "question")

    assert result == "42"
