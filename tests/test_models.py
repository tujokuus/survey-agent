from survey_browser_agent.models import ExtractionStatus, NewsArticle


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
