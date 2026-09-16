import json

import pytest

from survey_browser_agent.browser_agent import LEAN_MAX_HISTORY_ITEMS, _ollama_options
from survey_browser_agent.config import Settings


def test_resolves_chrome_profile_by_display_name(tmp_path, monkeypatch) -> None:
    user_data = tmp_path / "Google" / "Chrome" / "User Data"
    user_data.mkdir(parents=True)
    (user_data / "Local State").write_text(
        json.dumps(
            {
                "profile": {
                    "info_cache": {
                        "Default": {"name": "Personal"},
                        "Profile 3": {"name": "Giveaway Agent"},
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    settings = Settings(chrome_profile_name="giveaway-agent")

    assert settings.resolve_chrome_profile_directory() == "Profile 3"


def test_missing_chrome_profile_does_not_fall_back(tmp_path, monkeypatch) -> None:
    user_data = tmp_path / "Google" / "Chrome" / "User Data"
    user_data.mkdir(parents=True)
    (user_data / "Local State").write_text(
        json.dumps({"profile": {"info_cache": {"Default": {"name": "Personal"}}}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    with pytest.raises(ValueError, match="was not found"):
        Settings(chrome_profile_name="Giveaway Agent").resolve_chrome_profile_directory()


def test_supported_local_models_get_their_own_timeout() -> None:
    qwen = Settings(
        ollama_model="qwen3.5:9b",
        qwen35_9b_llm_timeout_seconds=180,
    )
    llama = Settings(
        ollama_model="llama3.1:8b",
        llama31_8b_llm_timeout_seconds=150,
    )
    another_model = Settings(ollama_model="gemma3:4b")

    assert qwen.llm_timeout_for_selected_model() == 180
    assert llama.llm_timeout_for_selected_model() == 150
    assert another_model.llm_timeout_for_selected_model() is None


def test_local_model_options_disable_extended_thinking() -> None:
    settings = Settings(ollama_context_tokens=8192, ollama_max_output_tokens=1024)

    assert _ollama_options(settings) == {
        "think": False,
        "temperature": 0.0,
        "num_ctx": 8192,
        "num_predict": 1024,
    }


def test_lean_history_respects_browser_use_minimum() -> None:
    assert LEAN_MAX_HISTORY_ITEMS > 5
