from survey_browser_agent.models import ExtractionStatus, NewsArticle

UNSUPPORTED_BROWSER_USE_SCHEMA_KEYWORDS = {
    "$ref",
    "$defs",
    "definitions",
    "allOf",
    "anyOf",
    "oneOf",
    "not",
    "if",
    "then",
    "else",
    "dependentSchemas",
    "dependentRequired",
}


def _schema_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {key for child in value.values() for key in _schema_keys(child)}
    if isinstance(value, list):
        return {key for child in value for key in _schema_keys(child)}
    return set()


def test_article_cleans_repeated_list_items() -> None:
    article = NewsArticle(
        page_title=" Example ",
        article_headline="Headline",
        source="Publisher",
        publication_date=None,
        article_url="https://example.com/news",
        short_factual_summary="Summary.",
        main_topics=["AI", " AI ", ""],
        extraction_status=ExtractionStatus.COMPLETED,
        missing_information=[],
        warnings=[],
    )

    assert article.page_title == "Example"
    assert article.main_topics == ["AI"]


def test_article_schema_uses_browser_use_compatible_subset() -> None:
    schema = NewsArticle.model_json_schema()

    assert not (_schema_keys(schema) & UNSUPPORTED_BROWSER_USE_SCHEMA_KEYWORDS)
    assert schema["properties"]["page_title"]["nullable"] is True
    assert schema["properties"]["extraction_status"]["enum"] == [
        "completed",
        "partial",
        "failed",
        "human_verification_required",
    ]
