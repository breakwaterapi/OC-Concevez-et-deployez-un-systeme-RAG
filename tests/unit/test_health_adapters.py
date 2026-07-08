from unittest.mock import MagicMock, patch

from api.modules.health.adapters import MistralModelChecker


def test_is_ready_false_when_api_key_empty():
    checker = MistralModelChecker(api_key="")

    assert checker.is_ready() is False


@patch("api.modules.health.adapters.Mistral")
def test_is_ready_true_when_models_list_succeeds(mock_mistral_cls):
    mock_client = MagicMock()
    mock_mistral_cls.return_value = mock_client

    checker = MistralModelChecker(api_key="valid-key")

    assert checker.is_ready() is True
    mock_mistral_cls.assert_called_once_with(api_key="valid-key")
    mock_client.models.list.assert_called_once()


@patch("api.modules.health.adapters.Mistral")
def test_is_ready_false_when_models_list_raises(mock_mistral_cls):
    mock_client = MagicMock()
    mock_client.models.list.side_effect = RuntimeError("401 Unauthorized")
    mock_mistral_cls.return_value = mock_client

    checker = MistralModelChecker(api_key="invalid-key")

    assert checker.is_ready() is False
