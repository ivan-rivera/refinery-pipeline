"""Unit tests for Reddit schema models."""

from __future__ import annotations

from src.schemas.reddit import Comment, Thread


def _make_thread(**overrides) -> Thread:
    defaults = {
        "id": "abc123",
        "title": "Gold breaking out above 3200",
        "body": "",
        "url": "https://reddit.com/r/goldsilver/comments/abc123",
        "score": 1234,
        "num_comments": 89,
        "subreddit": "goldsilver",
        "top_comments": [],
    }
    return Thread(**{**defaults, **overrides})


def test_to_text_header_contains_subreddit_and_title():
    thread = _make_thread()
    text = thread.to_text()
    assert "r/goldsilver" in text
    assert "Gold breaking out above 3200" in text


def test_to_text_includes_score_and_comment_count():
    thread = _make_thread()
    text = thread.to_text()
    assert "1234" in text
    assert "89" in text


def test_to_text_renders_comments():
    thread = _make_thread(
        top_comments=[
            Comment(body="Textbook breakout.", score=890, replies=[]),
            Comment(body="Already priced in.", score=445, replies=[]),
        ]
    )
    text = thread.to_text()
    assert "[+890] Textbook breakout." in text
    assert "[+445] Already priced in." in text


def test_to_text_indents_replies():
    thread = _make_thread(
        top_comments=[
            Comment(
                body="Breakout incoming.",
                score=500,
                replies=[Comment(body="Watch the 50d MA.", score=88, replies=[])],
            )
        ]
    )
    text = thread.to_text()
    assert "  [+88] Watch the 50d MA." in text


def test_to_text_includes_body_when_present():
    thread = _make_thread(body="OP text here about gold signals.")
    text = thread.to_text()
    assert "OP text here about gold signals." in text


def test_to_text_omits_body_section_when_empty():
    thread = _make_thread(body="")
    lines = thread.to_text().split("\n")
    assert not any(line == "" and i == 1 for i, line in enumerate(lines[:3]))
