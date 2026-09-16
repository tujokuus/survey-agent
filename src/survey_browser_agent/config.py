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
    chrome_profile_dir: Path = Path("data/chrome-profile")
    chrome_executable_path: Path | None = None
    max_steps: int = Field(default=12, ge=1, le=50)
    timeout_seconds: int = Field(default=180, ge=30, le=1800)
    use_vision: bool = False

    def absolute_path(self, path: Path) -> Path:
        return path if path.is_absolute() else PROJECT_ROOT / path

    @property
    def resolved_database_path(self) -> Path:
        return self.absolute_path(self.database_path)

    @property
    def resolved_chrome_profile_dir(self) -> Path:
        return self.absolute_path(self.chrome_profile_dir)
