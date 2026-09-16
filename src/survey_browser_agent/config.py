import json
import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application settings loaded from environment variables and `.env`."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_prefix="SURVEY_AGENT_",
        env_ignore_empty=True,
        extra="ignore",
    )

    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3.5:9b"
    database_path: Path = Path("data/survey_browser_agent.db")
    chrome_profile_name: str = "Giveaway Agent"
    chrome_executable_path: Path | None = None
    max_steps: int = Field(default=12, ge=1, le=50)
    timeout_seconds: int = Field(default=600, ge=30, le=3600)
    qwen35_9b_llm_timeout_seconds: int = Field(default=180, ge=30, le=600)
    use_vision: bool = False

    def absolute_path(self, path: Path) -> Path:
        return path if path.is_absolute() else PROJECT_ROOT / path

    @property
    def resolved_database_path(self) -> Path:
        return self.absolute_path(self.database_path)

    @property
    def system_chrome_user_data_dir(self) -> Path:
        local_app_data = os.getenv("LOCALAPPDATA")
        if not local_app_data:
            raise ValueError("LOCALAPPDATA is unavailable; cannot locate Chrome profiles.")
        return Path(local_app_data) / "Google" / "Chrome" / "User Data"

    def resolve_chrome_profile_directory(self) -> str:
        """Translate a Chrome display name such as 'Giveaway Agent' to 'Profile 3'."""

        local_state = self.system_chrome_user_data_dir / "Local State"
        if not local_state.exists():
            raise ValueError(f"Chrome profile metadata was not found at {local_state}.")

        try:
            payload = json.loads(local_state.read_text(encoding="utf-8"))
            profiles = payload["profile"]["info_cache"]
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            raise ValueError(f"Could not read Chrome profile metadata: {exc}") from exc

        wanted = _normalize_profile_name(self.chrome_profile_name)
        for directory, profile in profiles.items():
            display_name = profile.get("name", "") if isinstance(profile, dict) else ""
            if wanted in {
                _normalize_profile_name(directory),
                _normalize_profile_name(display_name),
            }:
                return directory

        available = ", ".join(
            sorted(
                str(profile.get("name", directory))
                for directory, profile in profiles.items()
                if isinstance(profile, dict)
            )
        )
        raise ValueError(
            f'Chrome profile "{self.chrome_profile_name}" was not found. '
            f"Available profiles: {available or 'none'}"
        )

    def llm_timeout_for_selected_model(self) -> int | None:
        """Return a model-specific timeout without changing other model defaults."""

        if self.ollama_model.casefold() == "qwen3.5:9b":
            return self.qwen35_9b_llm_timeout_seconds
        return None


def _normalize_profile_name(value: str) -> str:
    return " ".join(value.replace("-", " ").split()).casefold()
