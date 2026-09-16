from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExtractionStatus(StrEnum):
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    HUMAN_VERIFICATION_REQUIRED = "human_verification_required"


class NewsArticle(BaseModel):
    """Validated data returned by the browser agent."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    page_title: str | None = Field(description="The browser page title, if visible")
    article_headline: str | None = Field(description="The article's main headline")
    source: str | None = Field(description="Publisher or news source")
    publication_date: str | None = Field(
        description="Publication date exactly as supported by page"
    )
    article_url: str = Field(description="The final URL of the article")
    short_factual_summary: str | None = Field(
        description="A short factual summary supported only by the page"
    )
    main_topics: list[str] = Field(default_factory=list, max_length=12)
    extraction_status: ExtractionStatus
    missing_information: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @classmethod
    def model_json_schema(cls, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Return the flat subset accepted by Browser Use 0.12.x extraction."""

        del args, kwargs
        nullable_string = {"type": "string", "nullable": True}
        string_list = {"type": "array", "items": {"type": "string"}}
        return {
            "title": "NewsArticle",
            "description": "Factual fields extracted from one news article.",
            "type": "object",
            "properties": {
                "page_title": {
                    **nullable_string,
                    "description": "Browser page title, or null if unavailable.",
                },
                "article_headline": {
                    **nullable_string,
                    "description": "Main article headline, or null if unavailable.",
                },
                "source": {
                    **nullable_string,
                    "description": "Publisher, or null if unavailable.",
                },
                "publication_date": {
                    **nullable_string,
                    "description": "Publication date as shown, or null if unavailable.",
                },
                "article_url": {
                    "type": "string",
                    "description": "Final URL of the article.",
                },
                "short_factual_summary": {
                    **nullable_string,
                    "description": "Short page-supported summary, or null.",
                },
                "main_topics": {
                    **string_list,
                    "description": "Main topics from the article.",
                },
                "extraction_status": {
                    "type": "string",
                    "enum": [status.value for status in ExtractionStatus],
                    "description": "Whether extraction completed or why it stopped.",
                },
                "missing_information": {
                    **string_list,
                    "description": "Requested fields unavailable on the page.",
                },
                "warnings": {
                    **string_list,
                    "description": "Uncertainty or access limitations.",
                },
            },
            "required": [
                "page_title",
                "article_headline",
                "source",
                "publication_date",
                "article_url",
                "short_factual_summary",
                "extraction_status",
            ],
        }

    @field_validator("main_topics", "missing_information", "warnings")
    @classmethod
    def clean_string_lists(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for value in values:
            item = value.strip()
            if item and item not in cleaned:
                cleaned.append(item)
        return cleaned


class RunSummary(BaseModel):
    id: int
    started_at: datetime
    completed_at: datetime
    url: str
    model: str
    status: str
    duration_seconds: float
    steps: int
    error: str | None = None


class SavedRun(RunSummary):
    result: NewsArticle | None = None


class OllamaCheck(BaseModel):
    reachable: bool
    model: str
    model_available: bool
    installed_models: list[str] = Field(default_factory=list)
    message: str
