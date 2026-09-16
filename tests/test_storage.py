from datetime import UTC, datetime

from survey_browser_agent.models import ExtractionStatus, NewsArticle
from survey_browser_agent.storage import RunStore


def test_run_round_trip(tmp_path) -> None:
    store = RunStore(tmp_path / "runs.db")
    article = NewsArticle(
        page_title="Page",
        article_headline="Headline",
        source="Publisher",
        publication_date="2026-01-02",
        article_url="https://example.com/article",
        short_factual_summary="A factual summary.",
        main_topics=["topic"],
        extraction_status=ExtractionStatus.COMPLETED,
        missing_information=[],
        warnings=[],
    )

    run_id = store.save(
        started_at=datetime.now(UTC),
        url=article.article_url,
        model="qwen3.5:9b",
        status=article.extraction_status.value,
        duration_seconds=1.25,
        steps=3,
        result=article,
    )

    loaded = store.get(run_id)
    assert loaded is not None
    assert loaded.result == article
    assert store.list()[0].id == run_id
