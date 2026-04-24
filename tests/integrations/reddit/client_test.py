"""RedditClient unit and integration tests."""

from __future__ import annotations

import time

import pytest
import requests

from src.integrations.reddit import RedditClient, make_reddit_client
from src.schemas.reddit import Comment, Thread


def _hot_response(posts: list[dict]) -> dict:
    return {"data": {"children": [{"kind": "t3", "data": p} for p in posts]}}


def _post_data(**overrides) -> dict:
    defaults = {
        "id": "abc123",
        "title": "Gold surges",
        "selftext": "",
        "url": "https://reddit.com/r/goldsilver/comments/abc123",
        "score": 500,
        "num_comments": 30,
        "subreddit": "goldsilver",
    }
    return {**defaults, **overrides}


def _comment_data(**overrides) -> dict:
    defaults = {"body": "Looks bullish.", "score": 100, "replies": ""}
    return {**defaults, **overrides}


def _comments_response(post: dict, comments: list[dict]) -> list[dict]:
    return [
        {"data": {"children": [{"kind": "t3", "data": post}]}},
        {"data": {"children": [{"kind": "t1", "data": c} for c in comments]}},
    ]


def test_get_hot_threads_returns_threads(mocker):
    session = mocker.MagicMock(spec=requests.Session)
    response = mocker.MagicMock()
    response.json.return_value = _hot_response([_post_data()])
    session.get.return_value = response
    client = RedditClient(session)
    threads = client.get_hot_threads("goldsilver", limit=1)
    assert len(threads) == 1
    assert isinstance(threads[0], Thread)
    assert threads[0].id == "abc123"
    assert threads[0].title == "Gold surges"


def test_get_hot_threads_skips_non_t3_children(mocker):
    session = mocker.MagicMock(spec=requests.Session)
    response = mocker.MagicMock()
    response.json.return_value = {
        "data": {
            "children": [
                {"kind": "t3", "data": _post_data(id="keep")},
                {"kind": "more", "data": {}},
            ]
        }
    }
    session.get.return_value = response
    client = RedditClient(session)
    threads = client.get_hot_threads("goldsilver")
    assert len(threads) == 1
    assert threads[0].id == "keep"


def test_get_thread_comments_returns_thread_with_comments(mocker):
    session = mocker.MagicMock(spec=requests.Session)
    response = mocker.MagicMock()
    response.json.return_value = _comments_response(
        _post_data(),
        [_comment_data(body="Strong momentum.", score=200)],
    )
    session.get.return_value = response
    client = RedditClient(session)
    thread = client.get_thread_comments("goldsilver", "abc123")
    assert thread.id == "abc123"
    assert len(thread.top_comments) == 1
    assert thread.top_comments[0].body == "Strong momentum."


def test_get_thread_comments_filters_removed_comments(mocker):
    session = mocker.MagicMock(spec=requests.Session)
    response = mocker.MagicMock()
    response.json.return_value = _comments_response(
        _post_data(),
        [
            _comment_data(body="[removed]", score=50),
            _comment_data(body="[deleted]", score=50),
            _comment_data(body="Good point.", score=50),
        ],
    )
    session.get.return_value = response
    client = RedditClient(session)
    thread = client.get_thread_comments("goldsilver", "abc123")
    assert len(thread.top_comments) == 1
    assert thread.top_comments[0].body == "Good point."


def test_get_thread_comments_filters_negative_score_comments(mocker):
    session = mocker.MagicMock(spec=requests.Session)
    response = mocker.MagicMock()
    response.json.return_value = _comments_response(
        _post_data(),
        [
            _comment_data(body="Spam.", score=-5),
            _comment_data(body="Valuable insight.", score=10),
        ],
    )
    session.get.return_value = response
    client = RedditClient(session)
    thread = client.get_thread_comments("goldsilver", "abc123")
    assert len(thread.top_comments) == 1
    assert thread.top_comments[0].body == "Valuable insight."


def test_get_thread_comments_truncates_long_body(mocker):
    session = mocker.MagicMock(spec=requests.Session)
    response = mocker.MagicMock()
    long_body = "x" * 1000
    response.json.return_value = _comments_response(_post_data(selftext=long_body), [])
    session.get.return_value = response
    client = RedditClient(session)
    thread = client.get_thread_comments("goldsilver", "abc123")
    assert len(thread.body) == 500


def test_get_thread_comments_truncates_long_comment(mocker):
    session = mocker.MagicMock(spec=requests.Session)
    response = mocker.MagicMock()
    response.json.return_value = _comments_response(
        _post_data(),
        [_comment_data(body="y" * 600, score=10)],
    )
    session.get.return_value = response
    client = RedditClient(session)
    thread = client.get_thread_comments("goldsilver", "abc123")
    assert thread.top_comments[0].body == "y" * 300 + "..."


def test_get_thread_comments_parses_nested_replies(mocker):
    session = mocker.MagicMock(spec=requests.Session)
    response = mocker.MagicMock()
    reply = {
        "kind": "t1",
        "data": {"body": "Good reply.", "score": 20, "replies": ""},
    }
    comment_with_reply = _comment_data(
        body="Top comment.",
        score=100,
        replies={"data": {"children": [reply]}},
    )
    response.json.return_value = _comments_response(_post_data(), [comment_with_reply])
    session.get.return_value = response
    client = RedditClient(session)
    thread = client.get_thread_comments("goldsilver", "abc123")
    assert len(thread.top_comments[0].replies) == 1
    assert thread.top_comments[0].replies[0].body == "Good reply."


def test_throttle_sleeps_when_within_one_second(mocker):
    session = mocker.MagicMock(spec=requests.Session)
    sleep_mock = mocker.patch("src.integrations.reddit.client.time.sleep")
    client = RedditClient(session)
    client._last_request_at = time.monotonic()  # simulate a request just happened
    client._throttle()
    sleep_mock.assert_called_once()
    sleep_arg = sleep_mock.call_args[0][0]
    assert 0 < sleep_arg <= 1.0


def test_throttle_does_not_sleep_after_one_second(mocker):
    session = mocker.MagicMock(spec=requests.Session)
    sleep_mock = mocker.patch("src.integrations.reddit.client.time.sleep")
    client = RedditClient(session)
    client._last_request_at = time.monotonic() - 2.0  # last request was 2s ago
    client._throttle()
    sleep_mock.assert_not_called()


def test_make_reddit_client_sets_user_agent():
    client = make_reddit_client()
    assert "refinery-pipeline" in client._session.headers["User-Agent"]


# ---------------------------------------------------------------------------
# Integration tests — hit the real Reddit JSON API
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_integration_get_hot_threads():
    client = make_reddit_client()
    threads = client.get_hot_threads("goldsilver", limit=3)
    assert len(threads) > 0
    assert all(isinstance(t, Thread) for t in threads)
    assert all(t.title for t in threads)


@pytest.mark.integration
def test_integration_get_thread_comments():
    client = make_reddit_client()
    threads = client.get_hot_threads("goldsilver", limit=1)
    assert threads, "No threads returned — check Reddit connectivity"
    thread = client.get_thread_comments("goldsilver", threads[0].id, limit=5)
    assert isinstance(thread, Thread)
    assert thread.id == threads[0].id
    text = thread.to_text()
    assert "r/goldsilver" in text
